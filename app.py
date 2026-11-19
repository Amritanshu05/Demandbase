"""Relay: locally hosted, temporary digital resource sharing."""

import hashlib
import io
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import click
from flask import (
    Flask, abort, current_app, flash, g, redirect, render_template,
    request, send_file, session, url_for,
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import SecurityError


EXPIRIES = {"60": "1 minute · demo", "3600": "1 hour", "86400": "1 day",
            "604800": "7 days", "2592000": "30 days"}
LANGUAGES = {"plain": "Plain text", "python": "Python", "javascript": "JavaScript",
             "typescript": "TypeScript", "json": "JSON", "html": "HTML",
             "css": "CSS", "sql": "SQL", "shell": "Shell"}
KINDS = {"text": "Text", "code": "Code", "document": "Document", "link": "Link"}
MAX_FILE = 5 * 1024 * 1024


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATA_DIR"] / "relay.sqlite3", timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


def now():
    return int(current_app.config["CLOCK"]())


def owner_hash():
    return hashlib.sha256(session["owner"].encode()).hexdigest()


def share_status(share):
    if share["revoked"]:
        return "revoked"
    return "expired" if share["expires_at"] <= now() else "active"


def remove_payload(share):
    """Only remove the server-named file referenced by an existing database row."""
    if share["storage_key"]:
        root = current_app.config["DATA_DIR"] / "uploads"
        path = (root / share["storage_key"]).resolve()
        if path.parent != root.resolve():
            raise RuntimeError("Refusing unsafe stored path")
        path.unlink(missing_ok=True)


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATA_DIR=Path(os.environ.get("RELAY_DATA_DIR", "instance")).resolve(),
        MAX_CONTENT_LENGTH=MAX_FILE + 256 * 1024,
        MAX_FORM_MEMORY_SIZE=200_000,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("RELAY_SECURE_COOKIE") == "1",
        PERMANENT_SESSION_LIFETIME=30 * 86400,
        CLOCK=time.time,
        TRUSTED_HOSTS=["localhost", "127.0.0.1", "[::1]"],
    )
    if config:
        app.config.update(config)
    app.config["DATA_DIR"] = Path(app.config["DATA_DIR"]).resolve()
    data_dir = app.config["DATA_DIR"]
    data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    (data_dir / "uploads").mkdir(exist_ok=True, mode=0o700)
    if not app.config.get("SECRET_KEY"):
        key_path = data_dir / "secret.key"
        try:
            with open(key_path, "x", opener=lambda p, flags: os.open(p, flags, 0o600)) as key:
                key.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = key_path.read_text().strip()

    with app.app_context():
        db = get_db()
        db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS shares (
                id TEXT PRIMARY KEY,
                owner_hash TEXT NOT NULL,
                title TEXT NOT NULL,
                kind TEXT NOT NULL CHECK(kind IN ('text','code','document','link')),
                content TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'plain',
                filename TEXT,
                storage_key TEXT,
                size INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0,
                views INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS shares_owner_created ON shares(owner_hash, created_at DESC);
            CREATE INDEX IF NOT EXISTS shares_expiry ON shares(expires_at);
        """)
        db.commit()
        db.close()
        g.pop("db")

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def protect_request():
        if "owner" not in session:
            session["owner"] = secrets.token_urlsafe(32)
            session["csrf"] = secrets.token_urlsafe(32)
            session.permanent = True
        if request.method == "POST":
            supplied = request.form.get("csrf", "")
            if not secrets.compare_digest(supplied, session["csrf"]):
                abort(403, description="This form has expired. Reload the page and try again.")

    @app.after_request
    def headers(response):
        response.headers.update({
            "Cache-Control": "no-store, private",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                                     "img-src 'self'; object-src 'none'; base-uri 'none'; "
                                     "frame-ancestors 'none'; form-action 'self'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        })
        return response

    @app.context_processor
    def template_helpers():
        return dict(kinds=KINDS, languages=LANGUAGES, expiries=EXPIRIES, status=share_status)

    @app.template_filter("date")
    def format_date(value):
        return datetime.fromtimestamp(value, timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    @app.template_filter("filesize")
    def file_size(value):
        return f"{value / 1024:.1f} KB" if value >= 1024 else f"{value} B"

    @app.get("/")
    def dashboard():
        query = request.args.get("q", "").strip()[:120]
        kind = request.args.get("kind", "")
        state = request.args.get("state", "")
        # Filtering is bounded to the owner's latest 200 records in this local MVP.
        rows = get_db().execute(
            "SELECT * FROM shares WHERE owner_hash=? ORDER BY created_at DESC, rowid DESC LIMIT 200",
            (owner_hash(),),
        ).fetchall()
        counts = {s: sum(share_status(row) == s for row in rows)
                  for s in ("active", "expired", "revoked")}
        filtered = [row for row in rows if
                    (not query or query.casefold() in row["title"].casefold()) and
                    (not kind or row["kind"] == kind) and
                    (not state or share_status(row) == state)]
        return render_template("dashboard.html", shares=filtered, counts=counts,
                               total=len(rows), query=query, kind=kind, state=state)

    @app.get("/new")
    def new_share():
        return render_template("new.html", values={}, error=None)

    @app.post("/shares")
    def create_share():
        form = request.form
        title = form.get("title", "").strip()
        kind = form.get("kind", "")
        content = form.get("content", "").strip() if kind == "link" else form.get("content", "")
        expiry = form.get("expiry", "")
        language = form.get("language", "plain")
        filename = storage_key = None
        payload = b""

        def invalid(message):
            return render_template("new.html", values=form, error=message), 422

        if not title or len(title) > 120:
            return invalid("Enter a title between 1 and 120 characters.")
        if kind not in KINDS or expiry not in EXPIRIES or language not in LANGUAGES:
            return invalid("Choose a supported resource type, language, and expiry.")
        if kind != "document" and (not content.strip() or len(content) > 100_000):
            return invalid("Enter content between 1 and 100,000 characters.")
        if kind == "link":
            try:
                parsed = urlsplit(content)
                valid = (parsed.scheme in ("https", "http") and parsed.hostname
                         and not parsed.username and not parsed.password and parsed.port != 0
                         and not any(c.isspace() or ord(c) < 32 for c in content)
                         and len(content) <= 2048 and "\\" not in content)
            except ValueError:
                valid = False
            if not valid:
                return invalid("Enter a full http:// or https:// URL without embedded credentials (max 2,048 characters).")
        if kind == "document":
            upload = request.files.get("file")
            if not upload or not upload.filename:
                return invalid("Choose a PDF, TXT, MD, or CSV document (maximum 5 MB).")
            filename = secure_filename(upload.filename)[:180]
            suffix = Path(filename).suffix.lower()
            if suffix not in (".pdf", ".txt", ".md", ".csv"):
                return invalid("Supported documents: PDF, TXT, MD, and CSV.")
            payload = upload.read(MAX_FILE + 1)
            if not payload or len(payload) > MAX_FILE:
                return invalid("The document must be non-empty and no larger than 5 MB.")
            if suffix == ".pdf":
                if not payload.startswith(b"%PDF-"):
                    return invalid("The selected file does not have a valid PDF header.")
            else:
                try:
                    payload.decode("utf-8")
                except UnicodeDecodeError:
                    return invalid("Text documents must use UTF-8 encoding.")
                if b"\x00" in payload:
                    return invalid("Text documents cannot contain binary data.")
            content = ""
            storage_key = secrets.token_hex(24)

        db = get_db()
        # Local abuse guard: bounded active resources and a persistent creation quota.
        recent = db.execute("SELECT count(*) FROM shares WHERE owner_hash=? AND created_at>?",
                            (owner_hash(), now() - 3600)).fetchone()[0]
        active = db.execute("SELECT count(*) FROM shares WHERE owner_hash=? AND revoked=0 AND expires_at>?",
                            (owner_hash(), now())).fetchone()[0]
        if recent >= 60 or active >= 100:
            abort(429, description="This browser has reached the local sharing limit. Try again later or revoke active shares.")
        token = secrets.token_urlsafe(24)
        path = data_dir / "uploads" / storage_key if storage_key else None
        try:
            if path:
                path.write_bytes(payload)
            db.execute(
                """INSERT INTO shares
                (id,owner_hash,title,kind,content,language,filename,storage_key,size,created_at,expires_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (token, owner_hash(), title, kind, content, language, filename, storage_key,
                 len(payload) if path else len(content.encode("utf-8")), now(), now() + int(expiry)),
            )
            db.commit()
        except Exception:
            db.rollback()
            if path:
                path.unlink(missing_ok=True)
            raise
        flash("Share created. Copy the link below to pass it on.")
        return redirect(url_for("view_share", token=token), code=303)

    def find_share(token, owner_only=False):
        share = get_db().execute("SELECT * FROM shares WHERE id=?", (token,)).fetchone()
        if share is None or (owner_only and share["owner_hash"] != owner_hash()):
            abort(404)
        return share

    def require_active(share):
        if share_status(share) != "active":
            abort(410, description="This share has expired or been revoked. Ask the owner for a new link.")

    @app.get("/s/<token>")
    def view_share(token):
        share = find_share(token)
        require_active(share)
        is_owner = share["owner_hash"] == owner_hash()
        if not is_owner and request.method != "HEAD":
            db = get_db()
            db.execute("UPDATE shares SET views=views+1 WHERE id=?", (token,))
            db.commit()
            share = find_share(token)
        preview = None
        if share["kind"] == "document" and Path(share["filename"]).suffix.lower() != ".pdf":
            path = data_dir / "uploads" / share["storage_key"]
            if not path.is_file():
                abort(404, description="The document is no longer available.")
            with path.open("rb") as source:
                preview = source.read(20_000).decode("utf-8", errors="replace")
        return render_template("share.html", share=share, is_owner=is_owner, preview=preview)

    @app.get("/s/<token>/download")
    def download_share(token):
        share = find_share(token)
        require_active(share)
        if share["kind"] == "document":
            source = data_dir / "uploads" / share["storage_key"]
            if not source.is_file():
                abort(404, description="The document is no longer available.")
            filename = share["filename"]
        else:
            source = io.BytesIO(share["content"].encode("utf-8"))
            filename = (secure_filename(share["title"]) or "resource") + ".txt"
        return send_file(source, as_attachment=True, download_name=filename,
                         mimetype="application/octet-stream", conditional=False, etag=False)

    @app.post("/s/<token>/revoke")
    def revoke_share(token):
        share = find_share(token, owner_only=True)
        db = get_db()
        # Commit denial first: file cleanup failure must never leave a live share.
        db.execute("UPDATE shares SET revoked=1,content='' WHERE id=?", (token,))
        db.commit()
        remove_payload(share)
        flash("Share revoked. The link and downloads are now unavailable.")
        return redirect(url_for("dashboard"), code=303)

    @app.cli.command("cleanup")
    def cleanup():
        """Delete expired/revoked rows and their document payloads."""
        db = get_db()
        rows = db.execute("SELECT * FROM shares WHERE expires_at<=? OR revoked=1", (now(),)).fetchall()
        for row in rows:
            remove_payload(row)
            db.execute("DELETE FROM shares WHERE id=?", (row["id"],))
        db.commit()
        click.echo(f"Removed {len(rows)} expired/revoked shares.")

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return {"status": "ok"}

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(410)
    @app.errorhandler(413)
    @app.errorhandler(429)
    @app.errorhandler(500)
    def error_page(error):
        # An untrusted host fails before Flask creates its URL adapter.
        # Rendering the normal layout would call url_for and mask the 400.
        if isinstance(error, SecurityError):
            return "Invalid request host.", 400, {"Content-Type": "text/plain; charset=utf-8"}
        messages = {404: "We couldn't find that resource.", 413: "The upload is too large. Documents must be 5 MB or smaller.",
                    500: "Something went wrong. Please try again."}
        message = messages.get(error.code, error.description)
        return render_template("error.html", code=error.code, message=message), error.code

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)

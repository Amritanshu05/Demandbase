"""Campus Commons: a local, persistent physical-item borrowing demo."""

import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (
    Flask, abort, current_app, flash, g, redirect, render_template,
    request, session, url_for,
)


CATEGORIES = {
    "Sports": "sports", "Electronics": "electronics", "Books": "books",
    "Tools": "tools", "Outdoors": "outdoors", "Other": "other",
}
CONDITIONS = ("Like new", "Good", "Fair")
COMMUNITY_TZ = ZoneInfo("Asia/Kolkata")

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL REFERENCES members(id),
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 100),
    category TEXT NOT NULL CHECK(category IN ('Sports','Electronics','Books','Tools','Outdoors','Other')),
    description TEXT NOT NULL CHECK(length(trim(description)) BETWEEN 1 AND 600),
    condition TEXT NOT NULL CHECK(condition IN ('Like new','Good','Fair')),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS borrow_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    borrower_id INTEGER NOT NULL REFERENCES members(id),
    expected_return TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK(status IN ('Pending','Approved','Rejected','Returned')),
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_approved_per_item
    ON borrow_requests(item_id) WHERE status = 'Approved';
CREATE UNIQUE INDEX IF NOT EXISTS one_pending_per_borrower
    ON borrow_requests(item_id, borrower_id) WHERE status = 'Pending';
CREATE INDEX IF NOT EXISTS requests_borrower ON borrow_requests(borrower_id);
"""

ITEM_QUERY = """
SELECT i.*, m.name AS owner_name,
       EXISTS(SELECT 1 FROM borrow_requests r
              WHERE r.item_id=i.id AND r.status='Approved') AS borrowed
FROM items i JOIN members m ON m.id=i.owner_id
"""
ACTIVITY_QUERY = """
SELECT r.*, i.name AS item_name, i.owner_id, i.category,
       o.name AS owner_name, o.email AS owner_email, b.name AS borrower_name
FROM borrow_requests r JOIN items i ON i.id=r.item_id
JOIN members o ON o.id=i.owner_id JOIN members b ON b.id=r.borrower_id
"""


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def today():
    return current_app.config.get("TODAY") or datetime.now(COMMUNITY_TZ).date()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=5)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@contextmanager
def write_transaction():
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def seed_database():
    db = get_db()
    db.executescript(SCHEMA)
    with write_transaction():
        if db.execute("SELECT 1 FROM metadata WHERE key='seed_version'").fetchone():
            return
        db.executemany("INSERT INTO members(id,name,email) VALUES(?,?,?)", [
            (1, "Amritanshu", "amritanshu@example.com"),
            (2, "Rahul", "rahul@example.com"),
            (3, "Priya", "priya@example.com"),
        ])
        seeds = [
            (2, "Cricket Bat", "Sports", "A trusty willow bat for a friendly match. Best with a tennis ball.", "Good"),
            (3, "Mini Projector", "Electronics", "Make movie night a little bigger. HDMI cable and remote included.", "Like new"),
            (1, "Cordless Drill", "Tools", "For that small DIY project. Includes a charged battery and a basic bit set.", "Good"),
            (3, "The Design of Everyday Things", "Books", "A well-loved copy for curious minds. Please keep the bookmarks inside.", "Fair"),
            (2, "Camping Tent", "Outdoors", "A two-person tent for a weekend under the stars. Pegs and carry bag included.", "Good"),
            (1, "Badminton Set", "Sports", "Two rackets and a few shuttlecocks. All you need is a court and a friend.", "Good"),
        ]
        db.executemany(
            "INSERT INTO items(owner_id,name,category,description,condition,created_at) VALUES(?,?,?,?,?,?)",
            [(*item, timestamp()) for item in seeds],
        )
        db.execute("INSERT INTO metadata VALUES('seed_version','1')")


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATA_DIR=Path(os.environ.get("COMMONS_DATA_DIR", Path(__file__).parent / "instance")),
        MAX_CONTENT_LENGTH=32 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)
    data_dir = Path(app.config["DATA_DIR"]).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    app.config.setdefault("DATABASE", str(data_dir / "commons.sqlite3"))
    if not app.config.get("SECRET_KEY"):
        key_path = data_dir / "secret.key"
        try:
            with open(key_path, "x", opener=lambda p, flags: os.open(p, flags, 0o600)) as key:
                key.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        app.config["SECRET_KEY"] = key_path.read_text().strip()

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        seed_database()

    @app.before_request
    def load_member():
        if request.endpoint == "static":
            return
        g.members = get_db().execute("SELECT * FROM members ORDER BY id").fetchall()
        member_id = session.get("member_id", 1)
        g.member = next((m for m in g.members if m["id"] == member_id), g.members[0])
        session["member_id"] = g.member["id"]
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(32)
        if request.method == "POST":
            token = request.form.get("csrf", "")
            if not secrets.compare_digest(token.encode(), session["csrf"].encode()):
                abort(403, description="This form has expired. Reload the page and try again.")

    @app.after_request
    def response_headers(response):
        response.headers.update({
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "same-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
                                       "img-src 'self' data:; object-src 'none'; base-uri 'self'; "
                                       "frame-ancestors 'none'; form-action 'self'",
        })
        return response

    @app.context_processor
    def shared_context():
        return dict(categories=CATEGORIES, conditions=CONDITIONS, today=today())

    @app.template_filter("return_date")
    def return_date(value):
        parsed = date.fromisoformat(value)
        label = f"{parsed.day} {parsed.strftime('%B')}"
        return label if parsed.year == today().year else f"{label} {parsed.year}"

    @app.get("/")
    def explore():
        db = get_db()
        items = db.execute(ITEM_QUERY + " WHERE NOT EXISTS (SELECT 1 FROM borrow_requests r WHERE r.item_id=i.id AND r.status='Approved') ORDER BY i.id DESC").fetchall()
        pending = {r["item_id"] for r in db.execute(
            "SELECT item_id FROM borrow_requests WHERE borrower_id=? AND status='Pending'", (g.member["id"],)
        )}
        own_count = db.execute("SELECT count(*) FROM items WHERE owner_id=?", (g.member["id"],)).fetchone()[0]
        return render_template("explore.html", items=items, pending=pending, own_count=own_count)

    @app.post("/demo-member")
    def switch_member():
        selected = request.form.get("member_id", type=int)
        if selected not in {m["id"] for m in g.members}:
            abort(400, description="Choose one of the demo members.")
        session["member_id"] = selected
        # Preserve only known destinations; never redirect to an arbitrary submitted URL.
        destination = "activity" if request.form.get("next") == "activity" else "explore"
        return redirect(url_for(destination), code=303)

    @app.get("/items/new")
    def new_item():
        return render_template("new_item.html", values={}, error=None)

    @app.post("/items")
    def create_item():
        values = {key: request.form.get(key, "").strip() for key in ("name", "description", "category", "condition")}
        error = None
        if not 1 <= len(values["name"]) <= 100:
            error = "Enter an item name between 1 and 100 characters."
        elif not 1 <= len(values["description"]) <= 600:
            error = "Enter a description between 1 and 600 characters."
        elif values["category"] not in CATEGORIES or values["condition"] not in CONDITIONS:
            error = "Choose a category and condition from the available options."
        if error:
            return render_template("new_item.html", values=values, error=error), 422
        with write_transaction() as db:
            db.execute(
                "INSERT INTO items(owner_id,name,description,category,condition,created_at) VALUES(?,?,?,?,?,?)",
                (g.member["id"], values["name"], values["description"], values["category"], values["condition"], timestamp()),
            )
        flash("Your item is listed. Someone's next great borrow starts here.", "success")
        return redirect(url_for("explore"), code=303)

    @app.route("/items/<int:item_id>/request", methods=["GET", "POST"])
    def request_item(item_id):
        item = get_db().execute(ITEM_QUERY + " WHERE i.id=?", (item_id,)).fetchone()
        if item is None:
            abort(404)
        if item["owner_id"] == g.member["id"]:
            abort(403, description="This is your item. Switch to another demo member to borrow it.")
        if item["borrowed"]:
            abort(409, description="This item is already borrowed. It will be available when its owner records the return.")
        value = request.form.get("expected_return", "")
        error = None
        if request.method == "POST":
            try:
                expected = date.fromisoformat(value)
                if expected < today():
                    raise ValueError
            except ValueError:
                error = "Choose an expected return date that is today or later."
            if not error:
                try:
                    with write_transaction() as db:
                        if db.execute("SELECT 1 FROM borrow_requests WHERE item_id=? AND status='Approved'", (item_id,)).fetchone():
                            abort(409, description="This item was just borrowed. Please choose another item.")
                        db.execute(
                            "INSERT INTO borrow_requests(item_id,borrower_id,expected_return,created_at) VALUES(?,?,?,?)",
                            (item_id, g.member["id"], expected.isoformat(), timestamp()),
                        )
                except sqlite3.IntegrityError:
                    abort(409, description="You already have a pending request for this item. Check My Activity.")
                flash(f"Request sent to {item['owner_name']}. You can follow it in My Activity.", "success")
                return redirect(url_for("activity"), code=303)
        return render_template("request_item.html", item=item, value=value, error=error), (422 if error else 200)

    @app.get("/activity")
    def activity():
        rows = get_db().execute(
            ACTIVITY_QUERY + " WHERE i.owner_id=? OR r.borrower_id=? ORDER BY r.id DESC",
            (g.member["id"], g.member["id"]),
        ).fetchall()
        incoming = [r for r in rows if r["owner_id"] == g.member["id"]]
        outgoing = [r for r in rows if r["borrower_id"] == g.member["id"]]
        return render_template("activity.html", incoming=incoming, outgoing=outgoing,
                               pending_count=sum(r["status"] == "Pending" for r in incoming))

    @app.post("/requests/<int:request_id>/<action>")
    def decide_request(request_id, action):
        transitions = {"approve": ("Pending", "Approved"), "reject": ("Pending", "Rejected"), "return": ("Approved", "Returned")}
        if action not in transitions:
            abort(404)
        required, target = transitions[action]
        with write_transaction() as db:
            row = db.execute(ACTIVITY_QUERY + " WHERE r.id=?", (request_id,)).fetchone()
            if row is None:
                abort(404)
            if row["owner_id"] != g.member["id"]:
                abort(403, description="Only the item owner can approve, reject, or record its return.")
            if row["status"] != required:
                abort(409, description="This request has already changed. Open My Activity to see its current status.")
            if action == "approve":
                if db.execute("SELECT 1 FROM borrow_requests WHERE item_id=? AND status='Approved'", (row["item_id"],)).fetchone():
                    abort(409, description="This item already has an approved borrow.")
            db.execute("UPDATE borrow_requests SET status=? WHERE id=?", (target, request_id))
            if action == "approve":
                db.execute("UPDATE borrow_requests SET status='Rejected' WHERE item_id=? AND id<>? AND status='Pending'", (row["item_id"], request_id))
        messages = {
            "approve": "Request approved. The borrower can now see your demo contact details. Other pending requests for this item were declined.",
            "reject": "Request rejected. Your item is still available.",
            "return": "Return recorded. Your item is available to borrow again.",
        }
        flash(messages[action], "success")
        return redirect(url_for("activity"), code=303)

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return {"status": "ok"}

    @app.errorhandler(sqlite3.OperationalError)
    def database_error(error):
        if "locked" not in str(error).lower():
            raise error
        return render_template("error.html", code=503, message="The demo is saving another change. Please try again in a moment."), 503

    def error_page(error):
        defaults = {404: "We couldn't find that item or page.", 413: "That form is too large. Keep your listing short and try again.", 500: "Something went wrong. Please try again."}
        return render_template("error.html", code=error.code, message=defaults.get(error.code, error.description)), error.code

    for code in (400, 403, 404, 409, 413, 422, 500):
        app.register_error_handler(code, error_page)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5001")), debug=False)

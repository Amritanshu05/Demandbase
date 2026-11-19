"""Campus Commons: discovery, date reservations, owner handover, and borrow chat."""

import os
import secrets
import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for

from booking import (
    ACTIVITY_QUERY, CATEGORIES, COMMUNITY_TZ, CONDITIONS, HISTORY_STATUSES,
    calendar_month, can_read_chat, check_window, expire_requests, find_borrow,
    get_item, has_overdue, is_overdue, overdue_days, parse_window, require_owner,
    require_uncommitted, timestamp, today, write_transaction,
)
from storage import get_db, initialize_database


def listing_values():
    values = {key: request.form.get(key, "").strip() for key in ("name", "description", "category", "condition")}
    error = None
    if not 1 <= len(values["name"]) <= 100:
        error = "Enter an item name between 1 and 100 characters."
    elif not 1 <= len(values["description"]) <= 600:
        error = "Enter a description between 1 and 600 characters."
    elif values["category"] not in CATEGORIES or values["condition"] not in CONDITIONS:
        error = "Choose a category and condition from the available options."
    return values, error


def render_item(item, values=None, error=None, block_values=None, block_error=None, status=200):
    blocks = []
    if item["owner_id"] == g.member["id"]:
        blocks = get_db().execute("SELECT * FROM unavailable_dates WHERE item_id=? ORDER BY start_date,id", (item["id"],)).fetchall()
    if values is None:
        values = {key: request.args.get(key, "") for key in ("start_date", "expected_return")}
    return render_template("item_detail.html", item=item, calendar=calendar_month(item, request.args.get("month")),
                           values=values, error=error, blocks=blocks,
                           block_values=block_values or {}, block_error=block_error), status


def render_conversation(borrow, draft="", error=None, status=200):
    messages = get_db().execute("""SELECT m.*,u.name AS sender_name FROM messages m
        JOIN members u ON u.id=m.sender_id WHERE m.borrow_request_id=? ORDER BY m.created_at,m.id""", (borrow["id"],)).fetchall()
    return render_template("borrow_chat.html", borrow=borrow, messages=messages,
                           draft=draft, error=error, late_risk=has_overdue(borrow["item_id"])), status


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATA_DIR=Path(os.environ.get("COMMONS_DATA_DIR", Path(__file__).parent / "instance")),
        MAX_CONTENT_LENGTH=32 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
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
    initialize_database(app.config["DATABASE"])

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def load_member():
        if request.endpoint == "static":
            return
        db = get_db()
        g.members = db.execute("SELECT * FROM members ORDER BY id").fetchall()
        g.member = next((m for m in g.members if m["id"] == session.get("member_id", 1)), g.members[0])
        session["member_id"] = g.member["id"]
        session.setdefault("csrf", secrets.token_hex(32))
        if request.method == "POST":
            if not secrets.compare_digest(request.form.get("csrf", "").encode(), session["csrf"].encode()):
                abort(403, description="This form has expired. Reload the page and try again.")
        if db.execute("SELECT 1 FROM borrow_requests WHERE status IN ('Pending','Approved') AND expected_return<? LIMIT 1", (today().isoformat(),)).fetchone():
            with write_transaction() as write_db:
                expire_requests(write_db)

    @app.after_request
    def response_headers(response):
        response.headers.update({
            "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "same-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
        })
        return response

    @app.context_processor
    def shared_context():
        return dict(categories=CATEGORIES, conditions=CONDITIONS, today=today(),
                    is_overdue=is_overdue, overdue_days=overdue_days, has_overdue=has_overdue, can_read_chat=can_read_chat)

    @app.template_filter("return_date")
    def return_date(value):
        parsed = date.fromisoformat(value)
        label = f"{parsed.day} {parsed.strftime('%B')}"
        return label if parsed.year == today().year else f"{label} {parsed.year}"

    @app.template_filter("message_time")
    def message_time(value):
        return datetime.fromisoformat(value).astimezone(COMMUNITY_TZ).strftime("%d %b %Y, %H:%M IST")

    @app.get("/")
    def explore():
        query, category = request.args.get("q", "").strip(), request.args.get("category", "")
        if len(query) > 100 or (category and category not in CATEGORIES):
            abort(400, description="Use a search of up to 100 characters and choose a listed category.")
        db = get_db()
        ids = db.execute("""SELECT id FROM items WHERE sharing_state='Listed'
            AND instr(lower(name),lower(?))>0 AND (?='' OR category=?) ORDER BY id DESC""", (query, category, category)).fetchall()
        items = [get_item(row["id"]) for row in ids]
        total = db.execute("SELECT count(*) FROM items WHERE sharing_state='Listed'").fetchone()[0]
        own_count = db.execute("SELECT count(*) FROM items WHERE owner_id=?", (g.member["id"],)).fetchone()[0]
        return render_template("explore.html", items=items, total=total, own_count=own_count, query=query, selected_category=category)

    @app.post("/demo-member")
    def switch_member():
        selected = request.form.get("member_id", type=int)
        if selected not in {m["id"] for m in g.members}:
            abort(400, description="Choose one of the demo members.")
        session["member_id"] = selected
        destination = "dashboard" if request.form.get("next") in ("activity", "dashboard", "chat") else "explore"
        return redirect(url_for(destination), code=303)

    @app.get("/items/new")
    def new_item():
        return render_template("new_item.html", values={}, error=None, item=None)

    @app.post("/items")
    def create_item():
        values, error = listing_values()
        if error:
            return render_template("new_item.html", values=values, error=error, item=None), 422
        with write_transaction() as db:
            cursor = db.execute("""INSERT INTO items(owner_id,name,description,category,condition,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)""", (g.member["id"], values["name"], values["description"], values["category"], values["condition"], timestamp(), timestamp()))
            item_id = cursor.lastrowid
        flash("Your item is listed. Its unreserved dates are ready to request.", "success")
        return redirect(url_for("item_detail", item_id=item_id), code=303)

    @app.get("/items/<int:item_id>")
    def item_detail(item_id):
        return render_item(get_item(item_id))

    @app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
    def edit_item(item_id):
        item = get_item(item_id)
        require_owner(item, g.member["id"])
        require_uncommitted(item)
        if item["sharing_state"] == "Archived":
            abort(409, description="Restore the archived item before editing it.")
        values, error = (listing_values() if request.method == "POST" else (item, None))
        if request.method == "POST" and not error:
            with write_transaction() as db:
                current = get_item(item_id)
                require_owner(current, g.member["id"])
                require_uncommitted(current)
                if current["sharing_state"] == "Archived":
                    abort(409, description="Restore the archived item before editing it.")
                db.execute("UPDATE items SET name=?,description=?,category=?,condition=?,updated_at=? WHERE id=?",
                           (values["name"], values["description"], values["category"], values["condition"], timestamp(), item_id))
            flash("Listing updated. Borrowing history is preserved.", "success")
            return redirect(url_for("item_detail", item_id=item_id), code=303)
        return render_template("new_item.html", values=values, error=error, item=item), (422 if error else 200)

    @app.route("/items/<int:item_id>/sharing-status", methods=["GET", "POST"])
    def sharing_status(item_id):
        item = get_item(item_id)
        require_owner(item, g.member["id"])
        transitions = {"pause": ("Listed", "Paused"), "resume": ("Paused", "Listed"),
                       "archive": (("Listed", "Paused"), "Archived"), "restore": ("Archived", "Listed")}
        action = request.values.get("action", "")
        if action not in transitions:
            abort(400, description="Choose pause, resume, archive, or restore.")
        required, target = transitions[action]
        required = (required,) if isinstance(required, str) else required
        require_uncommitted(item)
        if item["sharing_state"] not in required:
            abort(409, description="This listing has changed. Check its current status in My Dashboard.")
        if request.method == "POST":
            with write_transaction() as db:
                current = get_item(item_id)
                require_uncommitted(current)
                if current["sharing_state"] not in required:
                    abort(409, description="This listing has already changed.")
                db.execute("UPDATE items SET sharing_state=?,updated_at=? WHERE id=?", (target, timestamp(), item_id))
                if action in ("pause", "archive"):
                    db.execute("UPDATE borrow_requests SET status='Rejected',decided_at=?,resolution_reason=? WHERE item_id=? AND status='Pending'",
                               (timestamp(), f"The owner {target.lower()} this listing.", item_id))
            flash(f"Listing {target.lower() if target != 'Listed' else 'available for reservations again'}. History has been kept.", "success")
            return redirect(url_for("dashboard"), code=303)
        pending_count = get_db().execute("SELECT count(*) FROM borrow_requests WHERE item_id=? AND status='Pending'", (item_id,)).fetchone()[0]
        return render_template("sharing_status.html", item=item, action=action, target=target, pending_count=pending_count)

    @app.route("/items/<int:item_id>/unavailable-dates", methods=["GET", "POST"])
    def unavailable_dates(item_id):
        item = get_item(item_id)
        require_owner(item, g.member["id"])
        if request.method == "GET":
            return redirect(url_for("item_detail", item_id=item_id, _anchor="owner-availability"), code=303)
        if item["sharing_state"] == "Archived":
            abort(409, description="Restore the listing before changing its calendar.")
        values = {key: request.form.get(key, "") for key in ("start_date", "end_date")}
        try:
            start, end = parse_window(values["start_date"], values["end_date"])
        except ValueError as error:
            return render_item(item, block_values=values, block_error=str(error), status=422)
        with write_transaction() as db:
            current = get_item(item_id)
            if current["sharing_state"] == "Archived":
                abort(409, description="Restore the listing before changing its calendar.")
            if db.execute("SELECT 1 FROM unavailable_dates WHERE item_id=? AND start_date<=? AND end_date>=?", (item_id, end, start)).fetchone():
                abort(409, description="These dates overlap an existing owner block. Remove it before changing the range.")
            db.execute("INSERT INTO unavailable_dates(item_id,start_date,end_date,created_at) VALUES(?,?,?,?)", (item_id, start, end, timestamp()))
            db.execute("""UPDATE borrow_requests SET status='Rejected',decided_at=?,resolution_reason='The owner marked these dates unavailable.'
                WHERE item_id=? AND status='Pending' AND start_date<=? AND expected_return>=?""", (timestamp(), item_id, end, start))
        flash("Dates marked unavailable. Overlapping pending requests were declined.", "success")
        return redirect(url_for("item_detail", item_id=item_id, month=start[:7], _anchor="owner-availability"), code=303)

    @app.post("/items/<int:item_id>/unavailable-dates/<int:block_id>/remove")
    def remove_unavailable_dates(item_id, block_id):
        with write_transaction() as db:
            item = get_item(item_id)
            require_owner(item, g.member["id"])
            if item["sharing_state"] == "Archived":
                abort(409, description="Restore the listing before changing its calendar.")
            cursor = db.execute("DELETE FROM unavailable_dates WHERE id=? AND item_id=?", (block_id, item_id))
            if not cursor.rowcount:
                abort(404)
        flash("Owner block removed. Other reservations are unchanged.", "success")
        return redirect(url_for("item_detail", item_id=item_id, _anchor="owner-availability"), code=303)

    @app.route("/items/<int:item_id>/request", methods=["GET", "POST"])
    def request_item(item_id):
        item = get_item(item_id)
        if item["owner_id"] == g.member["id"]:
            abort(403, description="This is your item. Choose another demo member to borrow it.")
        if request.method == "GET":
            return redirect(url_for("item_detail", item_id=item_id, _anchor="request-form"), code=303)
        values = {key: request.form.get(key, "") for key in ("start_date", "expected_return")}
        try:
            start, end = parse_window(values["start_date"], values["expected_return"])
        except ValueError as error:
            return render_item(item, values=values, error=str(error), status=422)
        with write_transaction() as db:
            expire_requests(db)
            check_window(item_id, start, end, borrower=g.member["id"])
            db.execute("INSERT INTO borrow_requests(item_id,borrower_id,start_date,expected_return,created_at) VALUES(?,?,?,?,?)",
                       (item_id, g.member["id"], start, end, timestamp()))
        flash(f"Request sent to {item['owner_name']}. Your dates are reserved only after approval.", "success")
        return redirect(url_for("dashboard"), code=303)

    @app.get("/activity")
    def activity():
        return redirect(url_for("dashboard"), code=303)

    @app.get("/dashboard")
    def dashboard():
        db = get_db()
        rows = db.execute(ACTIVITY_QUERY + " WHERE i.owner_id=? OR r.borrower_id=? ORDER BY r.start_date,r.id DESC", (g.member["id"], g.member["id"])).fetchall()
        ids = db.execute("SELECT id FROM items WHERE owner_id=? ORDER BY id DESC", (g.member["id"],)).fetchall()
        owned, archived = [], []
        for row in ids:
            item = get_item(row["id"])
            incoming = [r for r in rows if r["item_id"] == item["id"] and r["owner_id"] == g.member["id"]]
            entry = dict(listing=item, active=next((r for r in incoming if r["status"] == "Active"), None),
                         reservations=[r for r in incoming if r["status"] == "Approved"],
                         pending=[r for r in incoming if r["status"] == "Pending"],
                         history=[r for r in reversed(incoming) if r["status"] in HISTORY_STATUSES])
            (archived if item["sharing_state"] == "Archived" else owned).append(entry)
        outgoing = [r for r in rows if r["borrower_id"] == g.member["id"]]
        borrowing = [r for r in outgoing if r["status"] == "Active"]
        approved = [r for r in outgoing if r["status"] == "Approved"]
        ready = [r for r in approved if r["start_date"] <= today().isoformat()]
        upcoming = [r for r in approved if r["start_date"] > today().isoformat()]
        pending = [r for r in outgoing if r["status"] == "Pending"]
        history = [r for r in reversed(outgoing) if r["status"] in HISTORY_STATUSES]
        return render_template("dashboard.html", owned=owned, archived=archived, borrowing=borrowing,
                               ready=ready, upcoming=upcoming, pending=pending, history=history,
                               owned_count=len(ids), lent_count=sum(bool(e["active"]) for e in owned),
                               pending_count=sum(r["status"] == "Pending" and r["owner_id"] == g.member["id"] for r in rows),
                               overdue_count=sum(is_overdue(r) for r in rows),
                               affected_count=sum(r["status"] == "Approved" and has_overdue(r["item_id"]) for r in rows))

    @app.get("/borrows/<int:request_id>")
    def borrow_chat(request_id):
        return render_conversation(find_borrow(request_id, g.member["id"], chat=True))

    @app.post("/borrows/<int:request_id>/messages")
    def send_message(request_id):
        draft = request.form.get("body", "")
        body, error = draft.strip(), None
        with write_transaction() as db:
            expire_requests(db)
            borrow = find_borrow(request_id, g.member["id"], chat=True)
            if borrow["status"] not in ("Approved", "Active"):
                abort(409, description="This conversation is now read-only.")
            if not 1 <= len(body) <= 1000:
                error = "Enter a message between 1 and 1,000 characters."
            else:
                db.execute("INSERT INTO messages(borrow_request_id,sender_id,body,created_at) VALUES(?,?,?,?)", (request_id, g.member["id"], body, timestamp()))
        if error:
            return render_conversation(borrow, draft=draft, error=error, status=422)
        return redirect(url_for("borrow_chat", request_id=request_id, _anchor="messages-end"), code=303)

    @app.post("/requests/<int:request_id>/<action>")
    def decide_request(request_id, action):
        if action not in ("approve", "reject", "start", "return", "cancel"):
            abort(404)
        with write_transaction() as db:
            expire_requests(db)
            row = find_borrow(request_id, g.member["id"])
            if action == "cancel":
                if row["status"] == "Pending" and g.member["id"] != row["borrower_id"]:
                    abort(403, description="Only the borrower can cancel a pending request; the owner can reject it.")
                if row["status"] not in ("Pending", "Approved"):
                    abort(409, description="Only pending requests or approved reservations before handover can be cancelled.")
                db.execute("UPDATE borrow_requests SET status='Cancelled',cancelled_at=?,resolution_reason=? WHERE id=?", (timestamp(), f"Cancelled by {g.member['name']} before handover.", request_id))
            else:
                if row["owner_id"] != g.member["id"]:
                    abort(403, description="Only the item owner can approve, reject, hand over, or record a return.")
                required = {"approve": "Pending", "reject": "Pending", "start": "Approved", "return": "Active"}[action]
                if row["status"] != required:
                    abort(409, description="This request has changed or this action is not available in its current state. Check My Dashboard.")
                if action == "approve":
                    check_window(row["item_id"], row["start_date"], row["expected_return"], exclude=request_id)
                    db.execute("UPDATE borrow_requests SET status='Approved',approved_at=?,decided_at=? WHERE id=?", (timestamp(), timestamp(), request_id))
                    db.execute("""UPDATE borrow_requests SET status='Rejected',decided_at=?,resolution_reason='Another overlapping request was approved.'
                        WHERE item_id=? AND id<>? AND status='Pending' AND start_date<=? AND expected_return>=?""", (timestamp(), row["item_id"], request_id, row["expected_return"], row["start_date"]))
                elif action == "reject":
                    db.execute("UPDATE borrow_requests SET status='Rejected',decided_at=?,resolution_reason='The owner declined this request.' WHERE id=?", (timestamp(), request_id))
                elif action == "start":
                    if not row["start_date"] <= today().isoformat() <= row["expected_return"]:
                        abort(409, description="Handover can be recorded only during the reserved date range.")
                    if db.execute("SELECT 1 FROM borrow_requests WHERE item_id=? AND status='Active'", (row["item_id"],)).fetchone():
                        abort(409, description="The earlier borrower has not returned this item. Confirm its return before another handover.")
                    if get_item(row["item_id"])["sharing_state"] != "Listed":
                        abort(409, description="Restore or resume this listing before handover.")
                    db.execute("UPDATE borrow_requests SET status='Active',handed_over_at=? WHERE id=?", (timestamp(), request_id))
                elif action == "return":
                    db.execute("UPDATE borrow_requests SET status='Returned',returned_at=? WHERE id=?", (timestamp(), request_id))
        flash({"approve": "Reservation approved. Only overlapping pending requests were declined. Open chat to arrange handover.",
               "reject": "Request rejected. Other reservations are unchanged.",
               "start": "Handover recorded. This item is now actively lent out.",
               "return": "Return confirmed. Remaining dates are released; future reservations are kept.",
               "cancel": "Request cancelled. Reserved dates are released and history is kept."}[action], "success")
        return redirect(url_for("dashboard"), code=303)

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return {"status": "ok"}

    @app.errorhandler(sqlite3.IntegrityError)
    def integrity_error(_error):
        return render_template("error.html", code=409, message="These dates conflict with another reservation, owner block, or active handover. Refresh the calendar and try again."), 409

    @app.errorhandler(sqlite3.OperationalError)
    def database_error(error):
        if "locked" not in str(error).lower():
            raise error
        return render_template("error.html", code=503, message="The demo is saving another change. Please retry in a moment."), 503

    def error_page(error):
        defaults = {404: "We couldn't find that item or page.", 413: "That form is too large. Keep your text short and retry.", 500: "Something went wrong. Please try again."}
        return render_template("error.html", code=error.code, message=defaults.get(error.code, error.description)), error.code

    for code in (400, 403, 404, 409, 413, 422, 500):
        app.register_error_handler(code, error_page)
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5001")), debug=False)

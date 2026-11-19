"""Date-range availability and borrowing rules for the local demo."""

import calendar
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import abort, current_app

from storage import get_db

CATEGORIES = {"Sports": "sports", "Electronics": "electronics", "Books": "books",
              "Tools": "tools", "Outdoors": "outdoors", "Other": "other"}
CONDITIONS = ("Like new", "Good", "Fair")
COMMUNITY_TZ = ZoneInfo("Asia/Kolkata")
OPEN_STATUSES = ("Approved", "Active")
HISTORY_STATUSES = ("Returned", "Rejected", "Cancelled", "Expired")
ACTIVITY_QUERY = """SELECT r.*, i.name AS item_name, i.owner_id, i.category,
    o.name AS owner_name, o.email AS owner_email, b.name AS borrower_name
    FROM borrow_requests r JOIN items i ON i.id=r.item_id
    JOIN members o ON o.id=i.owner_id JOIN members b ON b.id=r.borrower_id"""


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def today():
    return current_app.config.get("TODAY") or datetime.now(COMMUNITY_TZ).date()


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


def expire_requests(db):
    db.execute("""UPDATE borrow_requests SET status='Expired', expired_at=?,
        resolution_reason='The requested period ended without handover.'
        WHERE status IN ('Pending','Approved') AND expected_return<?""", (timestamp(), today().isoformat()))


def parse_window(start, end):
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first.isoformat() != start or last.isoformat() != end or first < today() or last < first:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("Choose a start date of today or later and a return date on or after it.")
    return first.isoformat(), last.isoformat()


def is_overdue(borrow):
    return borrow["status"] == "Active" and borrow["expected_return"] < today().isoformat()


def overdue_days(borrow):
    return max(0, (today() - date.fromisoformat(borrow["expected_return"])).days)


def has_overdue(item_id):
    return bool(get_db().execute("SELECT 1 FROM borrow_requests WHERE item_id=? AND status='Active' AND expected_return<?",
                                 (item_id, today().isoformat())).fetchone())


def get_item(item_id):
    row = get_db().execute("SELECT i.*,m.name AS owner_name FROM items i JOIN members m ON m.id=i.owner_id WHERE i.id=?", (item_id,)).fetchone()
    if row is None:
        abort(404)
    item = dict(row)
    db = get_db()
    active = db.execute("SELECT * FROM borrow_requests WHERE item_id=? AND status='Active'", (item_id,)).fetchone()
    now = today().isoformat()
    reserved = db.execute("SELECT 1 FROM borrow_requests WHERE item_id=? AND status='Approved' AND start_date<=? AND expected_return>=?", (item_id, now, now)).fetchone()
    blocked = db.execute("SELECT 1 FROM unavailable_dates WHERE item_id=? AND start_date<=? AND end_date>=?", (item_id, now, now)).fetchone()
    item["overdue"] = bool(active and is_overdue(active))
    item["availability"] = (item["sharing_state"] if item["sharing_state"] != "Listed" else
                            "Return overdue" if item["overdue"] else "Lent Out" if active else
                            "Reserved today" if reserved else "Owner unavailable today" if blocked else "Available now")
    item["committed"] = bool(db.execute("SELECT 1 FROM borrow_requests WHERE item_id=? AND status IN ('Approved','Active')", (item_id,)).fetchone())
    return item


def require_owner(item, actor):
    if item["owner_id"] != actor:
        abort(403, description="Only the item owner can manage this listing.")


def require_uncommitted(item):
    if item["committed"]:
        abort(409, description="Cancel approved reservations or record the active return before editing, pausing, or archiving this item.")


def check_window(item_id, start, end, borrower=None, exclude=None):
    item = get_item(item_id)
    if item["sharing_state"] != "Listed":
        abort(409, description=f"This listing is {item['sharing_state'].lower()} and is not accepting requests.")
    if item["overdue"]:
        abort(409, description="New reservations are paused until the owner confirms the overdue item has returned. Existing approvals are retained.")
    rows = get_db().execute("""SELECT * FROM borrow_requests WHERE item_id=?
        AND start_date<=? AND expected_return>=? AND (? IS NULL OR id<>?)""", (item_id, end, start, exclude, exclude)).fetchall()
    if any(r["status"] in OPEN_STATUSES for r in rows):
        abort(409, description="These dates overlap an approved reservation or active borrow. Please check the calendar again.")
    if borrower is not None and any(r["borrower_id"] == borrower and r["status"] == "Pending" for r in rows):
        abort(409, description="You already have a pending request overlapping these dates. Check My Dashboard.")
    if get_db().execute("SELECT 1 FROM unavailable_dates WHERE item_id=? AND start_date<=? AND end_date>=?", (item_id, end, start)).fetchone():
        abort(409, description="The owner has marked these dates unavailable.")


def can_read_chat(borrow):
    return borrow["status"] in ("Approved", "Active", "Returned") or (
        borrow["status"] in ("Cancelled", "Expired") and borrow["approved_at"] is not None)


def find_borrow(request_id, actor, chat=False):
    borrow = get_db().execute(ACTIVITY_QUERY + " WHERE r.id=?", (request_id,)).fetchone()
    if borrow is None:
        abort(404)
    if actor not in (borrow["owner_id"], borrow["borrower_id"]):
        abort(403, description="Only this borrow's owner and borrower can access it.")
    if chat and not can_read_chat(borrow):
        abort(409, description="Chat becomes available after a request has been approved.")
    return borrow


def calendar_month(item, value=None):
    try:
        month = date.fromisoformat((value or today().strftime("%Y-%m")) + "-01")
        if not 2 <= month.year <= 9998:
            raise ValueError
    except ValueError:
        abort(400, description="Choose a valid calendar month in YYYY-MM format.")
    previous = (month - timedelta(days=1)).strftime("%Y-%m")
    following = (month.replace(day=28) + timedelta(days=4)).replace(day=1).strftime("%Y-%m")
    last = month.replace(day=calendar.monthrange(month.year, month.month)[1])
    db = get_db()
    reservations = db.execute("SELECT start_date,expected_return,status FROM borrow_requests WHERE item_id=? AND status IN ('Approved','Active') AND start_date<=? AND expected_return>=?", (item["id"], last.isoformat(), month.isoformat())).fetchall()
    blocks = db.execute("SELECT start_date,end_date FROM unavailable_dates WHERE item_id=? AND start_date<=? AND end_date>=?", (item["id"], last.isoformat(), month.isoformat())).fetchall()
    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(month.year, month.month):
        cells = []
        for day in week:
            iso = day.isoformat()
            held = next((r for r in reservations if r["start_date"] <= iso <= r["expected_return"]), None)
            blocked = any(b["start_date"] <= iso <= b["end_date"] for b in blocks)
            label, state = "Available", "available"
            if item["sharing_state"] != "Listed":
                label, state = item["sharing_state"], "blocked"
            elif item["overdue"] and day >= today():
                label, state = ("Reserved · late-return risk" if held else "Reservations paused"), "overdue"
            elif held:
                label, state = ("Lent Out", "active") if held["status"] == "Active" else ("Reserved", "reserved")
            elif blocked:
                label, state = "Owner unavailable", "blocked"
            cells.append(dict(date=iso, day=day.day, label=label, state=state,
                              outside=day.month != month.month,
                              disabled=day < today() or day.month != month.month or state != "available"))
        weeks.append(cells)
    return dict(label=month.strftime("%B %Y"), value=month.strftime("%Y-%m"),
                previous=previous, following=following, weeks=weeks)

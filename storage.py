"""SQLite schema, safe legacy upgrade, and one-time demo seed data."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import current_app, g


REQUEST_TABLE = """CREATE TABLE IF NOT EXISTS borrow_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL REFERENCES items(id),
    borrower_id INTEGER NOT NULL REFERENCES members(id),
    start_date TEXT NOT NULL CHECK(length(start_date)=10),
    expected_return TEXT NOT NULL CHECK(length(expected_return)=10 AND expected_return>=start_date),
    status TEXT NOT NULL DEFAULT 'Pending'
        CHECK(status IN ('Pending','Approved','Active','Rejected','Cancelled','Returned','Expired')),
    created_at TEXT NOT NULL,
    approved_at TEXT, decided_at TEXT, handed_over_at TEXT,
    returned_at TEXT, cancelled_at TEXT, expired_at TEXT, resolution_reason TEXT
)"""
TABLES = [
    "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE)",
    """CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL REFERENCES members(id),
        name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 100),
        category TEXT NOT NULL CHECK(category IN ('Sports','Electronics','Books','Tools','Outdoors','Other')),
        description TEXT NOT NULL CHECK(length(trim(description)) BETWEEN 1 AND 600),
        condition TEXT NOT NULL CHECK(condition IN ('Like new','Good','Fair')),
        sharing_state TEXT NOT NULL DEFAULT 'Listed' CHECK(sharing_state IN ('Listed','Paused','Archived')),
        created_at TEXT NOT NULL, updated_at TEXT
    )""",
    REQUEST_TABLE,
    """CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        borrow_request_id INTEGER NOT NULL REFERENCES borrow_requests(id),
        sender_id INTEGER NOT NULL REFERENCES members(id),
        body TEXT NOT NULL CHECK(length(trim(body)) BETWEEN 1 AND 1000), created_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS unavailable_dates (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL REFERENCES items(id),
        start_date TEXT NOT NULL CHECK(length(start_date)=10),
        end_date TEXT NOT NULL CHECK(length(end_date)=10 AND end_date>=start_date),
        created_at TEXT NOT NULL
    )""",
]
INDEXES = [
    "CREATE UNIQUE INDEX IF NOT EXISTS one_active_per_item ON borrow_requests(item_id) WHERE status='Active'",
    "CREATE UNIQUE INDEX IF NOT EXISTS pending_window ON borrow_requests(item_id,borrower_id,start_date,expected_return) WHERE status='Pending'",
    "CREATE INDEX IF NOT EXISTS requests_item_window ON borrow_requests(item_id,status,start_date,expected_return)",
    "CREATE INDEX IF NOT EXISTS requests_borrower ON borrow_requests(borrower_id)",
    "CREATE INDEX IF NOT EXISTS messages_borrow_order ON messages(borrow_request_id,created_at,id)",
    "CREATE INDEX IF NOT EXISTS unavailable_item_window ON unavailable_dates(item_id,start_date,end_date)",
]


def constraint_triggers():
    statements = []
    for event in ("INSERT", "UPDATE"):
        exclude_self = "AND r.id<>NEW.id" if event == "UPDATE" else ""
        statements.append(f"""CREATE TRIGGER IF NOT EXISTS reservations_no_overlap_{event.lower()}
            BEFORE {event} ON borrow_requests WHEN NEW.status IN ('Approved','Active') BEGIN
            SELECT RAISE(ABORT,'Reservation dates overlap') WHERE EXISTS (
                SELECT 1 FROM borrow_requests r WHERE r.item_id=NEW.item_id {exclude_self}
                AND r.status IN ('Approved','Active') AND r.start_date<=NEW.expected_return
                AND r.expected_return>=NEW.start_date);
            SELECT RAISE(ABORT,'Owner unavailable on these dates') WHERE EXISTS (
                SELECT 1 FROM unavailable_dates b WHERE b.item_id=NEW.item_id
                AND b.start_date<=NEW.expected_return AND b.end_date>=NEW.start_date);
            END""")
        statements.append(f"""CREATE TRIGGER IF NOT EXISTS blocks_no_reservations_{event.lower()}
            BEFORE {event} ON unavailable_dates BEGIN
            SELECT RAISE(ABORT,'Existing reservation on these dates') WHERE EXISTS (
                SELECT 1 FROM borrow_requests r WHERE r.item_id=NEW.item_id
                AND r.status IN ('Approved','Active') AND r.start_date<=NEW.end_date
                AND r.expected_return>=NEW.start_date);
            END""")
    return statements


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=5)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def seed(db):
    if db.execute("SELECT 1 FROM metadata WHERE key='seed_version'").fetchone():
        return
    now = datetime.now(timezone.utc).isoformat()
    db.executemany("INSERT INTO members(id,name,email) VALUES(?,?,?)", [
        (1, "Amritanshu", "amritanshu@example.com"), (2, "Rahul", "rahul@example.com"),
        (3, "Priya", "priya@example.com"),
    ])
    items = [
        (2, "Cricket Bat", "Sports", "A trusty willow bat for a friendly match. Best with a tennis ball.", "Good"),
        (3, "Mini Projector", "Electronics", "Make movie night a little bigger. HDMI cable and remote included.", "Like new"),
        (1, "Cordless Drill", "Tools", "For that small DIY project. Includes a charged battery and a basic bit set.", "Good"),
        (3, "The Design of Everyday Things", "Books", "A well-loved copy for curious minds. Please keep the bookmarks inside.", "Fair"),
        (2, "Camping Tent", "Outdoors", "A two-person tent for a weekend under the stars. Pegs and carry bag included.", "Good"),
        (1, "Badminton Set", "Sports", "Two rackets and a few shuttlecocks. All you need is a court and a friend.", "Good"),
    ]
    db.executemany("INSERT INTO items(owner_id,name,category,description,condition,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                   [(*item, now, now) for item in items])
    db.execute("INSERT INTO metadata VALUES('seed_version','1')")


def initialize_database(path):
    """Upgrade before serving requests; preserve child references and original IDs."""
    path = Path(path)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    columns = {r["name"] for r in db.execute("PRAGMA table_info(borrow_requests)")}
    legacy = bool(columns) and "start_date" not in columns
    try:
        if legacy:
            backup_dir = path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            with closing(sqlite3.connect(backup_dir / f"commons-before-calendar-{suffix}.sqlite3")) as backup:
                db.backup(backup)
        # SQLite requires changing this PRAGMA outside the rebuild transaction.
        db.execute("PRAGMA foreign_keys=OFF" if legacy else "PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        if legacy:
            old_sequence = db.execute("SELECT seq FROM sqlite_sequence WHERE name='borrow_requests'").fetchone()
            db.execute("ALTER TABLE items ADD COLUMN sharing_state TEXT NOT NULL DEFAULT 'Listed' CHECK(sharing_state IN ('Listed','Paused','Archived'))")
            db.execute("ALTER TABLE items ADD COLUMN updated_at TEXT")
            db.execute("UPDATE items SET updated_at=created_at")
            db.execute(REQUEST_TABLE.replace("borrow_requests", "new_borrow_requests", 1))
            old_rows = db.execute("SELECT * FROM borrow_requests ORDER BY id").fetchall()
            for row in old_rows:
                created = datetime.fromisoformat(row["created_at"])
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                start = created.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat()
                db.execute("""INSERT INTO new_borrow_requests
                    (id,item_id,borrower_id,start_date,expected_return,status,created_at)
                    VALUES(?,?,?,?,?,?,?)""", (row["id"], row["item_id"], row["borrower_id"], start,
                    row["expected_return"], "Active" if row["status"] == "Approved" else row["status"], row["created_at"]))
            # Do not rename the old parent first: child FK definitions must keep its original name.
            db.execute("DROP TABLE borrow_requests")
            db.execute("ALTER TABLE new_borrow_requests RENAME TO borrow_requests")
            if old_sequence:
                db.execute("UPDATE sqlite_sequence SET seq=max(seq,?) WHERE name='borrow_requests'", (old_sequence[0],))
        for statement in TABLES + INDEXES + constraint_triggers():
            db.execute(statement)
        seed(db)
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Database migration failed its foreign-key check; original data has been retained.")
        db.execute("INSERT OR REPLACE INTO metadata VALUES('schema_version','1')")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.execute("PRAGMA foreign_keys=ON")
        db.close()

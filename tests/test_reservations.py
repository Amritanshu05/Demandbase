"""Scheduling and listing controls: focused checks against real temporary SQLite."""

import sqlite3
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Barrier

from app import create_app, get_db
from test_lifecycle import BorrowingTestCase


class ReservationTests(BorrowingTestCase):
    def reserve(self, member, start, end, item=1):
        self.switch(member)
        result = self.post(f'/items/{item}/request', start_date=start, expected_return=end)
        self.assertEqual(result.status_code, 303, result.get_data(as_text=True)[:300])
        with self.app.app_context():
            return get_db().execute('SELECT max(id) FROM borrow_requests').fetchone()[0]

    def approve(self, request_id):
        self.switch(2)
        self.assertEqual(self.post(f'/requests/{request_id}/approve').status_code, 303)

    def test_disjoint_ranges_and_inclusive_overlap(self):
        first = self.reserve(1, '2026-12-01', '2026-12-10')
        clash = self.reserve(3, '2026-12-05', '2026-12-08')
        later = self.reserve(3, '2026-12-20', '2026-12-25')
        self.approve(first)
        self.assertEqual(self.states(), ['Approved', 'Rejected', 'Pending'])
        self.assertEqual(self.post(f'/requests/{later}/approve').status_code, 303)
        self.switch(1)
        self.assertEqual(self.post('/items/1/request', start_date='2026-12-10', expected_return='2026-12-12').status_code, 409)
        adjacent = self.reserve(1, '2026-12-11', '2026-12-19')
        self.approve(adjacent)
        self.assertEqual(self.states(), ['Approved', 'Rejected', 'Approved', 'Approved'])
        self.assertEqual(self.post(f'/requests/{clash}/approve').status_code, 409)
        # Direct database writes cannot bypass the overlap guard.
        with self.app.app_context():
            db = get_db()
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'overlap'):
                db.execute("INSERT INTO borrow_requests(item_id,borrower_id,start_date,expected_return,status,created_at) VALUES(1,3,'2026-12-10','2026-12-12','Approved','2026-11-19T00:00:00+00:00')")
            db.rollback()
        self.assertIn(b'Cricket Bat', self.client.get('/').data)
        html = self.client.get('/items/1?month=2026-12').get_data(as_text=True)
        self.assertIn('2026-12-01: Reserved', html)
        self.assertIn('2026-12-20: Reserved', html)
        calendar_only = html.split('class="calendar-grid"')[1].split('</section>')[0]
        self.assertNotIn('Amritanshu', calendar_only)
        self.assertNotIn('Priya', calendar_only)

    def test_concurrent_approval_has_one_winner(self):
        first = self.reserve(1, '2026-12-01', '2026-12-10')
        other = self.reserve(3, '2026-12-05', '2026-12-15')
        barrier = Barrier(2)

        def approve_concurrently(request_id):
            client = self.app.test_client()
            client.get('/health')
            with client.session_transaction() as state:
                state['member_id'] = 2
                token = state['csrf']
            barrier.wait(timeout=5)
            return client.post(f'/requests/{request_id}/approve', data={'csrf': token}).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(approve_concurrently, [first, other]))
        self.assertEqual(sorted(results), [303, 409])
        self.assertEqual(sorted(self.states()), ['Approved', 'Rejected'])

    def test_handover_late_return_and_early_release(self):
        first = self.reserve(1, '2026-11-19', '2026-11-20')
        self.approve(first)
        self.switch(1)
        self.assertEqual(self.post(f'/requests/{first}/start').status_code, 403)
        self.assertEqual(self.post(f'/requests/{first}/return').status_code, 403)
        self.switch(2)
        self.assertEqual(self.post(f'/requests/{first}/start').status_code, 303)
        later = self.reserve(3, '2026-11-21', '2026-11-23')
        self.approve(later)
        self.assertEqual(self.post(f'/requests/{later}/start').status_code, 409)
        self.app.config['TODAY'] = date(2026, 11, 21)
        html = self.client.get('/dashboard').get_data(as_text=True)
        self.assertIn('overdue', html)
        self.assertIn('affected by an earlier late return', html)
        self.assertEqual(self.states(), ['Active', 'Approved'])
        self.assertEqual(self.post(f'/requests/{later}/start').status_code, 409)
        self.switch(1)
        self.assertEqual(self.post('/items/1/request', start_date='2026-11-24', expected_return='2026-11-25').status_code, 409)
        self.switch(2)
        with self.app.app_context():
            db = get_db()
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE borrow_requests SET status='Active' WHERE id=?", (later,))
            db.rollback()
        self.assertEqual(self.post(f'/requests/{first}/return').status_code, 303)
        self.assertEqual(self.post(f'/requests/{later}/start').status_code, 303)
        self.assertEqual(self.post(f'/requests/{later}/cancel').status_code, 409)
        self.assertEqual(self.post(f'/requests/{later}/return').status_code, 303)
        self.assertEqual(self.post(f'/requests/{later}/return').status_code, 409)
        # Returned early on the 21st: the remainder is immediately requestable.
        self.reserve(1, '2026-11-21', '2026-11-22')

    def test_cancellation_expiry_and_closed_chat(self):
        first = self.reserve(1, '2026-12-01', '2026-12-10')
        self.switch(2)
        self.assertEqual(self.post(f'/requests/{first}/cancel').status_code, 403)
        self.switch(1)
        self.assertEqual(self.post(f'/requests/{first}/cancel').status_code, 303)
        self.assertEqual(self.client.get(f'/borrows/{first}').status_code, 409)
        later = self.reserve(1, '2026-12-01', '2026-12-10')
        self.approve(later)
        self.assertEqual(self.post(f'/requests/{later}/start').status_code, 409)
        self.switch(1)
        self.assertEqual(self.post(f'/requests/{later}/cancel').status_code, 303)
        self.assertIn(b'read-only', self.client.get(f'/borrows/{later}').data)
        self.assertEqual(self.post(f'/borrows/{later}/messages', body='closed').status_code, 409)
        expiring = self.reserve(3, '2026-11-19', '2026-11-20')
        self.approve(expiring)
        pending = self.reserve(1, '2026-11-19', '2026-11-20', item=2)
        self.app.config['TODAY'] = date(2026, 11, 21)
        self.client.get('/dashboard')
        self.assertEqual(self.states(), ['Cancelled', 'Cancelled', 'Expired', 'Expired'])
        self.switch(2)
        self.assertEqual(self.post(f'/requests/{expiring}/start').status_code, 409)
        self.assertIn(b'read-only', self.client.get(f'/borrows/{expiring}').data)
        self.switch(1)
        self.assertEqual(self.client.get(f'/borrows/{pending}').status_code, 409)

    def test_owner_blocks_edit_pause_archive_restore_and_search(self):
        first = self.reserve(1, '2026-12-01', '2026-12-10')
        self.assertEqual(self.client.get('/items/1/edit').status_code, 403)
        self.assertEqual(self.post('/items/1/unavailable-dates', start_date='2026-12-01', end_date='2026-12-05').status_code, 403)
        self.switch(2)
        self.assertEqual(self.post('/items/1/unavailable-dates', start_date='2026-12-01', end_date='2026-12-05').status_code, 303)
        self.assertEqual(self.states(), ['Rejected'])
        with self.app.app_context():
            block = get_db().execute('SELECT id FROM unavailable_dates').fetchone()[0]
        self.switch(1)
        self.assertEqual(self.post('/items/1/request', start_date='2026-12-05', expected_return='2026-12-06').status_code, 409)
        self.switch(2)
        self.assertEqual(self.post(f'/items/1/unavailable-dates/{block}/remove').status_code, 303)
        self.assertEqual(self.post('/items/1/edit', name='Match Bat', category='Sports', condition='Good', description='Updated description.', owner_id=3).status_code, 303)
        response = self.client.get('/?q=MATCH&category=Sports').get_data(as_text=True)
        self.assertIn('Match Bat', response)
        self.assertNotIn('Mini Projector', response)
        self.assertIn(b'No items match', self.client.get('/?q=MATCH&category=Books').data)
        second = self.reserve(1, '2026-12-01', '2026-12-10')
        self.approve(second)
        self.assertEqual(self.post('/items/1/unavailable-dates', start_date='2026-12-03', end_date='2026-12-04').status_code, 409)
        self.assertEqual(self.client.get('/items/1/edit').status_code, 409)
        self.assertEqual(self.post('/items/1/sharing-status', action='pause').status_code, 409)
        self.assertEqual(self.post(f'/requests/{second}/cancel').status_code, 303)
        third = self.reserve(3, '2026-12-01', '2026-12-10')
        self.switch(2)
        self.assertIn(b'pending request', self.client.get('/items/1/sharing-status?action=pause').data)
        self.assertEqual(self.post('/items/1/sharing-status', action='pause').status_code, 303)
        self.assertEqual(self.states(), ['Rejected', 'Cancelled', 'Rejected'])
        self.assertNotIn(b'Match Bat', self.client.get('/').data)
        self.switch(1)
        self.assertEqual(self.post('/items/1/request', start_date='2026-12-20', expected_return='2026-12-25').status_code, 409)
        self.switch(2)
        self.assertEqual(self.post('/items/1/sharing-status', action='resume').status_code, 303)
        self.assertEqual(self.post('/items/1/sharing-status', action='archive').status_code, 303)
        self.assertEqual(self.client.get('/items/1/edit').status_code, 409)
        self.assertIn(b'Archived items', self.client.get('/dashboard').data)
        self.assertEqual(self.post('/items/1/sharing-status', action='restore').status_code, 303)
        self.assertIn(b'Match Bat', self.client.get('/').data)
        self.assertEqual(self.states(), ['Rejected', 'Cancelled', 'Rejected'])
        self.assertEqual(self.post(f'/requests/{first}/approve').status_code, 409)
        self.assertEqual(self.post(f'/requests/{third}/approve').status_code, 409)

    def test_invalid_windows_and_cross_month_calendar(self):
        for start, end in [('', '2026-12-01'), ('2026-11-18', '2026-11-20'),
                           ('2026-12-10', '2026-12-09'), ('2026-02-30', '2026-12-01'),
                           ('20261201', '2026-12-02')]:
            self.assertEqual(self.post('/items/1/request', start_date=start, expected_return=end).status_code, 422)
        self.assertEqual(self.client.get('/items/1?month=invalid').status_code, 400)
        self.assertEqual(self.client.get('/?category=not-real').status_code, 400)
        self.assertIn(b'No items match', self.client.get('/?q=%25').data)
        self.reserve(1, '2026-12-30', '2027-01-03')
        self.approve(1)
        self.assertIn(b'2027-01-01: Reserved', self.client.get('/items/1?month=2027-01').data)
        self.assertIn(b'2026-12-31: Reserved', self.client.get('/items/1?month=2026-12').data)


class LegacyMigrationTests(BorrowingTestCase):
    def test_legacy_backup_preservation_and_failure_rollback(self):
        for invalid in (False, True):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'commons.sqlite3'
                key = Path(directory) / 'secret.key'
                key.write_text('test-only-legacy-signing-key')
                db = sqlite3.connect(path)
                db.executescript('''
                    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                    INSERT INTO metadata VALUES('seed_version','1');
                    CREATE TABLE members(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE);
                    INSERT INTO members VALUES(1,'Amritanshu','amritanshu@example.com'),(2,'Rahul','rahul@example.com'),(3,'Priya','priya@example.com');
                    CREATE TABLE items(id INTEGER PRIMARY KEY AUTOINCREMENT,owner_id INTEGER REFERENCES members(id),name TEXT,category TEXT,description TEXT,condition TEXT,created_at TEXT);
                    INSERT INTO items VALUES(1,2,'Legacy Bat','Sports','Keep this item.','Good','2026-11-19T00:00:00+00:00');
                    CREATE TABLE borrow_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,item_id INTEGER REFERENCES items(id),borrower_id INTEGER REFERENCES members(id),expected_return TEXT,status TEXT CHECK(status IN ('Pending','Approved','Rejected','Returned')),created_at TEXT);
                    INSERT INTO borrow_requests VALUES(41,1,1,'2026-11-22','Approved','2026-11-19T00:00:00+00:00');
                    CREATE UNIQUE INDEX one_approved_per_item ON borrow_requests(item_id) WHERE status='Approved';
                    CREATE UNIQUE INDEX one_pending_per_borrower ON borrow_requests(item_id,borrower_id) WHERE status='Pending';
                    CREATE TABLE messages(id INTEGER PRIMARY KEY AUTOINCREMENT,borrow_request_id INTEGER REFERENCES borrow_requests(id),sender_id INTEGER REFERENCES members(id),body TEXT,created_at TEXT);
                    INSERT INTO messages VALUES(73,41,1,'Keep this conversation.','2026-11-19T01:00:00+00:00');
                ''')
                if invalid:
                    db.execute('UPDATE messages SET sender_id=999')
                db.commit()
                db.close()
                config = {'TESTING': True, 'DATA_DIR': directory, 'TODAY': date(2026, 11, 19)}
                if invalid:
                    with self.assertRaisesRegex(RuntimeError, 'foreign-key'):
                        create_app(config)
                    with sqlite3.connect(path) as original:
                        self.assertNotIn('start_date', [r[1] for r in original.execute('PRAGMA table_info(borrow_requests)')])
                        self.assertEqual(original.execute('SELECT status FROM borrow_requests WHERE id=41').fetchone()[0], 'Approved')
                        self.assertNotIn('sharing_state', [r[1] for r in original.execute('PRAGMA table_info(items)')])
                else:
                    app = create_app(config)
                    self.assertEqual(app.secret_key, 'test-only-legacy-signing-key')
                    with app.app_context():
                        upgraded = get_db()
                        row = upgraded.execute('SELECT * FROM borrow_requests WHERE id=41').fetchone()
                        self.assertEqual(row['status'], 'Active')
                        self.assertEqual(row['start_date'], '2026-11-19')
                        self.assertIsNone(row['handed_over_at'])
                        self.assertEqual(upgraded.execute('SELECT body FROM messages WHERE id=73').fetchone()[0], 'Keep this conversation.')
                        self.assertEqual(upgraded.execute('SELECT count(*) FROM items').fetchone()[0], 1)
                        self.assertEqual(upgraded.execute('PRAGMA foreign_key_check').fetchall(), [])
                    client = app.test_client()
                    self.assertIn(b'Keep this conversation.', client.get('/borrows/41').data)
                    create_app(config)
                backups = list((Path(directory) / 'backups').glob('*.sqlite3'))
                self.assertEqual(len(backups), 1)
                with sqlite3.connect(backups[0]) as backup:
                    self.assertEqual(backup.execute('SELECT status FROM borrow_requests WHERE id=41').fetchone()[0], 'Approved')
                    self.assertEqual(backup.execute('SELECT count(*) FROM messages').fetchone()[0], 1)

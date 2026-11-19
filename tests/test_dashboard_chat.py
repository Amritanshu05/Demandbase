"""Focused dashboard, chat authorization, and upgrade integration checks."""

import sqlite3

from app import create_app, get_db
from test_lifecycle import BorrowingTestCase


class DashboardChatTests(BorrowingTestCase):
    def test_dashboard_inventory_tracks_pending_lent_and_returned(self):
        self.assertEqual(self.client.get('/activity').status_code, 303)
        html = self.client.get('/dashboard').get_data(as_text=True)
        self.assertIn('My Dashboard', html)
        self.assertIn('Cordless Drill', html)
        self.assertIn('Badminton Set', html)
        self.assertIn('Available', html)
        self.assertNotIn('Mini Projector', html)

        self.post('/items/1/request', expected_return='2026-11-22')
        self.switch(2)
        html = self.client.get('/dashboard').get_data(as_text=True)
        self.assertIn('Cricket Bat', html)
        self.assertIn('Amritanshu', html)
        self.assertIn('Approve request', html)
        self.post('/requests/1/approve')
        html = self.client.get('/dashboard').get_data(as_text=True)
        self.assertIn('Lent Out', html)
        self.assertIn('22 November', html)
        self.assertIn('/borrows/1', html)
        self.switch(1)
        html = self.client.get('/dashboard').get_data(as_text=True)
        self.assertIn('Actively borrowing', html)
        self.assertIn('Cricket Bat', html)
        self.assertIn('Rahul', html)
        self.switch(2)
        self.post('/requests/1/return')
        html = self.client.get('/dashboard').get_data(as_text=True)
        self.assertNotIn('Lent Out</span>', html)
        self.assertIn('View conversation', html)
        self.switch(1)
        html = self.client.get('/dashboard').get_data(as_text=True)
        self.assertIn('Past requests', html)
        self.assertIn('Returned', html)

    def test_chat_participants_validation_return_history_and_persistence(self):
        self.post('/items/1/request', expected_return='2026-11-22')
        self.assertEqual(self.client.get('/borrows/1').status_code, 409)
        self.assertEqual(self.post('/borrows/1/messages', body='Too early').status_code, 409)
        self.switch(2)
        self.post('/requests/1/approve')
        self.assertEqual(self.client.get('/borrows/1').status_code, 200)
        for body in ('  \n ', 'a' * 1001):
            response = self.post('/borrows/1/messages', body=body)
            self.assertEqual(response.status_code, 422)
            self.assertIn('Enter a message between 1 and 1,000 characters.', response.get_data(as_text=True))
            self.assertIn(body, response.get_data(as_text=True))
        response = self.post('/borrows/1/messages', body='  Hello <script>alert(1)</script>\nMeet at the campus cafe?  ', sender_id=3)
        self.assertEqual(response.status_code, 303)
        self.switch(1)
        self.assertEqual(self.post('/borrows/1/messages', body='Yes, thanks!').status_code, 303)
        html = self.client.get('/borrows/1').get_data(as_text=True)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertLess(html.index('Meet at the campus cafe?'), html.index('Yes, thanks!'))
        self.assertEqual(self.client.post('/borrows/1/messages', data={'body': 'No token'}).status_code, 403)
        self.switch(3)
        self.assertEqual(self.client.get('/borrows/1').status_code, 403)
        self.assertEqual(self.post('/borrows/1/messages', body='Not my borrow').status_code, 403)
        self.switch(2)
        self.assertEqual(self.post('/demo-member', member_id=1, next='chat').location, '/dashboard')
        self.switch(2)
        self.post('/requests/1/return')
        for member in (1, 2):
            self.switch(member)
            html = self.client.get('/borrows/1').get_data(as_text=True)
            self.assertIn('read-only', html)
            self.assertIn('Yes, thanks!', html)
            self.assertNotIn('name="body"', html)
            self.assertEqual(self.post('/borrows/1/messages', body='Stale composer').status_code, 409)
        restarted = create_app(self.config)
        with restarted.app_context():
            rows = get_db().execute('SELECT sender_id,body FROM messages ORDER BY id').fetchall()
            self.assertEqual([r['sender_id'] for r in rows], [2, 1])
            self.assertTrue(rows[0]['body'].startswith('Hello'))

        self.switch(1)
        self.post('/items/1/request', expected_return='2026-11-23')
        self.switch(2)
        self.post('/requests/2/reject')
        self.assertEqual(self.client.get('/borrows/2').status_code, 409)
        self.assertEqual(self.client.get('/borrows/999').status_code, 404)

    def test_upgrade_preserves_existing_database_and_opens_old_borrows(self):
        self.post('/items', name='Existing camera', category='Electronics', condition='Good', description='Keep this listing.')
        self.post('/items/1/request', expected_return='2026-11-22')
        self.switch(2)
        self.post('/requests/1/approve')
        # Simulate the pre-chat schema while retaining real listing/request data.
        with self.app.app_context():
            db = get_db()
            db.execute('DROP TABLE messages')
            db.commit()
            members = [tuple(r) for r in db.execute('SELECT * FROM members ORDER BY id')]
            items = [tuple(r) for r in db.execute('SELECT * FROM items ORDER BY id')]
            requests = [tuple(r) for r in db.execute('SELECT * FROM borrow_requests ORDER BY id')]
        upgraded = create_app(self.config)
        self.assertEqual(upgraded.secret_key, self.app.secret_key)
        with upgraded.app_context():
            db = get_db()
            self.assertEqual([tuple(r) for r in db.execute('SELECT * FROM members ORDER BY id')], members)
            self.assertEqual([tuple(r) for r in db.execute('SELECT * FROM items ORDER BY id')], items)
            self.assertEqual([tuple(r) for r in db.execute('SELECT * FROM borrow_requests ORDER BY id')], requests)
            self.assertEqual(db.execute('SELECT value FROM metadata WHERE key=?', ('seed_version',)).fetchone()[0], '1')
            self.assertEqual(db.execute('SELECT count(*) FROM messages').fetchone()[0], 0)
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO borrow_requests(item_id,borrower_id,expected_return,status,created_at) VALUES(1,3,'2026-11-23','Approved','now')")
            db.rollback()
        client = upgraded.test_client()
        client.get('/')
        self.assertEqual(client.get('/borrows/1').status_code, 200)

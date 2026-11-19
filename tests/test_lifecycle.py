"""Small integration checks for the demo's core workflow and integrity rules."""

import sqlite3
import tempfile
import unittest
from datetime import date

from app import create_app, get_db


class BorrowingTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = {"TESTING": True, "DATA_DIR": self.temp.name, "TODAY": date(2026, 11, 19)}
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def post(self, path, **data):
        with self.client.session_transaction() as state:
            data["csrf"] = state["csrf"]
        return self.client.post(path, data=data)

    def switch(self, member):
        self.assertEqual(self.post("/demo-member", member_id=member).status_code, 303)

    def states(self):
        with self.app.app_context():
            return [row[0] for row in get_db().execute("SELECT status FROM borrow_requests ORDER BY id")]


class BorrowingSmokeTests(BorrowingTestCase):
    def test_listing_borrow_approve_contact_return_and_restart(self):
        response = self.post("/items", name="Tripod <script>", category="Electronics",
                             condition="Good", description="A steady camera stand.")
        self.assertEqual(response.status_code, 303)
        self.assertIn(b"Tripod &lt;script&gt;", self.client.get("/").data)
        self.assertEqual(self.post("/items/1/request", expected_return="2026-11-22").status_code, 303)
        self.assertEqual(self.states(), ["Pending"])
        self.switch(2)
        self.assertIn(b"Amritanshu", self.client.get("/dashboard").data)
        self.assertEqual(self.post("/requests/1/approve").status_code, 303)
        self.switch(1)
        html = self.client.get("/dashboard").get_data(as_text=True)
        for text in ("Request approved", "Accepted", "Rahul has approved your request for his Cricket Bat.",
                     "rahul@example.com", "22 November", "Please message the owner here to arrange the handover."):
            self.assertIn(text, html)
        self.assertNotIn(b"Cricket Bat", self.client.get("/").data)
        self.switch(2)
        self.assertEqual(self.post("/requests/1/return").status_code, 303)
        self.assertEqual(self.states(), ["Returned"])
        self.assertIn(b"Cricket Bat", self.client.get("/").data)
        # Recreate the app using the same database and signing key, as on restart.
        restarted = create_app(self.config)
        with restarted.app_context():
            db = get_db()
            self.assertEqual(db.execute("SELECT count(*) FROM items").fetchone()[0], 7)
            self.assertEqual(db.execute("SELECT status FROM borrow_requests").fetchone()[0], "Returned")
        self.assertEqual(restarted.secret_key, self.app.secret_key)

    def test_competing_requests_and_database_guard(self):
        self.assertEqual(self.post("/items/1/request", expected_return="2026-11-22").status_code, 303)
        self.switch(3)
        self.assertEqual(self.post("/items/1/request", expected_return="2026-11-23").status_code, 303)
        self.switch(2)
        self.assertEqual(self.post("/requests/1/approve").status_code, 303)
        self.assertEqual(self.states(), ["Approved", "Rejected"])
        self.assertEqual(self.post("/requests/2/approve").status_code, 409)
        with self.app.app_context():
            db = get_db()
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE borrow_requests SET status='Approved' WHERE id=2")
            db.rollback()
        self.switch(3)
        self.assertEqual(self.post("/items/1/request", expected_return="2026-11-23").status_code, 409)

    def test_validation_identity_authorization_and_csrf(self):
        self.assertEqual(self.post("/items", name=" ", category="Sports", condition="Good", description="Something").status_code, 422)
        for value in ("2026-11-18", "2026-02-30", "", "not-a-date"):
            self.assertEqual(self.post("/items/1/request", expected_return=value).status_code, 422)
        self.assertEqual(self.post("/items/3/request", expected_return="2026-11-22").status_code, 403)
        self.assertEqual(self.client.post("/items", data={}).status_code, 403)
        self.assertEqual(self.post("/demo-member", member_id=99).status_code, 400)
        self.post("/items/1/request", expected_return="2026-11-22")
        self.assertEqual(self.post("/items/1/request", expected_return="2026-11-22").status_code, 409)
        for action in ("approve", "reject", "return"):
            self.assertEqual(self.post(f"/requests/1/{action}").status_code, 403)
        self.switch(2)
        self.assertEqual(self.post("/requests/1/return").status_code, 409)
        self.assertEqual(self.post("/requests/1/reject").status_code, 303)
        self.assertEqual(self.states(), ["Rejected"])
        self.assertIn(b"Cricket Bat", self.client.get("/").data)
        self.assertEqual(self.post("/requests/1/approve").status_code, 409)
        self.assertEqual(self.client.get("/items/999/request").status_code, 404)


if __name__ == "__main__":
    unittest.main()

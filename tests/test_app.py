import io
import tempfile
import unittest
from pathlib import Path

from app import create_app, get_db


class ShareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1_800_000_000
        self.app = create_app({
            "TESTING": True,
            "DATA_DIR": Path(self.temp.name),
            "SECRET_KEY": "test-only-secret",
            "CLOCK": lambda: self.now,
        })
        self.client = self.app.test_client()
        self.client.get("/")
        with self.client.session_transaction() as session:
            self.csrf = session["csrf"]

    def create(self, **overrides):
        data = dict(title="Team notes", kind="text", content="Hello team",
                    language="plain", expiry="3600", csrf=self.csrf)
        data.update(overrides)
        response = self.client.post("/shares", data=data)
        return response

    def test_create_preview_and_download_text(self):
        response = self.create()
        self.assertEqual(response.status_code, 303)
        url = response.location
        recipient = self.app.test_client()
        self.assertIn(b"Hello team", recipient.get(url).data)
        download = recipient.get(url + "/download")
        self.assertEqual(download.data, b"Hello team")
        self.assertIn("attachment", download.headers["Content-Disposition"])

    def test_code_is_escaped_not_executed(self):
        response = self.create(kind="code", content="<script>alert(1)</script>")
        page = self.client.get(response.location).data
        self.assertIn(b"&lt;script&gt;", page)
        self.assertNotIn(b"<script>alert(1)</script>", page)

    def test_expiry_blocks_page_and_download_at_exact_boundary(self):
        url = self.create(expiry="60").location
        self.now += 60
        self.assertEqual(self.client.get(url).status_code, 410)
        self.assertEqual(self.client.get(url + "/download").status_code, 410)

    def test_only_owner_can_revoke(self):
        url = self.create().location
        other = self.app.test_client()
        other.get("/")
        with other.session_transaction() as session:
            csrf = session["csrf"]
        self.assertEqual(other.post(url + "/revoke", data={"csrf": csrf}).status_code, 404)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url + "/revoke", data={"csrf": self.csrf}).status_code, 303)
        self.assertEqual(other.get(url).status_code, 410)
        self.assertEqual(other.get(url + "/download").status_code, 410)

    def test_csrf_is_required(self):
        self.assertEqual(self.create(csrf="wrong").status_code, 403)

    def test_reject_unsafe_link(self):
        self.assertEqual(self.create(kind="link", content="javascript:alert(1)").status_code, 422)

    def test_link_preview_has_explicit_external_destination(self):
        url = self.create(kind="link", content="https://example.com/docs").location
        self.assertIn(b'href="https://example.com/docs"', self.client.get(url).data)

    def test_validate_required_fields_and_enums(self):
        for values in ({"title": ""}, {"content": ""}, {"expiry": "-1"},
                       {"kind": "other"}, {"language": "invalid"}, {"title": "x" * 121}):
            with self.subTest(values=values):
                self.assertEqual(self.create(**values).status_code, 422)

    def test_upload_and_revoke_document(self):
        response = self.create(kind="document", file=(io.BytesIO(b"%PDF-1.7\nexample"), "../../notes.pdf"))
        self.assertEqual(response.status_code, 303)
        download = self.client.get(response.location + "/download")
        self.assertEqual(download.data, b"%PDF-1.7\nexample")
        download.close()
        self.client.post(response.location + "/revoke", data={"csrf": self.csrf})
        self.assertEqual(self.client.get(response.location + "/download").status_code, 410)
        self.assertEqual(list((Path(self.temp.name) / "uploads").iterdir()), [])

    def test_reject_disguised_pdf_and_executable(self):
        for filename, body in (("bad.pdf", b"not pdf"), ("bad.exe", b"MZ")):
            self.assertEqual(self.create(kind="document", file=(io.BytesIO(body), filename)).status_code, 422)

    def test_reject_oversized_text(self):
        self.assertEqual(self.create(content="x" * 100_001).status_code, 422)

    def test_dashboard_is_private_and_searchable(self):
        self.create(title="Unique title")
        self.assertIn(b"Unique title", self.client.get("/?q=Unique").data)
        self.assertNotIn(b"Unique title", self.client.get("/?q=missing").data)
        other = self.app.test_client()
        self.assertNotIn(b"Unique title", other.get("/").data)

    def test_security_headers(self):
        response = self.client.get("/")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
        self.assertIn("HttpOnly", response.headers.get("Set-Cookie", ""))

    def test_cleanup_removes_expired_payload(self):
        self.create(expiry="60", kind="document", file=(io.BytesIO(b"notes"), "notes.txt"))
        self.now += 60
        result = self.app.test_cli_runner().invoke(args=["cleanup"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(list((Path(self.temp.name) / "uploads").iterdir()), [])
        with self.app.app_context():
            self.assertEqual(get_db().execute("SELECT count(*) FROM shares").fetchone()[0], 0)

    def test_missing_share_and_static_traversal(self):
        self.assertEqual(self.client.get("/s/not-a-real-share").status_code, 404)
        self.assertEqual(self.client.get("/static/../app.py").status_code, 404)

    def test_persistence_across_app_restart(self):
        url = self.create().location
        restarted = create_app(dict(self.app.config))
        self.assertIn(b"Hello team", restarted.test_client().get(url).data)

    def test_preserves_code_whitespace(self):
        content = "\n    def hello():\n        return 'hello'\n"
        url = self.create(kind="code", content=content).location
        self.assertEqual(self.client.get(url + "/download").data.decode(), content)

    def test_reject_request_above_upload_limit(self):
        response = self.create(kind="document", file=(io.BytesIO(b"x" * (6 * 1024 * 1024)), "large.txt"))
        self.assertEqual(response.status_code, 413)
        response.request.environ["wsgi.input"].close()
        response.request.close()

    def test_expired_link_does_not_expose_destination(self):
        url = self.create(kind="link", content="https://example.com/private", expiry="60").location
        self.now += 60
        response = self.client.get(url)
        self.assertEqual(response.status_code, 410)
        self.assertNotIn(b"https://example.com/private", response.data)

    def test_unknown_host_is_rejected(self):
        self.assertEqual(self.client.get("/", base_url="http://evil.example").status_code, 400)

    def test_first_start_generates_and_reuses_signing_key(self):
        directory = Path(self.temp.name) / "fresh-install"
        first = create_app({"TESTING": True, "DATA_DIR": directory})
        second = create_app({"TESTING": True, "DATA_DIR": directory})
        self.assertEqual(first.config["SECRET_KEY"], second.config["SECRET_KEY"])
        self.assertEqual(len(first.config["SECRET_KEY"]), 64)
        self.assertEqual(first.test_client().get("/").status_code, 200)

    def test_plain_text_document_preview_is_escaped(self):
        url = self.create(kind="document", file=(io.BytesIO(b"<b>notes</b>"), "notes.md")).location
        self.assertIn(b"&lt;b&gt;notes&lt;/b&gt;", self.client.get(url).data)

    def test_persistent_creation_quota(self):
        # Create one real record, then duplicate its metadata to reach the quota.
        self.create()
        with self.app.app_context():
            db = get_db()
            row = dict(db.execute("SELECT * FROM shares LIMIT 1").fetchone())
            for number in range(59):
                db.execute(
                    "INSERT INTO shares (id,owner_hash,title,kind,size,created_at,expires_at) VALUES (?,?,?,?,?,?,?)",
                    (f"quota-{number}", row["owner_hash"], "Quota", "text", 1, self.now, self.now + 3600),
                )
            db.commit()
        self.assertEqual(self.create().status_code, 429)


if __name__ == "__main__":
    unittest.main()

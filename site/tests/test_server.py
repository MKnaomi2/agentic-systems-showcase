import http.client
import re
import threading
import unittest

from http.server import ThreadingHTTPServer

from server import PortfolioHandler


class PortfolioServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), PortfolioHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=3)
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        headers = {name.lower(): value for name, value in response.getheaders()}
        connection.close()
        return response.status, headers, body

    def test_home_uses_nonce_bound_csp(self):
        status, headers, body = self.request("GET", "/")
        page = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertNotIn("'unsafe-inline'", headers["content-security-policy"])
        match = re.search(r"style-src 'nonce-([^']+)'", headers["content-security-policy"])
        self.assertIsNotNone(match)
        nonce = match.group(1)
        self.assertIn(f'<style nonce="{nonce}">', page)
        self.assertIn(f'<script nonce="{nonce}" type="application/ld+json">', page)
        self.assertEqual(headers["strict-transport-security"], "max-age=31536000; includeSubDomains")
        self.assertEqual(headers["cross-origin-opener-policy"], "same-origin")

    def test_health_endpoint_is_minimal_and_not_indexed(self):
        status, headers, body = self.request("GET", "/healthz")
        self.assertEqual((status, body), (200, b"ok\n"))
        self.assertEqual(headers["x-robots-tag"], "noindex, nofollow, noarchive")
        self.assertEqual(headers["cache-control"], "no-store")

    def test_sensitive_and_admin_paths_are_indistinguishable_404s(self):
        for path in ("/admin", "/.env", "/.git/config", "/server.py", "/AJ-Chandler-Public-Resume.pdf"):
            with self.subTest(path=path):
                status, headers, body = self.request("GET", path)
                self.assertEqual((status, body), (404, b"Not Found"))
                self.assertEqual(headers["x-robots-tag"], "noindex, nofollow, noarchive")

    def test_resume_is_not_advertised(self):
        for path in ("/", "/llms.txt", "/llms-full.txt", "/proof.json"):
            with self.subTest(path=path):
                status, _, body = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertNotIn(b"resume", body.lower())
                self.assertNotIn("résumé".encode("utf-8"), body.lower())

    def test_unsafe_methods_are_rejected_with_hardened_headers(self):
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"):
            with self.subTest(method=method):
                status, headers, body = self.request(method, "/")
                self.assertEqual((status, body), (405, b"Method Not Allowed"))
                self.assertEqual(headers["allow"], "GET, HEAD")
                self.assertIn("default-src 'none'", headers["content-security-policy"])

    def test_public_surfaces_use_only_the_dedicated_contact(self):
        for path in ("/", "/llms.txt", "/llms-full.txt", "/proof.json", "/security.txt"):
            with self.subTest(path=path):
                status, _, body = self.request("GET", path)
                page = body.decode("utf-8").lower()
                self.assertEqual(status, 200)
                self.assertNotIn("protonmail" + ".com", page)
                self.assertNotIn("internal" + "-only", page)

        _, _, homepage = self.request("GET", "/")
        self.assertIn("alvento.lisp@proton.me", homepage.decode("utf-8").lower())

    def test_structured_proof_is_public_and_specific(self):
        status, headers, body = self.request("GET", "/proof.json")
        proof = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "application/json; charset=utf-8")
        self.assertEqual(headers["access-control-allow-origin"], "*")
        self.assertEqual(headers["cross-origin-resource-policy"], "cross-origin")
        self.assertIn('"formal_current_title": "IT Systems Administrator II"', proof)
        self.assertIn('"name": "Wadevo Design"', proof)
        self.assertIn('"name": "Wadevo Finance"', proof)
        self.assertIn('"status": "live invite-only alpha with public landing"', proof)
        self.assertIn('"name": "Agentic Systems Showcase"', proof)
        self.assertIn('"tests": 12', proof)
        self.assertIn('"name": "Healthspan"', proof)
        self.assertIn('"name": "Hermes agent lab"', proof)

    def test_machine_readable_assets_are_cross_origin_fetchable(self):
        for path in ("/robots.txt", "/llms.txt", "/llms-full.txt", "/proof.json"):
            with self.subTest(path=path):
                status, headers, _ = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertEqual(headers["access-control-allow-origin"], "*")
                self.assertEqual(headers["cross-origin-resource-policy"], "cross-origin")

        status, headers, _ = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertNotIn("access-control-allow-origin", headers)
        self.assertEqual(headers["cross-origin-resource-policy"], "same-origin")


if __name__ == "__main__":
    unittest.main()

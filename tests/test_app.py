import unittest

from main import app


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"Hello World!")

    def test_health_is_independent_of_demo_error(self):
        self.client.get("/error")
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_demo_preserves_incorrect_http_status(self):
        with self.assertLogs("main", level="ERROR"):
            response = self.client.get("/error")
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.json)

    def test_unknown_route(self):
        self.assertEqual(self.client.get("/missing").status_code, 404)

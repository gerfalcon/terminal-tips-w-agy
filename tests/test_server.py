import json
import threading
import unittest
import urllib.error
import urllib.request

from serve import make_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0, quiet=True)  # port 0: any free port
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=5) as response:
            return response.status, response.read().decode("utf-8")

    def post(self, path, body):
        request = urllib.request.Request(self.base + path, data=body, method="POST",
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())

    def status_of(self, call, *args):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            call(*args)
        return caught.exception.code

    def test_home_page_shows_the_board(self):
        status, html = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn('<table class="board">', html)

    def test_static_files_are_served(self):
        self.assertEqual(self.get("/static/app.js")[0], 200)
        self.assertEqual(self.get("/static/style.css")[0], 200)

    def test_check_scores_answers(self):
        body = json.dumps({"entries": {"0,0": "P", "1,0": "L", "2,0": "A", "3,0": "N"}}).encode()
        status, result = self.post("/api/check", body)
        self.assertEqual(status, 200)
        self.assertEqual(result["correct"], ["1D"])

    def test_bad_request_is_refused(self):
        self.assertEqual(self.status_of(self.post, "/api/check", b"not json"), 400)

    def test_unknown_pages_are_not_found(self):
        self.assertEqual(self.status_of(self.get, "/nope"), 404)
        self.assertEqual(self.status_of(self.get, "/?puzzle=nope"), 404)
        self.assertEqual(self.status_of(self.post, "/api/nope", b"{}"), 404)


if __name__ == "__main__":
    unittest.main()

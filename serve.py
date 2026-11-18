"""Run the crossword in your browser.

    python3 serve.py              then open http://localhost:8080
    PORT=8081 python3 serve.py    to use another port

In Cloud Shell, click Web Preview, then "Preview on port 8080".
Python standard library only. Nothing to install.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from game.puzzle import check_answers, load_puzzle
from game.render import render_page

ROOT = Path(__file__).resolve().parent
STATIC = {
    "/static/style.css": ("static/style.css", "text/css; charset=utf-8"),
    "/static/app.js": ("static/app.js", "text/javascript; charset=utf-8"),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            puzzle_id = parse_qs(url.query).get("puzzle", [None])[0]
            try:
                puzzle = load_puzzle(puzzle_id)
            except KeyError:
                return self.send_text(404, "No such puzzle.")
            return self.send_body(200, render_page(puzzle).encode("utf-8"), "text/html; charset=utf-8")
        if url.path in STATIC:
            name, kind = STATIC[url.path]
            return self.send_body(200, (ROOT / name).read_bytes(), kind)
        return self.send_text(404, "Not found.")

    def do_POST(self):
        if urlparse(self.path).path != "/api/check":
            return self.send_text(404, "Not found.")
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            puzzle = load_puzzle(data.get("puzzle"))
            result = check_answers(puzzle, data.get("entries", {}))
        except (ValueError, KeyError, AttributeError, TypeError):
            return self.send_text(400, "Bad request.")
        return self.send_body(200, json.dumps(result).encode("utf-8"), "application/json")

    def send_text(self, status, text):
        self.send_body(status, text.encode("utf-8"), "text/plain; charset=utf-8")

    def send_body(self, status, body, kind):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if not getattr(self.server, "quiet", False):
            super().log_message(format, *args)


def make_server(port, host="127.0.0.1", quiet=False):
    server = ThreadingHTTPServer((host, port), Handler)
    server.quiet = quiet
    return server


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = make_server(port, os.environ.get("HOST", "127.0.0.1"))
    print(f"Crossword is running on http://localhost:{port}   (Ctrl+C stops it)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

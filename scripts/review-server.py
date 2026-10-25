#!/usr/bin/env python3
"""
Slide review comments: the queue between the deck player and a Claude session.

In the deck player (assets/class.html, review mode: press R or add ?review),
Petra circles part of a slide and types a comment. The player POSTs it here,
and this server appends it as one JSON line to reviews/slide-comments.jsonl.
A Claude session drains that file — "watch my slide comments" sets a watcher
on it, "check my slide comments" reads it once — and acts on each comment
(deck, slide, circled region, text). See CLAUDE.md, "Slide review comments".

Started by ./preview-slides.sh alongside the edit server, or standalone:

    python3 scripts/review-server.py

Deliberately local-only (binds 127.0.0.1) and append-only: it writes exactly
one file, reviews/slide-comments.jsonl, and never truncates it. Processed
comments are archived by the Claude session, not by this server.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Per-project override (REVIEW_PORT) so two projects can run side by side; the
# player's matching setting is COURSE.reviewPort in assets/course.js.
PORT = int(os.environ.get('REVIEW_PORT', 8928))
ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "reviews" / "slide-comments.jsonl"


def read_queue():
    if not QUEUE.exists():
        return []
    out = []
    for line in QUEUE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # a hand-edited or truncated line must not take the API down
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        # The player is served from another localhost port (8352), so this is
        # cross-origin; the server is loopback-only, so a wildcard is safe.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "queued": len(read_queue())})
        elif self.path == "/slide-comments":
            self._send(200, read_queue())
        else:
            self._send(404, {"error": "unknown path"})

    def do_POST(self):
        if self.path != "/slide-comment":
            self._send(404, {"error": "unknown path"})
            return
        try:
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            comment = json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": "body must be JSON"})
            return
        if not isinstance(comment, dict) or not str(comment.get("text", "")).strip():
            self._send(400, {"error": "comment has no text"})
            return
        # A slide comment names its deck; a book comment (ptx-review.js)
        # names its page. Either anchors it; neither is a reason to lose it.
        if not comment.get("deck") and not comment.get("page"):
            self._send(400, {"error": "comment names no deck or page"})
            return
        comment["received"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        QUEUE.parent.mkdir(exist_ok=True)
        with QUEUE.open("a") as f:
            f.write(json.dumps(comment, ensure_ascii=False) + "\n")
        self._send(200, {"ok": True, "queued": len(read_queue())})

    def log_message(self, fmt, *args):
        pass  # quiet beside the page server's own log


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"review server on http://127.0.0.1:{PORT} -> {QUEUE.relative_to(ROOT)}")
    server.serve_forever()

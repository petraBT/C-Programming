#!/usr/bin/env python3
"""
A drop-in for `python3 -m http.server PORT --directory DIR` that also sends
Cache-Control: no-cache on every response.

Plain http.server sends no cache headers at all, so a browser tab that has
ever loaded a file from one of these preview servers is free to keep reusing
its own cached copy on later visits — including a plain reload — instead of
asking the server again. Every *.ptx save is caught by watch.py and rebuilt,
but the browser doesn't know that, so a book or slide page can sit there
showing stale JS/CSS after a rebuild until a hard refresh happens to catch it.
no-cache forces revalidation on every request; SimpleHTTPRequestHandler
already sends Last-Modified, so an unchanged file still comes back as a cheap
304 — this only removes the "browser skips asking" behavior.

Usage: python3 scripts/serve-no-cache.py PORT [DIRECTORY]
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1])
    directory = sys.argv[2] if len(sys.argv) > 2 else "."
    handler = partial(NoCacheHandler, directory=directory)
    server = ThreadingHTTPServer(("", port), handler)
    print(f"serving {directory} on port {port} (Cache-Control: no-cache)")
    server.serve_forever()

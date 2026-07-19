#!/usr/bin/env python3
"""Static file server that adds the two headers interactive stdin needs
(Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy), which Python's
built-in `http.server` doesn't send. Used by preview-client.sh so local
preview actually shows the same interactive terminal a real cross-origin
isolated deployment (e.g. the Cloudflare Pages preview) would, instead of
the non-interactive "Input" box fallback.

Only applies these headers to pages that actually embed the coding-window
tool (same allow-list approach as generate-middleware.py, which produces the
real Cloudflare Pages Function used in production - see that script's
docstring for the full reasoning, including why isolating pages that don't
need it stays unsafe regardless of COEP mode chosen). Cross-origin isolation
blocks any cross-origin subresource without a matching
Cross-Origin-Resource-Policy header, which silently breaks things like
YouTube video embeds and Google Docs embeds elsewhere in the book -
confirmed live. Applying the headers blanket-wide was tried first and is
exactly what caused that breakage; scoping to only the pages that need it
avoids the problem entirely, including for embed types not yet audited. The
page list is computed once at startup by scanning the served directory, so
it can't drift out of sync with the actual content. No rule-count cap here
(this is plain Python, not a declarative rules file), so unlike the
production Function this script never needed to change for that reason.

Usage: python3 serve-with-headers.py <port> <directory>
"""
import http.server
import sys
from pathlib import Path

NEEDLE = "coding-window/index.html"

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8299
directory = sys.argv[2] if len(sys.argv) > 2 else "."

isolated_pages = set()
for html_file in Path(directory).glob("*.html"):
    if NEEDLE in html_file.read_text(errors="ignore"):
        isolated_pages.add("/" + html_file.name)

# The classroom deck player (external/class.html) shows those book pages as
# slides in an iframe. Cross-origin isolation only holds if EVERY frame from
# the top down has the headers, so the outermost frame needs them too - even
# though the player itself contains no coding window, only pages that do.
# Without this line the nested coding windows silently drop to the
# non-interactive "type your input first" fallback (confirmed live).
isolated_pages.add("/external/class.html")

print(f"Applying isolation headers to {len(isolated_pages)} page(s) that embed the coding-window tool.")


class IsolatedRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        path_only = self.path.split("?", 1)[0]
        # Cross-origin isolation must propagate through every frame in the
        # ancestor chain (empirically confirmed earlier), so the
        # coding-window tool's own files need these headers too, on top of
        # whichever parent page embeds it. Safe to always isolate this path
        # regardless of which page loaded it: only allow-listed pages ever
        # embed the coding-window iframe in the first place.
        if path_only in isolated_pages or "/coding-window/" in path_only:
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
            self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()


def handler_factory(*args, **kwargs):
    return IsolatedRequestHandler(*args, directory=directory, **kwargs)


http.server.test(HandlerClass=handler_factory, port=port)

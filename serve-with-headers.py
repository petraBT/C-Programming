#!/usr/bin/env python3
"""Static file server that adds the two headers interactive stdin needs
(Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy), which Python's
built-in `http.server` doesn't send. Used by preview-client.sh so local
preview actually shows the same interactive terminal a real cross-origin
isolated deployment (e.g. the Cloudflare Pages preview) would, instead of
the non-interactive "Input" box fallback.

Usage: python3 serve-with-headers.py <port> <directory>
"""
import http.server
import sys

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8299
directory = sys.argv[2] if len(sys.argv) > 2 else "."


class IsolatedRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()


def handler_factory(*args, **kwargs):
    return IsolatedRequestHandler(*args, directory=directory, **kwargs)


http.server.test(HandlerClass=handler_factory, port=port)

#!/usr/bin/env python3
"""Fail if a file that belongs to slide-tooling was edited in this book.

Those files are copies (tooling.lock lists their hashes). Edit them in the
slide-tooling repo and run scripts/sync-tooling.sh; a local edit would be
silently overwritten by the next sync and is not shared with the other books.
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lock_path = os.path.join(ROOT, "tooling.lock")
if not os.path.exists(lock_path):
    print("no tooling.lock - run scripts/sync-tooling.sh")
    sys.exit(1)
lock = json.load(open(lock_path))
bad = []
for rel, want in lock["files"].items():
    p = os.path.join(ROOT, rel)
    have = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    if have != want:
        bad.append(rel + (" (missing)" if have is None else ""))
if bad:
    print("slide-tooling files differ from tooling.lock (%s):" % lock["commit"][:9])
    for b in bad:
        print("  " + b)
    print("Edit them in the slide-tooling repo, then run scripts/sync-tooling.sh.")
    sys.exit(1)
sys.exit(0)

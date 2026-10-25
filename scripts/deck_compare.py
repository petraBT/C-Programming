#!/usr/bin/env python3
"""Compare two deck_snapshot_all.sh runs slide by slide.

    python3 scripts/deck_compare.py before after

A slide is identical when its screenshot, its text and its stage HTML all
match. Prints every difference and exits 1 if there is any.
"""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(label):
    root = os.path.join(REPO, "output", "snapshots", label)
    runs = {}
    for view in sorted(os.listdir(root)):
        for deck in sorted(os.listdir(os.path.join(root, view))):
            m = os.path.join(root, view, deck, "manifest.json")
            if os.path.exists(m):
                runs[(view, deck)] = json.load(open(m))
    return runs


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    a, b = load(sys.argv[1]), load(sys.argv[2])
    bad = slides = 0
    for key in sorted(set(a) | set(b)):
        view, deck = key
        if key not in a or key not in b:
            print(f"{view}/{deck}: only in {'after' if key in b else 'before'}")
            bad += 1
            continue
        x, y = a[key], b[key]
        if len(x) != len(y):
            print(f"{view}/{deck}: {len(x)} slides before, {len(y)} after")
            bad += 1
            continue
        for s, t in zip(x, y):
            slides += 1
            what = [k for k in ("png", "text", "html") if s[k] != t[k]]
            if what:
                bad += 1
                print(f"{view}/{deck} slide {s['n']} ({s['title'] or '?'}): {', '.join(what)} differ")
    print(f"{slides} slides compared, {bad} difference(s)")
    sys.exit(1 if bad else 0)


main()

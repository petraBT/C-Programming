#!/usr/bin/env python3
"""Write assets/decks/index.json — the deck player's table of contents.

The player is served as static files, and a static host has no directory
listing, so the list of decks has to exist as a file. This regenerates it from
the decks themselves, so the titles can never disagree with what a deck says
about itself.

Run it after adding or renaming a deck:

    python3 scripts/make_deck_index.py

preview-slides.sh runs it on every start, and check_deck.py fails if the
committed index is out of date — so the usual way to notice is to be told.

Ordering is teaching order, which is not alphabetical: Day 1, then Day 1X,
then Day 2 … and a day's pre-class video sits with its day rather than at the
end. That comes out of the id (day7x sorts inside day 7), which is why the
sort key is parsed rather than taken from the filename.
"""

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
DECKS = os.path.join(PROJECT, "assets", "decks")
INDEX = os.path.join(DECKS, "index.json")

# day8video -> (8, 2, ''), day7x -> (7, 1, 'x'), day3 -> (3, 0, '')
ID_PARTS = re.compile(r"^day(\d+)(x?)(video)?$", re.I)


def sort_key(deck_id: str):
    """Teaching order. Anything unrecognised sorts last, alphabetically, rather
    than crashing or silently vanishing from the contents."""
    match = ID_PARTS.match(deck_id)
    if not match:
        return (10_000, 0, deck_id)
    day, ex, video = match.groups()
    # Within a day: the class deck, then its X session, then its video.
    part = 2 if video else (1 if ex else 0)
    return (int(day), part, deck_id)


def describe(deck_id: str, title: str):
    """Split "Day 8 — Timers and Interrupts" into its label and its name.

    The em dash is the authored convention (see AUTHORING-slides.md). A title
    that doesn't follow it still lists — it just carries no separate label,
    rather than being mangled to fit.
    """
    if "—" in title:
        label, _, name = title.partition("—")
        return label.strip(), name.strip()
    return "", title.strip()


def build():
    decks = []
    for path in glob.glob(os.path.join(DECKS, "*.json")):
        if os.path.basename(path) == "index.json":
            continue
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        deck_id = data.get("id") or os.path.splitext(os.path.basename(path))[0]
        title = data.get("title") or deck_id
        label, name = describe(deck_id, title)
        slides = data.get("slides") or []
        decks.append({
            "id": deck_id,
            "title": title,
            "label": label,
            "name": name,
            # A pre-class video deck is watched at home, not projected, so the
            # contents page marks it rather than listing it as another lecture.
            "kind": "video" if deck_id.lower().endswith("video") else "class",
            "slides": len(slides),
            # Shown so a deck that is mostly solutions is recognisable as one.
            "instructorOnly": sum(1 for s in slides if s.get("instructor")),
        })
    decks.sort(key=lambda d: sort_key(d["id"]))
    return {"decks": decks}


def main():
    index = build()
    text = json.dumps(index, ensure_ascii=False, indent=2) + "\n"

    try:
        with open(INDEX, encoding="utf-8") as handle:
            current = handle.read()
    except OSError:
        current = None

    if "--check" in sys.argv:
        if current != text:
            print("assets/decks/index.json is out of date — "
                  "run: python3 scripts/make_deck_index.py")
            return 1
        return 0

    # Only write when the content actually changed. This file lives in
    # assets/decks/, which watch.py watches, so an unconditional write makes
    # every build that regenerates the index retrigger every running watcher —
    # and a watcher's rebuild racing a build-all on the same output/<target>/
    # fails it outright with "rm: Directory not empty".
    if current == text:
        print(f"{os.path.relpath(INDEX, PROJECT)} already up to date — {len(index['decks'])} decks")
        return 0

    with open(INDEX, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"wrote {os.path.relpath(INDEX, PROJECT)} — {len(index['decks'])} decks")
    return 0


if __name__ == "__main__":
    sys.exit(main())

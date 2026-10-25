#!/usr/bin/env python3
"""Strip instructor-only slides from the deck JSON inside a STUDENT deck build.

The XSL strips instructor slides from the HTML of the "web-deck" target, so the
answers are not in its page source. The deck JSON is a different pipeline:
PreTeXt copies assets/ verbatim into <output>/external/, so the copy that lands
beside the stripped pages still lists every instructor slide. Two things go
wrong if it is left alone:

  * the player looks the slide up by id, does not find it, and fails the deck
    with 'Slide "..." not found' — 29 times, in a build that is otherwise
    correct;
  * the entry's "title" is readable in the JSON, and the titles are things like
    "Solution — blink, dim, write". Less than the answer, but not nothing.

So the deck list is filtered to match the pages beside it. This runs against an
OUTPUT directory and never touches assets/decks/ — the source keeps every slide,
because the instructor build needs them.

    python3 scripts/filter_student_decks.py output/web-deck

Nothing to do for web-deck-instructor: that build renders the slides, so its
deck JSON should list them.
"""

import glob
import json
import os
import sys


def filter_deck(path):
    """Drop instructor slides from one deck file. Returns how many went.

    Also stamps `studentBuild`, which the player reads to know it is running
    against a build that HAS no instructor slides -- so it drops the audience
    switch instead of announcing "Instructor view" on a public site. Stamped
    on every deck, including ones that had nothing to drop, because the flag
    describes the BUILD and not this one file.
    """
    with open(path, encoding="utf-8") as fh:
        deck = json.load(fh)
    slides = deck.get("slides", [])
    kept = [s for s in slides if not s.get("instructor")]
    dropped = len(slides) - len(kept)
    # Presenter notes are hers and are never projected, but they live in the
    # deck JSON, which PreTeXt copies to external/ and the deploy publishes --
    # so 349 of them were being served, readable by fetching the file directly,
    # no ?notes needed. Dropped here with the instructor slides.
    # NOT `note`: that one is the text a prompt slide SHOWS. Only
    # `presenterNote` is the private one.
    for s in kept:
        s.pop("presenterNote", None)
    deck["slides"] = kept
    # A deck's top-level "_comment" is authoring notes for whoever edits the
    # JSON; the player never reads it. Some name the instructor-only slides
    # ("Two instructor-only slides: inst-datasheet-worked and ..."), so it does
    # not ship either.
    deck.pop("_comment", None)
    deck["studentBuild"] = True
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(deck, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return dropped


def filter_index(path):
    """Bring index.json's per-deck counts back in line with the filtered decks.

    The contents page prints these, so a stale count is a visible wrong number
    rather than a silent one.
    """
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        index = json.load(fh)
    for entry in index.get("decks", []):
        deck_path = os.path.join(os.path.dirname(path), entry["id"] + ".json")
        if not os.path.exists(deck_path):
            continue
        with open(deck_path, encoding="utf-8") as fh:
            entry["slides"] = len(json.load(fh).get("slides", []))
        entry["instructorOnly"] = 0
    # The contents page reads this before any deck is chosen, so it needs the
    # flag too -- that page is where "Instructor view" was being announced.
    index["studentBuild"] = True
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def check(decks_dir):
    """Fail if the built student deck still lists instructor-only slides.

    The safety net for a bare `pretext build web-deck`, which re-copies
    assets/decks/ over a filtered output and undoes this script. That is not a
    hypothetical: a watch.py left running from an older preview-slides.sh did
    exactly that, on every save.
    """
    stale = []
    for path in sorted(glob.glob(os.path.join(decks_dir, "*.json"))):
        if os.path.basename(path) == "index.json":
            continue
        with open(path, encoding="utf-8") as fh:
            left = [s for s in json.load(fh).get("slides", []) if s.get("instructor")]
        if left:
            stale.append((os.path.basename(path), len(left)))
    if not stale:
        print(f"  student deck is filtered: {decks_dir}")
        return 0
    print(f"  UNFILTERED STUDENT DECK  {decks_dir}")
    for name, n in stale:
        print(f"    {name}: {n} instructor-only slide(s) still listed")
    print("    The pages were stripped but the deck list was not, so the player will")
    print("    fail on each one and the entry titles name the answers.")
    print("    Rebuild with ./scripts/build-deck.sh, not `pretext build web-deck`.")
    return 1


def main():
    args = [a for a in sys.argv[1:] if a != "--check"]
    if len(args) != 1:
        sys.exit("usage: filter_student_decks.py [--check] <output-dir>   e.g. output/web-deck")
    decks_dir = os.path.join(args[0], "external", "decks")
    if not os.path.isdir(decks_dir):
        sys.exit(f"no deck directory at {decks_dir} — build the target first")

    if "--check" in sys.argv:
        sys.exit(check(decks_dir))

    total = 0
    for path in sorted(glob.glob(os.path.join(decks_dir, "*.json"))):
        if os.path.basename(path) == "index.json":
            continue
        total += filter_deck(path)
    filter_index(os.path.join(decks_dir, "index.json"))
    print(f"  student decks: dropped {total} instructor-only slide(s) from {decks_dir}")


if __name__ == "__main__":
    main()

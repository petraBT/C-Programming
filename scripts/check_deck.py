#!/usr/bin/env python3
"""Verify a built deck: every ref resolves, and every slide's @ref target is
reachable from the page the deck names.

The second check is the one that matters. PreTeXt chunks each subsection to its
own page, and the player resolves a <slide>'s @ref *within that page only* — so a
slide block authored next to Part 6 cannot reference a figure that lives in the
pre-class reading. Nothing in the source flags this: the build is clean, the
xml:ids all exist, and the slide simply renders blank in class.

    python3 scripts/check_deck.py assets/decks/day7.json
    python3 scripts/check_deck.py --build=output/web assets/decks/*.json

--build resolves against another build instead of web-deck-instructor.
scripts/deploy.sh points it at output/web, the tree it publishes: a STUDENT
build, so its instructor-only slides are skipped (they were stripped on
purpose) and everything else must resolve there, which is what a student
opening the deployed deck will get.
"""
import glob, json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The INSTRUCTOR deck build, because it is the only one with every slide in it.
# Resolving against plain web-deck would report each instructor-only slide as a
# missing id — that build strips them on purpose.
BUILD = os.path.join(REPO, "output", "web-deck-instructor")


def source_instructor_ids():
    """Every id the SOURCE marks instructor-only, mapped to how: "yes"
    (<slide instructor="yes">, projected in the instructor deck), "private"
    (<slide instructor="private">, never projected; review mode only), or
    "block" (<instructor xml:id="...">, which a deck may ref directly; the deck
    entry then says which of the two it is)."""
    ids = {}
    for path in glob.glob(os.path.join(REPO, "source", "*.ptx")):
        src = open(path, encoding="utf-8").read()
        for tag in re.finditer(r"<slide\b([^>]*)>", src):
            attrs = tag.group(1)
            xml_id = re.search(r'xml:id="([^"]+)"', attrs)
            kind = re.search(r'instructor="(yes|private)"', attrs)
            if xml_id and kind:
                ids[xml_id.group(1)] = kind.group(1)
        for tag in re.finditer(r"<instructor\b([^>]*)>", src):
            xml_id = re.search(r'xml:id="([^"]+)"', tag.group(1))
            if xml_id:
                ids[xml_id.group(1)] = "block"
    return ids


def main():
    global BUILD
    student_build = False
    for a in [a for a in sys.argv[1:] if a.startswith("--build=")]:
        BUILD = os.path.abspath(a[len("--build="):])
        sys.argv.remove(a)
        index = os.path.join(BUILD, "external", "decks", "index.json")
        student_build = os.path.exists(index) and bool(
            json.load(open(index, encoding="utf-8")).get("studentBuild"))
    if len(sys.argv) < 2:
        sys.exit("usage: check_deck.py [--build=DIR] <deck.json> [more.json ...]")
    bad = 0
    marked = source_instructor_ids()
    src_minutes = source_slide_minutes()
    for deck_path in sys.argv[1:]:
        # index.json is the contents page's deck list, not a deck. It is in this
        # directory (and so in a *.json glob), but has no slides to check —
        # instead, check that it still agrees with the decks beside it.
        if os.path.basename(deck_path) == "index.json":
            if subprocess.call([sys.executable,
                                os.path.join(REPO, "scripts", "make_deck_index.py"),
                                "--check"]) != 0:
                bad += 1
            continue
        deck = json.load(open(deck_path, encoding="utf-8"))
        refs = [s for s in deck["slides"] if s.get("type") == "ref"]
        print(f"\n{os.path.basename(deck_path)} — {len(deck['slides'])} slides, {len(refs)} refs")
        bad += check_part_minutes(deck, src_minutes)
        for s in refs:
            # The deck JSON and the source must agree about instructor-only.
            # They drive different halves: the JSON decides the player's badge
            # and whether ?student drops the slide, the source attribute decides
            # whether the slide is in the student BUILD at all. Disagree one way
            # and the student deck lists a slide whose markup was stripped;
            # disagree the other and it ships an answer the player then hides.
            flagged, in_source = bool(s.get("instructor")), s["slide"] in marked
            if flagged and s["instructor"] not in (True, "private"):
                print(f"  BAD FLAG      {s['slide']}: \"instructor\" must be true or \"private\","
                      f" not {s['instructor']!r}")
                bad += 1
            kind = marked.get(s["slide"])
            want = {"yes": True, "private": "private"}.get(kind)
            if flagged and want is not None and s["instructor"] != want:
                print(f"  FLAG DIFFERS  {s['slide']}: the source says instructor=\"{kind}\","
                      f" this deck entry says {s['instructor']!r}")
                bad += 1
            if flagged and not in_source:
                print(f"  NOT STRIPPED  {s['slide']} is \"instructor\": true here, but its source"
                      f" is not marked")
                print(f"                (add instructor=\"yes\" to the <slide>, or ref an"
                      f" <instructor> block by its xml:id)")
                bad += 1
            elif in_source and not flagged:
                print(f"  NOT FLAGGED   {s['slide']} is instructor-only in the source, but this"
                      f" deck entry has no \"instructor\": true")
                print(f"                (the student build drops the slide; this deck would"
                      f" still list it)")
                bad += 1
            if student_build and flagged:
                continue    # stripped from this build on purpose
            page = os.path.join(BUILD, s["page"])
            if not os.path.exists(page):
                print(f"  MISSING PAGE  {s['page']}  ({s['slide']})"); bad += 1; continue
            html = open(page, encoding="utf-8").read()
            m = re.search(r'id="%s"([^>]*)' % re.escape(s["slide"]), html)
            if not m:
                print(f"  MISSING ID    {s['slide']}  on {s['page']}"); bad += 1; continue
            # "respond" puts a short/code slide's answer box on this slide: it must be a
            # <slide kind="short|code"> on the same page.
            if s.get("respond"):
                rm = re.search(r'id="%s"[^>]*data-deck-kind="(short|code)"' % re.escape(s["respond"]), html)
                if not rm:
                    print(f"  BAD RESPOND   {s['slide']}: \"respond\": \"{s['respond']}\" is not a"
                          f" kind=\"short\" or \"code\" slide on {s['page']}")
                    bad += 1
            # If the slide block delegates to a figure/table, that target must be
            # on this same page or the slide renders empty -- unless the deck entry
            # names the page it lives on with "refPage", which the player fetches
            # separately so a figure can be reused without duplicating it.
            ref = re.search(r'data-deck-ref="([^"]+)"', m.group(1))
            if ref and not re.search(r'id="%s"' % re.escape(ref.group(1)), html):
                ref_page = s.get("refPage")
                if not ref_page:
                    print(f"  OFF-PAGE REF  {s['slide']} -> {ref.group(1)} is not on {s['page']}")
                    print(f"                (author the <slide> block in that target's own subsection,")
                    print(f"                 or add \"refPage\" naming the page the target is on)")
                    bad += 1
                else:
                    rp = os.path.join(BUILD, ref_page)
                    if not os.path.exists(rp):
                        print(f"  MISSING PAGE  refPage {ref_page}  ({s['slide']})"); bad += 1
                    elif not re.search(r'id="%s"' % re.escape(ref.group(1)),
                                       open(rp, encoding="utf-8").read()):
                        print(f"  OFF-PAGE REF  {s['slide']} -> {ref.group(1)} is not on its"
                              f" refPage {ref_page} either")
                        bad += 1
            elif ref and s.get("refPage"):
                print(f"  STALE refPage {s['slide']}: {ref.group(1)} is already on {s['page']}")
                bad += 1
    bad += check_every_solution_is_projected(marked)
    print(f"\n{bad} problem(s)")
    sys.exit(1 if bad else 0)


MINUTES = re.compile(r"\u2248 ?(\d+) min")


def source_slide_minutes():
    """xml:id -> the minutes in that block's own <note>, for every <slide> in
    source/*.ptx.  Most of a Part's beats are timed here rather than in the deck
    JSON, so a budget check that reads only the deck under-counts every Part."""
    mins = {}
    for path in glob.glob(os.path.join(REPO, "source", "*.ptx")):
        src = open(path, encoding="utf-8").read()
        for m in re.finditer(r'<slide\b[^>]*xml:id="([^"]+)"[^>]*>(.*?)</slide>',
                             src, re.S):
            note = re.search(r"<note>(.*?)</note>", m.group(2), re.S)
            if note:
                found = MINUTES.findall(note.group(1))
                if found:
                    mins[m.group(1)] = int(found[0])
    return mins


def check_part_minutes(deck, src_minutes):
    """S-8: a Part's row must equal the sum of its own beats.

    The Part table is not the budget; the beats are.  A day whose Part rows sum
    to the class length can still be over, because the per-slide and
    per-activity timings inside a Part are what the hour actually spends -- and a
    beat with no time on it at all is the failure mode.

    Found three times by hand, each time one level further down: Day 11's class
    length was wrong; Day 12's Gate 1 found the Part rows summing to 115 against
    110; Day 12's Gate 2' found the rows correct and Part 5's beats summing to 9
    against a row of 5.  All three were a script's work.

    A beat is timed either on its deck entry's presenterNote or in the <slide>
    block's own <note>; the deck wins, since it is the more specific of the two.
    Only OVERSHOOT is reported.  A Part whose beats fall short of its row is the
    normal case for open work -- a build block is thirty minutes with nothing
    scheduled in it -- and reporting those would bury the one that matters.  Only
    Parts where the convention is in use are checked, so older decks that time
    nothing do not fire.  WARNS rather than failing, because the fix is a
    judgment about what to cut.
    """
    section, beats, rows, order = None, {}, {}, []
    for s in deck["slides"]:
        mins = MINUTES.findall(s.get("presenterNote") or "")
        if s.get("type") == "section":
            section = s.get("kicker") or s.get("title") or "?"
            order.append(section)
            if mins:
                rows[section] = int(mins[0])
            continue
        if not section:
            continue
        if mins:
            beats[section] = beats.get(section, 0) + int(mins[0])
        elif s.get("slide") in src_minutes:
            beats[section] = beats.get(section, 0) + src_minutes[s["slide"]]
    warned = 0
    for sec in order:
        if sec not in rows or sec not in beats or beats[sec] <= rows[sec]:
            continue
        if not warned:
            print("  minute budgets that do not reconcile (S-8):")
        warned += 1
        print(f"    {sec}: the row says {rows[sec]} min and its beats sum to "
              f"{beats[sec]} — the Part is over its own budget")
    return 0


def check_every_solution_is_projected(marked):
    """P-10: a solution the class never sees is not a reveal.

    Petra, 2026-08-13: solutions to activities are instructor slides, so they
    show up only in the instructor deck.  The half check_deck already does is
    that a projected slide's flag agrees with its source marker.  This is the
    other half -- an <instructor> block or instructor="yes" slide that no deck
    refs at all is invisible in class, and nothing else would say so.

    Repo-wide by construction: an id counts as projected if ANY deck refs it, so
    this scans assets/decks/ rather than only the decks named on the command
    line, and reports once at the end.
    """
    projected = set()
    for path in glob.glob(os.path.join(REPO, "assets", "decks", "*.json")):
        if os.path.basename(path) == "index.json":
            continue
        for s in json.load(open(path, encoding="utf-8"))["slides"]:
            if s.get("slide"):
                projected.add(s["slide"])
    orphans = sorted(set(marked) - projected)
    if orphans:
        print(f"\nsolutions no deck projects — {len(orphans)}:")
        for o in orphans:
            print(f"  NOT PROJECTED {o} is instructor-only in the source, but no deck refs it")
        print("                (add a deck entry with \"instructor\": true, or delete the block)")
    return len(orphans)


if __name__ == "__main__":
    main()

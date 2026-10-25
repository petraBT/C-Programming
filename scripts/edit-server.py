#!/usr/bin/env python3
"""
Authoring helper: jump from the rendered book - or a projected slide - back to
its source.

Run this alongside a local preview build, then in the book:

  * alt-click any paragraph  -> opens that spot in your text editor  (option A)
  * alt-shift-click          -> edit the text in place, save, done   (option C)

and in the deck player (assets/class.html, served from a web-deck build):

  * alt-click a slide        -> opens its source: the <slide> block in
                                source/*.ptx, or the deck's JSON entry
  * alt-shift-click          -> edit a bullet / caption in place, or open a
                                form for a glue slide's fields

    python3 scripts/edit-server.py                    # this project
    python3 scripts/edit-server.py --project ../ENGS28

The browser half lives in assets/ptx-edit.js and is injected only by the
"web-edit" target, so nothing here can reach a deployed build.

Deliberately local-only: it binds to 127.0.0.1 and refuses to touch any file
outside the project's source/ directory, because its whole job is rewriting
files on disk in response to an HTTP request.
"""

import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ptx_source_index import SourceIndex, TEXT_ELEMENTS, normalize  # noqa: E402


# Below this similarity, we would be guessing at which paragraph the reader
# meant, and guessing wrong means opening an editor on unrelated prose.
MATCH_THRESHOLD = 0.75

REFUSAL = ("That edit would change text inside inline markup (<c>, <em>, ...), "
           "which can't be done safely from here. Alt-click instead to open it "
           "in your editor.")

# Elements whose displayed text is generated when the book is built, and so has
# no counterpart in the source: math is LaTeX in the file and rendered glyphs in
# the browser, and <xref> and the character entities produce text that simply
# isn't written anywhere. A block containing one can never round-trip, so the
# mismatch it causes is not evidence that the file changed underneath the author
# — which is what the generic message unhelpfully implies. Longest alternatives
# first so <mrow> isn't matched as <m>.
#
# <q> belongs here for the same reason, though it is easy to miss: the source
# says <q>Hello, World</q> and the page shows “Hello, World” — PreTeXt supplies
# the curly quotes, so the displayed text has two characters the source does
# not, and the round-trip fails. 41 blocks in this book are that case.
GENERATED = re.compile(
    rb"<(mrow|xref|ellipsis|fillin|today|nbsp|ndash|mdash|sim|md|me|m|q)[\s/>]")


# A <p> holding display math does not render as one block: PreTeXt emits the
# text before the first <md> as its own .para div, the math as a sibling, and
# the text after it as another .para. So the block a reader clicks carries a
# *fragment* of the source paragraph, and comparing whole texts is the wrong
# question — the length prefilter in locate() throws the real element out before
# it is ever scored. Asking instead "is nearly all of what they clicked present,
# in order, in this element?" identifies the block. Only ever used to point an
# editor at the right line; writing still demands the exact match in apply_edit.
FRAGMENT_COVERAGE = 0.90

# Math is LaTeX in the source and rendered glyphs in the browser, so it can
# never match either way — set it aside before comparing. Longest first so
# <mrow> is not matched as <m>.
MATH_SUBTREE = re.compile(
    rb"<(mrow|md|me|m)(\s[^>]*)?>.*?</\1>|<(mrow|md|me|m)(\s[^>]*)?/>", re.S)
ANY_TAG = re.compile(rb"<[^>]+>")


def text_without_math(element):
    """The element's text with math subtrees removed, normalized for matching."""
    try:
        with open(element.path, "rb") as handle:
            handle.seek(element.inner_start)
            raw = handle.read(max(element.inner_end - element.inner_start, 0))
    except OSError:
        return ""
    raw = MATH_SUBTREE.sub(b" ", raw)
    raw = ANY_TAG.sub(b" ", raw)
    return normalize(raw.decode("utf-8", "replace"))


def generated_markup(element):
    """Tag of the first build-time-generated element in this block, or None."""
    try:
        with open(element.path, "rb") as handle:
            handle.seek(element.inner_start)
            raw = handle.read(max(element.inner_end - element.inner_start, 0))
    except OSError:
        return None
    hit = GENERATED.search(raw)
    return hit.group(1).decode() if hit else None


# Why a block can't be line-edited, in the words the author should see. The key
# is the offending tag; the value completes "This … can't be edited in place".
BLOCKED_BY = {
    "m": "paragraph contains math",
    "md": "paragraph contains display math",
    "me": "paragraph contains display math",
    "mrow": "paragraph contains display math",
    "xref": "paragraph contains a cross-reference",
    "ellipsis": "paragraph contains an ellipsis",
    "fillin": "paragraph contains a fill-in blank",
    "today": "paragraph contains a generated date",
    "nbsp": "paragraph contains a special character",
    "ndash": "paragraph contains a special character",
    "mdash": "paragraph contains a special character",
    "sim": "slide contains the board simulator",
    "q": "paragraph contains quoted text (the quote marks are generated)",
}


def edit_status(element, shown_text=None):
    """Can this block be rewritten in place? (editable, reason) — decided BEFORE
    the author types, so nobody is invited to edit text that cannot be saved.

    Two things make a block a dead end no matter what is typed:

      * it contains markup whose displayed text is GENERATED at build time
        (math, an xref, a character entity). That text has no counterpart in
        the source, so the block can never round-trip and every save would be
        refused as a mismatch.
      * none of its text is its own — every character belongs to nested inline
        markup, so there is nothing here this can safely rewrite.

    A block holding ANY inline markup is a dead end too, and this is the case
    that cost real work before it was one. The write is refused per changed
    span, so editing the prose *around* <c>GPIOA</c> does land — which made
    partial editing look supportable, and the browser marked the marked-up
    words contenteditable=false so they could not be typed into.

    That protection does not hold. Selecting a block and retyping it deletes
    the non-editable spans outright: the selection reads as just the owned
    text, so the edit looks safe right up until the replacement removes the
    markup from the DOM and the save is refused — after the rewording is done.
    Since the guard cannot be trusted, the offer is withdrawn: a block with
    markup opens in the editor, where every kind of edit to it actually works.

    The last test is the catch-all, and the reason this takes `shown_text`:
    apply_edit demands that what the page displayed matches the source EXACTLY
    before it will write, so anything that renders differently from its source
    is a dead end no matter how it got that way. The named cases above give a
    better message; this catches the rest — most usefully a page built before
    the source last changed, which no list of tags could anticipate.
    """
    tag = generated_markup(element)
    if tag:
        return False, BLOCKED_BY.get(tag, "paragraph contains generated <%s>" % tag)
    flat, _starts, _ends, owned = element.flatten()
    if not any(owned):
        return False, "every word here belongs to inline markup"
    if not all(owned):
        return False, ("this has inline markup in it "
                       "(code, emphasis, a term or a colour span)")
    if shown_text is not None and flat != normalize(shown_text):
        return False, ("this page doesn't match the source exactly "
                       "(it may have been built before the last edit)")
    return True, None


class Locator:
    def __init__(self, project_dir: str):
        self.project_dir = os.path.abspath(project_dir)
        self.index = SourceIndex(os.path.join(self.project_dir, "source"))

    def _xml_id_hint(self, html_id: str):
        """Find the source element a PreTeXt-generated HTML id descends from.

        PreTeXt numbers auto-generated ids off the nearest ancestor that has a
        real xml:id: "integers-intro-5-1-2" is a descendant of "integers-intro".
        We don't try to follow the numbering (its rules are an implementation
        detail and change with generated content) - we just strip the numeric
        tail to recover the ancestor, which narrows the text search to one
        subtree and makes a repeated sentence unambiguous.
        """
        if not html_id:
            return None
        parts = html_id.split("-")
        while parts:
            candidate = "-".join(parts)
            element = self.index.by_xml_id(candidate)
            if element is not None:
                return element
            if not parts[-1].isdigit():
                break
            parts.pop()
        return None

    def locate(self, text: str, html_id: str = ""):
        self.index.refresh()
        needle = normalize(text)
        if not needle:
            return None

        hint = self._xml_id_hint(html_id)
        candidates = [e for e in self.index.elements if e.tag in TEXT_ELEMENTS]
        if hint is not None:
            scoped = [
                e for e in candidates
                if e.path == hint.path
                and e.inner_start >= hint.inner_start
                and e.inner_end <= hint.inner_end
            ]
            # Fall back to the whole tree if the hint's subtree has nothing -
            # better a project-wide match than none at all.
            candidates = scoped or candidates

        exact = [e for e in candidates if e.text() == needle]
        if exact:
            # The tightest element containing exactly this text is the one that
            # was clicked; anything longer is an ancestor that merely wraps it.
            return min(exact, key=lambda e: e.inner_end - e.inner_start), 1.0

        best, best_score = None, 0.0
        for element in candidates:
            haystack = element.text()
            if not haystack:
                continue
            # Cheap prefilter: a real match can't differ hugely in length.
            if not (0.5 <= len(haystack) / len(needle) <= 2.0):
                continue
            score = difflib.SequenceMatcher(None, haystack, needle).ratio()
            if score > best_score:
                best, best_score = element, score

        if best is not None and best_score >= MATCH_THRESHOLD:
            return best, best_score

        # Nothing matched as a whole. Before giving up, try the fragment case
        # (see FRAGMENT_COVERAGE): a paragraph broken up by display math.
        if len(needle) >= 20:
            best, best_cov = None, 0.0
            for element in candidates:
                haystack = text_without_math(element)
                if len(haystack) < 20:
                    continue
                matcher = difflib.SequenceMatcher(None, haystack, needle)
                covered = sum(b.size for b in matcher.get_matching_blocks())
                coverage = covered / len(needle)
                # Prefer the tightest element when two cover equally well; a
                # parent wrapping the clicked block covers it just as fully.
                span = element.inner_end - element.inner_start
                if coverage > best_cov or (
                    coverage == best_cov and best is not None
                    and span < best.inner_end - best.inner_start
                ):
                    best, best_cov = element, coverage
            if best is not None and best_cov >= FRAGMENT_COVERAGE:
                return best, best_cov
        return None

    def in_project(self, path: str) -> bool:
        source = os.path.join(self.project_dir, "source")
        return os.path.abspath(path).startswith(source + os.sep)

    def deck_path(self, deck: str):
        """Resolve a deck name to assets/decks/<deck>.json, or None.

        The name comes straight off a URL, so it is checked against a strict
        allow-list (letters, digits, _ and -) before being joined - a crafted
        "../.." must not be able to reach a file outside the decks directory.
        """
        if not deck or not all(c.isalnum() or c in "_-" for c in deck):
            return None
        decks = os.path.realpath(os.path.join(self.project_dir, "assets", "decks"))
        path = os.path.realpath(os.path.join(decks, deck + ".json"))
        if not path.startswith(decks + os.sep):
            return None
        return path if os.path.isfile(path) else None


def open_in_editor(path: str, line: int) -> str:
    """Launch the user's editor at a file and line. Returns what it used."""
    override = os.environ.get("PTX_EDITOR")
    if override:
        subprocess.Popen(
            [part.replace("{file}", path).replace("{line}", str(line))
             for part in override.split()]
        )
        return override

    sublime = shutil.which("subl") or (
        "/Applications/Sublime Text.app/Contents/SharedSupport/bin/subl"
    )
    if os.path.exists(sublime):
        subprocess.Popen([sublime, f"{path}:{line}"])
        return "subl"

    code = shutil.which("code")
    if code:
        subprocess.Popen([code, "-g", f"{path}:{line}"])
        return "code"

    # Last resort: hand it to macOS, which at least opens the right file.
    subprocess.Popen(["open", path])
    return "open"


# ----------------------------------------------------------------------------
# The deck half: assets/decks/<id>.json.
#
# A deck is a thin playlist. Its "ref" slides carry no content - they name a
# <slide> block in source/*.ptx, which the /locate and /patch endpoints above
# already handle. What lives HERE is the in-class glue written in the JSON
# itself (title, section, agenda, recap, notice, prompt), which the deck
# player's slide form edits.
#
# These walk the raw JSON text rather than round-tripping through json.dump,
# for two reasons: json.load discards the line numbers an editor needs, and a
# reserialize would reflow the whole deck on every one-field edit, turning a
# caption fix into a hundred-line diff. Ported from the ENGS 20 book.
# ----------------------------------------------------------------------------


def deck_slide_line(text: str, index: int) -> int:
    """1-based line of the Nth (1-based) object in the top-level "slides" array.

    Track string state so braces inside strings don't count, and only count
    elements at the array's own top level (a slide's own nested objects and
    arrays - an items list - must not be miscounted as slides). Falls back to
    line 1 if the structure isn't found: opening the file at the top is still
    more useful than refusing.
    """
    key = text.find('"slides"')
    if key == -1:
        return 1
    i = text.find("[", key)
    if i == -1:
        return 1
    i += 1  # step past the opening [ so depth 0 means "directly in the array"
    depth = count = 0
    in_str = esc = False
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in "{[":
            if depth == 0:
                count += 1
                if count == index:
                    return text.count("\n", 0, i) + 1
            depth += 1
        elif c in "}]":
            if depth == 0:
                break  # the slides array's own closing bracket
            depth -= 1
        i += 1
    return 1


def array_element_span(text: str, key: str, position: int):
    """(start, end) char offsets of the position-th (1-based) top-level element
    of the "<key>": [...] array, end just past its closing brace; or None.

    Same raw-text walk as deck_slide_line, but returning the element's whole
    span so a single object can be replaced without reformatting the rest of
    the file.
    """
    k = text.find('"%s"' % key)
    if k == -1:
        return None
    i = text.find("[", k)
    if i == -1:
        return None
    i += 1
    depth = count = 0
    in_str = esc = False
    start = None
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c in "{[":
            if depth == 0:
                count += 1
                if count == position:
                    start = i
            depth += 1
        elif c in "}]":
            if depth == 0:
                break  # the array's own closing bracket
            depth -= 1
            if depth == 0 and start is not None:
                return (start, i + 1)
        i += 1
    return None


def _scan_string(s: str, i: int) -> int:
    """Index just past the JSON string starting at s[i] == '"'."""
    i += 1
    while i < len(s):
        if s[i] == "\\":
            i += 2
            continue
        if s[i] == '"':
            return i + 1
        i += 1
    return i


def _scan_value(s: str, i: int) -> int:
    """Index just past the JSON value starting at s[i]."""
    c = s[i]
    if c == '"':
        return _scan_string(s, i)
    if c in "{[":
        depth = 0
        while i < len(s):
            ch = s[i]
            if ch == '"':
                i = _scan_string(s, i)
                continue
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        return i
    while i < len(s) and s[i] not in ",}] \t\r\n":  # number / true / false / null
        i += 1
    return i


def _top_level_fields(text: str, obj_start: int, obj_end: int):
    """(name, key_start, value_start, value_end) for each field directly in the
    object spanning [obj_start, obj_end) (obj_start at '{', obj_end past '}')."""
    fields = []
    i = obj_start + 1
    while i < obj_end:
        while i < obj_end and text[i] in " \t\r\n":
            i += 1
        if i >= obj_end or text[i] != '"':
            break
        key_start = i
        key_end = _scan_string(text, i)
        name = json.loads(text[key_start:key_end])
        j = key_end
        while j < obj_end and text[j] in " \t\r\n":
            j += 1
        if j >= obj_end or text[j] != ":":
            break
        j += 1
        while j < obj_end and text[j] in " \t\r\n":
            j += 1
        value_end = _scan_value(text, j)
        fields.append((name, key_start, j, value_end))
        k = value_end
        while k < obj_end and text[k] in " \t\r\n":
            k += 1
        if k < obj_end and text[k] == ",":
            k += 1
        i = k
    return fields


def _dump_value(value, field_indent: str) -> str:
    """Serialize a field value in the deck's house style: a top-level array
    (an agenda's items) one entry per line, everything else on one line."""
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, indent=2).replace("\n", "\n" + field_indent)
    return json.dumps(value, ensure_ascii=False)


def patch_object_fields(text: str, span, updates) -> str:
    """Apply field updates to the object at span, touching ONLY the changed
    fields' text. Untouched fields are left byte-for-byte, so editing one field
    never reflows the rest of the slide. A value of None / "" / [] removes the
    field."""
    obj_start, obj_end = span
    multiline = "\n" in text[obj_start:obj_end]
    fields = _top_level_fields(text, obj_start, obj_end)
    by_name = {f[0]: f for f in fields}

    field_indent = ""
    if fields and multiline:
        nl = text.rfind("\n", obj_start, fields[0][1])
        if nl != -1:
            field_indent = text[nl + 1:fields[0][1]]
        else:
            # No newline before the first field: this book's decks open a slide
            # with several fields on the brace's own line —
            #     { "type": "agenda", "title": "Today", "items": [
            # — so there is no existing field indent to copy. Fall back to the
            # indentation of the line the object starts on, which is what its
            # own continuation lines (the items, the closing bracket) already
            # line up against. Without this a re-dumped array lands at column 0.
            line_start = text.rfind("\n", 0, obj_start) + 1
            lead = text[line_start:obj_start]
            field_indent = lead[:len(lead) - len(lead.lstrip())]

    edits = []  # (start, end, replacement), applied back to front
    for name, value in updates.items():
        removing = value is None or value == "" or value == []
        if name in by_name:
            _, key_start, value_start, value_end = by_name[name]
            if not removing:
                edits.append((value_start, value_end, _dump_value(value, field_indent)))
                continue
            # Drop the whole "key": value pair, plus one comma, leaving no gap.
            after = value_end
            while after < obj_end and text[after] in " \t\r\n":
                after += 1
            if after < obj_end and text[after] == ",":
                # not the last field: remove from this line's newline to the comma
                line_nl = text.rfind("\n", obj_start, key_start)
                edits.append((line_nl if line_nl != -1 else key_start, after + 1, ""))
            else:
                # last field: remove the preceding comma through this value
                p = key_start - 1
                while p > obj_start and text[p] in " \t\r\n":
                    p -= 1
                edits.append((p if text[p] == "," else key_start, value_end, ""))
        elif not removing:
            # Add as the last field.
            insert_at = fields[-1][3] if fields else obj_start + 1
            body = '"%s": %s' % (name, _dump_value(value, field_indent))
            edits.append((insert_at, insert_at,
                          (",\n" + field_indent + body) if multiline else (", " + body)))

    for start, end, replacement in sorted(edits, key=lambda e: e[0], reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def slide_fingerprint(text: str, span) -> str:
    """A short hash of one slide's exact text in the deck file.

    Handed out when a form is opened and checked when it saves, so an edit made
    to the deck in between — by hand in the editor, by a git pull — is caught
    instead of being silently overwritten by a form that never saw it.
    """
    return hashlib.sha1(text[span[0]:span[1]].encode("utf-8")).hexdigest()[:12]


def mirror_to_served(project_dir: str, deck: str, text: str):
    """Authoring convenience: the preview serves a BUILD, not the source, so
    refresh the served copy too - otherwise a reload would show the pre-edit
    deck until the next build. web-deck is the one the player runs from;
    web-edit is mirrored too so the two previews never disagree. Best-effort
    and silent if a target isn't built."""
    for target in ("web-deck", "web-edit"):
        served = os.path.join(project_dir, "output", target,
                              "external", "decks", deck + ".json")
        try:
            if os.path.isfile(served):
                with open(served, "w", encoding="utf-8") as handle:
                    handle.write(text)
        except OSError:
            pass


def apply_edit(element, old_text: str, new_text: str):
    """Rewrite an element's own visible text in place, preserving everything else.

    Only the bytes that actually changed are touched, and only where they belong
    to the block's own character data. Anything owned by nested inline markup
    (<c>, <em>, ...) is off limits, and an edit reaching into it is refused
    rather than guessed at.

    That restriction is doing more work than it looks. Requiring merely that the
    result stay well-formed is not enough: difflib is happy to align an
    unrelated word onto the text inside a <c>, so rewriting "Recall that
    <c>5/2=2</c> in C." wholesale yields the perfectly well-formed but absurd
    "Integer division truncates toward <c>zero</c> always." Markup must not
    migrate onto words it was never meant to mark, so edits that would move it
    get handed to the editor instead.
    """
    flat, starts, ends, owned = element.flatten()
    if flat != normalize(old_text):
        tag = generated_markup(element)
        if tag:
            return None, (f"This block contains <{tag}>, whose displayed text is "
                          "generated when the book is built and has no counterpart "
                          "in the source, so it can't be edited in place. "
                          "Alt-click to open it in your editor instead.")
        return None, ("The source no longer matches what the preview showed - "
                      "it may have changed since this page was built.")

    new_flat = normalize(new_text)
    if new_flat == flat:
        return None, None  # nothing to do

    with open(element.path, "rb") as handle:
        data = handle.read()

    edits = []
    matcher = difflib.SequenceMatcher(None, flat, new_flat)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            continue
        if op == "insert":
            # Anchor the insertion just after the preceding owned character, so
            # that new text always lands in this block's own character data and
            # never inside a nested element's tags.
            if i1 > 0 and owned[i1 - 1]:
                start = end = ends[i1 - 1]
            elif i1 < len(starts) and owned[i1]:
                start = end = starts[i1]
            elif not flat:
                start = end = element.inner_start
            else:
                return None, REFUSAL
        else:
            if not all(owned[i1:i2]):
                return None, REFUSAL
            start, end = starts[i1], ends[i2 - 1]

        # Belt and braces: character data can never contain "<", so a span that
        # does would be reaching across a tag boundary. The ownership test above
        # should already have caught it.
        if b"<" in data[start:end]:
            return None, REFUSAL
        # Escape on the way in. The author is typing prose, not XML, so an "&"
        # or "<" they type is a literal one — written raw it would produce a
        # file that no longer parses, which is the same failure as the stray
        # "212;" this pair of fixes is about, just louder.
        inserted = (new_flat[j1:j2]
                    .replace("&", "&amp;")
                    .replace("<", "&lt;"))
        edits.append((start, end, inserted.encode("utf-8")))

    # Apply back to front so earlier offsets stay valid.
    for start, end, replacement in sorted(edits, reverse=True):
        data = data[:start] + replacement + data[end:]

    with open(element.path, "wb") as handle:
        handle.write(data)
    return len(edits), None


def make_handler(locator: Locator):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, payload, status=200):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            # The preview is served from a different local port than this
            # helper, so the browser treats these as cross-origin.
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass  # the server's own reporting is friendlier than access logs

        def do_OPTIONS(self):
            self._send({})

        def _open_deck(self, query):
            """Open assets/decks/<deck>.json at the Nth slide in the editor.

            This is the deck player's plain Alt-click on a glue slide, and the
            escape hatch for anything the slide form can't express: it puts the
            author in the raw JSON at the right entry.
            """
            deck = query.get("deck", [""])[0]
            path = locator.deck_path(deck)
            if path is None:
                return self._send({"error": "No such deck."}, 404)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            try:
                slide = int(query.get("slide", ["0"])[0])
            except ValueError:
                slide = 0
            line = deck_slide_line(text, slide) if slide > 0 else 1
            editor = open_in_editor(path, line)
            relative = os.path.relpath(path, locator.project_dir)
            print(f"  -> {relative}:{line} ({editor})")
            return self._send({"file": relative, "line": line})

        def _open_slide(self, query):
            """Open a <slide> block in source/*.ptx by its xml:id.

            The player's ref slides are extracted from a built page, so the
            author clicking one wants the BLOCK, not whichever paragraph the
            pointer happened to be over. Looked up by id rather than by text,
            so it works on a slide whose body is a figure, a <sim>, or a table
            with no clickable prose at all.
            """
            locator.index.refresh()
            element = locator.index.by_xml_id(query.get("id", [""])[0])
            if element is None:
                return self._send({"error": "No such slide block."}, 404)
            if not locator.in_project(element.path):
                return self._send({"error": "refusing to open outside source/"}, 403)
            editor = open_in_editor(element.path, element.start_line)
            relative = os.path.relpath(element.path, locator.project_dir)
            print(f"  -> {relative}:{element.start_line} ({editor})")
            return self._send({
                "file": relative, "line": element.start_line, "tag": element.tag,
            })

        def _deck_slide(self, query):
            """The current text of one slide in a deck, straight from the file.

            The player's copy of a deck is whatever it loaded at page load, and
            a deck hand-edited since then makes that a stale copy — the slide
            form would open showing the old values and, on save, write them back
            over the newer file. So the form populates from here instead, and
            carries the fingerprint below back to the save.
            """
            deck = query.get("deck", [""])[0]
            path = locator.deck_path(deck)
            if path is None:
                return self._send({"error": "No such deck."}, 404)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            data = json.loads(text)
            try:
                position = int(query.get("slide", ["0"])[0])
            except ValueError:
                position = 0
            if not 1 <= position <= len(data.get("slides", [])):
                return self._send({"error": "slide not found"}, 404)
            span = array_element_span(text, "slides", position)
            if span is None:
                return self._send({"error": "could not locate slide in file"}, 500)
            return self._send({
                "slide": data["slides"][position - 1],
                "fingerprint": slide_fingerprint(text, span),
            })

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/deck-slide":
                return self._deck_slide(parse_qs(url.query))
            if url.path == "/open-deck":
                return self._open_deck(parse_qs(url.query))
            if url.path == "/open-slide":
                return self._open_slide(parse_qs(url.query))
            if url.path != "/locate":
                return self._send({"error": "not found"}, 404)

            query = parse_qs(url.query)
            found = locator.locate(
                query.get("text", [""])[0], query.get("id", [""])[0]
            )
            if not found:
                return self._send({"error": "No matching source found."}, 404)

            element, score = found
            relative = os.path.relpath(element.path, locator.project_dir)
            editable, reason = edit_status(element, query.get("text", [""])[0])
            # ?open=1 opens the editor. The browser also sends it when a block
            # turns out not to be line-editable, so a refusal hands the author
            # straight to the file instead of stopping at a message.
            if query.get("open", ["0"])[0] == "1":
                editor = open_in_editor(element.path, element.start_line)
                print(f"  -> {relative}:{element.start_line} ({editor})")
            return self._send({
                "file": relative,
                "path": element.path,
                "line": element.start_line,
                "tag": element.tag,
                "score": round(score, 3),
                "text": element.text(),
                # Asked BEFORE the author starts typing (see edit_status).
                "editable": editable,
                "blocked": reason,
            })

        # Content fields a slide form may set, across every glue type: title
        # (all), subtitle (title), kicker (section), items (agenda / recap /
        # notice), body + note (prompt), presenterNote (any).
        #
        # This allow-list is the guard the design rests on. "type", "page",
        # "slide", "instructor" and "room" are deliberately absent, so a form
        # save can never rewrite which book element a ref resolves to, retype a
        # slide, or quietly drop an instructor-only flag - the fields that
        # decide what students see are not reachable from the browser.
        DECK_FIELDS = {"title", "subtitle", "kicker", "body", "items",
                       "note", "presenterNote"}

        def _patch_deck(self):
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send({"error": "bad request"}, 400)

            path = locator.deck_path(payload.get("deck", ""))
            if path is None:
                return self._send({"error": "No such deck."}, 404)

            # Validate up front: strings (or null to clear), and items a list of
            # strings. Anything off-shape is refused whole rather than written
            # partly.
            updates = {}
            for name, value in (payload.get("fields") or {}).items():
                if name not in self.DECK_FIELDS:
                    continue
                if name == "items" or isinstance(value, list):
                    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
                        return self._send({"error": "%s must be a list of strings" % name}, 400)
                    updates[name] = value
                elif value is None or isinstance(value, str):
                    updates[name] = value
                else:
                    return self._send({"error": "bad type for %s" % name}, 400)

            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            data = json.loads(text)

            try:
                position = int(payload.get("slide", 0))
            except (TypeError, ValueError):
                position = 0
            if not 1 <= position <= len(data.get("slides", [])):
                return self._send({"error": "slide not found"}, 404)

            # Refuse to patch a slide the player thinks is a different one than
            # the file does. The player sends the type it rendered; if the deck
            # changed underneath (the parallel authoring session, a git pull),
            # writing by position would land the edit on the wrong slide.
            expected = payload.get("type")
            actual = data["slides"][position - 1].get("type")
            if expected and expected != actual:
                return self._send({
                    "error": "This deck changed on disk (slide %d is now a "
                             "'%s', not a '%s'). Reload the deck and try again."
                             % (position, actual, expected)}, 409)

            span = array_element_span(text, "slides", position)
            if span is None:
                return self._send({"error": "could not locate slide in file"}, 500)

            # Refuse to write over a change this form never saw (see
            # slide_fingerprint). The type check above catches a slide that
            # became a different KIND of slide; this catches any edit at all.
            #
            # Required, not optional: treating a missing or empty fingerprint as
            # "no check needed" would mean the one bug that silently disables
            # this guard is also the easiest one to write.
            sent = payload.get("fingerprint")
            if not sent:
                return self._send({"error": "fingerprint required — reopen the form"}, 400)
            if sent != slide_fingerprint(text, span):
                return self._send({
                    "error": "This slide changed on disk since the form was "
                             "opened — reload the deck so you're editing the "
                             "current version, or your edit would overwrite it."
                }, 409)

            new_text = patch_object_fields(text, span, updates)
            # The source is the truth; never leave it unparseable.
            try:
                json.loads(new_text)
            except json.JSONDecodeError:
                return self._send({"error": "internal: refusing to write invalid JSON"}, 500)

            with open(path, "w", encoding="utf-8") as handle:
                handle.write(new_text)
            mirror_to_served(locator.project_dir, payload.get("deck", ""), new_text)

            relative = os.path.relpath(path, locator.project_dir)
            line = text.count("\n", 0, span[0]) + 1
            print(f"  patched {relative}:{line}")
            return self._send({"file": relative, "line": line})

        def _patch_attr(self):
            """Rewrite one attribute (title, kicker, subtitle) of a <slide> block.

            The words of a card or a slide title are attributes of its <slide>,
            not text inside it, so /patch cannot reach them. Refuses unless the
            attribute still holds the text the player showed.
            """
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send({"error": "bad request"}, 400)
            attr = payload.get("attr", "")
            if attr not in ("title", "kicker", "subtitle"):
                return self._send({"error": "that attribute is not editable here"}, 400)
            new_value = payload.get("newText", "")
            if not isinstance(new_value, str) or not new_value.strip() or "\n" in new_value:
                return self._send({"error": "the new text must be one non-empty line"}, 400)
            locator.index.refresh()
            element = locator.index.by_xml_id(payload.get("id", ""))
            if element is None or element.tag != "slide":
                return self._send({"error": "No such slide block."}, 404)
            if not locator.in_project(element.path):
                return self._send({"error": "refusing to write outside source/"}, 403)
            with open(element.path, encoding="utf-8") as handle:
                text = handle.read()
            quoted = r"""(?:[^>"']|"[^"]*"|'[^']*')*"""
            tag = re.search(r'<slide\b%s\bxml:id="%s"%s>' % (quoted, re.escape(payload["id"]), quoted), text)
            if tag is None:
                return self._send({"error": "could not find the slide's start tag"}, 500)
            held = re.search(r'(\s%s=)("([^"]*)"|\'([^\']*)\')' % attr, tag.group(0))
            if held is None:
                return self._send({"error": "this slide has no %s attribute" % attr}, 404)
            unescape = lambda v: (v.replace("&quot;", '"').replace("&apos;", "'")
                                  .replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
            current = unescape(held.group(3) if held.group(3) is not None else held.group(4))
            if " ".join(current.split()) != " ".join(payload.get("text", "").split()):
                return self._send({"error": "This %s changed on disk since the slide was "
                                   "shown; reload the deck first." % attr}, 409)
            escaped = (new_value.strip().replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;").replace('"', "&quot;"))
            new_tag = (tag.group(0)[:held.start()] + held.group(1) + '"' + escaped + '"'
                       + tag.group(0)[held.end():])
            with open(element.path, "w", encoding="utf-8") as handle:
                handle.write(text[:tag.start()] + new_tag + text[tag.end():])
            relative = os.path.relpath(element.path, locator.project_dir)
            line = text.count("\n", 0, tag.start()) + 1
            print(f"  edited {relative}:{line} ({attr})")
            return self._send({"file": relative, "line": line, "changes": 1})

        def do_POST(self):
            url = urlparse(self.path)
            if url.path == "/patch-deck":
                return self._patch_deck()
            if url.path == "/patch-attr":
                return self._patch_attr()
            if url.path != "/patch":
                return self._send({"error": "not found"}, 404)

            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send({"error": "bad request"}, 400)

            found = locator.locate(payload.get("text", ""), payload.get("id", ""))
            if not found:
                return self._send({"error": "No matching source found."}, 404)

            element, _score = found
            if not locator.in_project(element.path):
                return self._send({"error": "refusing to write outside source/"}, 403)

            count, problem = apply_edit(
                element, payload.get("text", ""), payload.get("newText", "")
            )
            if problem:
                return self._send({"error": problem}, 409)

            relative = os.path.relpath(element.path, locator.project_dir)
            if count:
                print(f"  edited {relative}:{element.start_line} "
                      f"({count} change{'s' if count != 1 else ''})")
            return self._send({
                "file": relative,
                "line": element.start_line,
                "changes": count or 0,
            })

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), ".."
    ), help="PreTeXt project root (the directory holding project.ptx)")
    parser.add_argument("--port", type=int, default=8927)
    args = parser.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isdir(os.path.join(project, "source")):
        sys.exit(f"No source/ directory in {project}")

    locator = Locator(project)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(locator))

    print(f"PreTeXt edit server: {os.path.basename(project)} on port {args.port}")
    print(f"  indexed {len(locator.index.elements)} elements")
    print("  alt-click a paragraph in the book to open it here; "
          "alt-shift-click to edit in place")
    print("  the deck player uses the same keys on slides "
          "(bullets and captions in source, glue text in decks/*.json)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()

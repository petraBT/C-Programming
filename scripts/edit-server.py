#!/usr/bin/env python3
"""
Authoring helper: jump from the rendered book back to its PreTeXt source.

Run this alongside a local preview build, then in the book:

  * alt-click any paragraph  -> opens that spot in your text editor  (option A)
  * alt-shift-click          -> edit the text in place, save, done   (option C)

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


def deck_slide_line(text: str, index: int) -> int:
    """1-based line of the Nth (1-based) object in the top-level "slides" array.

    json.load would give us the slide but discards line numbers, so walk the
    raw text instead. Track string state so braces inside strings don't count,
    and only count elements at the array's own top level (a slide's own nested
    objects/arrays - a table, a bullet list - must not be miscounted as slides).
    Falls back to line 1 if the structure isn't found: opening the file at the
    top is still more useful than refusing.
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


def json_id_line(text: str, ident: str) -> int:
    """1-based line of the object whose "id" is `ident`, or 1 if not found.

    For files keyed by id rather than array position - the icebreaker bank,
    decks/icebreakers.json, which an icebreaker slide only references. Matched
    with tolerance for whatever spacing the file uses around the colon.
    """
    match = re.search(r'"id"\s*:\s*"' + re.escape(ident) + r'"', text)
    return text.count("\n", 0, match.start()) + 1 if match else 1


def array_element_span(text: str, key: str, position: int):
    """(start, end) char offsets of the position-th (1-based) top-level element
    of the "<key>": [...] array, end just past its closing brace; or None.

    Same raw-text walk as deck_slide_line, but returning the element's whole
    span so a single object can be replaced without reformatting the rest of
    the file. Only elements at the array's own level are counted; a slide's
    own nested objects/arrays are stepped over.
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
    (bullets, demo paragraphs) one item per line, a table object one key per
    line with its own short arrays kept inline, everything else on one line."""
    if isinstance(value, dict):
        inner = field_indent + "  "
        pairs = [inner + json.dumps(k, ensure_ascii=False) + ": " +
                 json.dumps(v, ensure_ascii=False) for k, v in value.items()]
        return "{\n" + ",\n".join(pairs) + "\n" + field_indent + "}"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, indent=2).replace("\n", "\n" + field_indent)
    return json.dumps(value, ensure_ascii=False)


def patch_object_fields(text: str, span, updates) -> str:
    """Apply field updates to the object at span, touching ONLY the changed
    fields' text. Untouched fields - including compact nested tables - are left
    byte-for-byte, so editing one field never reflows the rest of the slide.
    A value of None / "" / [] removes the field."""
    obj_start, obj_end = span
    multiline = "\n" in text[obj_start:obj_end]
    fields = _top_level_fields(text, obj_start, obj_end)
    by_name = {f[0]: f for f in fields}

    field_indent = ""
    if fields and multiline:
        nl = text.rfind("\n", obj_start, fields[0][1])
        if nl != -1:
            field_indent = text[nl + 1:fields[0][1]]

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


def mirror_to_served(project_dir: str, deck: str, text: str):
    """Authoring convenience: the local preview serves output/web-edit, not the
    source, so refresh the served copy too - otherwise a reload would show the
    pre-edit deck until the next build. Best-effort and silent if absent."""
    served = os.path.join(project_dir, "output", "web-edit",
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
        edits.append((start, end, new_flat[j1:j2].encode("utf-8")))

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

            The deck player's 'ref' slides open their book page (handled by
            ptx-edit.js in the slide iframe); every other slide is authored in
            the deck JSON, and this is how it opens from the player.
            """
            deck = query.get("deck", [""])[0]
            path = locator.deck_path(deck)
            if path is None:
                return self._send({"error": "No such deck."}, 404)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            # id wins over slide: an icebreaker slide only references an entry in
            # the shared bank (deck=icebreakers), so it opens by id, not index.
            ident = query.get("id", [""])[0]
            if ident:
                line = json_id_line(text, ident)
            else:
                try:
                    slide = int(query.get("slide", ["0"])[0])
                except ValueError:
                    slide = 0
                line = deck_slide_line(text, slide) if slide > 0 else 1
            editor = open_in_editor(path, line)
            relative = os.path.relpath(path, locator.project_dir)
            print(f"  -> {relative}:{line} ({editor})")
            return self._send({"file": relative, "line": line})

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/open-deck":
                return self._open_deck(parse_qs(url.query))
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
            })

        # Content fields a slide form may set. Nothing else is touched, so the
        # form can never rewrite a slide's type, page, focus, or id.
        DECK_FIELDS = {"title", "body", "note", "prompt", "startPoint", "items", "table"}

        def _patch_deck(self):
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._send({"error": "bad request"}, 400)

            path = locator.deck_path(payload.get("deck", ""))
            if path is None:
                return self._send({"error": "No such deck."}, 404)

            # Validate the fields up front: strings (or null to clear), and
            # items a list of strings. Anything off-shape is refused whole.
            updates = {}
            for name, value in (payload.get("fields") or {}).items():
                if name not in self.DECK_FIELDS:
                    continue
                if name == "table":
                    if value is None:
                        updates[name] = None
                    elif (isinstance(value, dict)
                          and all(isinstance(value.get(k), list)
                                  and all(isinstance(x, str) for x in value[k])
                                  for k in ("columns", "rows"))):
                        # keep just the two known keys, in a stable order
                        updates[name] = {"columns": value["columns"], "rows": value["rows"]}
                    else:
                        return self._send({"error": "table needs columns and rows lists of strings"}, 400)
                elif name == "items" or isinstance(value, list):
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

            ident = payload.get("id")
            if ident is not None:
                bank = data.get("icebreakers", [])
                position = next((i + 1 for i, e in enumerate(bank) if e.get("id") == ident), None)
                key = "icebreakers"
            else:
                key = "slides"
                try:
                    position = int(payload.get("slide", 0))
                except (TypeError, ValueError):
                    position = 0
                if not 1 <= position <= len(data.get("slides", [])):
                    position = None
            if not position:
                return self._send({"error": "slide not found"}, 404)

            span = array_element_span(text, key, position)
            if span is None:
                return self._send({"error": "could not locate slide in file"}, 500)

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

        def do_POST(self):
            url = urlparse(self.path)
            if url.path == "/patch-deck":
                return self._patch_deck()
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
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()

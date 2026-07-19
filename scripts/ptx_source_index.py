"""
Index of every element in a PreTeXt source tree, with byte-exact locations.

This is the shared foundation for the authoring "edit from the preview" tools
(see scripts/edit-server.py): given a chunk of text that a reader clicked on in
the built HTML, find which .ptx file it came from, which line it starts on, and
- for in-place editing - exactly which bytes of that file hold its text.

Why expat rather than lxml: lxml gives us element.sourceline but no column or
byte offset, and re-serializing a parsed tree to write a change back would
reformat the entire file. We need surgical edits that leave every other byte of
the author's file untouched, so we parse with expat (which exposes
CurrentByteIndex) and treat the file as bytes throughout, only decoding at the
edges.
"""

import os
import re
import xml.parsers.expat
from dataclasses import dataclass, field


# Elements whose text a person would plausibly click on and want to edit.
# Restricting matches to these keeps a search for a sentence from returning the
# <section> and <chapter> that merely contain it.
TEXT_ELEMENTS = {
    "p", "li", "title", "cell", "term", "q", "blockquote", "caption",
    "pre", "line", "attribution", "em", "alert", "insert", "delete", "stale",
}

# Elements whose text is in the source but renders nowhere in the running prose
# - <idx>division</idx> sits inside a sentence but only ever surfaces in the
# index. Their content has to be skipped or the source text won't match what a
# reader clicked on, and an in-place edit would compute its byte offsets against
# characters that aren't on screen.
INVISIBLE_ELEMENTS = {"idx", "notation"}

# Whitespace runs in XML source collapse to a single space in rendered HTML, so
# every comparison happens on a normalized form.
_WS = re.compile(r"\s+")

# PreTeXt curls quotes on the way to HTML: the source says What's, the page says
# What's. Folding them back is what lets an in-place edit of such a paragraph
# work at all - without it the source and the preview never compare equal and
# every edit is refused as "stale".
#
# Every entry here MUST be a single character mapping to exactly one character.
# The byte offset of each character is what makes a surgical edit possible, and
# a 1:n replacement (an ellipsis becoming "...") would slide every offset after
# it out of alignment. Dashes are deliberately left alone for that reason: a
# source "--" rendering as a single en dash is not a 1:1 fold. A paragraph
# containing one still locates correctly by fuzzy match; only editing it in
# place is declined.
TYPOGRAPHIC = {
    "‘": "'", "’": "'",   # single curly quotes
    "“": '"', "”": '"',   # double curly quotes
}


def fold(ch: str) -> str:
    return TYPOGRAPHIC.get(ch, ch)


@dataclass
class Element:
    tag: str
    path: str              # absolute path of the .ptx file
    xml_id: str | None
    start_line: int        # 1-based, for jumping an editor to the element
    inner_start: int       # byte offset just past the start tag
    inner_end: int         # byte offset of the "<" of the end tag
    # Character data directly inside this element and its descendants, as
    # (text_bytes, byte_offset) chunks in document order. Keeping the offset per
    # chunk is what lets an edit to the flattened text be mapped back onto the
    # exact bytes it came from, skipping over any inline markup between chunks.
    # depth is 0 for data belonging directly to this element and >0 for data
    # owned by a nested element such as <c> or <em>. That distinction is what
    # keeps an in-place edit from rewriting another element's content.
    chunks: list[tuple[bytes, int, int]] = field(default_factory=list)

    def raw_text(self) -> str:
        return b"".join(c for c, _, _ in self.chunks).decode("utf-8", "replace")

    def text(self) -> str:
        return normalize(self.raw_text())

    def flatten(self) -> tuple[str, list[int], list[int], list[bool]]:
        """Normalized text, plus where each character came from and who owns it.

        Returns (text, starts, ends, owned): character i of text occupies source
        bytes [starts[i], ends[i]), and owned[i] says whether it is this
        element's own character data rather than a nested element's.

        The spans are the crux of surgical editing, and are reported rather than
        recomputed from the returned text because the two can differ: a folded
        curly quote is three bytes in the source but one character here. The
        ownership flags are the crux of *safe* editing - see apply_edit.
        """
        out: list[str] = []
        starts: list[int] = []
        ends: list[int] = []
        owned: list[bool] = []
        ws_start = -1  # byte offset where the current whitespace run began
        for data, base, depth in self.chunks:
            text = data.decode("utf-8", "replace")
            # Byte offset of character i is base + the UTF-8 length of the
            # characters before it, so multi-byte characters stay aligned.
            pos = base
            for ch in text:
                width = len(ch.encode("utf-8"))
                if ch.isspace():
                    if ws_start < 0:
                        ws_start = pos
                else:
                    if ws_start >= 0 and out:
                        # The single normalized space stands for the whole run,
                        # so deleting it in the preview really does join the two
                        # words in the source rather than silently doing nothing.
                        out.append(" ")
                        starts.append(ws_start)
                        ends.append(pos)
                        # A gap that straddles a tag boundary counts as not
                        # owned, so nothing can be written into it.
                        owned.append(owned[-1] and depth == 0)
                    ws_start = -1
                    out.append(fold(ch))
                    starts.append(pos)
                    ends.append(pos + width)
                    owned.append(depth == 0)
                pos += width
        return "".join(out), starts, ends, owned


def normalize(text: str) -> str:
    return _WS.sub(" ", "".join(fold(ch) for ch in text)).strip()


def _inner_start(data: bytes, tag_start: int) -> int:
    """Byte just past the '>' that closes the start tag beginning at tag_start.

    Expat reports where an element starts but not where its start tag ends, so
    we scan for the closing '>' ourselves, stepping over any '>' that appears
    inside a quoted attribute value.
    """
    i = tag_start
    quote = None
    while i < len(data):
        ch = data[i : i + 1]
        if quote:
            if ch == quote:
                quote = None
        elif ch in (b'"', b"'"):
            quote = ch
        elif ch == b">":
            return i + 1
        i += 1
    return len(data)


def index_file(path: str) -> list[Element]:
    """Parse one .ptx file into a flat list of Elements."""
    with open(path, "rb") as handle:
        data = handle.read()

    parser = xml.parsers.expat.ParserCreate()
    elements: list[Element] = []
    stack: list[Element] = []
    hidden = [0]  # depth of nesting inside an INVISIBLE_ELEMENTS subtree

    def start(tag, attrs):
        if hidden[0] or tag in INVISIBLE_ELEMENTS:
            hidden[0] += 1
        element = Element(
            tag=tag,
            path=path,
            xml_id=attrs.get("xml:id"),
            start_line=parser.CurrentLineNumber,
            inner_start=_inner_start(data, parser.CurrentByteIndex),
            inner_end=-1,
        )
        stack.append(element)
        elements.append(element)

    def end(_tag):
        if hidden[0]:
            hidden[0] -= 1
        element = stack.pop()
        # For a self-closing tag expat reports the element's own start here, so
        # inner_end would land before inner_start; clamp it to an empty span.
        element.inner_end = max(parser.CurrentByteIndex, element.inner_start)

    def chardata(text):
        if not stack or hidden[0]:
            return
        encoded = text.encode("utf-8")
        offset = parser.CurrentByteIndex
        # Character data belongs to the innermost element and to every ancestor,
        # so a search for a sentence finds the <p> as well as the <em> inside it.
        # Each ancestor records how far below itself the data sits: 0 means the
        # data is its own, deeper means it belongs to a nested element.
        top = len(stack) - 1
        for index, element in enumerate(stack):
            element.chunks.append((encoded, offset, top - index))

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = chardata

    try:
        parser.Parse(data, True)
    except xml.parsers.expat.ExpatError:
        # A file mid-edit may not parse. Whatever we indexed before the error is
        # still usable, and the next rebuild will pick up the rest.
        pass

    return elements


class SourceIndex:
    """Every element in a project's source tree, rebuilt when files change."""

    def __init__(self, source_dir: str):
        self.source_dir = os.path.abspath(source_dir)
        self.elements: list[Element] = []
        self._stamps: dict[str, float] = {}
        self.refresh()

    def _ptx_files(self) -> list[str]:
        found = []
        for root, _dirs, names in os.walk(self.source_dir):
            for name in names:
                # .old.ptx files are the author's own superseded drafts; editing
                # one because its text happens to match would be a silent
                # no-op on the live book.
                if name.endswith(".ptx") and not name.endswith(".old.ptx"):
                    found.append(os.path.join(root, name))
        return sorted(found)

    def refresh(self) -> bool:
        """Reindex if any file changed. Returns True if the index was rebuilt."""
        stamps = {}
        for path in self._ptx_files():
            try:
                stamps[path] = os.path.getmtime(path)
            except OSError:
                pass
        if stamps == self._stamps:
            return False
        self._stamps = stamps
        self.elements = []
        for path in stamps:
            self.elements.extend(index_file(path))
        return True

    def by_xml_id(self, xml_id: str) -> Element | None:
        for element in self.elements:
            if element.xml_id == xml_id:
                return element
        return None

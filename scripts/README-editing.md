# Editing the book from the preview

Finding the right `.ptx` file and the right spot inside it is the slow part of
making a small change. This lets you start from the rendered book instead:

| In the preview | What happens |
| --- | --- |
| **alt-click** a paragraph | opens that exact spot in your text editor |
| **alt-shift-click** a paragraph | edit the text right there; ⌘⏎ saves it to the source |

Hold <kbd>alt</kbd> and everything clickable outlines in green, so you can see
what a click would land on before you commit to it.

## Running it

One command, from the repo root:

```bash
./preview-edit.sh
```

That builds the `web-edit` target, serves it on 8931, and starts the edit server
on 8927 (which is what finds and rewrites the source). Ctrl-C stops both. If the
port is already taken it says so and carries on serving the book, so a second
copy won't fight the first.

Pair it with `watch.py`, which takes a target, and an in-place edit shows up in
the preview a few seconds later:

```bash
python3 watch.py web-edit
```

`web-edit` is deliberately kept out of `build.sh`: it is the one target carrying
a script that talks to a server able to rewrite source files, so it should never
end up in a build you share.

### Your editor

Sublime Text and VS Code are found automatically. Anything else:

```bash
PTX_EDITOR="myeditor --line {line} {file}" python3 scripts/edit-server.py
```

## How it finds the source

There is no build-time source map, and deliberately so — it would have to
reproduce PreTeXt's internal id-numbering rules, which are an implementation
detail that changes with generated content.

Instead the server keeps a byte-exact index of every element in `source/`
(`ptx_source_index.py`, built with expat because it reports byte offsets, which
lxml does not) and matches on the text you clicked. The clicked element's HTML
id is used as a hint: PreTeXt derives ids like `ch-uart-2-1` from the nearest
ancestor with a real `xml:id`, so stripping the numeric tail recovers `ch-uart`
and narrows the search to one chapter. That disambiguates a sentence that
appears in more than one place. If the hint yields nothing the search falls back
to the whole tree, and if the best match is still below 75% similarity it
reports a miss rather than opening something unrelated.

Text that is in the source but invisible in the rendered page is skipped on both
sides — `<idx>` and `<notation>` in the source, the `🔗` permalink widget in the
HTML — and curly quotes are folded back to straight ones. Otherwise neither the
matching nor the byte offsets would line up.

## What in-place editing will and won't do

Saving rewrites **only the bytes that actually changed**, so the rest of the file
— indentation, attributes, comments, the inline markup around your edit — is
left exactly as it was. A reworded sentence in a multi-line `<p>` produces a
one-line diff.

You can edit a block's **own** text freely. Text belonging to inline markup
inside it — `<term>`, `<c>`, `<em>` — is off limits, and an edit reaching into it
is refused rather than guessed at.

That rule is stricter than "keep the XML well-formed", deliberately. Requiring
only well-formedness is not enough, because the diff is happy to align an
unrelated word onto the text inside a `<term>`, quietly moving markup onto words
it was never meant to mark. So rewording the prose around
`<term>Universal Asynchronous Receiver-Transmitter (UART)</term>` works, while
rewriting the term itself is declined.

An edit is also refused if the source no longer matches what the preview showed,
which is what you get when the page is stale relative to the file. Rebuild and
try again.

Structural changes — new paragraphs, new elements, anything involving markup —
are what alt-click is for.

## Relationship to the C-Programming book

This is a port of the same tooling from `~/repos/C-Programming`, minus the parts
that book needs for its in-browser coding windows. `ptx-edit.js` is kept
byte-identical to the copy there so that fixes move across cleanly; the
coding-window handling it contains is simply inert here, since this book has no
`<cmecode>` elements. `edit-server.py` and `ptx_source_index.py` are likewise
copies rather than a shared dependency, so this repo stands on its own.

If you fix something here, port it there too, and vice versa.

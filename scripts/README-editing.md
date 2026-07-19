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

Two things, in either order:

```bash
pretext build web-edit && pretext view web-edit   # the preview
python3 scripts/edit-server.py                    # the helper, in another shell
```

Both are local-only. `web-edit` is the only target that carries
`assets/ptx-edit.js`, and it is deliberately kept out of `build.sh` and
`deploy.sh` — a deployed book must never ship a script that talks to something
able to rewrite source files.

Pair it with a rebuild watcher (ENGS28 has `watch.py`) and an in-place edit
shows up in the preview a few seconds after you save it.

### The other books

The server works on any PreTeXt project — it takes the project root:

```bash
python3 scripts/edit-server.py --project ../ENGS28
```

To use it there, copy `assets/ptx-edit.js` into that project's `assets/` and add
a `web-edit` target to its `project.ptx` mirroring the one here.

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
id is used as a hint: PreTeXt derives ids like `integers-intro-5-1-2` from the
nearest ancestor with a real `xml:id`, so stripping the numeric tail recovers
`integers-intro` and narrows the search to one subtree. That disambiguates a
sentence that appears in more than one chapter. If the hint yields nothing the
search falls back to the whole tree, and if the best match is still below 75%
similarity it reports a miss rather than opening something unrelated.

Text that is in the source but invisible in the rendered page is skipped on both
sides — `<idx>` and `<notation>` in the source, the `🔗` permalink widget in the
HTML. Otherwise neither the matching nor the byte offsets would line up.

## What in-place editing will and won't do

Saving rewrites **only the bytes that actually changed**, so the rest of the file
— indentation, attributes, comments, the inline markup around your edit — is
left exactly as it was. Editing "division behaviors" to "surprising division
behaviors" in

```xml
<p><idx>division</idx>Previously, we learned that <c>5/2=2</c>. But why?</p>
```

produces a one-word diff, with the `<idx>` and `<c>` untouched.

You can edit a block's **own** text freely. Text belonging to inline markup
inside it — `<c>`, `<em>`, and friends — is off limits, and an edit reaching into
it is refused rather than guessed at.

That rule is stricter than "keep the XML well-formed", deliberately. Requiring
only well-formedness is not enough, because the diff is happy to align an
unrelated word onto the text inside a `<c>`. Rewriting

```xml
<p>Recall that <c>5/2=2</c> in C.</p>
```

wholesale into "Integer division truncates toward zero always." produces the
perfectly well-formed but nonsensical `<c>zero</c>` — markup migrated onto a word
it was never meant to mark. So:

| Edit | |
| --- | --- |
| reword the prose around `<c>5/2=2</c>` | ✅ applied |
| rewrite the whole sentence over it | ❌ refused |
| change the `5/2=2` inside it | ❌ refused |
| reword a paragraph with no inline markup | ✅ applied |
| join two words across a source line break | ✅ applied |

Smart quotes are handled: PreTeXt renders the source's `What's` as `What's`, and
both sides are folded back to a straight quote before comparing, so editing such
a paragraph works. Only strictly one-character-to-one-character folds are
applied — every character's byte offset has to stay aligned for a surgical edit,
so an en dash rendered from `--` is left alone. Such a paragraph still locates
fine for alt-click; only editing it in place is declined.

An edit is also refused if the source no longer matches what the preview showed,
which is what you get when the page is stale relative to the file. Rebuild and
try again.

Structural changes — new paragraphs, new elements, anything involving markup —
are what alt-click is for.

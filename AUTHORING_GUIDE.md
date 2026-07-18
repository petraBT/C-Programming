# Authoring Guide: Book, Coding Window, Canvas, and the Local Tools

One place to remember everything around adding content to this book, adding
starting points (for the book or for Canvas), and running the local tools
that help with that. See `README.md` for the plain build/deploy basics of
the `web`/`web-static` targets; this file covers everything built up around
the client-side coding window and Canvas integration.

## 1. The moving pieces

- **The book itself** — PreTeXt source in `source/`, built via `pretext build
  <target>`. Three HTML targets in `project.ptx`: `web` (live Thayer server
  windows), `web-static` (read-only code blocks), `web-client` (the new
  client-side coding window — this is the one everything below is about).
- **`coding-window/`** — a *committed, built copy* (dist output) of a
  **separate repo**, `C-InBroserEnvironment`. This is the actual client-side
  C compiler/editor tool (CodeMirror + a WASM C compiler, runs entirely in
  the browser, no server). If you're changing the *tool itself* (not just
  adding starting points), you're working in that other repo — see §7.
- **`CMeCodeDir/`** — starting-point `.c` files *for the book*. Every
  `<cmecode startPoint="...">` in `source/**/*.ptx` points at a file here by
  name (no subfolders).
- **`CanvasStartDir/`** — starting-point `.c` files *for Canvas* (short
  assignments, quizzes, tests), organized in one subfolder per category
  (`Short Assignment/`, `Canvas Quiz/`, `Test/`, or any new category you
  type when saving). Not referenced by any book `.ptx` file — these exist
  purely to be `?src=`-embedded into Canvas pages.
- **`starting-points-tool/`** — a small local Node server + browser UI for
  browsing, creating, and editing starting points in both of the above, and
  generating ready-to-paste Canvas embed HTML. See §5.
- **Deployment target**: `cprog-client-preview.pages.dev` (Cloudflare
  Pages) — the only host serving `web-client` + `coding-window/` +
  `CMeCodeDir/` + `CanvasStartDir/` together with the COOP/COEP headers the
  coding window needs for interactive stdin. `deploy-client-preview.sh`
  publishes to it. See §6.

## 2. Adding new content to the book

Normal PreTeXt authoring in `source/**/*.ptx`. To preview:

```sh
pretext build web-client
```

Then either `pretext view web-client`, or serve it yourself so the
COOP/COEP-dependent bits (interactive stdin) actually work:

```sh
python3 serve-with-headers.py 8299 output/web-client
```

`pretext build` does **not** copy `coding-window/` into `output/web-client/`
itself — that directory needs to be a sibling of the built pages manually
when testing locally:

```sh
rm -rf output/web-client/coding-window
cp -R coding-window output/web-client/coding-window
```

(`deploy-client-preview.sh` does this same copy automatically when
deploying — see §6 — this manual step is only for local preview.)

## 3. Adding a new starting point *for the book*

Two ways to get the `.c` file into `CMeCodeDir/`:

- **Via the starting-points-tool** (§5): Create New → Book (CMeCodeDir) →
  fill in name + code → Save. This *only* creates the file.
- **By hand**: just drop a `<name>.c` file into `CMeCodeDir/`.

Either way, **you still have to add the actual embed to the book's source
yourself** — the tool deliberately doesn't guess where in the book a new
exercise belongs:

```xml
<cmecode startPoint="engs20p_NyourNewName" addOn="&amp;nocheck=true" height="400"></cmecode>
```

- `startPoint` must exactly match the filename (minus `.c`).
- `addOn="&amp;nocheck=true"` is a leftover convention from the Thayer-server
  era (autograder behavior) — harmless to include, ignored by the client
  tool, but not required for it either.
- `height` is in pixels; the client tool adds its own buffer on top for the
  output panel.
- If the exercise simulates file input (`fopen`/`fscanf` against a
  pre-seeded file), drop a matching `<name>.datafile.json` next to the `.c`
  file: `{"path": "my_file.txt", "data": "..."}`.

Naming convention (not enforced, just the existing pattern): most starting
points are named `engs20p_N<Description>` — the `N` marks it as
book-internal; a handful of older ones omit it.

## 4. Adding a new starting point *for Canvas*

Use the starting-points-tool (§5), Create New → Canvas (CanvasStartDir),
pick or type a category, fill in name + code, Save. That's it — no book
source to touch. Then use "Generate Embed HTML" (on that same entry, or
from the Canvas tab afterward) to get the `<iframe>`/`<a>` snippet to paste
into Canvas.

**You must redeploy before a newly-created or edited Canvas starting point
will actually load in Canvas** — see §6. The tool's generated embed HTML
always says this underneath the snippet, as a reminder.

## 5. Running the starting-points tool

```sh
node starting-points-tool/server.js
```

Then open **http://localhost:5050**. No `npm install` — it's plain Node
`http`/`fs`, zero dependencies. Binds to `127.0.0.1` only (reads/writes your
working tree directly; not meant to be reachable from anywhere else).

Three tabs:

- **Canvas** — browse `CanvasStartDir/`, grouped by category. Edit or
  generate embed HTML for anything listed.
- **Book** — browse `CMeCodeDir/`, grouped by whichever chapter's
  `source/**/*.ptx` actually references it (scanned fresh on every load, so
  it can't drift out of sync with the book itself). Anything with no
  `<cmecode startPoint="...">` pointing at it shows under "Unreferenced".
- **Create New** — make a new starting point in either location (§3/§4).

Editing: "Edit" loads the code into an editable box; "Save changes" writes
it back to disk; **"Close" discards without saving** — safe to open just to
look and back out.

The "Deployed site origin" field at the top (defaults to
`https://cprog-client-preview.pages.dev`) is what gets baked into generated
embed URLs — update it here (not in code) if the deploy target ever changes
(see the redirect/custom-domain discussion in the conversation this file
was written from).

This tool never touches git (no add/commit/push) and never touches
`source/**/*.ptx`.

## 6. Deploying

```sh
./deploy-client-preview.sh
```

What it does: builds `web-client`, stages it together with `coding-window/`,
`CMeCodeDir/`, and `CanvasStartDir/` as siblings (matching the relative URLs
the tool generates), regenerates the Cloudflare Pages Function that applies
COOP/COEP headers only to pages that actually embed the coding window (see
the script's own comments for why that allow-list approach specifically),
and runs `wrangler pages deploy`.

**Important: this reads straight from your working tree, not from git.**
Uncommitted changes deploy fine (you'll get a wrangler warning about
"uncommitted changes" — that's just a warning, not a blocker). Committing
and pushing is still worth doing for history/backup, but it's not what
makes a change go live — running this script is.

**When you need to redeploy:**

- Any new or edited file under `CMeCodeDir/` or `CanvasStartDir/` — until
  you do, Canvas (or the book) will fetch that URL and get Cloudflare's
  fallback page instead of the real file, which the coding-window tool
  reports as `Could not load the starting code ... server returned an HTML
  page instead`. This is the single most common "why isn't this working"
  cause — if you see that error, you probably just forgot to redeploy.
- Any book content change you want visible in `web-client`.
- Any change to the `coding-window/` tool itself (after rebuilding it — see
  §7).

**After deploying, give it a few seconds before testing** — Cloudflare's
edge cache can briefly serve a stale response (wrong `Content-Type`, or the
old fallback page) for the first request or two right after a deploy. If a
freshly-deployed file looks broken, wait ~5–10 seconds and retry before
assuming something's actually wrong.

You don't need to redeploy just for changes to the starting-points-tool
itself (`starting-points-tool/`) — that only runs locally.

## 7. Changing the coding-window tool itself

The tool's real source lives in a **separate repo**: `C-InBroserEnvironment`
(a Vite + TypeScript project). `coding-window/` here in the book repo is a
built, committed *copy* of that repo's `dist/` output — `pretext build`
doesn't know how to build it, and neither does anything else in this repo.

To ship a change to the tool itself:

```sh
cd ~/repos/C-InBroserEnvironment
# make your change in src/, index.html, linux.html, public/, etc.
npm run build
```

Then sync the fresh build into this repo:

```sh
cd ~/repos/C-Programming
rm -rf coding-window/assets
cp -R ~/repos/C-InBroserEnvironment/dist/. coding-window/
```

(Leave `coding-window/starters/` alone if `cp -R` brings it in — it's
Linux-shell-tool test fixtures, not used by the book or Canvas, and
deliberately left untracked here.)

Then rebuild the book (`pretext build web-client`) if the change affects
book pages, and redeploy (§6).

## 8. In-class "follow me" sessions

Every `web-client` page carries `assets/classroom.js` (wired via the
`html.js.extra` stringparam), inert unless a tab joins a session:

- **Lead a session**: open any book page with `?classroom=start`. A bottom
  banner shows a 4-character code and the join link (read it to the class /
  put it on a slide). Every page you navigate to — and every in-page anchor
  jump — is mirrored to everyone following, live. The banner shows how many
  are connected.
- **Join**: open the join link (any book page with `?classroom=<CODE>`).
  The tab follows the lead until Leave is clicked or the tab closes.
  Sessions are per-tab, so students' popped-out coding windows stay put.
- Followers can only ever be sent to same-origin book pages (enforced on
  both server and client), and there are no accounts — joining is anonymous.

Moving parts: `assets/classroom.js` (client) → `functions/session/[code].js`
(same-origin WebSocket endpoint, a Pages Function) → `ClassSession` Durable
Object hosted by the `classroom-worker/` Worker (deployed separately:
`cd classroom-worker && npx wrangler deploy`).

**One-time activation** (not yet done as of this writing):

1. Open the Cloudflare dashboard → Workers & Pages. Visiting the Workers
   area the first time registers the account's `workers.dev` subdomain —
   required before ANY Worker can be uploaded (API error 10063), and only
   doable from the dashboard.
2. `cd classroom-worker && npx wrangler deploy`
3. `mv wrangler.toml.pending wrangler.toml` (repo root — it holds the
   Durable Object binding for the Pages Functions; it's parked as
   `.pending` because a Pages deploy FAILS if the binding names a Worker
   that doesn't exist yet, which would break all normal deploys)
4. `./deploy-client-preview.sh`

Until then everything degrades gracefully: `/session/<CODE>` answers 503,
and a session banner just shows an amber "connecting" dot.

## 9. Known gotchas

- **Canvas can't be made interactive via iframe, ever** — Canvas doesn't
  send the COOP/COEP headers required for the browser's interactive-stdin
  feature (`SharedArrayBuffer`), and a nested iframe can't become isolated
  unless *every* ancestor frame is too. This isn't fixable from this tool's
  side. The workaround is Option B in the generated embed HTML: a plain
  link that opens the exercise in its **own new tab** instead of an iframe
  — a new tab has no parent frame, so it only needs its own (already
  correct) headers to be interactive.
- **Category/topic names with spaces are fine** — `CanvasStartDir/Short
  Assignment/` is a real, correct path. Generated embed URLs percent-encode
  each path segment separately, so this doesn't produce a broken URL.
- **`popen()` only works for gnuplot, and only fake-ly** — the client-side
  compiler's libc has no real subprocess support; its `popen()` recognizes
  exactly a write-mode `"gnuplot"` command and backs it with a virtual file
  the tool then parses and renders as an SVG chart (`src/gnuplot.ts` in the
  tool repo — only the narrow script subset the book's plotting exercises
  use: `set title/xlabel/ylabel/grid/output`, `plot '-' [with lines]
  [title ...]` with inline data). Any other `popen()` returns NULL. A new
  plotting exercise using fancier gnuplot features will need that parser
  extended.
- **The old Django/SQLite tool** (`~/Documents/CMeCode`) is retired but
  still holds historical Canvas-tagged content if more of it needs pulling
  into `CanvasStartDir/` later. Its `canvas` column (free text, no fixed
  vocabulary) was the tagging mechanism; `assignments/starting_points/`
  held the actual `.c` files.

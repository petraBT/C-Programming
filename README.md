# ENGS 20 C-Programming Book

Visit <https://engs20book.thayer.dartmouth.edu/C-Programming> to learn more.

## Building and deploying

There are two build targets, both defined in `project.ptx`:

- **`web`** — the live version. Every `cmecode` window is an interactive, editable
  code box that actually compiles/runs on the Thayer network (`code.thayer.dartmouth.edu`).
  This is what's normally linked to and lives at the site root.
- **`web-static`** — the same content, but every `cmecode` window is rendered as a
  plain, read-only, copy-pasteable code block instead of a live Thayer iframe. This
  exists for two reasons: (1) to preview/proofread new content before its starting
  points are registered on the Thayer server, and (2) to give readers without Thayer
  network access (e.g. off-campus, or after the course ends) a way to still read the
  book and copy-paste the code themselves. It's published alongside `web` at `/static/`.

Neither build automatically gets its sorting-algorithm animations (bubble/selection/
insertion/quicksort) — those are injected as a separate post-processing pass
(`scripts/add-applets.sh`) that rewrites `ADAMSAPPLET...ENDADAMSAPPLET` placeholder
text in the built HTML into the actual interactive divs + `sorters.js` include. This
has to run on *each* build's output separately.

**To deploy both:** just run

```
./deploy.sh
```

This builds `web` and `web-static`, runs `add-applets.sh` on both, then pushes the
result straight to `gh-pages` itself (via a local git worktree at
`.gh-pages-worktree`) — `web`'s output lands at the site root exactly as before
(existing bookmarks keep working), `web-static`'s lands under `/static/`. No GitHub
Actions involved; it's all done locally with your own git credentials, same as
before there were two targets.

(The `.github/workflows/*.yml` files in this repo are unused leftover boilerplate —
ignore them.)
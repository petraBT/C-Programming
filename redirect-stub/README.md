# The `cprog-client-preview` redirect stub

This directory is the entire content of the old `cprog-client-preview` Pages
project, as of step 23 of the hosting migration. That project used to serve the
interactive book, the coding window, `CMeCodeDir/` and `CanvasStartDir/`; all of
that now lives at `engs20book.thayer.dartmouth.edu`, published by
`deploy-client-preview.sh`.

The project is kept alive, serving nothing but redirects, because coding windows
embedded in Canvas before the move name the old origin twice: once for the
window itself, and again in the `?src=` starter-file URL the window fetches.
Both have to keep resolving until those pages are regenerated with the new
origin (the "Deployed site origin" field in `starting-points-tool/`).

The `?src=` fetch crosses origins after the redirect, so it only works because
Cloudflare Pages puts `access-control-allow-origin: *` on both the 301 and the
file at the far end. Checked at the time; worth rechecking if a window ever
comes up empty.

To republish it:

    npx wrangler pages deploy redirect-stub --project-name cprog-client-preview --branch main

Run that from a directory with no `functions/` in it, or wrangler bundles this
repo's Pages Functions into the stub.

Phase 5 of the migration deletes the project outright, once no Canvas page
embeds it.

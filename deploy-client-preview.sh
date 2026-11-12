#!/bin/bash
set -e

# Deploys ONLY the "web-client" target (the new client-side coding-window tool,
# evaluation stage) to Cloudflare Pages. Completely separate from deploy.sh and
# GitHub Pages: doesn't touch the gh-pages branch, doesn't touch git at all
# beyond reading the working tree. Cannot affect the live "web"/"web-static"
# site no matter what.
#
# Why a separate host at all: interactive stdin in the coding-window tool needs
# the page to be cross-origin isolated (COOP/COEP headers), and GitHub Pages
# cannot send custom headers, full stop - see DEPLOYMENT.md and the
# coding-window tool's own README.md for the details. This script publishes to
# a host that can, so this preview gets the real interactive experience
# instead of the non-interactive fallback.
#
# functions/_middleware.js is generated fresh below (at the repo root, NOT
# inside STAGE_DIR - Cloudflare Pages Functions are discovered relative to
# where `wrangler pages deploy` is invoked, not the deployed directory
# argument), not committed as a static file: COOP/COEP can only be applied to
# pages that actually embed the coding-window tool, not blanket-wide ("/*").
# Cross-origin isolation blocks ANY cross-origin subresource that doesn't
# send a matching Cross-Origin-Resource-Policy header - confirmed live, this
# is exactly what made YouTube video embeds "refuse to connect" the first
# time this was tried blanket-wide. Google Docs embeds have the same
# vulnerability (confirmed: no CORP header either), and there may be others
# not yet audited - allow-listing only the pages that need isolation, rather
# than blanket-applying it and hand-maintaining a deny-list of every
# cross-origin embed type in the book, means nothing else is ever at risk,
# including embed types nobody's found yet. The list is derived from the
# actual build output every time (grep for coding-window/index.html), so it
# can never drift out of sync with the book's real content.
#
# A Pages Function (real per-request code), not a static _headers file: the
# latter hit Cloudflare's hard 100-header-rule cap once the book grew past
# 100 pages needing isolation - confirmed live, pages sorted past the cutoff
# (e.g. the Strings chapter) silently lost interactive stdin with no error
# anywhere. Also confirmed live that COEP: credentialless does NOT fix this
# the way it might seem to (a common fix for "isolation breaks third-party
# embeds"): isolating a page with a YouTube embed still breaks it under
# EITHER require-corp or credentialless, because Cross-Origin-Opener-Policy
# itself disrupts the embed's window/postMessage relationship with its
# parent, independent of COEP's resource-loading policy. So the allow-list
# stays required regardless - see generate-middleware.py's docstring for
# the full history.
#
# One-time setup before this works (see chat for the full walkthrough):
#   1. Sign up for a free Cloudflare account: https://dash.cloudflare.com/sign-up
#   2. Authenticate Wrangler (Cloudflare's CLI) once on this machine:
#        npx wrangler login
#      (opens a browser to approve access - only needs doing once)
#
# Usage: ./deploy-client-preview.sh [--staging]
#
#   --staging   publish to staging.engs20-book.pages.dev instead of the live
#               site, for trying a change nobody should see yet.

PROJECT_NAME="engs20-book"
STAGE_DIR="output/cloudflare-client-preview"
SITE="https://engs20book.thayer.dartmouth.edu"

BRANCH=main
TARGET_SITE="$SITE"
for a in "$@"; do
  case "$a" in
    --staging) BRANCH=staging; TARGET_SITE="https://staging.$PROJECT_NAME.pages.dev" ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

pretext build web-client
./scripts/add-applets.sh output/web-client

# The static version (every coding window rendered as a plain, copy-pasteable
# code block) travels with the book now, under /static/, instead of living at
# the old /C-Programming/static/ address on GitHub Pages. The middleware
# redirects the old address here.
pretext build web-static

# coding-window/ and CMeCodeDir/ need to be siblings of the built pages, not
# nested inside each other - matches the relative paths the XSL generates
# (coding-window/index.html?src=../CMeCodeDir/<name>.c). See the cmecode.client.*
# param comments in xsl/c-programming-html.xsl.
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp -R output/web-client/. "$STAGE_DIR/"
# ENGS 20 has no instructor-only slides, so the published decks ARE the student decks. This
# stamps studentBuild on them (in the staged copy only, not in assets/ or output/web-client);
# the player offers its PDF download only for a student build.
python3 scripts/filter_student_decks.py "$STAGE_DIR"
cp -R coding-window "$STAGE_DIR/"
mkdir -p "$STAGE_DIR/CMeCodeDir"
find CMeCodeDir -maxdepth 1 -name '*.c' -exec cp {} "$STAGE_DIR/CMeCodeDir/" \;
find CMeCodeDir -maxdepth 1 -name '*.datafile.json' -exec cp {} "$STAGE_DIR/CMeCodeDir/" \;

# CanvasStartDir/ (Canvas-only starting points, see starting-points-tool/)
# isn't referenced by any XSL param - it just needs to be reachable at a
# stable, predictable URL for the embed HTML that tool generates
# (?src=<origin>/CanvasStartDir/<category>/<name>.c) to actually resolve.
if [ -d CanvasStartDir ]; then
  cp -R CanvasStartDir "$STAGE_DIR/"
fi

# Note-taking PDFs of the decks, if ./make-slide-pdfs.sh has been run: the deck player looks
# for them at slides/pdf/ (beside external/) and shows its PDF button only when it finds
# manifest.json there. Not built here - they take a minute per deck and are rarely stale.
if [ -f output/slide-pdfs/manifest.json ]; then
  mkdir -p "$STAGE_DIR/slides/pdf"
  cp output/slide-pdfs/*.pdf output/slide-pdfs/manifest.json "$STAGE_DIR/slides/pdf/"
fi

# The static version, under /static/.
mkdir -p "$STAGE_DIR/static"
cp -R output/web-static/. "$STAGE_DIR/static/"

# Which addresses run a Pages Function. WITHOUT this file Cloudflare runs one on
# EVERY request -- measured at 74 for a single cold page view of this book -- and
# every one counts against the account's daily limit, which ENGS 28 shares. Yet
# the middleware only sets headers for the allow-listed pages and coding-window/;
# for everything else it hands the response straight back. So roughly 56 of those
# 74 were invoking a Function purely to do nothing.
#
# Excluded below: bundles, images, starter sources and the coding-window payload,
# none of which is ever a page needing isolation headers or an old address needing
# a redirect. coding-window/index.html, linux.html and embed-generator.html stay
# INCLUDED, so nothing loses its isolation. Static assets are free and unlimited
# either way; only Function invocations count.
cat > "$STAGE_DIR/_routes.json" <<'ROUTES'
{
  "version": 1,
  "include": ["/*"],
  "exclude": [
    "/_static/*",
    "/external/*",
    "/CMeCodeDir/*",
    "/CanvasStartDir/*",
    "/static/_static/*",
    "/static/external/*",
    "/coding-window/assets/*",
    "/coding-window/starters/*",
    "/coding-window/wccfiles.zip"
  ]
}
ROUTES

# A real 404. Without one Cloudflare quietly serves the FRONT PAGE for every
# wrong address, so a mistyped link looks like it worked and a dead link in
# Canvas is invisible until a student says so.
cat > "$STAGE_DIR/404.html" <<'NOTFOUND'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found — ENGS 20</title>
</head>
<body style="font-family: system-ui, sans-serif; margin: 4em auto; max-width: 34em; line-height: 1.5; padding: 0 1em">
<h1 style="font-size: 1.4em">That page is not here</h1>
<p>The address may be mistyped, or it may be a link to an older version of this
book, where the page had a different name.</p>
<ul>
<li><a href="/">The book</a> — start here and use the search box</li>
<li><a href="/static/">The static version</a>, without the live coding windows</li>
</ul>
</body>
</html>
NOTFOUND

python3 generate-middleware.py output/web-client functions/_middleware.js

npx wrangler pages deploy "$STAGE_DIR" --project-name="$PROJECT_NAME" --branch="$BRANCH"

echo ""
echo "Deployed. $TARGET_SITE/"

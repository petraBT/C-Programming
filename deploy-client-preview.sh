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
# Usage: ./deploy-client-preview.sh

PROJECT_NAME="cprog-client-preview"
STAGE_DIR="output/cloudflare-client-preview"

pretext build web-client
./scripts/add-applets.sh output/web-client

# coding-window/ and CMeCodeDir/ need to be siblings of the built pages, not
# nested inside each other - matches the relative paths the XSL generates
# (coding-window/index.html?src=../CMeCodeDir/<name>.c). See the cmecode.client.*
# param comments in xsl/c-programming-html.xsl.
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
cp -R output/web-client/. "$STAGE_DIR/"
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

python3 generate-middleware.py output/web-client functions/_middleware.js

npx wrangler pages deploy "$STAGE_DIR" --project-name="$PROJECT_NAME"

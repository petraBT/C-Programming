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
cp _headers "$STAGE_DIR/_headers"

npx wrangler pages deploy "$STAGE_DIR" --project-name="$PROJECT_NAME"

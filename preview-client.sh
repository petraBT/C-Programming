#!/bin/bash
set -e

# Builds "web-client" and serves it locally so you can look at it in a browser.
# Completely separate from deploy.sh / GitHub Pages / deploy-client-preview.sh
# (Cloudflare) - this doesn't publish anywhere, just runs a throwaway local
# server. Safe to run any time; doesn't touch git or any live site.
#
# Serves with the COOP/COEP headers interactive stdin needs (see
# serve-with-headers.py), so this shows the real interactive terminal, not
# the "Input" pre-fill fallback you'd see behind a plain file server (or on
# GitHub Pages, which can't send these headers at all - see DEPLOYMENT.md /
# coding-window/README.md).
#
# Usage: ./preview-client.sh [port]   (defaults to 8299)

PORT="${1:-8299}"

pretext build web-client

# coding-window/ and CMeCodeDir/ need to be siblings of the built pages - see
# the cmecode.client.* param comments in xsl/c-programming-html.xsl for why.
cp -R coding-window output/web-client/
mkdir -p output/web-client/CMeCodeDir
find CMeCodeDir -maxdepth 1 -name '*.c' -exec cp {} output/web-client/CMeCodeDir/ \;
find CMeCodeDir -maxdepth 1 -name '*.datafile.json' -exec cp {} output/web-client/CMeCodeDir/ \;

echo ""
echo "Serving at http://localhost:$PORT/ (Ctrl-C to stop)"
python3 serve-with-headers.py "$PORT" output/web-client

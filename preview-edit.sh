#!/bin/bash
set -e

# Builds "web-edit" and serves it locally for authoring: the in-browser coding
# environment (same as preview-client.sh) plus the click-to-source helper.
#
#   alt-click       a paragraph -> opens it in your text editor
#   alt-shift-click a paragraph -> edit the text in place, cmd-enter to save
#
# See scripts/README-editing.md. Also starts scripts/edit-server.py, which is
# what actually finds and rewrites the source - without it the clicks just
# report that it isn't running.
#
# Local only: doesn't publish anywhere, doesn't touch git or any live site.
# web-edit is deliberately absent from build.sh and deploy.sh, because it is the
# one target carrying a script that talks to a server able to rewrite source.
#
# Usage: ./preview-edit.sh [port]   (defaults to 8931)

PORT="${1:-8931}"

pretext build web-edit
./scripts/add-applets.sh output/web-edit

# coding-window/ and CMeCodeDir/ need to be siblings of the built pages - see
# the cmecode.client.* param comments in xsl/c-programming-html.xsl for why.
# Same steps as preview-client.sh; keep the two in step.
cp -R coding-window output/web-edit/
mkdir -p output/web-edit/CMeCodeDir
find CMeCodeDir -maxdepth 1 -name '*.c' -exec cp {} output/web-edit/CMeCodeDir/ \;
find CMeCodeDir -maxdepth 1 -name '*.datafile.json' -exec cp {} output/web-edit/CMeCodeDir/ \;

python3 scripts/edit-server.py &
EDIT_SERVER=$!
# Ctrl-C stops the page server; make sure it takes the edit server with it
# rather than leaving a stray process holding port 8927.
trap 'kill $EDIT_SERVER 2>/dev/null' EXIT

echo ""
echo "Serving at http://localhost:$PORT/ (Ctrl-C to stop)"
# COOP/COEP headers, as preview-client.sh explains - without them the coding
# windows fall back to the non-interactive "Input" pre-fill.
python3 serve-with-headers.py "$PORT" output/web-edit

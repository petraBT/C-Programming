#!/bin/bash
set -e

# Full rebuild of the "web-edit" authoring target, post-build steps included.
#
# Split out of preview-edit.sh so that the initial build and the rebuild the
# file watcher runs on every save are the same code. `pretext build web-edit`
# on its own is NOT enough - the coding windows need the applet pass and the
# sibling directories below, and a preview missing those looks broken in ways
# that have nothing to do with what you just edited.
#
# Not part of build.sh or deploy.sh: web-edit is local-only. See
# scripts/README-editing.md.

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

pretext build web-edit
./scripts/add-applets.sh output/web-edit

# coding-window/ and CMeCodeDir/ need to be siblings of the built pages - see
# the cmecode.client.* param comments in xsl/c-programming-html.xsl for why.
# Same steps as preview-client.sh; keep the two in step.
cp -R coding-window output/web-edit/
mkdir -p output/web-edit/CMeCodeDir
find CMeCodeDir -maxdepth 1 -name '*.c' -exec cp {} output/web-edit/CMeCodeDir/ \;
find CMeCodeDir -maxdepth 1 -name '*.datafile.json' -exec cp {} output/web-edit/CMeCodeDir/ \;

#!/bin/bash
set -e

# Builds "web-edit" and serves it locally for authoring: the in-browser coding
# environment (same as preview-client.sh) plus the click-to-source helper.
#
#   alt-click       a paragraph -> opens it in your text editor
#   alt-shift-click a paragraph -> edit the text in place, cmd-enter to save
#
# One command for the whole authoring setup: it starts the two helper processes
# as well as the page server, so there's nothing else to remember. Those are
# scripts/edit-server.py, which finds and rewrites the source behind the
# paragraph clicks, and starting-points-tool/server.js, which the coding-window
# clicks open into. Ctrl-C stops all three. See scripts/README-editing.md.
#
# Local only: doesn't publish anywhere, doesn't touch git or any live site.
# web-edit is deliberately absent from build.sh and deploy.sh, because it is the
# one target carrying a script that talks to a server able to rewrite source.
#
# Usage: ./preview-edit.sh [port] [--no-watch]   (port defaults to 8931)
#
# --no-watch skips the rebuild-on-save watcher, for when you want the preview
# held still at a known build. A warm rebuild is a few seconds; the first one
# after a PreTeXt upgrade is much slower, since it re-fetches Runestone.

PORT=8931
WATCH=yes
for arg in "$@"; do
  case "$arg" in
    --no-watch) WATCH=no ;;
    *) PORT="$arg" ;;
  esac
done

# The build and its post-build steps live in scripts/build-edit.sh, so that the
# watcher below re-runs exactly what happens here rather than a partial copy.
./scripts/build-edit.sh

# Everything this script starts goes in here and is torn down together, so that
# authoring is one command rather than three terminals. Collecting PIDs as they
# start means the trap is correct even if a later one never starts.
STARTED=()
cleanup() {
  [ ${#STARTED[@]} -gt 0 ] && kill "${STARTED[@]}" 2>/dev/null
  return 0
}
# INT and TERM as well as EXIT, not just EXIT: bash defers a trap while it waits
# on a *foreground* child, so if only this shell gets the signal (rather than
# the whole process group, as a terminal Ctrl-C sends) the cleanup would never
# run and the helpers would be orphaned on their ports. Hence also running the
# page server in the background and waiting on it, below - "wait" is
# interruptible, a foreground child is not.
trap 'cleanup; exit 130' INT TERM
trap cleanup EXIT

# Refuses to start a helper whose port is already taken: the process would die
# immediately and the failure would only show up later as clicks in the book
# quietly not working. Better to say so now, and keep serving the book either
# way - the preview is still useful without the helpers.
start_helper() {
  local label="$1" port="$2"
  shift 2
  # -sTCP:LISTEN matters: without it this also matches a browser tab's open
  # client connection to the port, so a stale tab would block a server that
  # isn't actually running any more.
  if lsof -ti "tcp:$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ! $label: port $port is already in use - not starting another."
    echo "    (If an earlier ./preview-edit.sh is still running, use that one.)"
    return
  fi
  "$@" &
  STARTED+=($!)
  echo "  - $label on port $port"
}

echo ""
echo "Helpers:"
# Finds and rewrites .ptx source in response to alt-clicks. See
# scripts/README-editing.md.
start_helper "edit server" 8927 python3 scripts/edit-server.py
# What alt-clicking a coding window opens into. Optional: everything else works
# without it, so a missing node shouldn't stop the preview.
if command -v node >/dev/null 2>&1; then
  start_helper "starting points tool" 5050 node starting-points-tool/server.js
else
  echo "  ! starting points tool: node not found - coding-window clicks won't land."
fi

# Rebuilds on every .ptx save, so an edit made in your editor - or in place in
# the preview - shows up after a refresh instead of needing a manual build. It
# runs scripts/build-edit.sh rather than "pretext build", because the post-build
# steps matter as much as the build here.
if [ "$WATCH" = "yes" ]; then
  python3 watch.py --command ./scripts/build-edit.sh &
  STARTED+=($!)
  echo "  - file watcher (rebuilds on save; --no-watch to skip)"
else
  echo "  - file watcher off (--no-watch)"
fi

echo ""
echo "Book:  http://localhost:$PORT/   <- open this one"
echo "  alt-click a paragraph      -> opens it in your editor"
echo "  alt-shift-click a paragraph -> edit in place, cmd-enter to save"
echo "  alt-click a coding window  -> opens it in the starting points tool"
echo ""
echo "Ctrl-C stops everything."
# COOP/COEP headers, as preview-client.sh explains - without them the coding
# windows fall back to the non-interactive "Input" pre-fill.
#
# Backgrounded and waited on rather than run in the foreground, so that a
# Ctrl-C is handled promptly by the traps above however the signal arrives.
python3 serve-with-headers.py "$PORT" output/web-edit &
STARTED+=($!)
wait

#!/bin/bash
# Build the deck you TEACH from: web-deck-instructor, plus the board
# simulator's instructor examples.
#
# This exists for the same reason scripts/build-edit.sh does: the target is not
# the whole build. `pretext build web-deck-instructor` leaves out the simulator
# side-car, which is installed after the fact because it must not live under
# assets/ (see instructor-only/README.md). Having it in one script means the
# file watcher can run it too - watch.py --command ./scripts/build-deck-instructor.sh -
# instead of rebuilding half of it on every save.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# Same macOS permission workaround as build.sh: shutil.copy2 preserves source
# permissions, which can leave the copies read-only and break the next build.
rm -rf output/web-deck-instructor/external/
pretext build web-deck-instructor
./scripts/install-instructor-sim.sh web-deck-instructor

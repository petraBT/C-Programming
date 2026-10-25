#!/bin/bash
# Build the STUDENT deck — "web-deck" — and filter its deck list to match.
#
# Always use this rather than a bare `pretext build web-deck`. The build strips
# instructor-only slides from the HTML, but PreTeXt copies assets/decks/
# verbatim into external/, so the deck list beside the stripped pages still
# names every one of them: the player then fails the deck ~29 times, and the
# entry titles ("Solution - blink, dim, write") are readable in the JSON.
#
# This was not hypothetical. A `watch.py web-deck` left running from an older
# preview-slides.sh rebuilt the target on every save and put the unfiltered list
# straight back, silently undoing the filter. Wrapping the two steps in one
# command is the only way "the student deck is built" can mean one thing.
#
# You are usually NOT building this. The deck you teach and author from is
# web-deck-instructor (./preview-slides.sh) — it has every slide. This one is
# the publishable copy.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# The contents page reads this; regenerate before the build so a deck added
# since last time shows up. (Same reason preview-slides.sh does it.)
python3 scripts/make_deck_index.py

# See build.sh: stale external/ copies can be read-only and break the copy.
rm -rf output/web-deck/external/
pretext build web-deck "$@"
python3 scripts/filter_student_decks.py output/web-deck

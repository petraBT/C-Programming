#!/bin/bash
# Snapshot every deck in three views, into output/snapshots/<label>/<view>/<deck>/.
#   ./scripts/deck_snapshot_all.sh before     # label names the run
# Views: instructor (with notes), instructor-as-student, and the real student
# build. Build both decks first (build-deck-instructor.sh, build-deck.sh).
# INSTR_DIR / STUDENT_DIR point at other builds; VIEWS="instructor-plain" limits the views.
# DECKS="day8 day9" limits the run to those decks.
# Compare two labels with scripts/deck_compare.py. See deck_snapshot.mjs.
set -e
cd "$(dirname "$0")/.."
LABEL="${1:?usage: deck_snapshot_all.sh <label>}"
OUT="output/snapshots/$LABEL"
python3 scripts/serve-no-cache.py 8371 "${INSTR_DIR:-output/web-deck-instructor}" >/dev/null 2>&1 & S1=$!
python3 scripts/serve-no-cache.py 8372 "${STUDENT_DIR:-output/web-deck}" >/dev/null 2>&1 & S2=$!
trap 'kill $S1 $S2 2>/dev/null' EXIT
sleep 1
DECKS="${DECKS:-$(python3 -c "import json;print(' '.join(x['id'] for x in json.load(open('output/web-deck-instructor/external/decks/index.json'))['decks']))")}"
run() { # view port flags
  for d in $DECKS; do
    while [ "$(jobs -rp | grep -vxE "$S1|$S2" | wc -l)" -ge 4 ]; do sleep 0.3; done
    node scripts/deck_snapshot.mjs "$d" "$2" --out="$OUT/$1" $3 2>/dev/null &
  done
  wait $(jobs -rp | grep -vxE "$S1|$S2")
}
V=" ${VIEWS:-instructor instructor-plain instructor-as-student student} "
case "$V" in *" instructor "*) run instructor 8371 --notes;; esac
case "$V" in *" instructor-plain "*) run instructor-plain 8371 "";; esac
case "$V" in *" instructor-as-student "*) run instructor-as-student 8371 --student;; esac
case "$V" in *" student "*) run student 8372 --student;; esac
echo "snapshots in $OUT"

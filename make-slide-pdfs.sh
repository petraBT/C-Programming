#!/bin/bash
# Build note-taking PDFs of the class slides — one landscape 16:9 page per
# slide, one PDF per deck, STUDENT VIEW ONLY.
#
#   ./make-slide-pdfs.sh                 # every deck
#   ./make-slide-pdfs.sh day1 day3 day6  # just these
#   ./make-slide-pdfs.sh --no-build      # reuse the last web-client build (faster)
#   ./make-slide-pdfs.sh -j4             # four decks at a time
#
# Output: output/slide-pdfs/<deck>.pdf, plus manifest.json naming them, which
# the deck player reads to decide whether to offer its PDF button. The player looks for
# them at slides/pdf/ beside external/, so deploy-client-preview.sh copies this folder
# there when it exists. A <cmecode> demo slide prints as its title and lead-in only: a
# live coding window cannot be paper.
#
# --site=DIR prints an already-built tree instead of rebuilding.

# Run it whenever. It rebuilds web-client from source first, so a slide
# edited a minute ago is in the PDF; there is no staleness to remember. That
# is also the whole point of it being one command — the decks change up to the
# last minute, and a handout built from yesterday's source is worse than no
# handout.
#
# It uses its own port (9362) and its own build directory, so it does NOT
# disturb ./preview-edit.sh, the review server on 9028, or anything else you
# have open. Safe to run mid-review.
#
# ENGS 20 has no instructor-only slides, so every slide is printed (always with &student).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT=9362
OUTDIR="output/slide-pdfs"
BUILD=yes
SITE=output/web-client
JOBS=1
# Links in a printed slide are relative, so they were printed as links to the
# throwaway server this script runs. They are rewritten to the published book.
BASE_URL="https://cprog-client-preview.pages.dev"

DECKS=()
for a in "$@"; do
    case "$a" in
        --no-build) BUILD=no ;;
        --site=*)   SITE="${a#--site=}"; BUILD=no ;;
        --out=*)    OUTDIR="${a#--out=}" ;;
        --port=*)   PORT="${a#--port=}" ;;
        --base-url=*) BASE_URL="${a#--base-url=}" ;;
        -j*)        JOBS="${a#-j}" ;;
        -h|--help)  sed -n '2,36p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*)         echo "unknown option: $a" >&2; exit 2 ;;
        *)          DECKS+=("$a") ;;
    esac
done

command -v node >/dev/null || { echo "error: node is not on PATH" >&2; exit 1; }
python3 -c "import fitz" 2>/dev/null || {
    echo "error: python package 'pymupdf' is missing (scripts/pdf_concat.py needs it)" >&2
    echo "       pip install pymupdf" >&2; exit 1; }
[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] || {
    echo "error: Google Chrome not found — deck_pdf.mjs drives it headless" >&2; exit 1; }

if [ "$BUILD" = yes ]; then
    echo "─── building web-client ──────────────────────────────────"
    # ENGS 20 has no instructor-only slides, so the one deck build is the student deck.
    python3 scripts/make_deck_index.py
    rm -rf output/web-client/external/
    pretext build web-client
else
    [ -f "$SITE/external/class.html" ] || {
        echo "error: --no-build, but $SITE has no build to reuse" >&2; exit 1; }
    echo "printing from the existing build in $SITE"
fi
case "$JOBS" in ''|*[!0-9]*|0) echo "error: -j needs a number, e.g. -j4" >&2; exit 2 ;; esac

# Which decks? Default to every one in the index, in teaching order.
if [ ${#DECKS[@]} -eq 0 ]; then
    while IFS= read -r d; do DECKS+=("$d"); done < <(
        python3 -c "
import json
for x in json.load(open('$SITE/external/decks/index.json'))['decks']:
    print(x['id'])"
    )
fi

# Serve the student build on our own port. Killed on any exit, including Ctrl-C,
# so a failed run does not leave a server holding the port.
python3 scripts/serve-no-cache.py "$PORT" "$SITE" > /dev/null 2>&1 &
SERVER_PID=$!
cleanup() { kill "$SERVER_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

for _ in $(seq 1 40); do
    curl -sf -o /dev/null "http://127.0.0.1:$PORT/external/class.html" && break
    sleep 0.25
done
curl -sf -o /dev/null "http://127.0.0.1:$PORT/external/class.html" || {
    echo "error: the deck player never came up on port $PORT" >&2; exit 1; }

mkdir -p "$OUTDIR"
echo ""
echo "─── printing ${#DECKS[@]} deck(s) to $OUTDIR ──────────────────"

# Each deck is its own headless Chrome, so -j runs several side by side. A
# failed deck leaves a marker in $FAILDIR rather than a shell variable, which a
# background job could not set.
FAILDIR=$(mktemp -d)
trap 'cleanup; rm -rf "$FAILDIR"' EXIT INT TERM
printers() { jobs -rp | grep -vx "$SERVER_PID" | wc -l; }   # the server is a job too
for d in "${DECKS[@]}"; do
    while [ "$(printers)" -ge "$JOBS" ]; do sleep 0.2; done
    ( node scripts/deck_pdf.mjs "$d" "$PORT" --out="$OUTDIR" || touch "$FAILDIR/$d" ) &
done
# Wait for the printers only: `wait` with no arguments would also wait for the
# server, which never exits.
for pid in $(jobs -rp); do [ "$pid" = "$SERVER_PID" ] || wait "$pid" 2>/dev/null || true; done

# The PDFs were printed from a server on 127.0.0.1:$PORT, so every link in them
# points there and is dead for a student. Point them at the published book, and
# refuse to ship a PDF that still links to this machine.
python3 - "$OUTDIR" "$PORT" "$BASE_URL" <<'PY'
import glob, os, re, sys
import fitz
out, port, base = sys.argv[1], sys.argv[2], sys.argv[3].rstrip("/")
local = re.compile(r"^https?://(127\.0\.0\.1|localhost)(:%s)?(/|$)" % re.escape(port))
fixed = bad = 0
for f in sorted(glob.glob(os.path.join(out, "*.pdf"))):
    doc = fitz.open(f)
    changed = False
    for page in doc:
        for link in page.get_links():
            uri = link.get("uri")
            if uri and local.match(uri):
                link["uri"] = local.sub(base + "/", uri, count=1)
                page.update_link(link)
                fixed += 1
                changed = True
    if changed:
        tmp = f + ".tmp"
        doc.save(tmp, garbage=3, deflate=True)
        doc.close()
        os.replace(tmp, f)
    else:
        doc.close()
    with fitz.open(f) as doc:
        for page in doc:
            for link in page.get_links():
                if re.match(r"^https?://(127\.0\.0\.1|localhost)", link.get("uri") or ""):
                    bad += 1
                    print("  still local: %s p%d %s" % (os.path.basename(f), page.number + 1, link["uri"]))
print("pdf links: %d rewritten to %s" % (fixed, base))
if bad:
    sys.exit("error: %d link(s) still point at this machine" % bad)
PY

# The manifest the deck player reads: one entry per deck whose PDF is here,
# with its page count and size for the button's tooltip.
python3 - "$OUTDIR" "$SITE/external/decks/index.json" <<'PY'
import datetime, json, os, subprocess, sys
import fitz
out, index = sys.argv[1], sys.argv[2]
decks = {}
for d in json.load(open(index))["decks"]:
    f = os.path.join(out, d["id"] + ".pdf")
    if os.path.exists(f):
        with fitz.open(f) as doc:
            decks[d["id"]] = {"file": d["id"] + ".pdf", "pages": doc.page_count,
                              "bytes": os.path.getsize(f)}
rev = subprocess.run(["git", "describe", "--always", "--dirty"],
                     capture_output=True, text=True).stdout.strip()
json.dump({"built": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
           "source": rev, "decks": decks},
          open(os.path.join(out, "manifest.json"), "w"), indent=2)
PY

echo ""
failed=$(ls "$FAILDIR")
if [ -n "$failed" ]; then
    echo "FAILED: $(echo $failed)" >&2
    exit 1
fi
echo "Done. ${#DECKS[@]} PDF(s) in $OUTDIR/"
ls -la "$OUTDIR"

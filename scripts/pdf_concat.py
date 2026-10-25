#!/usr/bin/env python3
"""Concatenate PDFs, then shrink the rasters — without rebuilding any font.

    python3 scripts/pdf_concat.py OUT.pdf PAGE1.pdf PAGE2.pdf ...
    python3 scripts/pdf_concat.py OUT.pdf --from-list FILE_OF_PATHS
    python3 scripts/pdf_concat.py OUT.pdf --from-list F --keep-images

Written for scripts/deck_pdf.mjs, which prints one PDF per slide and needs them
in one file per deck.

WHY NOT GHOSTSCRIPT, the obvious tool and already on the machine: `gs
-sDEVICE=pdfwrite` rebuilds every embedded font subset, and it gets that wrong
on the subsets Chrome embeds.  Concatenating day1 cost the `|` in the
bitwise-OR listing on slide 20 -- gs reported

    Missing glyph CID=95, glyph=005f in the font EAAAAA+Menlo-Regular

and drew a tofu box in a deck whose subject is that operator.  The glyph is
present and correct in Chrome's own output (confirmed by rendering it with
MuPDF) and the character was in the text layer throughout, so the loss was
purely in gs's re-embedding.  A handout that silently drops operators out of C
code is worse than no handout.  MuPDF copies page objects by reference instead,
so each font program arrives byte for byte as Chrome wrote it.

THE IMAGE PASS is why gs looked good on size: day1 concatenated raw is 13.6 MB,
and 11.4 MB of that is four screenshots Chrome embedded as full-resolution PNG
(~2400 px wide, ~3.5 MB each).  PNG is the wrong container for a photograph,
and no amount of object de-duplication helps, because each page's copy is
subsetted differently.  Re-encoding just those images to 150 dpi JPEG brings
day1 to 2.1 MB with the board photos still crisp at print size -- and, unlike
the gs route, touches nothing but the images.

150 dpi is chosen against the page, not by habit: the page is 13.333 in wide,
so a figure spanning half of it gets ~1000 px, which is more than a laser
printer resolves and more than a laptop screen shows.
"""

import os
import sys

import fitz  # PyMuPDF

# Above DPI_THRESHOLD an image is re-encoded down to DPI_TARGET.  MuPDF requires
# target < threshold, so the gap also keeps images that are already reasonable
# from being re-encoded for nothing.
DPI_THRESHOLD = 200
DPI_TARGET = 150
JPEG_QUALITY = 85


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}

    if len(args) < 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2

    out = args[0]
    if "--from-list" in flags:
        if len(args) != 2:
            print("--from-list takes exactly one file", file=sys.stderr)
            return 2
        with open(args[1], encoding="utf-8") as fh:
            pages = [ln.strip() for ln in fh if ln.strip()]
    else:
        pages = args[1:]

    if not pages:
        print("no input pages", file=sys.stderr)
        return 2

    doc = fitz.open()
    for path in pages:
        with fitz.open(path) as part:
            doc.insert_pdf(part)

    if "--keep-images" not in flags:
        doc.rewrite_images(
            dpi_threshold=DPI_THRESHOLD,
            dpi_target=DPI_TARGET,
            quality=JPEG_QUALITY,
        )

    # garbage=4 is the most aggressive object de-duplication; clean+deflate
    # rewrite the object streams.  None of these touch a font program.
    # no_new_id: no random trailer /ID, which was the ONLY difference between
    # two printings of an unchanged deck.  Without it every deploy commits a
    # new copy of every PDF to gh-pages (~60 MB of history each time); with it
    # an unchanged deck is byte-identical and git stores it once.
    doc.save(out, garbage=4, deflate=True, clean=True, no_new_id=True)
    doc.close()

    print(f"  {len(pages)} page(s) -> {out} ({round(os.path.getsize(out) / 1024)} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

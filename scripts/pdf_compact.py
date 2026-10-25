#!/usr/bin/env python3
"""Shrink the rasters in a PDF in place, touching nothing else.

    python3 scripts/pdf_compact.py output/print/main.pdf

The book PDF straight out of LaTeX is about 59 MB, nearly all of it
full-resolution PNG screenshots and photos. This is the image pass from
scripts/pdf_concat.py, with the same settings and for the same reasons (read
its docstring before changing either): images above 200 dpi at their printed
size are re-encoded to 150 dpi JPEG, and no font program is rebuilt, which is
why this is MuPDF and not ghostscript. The outline, links and the
/ENGS28Complete key survive the save; scripts/build-print.sh checks the book
before this runs, not after.
"""

import os
import sys

import fitz  # PyMuPDF

from pdf_concat import DPI_TARGET, DPI_THRESHOLD, JPEG_QUALITY


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    path = argv[1]
    before = os.path.getsize(path)
    doc = fitz.open(path)
    doc.rewrite_images(dpi_threshold=DPI_THRESHOLD, dpi_target=DPI_TARGET,
                       quality=JPEG_QUALITY)
    tmp = path + ".compact"
    doc.save(tmp, garbage=4, deflate=True, clean=True)
    doc.close()
    os.replace(tmp, path)
    print(f"pdf_compact: {path} {before / 1e6:.1f} MB -> "
          f"{os.path.getsize(path) / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

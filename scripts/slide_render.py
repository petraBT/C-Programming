#!/usr/bin/env python3
"""Whole-slide SVG compositor for slides pptx_annotate.py can't handle:
multiple sliced pictures with labels beside them, or pure-shape diagrams.

Adds over pptx_annotate: text wrapping to the shape box width, and
flipH/flipV handling on connectors.

    python3 scripts/slide_render.py <deck> --slide 11 -o out.svg --ymin 1.1

CAUTION: slide shape layers can contain opaque white rects that erase artwork
in the output -- grep the SVG for fill="#FFFFFF" rects and inspect a render.
"""
import argparse, base64, os, sys, zipfile

from pptx_annotate import (collect, paragraphs, shape_fill, shape_line,
                           line_ends, NS)
from xml.sax.saxutils import escape


def get_flips(sp):
    x = sp.find(".//a:xfrm", NS)
    if x is None:
        return False, False
    return x.get("flipH") == "1", x.get("flipV") == "1"


def wrap_text(text, max_chars):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    if cur:
        lines.append(cur)
    return lines


def render_shape(kind, box, sp, ox, oy, s, max_text, font_scale=1.0):
    out = []
    x, y = (box.x - ox) * s, (box.y - oy) * s
    w, h = box.w * s, box.h * s
    geom = sp.find(".//a:prstGeom", NS)
    prst = geom.get("prst") if geom is not None else "rect"
    fill, falpha = shape_fill(sp)
    stroke, salpha, sw = shape_line(sp)
    swpx = max(sw * s, 1.0) if stroke else 0

    xf = ""
    if abs(box.rot) > 0.01:
        xf = f' transform="rotate({box.rot:.2f} {x + w / 2:.1f} {y + h / 2:.1f})"'

    def paint():
        p = f'fill="{fill}"' if fill else 'fill="none"'
        if fill and falpha < 1:
            p += f' fill-opacity="{falpha:.2f}"'
        if stroke:
            p += f' stroke="{stroke}" stroke-width="{swpx:.1f}"'
            if salpha < 1:
                p += f' stroke-opacity="{salpha:.2f}"'
        return p

    if kind == "cxn" or prst in ("line", "straightConnector1", "bentConnector2",
                                 "bentConnector3", "curvedConnector3"):
        if stroke:
            fh, fv = get_flips(sp)
            x1, y1, x2, y2 = x, y, x + w, y + h
            if fh:
                x1, x2 = x2, x1
            if fv:
                y1, y2 = y2, y1
            head, tail = line_ends(sp)
            m = ""
            if tail:
                m += ' marker-end="url(#arrow)"'
            if head:
                m += ' marker-start="url(#arrow)"'
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                       f'stroke="{stroke}" stroke-width="{swpx:.1f}"{m}{xf}/>')
    elif prst in ("ellipse", "circle"):
        out.append(f'<ellipse cx="{x + w / 2:.1f}" cy="{y + h / 2:.1f}" '
                   f'rx="{w / 2:.1f}" ry="{h / 2:.1f}" {paint()}{xf}/>')
    elif prst == "roundRect":
        r = min(w, h) * 0.25
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                   f'rx="{r:.1f}" {paint()}{xf}/>')
    elif fill or stroke:
        out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                   f'{paint()}{xf}/>')

    paras = paragraphs(sp)
    total = sum(len(t) for t, *_ in paras)
    if paras and total <= max_text:
        # Wrap each paragraph to the box width, then lay out all lines.
        all_lines = []
        for text, size, colour, bold, align in paras:
            size = size * font_scale
            fs = size * s / 72.0
            max_chars = max(int((w * 0.96) / (fs * 0.52)), 8)
            for ln in wrap_text(text, max_chars):
                all_lines.append((ln, size, colour, bold, align))
        line_h = max((p[1] for p in all_lines), default=12) * s / 72.0 * 1.22
        start = y + h / 2 - (len(all_lines) - 1) * line_h / 2 + line_h * 0.32
        for i, (text, size, colour, bold, align) in enumerate(all_lines):
            anchor = {"l": "start", "r": "end", "ctr": "middle",
                      "just": "start"}.get(align, "middle")
            tx = {"start": x + w * 0.02, "end": x + w * 0.98,
                  "middle": x + w / 2}[anchor]
            fs = size * s / 72.0
            out.append(
                f'<text x="{tx:.1f}" y="{start + i * line_h:.1f}" font-size="{fs:.1f}" '
                f'fill="{colour}" text-anchor="{anchor}" '
                f'font-family="Helvetica, Arial, sans-serif"'
                f'{" font-weight=\"bold\"" if bold else ""}{xf}>{escape(text)}</text>')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--slide", type=int, required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--max-text", type=int, default=200)
    ap.add_argument("--ymin", type=float, default=0.9,
                    help="ignore shapes entirely above this y (title zone), inches")
    ap.add_argument("--ymax", type=float, default=99.0)
    ap.add_argument("--dpi", type=float, default=150.0)
    ap.add_argument("--font-scale", type=float, default=1.0)
    args = ap.parse_args()

    with zipfile.ZipFile(args.pptx) as z:
        pics, shapes = collect(z, args.slide)

        keep_shapes = []
        for kind, box, sp in shapes:
            if box.y + box.h <= args.ymin or box.y >= args.ymax:
                continue
            txt = "".join(p[0] for p in paragraphs(sp))
            if len(txt) > args.max_text:
                continue
            keep_shapes.append((kind, box, sp))

        pics = [p for p in pics if p[0].y + p[0].h > args.ymin and p[0].y < args.ymax]
        if not pics and not keep_shapes:
            sys.exit("nothing to render")

        xs0 = [b.x for b, *_ in pics] + [b.x for _, b, _ in keep_shapes]
        ys0 = [b.y for b, *_ in pics] + [b.y for _, b, _ in keep_shapes]
        xs1 = [b.x + b.w for b, *_ in pics] + [b.x + b.w for _, b, _ in keep_shapes]
        ys1 = [b.y + b.h for b, *_ in pics] + [b.y + b.h for _, b, _ in keep_shapes]
        pad = 0.08
        x0, y0, x1, y1 = min(xs0) - pad, min(ys0) - pad, max(xs1) + pad, max(ys1) + pad

        scale = args.dpi
        W, H = (x1 - x0) * scale, (y1 - y0) * scale

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}">',
            '<defs>',
            '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            'markerHeight="6" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker>',
        ]
        body = ['<rect width="100%" height="100%" fill="#ffffff"/>']
        media_cache = {}
        for i, (box, target, sr) in enumerate(pics):
            if target not in media_cache:
                media_cache[target] = z.read(target)
            data = media_cache[target]
            l, t, r, b = sr
            full_w = box.w / max(1.0 - l - r, 1e-6)
            full_h = box.h / max(1.0 - t - b, 1e-6)
            ix = (box.x - l * full_w - x0) * scale
            iy = (box.y - t * full_h - y0) * scale
            mime = "image/jpeg" if target.lower().endswith((".jpg", ".jpeg")) else "image/png"
            b64 = base64.b64encode(data).decode("ascii")
            parts.append(
                f'<clipPath id="pc{i}"><rect x="{(box.x - x0) * scale:.1f}" '
                f'y="{(box.y - y0) * scale:.1f}" width="{box.w * scale:.1f}" '
                f'height="{box.h * scale:.1f}"/></clipPath>')
            body.append(
                f'<image clip-path="url(#pc{i})" x="{ix:.1f}" y="{iy:.1f}" '
                f'width="{full_w * scale:.1f}" height="{full_h * scale:.1f}" '
                f'xlink:href="data:{mime};base64,{b64}"/>')
        parts.append('</defs>')
        parts += body
        for kind, sb, sp in keep_shapes:
            parts += render_shape(kind, sb, sp, x0, y0, scale, args.max_text, args.font_scale)
        parts.append("</svg>")
        svg = "\n".join(parts)
        with open(args.out, "w") as f:
            f.write(svg)
        kb = len(svg.encode()) / 1024
        print(f"wrote {args.out}  ({W:.0f}x{H:.0f}px, {len(pics)} pic(s), "
              f"{len(keep_shapes)} shape(s), {kb:.0f} KB)")


if __name__ == "__main__":
    main()

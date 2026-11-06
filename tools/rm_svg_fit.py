#!/usr/bin/env python3
"""Fit an rmc SVG to a fixed pixel width and print the resulting pixel height.

`rmc` writes a content-based ``viewBox``. The old preview scripts replaced it
with a fixed window, which silently clipped Paper Pro pages. This helper keeps
the viewBox (optionally pads x) and only sets width/height, so Chrome
screenshots the whole page.

Aufruf:
    python3 tools/rm_svg_fit.py <page.svg> [--width 1404] [--pad-x 0.0]

Schreibt das SVG an Ort und Stelle und gibt die Pixelhoehe aus (fuer
``--window-size``). Nur Standardbibliothek.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SVG_RE = re.compile(r"<svg\b[^>]*>")
VIEWBOX_RE = re.compile(r'\sviewBox="([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)"')
SIZE_RE = re.compile(r'\s(?:width|height|viewBox)="[^"]*"')


def fit(text: str, *, width: int = 1404, pad_x: float = 0.0) -> tuple[str, int]:
    """Return the fitted SVG and its pixel height."""
    if width <= 0:
        raise ValueError(f"width muss positiv sein, nicht {width}")
    if pad_x < 0:
        raise ValueError(f"pad_x darf nicht negativ sein, nicht {pad_x}")
    match = SVG_RE.search(text)
    if not match:
        raise ValueError("kein <svg>-Kopf in der rmc-Ausgabe")
    head = match.group(0)
    viewbox = VIEWBOX_RE.search(head)
    if not viewbox:
        raise ValueError("kein viewBox in der rmc-Ausgabe")
    x, y, box_w, box_h = map(float, viewbox.groups())
    if box_w <= 0 or box_h <= 0:
        raise ValueError(f"ungueltiger viewBox: {box_w} x {box_h}")

    pad = box_w * pad_x
    x -= pad
    box_w += 2 * pad
    height = round(width * box_h / box_w)
    new_head = SIZE_RE.sub("", head)
    new_head = new_head.replace(
        "<svg",
        f'<svg width="{width}" height="{height}" '
        f'viewBox="{x:.6g} {y:.6g} {box_w:.6g} {box_h:.6g}"',
        1,
    )
    return text[:match.start()] + new_head + text[match.end():], height


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("svg", type=Path)
    parser.add_argument("--width", type=int, default=1404)
    parser.add_argument("--pad-x", type=float, default=0.0,
                        help="Anteil der viewBox-Breite, links/rechts ergaenzt (z. B. 0.5)")
    args = parser.parse_args(argv)
    try:
        text = args.svg.read_text(encoding="utf-8")
        fitted, height = fit(text, width=args.width, pad_x=args.pad_x)
        args.svg.write_text(fitted, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    print(height)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

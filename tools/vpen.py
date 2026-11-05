#!/usr/bin/env python3
"""Roh-Evdev-Strom (.vpen) lesen und als SVG-Skizze rendern.

Ein .vpen ist eine Folge von 24-Byte-``input_event``-Frames (``<qqHHi``), wie sie
das Algebra-Agent-Modul ``inject.py`` fuer das Paper-Pro-Stiftdevice dokumentiert.
Die Endung ist eine Aufnahme-Konvention, kein offizielles reMarkable-Format:
aufgenommen wird der Rohstrom, den ``/dev/input/event2`` liefert.

Aufruf:
    python3 tools/vpen.py skizze.vpen [--out skizze.svg]
                             [--page-size 1620x2160]
                             [--digitizer 11180x15340] [--stats]

Nur Standardbibliothek. Der Build bleibt offline; die Aufnahme ist ein
getrennter, bewusst gestarteter Schritt (``tools/vpen_capture.py``).
"""
from __future__ import annotations

import argparse
import html
import json
import struct
import sys
from pathlib import Path
from typing import Iterable, Iterator, Sequence

EVENT_FORMAT = "<qqHHi"
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)  # 24 Byte auf aarch64
EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
SYN_REPORT = 0
BTN_TOOL_PEN = 320
BTN_TOUCH = 330
ABS_X, ABS_Y, ABS_PRESSURE = 0, 1, 24
PAGE_SIZE = (1620, 2160)
DIGITIZER_RANGE = (11180, 15340)
PRESSURE_MAX = 2630
INK = "#1f1f1f"
WIDTH_MIN, WIDTH_MAX = 2.0, 3.4

Point = tuple[float, float, int]
Stroke = list[Point]


class VpenError(ValueError):
    """Die Aufnahme ist kein gueltiger 24-Byte-Eventstrom."""


def parse_size(text: str) -> tuple[int, int]:
    """Liest ``BREITExHOEHE``; wirft bei ungueltigen Werten einen ValueError."""
    try:
        width, height = text.lower().split("x", 1)
        size = (int(width), int(height))
    except (AttributeError, ValueError):
        raise ValueError(f"Groesse muss BREITExHOEHE sein, nicht {text!r}") from None
    if size[0] <= 0 or size[1] <= 0:
        raise ValueError(f"Groesse muss positiv sein, nicht {text!r}")
    return size


def iter_events(data: bytes) -> Iterator[tuple[int, int, int, int, int]]:
    """Zerlegt den Rohstrom in ``(sec, usec, type, code, value)``-Frames.

    Ein angebrochener Frame am Ende ist ein Fehler, kein stilles Verwerfen:
    sonst wuerde eine abgeschnittene Aufnahme als vollstaendig gelten.
    """
    if len(data) % EVENT_SIZE:
        rest = len(data) % EVENT_SIZE
        raise VpenError(
            f"unvollstaendiger Frame: {rest} Restbytes "
            f"(erwartet Vielfache von {EVENT_SIZE})"
        )
    for offset in range(0, len(data), EVENT_SIZE):
        yield struct.unpack_from(EVENT_FORMAT, data, offset)


def read_strokes(data: bytes) -> list[Stroke]:
    """Liest Striche aus dem Rohstrom.

    Akzeptiert beide Reihenfolgen: ``inject.py`` setzt ``BTN_TOUCH`` erst nach
    den ABS-Werten des ersten Punkts, echte Aufnahmen oft davor. Ein Punkt
    zaehlt bei ``SYN_REPORT`` oder beim Pen-up, sobald X und Y im laufenden
    Paket waren. Ein bereits mit ``SYN_REPORT`` abgeschlossenes Hover-Paket vor
    dem Kontakt wird verworfen, damit der Stift nicht als Strich erscheint,
    bevor er die Seite beruehrt.
    """
    events = list(iter_events(data))
    use_touch = any(
        etype == EV_KEY and code == BTN_TOUCH and value == 1
        for _, _, etype, code, value in events
    )
    start_code = BTN_TOUCH if use_touch else BTN_TOOL_PEN

    strokes: list[Stroke] = []
    current: Stroke = []
    active = False
    pen_down = touch_down = False
    x = y = None
    pressure = 0
    has_x = has_y = False
    pending_synced = False

    def append_pending() -> None:
        nonlocal has_x, has_y
        if active and has_x and has_y and x is not None and y is not None:
            current.append((float(x), float(y), max(0, int(pressure))))
        has_x = has_y = False

    def finish() -> None:
        nonlocal active, current, has_x, has_y, pending_synced
        append_pending()
        if current:
            strokes.append(current)
        current = []
        active = False
        has_x = has_y = False
        pending_synced = False

    def start() -> None:
        nonlocal active, current, has_x, has_y
        if pending_synced:
            has_x = has_y = False
        active = True
        current = []

    for _sec, _usec, etype, code, value in events:
        if etype == EV_KEY:
            if code == BTN_TOOL_PEN:
                if value == 1:
                    pen_down = True
                    if start_code == BTN_TOOL_PEN and not active:
                        start()
                elif value == 0:
                    pen_down = False
                    if start_code == BTN_TOOL_PEN and active:
                        finish()
            elif code == BTN_TOUCH:
                if value == 1:
                    touch_down = True
                    if start_code == BTN_TOUCH and not active:
                        start()
                elif value == 0:
                    touch_down = False
                    if start_code == BTN_TOUCH and active:
                        finish()
        elif etype == EV_ABS:
            if active or pen_down or touch_down:
                if code == ABS_X:
                    x, has_x, pending_synced = value, True, False
                elif code == ABS_Y:
                    y, has_y, pending_synced = value, True, False
                elif code == ABS_PRESSURE:
                    pressure, pending_synced = value, False
        elif etype == EV_SYN and code == SYN_REPORT:
            if active:
                append_pending()
            elif has_x and has_y:
                pending_synced = True
    if active:
        finish()
    return strokes


def stroke_width(points: Sequence[Point]) -> float:
    """Strichbreite aus dem mittleren Druck; ohne Druck bleibt sie duenn."""
    if not points:
        return WIDTH_MIN
    average = sum(max(0, point[2]) for point in points) / len(points)
    share = min(1.0, average / PRESSURE_MAX)
    return round(WIDTH_MIN + (WIDTH_MAX - WIDTH_MIN) * share, 2)


def _map(value: float, page_max: int, digitizer_max: int) -> float:
    scaled = float(value) * page_max / digitizer_max
    return max(0.0, min(float(page_max), scaled))


def _num(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def strokes_to_svg(strokes: Iterable[Stroke], *, page_size: tuple[int, int] = PAGE_SIZE,
                   digitizer: tuple[int, int] = DIGITIZER_RANGE,
                   title: str = "Skizze") -> str:
    """Rendert Striche als eigenstaendiges SVG mit Seitenkoordinaten."""
    page_w, page_h = page_size
    dig_w, dig_h = digitizer
    if min(page_w, page_h, dig_w, dig_h) <= 0:
        raise ValueError(f"Ungueltige Groessen: page_size={page_size!r}, digitizer={digitizer!r}")

    body: list[str] = []
    for stroke in strokes:
        if not stroke:
            continue
        width = stroke_width(stroke)
        mapped = [(_map(point[0], page_w, dig_w), _map(point[1], page_h, dig_h)) for point in stroke]
        if len(mapped) == 1:
            cx, cy = mapped[0]
            body.append(
                f'      <circle cx="{_num(cx)}" cy="{_num(cy)}" '
                f'r="{_num(width / 2)}" fill="{INK}"/>'
            )
        else:
            path = "M " + " L ".join(f"{_num(x)} {_num(y)}" for x, y in mapped)
            body.append(f'      <path d="{path}" stroke-width="{_num(width)}"/>')

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {page_w} {page_h}" '
        f'width="{page_w}" height="{page_h}" role="img">',
        f"  <title>{html.escape(title, quote=True)}</title>",
        f'  <rect width="{page_w}" height="{page_h}" fill="#fff"/>',
        f'  <g fill="none" stroke="{INK}" stroke-linecap="round" stroke-linejoin="round">',
    ]
    lines.extend(body)
    lines.extend(["  </g>", "</svg>", ""])
    return "\n".join(lines)


def render_file(src: Path, dst: Path, *, page_size: tuple[int, int] = PAGE_SIZE,
                digitizer: tuple[int, int] = DIGITIZER_RANGE) -> dict:
    """Liest ``src`` und schreibt ``dst`` als SVG; gibt Zaehlwerte zurueck."""
    strokes = read_strokes(Path(src).read_bytes())
    svg = strokes_to_svg(strokes, page_size=page_size, digitizer=digitizer)
    Path(dst).write_text(svg, encoding="utf-8")
    return {"strokes": len(strokes), "points": sum(len(stroke) for stroke in strokes),
            "bytes": len(svg.encode("utf-8"))}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path, help=".vpen-Aufnahme (rohe input_event-Frames)")
    parser.add_argument("--out", type=Path, help="Ziel-SVG (Standard: <input>.svg)")
    parser.add_argument("--page-size", default="1620x2160", help="Seitenpixel, z. B. 1620x2160")
    parser.add_argument("--digitizer", default="11180x15340", help="Digitizer-Maxima, z. B. 11180x15340")
    parser.add_argument("--stats", action="store_true", help="Zaehlwerte als JSON ausgeben")
    args = parser.parse_args(argv)
    try:
        page_size = parse_size(args.page_size)
        digitizer = parse_size(args.digitizer)
        dst = args.out or args.input.with_suffix(".svg")
        stats = render_file(args.input, dst, page_size=page_size, digitizer=digitizer)
    except (VpenError, ValueError, OSError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {stats['strokes']} Striche, {stats['points']} Punkte -> {dst}")
    if args.stats:
        print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

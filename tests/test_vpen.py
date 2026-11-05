#!/usr/bin/env python3
"""Tests für tools/vpen.py: Rohstrom, Striche, SVG und CLI."""
import io
import struct
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from tools import vpen


def frame(etype, code, value, sec=0, usec=0):
    return struct.pack(vpen.EVENT_FORMAT, sec, usec, etype, code, value)


def point(x, y, pressure=600, sec=0):
    return b"".join([
        frame(vpen.EV_ABS, vpen.ABS_X, x, sec),
        frame(vpen.EV_ABS, vpen.ABS_Y, y, sec),
        frame(vpen.EV_ABS, vpen.ABS_PRESSURE, pressure, sec),
        frame(vpen.EV_SYN, vpen.SYN_REPORT, 0, sec),
    ])


def inject_stroke(points):
    """Genau die Reihenfolge aus algebra_agent.inject.build_stream."""
    frames = [frame(vpen.EV_KEY, vpen.BTN_TOOL_PEN, 1)]
    for index, (x, y, pressure) in enumerate(points):
        frames.append(point_without_syn(x, y, pressure, sec=index))
        if index == 0:
            frames.append(frame(vpen.EV_KEY, vpen.BTN_TOUCH, 1))
        frames.append(frame(vpen.EV_SYN, vpen.SYN_REPORT, 0, sec=index))
    frames.extend([
        frame(vpen.EV_ABS, vpen.ABS_PRESSURE, 0),
        frame(vpen.EV_KEY, vpen.BTN_TOUCH, 0),
        frame(vpen.EV_SYN, vpen.SYN_REPORT, 0),
        frame(vpen.EV_KEY, vpen.BTN_TOOL_PEN, 0),
        frame(vpen.EV_SYN, vpen.SYN_REPORT, 0),
    ])
    return b"".join(frames)


def point_without_syn(x, y, pressure=600, sec=0):
    return b"".join([
        frame(vpen.EV_ABS, vpen.ABS_X, x, sec),
        frame(vpen.EV_ABS, vpen.ABS_Y, y, sec),
        frame(vpen.EV_ABS, vpen.ABS_PRESSURE, pressure, sec),
    ])


def stroke(points, *, touch=True, pen=True):
    frames = []
    if pen:
        frames.append(frame(vpen.EV_KEY, vpen.BTN_TOOL_PEN, 1))
    if touch:
        frames.append(frame(vpen.EV_KEY, vpen.BTN_TOUCH, 1))
    for index, (x, y, pressure) in enumerate(points):
        frames.append(point(x, y, pressure, sec=index))
    if touch:
        frames.append(frame(vpen.EV_KEY, vpen.BTN_TOUCH, 0))
    if pen:
        frames.append(frame(vpen.EV_KEY, vpen.BTN_TOOL_PEN, 0))
    frames.append(frame(vpen.EV_SYN, vpen.SYN_REPORT, 0))
    return b"".join(frames)


class EventStreamTest(unittest.TestCase):
    def test_frame_ist_24_byte(self):
        self.assertEqual(vpen.EVENT_SIZE, 24)

    def test_hartcodierter_little_endian_frame(self):
        data = struct.pack("<qqHHi", 1, 2, 3, 24, 2630)
        self.assertEqual(list(vpen.iter_events(data)), [(1, 2, 3, 24, 2630)])

    def test_ein_strich_mit_zwei_punkten(self):
        data = stroke([(100, 200, 500), (300, 400, 900)])
        strokes = vpen.read_strokes(data)
        self.assertEqual(len(strokes), 1)
        self.assertEqual(strokes[0], [(100.0, 200.0, 500), (300.0, 400.0, 900)])

    def test_zwei_striche(self):
        data = stroke([(1, 2, 3)]) + stroke([(4, 5, 6), (7, 8, 9)])
        self.assertEqual(len(vpen.read_strokes(data)), 2)

    def test_nur_btn_tool_pen_funktioniert(self):
        data = stroke([(10, 20, 30)], touch=False, pen=True)
        self.assertEqual(vpen.read_strokes(data), [[(10.0, 20.0, 30)]])

    def test_btn_touch_ohne_down_faellt_auf_tool_pen_zurueck(self):
        data = (frame(vpen.EV_KEY, vpen.BTN_TOUCH, 0)
                + stroke([(10, 20, 30)], touch=False, pen=True))
        self.assertEqual(vpen.read_strokes(data), [[(10.0, 20.0, 30)]])

    def test_inject_reihenfolge_ein_punkt(self):
        self.assertEqual(vpen.read_strokes(inject_stroke([(100, 200, 500)])),
                         [[(100.0, 200.0, 500)]])

    def test_inject_reihenfolge_zwei_punkte_ohne_duplikat(self):
        data = inject_stroke([(100, 200, 500), (300, 400, 900)])
        self.assertEqual(vpen.read_strokes(data),
                         [[(100.0, 200.0, 500), (300.0, 400.0, 900)]])

    def test_abgeschlossenes_hover_paket_wird_verworfen(self):
        data = b"".join([
            frame(vpen.EV_KEY, vpen.BTN_TOOL_PEN, 1),
            point_without_syn(10, 20, 100),
            frame(vpen.EV_SYN, vpen.SYN_REPORT, 0),
            frame(vpen.EV_KEY, vpen.BTN_TOUCH, 1),
            point_without_syn(30, 40, 500),
            frame(vpen.EV_SYN, vpen.SYN_REPORT, 0),
            frame(vpen.EV_KEY, vpen.BTN_TOUCH, 0),
            frame(vpen.EV_KEY, vpen.BTN_TOOL_PEN, 0),
            frame(vpen.EV_SYN, vpen.SYN_REPORT, 0),
        ])
        self.assertEqual(vpen.read_strokes(data), [[(30.0, 40.0, 500)]])

    def test_events_ausserhalb_des_kontakts_werden_ignoriert(self):
        data = (frame(vpen.EV_ABS, vpen.ABS_X, 999)
                + stroke([(10, 20, 30)])
                + frame(vpen.EV_ABS, vpen.ABS_Y, 999))
        self.assertEqual(vpen.read_strokes(data), [[(10.0, 20.0, 30)]])

    def test_syn_ohne_neue_abs_verdoppelt_keinen_punkt(self):
        data = b"".join([
            frame(vpen.EV_KEY, vpen.BTN_TOUCH, 1),
            point(10, 20, 30),
            frame(vpen.EV_SYN, vpen.SYN_REPORT, 0),
            frame(vpen.EV_SYN, vpen.SYN_REPORT, 0),
            frame(vpen.EV_KEY, vpen.BTN_TOUCH, 0),
        ])
        self.assertEqual(vpen.read_strokes(data), [[(10.0, 20.0, 30)]])

    def test_abgeschnittener_frame_ist_ein_fehler(self):
        with self.assertRaises(vpen.VpenError):
            list(vpen.iter_events(b"x" * (vpen.EVENT_SIZE + 1)))

    def test_leerer_strom_ergibt_keine_striche(self):
        self.assertEqual(vpen.read_strokes(b""), [])
        svg = vpen.strokes_to_svg([])
        self.assertNotIn("<path", svg)
        self.assertNotIn("<circle", svg)

    def test_parse_size(self):
        self.assertEqual(vpen.parse_size("1620x2160"), (1620, 2160))
        with self.assertRaises(ValueError):
            vpen.parse_size("1620")


class SvgTest(unittest.TestCase):
    def test_ecken_werden_auf_seite_abgebildet(self):
        svg = vpen.strokes_to_svg([[(0, 0, 0), (11180, 15340, 0)]])
        self.assertIn('viewBox="0 0 1620 2160"', svg)
        self.assertIn('d="M 0 0 L 1620 2160"', svg)

    def test_negative_und_zu_grosse_werte_werden_geklemmt(self):
        svg = vpen.strokes_to_svg([[[-100, -100, 0], (20000, 20000, 0)]])
        self.assertIn('d="M 0 0 L 1620 2160"', svg)

    def test_druck_bestimmt_strichbreite(self):
        thin = vpen.strokes_to_svg([[(0, 0, 0), (10, 10, 0)]])
        thick = vpen.strokes_to_svg([[(0, 0, 2630), (10, 10, 2630)]])
        self.assertIn('stroke-width="2"', thin)
        self.assertIn('stroke-width="3.4"', thick)

    def test_einzelner_punkt_wird_kreis(self):
        svg = vpen.strokes_to_svg([[(100, 200, 1000)]])
        self.assertIn("<circle", svg)
        self.assertIn('r="', svg)


class CliTest(unittest.TestCase):
    def test_cli_schreibt_svg(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "skizze.vpen"
            dst = Path(temp) / "skizze.svg"
            src.write_bytes(stroke([(0, 0, 0), (11180, 15340, 0)]))
            out = io.StringIO()
            with redirect_stdout(out):
                code = vpen.main([str(src), "--out", str(dst)])
            self.assertEqual(code, 0)
            self.assertTrue(dst.exists())
            self.assertIn("OK: 1 Striche, 2 Punkte", out.getvalue())
            self.assertIn("<svg", dst.read_text(encoding="utf-8"))

    def test_cli_meldet_kaputte_aufnahme(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / "kaputt.vpen"
            src.write_bytes(b"x" * (vpen.EVENT_SIZE + 1))
            err = io.StringIO()
            with redirect_stderr(err):
                code = vpen.main([str(src)])
            self.assertEqual(code, 1)
            self.assertIn("unvollstaendiger Frame", err.getvalue())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests für tools/rm_svg_fit.py: viewBox bleibt, Höhe folgt dem Seitenverhältnis."""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tools.rm_svg_fit import fit


CALIB = ('<svg xmlns="http://www.w3.org/2000/svg" width="470" height="683" '
         'viewBox="-223.646 0 470.558 683.582"><path d="M 0 0 L 1 1"/></svg>')
TALL = ('<svg xmlns="http://www.w3.org/2000/svg" width="621" height="2875" '
        'viewBox="-305.47 0 621.35 2874.94"><path d="M 0 0 L 1 1"/></svg>')


class FitTest(unittest.TestCase):
    def test_preview_behaelt_viewbox_und_berechnet_hoehe(self):
        fitted, height = fit(CALIB)
        self.assertEqual(height, 2040)
        self.assertIn('width="1404"', fitted)
        self.assertIn('height="2040"', fitted)
        self.assertIn('viewBox="-223.646 0 470.558 683.582"', fitted)
        self.assertNotIn('width="470"', fitted)
        self.assertNotIn('height="683"', fitted)

    def test_pull_paddet_x_und_berechnet_hoehe(self):
        fitted, height = fit(TALL, pad_x=0.5)
        self.assertEqual(height, 3248)
        self.assertIn('viewBox="-616.145 0 1242.7 2874.94"', fitted)
        self.assertIn('width="1404"', fitted)
        self.assertIn('height="3248"', fitted)

    def test_ohne_viewbox_ist_ein_fehler(self):
        with self.assertRaises(ValueError):
            fit('<svg xmlns="http://www.w3.org/2000/svg"><path d="M 0 0"/></svg>')

    def test_ungueltige_groessen_sind_fehler(self):
        with self.assertRaises(ValueError):
            fit(CALIB, width=0)
        with self.assertRaises(ValueError):
            fit(CALIB, pad_x=-0.1)
        with self.assertRaises(ValueError):
            fit('<svg viewBox="0 0 0 10"></svg>')

    def test_cli_schreibt_svg_und_gibt_hoehe_aus(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "page.svg"
            path.write_text(CALIB, encoding="utf-8")
            out = io.StringIO()
            from tools import rm_svg_fit
            with redirect_stdout(out):
                code = rm_svg_fit.main([str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(out.getvalue().strip(), "2040")
            self.assertIn('viewBox="-223.646 0 470.558 683.582"',
                          path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

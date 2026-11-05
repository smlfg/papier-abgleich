#!/usr/bin/env python3
"""Tests für build.py: Validierung, Einzeldatei, Beispiele und .vpen-Eingang."""
import json
import re
import shutil
import struct
import tempfile
import unittest
from pathlib import Path

from build import BuildError, build

ROOT = Path(__file__).resolve().parents[1]
MINIMAL = ROOT / "examples" / "minimal"
INKPARTNER = ROOT / "examples" / "inkpartner-grillme"


def event(etype, code, value):
    return struct.pack("<qqHHi", 0, 0, etype, code, value)


def vpen_bytes():
    """Reihenfolge wie algebra_agent.inject.build_stream."""
    frames = [
        event(1, 320, 1),
        event(3, 0, 100), event(3, 1, 200), event(3, 24, 800), event(1, 330, 1), event(0, 0, 0),
        event(3, 0, 900), event(3, 1, 1200), event(3, 24, 1200), event(0, 0, 0),
        event(3, 24, 0), event(1, 330, 0), event(0, 0, 0),
        event(1, 320, 0), event(0, 0, 0),
    ]
    return b"".join(frames)


def make_project(temp, *, image="notiz.png", flow_mutator=None, project_mutator=None):
    project = Path(temp) / "projekt"
    project.mkdir()
    flow = json.loads((MINIMAL / "flow.json").read_text(encoding="utf-8"))
    meta = json.loads((MINIMAL / "project.json").read_text(encoding="utf-8"))
    if flow_mutator:
        flow_mutator(flow)
    if project_mutator:
        project_mutator(meta)
    (project / "flow.json").write_text(json.dumps(flow, ensure_ascii=False), encoding="utf-8")
    (project / "project.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    if image == "notiz.png":
        shutil.copyfile(MINIMAL / "notiz.png", project / image)
    return project


class BuildTest(unittest.TestCase):
    def test_minimal_baut_und_ist_selbsttragend(self):
        with tempfile.TemporaryDirectory() as temp:
            result = build(MINIMAL, Path(temp) / "site", "minimal.html")
            self.assertEqual((result["nodes"], result["stages"]), (6, 3))
            single = Path(result["single"]).read_text(encoding="utf-8")
            leftovers = re.findall(r'(?:src|href)="(?!#|data:|https?:|\$\{)[^"]+"', single)
            self.assertEqual(leftovers, [])
            self.assertIn("data:image/png;base64,", single)

    def test_eingebettete_daten_stammen_aus_flow_json(self):
        with tempfile.TemporaryDirectory() as temp:
            result = build(MINIMAL, Path(temp) / "site", "minimal.html")
            single = Path(result["single"]).read_text(encoding="utf-8")
            match = re.search(r'<script type="application/json" id="flow">(.*?)</script>', single, re.S)
            self.assertIsNotNone(match)
            embedded = json.loads(match.group(1))
            original = json.loads((MINIMAL / "flow.json").read_text(encoding="utf-8"))
            self.assertEqual(embedded["nodes"], original["nodes"])
            self.assertEqual(embedded["stages"], original["stages"])

    def test_ungueltiger_status_wird_abgelehnt(self):
        def broken(flow):
            flow["nodes"][0]["status"] = "fast-richtig"
        with tempfile.TemporaryDirectory() as temp:
            project = make_project(temp, flow_mutator=broken)
            with self.assertRaises(BuildError):
                build(project, Path(temp) / "site", "x.html")

    def test_unbekannter_pfeil_wird_abgelehnt(self):
        def broken(flow):
            flow["nodes"][0]["next"] = ["gibt-es-nicht"]
        with tempfile.TemporaryDirectory() as temp:
            project = make_project(temp, flow_mutator=broken)
            with self.assertRaises(BuildError):
                build(project, Path(temp) / "site", "x.html")

    def test_fehlendes_bild_wird_abgelehnt(self):
        with tempfile.TemporaryDirectory() as temp:
            project = make_project(temp)
            (project / "notiz.png").unlink()
            with self.assertRaises(BuildError):
                build(project, Path(temp) / "site", "x.html")

    def test_vpen_wird_als_svg_gerendert(self):
        def image_vpen(meta):
            meta["image"] = "skizze.vpen"
        with tempfile.TemporaryDirectory() as temp:
            project = make_project(temp, project_mutator=image_vpen)
            (project / "skizze.vpen").write_bytes(vpen_bytes())
            result = build(project, Path(temp) / "site", "vpen.html")
            self.assertEqual(result["vpen"], {"strokes": 1, "points": 2})
            svg = (Path(temp) / "site" / "skizze.svg").read_text(encoding="utf-8")
            self.assertIn("<path", svg)
            single = Path(result["single"]).read_text(encoding="utf-8")
            self.assertIn("data:image/svg+xml;base64,", single)
            leftovers = re.findall(r'(?:src|href)="(?!#|data:|https?:|\$\{)[^"]+"', single)
            self.assertEqual(leftovers, [])

    def test_leere_vpen_warnt_aber_baut(self):
        def image_vpen(meta):
            meta["image"] = "leer.vpen"
        with tempfile.TemporaryDirectory() as temp:
            project = make_project(temp, project_mutator=image_vpen)
            (project / "leer.vpen").write_bytes(b"")
            result = build(project, Path(temp) / "site", "leer.html")
            self.assertTrue(any("keine Striche" in warning for warning in result["warnings"]))
            self.assertEqual(result["vpen"], {"strokes": 0, "points": 0})
            svg = (Path(temp) / "site" / "leer.svg").read_text(encoding="utf-8")
            self.assertNotIn("<path", svg)

    def test_kaputte_vpen_wird_abgelehnt(self):
        def image_vpen(meta):
            meta["image"] = "kaputt.vpen"
        with tempfile.TemporaryDirectory() as temp:
            project = make_project(temp, project_mutator=image_vpen)
            (project / "kaputt.vpen").write_bytes(b"x" * 25)
            with self.assertRaises(BuildError):
                build(project, Path(temp) / "site", "x.html")

    def test_svg_bild_wird_eingebettet(self):
        def image_svg(meta):
            meta["image"] = "notiz.svg"
        with tempfile.TemporaryDirectory() as temp:
            project = make_project(temp, image="notiz.svg", project_mutator=image_svg)
            (project / "notiz.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M 0 0 L 10 10"/></svg>',
                encoding="utf-8",
            )
            result = build(project, Path(temp) / "site", "svg.html")
            single = Path(result["single"]).read_text(encoding="utf-8")
            self.assertIn("data:image/svg+xml;base64,", single)


class ExamplesTest(unittest.TestCase):
    def test_alle_beispiele_bauen(self):
        with tempfile.TemporaryDirectory() as temp:
            minimal = build(MINIMAL, Path(temp) / "minimal", "minimal.html")
            inkpartner = build(INKPARTNER, Path(temp) / "inkpartner", "inkpartner.html")
            self.assertEqual((minimal["nodes"], minimal["stages"]), (6, 3))
            self.assertEqual((inkpartner["nodes"], inkpartner["stages"]), (24, 7))


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests für build.py: Validierung, Einzeldatei, Beispiele und Shell-Skript-Syntax."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from build import BuildError, build

ROOT = Path(__file__).resolve().parents[1]
MINIMAL = ROOT / "examples" / "minimal"
INKPARTNER = ROOT / "examples" / "inkpartner-grillme"


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


class ShellSyntaxTest(unittest.TestCase):
    def test_shell_skripte_sind_syntaktisch_gueltig(self):
        for script in ("shots.sh", "rm-pull.sh", "rm-preview.sh", "rm-push.sh"):
            proc = subprocess.run(["bash", "-n", str(ROOT / "tools" / script)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f"{script}: {proc.stderr}")


if __name__ == "__main__":
    unittest.main()

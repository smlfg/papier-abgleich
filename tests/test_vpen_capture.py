#!/usr/bin/env python3
"""Tests für tools/vpen_capture.py: Device-Erkennung, Frame-Trimmen und Kopieren."""
import io
import struct
from contextlib import redirect_stderr
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools import vpen, vpen_capture


DEVICES = '''I: Bus=0018 Vendor=04f3 Product=0001 Version=0100
N: Name="Elan touch input"
P: Phys=
H: Handlers=event3
B: PROP=2

I: Bus=0018 Vendor=04f3 Product=0002 Version=0100
N: Name="Elan marker input"
P: Phys=
H: Handlers=event2
B: PROP=0
'''


class DeviceTest(unittest.TestCase):
    def test_findet_marker_device(self):
        self.assertEqual(vpen_capture.event_device_for_name(DEVICES), "/dev/input/event2")

    def test_mehrdeutig_ist_ein_fehler(self):
        with self.assertRaises(ValueError):
            vpen_capture.event_device_for_name(DEVICES + '\nN: Name="Elan marker input"\nH: Handlers=event7\n\n')

    def test_fehlend_ist_ein_fehler(self):
        with self.assertRaises(ValueError):
            vpen_capture.event_device_for_name('N: Name="Elan touch input"\nH: Handlers=event3\n\n')


class FrameTest(unittest.TestCase):
    def test_trimmt_angebrochenen_frame(self):
        data, dropped = vpen_capture.trim_frames(b"x" * (vpen.EVENT_SIZE + 3))
        self.assertEqual(len(data), vpen.EVENT_SIZE)
        self.assertEqual(dropped, 3)

    def test_kopiert_bis_eof(self):
        source = io.BytesIO(b"abc" * 5)
        sink = bytearray()
        total = vpen_capture.copy_frames(source, sink, max_seconds=5, use_select=False)
        self.assertEqual(total, 15)
        self.assertEqual(bytes(sink), b"abc" * 5)

    def test_capture_schreibt_nur_vollstaendige_frames_und_ist_lesend(self):
        frames = b"".join([
            struct.pack("<qqHHi", 0, 0, 1, 330, 1),
            struct.pack("<qqHHi", 0, 0, 3, 0, 100),
            struct.pack("<qqHHi", 0, 0, 3, 1, 200),
            struct.pack("<qqHHi", 0, 0, 0, 0, 0),
            struct.pack("<qqHHi", 0, 0, 1, 330, 0),
            struct.pack("<qqHHi", 0, 0, 0, 0, 0),
            b"xx",
        ])
        calls = {}
        proc = FakeProc(frames, returncode=0)

        def fake_run(argv, **kwargs):
            calls["identity"] = argv
            return SimpleNamespace(stdout=DEVICES.encode(), stderr=b"")

        def fake_popen(argv, **kwargs):
            calls["reader"] = argv
            return proc

        def fake_select(read, write, except_, timeout):
            return read, [], []

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "aufnahme.vpen"
            with mock.patch.object(vpen_capture.subprocess, "Popen", side_effect=fake_popen), \
                 mock.patch.object(vpen_capture.select, "select", side_effect=fake_select):
                stats = vpen_capture.capture("host", out, seconds=1, runner=fake_run)
            self.assertEqual(out.read_bytes(), frames[:-2])
            self.assertEqual(stats["dropped"], 2)
            self.assertEqual(stats["strokes"], 1)
            self.assertEqual(stats["points"], 1)
            self.assertIn("cat /proc/bus/input/devices", calls["identity"])
            self.assertIn("exec < /dev/input/event2", " ".join(calls["reader"]))
            self.assertNotIn("cat >", " ".join(calls["reader"]))
            self.assertTrue(proc.terminated)

    def test_remote_fehler_schreibt_keine_datei(self):
        proc = FakeProc(b"\x00" * vpen.EVENT_SIZE, returncode=1)

        def fake_run(argv, **kwargs):
            return SimpleNamespace(stdout=DEVICES.encode(), stderr=b"")

        def fake_select(read, write, except_, timeout):
            return read, [], []

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "aufnahme.vpen"
            with mock.patch.object(vpen_capture.subprocess, "Popen", return_value=proc), \
                 mock.patch.object(vpen_capture.select, "select", side_effect=fake_select):
                with self.assertRaises(RuntimeError):
                    vpen_capture.capture("host", out, seconds=1, runner=fake_run)
            self.assertFalse(out.exists())
            self.assertTrue(proc.terminated)

    def test_falsche_bereitschaft_schreibt_keine_datei(self):
        proc = FakeProc(b"", stderr=b"NO\n", returncode=0)

        def fake_run(argv, **kwargs):
            return SimpleNamespace(stdout=DEVICES.encode(), stderr=b"")

        def fake_select(read, write, except_, timeout):
            return read, [], []

        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "aufnahme.vpen"
            with mock.patch.object(vpen_capture.subprocess, "Popen", return_value=proc), \
                 mock.patch.object(vpen_capture.select, "select", side_effect=fake_select):
                with self.assertRaises(RuntimeError):
                    vpen_capture.capture("host", out, seconds=1, runner=fake_run)
            self.assertFalse(out.exists())
            self.assertTrue(proc.terminated)

    def test_main_lehnt_nan_und_option_host_ab(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                vpen_capture.main(["--seconds", "nan"])
            with self.assertRaises(SystemExit):
                vpen_capture.main(["--host=-oProxyCommand=unfug"])


class FakeProc:
    def __init__(self, stdout, stderr=b"VPEN_READY\n", returncode=None):
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.terminated = False

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return self.returncode if self.returncode is not None else 0


if __name__ == "__main__":
    unittest.main()

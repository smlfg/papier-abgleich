#!/usr/bin/env python3
"""Read-only-Aufnahme des Stift-Eventstroms vom reMarkable in eine .vpen-Datei.

Der Aufruf liest ausschliesslich ``/dev/input/eventN`` (Standard: das Device
mit dem exakten Namen ``Elan marker input``) ueber SSH und schreibt die rohen
24-Byte-``input_event``-Frames lokal. Auf dem Tablet wird nichts geschrieben,
nichts gestartet und nichts geloescht. Die Aufnahme ist zeitlich begrenzt.

Aufruf:
    python3 tools/vpen_capture.py --out skizze.vpen --seconds 90

Die .vpen-Endung ist eine Aufnahme-Konvention, kein offizielles
reMarkable-Format. Der Build liest sie offline ueber ``tools/vpen.py``.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import select
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import BinaryIO

try:
    from tools import vpen
except ModuleNotFoundError:  # direkt als Skript gestartet
    import vpen  # type: ignore[no-redef]

HOST = "remarkable"
EXPECTED_NAME = "Elan marker input"
READY = b"VPEN_READY\n"
CHUNK = 64 * 1024
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=5"]


def event_device_for_name(devices_text: str, expected_name: str = EXPECTED_NAME) -> str:
    """Liefert den eindeutigen Event-Knoten fuer einen exakten Geraetenamen."""
    found: list[str] = []
    name = None
    handlers: list[str] = []
    for line in devices_text.splitlines() + [""]:
        if line.startswith("N: Name="):
            name = line.partition('Name="')[2].partition('"')[0]
        elif line.startswith("H: Handlers="):
            handlers = re.findall(r"\bevent\d+\b", line.partition("=")[2])
        elif not line.strip():
            if name == expected_name:
                found.extend(handlers)
            name, handlers = None, []
    if len(found) != 1:
        raise ValueError(f"erwartet genau ein {expected_name!r}-Event-Device, gefunden: {found}")
    return "/dev/input/" + found[0]


def trim_frames(data: bytes) -> tuple[bytes, int]:
    """Schneidet einen angebrochenen letzten Frame ab; gibt (Daten, verworfene Bytes)."""
    complete = len(data) - len(data) % vpen.EVENT_SIZE
    return data[:complete], len(data) - complete


def copy_frames(stream: BinaryIO, sink: bytearray, *, max_seconds: float,
                clock=time.monotonic, use_select: bool = True) -> int:
    """Liest Frames bis EOF oder Zeitlimit; gibt die Anzahl gelesener Bytes zurueck."""
    deadline = clock() + max_seconds
    total = 0
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            break
        if use_select:
            ready, _, _ = select.select([stream], [], [], remaining)
            if not ready:
                break
        chunk = stream.read(CHUNK)
        if not chunk:
            break
        sink.extend(chunk)
        total += len(chunk)
    return total


def capture(host: str, out: Path, *, seconds: float,
            device_name: str = EXPECTED_NAME, runner=None) -> dict:
    """Liest den Eventstrom ueber SSH und schreibt eine .vpen-Datei."""
    run = runner or (lambda argv, **kw: subprocess.run(argv, check=True, **kw))
    identity = run(["ssh", *SSH_OPTS, host, "cat /proc/bus/input/devices"],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    path = event_device_for_name(identity.stdout.decode("utf-8", "replace"), device_name)
    remote = (f"exec < {shlex.quote(path)}; "
              f"printf '%s\\n' {READY.decode().strip()} >&2; exec cat")
    proc = subprocess.Popen(["ssh", *SSH_OPTS, host, remote],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    assert proc.stdout is not None
    assert proc.stderr is not None
    try:
        ready, _, _ = select.select([proc.stderr], [], [], 5.0)
        line = proc.stderr.readline().strip() if ready else b""
        if line != READY.strip():
            detail = line.decode("utf-8", "replace") or "keine Antwort"
            raise RuntimeError(f"SSH-Event-Reader hat das Oeffnen nicht bestaetigt: {detail}")
        buffer = bytearray()
        total = copy_frames(proc.stdout, buffer, max_seconds=seconds)
        returncode = proc.poll()
        if returncode not in (None, 0):
            raise RuntimeError(f"SSH-Event-Reader endete mit Code {returncode}")
        data, dropped = trim_frames(bytes(buffer))
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + ".tmp")
        try:
            tmp.write_bytes(data)
            tmp.replace(out)
        finally:
            tmp.unlink(missing_ok=True)
        strokes = vpen.read_strokes(data)
        return {"bytes": len(data), "dropped": dropped, "strokes": len(strokes),
                "points": sum(len(stroke) for stroke in strokes),
                "device": path, "read_bytes": total}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("skizze.vpen"))
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--device-name", default=EXPECTED_NAME)
    parser.add_argument("--force", action="store_true", help="vorhandene Ausgabe ueberschreiben")
    parser.add_argument("--stats", action="store_true", help="Zaehlwerte als JSON ausgeben")
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("--seconds muss eine positive endliche Zahl sein")
    if not args.host or args.host.startswith("-"):
        parser.error("--host darf nicht leer sein oder mit '-' beginnen")
    if args.out.exists() and not args.force:
        print(f"Fehler: {args.out} existiert bereits (--force zum Ueberschreiben)", file=sys.stderr)
        return 1
    try:
        stats = capture(args.host, args.out, seconds=args.seconds, device_name=args.device_name)
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {stats['strokes']} Striche, {stats['points']} Punkte -> {args.out}")
    if stats["dropped"]:
        print(f"    {stats['dropped']} Restbytes eines angebrochenen Frames verworfen")
    if args.stats:
        print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

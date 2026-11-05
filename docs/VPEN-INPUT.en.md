# `.vpen`: sketches as a pen event stream

This page explains why `papier-abgleich` also reads a `.vpen` recording, what
is inside it, what the tests prove — and what they explicitly do **not**.

## Why not `.rm` or a screenshot?

An `.rm` poll reads a **saved state**: `stat` + `cat` return bytes, not pen
time. Between two polls, pen contact, writing start, pen-up and overwritten
intermediate states can remain invisible. This is documented in the workspace
in `Flywheelliveinput/README.md` (“Vorhandene Input-Signalwege”, 29 Oct 2026):
the implemented `.rm` reader observes *when* a poll finds a new state; its
timestamps are observation times, not pen times. A read-only `BTN_TOUCH` edge
logger exists alongside it in `Flywheelliveinput/activity_logger.py`, but it
records only contact start/end, not coordinates.

`cat` is only transport. It does not say where a stroke starts, where it ends,
or how much pressure each point had. A screenshot is even later: it shows the
result, not the events.

The event stream is the closer source. The order is therefore:

1. **`.vpen`** — raw pen events, rendered offline and deterministically.
2. **`.svg`/`.png`/`.jpg`** — an existing image when no recording is possible.
3. **`.rm`** — only as a snapshot fallback, never as a claim about pen times.

## What is a `.vpen` file?

**Not an official reMarkable format.** `.vpen` is a recording convention for
the same raw stream that the pen device `/dev/input/event2` delivers. The name
comes from the virtual pen (`vpen2`) in the Algebra Agent environment; its FIFO
`/tmp/vpen.fifo` is a **write mux** there, not a proven input reader. This
repository does not claim that the FIFO can be read.

The file is a sequence of 24-byte frames in the `<qqHHi` format. Format and
constants come from the Algebra Agent module `inject.py`; the read-only device
discovery from `Flywheelliveinput/activity_logger.py`.

| Field | Type | Meaning |
|---|---|---|
| `sec`, `usec` | `int64` | event timestamp |
| `type` | `uint16` | `EV_SYN=0`, `EV_KEY=1`, `EV_ABS=3` |
| `code` | `uint16` | e.g. `BTN_TOUCH=330`, `ABS_X=0`, `ABS_Y=1`, `ABS_PRESSURE=24` |
| `value` | `int32` | contact 0/1, coordinate or pressure |

A stroke typically looks like this:

```
BTN_TOOL_PEN 1
ABS_X, ABS_Y, ABS_PRESSURE, BTN_TOUCH 1, SYN_REPORT   (first point)
ABS_X, ABS_Y, ABS_PRESSURE, SYN_REPORT                (further points)
...
ABS_PRESSURE 0, BTN_TOUCH 0, SYN_REPORT
BTN_TOOL_PEN 0, SYN_REPORT
```

This is the order from `inject.py`; real recordings may put `BTN_TOUCH` before
the ABS values. `tools/vpen.py` accepts both. A point counts on `SYN_REPORT`
or at pen-up once X and Y were present in the current packet; a completed
hover packet before contact is discarded. A truncated frame at the end of the
file is an error, not something to silently discard.

## Recording

`tools/vpen_capture.py` reads **read-only** over SSH:

```bash
python3 tools/vpen_capture.py --out my-project/sketch.vpen --seconds 90
```

The script

- finds the device by the exact name `Elan marker input`,
- opens `/dev/input/eventN` read-only and confirms the open,
- writes a local `.vpen` file and stops after `--seconds`,
- writes nothing to the tablet, starts no service and deletes nothing.

Recording is a **deliberately started** step. The build itself stays offline
and needs neither tablet nor network.

## Render and build

```bash
python3 tools/vpen.py my-project/sketch.vpen --out my-project/sketch.svg
# or directly in the build:
# project.json:  "image": "sketch.vpen"
python3 build.py my-project --name my-project.html
```

`build.py` renders the recording to `site/<stem>.svg` and embeds it in the
single file. No new dependency; everything remains standard library.

### Coordinates

By default the digitizer `11180 × 15340` is mapped linearly onto the page
`1620 × 2160` and clamped to the page. That is sufficient for displaying the
sketch, but it is **not a calibrated page mapping**: the digitizer reports
screen coordinates; on a real session the mapping to the page depends on zoom,
scroll position and the toolbar. If a recording is already in page pixels, use
`--digitizer 1620x2160`. A page-accurate mapping needs its own device
calibration and is not claimed here.

## What the test showed

The first parser version assumed `BTN_TOUCH` comes before the ABS values.
Against the real `inject.build_stream` it lost the first point and duplicated
the last one with pressure 0. The parser therefore buffers ABS values from
`BTN_TOOL_PEN` onwards, discards a completed hover packet before contact, and
accepts a point only when X and Y were present in the packet. The regression
tests `test_inject_reihenfolge_*` and
`test_abgeschlossenes_hover_paket_wird_verworfen` pin this down.

The order remains deliberate: first build and check the minimal example
offline, then take a real recording as a separate, deliberate device step.

## What the tests prove

```bash
python3 -m unittest discover -s tests -v
```

The suite checks, among other things:

- the 24-byte frame, field layout and little-endian parsing (also hard-coded),
- strokes with `BTN_TOUCH`, with `BTN_TOOL_PEN` and in the real `inject.py` order,
- pen-up, a hover packet before contact, events outside contact,
  duplicate `SYN_REPORT` packets,
- truncated frames and empty recordings,
- pressure → stroke width, coordinate mapping and clamping,
- `.vpen` → SVG in the build, a single file without local references,
- both examples (`minimal`, `inkpartner-grillme`) still build,
- Chrome discovery in `tools/verify.py` without launching a browser.

**Not proven**: a real recording on the tablet, visibility on the display, the
latency between pen and file, or a page-accurate coordinate mapping. Those
remain device acceptance steps.

## Evidence in one sentence

`BELEGT` are the frame format and event constants from the Algebra Agent
module `inject.py`; the `.rm` snapshot limit is documented in
`Flywheelliveinput/README.md`, the read-only device discovery in
`Flywheelliveinput/activity_logger.py`. `OFFLINE` is the parser, renderer and
build path through the tests; `HYPOTHESE` remains the page-accurate mapping
without device calibration. What does **not** follow is listed above under
“Not proven”.

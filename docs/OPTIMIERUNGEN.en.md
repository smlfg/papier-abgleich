# Optimisation opportunities from the Algebra Agent

Status: 5 November 2026. This document is a **map**, not a promise. It collects
what is transferable from the Algebra Agent environment to `papier-abgleich`,
what has already been implemented, and what deliberately does not come.

Legend:

- **DONE** — in PR [#11](https://github.com/smlfg/papier-abgleich/pull/11) (open, all checks green).
- **OPEN** — next sensible step with a clear acceptance test.
- **NOT RECOMMENDED** — deliberately not, with a reason.

## Overview

| # | Optimisation | Why | Effort | Acceptance | Status |
|---|---|---|---|---|---|
| 1 | `.vpen` input instead of PNG/`.rm` | The raw stream has contact edges, X/Y and pressure; `.rm` is only a snapshot | M | parser + build + tests | DONE |
| 2 | Offline test gate + CI | 46 tests, both examples, Python 3.9/3.12 | S | CI green | DONE |
| 3 | macOS verification tools | `google-chrome`/`realpath` were Linux-only | S | `verify.py` + `shots.sh` run on macOS | DONE |
| 4 | Device acceptance of the recording | Offline tests do not prove `event2` readability or visibility | M | one deliberate real recording; SVG shows the same strokes | OPEN |
| 5 | Page calibration | The digitizer reports screen, not page coordinates | M | probe points, affine map, verification probe ≤ 2 % | OPEN |
| 6 | Two-read transcription | one read can be wrong; two can be too strict | M | `NOTIZEN.md` with confidence; no invented labels | OPEN |
| 7 | Link/evidence gate | “all links 200” is manual today | S | offline schema + optional HTTP check | OPEN |
| 8 | Example benchmark | regressions in nodes/arrows/stages/bytes go unnoticed | S | deterministic JSON + CI comparison | OPEN |
| 9 | `.rm` parser as input | snapshot limit and format risk | L | — | NOT RECOMMENDED |
| 10 | FIFO `/tmp/vpen.fifo` as input | unverified write mux, no proven reader | — | — | NOT RECOMMENDED |

Effort: S ≈ half a day, M ≈ one to two days, L ≈ more.

## The open items in detail

### 4. Device acceptance of the recording

**What:** One real, deliberately started `.vpen` recording with three strokes;
then run `tools/vpen.py` and `build.py` on it and compare the SVG with the
handwriting.

**Why:** The offline tests prove the parser, renderer and build. They do not
prove that the device delivers readable frames, that the recording is complete,
or that the strokes are visible on the display. The Flywheel logger observed
`BTN_TOUCH` naturally, but measured neither coordinates nor latency.

**Acceptance:** `vpen_capture.py --seconds 30` produces a parseable file; the
stroke count and shape match the handwriting; the original page is unchanged;
no service is started; exactly one run, only with the owner's explicit yes.

**Evidence:** `Flywheelliveinput/README.md` (event node, root, `BTN_TOUCH`
probe); `algebra-agent/LEARNINGS.md` (evdev write path on the device, reading as
a candidate).

### 5. Page calibration

**What:** A calibration file and a tool that measures the mapping from
digitizer/screen coordinates to page pixels per axis — analogous to
`tools/live_probe.py` in the Algebra Agent.

**Why:** The digitizer reports screen coordinates. The mapping to the page
depends on zoom, scroll position and the toolbar. The earlier `0.867` number was
never measured. What is established: one `.rm` document unit equals one page
pixel (IoU 0.81 against xochitl's thumbnail, maximum on 15/15 pages).

**Acceptance:** Several probe points, read back from the saved page, an affine
map per axis, and a verification probe that lands within 2 %. Nothing is
written without a passing probe.

**Evidence:** `algebra-agent/LEARNINGS.md`, entries on digitizer/viewport and
`DOC_WIDTH 1620`.

### 6. Two-read transcription

**What:** Transcribe the sketch labels with two independent reads; only
agreeing reads count as certain, otherwise `[?]` and an open question.

**Why:** A single read can be wrong; two reads can also be too strict. The
Algebra Agent benchmark shows both: raw VLM 86.4 % (19/22), the status-quo
two-reader gate only 45.5 % (10/22) on the old five pages, and 87.5 % (49/56)
on ten pages after the fixes. The lesson is not “always two readers” but
**measure whether the gate helps**.

**Acceptance:** `NOTIZEN.md` with confidence per sketch point; no invented
labels; a small benchmark over 5 sketches compares one read against two.

**Evidence:** `mlops-gedanken/5-seiten-labor/BENCHMARK-CHANGES.md`;
`algebra-agent/README.md` (two independent reads, uncertain is never green).

### 7. Link/evidence gate

**What:** `tools/check_links.py` checks the URLs in `flow.json` (HTTP 200) and
ensures unpushed commits carry `url: null`. The schema check runs offline, the
HTTP part optionally with `--online`.

**Why:** The workflow demands “all links return HTTP 200”, but today nobody
checks it automatically. A dead permalink is evidence that can no longer be
checked.

**Acceptance:** fixtures with good and broken URLs; CI checks offline; the
online run is a separate, deliberately started step.

### 8. Example benchmark

**What:** `tools/benchmark.py` builds the existing examples and writes
deterministic JSON with nodes, arrows, stages, bytes and duration. CI compares
against a checked-in baseline.

**Why:** The Algebra Agent used a 10-page benchmark to expose a regression from
86.4 % to 45.5 % and bring the fixes to 87.5 %. `papier-abgleich` today only has
“builds or does not build”; silent regressions in nodes or single-file size go
unnoticed.

**Acceptance:** JSON is stable (no mandatory timing field), CI fails on
deviation, both examples are covered.

## Not recommended

- **`.rm` as the primary input:** the poll reads a saved state; pen contact,
  pen-up and intermediate states between polls remain invisible. `.vpen` is the
  closer source; `.rm` stays a fallback.
- **FIFO `/tmp/vpen.fifo` as input:** in the Algebra Agent it is a write mux; a
  reading service, a passing test and a device start are not proven. This gap
  is not dressed up as a feature.
- **OCR directly in `build.py`:** the build stays offline and without network
  access. Transcription is a separate agent step, not a build step.

## Order

1. **Merge #11** — `.vpen` input, tests, CI and the macOS gate are ready.
2. **Device acceptance (4)** — only with an explicit yes, exactly one run.
3. **Page calibration (5)** — only after that are page-accurate claims allowed.
4. **Two reads (6) + benchmark (8)** — measure together, do not adopt blindly.
5. **Link gate (7)** — small, independent hardening.

## Not claimed

- PR #11 contains no real device recording and no live run.
- The digitizer→page mapping is not page-accurate without calibration.
- The OCR/gate numbers from the Algebra Agent prove nothing about
  `papier-abgleich`; they only justify measuring.
- `.vpen` is not an official reMarkable format.

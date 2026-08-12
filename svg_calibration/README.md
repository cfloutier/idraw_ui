# Time-estimation calibration test set

SVGs, each isolating a different combination of **pen lift count**,
**pen-down distance**, and **pen-up hop length**, so that plotting all of
them fills `logs/time_estimation_calibration.csv` with a spread of data
points to fit a time-estimation correction against. All are plain mm
coordinates on a small page (200×200 mm or 200×150 mm), positioned near the
page origin so they should fit under most machine/margin configurations.

How to use: Load each file in the Trace tab, Play, let it run to completion
(don't Stop early — only a full completion gets logged). Each run appends one
row to `logs/time_estimation_calibration.csv` with the estimated vs. actual
duration plus the drawing/profile metadata.

| File | Isolates | Expected shape |
| --- | --- | --- |
| `01_concentric_circles.svg` | Moderate lift count (6), high pen-down distance (~2 m), continuous curvature | 6 separate circles, radii 15-90 mm |
| `02_single_stroke_spiral.svg` | ~1 pen lift, high pen-down distance (~4.8 m), continuous curvature (cornering-speed model) | One path: 8-turn spiral outward, then back inward on an offset path, never lifting |
| `03_many_pen_lifts.svg` | Many pen lifts (150), ~zero pen-down distance (~0.3 m), **short** pen-up hops (~12 mm) | 150 separate 2 mm strokes in a 15×10 grid — isolates the per-lift overhead almost purely |
| `04_straight_line_back_and_forth.svg` | ~1 pen lift, high pen-down distance (~1.8 m), **zero curvature** | One 180 mm straight line traced back and forth 10 times in a single path — cleanest possible speed/accel-only baseline, no cornering-model influence |
| `05_crosshatch_grid.svg` | Realistic mixed case: moderate lifts (40) and moderate distance (~4.8 m) | 20 horizontal + 20 vertical lines forming a grid |
| `06_many_pen_lifts_long_hops.svg` | Same 150 lifts and same ~0.3 m pen-down distance as `03`, but **long** pen-up hops (~60 mm, alternating between two rows) instead of short | 150 separate 2 mm strokes, two interleaved rows 60 mm apart |
| `07_pure_pen_lifts_stationary.svg` | 300 pen lifts, minimal pen-up travel (~0.4 m, ~1.4 mm/hop) and negligible pen-down distance (~0.15 m) | 300 separate 0.5 mm strokes in a compact 20×15, 1 mm-spaced grid — the closest practical isolation of per-lift servo dwell time |
| `08_single_long_pen_up_hop.svg` | Only 2 lifts, **one single very long pen-up hop** (~250 mm) | 2 tiny 2 mm marks at opposite corners of the page — isolates whether a single long trapezoidal pen-up move has a timing error by itself, independent of hop *count* |

Why this spread: `pen_lifts` ranges from ~1 to 150 and pen-down distance from
~0.3 m to ~4.8 m across the set, largely independently of each other, so a fit
against the CSV can separate the "per-lift" contribution (pen servo dwell,
now computed by the restored `PenLiftTiming.update()` in `idraw2_internal`)
from the "per-distance" contribution (XY motion time) instead of only ever
seeing them change together, as a real mixed drawing would.

Files 02 and 04 both isolate "~1 lift, high distance" but differ in
curvature (continuous spiral vs. straight reversals) — comparing their
estimate/actual ratio should show whether the cornering-speed model
(`plan_trajectory()` in `motion.py`) is a meaningful source of error on its
own, separate from the pen-lift fix.

**03 vs 06** isolate the same question for pen-*up* travel: both have exactly
150 lifts and the same 300 mm of pen-down drawing, only the hop length
between marks differs (~12 mm vs ~60 mm, though the actual optimizer-driven
travel patterns ended up longer than designed — see the real numbers below).

**07** goes one step further: 300 lifts packed as tightly as practical
(1 mm apart, ~1.4 mm/hop average) with negligible pen-down distance, so
`(estimated - actual) / 300` on this file's row is close to the actual
per-lift error in milliseconds, with very little XY-motion model involved to
muddy the number.

**Results so far** (first real-hardware run): `07` came back at 100.0%
(estimated 103.22s vs. actual 103.18s) — the restored `PenLiftTiming`
formula is essentially correct on its own. `06` at the same pen-height
(`v_dist` = 10) came back at only 88.0% (147.36s estimated vs. 129.69s
actual), despite having *fewer* lifts (151 vs. 301) — the only structural
difference is `06`'s much longer average pen-up hop (~124 mm vs. ~4.7 mm).
So the per-lift timing is not the (remaining) problem; a long pen-up hop is.

Traced this into `idraw2_0internal`: every pen-up hop goes through
`iDraw.go_to_position()` (`idraw.py`) → `motion.compute_segment()` with
zero initial/final velocity. A ~4.7 mm hop stays in the "Triangle" case
(never reaches cruising speed); a ~124 mm hop is long enough to hit the
"Trapezoid" case (accelerate → cruise → decelerate). `07`'s hops are all
Triangle, `06`'s are all Trapezoid — which is exactly the axis along which
the error appeared. Nothing incorrect found in `compute_segment()` itself on
a read-through (and `enable_motors()` correctly syncs `speed_penup` from
`ad_ref.options` before every plot, ruling out a stale-config-default bug).

**08** isolates this cleanly: only 2 lifts (like `02`/`04`, both close to
perfectly estimated already), but the two marks sit at opposite corners of
the page so there is exactly **one** long (~250 mm) Trapezoid-case pen-up
hop between them. If `08` shows a large proportional error from a *single*
long hop, the Trapezoid-case computation itself is the culprit. If `08` is
accurate, the error in `06` only shows up when *many* separate Trapezoid
hops accumulate — pointing instead at something per-move in the real
(non-preview) path, e.g. the `move_time - 30` sleep adjustment in
`dripfeed.feed_sm()` (real mode only, not mirrored in the preview
accumulation) or per-command serial round-trip latency.

**Result and fix**: `08` came back accurate at every speed tested
(100.6-103.2%, three runs at very different `speed_penup` values) — ruling
out the Trapezoid-case computation itself. That confirmed the second
hypothesis: `dripfeed.feed_sm()` sleeps `move_time - 30 ms` in real mode for
every motion sub-command over 50 ms, but preview always added the full
`move_time`. A single ~250 mm hop only produces ~12 sub-commands (~0.2-1 s of
uncounted discount, lost in the noise of a short test); 151 repeated ~124 mm
hops produce ~1500 (tens of seconds of discount, exactly matching the
observed gap). Short ~4.7 mm hops (`07`) mostly stay under the 50 ms gate
entirely, so they were never affected — consistent with `07`'s 100.0% result.
Fixed in `dripfeed.py` to apply the same discount in preview. Re-run `03`,
`05`, `06` (the tests that showed the largest gaps) to confirm.

**Known vendor issue, worked around here**: an earlier version of this file
clustered all 300 marks within a 0.3 mm span (truly ~zero pen-up travel).
Loading it froze the app. Root cause: `idraw2_0internal/plot_optimizations.py`
`connect_nearby_ends()` tries to join any path endpoints closer than
`min_gap` (0.008 in ≈ 0.2 mm) — with everything crammed into 0.3 mm, nearly
all 300 paths were mutually "nearby," and that join pass became pathological
(at best very slow, possibly worse; not fully root-caused). The working
`marilyn_A4_*.svg` stippling example in `test_svg_files/` spaces its dots
~1-2 mm apart and loads fine, which is the clue that led here. `07` now uses
1 mm spacing (5x the `min_gap` threshold) to stay well clear of this path
entirely — safe, but not investigated/fixed at the vendor level. Worth a
closer look later if a real drawing ever legitimately needs sub-0.2 mm-spaced
marks, but out of scope for calibration.

## Testing different pen heights

`PenLiftTiming`'s formula scales with `v_dist = |pen_pos_up - pen_pos_down|`
(the Draw Profile tab's Pen Up / Pen Down height settings) — none of the
files above vary this, since pen height is a *profile* setting, not
something an SVG file controls. To check whether the model's dependence on
`v_dist` is roughly right, re-run the same lift-heavy file (`03` or `06`,
whichever isolates cleanly per the paragraph above) two or three times with
different **Pen Down** height values in the Draw Profile tab before each Play
(e.g. a small gap ~2 mm, the current default ~5 mm, and a large gap ~9 mm),
keeping Pen Up height fixed. All three runs will show up as separate CSV rows
for the same `svg_name` but different `pen_down_height` — the estimate/actual
ratio should move in a consistent direction as the gap grows if the model's
`v_dist` scaling is in the right ballpark.

Regenerated with a small script (not checked in) if the geometry ever needs
tweaking — regular SVG files, safe to hand-edit too.

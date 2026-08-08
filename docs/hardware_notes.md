# Hardware Notes

## 2026-08-03 - Direction axes

![Axis mapping observed on hardware](axes.png)



Context:
- Test action: press `Center` after `Home`.
- Center command currently sends a sequence: `Home`, then relative move of +300 mm in X and -400 mm in Y.
- Initial position before test: carriage manually placed near center.

Observed behavior (user validation on machine):
- Home reference zone is in the bottom-right area.
- Axis mapping validated with jog tests:
  - `+X` moves the carriage to the left
  - `+Y` moves the carriage toward `Home` (down on the frame view)

Interpretation to keep for adjustments:
- Positive X currently maps to motion toward the left.
- Positive Y currently maps to motion toward the operator (down in the frame representation).

Center implication:
- From `Home` (bottom-right), an inward safe test move is `+X` and `-Y`.
- This matches the current `Center` implementation (`Home`, then `+300 X`, `-400 Y`).

Manual stop behavior:
- During manual actions (home/center/jog), the Stop button triggers forced disconnect.
- This interruption is best effort (serial teardown); exact stop timing depends on firmware command state.

Practical impact:
- Do not assume a "math-style" axis orientation for this machine.
- Any helper motion (centering, safe offsets, edge avoidance checks) must use this observed orientation.
- Before changing signs in motion helpers, validate again on hardware with a short move (for example 10 mm).

## 2026-08-08 - Initial SVG placement test

Test setup:
- A6 SVG in portrait mode.
- Pen manually positioned at the center before plotting.

Observed behavior:
- The current runtime draws toward the upper-left area from the starting point.
- This behavior is consistent with the runtime's historical setup, but its
  terminology must not define the new UI convention.

Project interpretation:
- A drawing extending left and up is visually anchored at `bottom-right`.
- The application owns the following logical-home convention:
  - `top-left` uses the lower-right zone.
  - `top-right` uses the lower-left zone.
  - `bottom-left` uses the upper-right zone.
  - `bottom-right` uses the upper-left zone.
- In every case, the drawing must extend inward from the selected logical home
  and remain inside the usable plotter bounds.

Next validation:
- Repeat physical tests for all four logical-home choices.
- Record the required SVG transform for each choice before implementing the
  final plotting-orientation pipeline.

Implemented test candidate (not yet hardware-validated):
- The app adapter now mirrors the iDraw digest after vendor rotation/clipping,
  while keeping every point inside the positive SVG page bounds.
- No vendor source has been modified.
- The transformed PLOB is reused by Play/Resume without applying the mirror twice.

Safe physical test protocol:
- Keep the A1 machine and portrait table setup used for the initial observation.
- Use `test_svg_files/_test_a6.svg`.
- Place the pen near the center, leaving at least one A6 page dimension free in
  every direction.
- Select one logical home at a time, reload the SVG (or let Play re-prepare it),
  then plot.
- Expected zones from the chosen starting point:
  - `bottom-right`: upper-left
  - `bottom-left`: upper-right
  - `top-right`: lower-left
  - `top-left`: lower-right
- Stop immediately if the first pen-up move heads toward an unexpected zone.
- Validate portrait first. Treat landscape mapping as unvalidated until it gets
  its own physical test series.

Physical result 1 - `bottom-left`:
- Setup: A1 machine, portrait table, A6 test SVG, pen initially near center.
- Selected logical home: `bottom-left`.
- Observed drawing zone: lower-right from the initial center point.
- Expected from the project convention: upper-right.
- Interpretation: the horizontal adaptation is consistent (`right`), but the
  vertical direction is inverted relative to the expected zone (`down` instead
  of `up`).
- Do not validate the current four-corner mapping yet. Use the next test to
  isolate whether vertical mirroring must be globally inverted or depends on
  another runtime/table-orientation convention.

Physical result 2 - `bottom-right`:
- Setup unchanged: A1 machine, portrait table, A6 test SVG, pen initially near
  center.
- Selected logical home: `bottom-right`.
- Observed drawing zone: upper-right from the initial center point.
- Expected from the project convention: upper-left.

Combined interpretation of results 1 and 2:
- Current `bottom-right` uses no digest mirror and produces right/up.
- Current `bottom-left` differs only by a digest X mirror and produces
  right/down.
- Therefore, in this physical/runtime setup, mirroring digest X changes the
  visual vertical direction rather than the visual horizontal direction.
- This disproves the earlier hypothesis of a simple global Y inversion. The
  digest axes must be mapped through the runtime/machine axis permutation before
  selecting mirrors for visual table corners.
- The next discriminating test is `top-right`, which currently applies only a
  digest Y mirror. It will show whether digest Y controls the visual horizontal
  direction as expected from the observed axis permutation.

Physical result 3 - `top-right`:
- Setup unchanged: A1 machine, portrait table, A6 test SVG, pen initially near
  center.
- Selected logical home: `top-right`.
- Observed drawing zone with the initial adapter: upper-left.
- This confirms that mirroring digest Y changes the visual horizontal direction
  (`right` to `left`) while preserving the visual vertical direction.

Corrected matrix derived from physical observations:
- Digest X mirror controls visual top/bottom.
- Digest Y mirror controls visual left/right.
- Required digest transforms for the project convention:
  - `bottom-left`: no mirror -> expected upper-right
  - `bottom-right`: mirror digest Y -> expected upper-left
  - `top-left`: mirror digest X -> expected lower-right
  - `top-right`: mirror digest X and Y -> expected lower-left
- This corrected matrix is now implemented. All four zones must be physically
  retested before marking portrait placement as validated.

Corrected mapping validation - `top-right`:
- The application was fully restarted after the mapping code change, then the
  SVG was prepared again for `top-right`.
- Observed drawing zone: lower-left from the initial center point.
- Expected drawing zone: lower-left.
- Result: `top-right` is physically validated for the A1 portrait + A6 test setup.
- Important test rule: after changing orientation code, restart the running app
  before interpreting a physical result; Python does not reload edited modules
  in the existing process.

Corrected mapping validation - `top-left`:
- The SVG was prepared for `top-left` with the corrected mapping loaded.
- Observed drawing zone: lower-right from the initial center point.
- Expected drawing zone: lower-right.
- Result: `top-left` is physically validated for the A1 portrait + A6 test setup.

Corrected mapping validation - `bottom-right`:
- The SVG was prepared for `bottom-right` with the corrected mapping loaded.
- Observed drawing zone: upper-left from the initial center point.
- Expected drawing zone: upper-left.
- Result: `bottom-right` is physically validated for the A1 portrait + A6 test setup.

Corrected mapping validation - `bottom-left`:
- The SVG was prepared for `bottom-left` with the corrected mapping loaded.
- Observed drawing zone: upper-right from the initial center point.
- Expected drawing zone: upper-right.
- Result: `bottom-left` is physically validated for the A1 portrait + A6 test setup.

Portrait validation conclusion:
- All four logical-home choices are physically validated on the A1 machine with
  the portrait table setup and the A6 test SVG:
  - `top-left`: lower-right
  - `top-right`: lower-left
  - `bottom-left`: upper-right
  - `bottom-right`: upper-left
- This validates the corrected digest mirror matrix for this setup.
- Landscape behavior and explicit large-SVG bounds protection remain separate,
  unvalidated follow-up work.

## 2026-08-08 - Pre-existing 180-degree content rotation

Observation:
- Before the logical-home corrections, the A6 drawing content was already
  rotated by 180 degrees.
- The four-home mirror work correctly selected drawing zones but did not cause
  this content-orientation issue.

Implemented correction candidate:
- Apply one global 180-degree rotation to the digest after vendor
  rotation/clipping and before logical-home relative transforms are finalized.
- Keep the same logical start coordinates, so the four validated quadrants do
  not change.
- Store `idraw_ui_content_orientation=upright-v1` in PLOB metadata so Play and
  Resume do not rotate the content twice.

Next physical check:
- Restart the application, reload the A6 SVG, and test one already validated
  home first.
- Expected: same quadrant as before, but A6 text/arrow upright rather than
  rotated by 180 degrees.

## 2026-08-08 - Horizontal flip after the 180-degree correction

Observation:
- With `bottom-right`, the drawing reached the expected upper-left A6 zone and
  the arrow pointed up, but text was reflected left-to-right.
- The remaining digest Y mirror was therefore changing visual horizontal
  orientation, exactly as the earlier axis tests predicted.

Correction:
- Logical homes now select only their start coordinates; they no longer mirror
  digest geometry.
- All four homes produce identical digest coordinates while retaining their
  four distinct start corners.
- A fresh Play now reads the original SVG instead of the prepared PLOB. Preview
  reproduction showed that plotting the prepared PLOB in `plot` mode introduced
  an additional vendor-side 180-degree rotation.

Validation:
- The real runtime produces identical geometry for all four homes.
- The rendered `bottom-right` PLOB has readable, non-reflected text.
- After a full app restart and SVG reload, all four logical homes were tested
  physically with the A6 test SVG on the A1 portrait setup.
- All four drawings reached the expected zones with upright, non-reflected
  content. The corrected portrait mapping is physically validated.
- Landscape behavior and explicit large-SVG bounds protection remain separate,
  unvalidated follow-up work.

## 2026-08-08 - Landscape validation

Setup: A1 machine, landscape table orientation, A6 test SVG, pen near center.
Physical home confirmed at bottom-left, jog axes confirmed matching the Machine
page display (X+=up, Y+=left).

Issues encountered and resolved:
- SVG content 90° rotated: vendor `auto_rotate=True` was rotating the portrait
  A6 SVG to landscape internally; combined with our X+Y correction this
  produced a net 90° error. Fix: force `auto_rotate=False` for landscape only.
- SVG content 180° rotated: in landscape the raw vendor digest arrives already
  upright (no 180° rotation); our portrait X+Y correction was being applied
  incorrectly. Fix: skip the global X+Y correction when orientation=landscape.
- Wrong drawing zone for bottom-right and top-left: the start_pos formula
  (mirror_x/mirror_y) derived for portrait does not directly apply to landscape
  because the machine axes are 90° rotated. Fix: for landscape,
  `(mirror_x, mirror_y) = (portrait_mirror_y, NOT portrait_mirror_x)`,
  which maps "right"→mirror_x and "bottom"→mirror_y instead of "top"/"right".

Final validated landscape results with A1 + A6 test SVG:
  - `top-left`: lower-right ✓
  - `top-right`: lower-left ✓
  - `bottom-left`: upper-right ✓
  - `bottom-right`: upper-left ✓

Both portrait and landscape are now fully validated for all four logical home
corners. Content appears upright and non-reflected in both orientations.

Runtime rules now in effect:
- Portrait: `auto_rotate=True`, global X+Y correction applied.
- Landscape: `auto_rotate=False`, global X+Y correction skipped.
- start_pos formula: portrait uses `logical_home_mirror_axes` directly;
  landscape swaps and inverts: `(mirror_y, NOT mirror_x)`.

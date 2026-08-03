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

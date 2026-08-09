# Validation checklist

## 0 — Setup

- [ ] Python 3.10+ installed, `run.bat` launches the app without error
- [ ] Machine connected via USB, iDraw model selected in **Machine** tab

---

## 1 — Machine configuration

- [ ] Physical home goes to the correct corner (limit switches) and pen raises before moving
- [ ] Jog **physical mode** (+X/−X/+Y/−Y) moves in the correct visual direction on the table
- [ ] Jog **table mode** (right/left/forward/backward) is consistent with the Machine tab preview arrows
- [ ] Keyboard arrow keys trigger jog when the Jog tab is active
- [ ] **Center** moves the carriage to the centre of the work area
- [ ] Changing table orientation (portrait ↔ landscape) updates the Machine preview and jog axes immediately

---

## 2 — Drawing margins — set from hardware

- [ ] Click **Home** on the Jog tab → position display resets to 0
- [ ] Jog to a physical boundary, click **Set Top** / **Set Bottom** / **Set Left** / **Set Right** → value saved and Machine preview updates
- [ ] Machine tab preview shows the asymmetric usable-area rectangle (dotted) matching the four margin values
- [ ] Trace tab preview places the SVG inside the correct margin zone

---

## 3 — Home corner (all 4)

For each home corner (`top-left`, `top-right`, `bottom-left`, `bottom-right`) in **portrait** and in **landscape**:

- [ ] **Portrait** — pen draws in the expected inward quadrant from the chosen corner
- [ ] **Landscape** — same check with machine in landscape orientation

---

## 4 — SVG orientation

- [ ] Content is upright (Up arrow ↑, text readable) in **portrait**
- [ ] Content is upright (Up arrow ↑, text readable) in **landscape**
- [ ] Content is not mirrored (horizontally or vertically) in either mode

---

## 5 — Trace tab

- [ ] **Load SVG** opens the file dialog in the last used folder (not a temp folder)
- [ ] **Reload** reloads the last explicitly user-loaded SVG
- [ ] After **Plot marks**, clicking Load SVG still opens the last user folder
- [ ] Preview shows the correct page placement and home marker before plotting
- [ ] **OUT OF BOUNDS** warning appears when the SVG does not fit the drawing area
- [ ] Reordering combo (Least / Basic / Full / None) changes the path order visibly
- [ ] Machine off → Play shows an immediate error, not a silent success

---

## 6 — Plot lifecycle

- [ ] **Play** starts the plot from the beginning
- [ ] **Pause** stops mid-stroke cleanly
- [ ] **Resume** continues from where it paused
- [ ] **Stop** interrupts the plot and the carriage returns to its pre-Play position
- [ ] After a natural finish, the carriage returns to the pre-Play position automatically

---

## 7 — Pen height (Draw Profile)

- [ ] Adjusting **Pen up height** and clicking **Pen Up** moves the pen to the configured height
- [ ] Adjusting **Pen down height** and clicking **Pen Down** moves the pen to the configured height
- [ ] During a real plot, pen up/down heights match the profile values (not the vendor defaults of 0.5 / 5)
- [ ] **Apply live** toggle applies slider changes in real time without re-plotting

---

## 8 — Speed and acceleration

- [ ] Travel speed slider changes the pen-up movement speed noticeably
- [ ] Drawing speed slider changes the stroke speed noticeably
- [ ] Estimate duration changes when speed values are modified

---

## 9 — Profiles

- [ ] Creating a new profile saves all speed and pen height values
- [ ] Switching profiles restores the correct values in all sliders
- [ ] Profile values persist after restarting the application

---

## 10 — Registration marks (Marks tab)

- [ ] Format selector and orientation toggle update the preview immediately
- [ ] Mark arm slider changes the corner mark size visibly in the preview
- [ ] **Plot marks** switches to Trace tab, loads and estimates the marks SVG
- [ ] Plotted marks are at the correct corners of the selected format
- [ ] Marks are not clipped (0.2 mm inset working)

---

## 11 — Log tab

- [ ] All significant events appear in the log (load, estimate, play, stop, errors)
- [ ] Timestamps are correct

---

## Notes

Record your observations here as you run through the checklist.

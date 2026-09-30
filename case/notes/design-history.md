# Case design history

What was tried, what failed and why the current numbers are what they are. The README
describes the case as it is; this file is the reasoning. All fits are measured in ABS.

## Layout

- **Battery-beside box** (until 2026-09-12): the cell lay next to the PCB. Wider than
  needed. In git history before 2026-09-12.
- **First stacked attempt** (2026-08-31): cell under the PCB, but too tight to work in.
  Scrapped.
- **Stacked layout** (2026-09-12, current): cell flat under the PCB in a rib pocket, PCB on
  posts, open pockets in front of (2 mm) and behind (4 mm) the board for fingers and the
  battery lead. Roomier on purpose. First printed 2026-09-14.
- **Posts** were 11 mm until 2026-09-14, now 8 (cell 6 + foam 1.5 + 0.5 for solder on the
  bare PCB bottom). The BAT1 tails lie beside the cell in X, not over it, which is asserted.
- **Wire-management rule** from the first boxes: exits are open to the seam and at the
  wire's height. Stiff wires take neither threading nor a vertical detour. Printed wire
  clips and guides do not work; use shorter or softer wire and glue.

## Closure

- **Screws** (first cases): threads in plastic stripped; heat-set inserts made assembly slow.
- **Continuous snap bead** on a 2.4 mm wall left 0.45 mm of lip behind the groove, which
  loosened after a few openings.
- **Cantilever fingers** (current). First stacked print 2026-09-14 had a 0.45 bead with 45°
  ramps on both retention faces: closed but held loosely. Now bead 0.55, a 0.4 click-in
  chamfer below and only 0.15 above, so most of the bead is a flat retention face.
- Press-fit walls are still thin and may loosen after repeated disassembly (2026-09-02).
  Revisit with the next case revision.

## Light pipe

- **Stepped counterbore** (first stacked print, 2026-09-14): the lid prints upside-down,
  so the step was a 1 mm ledge over the bed-side opening. The slicer filled it with
  support and the edge came out ragged. Replaced by a 26.6° funnel, under the slicer's 30°
  support threshold.
- **Snap bead inside the collar**: a bead deep enough to click is deeper than a solid pipe
  can squeeze past, and the 0.6 mm collar wall just splayed.
- **Interference bore** (`led_stem_clr` −0.10, ~0.05/side): could not be pressed in by
  hand, reverted 2026-09-20.
- **Slip fit + glue** (current): stem and head both drop in, the 2.6 mm collar keeps it
  straight, one drop of glue holds it. Do not go back to a negative `led_stem_clr`.
- The pipe gap to the LEDs is 0.8 since 2026-09-16.

## Switch

- **SS12F15 slide switch** on M2 screw pillars, until 2026-09-14. The pillar bosses were the
  fit-critical interference; they are gone and the fit is now enforced as keepout geometry
  and asserts, not by looking at a preview.
- **KCD11 snap-in rocker** (current) on the front wall. The lid grew to make room for the
  latch pocket; that, not the PH plugs, now sets the lid height.

## USB-C opening

- **Plug pocket** (14 × 9.5 × 1.2) added 2026-09-14; the user's old Fusion case had one.
- **`usb_shell_poke`** 1.4 (2026-09-19): slides the board toward the USB wall so the shell
  noses into the recess instead of stopping 0.4 short. Plug seats deeper, box 1.4 narrower.

## Lid text

- **Arial "OpenRZ67" / "Trigger"** (until 2026-09-14): uneven weights, wide gap, near the
  edge. DIN Alternate was tried and dropped for Futura Bold.
- **Rail** across the LED row: the off-centre LED (fixed by the PCB) reads as an indicator
  on a line instead of a hole that missed the middle.
- **Empty pockets** at 0.6 mm: the lid prints upside down, so a pocket floor is a bridge.
  It sagged and the letters read fuzzy (2026-09-16). Now an inlay part on filament 2, so
  the letters print first, flat on the bed.
- **Depth** 0.6 (3 layers) until 2026-09-17: body colour ghosted through. 0.8 now; 0.9 is
  the cap from the antenna-recess assert at `lid_top_t` 2.0.
- **Why not slicer colour painting**: stored per mesh triangle, wiped by every re-export.
- **Why not a height-range modifier**: QIDI Studio (≤ v2.x) segfaults on opening a .3mf
  that carries `Metadata/layer_config_ranges.xml`. Per-object settings are safe.
- The inlay never matches a true empty recess (the colour boundary sits in the spreading
  first layer). Soluble support (HIPS under ABS) would allow a real recess: parked.

## Camera plug (removed in dff0c23)

`camera_plug.py` was a printed two-half clamshell around four Dupont sleeves, with press pegs and later
rib-and-groove sides (2026-09-08 to 2026-09-10). Hole tuning: Ø1.5 no-go, Ø1.7 very tight,
pegs sheared. Never got it working; the sleeves are still taped one by one (2026-09-18).
Candidate replacement: a stamped 2.54 mm female header strip cut to 4.

## Other

- D3 (red) moved next to the BQ25185 charger 2026-09-07, so the light-pipe window is
  centred between the two LEDs.
- Antenna: own 40 × 20 antennas were too big for the ceiling band; Ebyte TX2400-FPC-2509
  (25 × 9) chosen 2026-09-16, Molex 146153-0050 as fallback.
- The box is wider than the old Fusion case (59 mm) because of the side-entry U4 and the KCD11
  rocker, both deliberate.

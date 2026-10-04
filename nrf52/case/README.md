# Parametric enclosure for the nRF52 board (build123d)

`openrz67_nrf_case.py` is a two-part snap-fit box for the coin-cell board in
[`../kicad/`](../kicad/). Outer size with default values: **34.2 × 37.2 × 12.6 mm**. Printed in
ABS, lid upside-down, base floor-down, no supports.

Layout: the board rests on a 1 mm ledge around the base cavity, component side up, with the
CR2032 and its clip hanging below it. The lid presses the board onto the ledge with four
bosses and carries the button tab, the LED hole and the opening for the camera plug. The
floor is flat and closed, for velcro on the camera. To change the cell, take the lid off and
turn the base over: the board drops out, and the cell slides sideways out of the clip.

## Source data

Board coordinates are the KiCad coordinates of `openrz67-nrf.kicad_pcb` (origin top-left,
Y toward the back wall). Values come from `../kicad/tools/design.py` and the part datasheets:

| What | Value |
|---|---|
| Board | 27 × 29 mm, R0.8, 1.6 thick, no mounting holes |
| Cell clip `BT1` (back) | 25.9 × 9.4, 3.75 high, cell Ø20 × 3.2 under it, centre (13.5, 18) |
| Button `SW1` | B3U-1000P at (6.0, 27.6), 1.6 high |
| LED `D1` | (15.8, 27.6) |
| Camera connector `J1` | SM04B-SRSS-TB at (21.3, 24.7), 6.0 wide, 2.9 high, mouth toward board y = 29 |
| Module `U1` | 15 × 19 × 2.0 incl. pads, antenna end at board y = 0 |

## Construction

- **Base**: tub with a board ledge: a wall standing on the floor up to `pcb_z`, `ledge_gap`
  (0.2) inside the lid tongue, reaching `ledge_w` (1.4) in from the wall (1.0 under the
  board). Below the tongue it joins the outer wall. Broken on both sides where the clip
  passes and along the back where the cell comes within 1 mm of the board edge. The front
  ledge bridges `ant_wall_clr` (1.0 mm of air in front of the antenna end). Flat closed
  floor. Pry slot on the front wall at the seam.
- **Lid**: telescoping tongue (`lap` 5) with four snap fingers on the **side** walls (the
  back wall carries the plug opening). Hold-down bosses (`bosses`, board x/y/Ø) at four free
  spots: the module owns the front-left corner and `C1` + `J1` the back-right one.
  - **Button**: a `tab_w × tab_l` (6 × 8) cantilever tab cut free by a `tab_slot` (0.7) U-slot,
    hinged at its front end, thinned to `tab_t` (1.0) from the inside, with a Ø`nub_d` (2.4)
    nub that stops `nub_gap` (0.3) above the switch cap.
  - **LED**: Ø`led_hole_d` (1.6) hole straight through the top over `D1`.
  - **Text**: "OpenRZ67" over a tracked "TRIGGER", Futura Bold grown `lid_text_bold` (0.1)
    per side so every stroke is at least 0.6 mm, debossed `lid_text_depth`
    (0.8) into the top, centred on the lid. The pockets are filled by
    `openrz67-nrf-lid-text.stl`, a second part of the lid on filament 2 in the .3mf.
    `LID_TEXT_SHOW=false` turns it off; `LID_TEXT` / `LID_TEXT_SIZE` change the name line.
  - **Plug opening**: connector width + 2 × `conn_clr` (0.5), from the board top up
    `conn_h + conn_clr`, open to the seam, so the lid lifts off with the plug in place. The base
    keeps a full-thickness wall under it and one `wall` to each side; the lid tongue is
    notched over that whole stretch.
- **Snap**: the ESP32 case's finger geometry unchanged (`snap_bead` 0.55, `bead_h` 1.4, 0.4
  click-in / 0.15 retention chamfers, `finger_t` 1.0, `finger_slot` 0.8), fingers 10 long,
  `wall` 3.2 so both lap halves stay two perimeters thick. Tune with `SNAP_TEST=true`.

The script carries module-level assertions: each part is one body, base and lid do not
overlap, outer dimensions, the board / cell / clip / module / connector / switch / LED
keepouts, every opening breaking through, and the front ledge actually being under the
board. They run on every export.

## Usage

```sh
cd nrf52/case
./export.sh                          # base + lid -> stl/, then openrz67-nrf-case.3mf
SNAP_TEST=true ./export.sh           # also a cropped corner pair (not in the .3mf)
```

Requires [uv](https://docs.astral.sh/uv/); the script carries its own dependency header.

`openrz67-nrf-case.3mf` is the QIDI Studio project: plate 1, base floor-down, lid upside-down,
ABS profile, lid text on filament 2. `../../case/make_3mf.py` builds it by swapping the fresh STLs into
`qidi-template.3mf`, so the slicer settings survive every re-export. To change settings or the
plate layout: open the project in QIDI Studio, change it, save, and copy it over
`qidi-template.3mf`.

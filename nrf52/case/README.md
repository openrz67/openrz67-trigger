# Parametric enclosure for the nRF52 board (build123d)

`openrz67_nrf_case.py` is a two-part snap-fit box, plus a light pipe, for the coin-cell board in
[`../kicad/`](../kicad/). Outer size with default values: **37.2 × 37.2 × 12.6 mm**. Printed in
ABS, lid upside-down, base floor-down, no supports. The light pipe prints in clear filament,
head-down, and is glued into the lid.

Layout: the board rests on a 1 mm ledge around the base cavity, component side up, with the
CR2032 and its clip hanging below it. The lid presses the board onto the ledge with four
bosses and carries the button tab, the LED light pipe and the opening for the camera plug. The
floor is flat and closed, for velcro on the camera. Two hooks in the lid clip under the
board's side edges. To change the cell, pry the lid off with a coin in the front slot: the
board comes with it, and the cell slides backwards out of the clip. To take the board out of
the lid, pull the tab under each hook outward.

## Source data

Board coordinates are the KiCad coordinates of `openrz67-nrf.kicad_pcb` (origin top-left,
Y toward the back wall). KiCad's view turned 180° puts the antenna at the front, so board X
runs right to left in the case: the module sits front-right, the camera plug back-left. Values come from `../kicad/tools/design.py` and the part datasheets:

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
  (0.2) inside the lid tongue, reaching 1.0 under the board on every side (`ledge_w` 1.4
  from the front and back walls). Below the tongue it joins the outer wall. Broken on both
  sides where the clip passes and the hooks hang, and along the back where the cell comes
  within 1 mm of the board edge. The base keeps its full wall along the whole back. A 10 mm
  "+" is debossed 0.4 into the floor under the cell: the cell's + side faces the floor. The front
  ledge bridges `ant_wall_clr` (1.0 mm of air in front of the antenna end). Flat closed
  floor. Pry slot on the front wall at the seam.
- **Orientation rib** (`orient_mark_*`): a 2.5 × 0.8 rib on the front wall, 7 tall, split at
  the seam between base and lid. The halves line up only when the lid is on the right way
  around. Off-centre at board x 4, clear of the pry slot.
- **Lid**: telescoping tongue (`lap` 5) with four snap fingers on the **side** walls (the
  back wall carries the plug opening). Hold-down bosses (`bosses`, board x/y/Ø) at four free
  spots: the module owns the board's (0, 0) corner and `C1` + `J1` the (27, 29) one.
  - **Button**: a `tab_w × tab_l` (6 × 7.45) cantilever tab cut free by a `tab_slot` (0.7)
    U-slot, hinged at its front end, thinned to `tab_t` (0.8) from the inside, with a
    Ø`nub_d` (2.4) nub that stops `nub_gap` (0.3) above the switch cap. The free end is
    `tab_tip` (1.45) past the switch centre, so it ends over the cavity, not over the wall.
  - **LED light pipe**: a top hat over `D1`, as on the ESP32 case. Ø`led_stem_d` (2.2) stem,
    ending `led_pipe_gap` (0.8) above the board, in a slip-fit window (`led_pipe_clr` 0.2)
    that a collar off the ceiling lengthens down to the pipe's lower end. The head tapers out
    by `led_head_lip` (0.7) over `led_head_t` (1.4), 26.6° from vertical, into a matching
    funnel in the top, so it self-centres and nothing needs support. Glued.
  - **Text**: "OpenRZ67" over a tracked "TRIGGER", Futura Bold grown `lid_text_bold` (0.1)
    per side so every stroke is at least 0.6 mm, debossed `lid_text_depth`
    (0.8) into the top, centred on the lid. The pockets are filled by
    `openrz67-nrf-lid-text.stl`, a second part of the lid on filament 2 in the .3mf.
    `LID_TEXT_SHOW=false` turns it off; `LID_TEXT` / `LID_TEXT_SIZE` change the name line.
  - **Board hooks** (`hook_*`): a 1.0 × 3.4 finger off the ceiling on each side wall, at
    board y 13.45, between the snap fingers and in front of the clip's solder legs. The barb
    reaches `hook_grip` (0.5) under the board, with a flat face toward the board and a 45°
    lead-in below it. `hook_flex` (0.7) of air behind the finger lets it spring out as the
    board goes in. A `hook_tab` (1.5) below the barb is the release: pull it outward with a
    fingernail between the tab and the clip leg. The hooks set the board-to-side-wall gap,
    `side_clr` (1.9).
  - **Plug opening**: connector width + 2 × `conn_clr` (0.5), from the board top up
    `conn_h + conn_clr`, open to the seam, so the lid lifts off with the plug in place.
  - **No tongue on the back wall**: the base has its full wall there instead. That gives the
    plug a floor, and with the board in the lid the cell slides out backwards under it.
- **Snap**: the ESP32 case's finger geometry unchanged (`snap_bead` 0.55, `bead_h` 1.4, 0.4
  click-in / 0.15 retention chamfers, `finger_t` 1.0, `finger_slot` 0.8), fingers 10 long,
  `wall` 3.2 so both lap halves stay two perimeters thick. Tune with `SNAP_TEST=true`.

The script carries module-level assertions: each part is one body, base and lid do not
overlap, outer dimensions, the board / cell / clip / module / connector / switch / LED
keepouts (the clip as strap plus solder legs, from its 3D model), the bosses and the light-pipe collar clear of every top-side part, the light pipe
clear of the lid, the button tab tip over the cavity, the
camera plug opening on the left (a board mapped without the mirror fails here), every opening breaking through, the orientation rib clear of the pry slot and the
lid chamfer, the front ledge actually being under the
board, the board hooks (placed where intended, clear of the snap finger slots, air behind
them, reaching under the board) and the cell's way out backwards with the board in the lid. They run on every export.

## Usage

```sh
cd nrf52/case
./export.sh                          # base + lid + light pipe -> stl/, then openrz67-nrf-case.3mf
SNAP_TEST=true ./export.sh           # also a cropped corner pair (not in the .3mf)
```

Requires [uv](https://docs.astral.sh/uv/); the script carries its own dependency header.

`openrz67-nrf-case.3mf` is the QIDI Studio project: plate 1 base floor-down and lid upside-down
(ABS profile, lid text on filament 2), plate 2 the light pipe head-down on filament 3 (clear,
0.28 mm layers, 100 % infill, 20 mm/s). The template has the ESP32 case's settings. `../../case/make_3mf.py` builds it by swapping the fresh STLs into
`qidi-template.3mf`, so the slicer settings survive every re-export. To change settings or the
plate layout: open the project in QIDI Studio, change it, save, and copy it over
`qidi-template.3mf`.

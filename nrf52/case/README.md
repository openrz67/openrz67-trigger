# Parametric enclosure for the nRF52 board (build123d)

`openrz67_nrf_case.py` is a two-part snap-fit box for the coin-cell board in
[`../kicad/`](../kicad/). Outer size with default values: **34.2 × 37.2 × 12.6 mm**. Printed in
ABS, lid upside-down, base floor-down, no supports.

Layout: the board rests on a 1 mm ledge around the base cavity, component side up, with the
CR2032 and its clip hanging below it. The lid presses the board onto the ledge with four
bosses and carries the button tab, the LED hole and the opening for the camera plug. A Ø14
hole in the floor lets a finger push the board up and out; the cell is changed with the board
out of the box (it slides sideways out of the clip).

## Source data

Board coordinates are the KiCad coordinates of `openrz67-nrf.kicad_pcb` (origin top-left,
Y toward the back wall). Values come from `../kicad/tools/design.py` and the part datasheets:

| What | Value |
|---|---|
| Board | 27 × 29 mm, R0.8, 1.6 thick, no mounting holes |
| Cell clip `BT1` (back) | 25.9 × 9.4, 3.75 high, cell Ø20 × 3.2 under it, centre (13.5, 18) |
| Button `SW1` | B3U-1000P at (6.0, 27.6), 1.6 high |
| LED `D1` | (12.0, 27.6) |
| Camera connector `J1` | SM04B-SRSS-TB at (21.3, 24.7), 6.0 wide, 2.9 high, mouth toward board y = 29 |
| Module `U1` | 15 × 19 × 2.0 incl. pads, antenna end at board y = 0 |

## Construction

- **Base**: tub with a `ledge_w` (1.4 from the wall, 1.0 under the board) × `ledge_h` (1.2)
  ledge at `pcb_z`, broken on both sides where the clip passes over it and along the back
  where the cell comes within 1 mm of the board edge. The front ledge bridges `ant_wall_clr`
  (1.0 mm of air in front of the antenna end). `floor_hole_d` (14) push-out hole under the
  cell. Pry slot on the front wall at the seam.
- **Lid**: telescoping tongue (`lap` 5) with four snap fingers on the **side** walls (the
  back wall carries the plug opening). Hold-down bosses (`bosses`, board x/y/Ø) at four free
  spots: the module owns the front-left corner and `C1` + `J1` the back-right one.
  - **Button**: a `tab_w × tab_l` (6 × 8) cantilever tab cut free by a `tab_slot` (0.7) U-slot,
    hinged at its front end, thinned to `tab_t` (1.0) from the inside, with a Ø`nub_d` (2.4)
    nub that stops `nub_gap` (0.3) above the switch cap.
  - **LED**: Ø`led_hole_d` (1.6) hole straight through the top over `D1`.
  - **Plug opening**: connector width + 2 × `conn_clr` (0.5), from the board top up
    `conn_h + conn_clr`, open to the seam, so the lid lifts off with the plug in place. The base
    keeps a full-thickness wall under it.
- **Snap**: the ESP32 case's finger geometry unchanged (`snap_bead` 0.55, `bead_h` 1.4, 0.4
  click-in / 0.15 retention chamfers, `finger_t` 1.0, `finger_slot` 0.8), fingers 10 long,
  `wall` 3.2 so both lap halves stay two perimeters thick. Tune with `SNAP_TEST=true`.

The script carries module-level assertions: outer dimensions, the board / cell / clip /
module / connector / switch / LED keepouts, every opening breaking through, and the front
ledge actually being under the board. They run on every export.

## Usage

```sh
cd nrf52/case
uv run openrz67_nrf_case.py          # base + lid -> stl/
SNAP_TEST=true uv run openrz67_nrf_case.py   # also a cropped corner pair
```

Requires [uv](https://docs.astral.sh/uv/); the script carries its own dependency header.
No slicer project yet: open the two STLs in QIDI Studio (lid upside-down, base floor-down,
elephant-foot compensation on).

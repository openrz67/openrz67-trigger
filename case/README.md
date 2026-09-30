# Parametric enclosure (build123d)

`openrz67_case.py` is a parametric two-part enclosure for the OpenRZ67 trigger PCB, written
in [build123d](https://build123d.readthedocs.io/). It is built from the board file and its
footprints, not from eyeballed measurements. Drawn for rev 2 (tag `pcb-rev2`); rev 3 keeps
the outline, holes and every connector and LED position, so the same case fits.

Layout: the LiPo cell lies flat **under the PCB** in a low rib pocket, the PCB sits on 8 mm
posts, and open pockets in front of (2 mm) and behind (4 mm) the board take fingers and the
battery lead. `U4` and its plug stay inside; only the heat-shrunk camera cable leaves
through a keyhole slot in the right wall. The lid snaps on, no hardware.

Finished size with default values: ~**64.9 × 36.0 × 25.5 mm**. The lid height is set by the
rocker switch's latch pocket. Printed in ABS; all fit numbers are ABS-measured.

The reasoning behind the numbers, and everything that was tried and dropped, is in
[`notes/design-history.md`](notes/design-history.md).

## Source data

Board coordinates in the script have the origin at the board's front-left corner with Y
toward the back; KiCad measures Y from the other long edge, so `board_y = 22 - kicad_y`
(`../pcb/kicad/out/openrz67-pos.csv` lists KiCad Y as negative numbers; drop the sign).

| Measurement | Value | Source |
|-----|-------|-------|
| Board outline | 48.0 × 22.0 mm, R2.0 | `openrz67.kicad_pcb` Edge.Cuts |
| Mounting holes | 2× Ø2.0 at (2,2) and (46,20) | `MountingHole_2.0mm_Pad3.0` footprints |
| PCB thickness | 1.6 mm | `pcb_t` (as ordered) |
| Component placement | see `openrz67_case.py` | `out/openrz67-pos.csv` |
| U4 camera connector | side-entry S4B-XH-A, pin row at (44.3, 11), mouth facing +X; body 12.4 wide × 6.1 tall, mouth 5.5 mm past the board edge | `CONN-TH_S4B-XH-A-LF-SN.kicad_mod` + `.wrl` |
| USB-C connector | body 8.95 × 3.2 mm, left edge 4.8 mm in from the PCB's left edge; shell protrudes ~2 mm past the board | measured |
| Rocker switch (KCD11) | snap-in body 13.5×8.5 (= panel cutout), flange 15×10, 10 deep behind the flange, two 2.8 mm tabs ~5 long at ~7 mm pitch; vendor drawings differ by ~0.5 mm | vendor data — measure your switch |
| FPC antenna | Ebyte TX2400-FPC-2509, 25 × 9 × ~0.2 mm, U.FL, ~100 mm cable, to `A1` | vendor data |
| LEDs | D3 red (20.5, 18.0), D4 blue (24.2, 20.2), 0603 top-emitting | `out/openrz67-pos.csv` |

Component heights are editable constants (`h_usbc`, `h_ph_plug`, `xh_h`) from the datasheets
and 3D models. Check them against your own parts.

The script carries **module-level assertions**: outer dimensions, probe checks that every
opening breaks through (USB, camera cable slot, LED window, locating-pin recesses, switch
hole and latch pocket), and that the fit-critical keepouts (switch body + tabs + receptacles,
USB-C body, U4 + mated plug, the cell under the PCB) stay open. They run on every export, so
a parameter tweak that closes a hole or re-introduces a known collision fails loudly.

## Construction

- **Base** (tub): floor, four **8 mm posts** (`standoff_h`; two at the mounting holes, two at
  `pcb_supports = [[2,20],[46,2]]`), and two **Ø1.85 locating pins** (`pin_d`) up into the
  board's Ø2 mounting holes. The cell lies on the floor between the posts, lengthwise from
  board-X `batt_x0`, inside a low rib ring (`batt_rib_t/h`, `batt_clr`) with foam tape on top.
  - **Through-hole solder relief** (`th_keepouts`, `[board_x, board_y, diameter]`,
    `th_keepout_depth` 3.5): a pocket in a post top where a through-hole part's tails stick down.
  - **Guide fins** (`frame_*`): fins from the wall across the pockets hold the PCB in Y, two
    per long edge (`frame_ribs_front/back`), ending `frame_clr` from the board edge with a
    lead-in lip `frame_proud` above it. The lid tongue is notched where they stand.
- **Lid**: telescopes into the base via a perimeter tongue (`lap` 7 mm). Carries the USB-C
  opening (left), the camera cable slot (right), the LED light-pipe seat (top) and the snap-in
  hole for the rocker switch (front). Top edge chamfered `lid_top_r` (2 mm, 45°): the lid
  prints upside-down, so this is the bed-side edge.
  - **Camera cable slot** (`cut_cable`): the U4 body and the mated XHP-4 plug (`xh_plug_proud`
    2.5 past the mouth, an estimate) stay inside; `xh_slack` (1.5) sets `pcb_overhang_right`
    (9.1). The cable leaves through a **keyhole** in the right wall: round top of `cable_d` +
    2 × `cable_clr` (Ø6) at the header's mid-height, open straight down to the seam, so the
    bundle drops in as the lid closes and the lid lifts off untethered.
  - **LED light pipe** (`led_*`, separate part, clear filament): a top hat with a tapered
    head in a 26.6° funnel seat and a rod down to `led_pipe_gap` (0.8) above the LEDs. **Slip
    fit, glued**: `led_stem_clr` = `led_pipe_clr` (0.2). A collar `led_collar_h` (2.6) off the
    ceiling keeps it straight. Parameters: `led_win_l/w/r`, `led_head_lip/t`, `led_pos`.
  - **Component clearance** (`comp_keepouts`): rectangles cut out of the lid's hold-down
    bosses where a boss would hit a component (e.g. the boss at hole (2,2) is D-shaped to
    clear the USB-C body).
  - **Antenna recess** (`ant_*`): a 25.6 × 9.6 × 0.3 mm pocket in the lid ceiling for the
    adhesive FPC antenna, in the free band between the rocker body and the light-pipe stem.
    `ant_cx_frac` (0.25) slides it along the band. Asserted to fit the band and to leave
    ≥ 0.8 mm of top plate under the lid text.
- **USB-C side**: `pcb_overhang_left` (2.0) makes room for the shell; `usb_shell_poke` (1.4)
  slides the board toward that wall so the shell noses into the recess. On the right,
  `pcb_overhang_right` (9.1) makes room for the mated XH plug.
- **Battery** (31 × 20 × 6 LiPo): under the PCB with `batt_foam` (1.5) between. Its lead comes
  out at the left end over the rib, into the 4 mm pocket behind the board, up past the edge
  and into BAT1 on top. Nothing is threaded: cell in, board onto the pins, lead over the
  edge, lid on. Parameters: `batt_w/l/t`, `batt_x0`, `batt_foam`, `batt_clr`, `batt_rib_t/h`,
  `pocket_front/back`.

## Closure — snap fingers

Four **cantilever fingers** cut free in the lid tongue (two per long wall, `snap_fingers_x`)
carry a bead (`snap_bead` 0.55, `bead_h` 1.4; 0.4 click-in chamfer below, 0.15 above) that
clicks into a pocket in the base lip (`pocket_extra_d/h`, `pocket_ch`). Each finger is
`finger_l` (12) long and `finger_t` (1.0) thick with a `finger_slot` (0.8) relief at each end;
the bead sits `bead_tip_h` (1.1) above the tip, so the lever is ~6 mm: about 2 % strain at
full deflection. The rest of the tongue and the base lip stay rigid (`wall` 3.2). The PCB is
pressed onto the posts by the lid's hold-down bosses (blind pin recesses, no holes through
the top). Open with a coin in the **pry slot** (`pry_w/d/h`) on the back wall; the back
fingers release first.

**Tune before the full print:** `SNAP_TEST=true ./export.sh` also exports a cropped
front-left corner pair (`openrz67-snaptest-*`) with one finger and one locating pin. Print
those and adjust `snap_bead` (click strength), `finger_t` (stiffness) and `lap_gap` (sliding
fit) until the corner snaps shut and pries open with reasonable force.

## Orientation mark — `orient_mark`

A raised rib on the front wall near the left corner, split across the seam: base carries the
lower half, lid the upper. Lid on the right way round, the halves line up; 180° wrong, the
lid's half lands at the other corner. Parameters `orient_mark_x/w/d/h`; delete the two
`orient_mark_rib` lines to remove it.

## Lid text — second colour (`lid_texts`)

Debossed nameplate in front of the LED seat: **"OpenRZ67"** (9.5 mm) over a tracked all-caps
**"TRIGGER"** (5 mm, +1.0 letter spacing), Futura Bold (macOS system font; OCCT falls back to
Arial if missing). A thin rail (`lid_rail_*`) runs across the LED row and breaks around the
light-pipe seat. Pockets are `lid_text_depth` (0.8 mm, 4 layers; 0.9 is the cap) deep and an
**inlay** solid (`lid_text`, exported as `openrz67-lid-text.stl`) fills them exactly.
Assertions enforce placement and printability (every glyph stroke ≥ `lid_text_min_stroke`
0.6 mm).

Colour it by **part, not by slicer paint**: `make_3mf.py` adds the inlay to the lid object as
a second part on filament 2 (`SUB_PARTS`). Set filament 2 to the letter colour and print. On
a single-filament printer, delete the inlay part and do a manual filament change at Z = 0.8
(slice the lid alone).

Edit `lid_texts`, `lid_font`, `lid_text_gap` and `lid_rail_*` to restyle; `LID_TEXT_SHOW=false`
disables the text.

## Usage

The parameters are plain Python constants at the top of `openrz67_case.py`. Requires
[uv](https://docs.astral.sh/uv/); the script carries its own dependency header.

```bash
cd case
./export.sh            # base, lid, lightpipe, lid text -> stl/  + openrz67-case.3mf
./export.sh out        # custom output dir (skips the .3mf)
```

Overrides from the environment:

```bash
LID_TEXT_SHOW=false  ./export.sh   # hide the lid text
LID_TEXT="My text"   ./export.sh   # the name line (TRIGGER stays)
LID_TEXT_SIZE=8.0    ./export.sh   # its font size (mm, default 9.5)
SNAP_TEST=true       ./export.sh   # also export the corner test pair
PCB_T=1.0            ./export.sh   # PCB thickness (sets the base/lid split)
MAKE_3MF=false       ./export.sh   # skip the .3mf
```

Or run the script directly: `uv run openrz67_case.py`. For a plain interpreter there is a
local venv: `uv venv .venv && uv pip install -p .venv "build123d>=0.11.1"` (git-ignored, as
is `stl/`). For a 3D preview, open the file with an OCP viewer (e.g. `ocp_vscode`) or inspect
the STLs in the slicer.

### Slicer project (.3mf)

`export.sh` rebuilds `openrz67-case.3mf`, a Bambu Studio / OrcaSlicer / QIDI Studio project:
base + lid on plate 1 (filament 1, lid text on filament 2), the light pipe alone on plate 2
(filament 3 = clear) with its own object settings (0.28 layers, 100 % infill, 8 walls,
20 mm/s). `make_3mf.py` swaps the fresh meshes into a template saved from the slicer
(`bambu-template.3mf`), so all slicer settings are preserved. To change print settings, plate
layout or filament mapping, edit the project in the slicer and re-save it over
`bambu-template.3mf`. Plate thumbnails are not regenerated; the slicer refreshes them.

Do not use height-range modifiers in the template: QIDI Studio crashes on opening a .3mf
that carries them. Per-object settings are safe.

## Print orientation

- **Base**: floor down. No supports.
- **Lid**: **upside down** (top plate on the bed). Bosses and lip point up, and the LED funnel
  is widest at the bed. Turn elephant-foot compensation on (~0.15) so the first layer does
  not close in on the funnel rim; support threshold 30° or lower.
- **Light pipe**: clear filament, upright (head down). For the clearest light: thick layers
  (0.28–0.3), 100 % infill, slow, hot, fan off, on a **smooth** plate (the head's top face
  prints against it).

## Worth adjusting before printing

- `pcb_t`: PCB thickness (1.6 as ordered). Sets the base/lid split height.
- `pcb_overhang_left`: air for the USB-C shell. Measure your connector. Default 2.0.
- `h_ph_plug`: PHR-2 plug + wire bend height on `BAT1`/`S3`. Lower it if yours sit lower.
- `xh_plug_proud` / `xh_slack`: mated XHP-4 plug past the U4 mouth (2.5, estimate) and air to
  the wall. `cable_d`: the heat-shrunk bundle's diameter (5.0).
- `snap_bead` / `finger_t` / `lap_gap`: tune with the `SNAP_TEST` corner pieces.
- `batt_*`: your cell and its pocket. `standoff_h` must stay ≥ cell + foam (asserted).
- `ant_l/w/clr/depth` / `ant_cx_frac`: the antenna and its recess. Optional part; BLE works
  without it at much less range.
- `sx`: rocker switch position, centred on the lid (`outer_w / 2`) on the front wall. The
  back wall carries S3, the LEDs and the lead pocket. `kcd_gap` (1.6) is the body's height
  above the PCB.
- **Switch mount**: hole `kcd_body_l/h` + 2 × `kcd_hole_clr` (0.3); the wall is pocketed from
  the inside to `kcd_panel_t` (2.0) for the latches, `kcd_latch_clr` (1.2) past the hole.
  Asserted clear of the tongue, ceiling, seam and chamfer. **Measure your switch first**: body,
  flange, depth, tab length and pitch, panel thickness.
- **Switch wiring**: two 2.8 mm **flag (90°) receptacles** on the tabs, 4–6 cm of 26 AWG to
  the PH plug in S3. A straight receptacle does not fit behind the switch (asserted). Fold
  the thin wire end double for the crimp.

## USB-C opening

Three layers in the wall, outside in:

- **Plug pocket** `usb_pocket_w/h/r/d` = 14 × 9.5 mm, R3, 1.2 deep, 45° bevel `usb_pocket_ch`
  (0.6). The cable's overmold sinks into it. Fits overmolds up to 13 × 8.5.
- **Pass-through** `usb_open_w/h` = 10 × 4.6 mm, R1.8. Its edge is the lip (0.8 mm, asserted)
  that stops the overmold.
- **Inner recess** `usb_recess_w/h/d` = 13 × 9 × 1.2 mm on the cavity side: the receptacle
  shell noses into it, 0.2 short of its floor (asserted).

The opening's centre (`usb_zc`) sits 1.65 mm above the base/lid split, so `cut_usb` is
subtracted from both parts and the base keeps full wall through the lap zone (`usb_solid_w`).
Measure your charging cable; test with a print of just the left end first.

## Known / to verify

- Check that your charging cable reaches the port.
- Measure `xh_plug_proud` and `cable_d` against your cable.
- Print the `SNAP_TEST` corner first.
- **Light pipe**: verify the rod lands over D3/D4 (`led_pos`) and clears them
  (`led_pipe_gap`). Drop it in and glue it on top. Rattles sideways: lengthen `led_collar_h`.
  Never a negative `led_stem_clr`.
- The USB-C and switch openings are open by necessity; the LED window is sealed by the pipe.

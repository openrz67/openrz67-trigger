# Parametric enclosure (build123d)

`openrz67_case.py` is a parametric two-part enclosure for the OpenRZ67 trigger PCB
**rev 2** (the KiCad project in `../pcb/kicad/`), written in
[build123d](https://build123d.readthedocs.io/) (Python). It is built from the board
file and its footprints, not from eyeballed measurements.

> Rev 2 keeps the 48 × 22 mm outline, the mounting holes, `BAT1` (top side, same
> place) and `S3` of the fabricated 2025-09-23 board, so the battery-beside layout
> carries over unchanged. What changed for the case: `U4` is now a **side-entry**
> S4B-XH-A whose body reaches **5.5 mm past the board edge**, so the cavity is 3 mm
> wider on the right and the connector passes through the lid wall; the G6K relays
> became low PhotoMOS parts. Not yet print-tested against a rev 2 board.

## Source data

Board coordinates in the script have the origin at the board's front-left corner
with Y toward the back; KiCad measures Y from the other long edge, so
`board_y = 22 - kicad_y` (`../pcb/kicad/out/openrz67-pos.csv` lists KiCad Y as
negative numbers — drop the sign).

| Measurement | Value | Source |
|-----|-------|-------|
| Board outline | 48.0 × 22.0 mm, R2.0 | `openrz67.kicad_pcb` Edge.Cuts |
| Mounting holes | 2× Ø2.0 at (2,2) and (46,20) | `MountingHole_2.0mm_Pad3.0` footprints |
| PCB thickness | 1.6 mm | `pcb_t` (as ordered) |
| Component placement | see openrz67_case.py | `out/openrz67-pos.csv` |
| U4 camera connector | side-entry S4B-XH-A, pin row at (44.3, 11), mouth facing +X; body 12.4 wide × 6.1 tall, 9.2 mm from pin row to mouth face and 2.3 to the rear face, i.e. the mouth sits 5.5 mm past the board edge | `CONN-TH_S4B-XH-A-LF-SN.kicad_mod` F.Fab + `.wrl` |
| USB-C connector | body 8.95 × 3.2 mm on the PCB, left edge 4.8 mm in from the PCB's left edge; the shell protrudes ~2 mm past the board edge | measured physically |
| Total HW length | ~50 mm (PCB 48 + USB-C shell 2) | `pcb_overhang_left` |
| Slide switch (SS12F15) | actuator opening 10.65×6.3; flat bracket 19.45×5.75×0.4; screw holes Ø2.2 at 15.0 mm spacing; body ~19.5×20×12.9 | `SS12F15.stp` + measured |
| LEDs | D3 red (20.5, 18.0), D4 blue (24.2, 20.2) – 0603 SMD, top-emitting; D3 moved next to the BQ25185 charger 2026-09-07, so the 6 × 4.4 light-pipe window is centred between them | `out/openrz67-pos.csv` |

Component **heights** are editable constants (`h_usbc`, `h_ph_plug`, `xh_h`) from the
datasheets / 3D models. `h_ph_plug` (8 mm: a PHR-2 plug in the 6 mm PH header plus the
wire bend on top, on `BAT1` and `S3`) is the tallest thing on rev 2 and sets the lid
height. Check them against your own parts.

The script carries **module-level assertions**: outer dimensions, plus probe checks that
every opening actually breaks through (USB, LED window, locating-pin recesses, switch
screws) and that the fit-critical keepouts (switch body envelope, USB-C body, the U4
connector body through the right wall, a fitted 8.5 mm vertical header on J1) stay open. They run on every export, so a parameter tweak that closes a hole or re-introduces
a known collision fails loudly instead of surfacing in the print.

## Construction
- **Base** (tub): floor, a **battery bay beside the PCB** (behind its back edge, separated
  by a divider wall), low standoffs that raise the PCB ~3.5 mm (only the through-hole
  solder tails need clearance underneath), **solid support pillars** in all four corners
  (`pcb_supports = [[2,20],[46,2]]` plus the two posts at the mounting holes), and two
  **Ø1.7 locating pins** up into the real Ø2 mounting holes.
  - **Through-hole solder relief** (`th_keepouts`): a small pocket in the top of a
    pillar where a through-hole component's pin tails/solder stick down (the pillar at
    (2,20) sits next to BAT1). The list is `[board_x, board_y, relief_diameter]`;
    `th_keepout_depth` sets how far down (3.5 mm, the PH tail length from the 3D model; with
    `standoff_h` 3.5 the pocket reaches the floor).
  - **PCB frame / guide fins** (`frame_*`): the lap joint removes the inner wall at board
    height, so **guide fins** in the ~1.2 mm tongue channel hold the PCB sideways: a thick
    fin beside the board edge with `frame_clr` (0.2 mm) clearance, plus a thin lead-in
    lip `frame_proud` (0.6 mm) above the board top. The lid tongue is cut away where the
    fins sit (`frame_tongue_notch`, clearance `frame_notch_clr`). The board drops straight
    down and is captured in Y between the front fins and the battery-bay **divider wall**
    (whose front face sits `frame_clr` from the board's back edge — `frame_ribs_back = []`).
    `frame_ribs_front` are the fin centres in board-X (default `[10, 38]`).
- **Lid**: telescopes down into the base via a perimeter tongue-and-groove edge (lap
  joint) for alignment. Carries the USB-C opening (left), the opening for the U4
  camera connector (right), the LED light-pipe window (top), and the slot + screw
  pillars for the SS12F15 slide switch.
  - **U4 opening** (`cut_xh`): the side-entry S4B-XH-A body sits in a rectangular
    through-cut in the lid's right wall (body + `xh_clr` all round). The cut runs the full
    `lap` below the split too, so there is no tongue or snap bead in the U4 band: the tongue
    would otherwise have to pass through the connector body while the lid is lowered (a
    closed-state probe cannot see that; a lift sweep does). The XHP plug goes in from **outside**,
    like the USB-C. The mouth face ends `xh_recess` (0.3 mm) inside the outer wall face —
    `pcb_overhang_right` is derived from that, so a different connector reach
    (`xh_mouth`) moves the wall, not the connector. The old drop-in cable slit is gone:
    the cable no longer lives inside the box. The lid's (46,20) hold-down boss is cut
    back (`comp_keepouts`) where it would touch the connector body 0.3 mm away. The base's
    outer wall half is lowered 0.25 mm in the same band: the body underside sits exactly at
    the split, and a proud print would otherwise lift the PCB off its posts.
  - **LED light pipe** (`led_*`, separate part): D3 (red) and D4 (blue) are top-emitting
    SMD LEDs ~8 mm below the lid. A separate **clear light pipe** is inserted from above
    as a top hat: a wide head in a top counterbore (flush with the top face) + a rod that
    goes down to ~1.5 mm above the LEDs and channels the light into two sharp dots. The
    lid is printed opaque; **only the light pipe is printed in clear filament**. It rests
    in the counterbore (gravity + optionally a drop of glue to seal). Parameters:
    `led_win_l/w/r` (window size), `led_head_lip/t` (head/counterbore), `led_pipe_gap`
    (air gap to the LED), `led_pipe_clr` (fit in the hole). `led_pos` are the LED
    positions from pick&place.
  - **Component clearance** (`comp_keepouts`): rectangles `[board_x0, board_y0, board_x1,
    board_y1]` cut out of the lid's hold-down bosses (full height above the PCB) where a
    boss would collide with a component body — e.g. the Ø6 boss at hole (2,2) is cut back
    to a D-shape to clear the USB-C connector's near edge (~board-Y 4.8).
- **USB-C asymmetry**: the USB-C shell protrudes ~2 mm past the PCB's left short side.
  `pcb_overhang_left = 2.0` extends the cavity on the left; the PCB is therefore centred
  toward the RIGHT in the cavity (normal `clr = 0.4` against the right wall, `clr +
  overhang = 2.4 mm` against the left). On the right, `pcb_overhang_right` (3.0 mm,
  derived from the U4 reach) does the same for the camera connector. The outer case
  width thus becomes ~**58.6 mm**.
- **The battery** (250 mAh LiPo) lies **beside the PCB** in its own bay behind the board's
  back edge, bounded by the **divider wall** (front, top flush with the split — it doubles
  as the PCB's back guide), the case walls (back/sides), and two low ribs that stop the
  cell sliding in X. BAT1 sits at board ≈ (3.3, 17) on the PCB top, so the lead just
  **drapes over the divider** and plugs straight in — short and flat. Everything is
  assembled from above in one layer. The bay is taller than the cell; fix it with a foam
  pad or a dab of glue. Parameters: `batt_w/l/t` (cell), `batt_clr` (bay fit), `batt_dx`
  (X nudge), `divider_t`, `rib_h`.

## Closure — snap-fit
**No hardware at all.** A perimeter **bead** (`snap_bead` 0.5 mm, `bead_h` 1.4, chamfered
0.4 top and bottom — click-in/pry-out ramps, and the first printed bead layer isn't a ledge
in mid-air) on the lid tongue clicks into a matching **groove** in the base lip (0.5 taller
/ 0.25 deeper for lead-in, ceiling chamfered so it prints without an overhang), holding the
whole rim down — including the battery-bay half, which a corner-screw
pattern would leave unclamped. The PCB is located by two **Ø1.7 pins** in its real Ø2
mounting holes and pressed onto the posts by the lid's hold-down bosses (blind pin recesses
inside — no holes through the top). Open with a coin or fingernail in the **pry slot**
(`pry_w/d/h`) on the back wall's lower lid edge, over the battery bay.

The case is rarely opened (charging is external via USB-C), so snap wear is not a concern
with PLA; print the lid in PETG if you want extra flex margin. **Tune before the full
print:** `SNAP_TEST=true ./export.sh` also exports a cropped front-left corner pair
(`openrz67-snaptest-*`) — print those and adjust `snap_bead` (click strength) and
`lap_gap` (sliding fit) until the corner snaps shut and pries open with reasonable force.

Finished size with default values: ~**58.6 × 50.0 × 18.1 mm** (X incl. the 2 mm USB-C
overhang and the 3 mm U4 overhang, Y incl. the battery bay behind the board, Z depends
on `pcb_t`).

## Orientation mark — `orient_mark`
A small **raised rib** on the front wall (low Y) near the left corner, split across the
seam: the base carries the lower half, the lid the upper half. When the lid is on the
right way around the two halves line up into **one continuous vertical rib**; a lid put on
180° wrong moves its half to the opposite corner, so the mismatch is obvious at a glance.
It is raised (not a recessed groove) on purpose — a groove here would thin the 1.2 mm lap
wall. Parameters: `orient_mark_x` (board-X of the mark, near the USB side), `orient_mark_w`
(width), `orient_mark_d` (how far it sticks out), `orient_mark_h` (total height across the
seam). Delete the two `orient_mark_rib` lines to remove it.

## Lid text — second colour (`lid_texts`)
**Debossed badge layout** around the LED window: **"OpenRZ67"** (9 mm caps) above it,
**"Trigger"** (7 mm) below, both centred on the light pipe's X, cut `lid_text_depth`
(0.6 mm) into the top face. Per the FDM rules: pockets, not raised letters, and well above
the 4.4 mm legibility minimum for a 0.4 nozzle. Placement is enforced by assertions (each
line must clear the LED recess, the walls and the face edges — an over-long string fails
the export instead of the print).

Colour it in the slicer with a **height range modifier on the lid**: select the lid,
add a height range **0.6–1.4 mm** and assign it the letter-colour filament. The lid prints
**upside down** (the pockets face the bed and come out crisp), so those four layers form
the pocket floors — the letters show in the contrast colour, recessed in the face colour,
with only a thin accent band at the lid's top edge. On a single-filament printer, do a
manual filament change at Z = 0.6 instead (recolours everything above 0.6, so slice the
lid alone).

**Do not save the height range into the project/template**: QIDI Studio (≤ v2.x)
**segfaults on opening** a .3mf that carries `Metadata/layer_config_ranges.xml`
(`ObjectList::add_settings_item` dereferences the not-yet-created model tab during
startup load). Add the range fresh after opening the project instead.

Edit the `lid_texts` constant to change strings/sizes/offsets; `LID_TEXT_SHOW=false`
disables the text (on by default).


## Usage
The parameters are plain Python constants at the top of `openrz67_case.py`. Requires
[uv](https://docs.astral.sh/uv/) — the script carries its own dependency header, so there
is no venv to manage.

**Easiest export** – run the script, which builds all three parts and the slicer project:

```bash
cd case
./export.sh            # base, lid, lightpipe -> stl/  + openrz67-case.3mf
./export.sh out        # custom output dir (skips the .3mf)
```

**Overrides** – `openrz67_case.py` reads these from the environment (the in-file default
applies when unset); anything else is a one-line edit of the constant:

```bash
LID_TEXT_SHOW=true   ./export.sh   # turn the lid text ON (off by default; for the final print)
LID_TEXT="My text"   ./export.sh   # change the lid text string
LID_TEXT_SIZE=4.0    ./export.sh   # cap height (mm)
SNAP_TEST=true       ./export.sh   # also export the corner test pair for snap tuning
PCB_T=1.0            ./export.sh   # PCB thickness (sets the base/lid split height)
LID_TEXT_SHOW=true LID_TEXT="v2" ./export.sh     # combine freely
```

Or run the script directly (same thing minus the .3mf step): `uv run openrz67_case.py`.
For a plain interpreter (IDE run button etc.) there is a local venv:
`.venv/bin/python openrz67_case.py` — recreate it anytime with
`uv venv .venv && uv pip install -p .venv "build123d>=0.11.1"` (it is git-ignored).
For an interactive 3D preview, open the file with an OCP viewer (e.g. `ocp_vscode`) or
just inspect the exported STLs in the slicer. STL output in `case/stl/` is git-ignored.

### Slicer project (.3mf)

After the STLs, `export.sh` rebuilds `openrz67-case.3mf` — a
**Bambu Studio / OrcaSlicer project** with the three parts arranged on the plate, the print
profile, and the **per-part filament assignment** (base + lid on filament 1, light pipe on
filament 4 = clear). It does this by swapping the fresh meshes into a hand-made template
(`bambu-template.3mf`) via `make_3mf.py`, so all slicer settings are preserved — only the
geometry changes. Skip it with `MAKE_3MF=false ./export.sh`, or run it standalone:

```bash
python3 make_3mf.py            # template + stl/ -> openrz67-case.3mf
```

To change the print settings, plate layout, or filament mapping, edit the project once in the
slicer and re-save it over `bambu-template.3mf`; subsequent exports inherit the new setup.
The plate thumbnails inside the .3mf are not regenerated (they show the template's geometry);
the slicer refreshes them when you open or slice the project — purely cosmetic.

## Print orientation
- **Base**: print as-is (floor down). No supports needed.
- **Lid**: print **upside down** (top plate against the bed). That way the bosses/lip
  point upward with no overhang and the LED window/counterbore gets a clean top surface.
- **Light pipe** (`openrz67-lightpipe.stl`): **clear filament**. Print upright (head down
  against the bed) for the fewest layer lines across the light path, or lying down for
  smoother walls – both work for an indicator. For the clearest light: print at a fine
  layer height and consider sanding/dipping the top face.

## Worth adjusting before printing
- `pcb_t` – PCB thickness (default **1.6 mm**, as ordered). Adjust only if your board
  differs; it sets the height of the base/lid split.
- `pcb_overhang_left` – the air gap on the left for the USB-C shell. Measure your own
  connector: distance from the PCB's left edge to the outermost point of the shell.
  Default 2.0.
- `pcb_supports` – extra support-pillar coordinates (without screw) on the base. Default
  is the two empty corners `[[2,20],[46,2]]`; add more if the board flexes.
- `h_ph_plug` – the tallest component (PHR-2 plug + wire bend on `BAT1`/`S3`) sets the
  total height. Lower it if your plugs sit lower.
- `xh_mouth` / `xh_recess` – how far the U4 body reaches past its pin row, and how far
  inside the outer wall face its mouth ends. Together they set `pcb_overhang_right`.
- `snap_bead` / `lap_gap` – snap click strength and sliding fit. Tune with the
  `SNAP_TEST=true` corner pieces before printing the whole box.
- `batt_w/l/t` / `batt_clr` – fit your LiPo in the bay; `batt_dx` nudges it in X if the
  leads want a different exit point.
- `sw_x` / `sw_z` / `sw_wall` – position of the slide switch. The **front wall**
  (`"front"`, low Y) is chosen deliberately: the back wall carries the S3 connector
  (board-X 28.7), the LEDs and the battery-bay divider, so there's no room there for a
  centred switch with 15 mm boss spacing. `sw_x = 22` is practically centred (case centre
  is 23; the bosses at board-X 14.5 and 29.5 sit over low 0402/0603 parts only). `sw_z = 4.8`
  puts the body underside 1.3 mm above the PCB, 0.4 mm over U1 (the body sits partly over it).
  The wire from S3 runs across the board to the switch. Verify against your own components.
- **Switch screw mount**: the switch's flat bracket mounts on the **outside** of the case;
  screws go from outside → through the bracket and wall → thread into two **rectangular
  pillars** that hang from the lid ceiling down to `sw_boss_gap` (1.5 mm) above the PCB. The
  pillars are anchored in the top plate and their front sits at the inner wall plane against
  the (now solid) inner wall, so tightening clamps **bracket → wall → boss** in compression —
  no free-standing cantilever. The `sw_boss_gap` air gap keeps the pillars clear of the
  densely packed front components under their footprint (Q1 SOT-23 ~1.1 mm, C15/C26 0603
  ~0.9 mm). `sw_screw_pitch` = 15.0 (centre spacing, ±7.5), `sw_screw_d` = 2.4
  (M2 clearance), `sw_boss_d/h/pilot` set the pillar cross-section and pilot hole.
  - **Body keepout** (`sw_body_l × sw_body_h × sw_body_w` = **11 × 7 × 8 mm**, + `sw_body_clr`
    0.4/side): the switch body that protrudes inside is wider than the gap between the
    bosses, so a keepout carves the body envelope out of the cavity, relieving the boss
    inner faces over the body's Y/Z extent only — the screw region (±7.5) and the pillar
    above the body stay full. Verify `sw_body_l/h/w` against your switch.
  - **Actuator opening** (`sw_slot_l × sw_slot_h`): **10.65 × 6.3 mm** through the wall,
    centred on `sw_x`/`sw_z`.
  - **Screw**: **M2 self-tapping**, ~**8 mm** long (M2×6 also fine). From outside through the
    bracket (0.4) + wall (1.6 behind the recess), threading `sw_boss_pilot` (1.5) into the
    pillar (up to `sw_boss_h` 5 mm engagement). The head sits on the external bracket, so the
    case has no head counterbore.
  - **Bracket recess** (`sw_plate_recess`, default on): the flat bracket (`sw_plate_w ×
    sw_plate_h × sw_plate_t` = **19.45 × 5.75 × 0.4 mm**) mounts on the **outside**, sitting
    in a pocket `sw_plate_t` deep cut into the **outer** wall so it is **flush** with the
    outside. The inner wall behind it stays solid, which is what the bosses bear against.
    `sw_plate_clr` (0.3) adds fit clearance around the bracket. Verify `sw_plate_w/h/t`
    against your switch; set `sw_plate_recess = false` to drop the pocket.

## USB-C opening
Two layers in the wall (outside in):
- `usb_open_w/h` = **11 × 7 mm**, R2 (`usb_open_r`) – pass-through through the whole wall.
  This outer edge IS the **lip** that stops the cable body/overmold (anything > 11 × 7)
  from coming in; the metal plug itself (~8.34 × 2.56) passes through easily.
- `usb_recess` (**on**) – an **inner recess** `usb_recess_w/h/d` = **13 × 9 × 1.5 mm**,
  R3 (`usb_recess_r`), on the cavity side of the wall. It eats away the last 1.5 mm of
  the wall so the USB-C receptacle's body/shell can poke slightly into the wall and bring
  the connector mouth close to the outer face.

The opening's centre sits ~1.65 mm **above** the base/lid split, so the lower ~1.85 mm of
the 7 mm-tall window falls below the seam. `cut_usb()` therefore runs in **both** `base()`
and `lid()` — otherwise the base side wall would block the lower edge of the hole.

Measure your own charging cable and adjust if needed. Test with a print of just the left
short end first.

## Known / to verify
- Check that your charging cable reaches the port (see "USB-C opening" above).
- Check that the wire bundle from the XH cable fits the `cable_port_*` mouth.
- **Light pipe**: verify the rod lands directly over D3/D4 (adjust `led_pos` if needed)
  and that the bottom clears the LEDs (`led_pipe_gap`). Print in clear filament; glue the
  head into the counterbore for a permanent/sealed fit.
- The USB-C and switch openings are open out of necessity; the LED window is sealed by
  the light pipe.

## Camera plug — `camera_plug.py`

A two-half shell (plate 2 of `openrz67-case.3mf`) around four female jumper-wire ends
(2.54 mm Dupont sleeves) so they go onto the RZ67 RC-outlet as one plug. Port measured
2026-09-06: pocket 13.91 × 3.57 mm, ~6.3 deep (uncertain), Ø0.8 round pins, 2.54 pitch,
row centred. The nose fills the pocket with two side cheeks; a front plate with pin holes
stops the sleeves on pull-off and a rear wall with wire notches stops them on push-on, so
the sleeves are not glued. The body is as tall as the nose (0.4 mm skins over/under the
sleeves), which is what lets each half print flat on its outer face with no bridges or
supports. Debossed triangle on top = 6 V pin (leave unconnected), like the camera's own
mark. `uv run camera_plug.py` (also run by `export.sh`) → `stl/openrz67-camera-plug-{bottom,top}.stl`,
both already print-side down; `make_3mf.py` appends them to the project as plate 2 (`EXTRA_PLATES`). Assemble: sleeves into the bottom half, wires out the back, CA glue along
the walls, top half on. PETG. Tune `nose_fit` (per-side clearance, go negative for press)
after the first print; if your sleeves measure 2.50 rather than 2.54, set `sleeve` — the
skin assert tells you if the stack no longer fits the pocket height. Not print-tested.

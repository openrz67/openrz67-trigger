# Parametric enclosure (build123d)

`openrz67_case.py` is a parametric two-part enclosure for the OpenRZ67 trigger PCB
**rev 2** (the KiCad project in `../pcb/kicad/`), written in
[build123d](https://build123d.readthedocs.io/) (Python). It is built from the board
file and its footprints, not from eyeballed measurements.

> **Stacked layout (2026-09-12):** the LiPo cell lies flat **under the PCB** (foam
> between) in a low rib pocket, the PCB sits on 8 mm posts, and open **pockets** in front of (2 mm) and
> behind (4 mm) the board take fingers and the battery lead. The lid's top edge has a 2 mm 45° chamfer. `U4` (side-entry
> S4B-XH-A, body 5.5 mm past the board edge) and its plug stay **inside**; only the
> heat-shrunk camera cable leaves through a keyhole slot in the right wall. Roomier on
> purpose — the previous stacked attempt was too tight to work in. Replaces the
> battery-beside box (git history before 2026-09-12). First printed 2026-09-14; the snap
> bead and the LED seat were reworked after it (see below).

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
| Rocker switch (KCD11) | snap-in body 13.5×8.5 (= panel cutout, nominal), flange 15×10, 10 deep behind the flange, two 2.8 mm tabs ~5 long at ~7 mm pitch; vendor drawings differ by ~0.5 mm | vendor data — measure your switch |
| FPC antenna | Ebyte TX2400-FPC-2509, 25 × 9 × ~0.2 mm, U.FL/IPEX-1, ~100 mm cable, to `A1` | vendor data — measure your foil |
| LEDs | D3 red (20.5, 18.0), D4 blue (24.2, 20.2) – 0603 SMD, top-emitting; D3 moved next to the BQ25185 charger 2026-09-07, so the 6 × 4.4 light-pipe window is centred between them | `out/openrz67-pos.csv` |

Component **heights** are editable constants (`h_usbc`, `h_ph_plug`, `xh_h`) from the
datasheets / 3D models. `h_ph_plug` (8 mm: a PHR-2 plug in the 6 mm PH header plus the
wire bend on top, on `BAT1` and `S3`) is the tallest thing on rev 2 and sets the lid
height. Check them against your own parts.

The script carries **module-level assertions**: outer dimensions, plus probe checks that
every opening actually breaks through (USB, camera cable slot, LED window, locating-pin
recesses, switch hole and latch pocket) and that the fit-critical keepouts (switch body + tabs + receptacles, USB-C
body, the U4 body + mated plug inside the box, the cell under the PCB) stay open. They run on every export, so a parameter tweak that closes a hole or re-introduces
a known collision fails loudly instead of surfacing in the print.

## Construction
- **Lid top edge**: `lid_top_r` (2 mm) 45° chamfer, applied to the shell before any cut. The
  lid prints upside-down, so this is the bed-side edge — a chamfer prints clean there, a fillet
  would overhang in its first layers. The base's bottom edge stays square. Text asserts keep
  `lid_top_r` + margin clear.
- **Base** (tub): floor, **8 mm posts** (`standoff_h` = cell 6 + foam 1.5 + 0.5 for the
  solder/vias on the bare PCB bottom; was 11 until 2026-09-14 — the BAT1 tails lie *beside*
  the cell in X, not over it, which is asserted) in all four corners (`pcb_supports =
  [[2,20],[46,2]]` plus the two posts at the mounting holes), and two **Ø1.7 locating
  pins** up into the real Ø2 mounting holes. The cell lies on the floor between the posts,
  lengthwise from board-X `batt_x0` (6), inside a **low rib ring** (`batt_rib_t` 1.6 ×
  `batt_rib_h` 2.5, `batt_clr` 0.5 around the cell — like the old battery-beside bay) that
  locates it; foam tape on top holds it down.
  - **Through-hole solder relief** (`th_keepouts`): a small pocket in the top of a
    pillar where a through-hole component's pin tails/solder stick down (the pillar at
    (2,20) sits next to BAT1). The list is `[board_x, board_y, relief_diameter]`;
    `th_keepout_depth` sets how far down (3.5 mm, the PH tail length from the 3D model).
  - **PCB frame / guide fins** (`frame_*`): the pockets leave air beside the board's long
    edges, so **guide fins** reaching from the wall across the pocket hold the PCB in Y: a
    thick fin ending `frame_clr` (0.2 mm) from the board edge, plus a thin lead-in lip
    `frame_proud` (0.6 mm) above the board top. Two per long edge
    (`frame_ribs_front` / `frame_ribs_back`, board-X centres, default `[20, 32]` — mid-edge,
    clear of the snap fingers near the corners and of the lead pocket at the back-left).
    The lid tongue is notched where the fins stand (`frame_notch_clr`).
- **Lid**: telescopes down into the base via a perimeter tongue (lap joint, `lap` 7 mm)
  for alignment. Carries the USB-C opening (left), the camera cable slot (right), the
  LED light-pipe window (top), and the snap-in hole for the KCD11 rocker switch (front).
  - **Camera cable slot** (`cut_cable`): the U4 header body (mouth 5.5 mm past the board
    edge) and the mated XHP-4 plug (`xh_plug_proud` 2.5 past the mouth — an estimate,
    measure yours) stay inside; `xh_slack` (1.5) air to the wall sets
    `pcb_overhang_right` (9.1 mm). The cable leaves through a **keyhole** in the lid's
    right wall: round top of `cable_d` + 2 × `cable_clr` (Ø6) centred at the header's
    mid-height, open straight down through the tongue to the seam, so the heat-shrunk
    bundle **drops in at its natural height** as the lid closes and the lid lifts off
    untethered. No tongue or finger in that band. Wire-management rule from the first
    boxes: exits are open to the seam and at the wire's height — stiff wires take neither
    threading nor a vertical detour.
  - **LED light pipe** (`led_*`, separate part): D3 (red) and D4 (blue) are top-emitting
    SMD LEDs ~8 mm below the lid. A separate **clear light pipe** is inserted from above
    as a top hat: a **tapered** head (funnel seat, ~flush with the top face) + a rod that
    goes down to ~0.8 mm above the LEDs and channels the light into two sharp dots. The
    lid is printed opaque; **only the light pipe is printed in clear filament**. It rests
    in the seat (gravity + optionally a drop of glue to seal). Why a funnel and not a
    stepped counterbore: the lid prints upside-down, and a step is a 1 mm ledge hanging
    over the bed-side opening — the slicer filled it with support and the edge came out
    ragged (first stacked print, 2026-09-14). The funnel wall is 26.6° from vertical, under
    the slicer's 30° support threshold, so nothing is supported and nothing sags. Parameters:
    `led_win_l/w/r` (window size), `led_head_lip/t` (head oversize / height -> taper), `led_pipe_gap`
    (air gap to the LED), `led_pipe_clr` (fit in the hole). `led_pos` are the LED
    positions from pick&place.
  - **Component clearance** (`comp_keepouts`): rectangles `[board_x0, board_y0, board_x1,
    board_y1]` cut out of the lid's hold-down bosses (full height above the PCB) where a
    boss would collide with a component body — e.g. the Ø6 boss at hole (2,2) is cut back
    to a D-shape to clear the USB-C connector's near edge (~board-Y 4.8).
  - **Antenna recess** (`ant_*`): a shallow **25.6 × 9.6 × 0.3 mm** pocket in the lid
    **ceiling** that locates the adhesive FPC antenna (Ebyte TX2400-FPC-2509, 25 × 9).
    It sits in the free ceiling band between the rocker body (front) and the light-pipe
    stem (back), right of the (2,2) hold-down boss — furthest from the cell's metal pouch
    and ~10 mm above the PCB ground plane. `ant_cx_frac` (0.25) slides it along the band;
    0.25 keeps it near the USB end, so the ~100 mm U.FL cable has a short run down to `A1`
    and coils in the air over the board. Two asserts: the recess must fit the free band,
    and `ant_depth` + `lid_text_depth` must leave ≥ 0.8 mm of top plate (this is what caps
    the lid text at 0.9 mm). The lid prints upside-down, so the recess is a flat-bottomed
    pocket in the print's **top** face — no bridging, no support.
- **USB-C asymmetry**: the USB-C shell protrudes ~2 mm past the PCB's left short side.
  `pcb_overhang_left = 2.0` extends the cavity on the left; the PCB is therefore centred
  toward the RIGHT in the cavity (normal `clr = 0.4` against the right wall, `clr +
  overhang = 2.4 mm` against the left). On the right, `pcb_overhang_right` (9.1 mm,
  derived from the U4 reach + plug + slack) makes room for the camera plug. The outer case
  width thus becomes ~**66.3 mm**.
- **The battery** (31 × 20 × 6 LiPo) lies flat **under the PCB**, lengthwise between the
  posts in the rib pocket, `batt_foam` (1.5 mm) under the PCB. Its lead comes out at the
  left end over the low rib (the pockets beside the board give it room), goes back into
  the **4 mm pocket behind the board**, up past the board edge and down
  into BAT1 at board ≈ (3.3, 17) on top; `comp_clr` has 2 mm extra for that loop. Nothing
  is threaded: cell in, board down onto the pins, lead over the edge, lid on. Fix the
  cell with foam tape or a dab of glue. Parameters: `batt_w/l/t`, `batt_x0`, `batt_foam`,
  `batt_clr`, `batt_rib_t/h`, `pocket_front/back`.

## Closure — snap fingers
**No hardware at all**, and the walls do not flex: four **cantilever fingers** cut free in
the lid tongue (two per long wall, `snap_fingers_x`, near the corners) carry a **bead**
(`snap_bead` 0.55, `bead_h` 1.4; a 0.4 click-in chamfer below, only 0.15 above so most of
the bead is a flat retention face) that clicks into a matching **pocket** in the base lip
(0.5 longer each side, `pocket_extra_d` 0.15 deeper, `pocket_extra_h` 0.3 taller; ceiling
edge chamfered `pocket_ch` 0.2). The first stacked print (2026-09-14, bead 0.45 with 45°
ramps on both retention faces) closed but held loosely — hence the bigger bead and the
steeper faces. The small ledges (0.4 on the bead, 0.5 on the pocket ceiling) print as a
single overhanging line without support.
Each finger is `finger_l` (12 mm) long, `finger_t` (1.0 mm) thick — thinned from the
cavity side, with a `finger_slot` (0.8) relief at each end — and the bead sits 1.1 mm
above the finger tip, so the flexing lever is ~6 mm: about 2 % strain at full deflection,
fine for PLA and comfortable in PETG. The rest of the tongue (1.45 mm) and the base lip
(1.6 mm, 0.9 behind the pockets) stay rigid; `wall` is 3.2 for that. The PCB is located by
two **Ø1.85 pins** (light friction fit, coned lead-in) in its real Ø2 mounting holes and pressed onto the posts by the lid's
hold-down bosses (blind pin recesses inside — no holes through the top). Open with a coin
or fingernail in the **pry slot** (`pry_w/d/h`) on the back wall's lower lid edge; the back
fingers release first, then the front.

Why fingers: the earlier continuous bead on a 2.4 mm wall left 0.45 mm of lip behind the
groove, which loosened after a few openings. Screws were ruled out before that (threads in
plastic stripped; heat-set inserts made assembly slow). **Tune before the full print:**
`SNAP_TEST=true ./export.sh` also exports a cropped front-left corner pair
(`openrz67-snaptest-*`) with one finger and one locating pin — print those and adjust
`snap_bead` (click strength), `finger_t` (stiffness) and `lap_gap` (sliding fit) until the
corner snaps shut and pries open with reasonable force.

Finished size with default values: ~**66.3 × 36.0 × 25.5 mm** (X incl. the 2 mm USB-C
overhang and the 9.1 mm U4 + plug overhang, Y incl. the two pockets, Z = floor 2 + posts
8 + PCB + 11.9 clearance + top 2; depends on `pcb_t`). The clearance is set by the rocker
switch (body 8.5 + 1.6 over the PCB + latch room), not by the PH plugs any more (10).

## Orientation mark — `orient_mark`
A small **raised rib** on the front wall (low Y) near the left corner, split across the
seam: the base carries the lower half, the lid the upper half. When the lid is on the
right way around the two halves line up into **one continuous vertical rib**; a lid put on
180° wrong moves its half to the opposite corner, so the mismatch is obvious at a glance.
It is raised (not a recessed groove) on purpose — a groove here would thin the 1.6 mm lap
wall. Parameters: `orient_mark_x` (board-X of the mark, near the USB side), `orient_mark_w`
(width), `orient_mark_d` (how far it sticks out), `orient_mark_h` (total height across the
seam). Delete the two `orient_mark_rib` lines to remove it.

## Lid text — second colour (`lid_texts`)
**Debossed nameplate lockup** in front of the LED window (the LEDs sit near the back edge):
**"OpenRZ67"** (9.5 mm) with a small tracked all-caps **"TRIGGER"** (5 mm, +1.0 mm letter
spacing) under it, in **Futura Bold** (macOS system font; OCCT warns and falls back to
Arial if it is missing). Both lines are centred on the lid's X and the block is centred
between the LED seat and the front edge. A thin debossed **rail** (`lid_rail_*`, 0.9 wide,
6 mm in from the side walls) runs across the LED row and breaks 1.5 mm around the
light-pipe seat — the off-centre LED then reads as an indicator sitting on a line instead
of a hole that missed the middle (the LED position is fixed by the PCB). All pockets are
`lid_text_depth` (0.8 mm, 4 layers) deep, and an **inlay** solid (`lid_text`, exported as
`openrz67-lid-text.stl`) fills them exactly — it is the pocket volume clipped by the lid,
so it inherits the top-edge chamfer and cannot fight the lid for the same space (asserted). Restyled 2026-09-14 — the old Arial "OpenRZ67" / "Trigger"
pair had uneven weights, a wide gap and sat near the edge; DIN Alternate was tried and
dropped for Futura.
Per the FDM rules: pockets, not raised letters. Assertions enforce placement (each line
clears the LED seat, the walls and the face edges) and **printability**: every glyph
stroke is at least `lid_text_min_stroke` (0.6 mm), measured by shrinking each glyph
outline — a narrower pocket smears. Tracking keeps the font's own advances and adds a
fixed gap per glyph (all-caps only: one face per letter).

Colour it by **part, not by slicer paint**: `make_3mf.py` adds the inlay to the lid object
as a second part on **filament 2** (`SUB_PARTS`), the same mechanism the light pipe already
uses for its clear filament. Open `openrz67-case.3mf`, set filament 2 to the letter colour,
print — nothing to select per slice. The colour lives on the part, so every re-export keeps it.

Why not the two older routes:

- **Slicer colour painting** stores the colour per mesh triangle. `make_3mf.py` replaces the
  mesh on every export, so the painting is wiped and has to be redone each time.
- **Height range modifier** cannot be saved: QIDI Studio (≤ v2.x) **segfaults on opening** a
  .3mf that carries `Metadata/layer_config_ranges.xml` (`ObjectList::add_settings_item`
  dereferences the not-yet-created model tab during startup load).

The inlay also fixes the print quality. The lid prints **upside down**, so an empty pocket's
floor is a bridge over open air — at 0.6 mm deep it sagged and the letters read fuzzy
(2026-09-16). As a part, the letters print **first, flat against the bed**, and come out
smooth. On a single-filament printer, delete the inlay part and do a manual filament change
at Z = 0.8 instead (recolours everything above 0.8, so slice the lid alone).

Depth was 0.6 (3 layers) until 2026-09-17: the body colour ghosted through and the letters
read weak. 0.8 (4 layers) is stronger; **0.9 is the cap** at `lid_top_t` 2.0, from the
antenna-recess assert. The inlay never matches the crispness of a true empty recess (the
colour boundary sits in the first bed layer, which spreads), but a real recess is not
available: the lid prints upside down, so the pocket floor bridges. Printing text-up would
put the whole lid interior in overhang. Soluble support (HIPS under ABS, dissolved in
d-limonene) would make a real recess work — parked, not tried.

Edit `lid_texts` (text, size, tracking), `lid_font`, `lid_text_gap` and `lid_rail_*` to restyle; `LID_TEXT_SHOW=false`
disables the text (on by default).


## Usage
The parameters are plain Python constants at the top of `openrz67_case.py`. Requires
[uv](https://docs.astral.sh/uv/) — the script carries its own dependency header, so there
is no venv to manage.

**Easiest export** – run the script, which builds the case parts and the camera plug
and the slicer project:

```bash
cd case
./export.sh            # base, lid, lightpipe, camera plug -> stl/  + openrz67-case.3mf
./export.sh out        # custom output dir (skips the .3mf)
uv run camera_plug.py  # just the plug; also rebuilds openrz67-case.3mf from the STLs in stl/
```

Slice from `openrz67-case.3mf` (plate 1 case, plate 2 camera plug). Every script that writes
to `stl/` rebuilds it, so the 3mf is never older than the STLs.

**Overrides** – `openrz67_case.py` reads these from the environment (the in-file default
applies when unset); anything else is a one-line edit of the constant:

```bash
LID_TEXT_SHOW=true   ./export.sh   # lid text (on by default); LID_TEXT_SHOW=false hides it
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
  point upward with no overhang and the LED funnel is widest at the bed (no ledge, no
  support). Turn **elephant-foot compensation** on (~0.15) so the first-layer squish does
  not close in on the funnel rim; keep the support threshold angle at 30° or lower.
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
- `xh_plug_proud` / `xh_slack` – how far the mated XHP-4 plug sticks past the U4 mouth
  (2.5 is an estimate — measure) and the air to the wall. Together they set
  `pcb_overhang_right`. `cable_d` – the heat-shrunk bundle's diameter (5.0) sets the slot.
- `snap_bead` / `finger_t` / `lap_gap` – snap click strength, finger stiffness and sliding
  fit. Tune with the `SNAP_TEST=true` corner pieces before printing the whole box.
- `batt_w/l/t` / `batt_x0` / `batt_foam` / `batt_clr` / `batt_rib_t/h` – your cell, where it
  lies under the board and the rib pocket around it; `standoff_h` must stay ≥ cell + foam
  (asserted), and the THT tails must stay beside the cell in X (asserted — otherwise add
  `th_keepout_depth`). `pocket_front/back` – hand and lead room beside the board.
- `ant_l/w/clr/depth` / `ant_cx_frac` – the FPC antenna's size, the air around it, the
  recess depth and where it sits along the ceiling band. Defaults are the Ebyte
  TX2400-FPC-2509 (25 × 9). A different foil changes `ant_l/w`; the fit assert tells you
  if it no longer fits the band. Antenna optional — BLE works without it, with much less range.
- `sx` – position of the rocker switch (KCD11, `kcd_*`). The **front wall** (low Y) is
  chosen deliberately: the back wall carries the S3 connector (board-X 28.7), the LEDs and
  the battery-lead pocket. Centred on the lid (`sx = outer_w / 2`, board-X ≈ 27.5); the body
  ends at the first `J1` pad and its tabs run over that row, so `J1` cannot take a pin header.
  `kcd_gap` = 1.6 puts the body underside 1.6 mm above the PCB (U1 0.9, X2 and 0603s beneath)
  and leaves a 1.6 mm wall strip between the hole and the seam.
- **Snap-in mount** (replaced the SS12F15 slide switch + M2 screw pillars 2026-09-14): the
  hole is `kcd_body_l/h` + 2 × `kcd_hole_clr` (0.3) through the wall; the flange sits proud on
  the outside. The latches on the body's long sides grip a panel of `kcd_panel_t` (2.0), so
  the wall is pocketed from the **inside** down to that thickness, `kcd_latch_clr` (1.2) past
  the hole on every side — the pocket top is the lid ceiling, which is what raises the lid.
  Asserted: pocket clear of the tongue and the ceiling, flange clear of the seam and the top
  chamfer.
- **Wiring**: two 2.8 mm receptacles on the tabs, 4–6 cm of 26 AWG to the PH plug in S3.
  Use **flag (90°) receptacles** or solder to the tab with the wire leaving sideways:
  `kcd_depth + kcd_tab_l + kcd_conn_l` is asserted to end in front of the light pipe and the
  S3 plug (~21.7 / 23.3 mm from the outer face), and a straight insulated FDFN 1.25-110 is
  ~12 mm past the tab tip — it does not fit. PH wire (26–28 AWG) is thin for a 2.8 mm crimp:
  fold the end double.
- **Measure before printing**: body L × H behind the flange, flange L × H, depth flange →
  body rear, tab length and pitch, and the panel thickness the latches accept.

## USB-C opening
Three layers in the wall (outside in):
- **Plug pocket** `usb_pocket_w/h/r/d` = **14 × 9.5 mm**, R3, **1.2 deep**, with a 45° bevel
  of `usb_pocket_ch` (0.6) on its outer edge. The cable's overmold sinks into it: the port
  is protected, the plug is guided in, and the overmold ends 1.2 mm closer to the receptacle
  mouth (which sits ~0.4 mm inside the wall's inner face). Fits overmolds up to 13 × 8.5.
  The user's old Fusion case had one (added here 2026-09-14).
- `usb_open_w/h` = **11 × 7 mm**, R2 (`usb_open_r`) – the pass-through. Its edge is the
  **lip** (1.0 mm thick between pocket and recess, asserted ≥ 0.8) that stops the overmold;
  the metal plug (~8.34 × 2.56) passes easily.
- **Inner recess** `usb_recess_w/h/d` = **13 × 9 × 1.0 mm**, R3 (`usb_recess_r`), on the
  cavity side: slack for the receptacle shell if the board sits further left than measured.

The opening's centre sits ~1.65 mm **above** the base/lid split, so the lower ~1.85 mm of
the 7 mm-tall window falls below the seam. `cut_usb()` therefore runs in **both** `base()`
and `lid()` — otherwise the base side wall would block the lower edge of the hole.

Measure your own charging cable and adjust if needed. Test with a print of just the left
short end first.

## Known / to verify
- Check that your charging cable reaches the port (see "USB-C opening" above).
- Measure how far the mated XHP-4 plug sticks past the U4 mouth and set `xh_plug_proud`;
  measure the heat-shrunk cable and set `cable_d`.
- Snap fingers are new: print the `SNAP_TEST` corner first.
- **Light pipe**: verify the rod lands directly over D3/D4 (adjust `led_pos` if needed)
  and that the bottom clears the LEDs (`led_pipe_gap`, 0.8). Print in clear filament; glue the
  head into the funnel seat for a permanent/sealed fit.
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
both already print-side down; `make_3mf.py` appends them to the project as plate 2 (`EXTRA_PLATES`). Assemble: sleeves into the bottom half, wires out the back, press the top half
on: four Ø1.6 pegs (`peg_*`) in its 3.2 mm side walls press into Ø1.5 holes in the bottom half,
no glue (a snap hook is not printable at 1.8 mm half height; loosen `peg_press` if they
split the wall). PETG. Tune `nose_fit` (per-side clearance, go negative for press)
after the first print; if your sleeves measure 2.50 rather than 2.54, set `sleeve` — the
skin assert tells you if the stack no longer fits the pocket height. Printed three times
(2026-09-08..10): Ø1.5 peg holes were a no-go, Ø1.7 very tight, and the pegs sheared off —
hence the rib + groove per side and the 1 mm taller body behind the nose. Untested since.

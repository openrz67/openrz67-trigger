# openrz67 PCB — KiCad project

KiCad 10 project for the OpenRZ67 trigger board: 48 × 22 mm, 2 layers, ESP32-C3, two
TLP172AM PhotoMOS relays, BQ25185 charger + TPS63031 buck-boost. This is the source.
Each fabricated revision's upload package is frozen in `../archive/`, and the EasyEDA Pro
project it was ported from in `../archive/easyeda/`.

| File | What |
|---|---|
| `openrz67.kicad_pro/.kicad_sch/.kicad_pcb` | project, schematic (1 sheet), board |
| `openrz67.kicad_sym`, `openrz67.pretty/` | symbols and footprints as imported from EasyEDA/LCSC (project-local libs) |
| `tools/regen.sh` | rebuilds everything in `out/`; run it after any change to the board or schematic |
| `tools/post_import.py` | design rules, net classes, zone settings, layer names. **Authoritative**: it overwrites `openrz67.kicad_pro`, so rule changes made in Board Setup are reverted on the next run. Edit the values in the script. Close KiCad first. Idempotent. |
| `tools/fetch_3d.sh` | downloads STEP+WRL models for every LCSC part into `openrz67.3dshapes/` |
| `tools/export_step.sh` | board STEP to `out/openrz67.step` (gitignored, ~20 MB); fetches missing part STEPs first |
| `openrz67.3dshapes/` | 3D models; `.wrl` committed (render), `.step` gitignored |
| `out/` | generated: Gerber+drill zip, position file, BOM (with LCSC numbers), schematic PDF, top/bottom renders, ERC/DRC reports |
| `notes/` | design history, reviews and research; see [Revisions](#revisions) |

## Regenerate outputs

Everything in `out/` is generated. Rebuild all of it with one command, so the committed
outputs and the check reports always describe the committed sources:

```sh
tools/regen.sh
```

It runs `post_import.py`, exports Gerbers, drill files and their maps, zips them, writes the
position file, the BOM, the schematic PDF and the two board renders, then runs DRC with
schematic parity and ERC. It exits non-zero on errors; warnings are printed and accepted
(see below). Close KiCad first: `post_import.py` rewrites the board and the project file.

Override the tool paths if KiCad is not in the macOS default location:

```sh
KICAD_CLI=/usr/bin/kicad-cli KICAD_PY=/usr/bin/python3 tools/regen.sh
```

## Design rules

Clearance 0.127 mm, min track 0.127, default track 0.16, via 0.45/0.25 (min 0.40/0.20),
hole-to-track 0.175, hole-to-hole 0.30, solder-mask expansion 0.051, thermal spoke 0.254 /
gap 0.152. Net classes: `gnd` (GND, 0.13 track), `3v` (VCC, VDDA, 0.20), `5v` (VBUS, BAT+,
BAT_CELL, VSYS, SW_SYS, SW1, SW2: 0.254 track, 0.5/0.3 via). Copper-to-edge 0.30 mm.
Silkscreen minimums are JLCPCB's: 1.0 mm text height, 0.15 mm line width. The only custom
rule is in `openrz67.kicad_dru` (hole clearance around USB1's two locating-peg holes).

## Accepted warnings

ERC and DRC both have **0 errors**. The warnings below are known and left in the reports
rather than silenced, so a genuinely new one stands out. No exclusions are configured.

| Check | Count | What |
|---|---|---|
| ERC `endpoint_off_grid` | 15 | The redrawn charger section sits on whole millimetres, not the 1.27 mm grid. Cosmetic; connectivity verified by netlist. |
| `courtyards_overlap` | 15 | Neighbours closer than 0.1 mm (USB1 corner, the U2/L3 power corner, R23 at U1, C32 at R24/R25, Q3 at BAT1/L3, C24 at L3/U2). Pad-to-pad ≥ 0.16 mm everywhere. |
| `silk_over_copper` | 4 | L3's and U2's outlines cross C24's mask openings by 0.05 mm; the fab clips silk there. |
| `silk_overlap` | 1 | U2's pin-1 dot touches L3's outline (0.02 mm). |
| `text_height`, `text_thickness` | 2 | The `BOOT EN` label is 0.5 mm / 0.10 mm, under JLCPCB's minimum. There is no room to enlarge it without moving parts. |

## Mechanical

Outline 48 × 22 mm, R2 corners, mounting holes at (2, 20) and (46, 2). All components are
on top. Under-board clearance the enclosure has to provide, from the datasheets:

| What | Height below the board |
|---|---|
| BAT1, S3 and U4 through-hole tails | 3.4 mm unclipped |
| USB1 shell posts | ~1 mm |

The cell can only sit against the board if those tails are clipped flush.

## Revisions

| Rev | Status | Package |
|---|---|---|
| 1 | fabricated, working; LGS5500 charger replaced in rev 2 | `../archive/2025-09-23-rev1/` |
| 2 | fabricated 2026-09-07, **working** (the boards in use) | `../archive/2026-09-07-rev2/` |
| 3 | **source**, not yet fabricated | this directory |

Rev 3 over rev 2: routing fixes from the 2026-09-08 review, R23 pull-up on GPIO8, battery
voltage sense on GPIO3 (S2 drive moved to GPIO6, J1 shrunk to 1×3), Q3 reverse-battery
P-FET, C24 moved to the buck-boost output, paste windows on the exposed pads, RF line
0.8 mm. The full change-by-change record, with coordinates and the reasoning behind every
part choice, is in [`notes/revisions.md`](notes/revisions.md); the reviews that drove it are
the other files in `notes/`.

Still open, not blocking: one-via ground islands, 0.16 mm power necks at the U2/U3 pads,
the U3 mask dam, and a 1 µF on VDD_SPI (no room on top).

## Ordering

Fab notes: 2 layers, 1.6 mm FR-4, 1 oz copper, no impedance control, smallest via
0.45/0.25 mm (pick the 0.25 mm minimum-hole option if the form asks). No bottom-side
assembly. BAT1, S3 and U4 are through-hole: confirm the assembler's through-hole service or
hand-solder them. J1 is DNP and absent from the BOM and position file.

`tools/regen.sh` writes `out/openrz67-gerber.zip`, which is what you upload; it is tracked so
the fab-ready file is always in the repo. `out/gerber/` is tracked unpacked so copper diffs
in git. When a revision is ordered, copy the zip, BOM and position file into
`../archive/<date>-rev<n>/`.

The BOM and position file are written in JLCPCB's column layout, so they upload without
mapping. Gerbers, drill and position all use the aux origin at the board's top-left corner.
`ROT_FIX` in `regen.sh` adds +90° for U1 (QFN-32) and U5/U6 (SO-4) because JLCPCB's library
orientation for those packages is 90° off the KiCad footprint.

**Before confirming the order:** U1, U5 and U6 must look like `out/openrz67-top.png` in the
preview; check pin 1 of U2, U3, U5, U6, Q3 and BAT1 against the same render; then check the
DFM analysis in Order History (U1, U5, U6, X1, D3, D4).

# openrz67 PCB — KiCad project

KiCad 10 project for the OpenRZ67 trigger board (48 × 22 mm, 2 layers, ESP32-C3,
two TLP172AM PhotoMOS relays, LGS5500 charger/boost). This is now the **source**; the EasyEDA Pro
project it was ported from is archived in `../archive/easyeda/` (v2 `.epro` and v3 `.epro2`);
the fabricated 2025-09-23 revision (Gerber, BOM, PnP, STEP) is in `../archive/2025-09-23-rev1/`.

| File | What |
|---|---|
| `openrz67.kicad_pro/.kicad_sch/.kicad_pcb` | project, schematic (1 sheet), board |
| `openrz67.kicad_sym`, `openrz67.pretty/` | symbols and footprints as imported from EasyEDA/LCSC (project-local libs) |
| `tools/regen.sh` | rebuilds everything in `out/` in one go; run it after any change to the board or schematic |
| `tools/post_import.py` | design rules, net classes, zone settings, layer names. **Authoritative**: it overwrites `openrz67.kicad_pro`, so rule changes made in Board Setup are reverted on the next run. Edit the values in the script. Rewrites the board in place, so close KiCad first. Idempotent. |
| `tools/fetch_3d.sh` | downloads STEP+WRL models for every LCSC part into `openrz67.3dshapes/` (uses `easyeda2kicad`, `uvx`, `pipx` or a local venv, whichever exists) |
| `tools/export_step.sh` | board STEP to `out/openrz67.step` (gitignored, ~20 MB); fetches missing part STEPs first |
| `openrz67.3dshapes/` | 3D models; `.wrl` committed (render), `.step` gitignored (fetch when you need a board STEP) |
| `out/` | generated: Gerber+drill zip, position file, BOM (with LCSC numbers), schematic PDF, top/bottom renders, ERC/DRC reports |

## Regenerate outputs

Everything in `out/` is generated. Rebuild all of it with one command, so the
committed outputs and the check reports always describe the committed sources:

```sh
tools/regen.sh
```

It runs `post_import.py`, exports Gerbers, drill files and their maps, zips them,
writes the position file, the BOM, the schematic PDF and the two board renders,
then runs DRC with schematic parity and ERC. It exits non-zero on errors;
warnings are printed and accepted (see below). Close KiCad first: `post_import.py`
rewrites the board and the project file in place.

Override the tool paths if KiCad is not in the macOS default location:

```sh
KICAD_CLI=/usr/bin/kicad-cli KICAD_PY=/usr/bin/python3 tools/regen.sh
```

## Design rules (from the EasyEDA project)

Clearance 0.127 mm (EasyEDA pour-to-track minimum; track-to-track was 0.152), min track
0.127, default track 0.16, via 0.45/0.20 (min 0.40/0.20), hole-to-track 0.175,
hole-to-hole 0.30, solder-mask expansion 0.051, thermal spoke 0.254 / gap 0.152.
Net classes: `gnd` (GND, 0.13 track), `3v` (VCC, 0.20), `5v` (+5V, 0.254 track, 0.5/0.3 via).
Copper-to-edge clearance is 0.30 mm (JLCPCB recommendation; the original pours ran to
the outline). Silkscreen minimums are JLCPCB's: 1.0 mm text height, 0.15 mm line width.

## Accepted warnings

ERC is clean: **0 errors, 0 warnings**. DRC has no errors; the warnings below are known,
understood and left in the reports rather than silenced, so a genuinely new one stands
out. No DRC or ERC exclusions are configured; the only custom rules are in `openrz67.kicad_dru`
(hole clearance around USB1's two locating-peg holes, see the port notes).

| Check | Count | What |
|---|---|---|
| `courtyards_overlap` | 5 | Neighbours closer than 0.1 mm on the fabricated rev-1 layout: C21/USB1, L3 against C20/R9/R12, H1/USB1. |
| `starved_thermal` | 2 | USB1 pads 1/12 get one GND spoke instead of two: the 0.7 mm locating-peg holes next to them take the second one. Same geometry as the fabricated rev 1. |
| `text_height`, `text_thickness` | 2 | The `BOOT EN` label on F.SilkS is 0.5 mm / 0.10 mm, under JLCPCB's 1.0 mm / 0.15 mm. Enlarged in place it runs over the R18 pads and the S3 body, where the fab clips silkscreen against solder mask. Splitting it into separate `BOOT` and `EN` labels does not help: the free band above the S1 pads is 0.85 mm and the one below the switches is 0.7 mm, both under the 1.0 mm the text needs. Fixing it means moving parts. Every other silkscreen text is at or above 1.067 mm. |

## Rev 2 layout changes (2026-09-03)

Outline unchanged from rev 1: **48 × 22 mm**, 2 mm corner radius, mounting holes at
(2, 20) and (46, 2). Edges are named here by their landmark, because the enclosure in
`../../case/` measures Y from the opposite side: the **USB-C end** is x = 0, the
**camera end** is x = 48, the **S3 edge** is y = 0, and the **switch edge** is y = 22.

- **U4** camera connector: side-entry S4B-XH-A (LCSC C157925) at (44.3, 11.0), opening
  out of the camera end.
- **BAT1** battery connector: vertical through-hole **B2B-PH-K-S(LF)(SN)** (LCSC C131337)
  on the **top** side, restored on 2026-09-05 from the layout before `d7d51ae`.
  Centre (3.275, 4.8105), rotation 90°. Pin 1 = BAT+, pin 2 = GND.
  The original 0.635 mm top-side BAT+ connection and five GND stitching vias are restored;
  the bottom-side BAT+ branch and its transfer via are removed. `BAT+` / `BAT-` labels
  on the bottom identify the through-hole solder pads. All components are now on top.
  The battery cable must reach around the board if the cell remains underneath.
- **Shutter outputs are PhotoMOS, not relays (2026-09-04).** K1/K2 (G6K-2F-Y), their DTC114E
  drivers Q1/Q2, flyback diodes D1/D2 and coil decoupling C27/C28 are gone. Each channel is one
  **TLP172AM** (Toshiba, LCSC C2152276, 4-pin SO6): the ESP32 GPIO drives the LED through a
  **220 Ω** 0402 (R21/R22, C25091), about 9 mA nominal. At 3.3 V, VOH = 0.8 × VDD,
  VF = 1.4 V and +1% resistance give 5.6 mA at 25 °C, within the datasheet's 5 to 25 mA
  recommendation. The MOSFET output closes S1/S2 to camera ground.
  TLP172AM replaced TLP172GM on 2026-09-05: maximum on-resistance is 2 Ω at 25 °C / IF = 5 mA,
  versus 50 Ω continuous for GM. AM's output rating is 60 V / 500 mA; package and pin functions
  are unchanged. The imported pad numbering 1/2/3/4 maps to Toshiba pins 1/3/4/6.
  Firmware activates S1, waits 10 ms, then activates S2. Camera input limits remain unverified;
  test the assembled prototype before ordering a production batch. See [research notes](notes/rz67-remote-inputs.md)
  and the [Toshiba datasheet](https://toshiba.semicon-storage.com/info/docget.jsp?did=36714&prodName=TLP172AM).
  U5 = S1 (net `S1_DRV`, **GPIO4**, U1 pin 9), U6 = S2 (net `S2_DRV`, GPIO3, U1 pin 8). Rev 1
  drove S1 from GPIO21, which is U0TXD: the ROM boot log leaves it high until `setup()` runs,
  so S1 was closed during every boot. Harmless alone, since the camera needs S1 and S2 together,
  but GPIO4 is a plain input at reset and GPIO21 is now free for serial logging. Isolation is kept: camera ground `AGND` still touches only U4 pin 2 and the two
  output pins, and the AGND pours (both layers) were pulled in from x = 32.1 to x = 34.6 so the
  LED side of each part sits in the GND domain. Eight parts became four, the tallest top-side part
  went from 5.2 mm (relay) to 2.2 mm, and the coil current (about 67 mA while an exposure is
  held) is gone. Footprint `SMD-4_L4.6-W3.7-P2.54-LS7.0-BR` and the 3D model came from
  `easyeda2kicad` for C261926; the unused relay/SOT-346/SOD-523 footprints, models and symbols
  were removed from the project libraries. R4/R5 (USB 22 Ω) are UNI-ROYAL 0402WGF220JTCE
  (C25092, JLCPCB Basic) since JLCPCB had 2 of the Yageo part in stock.
- **C5** moved to the analog supply: the 100 nF that sat on VCC next to the ferrite bead
  L2 now sits on the far side of it, on the new **VDDA** net feeding U1 pins 31/32 (radio and
  ADC supply). Before, nothing decoupled that net; the bead alone was just series impedance.
  VCC reaches L2 pin 1 through a new via 0.55 mm below the pad and a short F.Cu stub. (Until
  2026-09-07 the via sat on the pad's edge with its hole 0.083 mm inside the pad copper — a
  paste-wicking risk DRC cannot see because both are VCC; the pre-fab review caught it.)
  Same part, same position, no BOM change. B.Cu ground under U1 stays connected.
- **R11 100 kΩ → 10 kΩ (2026-09-07).** R11 sets the LGS5500 charge current (ISET pin). The
  datasheet table reads ≤14 k → 400 mA, 20 k → 600, 27 k → 800, ≥36 k or open → 1000 mA, and
  the value is latched at power-up, so rev 1 charged the 250 mAh cell at 1 A (4C). 10 kΩ is the
  datasheet's reference value: 400 mA. Note the JEITA thermistor R16 sits on the PCB, not in
  the pack, so it reads board temperature.
- **Resistor sourcing (2026-09-07).** Three lines had 19–40 pieces in JLCPCB stock: the 10 kΩ
  group R6/R7/R8/R13/R14/R17/R20 (+R11) → UNI-ROYAL 0402WGF1002TCE C25744 (Basic), R12 1 kΩ →
  0603WAF1001T5E C21190 (Basic, ±1 % instead of ±5 %), R18 3 kΩ → FOJAN FRC0402F3001TS
  C2909355. Library symbols are named after the MPN, so the three symbols were renamed and the
  100 kΩ one removed. Re-check stock at JLCPCB right before ordering.
- **U4 pads** are 1.6 mm on the unchanged 1.0 mm drill (rev 1: 1.7 mm) because the S4B-XH-A
  footprint from LCSC draws them so — annular ring 0.30 mm, above JLCPCB's 0.20 mm minimum.
- The S1_DRV via next to U1 pin 9 moved 0.15 mm east (mask dam to the pad was 0.067 mm), and
  `VDDA` joined the `3v` net class so its stub is 0.20 mm like the VCC copper it replaced.
- **J1 — 1×4 GPIO header, not populated (branch `gpio-header`, 2026-09-07).** Through-hole
  pads along the bottom edge, x = 34.4–42.0 mm, y = 20.6 mm (0.55 mm copper to edge), 2.54 mm
  pitch, for a benchtop header or wires soldered straight into the holes. Pin 1 (square) =
  **3V3**, 2 = **GND**, 3 = **GPIO21** (U0TXD, so it doubles as a UART TX for logging with a
  USB-UART dongle), 4 = **GPIO6**. Silkscreen labels `3V3 GND TX IO6` sit above the pads in
  two staggered rows (1.0 mm text), below the U4 housing so they stay readable with the
  connector fitted; the footprint's own silk outline was removed to make room. The symbol is marked DNP, so `--exclude-dnp` keeps it out of the BOM and
  the position file and JLCPCB never sees it; the pads are just copper and holes on the
  bare board. Why only two GPIOs: GPIO21 sits on the QFN's left column and escapes freely,
  but every other free pin (GPIO5/6/7/8/10) is on the right column, where the single gap
  between the VCC, CHIP_EN and S2_DRV tracks fits exactly one more escape — the same limit
  the 2026-09-03 header attempt hit. GPIO6 took it. A third would need the VCC spine on
  B.Cu (x ≈ 31) and the S1/S2 drive diagonals moved. The header sits below the AGND island
  (y > 17.7) in the GND domain, so camera isolation is untouched. Three GND stitching vias that
  collided with the pads were removed, one was added at (32.8, 17.6) to re-connect the F.Cu
  ground strip the tracks cut off (the two new tracks also leave a few via-connected F.Cu
  pieces along the bottom edge), and the tracks were routed with a scratch grid router
  (0.16 mm, DRC-clean at the board's 0.127 mm rule). Cost: GPIO6 has to loop north of U1's
  right column on B.Cu before it can head south, which separates a ~57 mm² piece of the B.Cu
  ground east of U1 (under R21/R22 and LDO1) from the main flood; it stays connected through
  the stitching vias there, and the flood under U1 itself is intact. The case has no opening
  for the header.
- **Under-board clearance** the enclosure has to provide, from the datasheets:

  | What | Height below the board |
  |---|---|
  | BAT1 through-hole tails, B2B-PH-K-S | 3.4 mm unclipped |
  | S3 through-hole tails, B2B-PH-K-S | 3.4 mm unclipped |
  | U4 through-hole tails, S4B-XH-A | 3.4 mm unclipped |
  | USB1 shell posts | ~1 mm |

  The cell can only sit against the board if those tails are **clipped flush**. Budget
  3.4 mm otherwise. A foam pad between cell and board is still wanted, but 1.5 mm of it
  only fits after clipping.

**Removed again:** an earlier attempt widened the board to 25 mm for an unpopulated 1×3
expansion header (GPIO4 / 3V3 / GND) along the switch edge. It was reverted. Reaching the
new edge strip forced the GPIO4 return path across the bottom pour, which split the B.Cu
ground under U1 and LDO1 into two islands and displaced three stitching vias next to the
antenna trace. One GPIO, on a header that was not going to be populated, did not pay for
that. There is no room on this outline for a through-hole header: a hole needs both layers
clear at once, and only two isolated spots on the whole board qualify. Bottom-side solder
pads do fit, but the cell now occupies the bottom. Revisit it together with the enclosure.

## Ordering

`out/gerber/` is tracked unpacked, so a revision's copper is diffable in git.
`tools/regen.sh` also writes `out/openrz67-gerber.zip`, which is what you upload;
it is gitignored because it is one command away and would otherwise churn the
history as a binary blob on every regen. When a revision is actually ordered, copy
the zip, BOM and position file into `../archive/<date>-rev<n>/` as the record of
what was fabricated.

The BOM is written with JLCPCB's column names (`Comment, Designator, Footprint, LCSC Part #`,
then Manufacturer, MPN, Qty) and the footprint column without KiCad's library prefix, so it
uploads without column mapping. The position file is rewritten by `regen.sh` into JLCPCB's
CPL layout (`Designator, Mid X, Mid Y, Layer, Rotation`, mm suffix, rotations 0–359 as in the
rev-1 file); their parser rejects KiCad's native header with "Failed processing the CPL
file". Gerbers, drill files and the position file all use the drill/aux origin at the
board's top-left corner (since 2026-09-07 — before that the gerbers were in KiCad's absolute
sheet frame while the CPL was origin-relative, which JLCPCB aligned silently). That is the
rev-1 frame, so `out/gerber/*.drl` diff directly against `../archive/2025-09-23-rev1/`.
Rotations for the top-side parts are unchanged since that order. BAT1 is back on top with its original through-hole
footprint and rotation. Check BAT1 pin 1 in the fab's assembly preview before confirming.
No bottom-side component assembly is needed. BAT1, S3 and U4 are through-hole parts;
confirm the assembler's through-hole service or hand-solder them after SMD assembly. J1
(the GPIO header) is DNP and absent from both files; nothing to select for it.

## Port notes (2026-09-03)

- Import path: EasyEDA Pro **v2** `.epro` → KiCad "Import Non-KiCad Project". The v3
  `.epro2` export loads as an empty board in KiCad 10.0.6.
- Removed the "JeefunPCB" A3 sheet-frame symbol that came with the EasyEDA template
  and replaced it with a KiCad title block. Annotated the 62 power flags (`#PWR001…`),
  deleted two floating GND flags, added a no-connect on U4 pin 1.
- EasyEDA local labels became global labels so net names match the board (`BAT+`, `D7`, and the
  Wemos-style `D1`/`D6`, renamed `S2_DRV`/`S1_DRV` on 2026-09-04); EasyEDA auto-nets (`$1N…`) were renamed to KiCad's `Net-(…)` names.
  Connectivity was verified pad-for-pad against the schematic netlist before renaming.
- USB-C shell pads 13/14 are GND in the schematic; the EasyEDA board had them net-less.
  They are GND now (they sit in the GND pour).
- Schematic footprint fields for L2 (L0603→L0402), U1 (TL→BL QFN variant) and
  R18 (R0603→R0402) were corrected to what is actually on the board.
- DRC: 0 errors, 0 unconnected, schematic parity clean. Remaining warnings are silk
  overlaps/courtyards from the LCSC footprints. Two dangling vias (+5V_VIN, a duplicated
  VCC via) and a 0.1 mm track stub from the original layout were removed.
- **USB1 locating pegs (fixed 2026-09-07).** The connector (C2765186) has two 0.7 mm
  locating pegs besides its four shell legs. The importer turned their NPTH holes into
  two small circles on Edge.Cuts, and the first cleanup pass moved those to F.Fab as
  "stray polygons" — so the rev-2 drill set had **no NPTH holes at all**. JLCPCB caught it
  before assembly ("no drill hole for the indicated pins" on USB1); that order was
  cancelled. The pegs are `np_thru_hole` pads again, in the library footprint and on the
  board, at the rev-1 positions (NPTH drill matches `archive/2025-09-23-rev1` exactly).
  They sit 0.171 mm from pads 1/12, as in the LCSC footprint and the fabricated rev 1;
  `openrz67.kicad_dru` accepts 0.17 mm between the pegs and USB1's own pads, and holds the
  pours 0.25 mm off the peg holes like rev 1 (JLCPCB's NPTH-to-copper minimum is 0.2 mm). A
  first version of the rule was unscoped, so the zone filler took 0.15 mm as its target too.
  Side effect: pads 1/12 now get one thermal spoke instead of two (2 DRC warnings).
- Gerber check against the fabricated 2025-09-23 set: copper and mask match apart from
  U4 (now S4B-XH-A side-entry instead of B4B-XH-A) and pour-fill details after KiCad's
  refill (thermal shapes); silkscreen differs in font rendering only. Drill files: PTH
  identical (incl. the four USB1 slots); NPTH identical again after the fix above —
  compare `out/gerber/*.drl` against the archive whenever a footprint changes.
- 3D models: the importer left dangling `EASYEDA_MODELS/…` references. Models were fetched
  per LCSC number with `easyeda2kicad` (`tools/fetch_3d.sh`) and both the board footprints and
  the library `.kicad_mod` files repointed to `openrz67.3dshapes/<name>.wrl`, keeping the
  importer's offsets/rotations, so "Update Footprints from Library" does not undo it. Board STEP:
  `kicad-cli pcb export step --subst-models -o out/openrz67.step openrz67.kicad_pcb`
  (needs the `.step` files, run `tools/fetch_3d.sh` first).
- Bottom silkscreen label changed from "EPS32-C3 Camera Trigger V1.0 / 2025-08-23" to
  "OpenRZ67 Trigger v2 / 2026-09".
- Pin electrical types were set by hand for the ICs (ESP32-C3, LGS5500, ME6211, USB-C);
  passives, connectors and the PhotoMOS pins are `passive`. Supply nets without a driver carry `PWR_FLAG`
  (GND, AGND, BAT+, VBUS, +5V_VIN, VDDA). ERC runs at default severities: 0 errors, 0
  warnings. The eight dangling wire ends inherited from the EasyEDA drawing were removed
  (an orphan S1/S2/AGND label cluster and three over-long wire tails); the netlist is
  unchanged, verified node-for-node before and after.
- The two mounting holes are real footprints (`MountingHole_2.0mm_Pad3.0`, plated 3.0 mm pad,
  2.0 mm drill) with `MountingHole` symbols H1/H2 in the schematic (excluded from BOM/POS).
- Courtyards were regenerated as pad/body bounding boxes (+0.05 mm) — the LCSC ones were
  oversized. Silkscreen outlines of 0402/0603 parts and of the two overhanging connectors
  (USB-C, U4) live on F.Fab now. DRC: 0 errors, 9 warnings: 5 courtyards where neighbours are
  closer than 0.1 mm on the fabricated layout (C21/USB1, L3 vs C20/R9/R12, H1/USB1), 2 silk-text
  size items from the LCSC footprints, 2 starved thermals on USB1 pads 1/12 (see the pegs note).
- The library symbol file was pruned to the symbols in use; the schematic's embedded copies are
  regenerated from it, so "symbol differs from library" warnings are gone.

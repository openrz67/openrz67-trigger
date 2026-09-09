# openrz67 PCB — KiCad project

KiCad 10 project for the OpenRZ67 trigger board (48 × 22 mm, 2 layers, ESP32-C3,
two TLP172AM PhotoMOS relays, BQ25185 charger + TPS63031 buck-boost). This is now the **source**; the EasyEDA Pro
project it was ported from is archived in `../archive/easyeda/` (v2 `.epro` and v3 `.epro2`);
each fabricated revision's upload package is in `../archive/<date>-rev<n>/` (rev 1 2025-09-23, rev 2 2026-09-07).

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
0.127, default track 0.16, via 0.45/0.25 (min 0.40/0.20), hole-to-track 0.175,
hole-to-hole 0.30, solder-mask expansion 0.051, thermal spoke 0.254 / gap 0.152.
Net classes: `gnd` (GND, 0.13 track), `3v` (VCC, VDDA, 0.20), `5v` (VBUS, BAT+, VSYS, SW_SYS,
SW1, SW2: 0.254 track, 0.5/0.3 via).
Copper-to-edge clearance is 0.30 mm (JLCPCB recommendation; the original pours ran to
the outline). Silkscreen minimums are JLCPCB's: 1.0 mm text height, 0.15 mm line width.

## Accepted warnings

ERC has **0 errors** (15 `endpoint_off_grid` warnings from the redrawn charger section, see the port notes). DRC has no errors; the warnings below are known,
understood and left in the reports rather than silenced, so a genuinely new one stands
out. No DRC or ERC exclusions are configured; the only custom rules are in `openrz67.kicad_dru`
(hole clearance around USB1's two locating-peg holes, see the port notes).

| Check | Count | What |
|---|---|---|
| `courtyards_overlap` | 7 | Neighbours closer than 0.1 mm: C21/USB1, L3 against C20/R9, H1/USB1 (all as on the fabricated rev-1 layout), plus C25 against R20/R6 and C24/D3 in the rev-2 power corner (pad-to-pad ≥ 0.40 mm everywhere). |
| `silk_overlap` | 1 | U2's pin-1 dot touches L3's silkscreen outline (0.02 mm). |
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
  **150 Ω** 0402 (R21/R22, UNI-ROYAL 0402WGF1500TCE C25082), about 12.7 mA nominal. At 3.3 V,
  VOH = 0.8 × VDD, VF = 1.4 V and +1% resistance give 8.2 mA at 25 °C, within the datasheet's
  5 to 25 mA recommendation. (220 Ω until 2026-09-07: its 5.6 mA worst case sat exactly on the
  5 mA minimum that the 2 Ω on-resistance is specified at.) The MOSFET output closes S1/S2 to camera ground.
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
- **Power path: LGS5500 + ME6211 → BQ25185 + TPS63031 (2026-09-07).** Rev 1 charged the
  250 mAh cell at 1 A (R11 = 100 kΩ on the LGS5500's ISET pin, latched at power-up); the
  LGS5500's lowest setting is 400 mA and the cell is rated for **120 mA**, so the charger IC
  was replaced rather than re-programmed. U3 is now a **BQ25185DLHR** (TI, LCSC C19725033,
  WSON-10): linear charger with power path, `IN` = VBUS, `BAT` = BAT+, `SYS` = VSYS.
  R11 2.7 kΩ ±1 % (C25885) on ISET → ICHG = 300 AΩ / 2.7 kΩ = **111 mA** nominal; the datasheet's
  ±10 % accuracy puts the worst case at ~122 mA against the cell's 120 mA rating, accepted
  (3.3 kΩ / 91 mA is the conservative alternative); R13 18 kΩ on ILIM/VSET → 500 mA input limit, 4.20 V regulation, 3.0 V precharge
  threshold (datasheet table 6-1, the value TI's own example uses); R16 (10 kΩ NTC, β 3434 K)
  on TS/MR matches the 10 kΩ / β 3435 K the pin is calibrated for — it still sits on the PCB,
  not in the pack. ~CE is grounded (always enabled), STAT1 is unused, STAT2 drives D3 (red)
  through R18 3 kΩ from VSYS: **lit = charging**, off = done / no USB / fault. SYS feeds the
  power switch S3 and then U2, a **TPS63031DSKR** fixed 3.3 V buck-boost (LCSC C15516,
  VSON-10, 1.8–5.5 V in, up to 500 mA out in boost), which replaces the ME6211 LDO: VCC now
  stays at 3.3 V down to the 3.0 V cutoff instead of sagging with the cell. L3 (2.2 µH,
  SPM6530T) is reused as its inductor (datasheet typical 1.5 µH; peak current ≈ 0.5 A at
  3.0 V in / 0.4 A out); C23 10 µF in, C24 10 µF out, C25 100 nF on VINA, PS/SYNC low =
  power-save, EN tied to VIN. LDO1, R12, R14, R17 and the +5V / +5V_VIN nets are gone.
  Footprints came from LCSC: the VSON-10 matches KiCad's `WSON-10-1EP_2.5x2.5mm_P0.5mm`
  pattern; the WSON-10 (TI `DLH`) has its 0.5 × 0.2 pads centred 0.25 mm further out than
  TI's land pattern (0.8 vs 0.55–1.05 mm), the usual LCSC/JLCPCB style. Check pin 1 of U2 and
  U3 in the assembly preview. Electrical cross-check against the TI datasheets (SLUSF65B,
  SLVS696D) 2026-09-07; not yet built.
- **R20 10 kΩ → 1 kΩ (2026-09-07, UNI-ROYAL 0402WGF1001TCE C11702, Basic).** D4 is an
  XL-1608UBC-04 (blue, 300 mcd at 20 mA, Vf 3.3 V typical at that current). On a 3.3 V rail
  the LED can never get near its rated current, so it runs current-starved: 10 kΩ gave ≈ 80 µA,
  about 1 mcd, which the fabricated rev 1 shows is visible indoors (the inverted firmware kept
  it lit at idle); 1 kΩ gives ≈ 0.3–0.8 mA depending on the part's Vf, 5–10× brighter, a normal
  indicator level, and well inside the GPIO's sink rating. The LED is now only on during
  trigger/bulb/countdown, so the extra current costs nothing at idle. Wiring is unchanged since
  rev 1: VCC → D4 anode, cathode → R20 → GPIO20 (active-low).
- **Resistor sourcing (2026-09-07).** Three lines had 19–40 pieces in JLCPCB stock: the 10 kΩ
  group R6/R7/R8/R20 → UNI-ROYAL 0402WGF1002TCE C25744 (Basic), R12 1 kΩ →
  0603WAF1001T5E C21190 (Basic, ±1 % instead of ±5 %), R18 3 kΩ → FOJAN FRC0402F3001TS
  C2909355. R12 has since gone with the LDO and R20 became 1 kΩ (see above); R6/R7/R8
  and R18 keep these parts. Library symbols are named after the MPN, so the three symbols were renamed and the
  100 kΩ one removed. Re-check stock at JLCPCB right before ordering.
- **C14/C26/C29 1 µF → Samsung CL10A105KB8NNNC C15849 (2026-09-07).** The HRE
  CGA0603X5R105K500JT (C6119852) was down to 8 pieces at JLCPCB. Same spec (1 µF ±10 % 50 V
  X5R 0603) and a Basic part, so no extended-part fee. All three sit on 3.3 V (VCC, CHIP_EN),
  so any ≥ 10 V 1 µF 0603 would do if this one runs out too. Every other BOM line had
  ≥ 500 pieces the same day; U3 (BQ25185, 572) and U2/U1 (~8 k) are the thinnest.
- **U4 pads** are 1.6 mm on the unchanged 1.0 mm drill (rev 1: 1.7 mm) because the S4B-XH-A
  footprint from LCSC draws them so — annular ring 0.30 mm, above JLCPCB's 0.20 mm minimum.
- The S1_DRV via next to U1 pin 9 moved 0.15 mm east (mask dam to the pad was 0.067 mm), and
  `VDDA` joined the `3v` net class (0.20 mm); the seven existing stub segments were drawn at
  0.16 mm and still are.
- **J1 — 1×4 GPIO header, not populated (branch `gpio-header`, 2026-09-07).** Through-hole
  pads along the bottom edge, x = 34.4–42.0 mm, y = 20.6 mm (0.55 mm copper to edge), 2.54 mm
  pitch, for a benchtop header or wires soldered straight into the holes. Pin 1 (square) =
  **3V3**, 2 = **GND**, 3 = **GPIO21** (U0TXD, so it doubles as a UART TX for logging with a
  USB-UART dongle), 4 = **GPIO6**. Silkscreen labels `3V3 GND TX IO6` sit above the pads in
  two staggered rows (1.0 mm text), below the U4 housing so they stay readable with the
  connector fitted; the footprint's own silk outline was removed to make room. The symbol is marked DNP and excluded from the BOM, and the footprint carries
  `exclude_from_bom` / `exclude_from_pos_files`, so J1 stays out of the BOM and the position file
  whichever way they are exported and JLCPCB never sees it; the pads are just copper and holes on the
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

- **Routing pass (2026-09-08).** U2's exposed pad has four GND vias (0.45/0.25) and U2's
  pads, like USB1's GND pads 1/12, now connect to the GND pour solid instead of through one
  thermal spoke — the four `starved_thermal` warnings are gone. The B.Cu VCC feed from U2's
  output no longer runs under U2's pad; it goes around the west side of the package. The
  SW1/SW2 pad exits are 0.254 mm (the `5v` class width) instead of 0.16. GPIO21's F.Cu jog
  past U1 pin 1 (LNA_IN) moved 0.75 mm west: 0.79 mm to the RF trace instead of 0.21. Two GND
  stitching vias next to it moved out of the way. The B.Cu ground under U1 still reaches the
  main pour through the same channel between the two GPIO21 vias (main B.Cu island 562 mm²,
  as before).

- **Review fixes (2026-09-08, after the rev-2 order).** A full review against rev 1 found the
  schematic sound and four layout items worth fixing before the next order; all are in
  (coordinates in the board frame, aux origin at the top-left corner):
  - C23 (the only 10 µF on SW_SYS) was 7 mm and two vias away from U2 pin 5 (VIN). It now
    sits at (15.15, 10.5), rot 180: pad 2 is 1.2 mm of 0.254 F.Cu from pin 5, pad 1 has a
    0.4 mm F.Cu strap into U2's exposed pad (PGND) and its own GND via at (15.85, 11.2).
  - The B.Cu ground under U1 hung on a 0.12 mm neck at (20.4, 18.6) — below the zone's own
    0.127 mm minimum, so a refill could have cut it. The VCC via at (20.32, 19.15) moved to
    (20.33, 19.40) and the CHIP_EN via 0.16 mm north to (22.92, 17.78). The erosion test that
    found the neck now gives ≥ 0.32 mm from U1 to every neighbouring pour region; the two
    pre-existing 0.16–0.20 mm necks in the north-west corridor (BAT+ vs the VCC B.Cu run,
    SW_SYS vs the VSYS via) were opened to ≥ 0.26 mm by nudging those runs 0.2–0.25 mm.
  - GPIO21 is one B.Cu run from a single via at (18.0, 14.17) to (25.15, 19.0) instead of
    four vias with two layer changes; the via is 0.25 mm from XTAL_N copper (was 0.16). The
    crossing under the LNA_IN microstrip at (19.3, 18.2) remains — every route from U1's left
    column to J1 has to cross the RF trace's line, so the slot (0.41 mm along the trace) can
    only go away by moving TX off GPIO21 or J1 off the bottom edge. Note: the earlier "0.79 mm
    to the RF trace" measured the F.Cu track; the via was 0.57 mm.
  - U3's exposed pad had no vias and thermal spokes. It has two GND vias 0.45/0.25 at
    (16.65, 3.7) and (17.35, 3.7), placed along x because the 0.4 mm-pitch pad rows leave only
    0.125 mm above/below, and U3 connects solid to the pour like U2.
  DRC after: 0 errors, 0 unconnected, the same 7 courtyard + 1 silk + 2 text warnings.
  Still open from the review, not done here: paste windows on U2/U3 exposed pads (100 % vs
  TI's 84–88 %), the F.Cu ground island under C26/C29/C6 with one via, the 68.7 mm² B.Cu
  island south-east of U1 with one via, a return via next to C24, 0.16 mm power necks at the
  U2/U3 pads, a `+` mark for BAT1 on F.SilkS, the 0.098 mm mask dam on U3.

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
Rotations for the parts carried over from rev 1 are unchanged since that order, except where
`ROT_FIX` in `regen.sh` adds a per-footprint offset so JLCPCB's order preview shows the part the way
KiCad does: +90° for the ESP32-C3 QFN-32 (U1: 0 → 90) and the TLP172AM SO-4 (U5/U6: 180 → 270).
JLCPCB's library orientation for those two packages is 90° off the KiCad footprint; their preview drew
U1 with pin 1 top-left (KiCad: bottom-left) and U5/U6 with the leads across the pads. The rev-1 order
had the same U1 offset with rotation 0 and JLCPCB's engineers corrected it against the silkscreen arc
(their FAQ: rotation and polarity are fixed from the silkscreen markings before assembly), so the
board came out right — sending the corrected angle just leaves them nothing to fix. The board itself is
unchanged. After uploading, U1, U5 and U6 must look like `out/openrz67-top.png` in the preview; then
check the DFM analysis in Order History (U1, U5, U6, X1, D3, D4) before approving production. Check pin 1 of U2, U3, U5, U6 and BAT1 in the fab's assembly preview before confirming:
the dot on the body must sit where `out/openrz67-top.png` shows it.
JLCPCB asked to confirm U3's polarity on the 2026-09-08 order: the WSON-10 footprint's pin-1 mark was a
0.06 mm ring, below their 0.15 mm silk minimum, so their preview showed no mark to check against. The
WSON-10 (U3) and QFN-32 (U1) footprints now carry a filled 0.4 mm pin-1 dot outside the body, like the
VSON-10 (U2) and SO-4 (U5/U6) already did.
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
  the library `.kicad_mod` files repointed to `openrz67.3dshapes/<name>.wrl`, so "Update
  Footprints from Library" does not undo it. The importer's model offsets were wrong for the
  three connectors (checked 2026-09-07 against the pin geometry inside the `.wrl` files): U4 sat
  3.45 mm off along its axis and 3.4 mm low, BAT1/S3 0.6 mm off and 3.5 mm low, USB1 1.2 mm off
  and 0.9 mm low. They now read U4 `offset 0 6.91 0, rotate 180`, PH `0 1.2 0, 180`, USB1
  `0 0 0, 0`; the pin tails land in their holes in the side renders. U2/U3 got the LCSC models
  (`WSON-10…DLH0010A.wrl` rotate 270, `SON-10…P0.50.wrl` rotate 0, as easyeda2kicad emits them). Board STEP:
  `kicad-cli pcb export step --subst-models -o out/openrz67.step openrz67.kicad_pcb`
  (needs the `.step` files, run `tools/fetch_3d.sh` first).
- Bottom silkscreen label changed from "EPS32-C3 Camera Trigger V1.0 / 2025-08-23" to
  "OpenRZ67 Trigger v2 / 2026-09".
- Pin electrical types were set by hand for the ICs (ESP32-C3, BQ25185, TPS63031, USB-C);
  passives, connectors and the PhotoMOS pins are `passive`. Supply nets without a driver carry `PWR_FLAG`
  (GND, AGND, BAT+, VBUS, SW_SYS, VDDA). ERC runs at default severities: 0 errors; the 15
  warnings are `endpoint_off_grid` from the redrawn charger/buck-boost section, whose
  symbols sit on whole millimetres rather than the 1.27 mm grid (cosmetic, connectivity
  verified by the netlist). The eight dangling wire ends inherited from the EasyEDA drawing were removed
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

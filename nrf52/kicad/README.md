# openrz67 nRF52 PCB — KiCad project

KiCad 10 project for the coin-cell trigger: 29.5 × 29 mm, 2 layers, Ebyte E73-2G4M08S1C
(nRF52840) module, CR2032 clip on the back, two TLP172AM PhotoMOS relays, JST SH 1.0 mm
side-entry camera connector, a second SH connector for SWD, one button, one LED, a P-MOSFET against a reversed cell. No regulator, no charger, no power
switch. Concept stage, not fabricated.

The schematic and the board are **generated**: `tools/design.py` holds parts, placement,
nets and every track, and the two generators write the KiCad files from it. Edit the model
and run `tools/regen.sh`; do not edit the `.kicad_sch` / `.kicad_pcb` by hand, the next
run overwrites them.

| File | What |
|---|---|
| `tools/design.py` | the design: parts with LCSC numbers, positions, nets, tracks, vias, keepout |
| `tools/gen_sch.py` | writes `openrz67-nrf.kicad_sch`: one symbol per part, a global label on every used pin, a no-connect on every unused one |
| `tools/gen_pcb.py` | writes `openrz67-nrf.kicad_pcb` with pcbnew: footprints, nets, outline, GND pours, antenna keepout, tracks, design rules |
| `tools/regen.sh` | runs both generators, then exports everything in `out/` and runs DRC (with schematic parity) and ERC |
| `tools/fetch_3d.sh` | downloads STEP+WRL models for every LCSC part in the BOM into `openrz67-nrf.3dshapes/` |
| `tools/export_step.sh` | board STEP to `out/openrz67-nrf.step` (gitignored); fetches missing part models first |
| `openrz67-nrf.3dshapes/` | 3D models; `.wrl` committed (renders), `.step` gitignored |
| `openrz67-nrf.kicad_sym`, `openrz67-nrf.pretty/` | project libraries: LCSC/EasyEDA imports via easyeda2kicad and KiCad's `R` |
| `out/` | generated: Gerber+drill zip, position file, BOM with LCSC numbers, schematic PDF, top/bottom renders, DRC/ERC reports |

## Regenerate

```sh
tools/regen.sh
```

Close KiCad first. Needs `kicad-cli` and KiCad's bundled python (for pcbnew); override with
`KICAD_CLI=… KICAD_PY=…`. It exits non-zero on any DRC/ERC error or unconnected pad.

## Circuit

The cell (`VBAT`) feeds the module through `Q1`, an AO3401A P-MOSFET with its drain on the
clip, source on `VDD` and gate on GND. The right way round the body diode conducts until the
channel turns on (under 85 mΩ at V<sub>GS</sub> = −2.5 V, about 1 mV at 15 mA). A cell put in upside
down leaves it off, so `VDD` never goes negative. `VDD` = `VDDH`, `DCCH` floating: nRF52840 normal-voltage
mode, 1.7–3.6 V). `VBUS` is tied to GND, as in Nordic's reference circuit for a supply on
VDD without USB. 100 µF sits at the clip terminal, ahead of `Q1` (a ceramic, a reversed cell does not harm it),
100 nF at the module. Each PhotoMOS LED
is driven from a GPIO through 330 Ω (about 5 mA at 3.0 V; the TLP172AM needs up to 3 mA).
P0.09/P0.10 are NFC pins that Nordic lists as standard drive, so the margin below 2.7 V is
not measured. The PhotoMOS outputs go to the camera connector; camera ground (`CAM_GND`)
is a separate net from the cell's `GND`.

| nRF52840 | Module pad | Function |
|---|---|---|
| P0.30 | 10 | button to GND, internal pull-up, wake from System OFF |
| P0.00 (XL1) | 11 | status LED through 330 Ω (LFCLK runs from the internal RC) |
| P0.09 (NFC1) | 41 | S1 PhotoMOS LED through 330 Ω |
| P0.10 (NFC2) | 43 | S2 PhotoMOS LED through 330 Ω |
| SWDIO / SWCLK | 37 / 39 | `J2` pins 3 / 4 |
| P0.18 (RESET) | 26 | not brought out; reset over SWD |

NFC pins need `nfct-pins-as-gpios` in the board devicetree; P0.00 needs the 32 kHz clock source
set to RC. P0.09/P0.10 run at high drive strength (S0H1) so the PhotoMOS LEDs get their 5 mA.

Connectors:

| Ref | Pin | Signal |
|---|---|---|
| `J1` camera, SH 1.0 mm (Qwiic/STEMMA QT cable) | 1 | camera ground (black) |
| | 2 | not connected |
| | 3 | S1 (blue) |
| | 4 | S2 (yellow) |
| `J2` SWD, SH 1.0 mm (Qwiic cable to the probe) | 1 | GND (black) |
| | 2 | VDD (red). With the cell out, the probe's 3.3 V powers the board here. Never with the cell in: it would charge the CR2032 |
| | 3 | SWDIO (blue) |
| | 4 | SWCLK (yellow) |

## Design rules

Clearance 0.127 mm, min track 0.127, default track 0.20 (signals 0.16, power 0.25), via
0.45/0.25, hole-to-track 0.175, hole-to-hole 0.30, copper-to-edge 0.30, mask expansion
0.051. JLCPCB silkscreen minimums (1.0 mm text, 0.15 mm line). A rule area over the
module antenna (x 0–16.5, y 0–3.8) keeps copper, tracks and vias off both layers.

## Accepted warnings

DRC and ERC have **0 errors**. The warnings left in the reports:

| Check | Count | What |
|---|---|---|
| ERC `endpoint_off_grid` | 17 | Pins of the imported symbols are not on the 1.27 mm grid. Connectivity is by label; verified by the schematic-parity DRC. |
| ERC `pin_to_pin` | 1 | The module's `VBUS` pin is bidirectional in the imported symbol and sits on GND with the power flag. Intended. |
| `silk_over_copper` | 11 | The holder footprint's own silkscreen crosses its centre pad. Fab clips it. |

## Mechanical

Outline 29.5 × 29 mm, R0.8 corners, no mounting holes. All parts on top except the cell clip
on the back. Module antenna end is flush with the top edge (y = 0); both SH connectors sit along the
bottom edge with their mouths facing it (y = 29), SWD left of camera (the SWD cable is a
lid-off job, no wall opening); the button sits bottom-left, the LED between the two connectors.

| Part | Height over the board |
|---|---|
| CR2032 clip `BT1` (back) | 3.75 mm, the cell under it; cell centre (13.5, 18), slides in from either long side |
| `J1` camera and `J2` SWD connectors | 2.9 mm, body 6.0 × 4.3 each |
| Module `U1` | about 2 mm (not verified) |

`BT1` is only the positive clip (MYOUNG drawing: "TERMINAL(+)"). The cell's negative face
rests on the Ø10 mm bare pad in the middle of the back. It has no paste, so the cell rests on
the pad's finish, not on a solder dome with flux on it. On the back a copper-free ring 7.5 to 10.2 mm from the cell centre lies
under the cell's rim, where the + can wraps over the edge; inside the ring only GND copper,
the same potential as the cell face resting on it. Ebyte's manual gives no antenna keepout figure, only "keep copper and
noisy traces away from the antenna end"; the 3.8 mm rule area is this project's choice.

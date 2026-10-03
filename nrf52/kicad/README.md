# openrz67 nRF52 PCB — KiCad project

KiCad 10 project for the coin-cell trigger: 27 × 29 mm, 2 layers, Ebyte E73-2G4M08S1C
(nRF52840) module, CR2032 clip on the back, two TLP172AM PhotoMOS relays, JST SH 1.0 mm
side-entry camera connector, four SWD pads, one button, one LED. No regulator, no charger, no power
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
| `openrz67-nrf.kicad_sym`, `openrz67-nrf.pretty/` | project libraries: LCSC/EasyEDA imports via easyeda2kicad, KiCad's `R`, and the own `SWD_1x04_P2.54` pad footprint |
| `out/` | generated: Gerber+drill zip, position file, BOM with LCSC numbers, schematic PDF, top/bottom renders, DRC/ERC reports |

## Regenerate

```sh
tools/regen.sh
```

Close KiCad first. Needs `kicad-cli` and KiCad's bundled python (for pcbnew); override with
`KICAD_CLI=… KICAD_PY=…`. It exits non-zero on any DRC/ERC error or unconnected pad.

## Circuit

The cell feeds the module directly (`VDD` = `VDDH`, `DCCH` floating: nRF52840 normal-voltage
mode, 1.7–3.6 V). 100 µF sits at the clip terminal, 100 nF at the module. Each PhotoMOS LED
is driven from a GPIO through 330 Ω (about 5 mA at 3.0 V, above the 3 mA trigger maximum
down to 2.5 V). The PhotoMOS outputs go to the camera connector; camera ground (`CAM_GND`)
is a separate net from the cell's `GND`.

| nRF52840 | Module pad | Function |
|---|---|---|
| P0.30 | 10 | button to GND, internal pull-up, wake from System OFF |
| P0.00 (XL1) | 11 | status LED through 1 kΩ (LFCLK runs from the internal RC) |
| P0.09 (NFC1) | 41 | S1 PhotoMOS LED through 330 Ω |
| P0.10 (NFC2) | 43 | S2 PhotoMOS LED through 330 Ω |
| SWDIO / SWCLK | 37 / 39 | `J2` pads 2 / 3 |
| P0.18 (RESET) | 26 | not brought out; reset over SWD |

NFC pins need `CONFIG_NFCT_PINS_AS_GPIOS=y`; P0.00 needs the 32 kHz clock source set to RC.

Connectors:

| Ref | Pin | Signal |
|---|---|---|
| `J1` camera, SH 1.0 mm (Qwiic/STEMMA QT cable) | 1 | camera ground (black) |
| | 2 | not connected |
| | 3 | S1 (blue) |
| | 4 | S2 (yellow) |
| `J2` SWD pads, 2.54 mm | 1 | VDD |
| | 2 | SWDIO |
| | 3 | SWCLK |
| | 4 | GND |

## Design rules

Clearance 0.127 mm, min track 0.127, default track 0.20 (signals 0.16, power 0.25), via
0.45/0.25, hole-to-track 0.175, hole-to-hole 0.30, copper-to-edge 0.30, mask expansion
0.051. JLCPCB silkscreen minimums (1.0 mm text, 0.15 mm line). A rule area over the
module antenna (x 0–16.5, y 0–3.8) keeps copper, tracks and vias off both layers.

## Accepted warnings

DRC and ERC have **0 errors**. The warnings left in the reports:

| Check | Count | What |
|---|---|---|
| ERC `endpoint_off_grid` | 15 | Pins of the imported symbols are not on the 1.27 mm grid. Connectivity is by label; verified by the schematic-parity DRC. |
| `silk_over_copper` | 11 | The holder footprint's own silkscreen crosses its centre pad. Fab clips it. |

## Mechanical

Outline 27 × 29 mm, R0.8 corners, no mounting holes. All parts on top except the cell clip
on the back. Module antenna end is flush with the top edge (y = 0); the camera connector
mouth faces the bottom edge (y = 29); SWD pads and the button sit bottom-left, the LED
between them and the connector.

| Part | Height over the board |
|---|---|
| CR2032 clip `BT1` (back) | 3.75 mm, the cell under it; cell centre (13.5, 18), slides in from either long side |
| Camera connector `J1` | 2.9 mm, body 6.0 × 4.3 |
| Module `U1` | about 2 mm (not verified) |

`BT1` is only the positive clip (MYOUNG drawing: "TERMINAL(+)"). The cell's negative face
rests on the Ø10 mm bare pad in the middle of the back; order the board with ENIG so that
pad does not oxidise. Ebyte's manual gives no antenna keepout figure, only "keep copper and
noisy traces away from the antenna end"; the 3.8 mm rule area is this project's choice.

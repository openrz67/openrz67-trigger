# nRF52 coin-cell trigger

Second board design for the RZ67 trigger: an nRF54L15 module on a CR2032, no regulator,
charger or power switch. Rev A is ordered (fab package in [`kicad/archive/`](kicad/archive/)).

| Directory | What |
|---|---|
| `kicad/` | the board, generated from `tools/design.py`; fab files in `out/` |
| `case/` | build123d snap-fit box |
| `firmware/` | Zephyr application, builds on nRF Connect SDK v3.4.1 |
| `notes/` | reasoning and history |

## Parts to buy

Nothing is soldered by hand. The board comes assembled, everything else plugs in.

| What | Where | Note |
|---|---|---|
| Assembled board | JLCPCB, upload `kicad/out/openrz67-nrf-gerber.zip` + BOM + pos from `kicad/out/` | assembly on both sides |
| CR2032 | anywhere | one per board |
| SH1.0 4P to Dupont female cable (Qwiic / STEMMA QT pigtail) | AliExpress | three: one camera cable (`J1`), one for flashing (`J2`), one spare |
| Raspberry Pi Pico 2 WH | any Pi reseller | the flashing probe; H = headers pre-soldered, W is irrelevant here. Load Raspberry Pi's `debugprobe_on_pico2.uf2` on it; a Pico H (`debugprobe_on_pico.uf2`) works the same |

`J2` pin 2 carries the cell voltage out. Never plug a powered Qwiic device into `J2`; only the
probe cable belongs there. The camera end of the `J1` cable goes to the RZ67 socket as today (GND, S1, S2). Wiring for
`J2` to the Pico is in [`firmware/README.md`](firmware/README.md).

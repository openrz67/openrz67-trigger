# nRF52 trigger: concept

A from-scratch second design. Same job as the ESP32-C3 board (close S1 and S2 to the camera's
ground over BLE, controlled from the existing apps), but built around the one thing the current
design cannot do: live on a coin cell with no power switch, no charger and no regulator.

## What stays

- The GATT: service `c9239c9e-…`, command characteristic `458d4dc9-…`, battery mV characteristic
  `cda71ce6-…`, DIS 0x180A, BAS 0x180F. The apps do not change.
- Two TLP172AM PhotoMOS channels. Isolated, bidirectional, proven on the camera.
- The camera cable's camera end. The board end becomes a JST SH plug (see layout decisions).

## What goes

| Today | Why it is not needed |
|---|---|
| TPS63031 + 7 × 6.5 mm inductor + 6 × 10 µF | nRF52 runs 1.7–3.6 V straight off the cell |
| BQ25185, USB-C, NTC, reverse-battery FET, LiPo + JST PH | primary cell, replaced not charged |
| KCD11 rocker + SW_SYS divider | System OFF is ~0.5 µA; the button is the power button |
| Bare ESP32-C3 + 2 crystals + matching + U.FL + FPC antenna | module with PCB antenna |
| VBAT divider | nRF52 ADC measures VDD internally |

## Board

- **MCU**: nRF52840 module with PCB antenna. Candidate Ebyte E73-2G4M08S1C (13 × 18 mm, LCSC
  stock, JLC-assemblable). Smaller alternative Raytac MDBT50Q-1MV2 (10.5 × 15.5 mm, not at LCSC).
  nRF52840 over nRF52832 for the USB peripheral: not used now, free option for a USB-flash variant later.
- **Cell**: CR2032 in an SMD holder. 220 mAh, 20 mm. CR2450 (620 mAh, 24.5 mm) if the case
  can take it; same holder family, decide when the outline is drawn.
- **Outputs**: 2 × TLP172AM, LED resistor **330 Ω** (not 150 Ω): 5.2 mA at 3.0 V, 3.4 mA at
  2.5 V, still above IFT max 3 mA (TLP172AM datasheet §11, see `../../pcb/kicad/notes/review-2026-09-10-verify.md` 4.2).
  Nominal IF 5 mA is the RON ≤ 2 Ω test point. Camera GND stays separate from cell GND.
- **Bulk cap**: 100–220 µF across the cell. CR2032 internal resistance is 10–40 Ω and climbs
  with age; worst-case peak is 2 × 5 mA LEDs + ~6 mA radio TX at 0 dBm ≈ 16 mA ≈ 0.6 V sag at
  end of life. The cap carries the radio bursts; TX power stays at 0 dBm.
- **UI**: one button (B3U-1000P, as today), one 0603 LED.
- **Programming**: SWD pads (SWDIO, SWCLK, GND, VDD, RESET), Tag-Connect TC2030 footprint or
  five 1.27 mm pads. No USB on the device. Probe: a Raspberry Pi Pico running debugprobe
  (CMSIS-DAP) or a J-Link EDU Mini.
- **Size**: the holder sets it, roughly 26 × 30 mm, 2 layers. Module antenna end over the
  board edge, keepout per the module datasheet, cell holder at the other end.

## Power behaviour

| State | Current | Note |
|---|---|---|
| System OFF, button wake | ~0.5 µA | default state |
| Advertising, 1 s interval | ~15 µA | 5 min after a press or a disconnect, then OFF |
| Connected, idle | ~10 µA | no timeout, lasts as long as the app holds the link |
| Shutter held | 5 mA per channel | 1 min bulb = 0.1 mAh |

A press wakes it and it advertises for 5 min. Once the app connects the timer no longer
applies. After a disconnect it advertises for another 5 min so the app can reconnect
unattended, then goes back to OFF. Cell life is set by shelf life, not use.

## Firmware

Zephyr via nRF Connect SDK (west + the VS Code nRF Connect extension). System OFF, advertising
timeouts, BAS and DIS are built in, and the Nordic BLE stack is the reference one. The
Arduino route (Adafruit nRF52 core) needs the Adafruit bootloader on the module and gives less
control of sleep. The command protocol is reimplemented 1:1 from `src/main.cpp`.

## Case

A new, much smaller box: cell holder, module and two PhotoMOS stacked in one layer, roughly
30 × 34 × 12 mm. Button through the lid, LED through a thin wall or a short pipe (glued, as
today). The lid comes off for the cell, so the snap closure must survive many cycles; the
press-fit walls on the current case are known to loosen. Cable exit through the wall at the
XH connector, as today.

## To verify before drawing

- E73-2G4M08S1C: JLC assembly class. (LCSC C356849, stock OK; Ebyte gives no keepout figure.)
- CR2450 clip variant, if the case wants the bigger cell.
- 100–220 µF in 1206/1210 at 6.3 V, or a tantalum.
- Actual TX current of the chosen module at 0 dBm with DC/DC enabled.
- Camera-side requirements in `../../case/notes/rz67-remote-inputs.md` still hold for 5 mA drive.

## Layout decisions (kicad/, first pass)

- **Board 31 × 30, not 26 × 30.** The XH connector is 17 mm wide including its two tabs
  and the holder clip spans 26 mm; both set the width. The cell sits on the back, centred,
  5 mm below the antenna end.
- **JST SH 1.0 mm (SM04B-SRSS-TB, C160404) instead of XH.** The user does not need the XH
  plug. XH side-entry is 7 mm tall and 17 mm wide with its tabs, SH is 2.9 × 6 mm, and SH
  4-pin is the Qwiic / STEMMA QT cable, so pigtails are everywhere. Pin 1 is camera ground
  so a Qwiic cable's black wire is ground. (The through-hole XH was never an option here:
  its tails would sit under the cell.)
- **Connector at the bottom edge, module at the top.** With the connector on the right edge
  there was no corridor for the SWD and drive traces between the module pads and the
  connector pads.
- **Four plain SWD pads instead of Tag-Connect.** The TC2030-NL footprint with its three
  locating holes did not fit next to the connector tab, and the reset line is not needed:
  pyOCD / J-Link reset the nRF52 over SWD.
- **GPIO choice is dictated by the module footprint.** Only the outer pad rows can be
  routed on the top layer (the inner row is boxed in). Button on P0.30 (last pad of the left
  column), LED on P0.00/XL1 (first pad of the bottom row), S1/S2 on the NFC pins P0.09/P0.10.
  The module has no 32 kHz crystal, so XL1 is a free GPIO when LFCLK runs from RC.
- **Both clip feet are VDD** and tied together on the back layer below the cell pad; 100 µF
  sits at the right foot. Electrically redundant with the clip itself, but it keeps the
  netlist honest and puts the bulk cap at the cell.
- **Antenna keepout** is a rule area over the module's antenna end, both layers, 3.8 mm
  deep. Ebyte's manual gives no number; this is the module's own antenna length plus 1 mm.

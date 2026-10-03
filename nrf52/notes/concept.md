# nRF52 trigger: concept

A from-scratch second design. Same job as the ESP32-C3 board (close S1 and S2 to the camera's
ground over BLE, controlled from the existing apps), but built around the one thing the current
design cannot do: live on a coin cell with no power switch, no charger and no regulator.

## What stays

- The GATT: service `c9239c9e-…`, command characteristic `458d4dc9-…`, battery mV characteristic
  `cda71ce6-…`, DIS 0x180A, BAS 0x180F. The apps do not change.
- Two TLP172AM PhotoMOS channels. Isolated, bidirectional, proven on the camera.
- The camera cable and its S4B-XH-A side-entry connector, so the existing cable fits.

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

- E73-2G4M08S1C LCSC number, stock, JLC assembly class, antenna keepout drawing.
- CR2032 holder footprint and LCSC part; CR2450 variant.
- 100–220 µF in 1206/1210 at 6.3 V, or a tantalum.
- Actual TX current of the chosen module at 0 dBm with DC/DC enabled.
- Camera-side requirements in `../../case/notes/rz67-remote-inputs.md` still hold for 5 mA drive.

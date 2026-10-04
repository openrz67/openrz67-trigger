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
| Bare ESP32-C3 + 2 crystals + matching + U.FL + FPC antenna | module with ceramic antenna |
| VBAT divider | nRF52 ADC measures VDD internally |

## Board

- **MCU**: nRF52840 module with ceramic antenna. Candidate Ebyte E73-2G4M08S1C (13 × 18 mm, LCSC
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
| Advertising, 30–60 ms interval | ~150 µA (estimate) | 5 min after a press or a disconnect, then OFF |
| Connected, idle, 30–50 ms interval | ~25 µA (estimate) | no timeout, lasts as long as the app holds the link |
| Shutter held | 5 mA per channel | 1 min bulb = 0.1 mAh |

A press wakes it and it advertises for 5 min. Once the app connects the timer no longer
applies. After a disconnect it advertises for another 5 min so the app can reconnect
unattended, then goes back to OFF. A 5 min advertising window is 0.01 mAh, a whole day connected
is 0.6 mAh of 220; cell life is set by shelf life, not use. The fast intervals are the ESP32
firmware's values, kept so the apps behave the same; slowing them is a tuning item for later.

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

- **Board 27 × 29.** The clip's two feet span 25.9 mm, that is the width. The cell sits on
  the back, centred, 5 mm below the antenna end. (The first pass was 31 × 30 because of the
  17 mm wide XH connector.)
- **JST SH 1.0 mm (SM04B-SRSS-TB, C160404) instead of XH.** The user does not need the XH
  plug. XH side-entry is 7 mm tall and 17 mm wide with its tabs, SH is 2.9 × 6 mm, and SH
  4-pin is the Qwiic / STEMMA QT cable, so pigtails are everywhere. Pin 1 is camera ground
  so a Qwiic cable's black wire is ground. (The through-hole XH was never an option here:
  its tails would sit under the cell.)
- **Connector at the bottom edge, module at the top.** With the connector on the right edge
  there was no corridor for the SWD and drive traces between the module pads and the
  connector pads.
- **SWD on a second JST SH connector (`J2`)**, not Tag-Connect and not bare pads. The
  user does not want to solder: a Qwiic cable onto a Pico H is a zero-solder probe. Pin 1
  GND so the cable's black wire is ground, like `J1`. Reset is not brought out: pyOCD /
  J-Link reset the nRF52 over SWD. (Tag-Connect's locating holes did not fit anyway.) The
  mouth faces into the board, so flashing needs the lid off.
- **GPIO choice is dictated by the module footprint.** Only the outer pad rows can be
  routed on the top layer (the inner row is boxed in). Button on P0.30 (last pad of the left
  column), LED on P0.00/XL1 (first pad of the bottom row), S1/S2 on the NFC pins P0.09/P0.10.
  The module has no 32 kHz crystal, so XL1 is a free GPIO when LFCLK runs from RC.
- **Both clip feet are VDD** and tied together on the back layer below the cell pad; 100 µF
  sits at the right foot. Electrically redundant with the clip itself, but it keeps the
  netlist honest and puts the bulk cap at the cell.
- **Antenna keepout** is a rule area over the module's antenna end, both layers, 3.8 mm
  deep. Ebyte's manual gives no number; this is the module's own antenna length plus 1 mm.

## Case decisions (case/, first pass)

- **Board on a ledge, cell hanging below, component side up.** The button and LED must face
  the lid, and the cell only needs the board lifted out to be changed: lid off, base turned
  over, the board drops out. (The first pass had a Ø14 push-out hole in the floor; it went
  so the floor stays flat for velcro on the camera, as on the ESP32 case.)
- **Ledge stands on the floor.** Above `split_z - lap` the base wall is only its outer half,
  the lid tongue fills the inner half, so the first-pass ledge hung on the wall was two
  floating bodies in the STL. It is now a wall from the floor up, 0.2 mm inside the tongue.
  The same check found the lid tongue overlapping the base's full-thickness wall beside the
  plug opening (the tongue notch was narrower than the zone the base keeps); the notch now
  spans it. Both are module-level checks now: one body per part, no base/lid overlap.
- **Snap fingers moved to the side walls.** The back wall carries the plug opening, the
  front wall faces the antenna end; the ESP32 case's finger geometry is reused unchanged,
  which is why the wall stays 3.2 mm on a box this small.
- **Button as a cantilever tab in the lid**, not a separate cap: nothing to lose, no extra
  part, and ABS at 1.0 mm over an 8 mm tab flexes the 0.3 mm the switch needs. Untested.
- **No light pipe.** A Ø1.6 hole 3 mm above a 0603 LED shows the light; a pipe can be glued
  in later if it is too dim. `D1` was moved 1.6 mm away from `SW1` on the board so the hole
  clears the tab's slot.
- **The clip feet are tied on the back layer outside the cell**, up at y = 6.5 and down the
  two side edges: the LED drive had to cross to the back to get under `J2`, and nothing but
  GND may lie under the cell (see the review fixes below).
- **Lid bosses sit on free copper, not on the board corners.** The module fills the
  front-left corner and `C1` + `J1` the back-right one; `J1` moved 0.7 mm and `C1` 2.8 mm
  on the board to free a spot.

## Review fixes (2026-10-04, before ordering)

A second-opinion review of the board and the firmware. Applied:

- **Copper-free ring under the cell rim** (`CELL_KEEPOUT`, B.Cu rule area, r 7.5 to 10.2 mm):
  the CR2032's + can wraps over the edge of its negative face, and the only thing between it
  and the back-layer copper was solder mask. Nothing but mask now sits under that rim; inside
  the ring the GND pour stays, it is the same potential as the cell face on it. The VDD loop
  that tied the clip feet at y = 10 ran under the cell and moved to y = 6.5.
- **GND vias on the back under the module** (6.0, 10.0), (20.8, 8.8), (21.0, 5.2), (7.0, 19.7):
  the VDD loop and the ring had cut the back pour into islands that the filler removed, so
  the module had no ground under it on the back.
- **PhotoMOS pins at high drive** (`NRF_GPIO_DRIVE_S0H1`): standard drive guarantees only
  about 2 mA at 3 V, the TLP172AM needs up to 3 mA; the 330 Ω asks for 5.
- **Advertising restarts from `recycled`**, not from `disconnected`: with one connection slot
  the object is still held in `disconnected()` and `bt_le_adv_start` returns -ENOMEM, which
  would have left the board unreachable until it slept.
- **Button on SENSE** (`sense-edge-mask`), not a GPIOTE channel, so the idle current while
  awake stays at the sleep figure.
- **PhotoMOS 3D model**: LCSC ships a 6-pin SOP model for C2152276; the board now uses the
  main board's `SMD-4_L3.7-W4.6-H2.2-LS7.0-P2.54` model, so the STEP export (and the case
  that reads it) sees the real 4-pin body.

Noted, not changed:

- **DC/DC regulator stays off.** It would halve the radio current, but it needs an inductor on
  the nRF52840's DCC pin, and that pin is inside the module. Ebyte's user manual (checked
  2026-10-04) lists DCCH (pad 25, "DC/DC converter output") but no DCC and says nothing about
  an inductor, so whether REG1 can run as DC/DC is unknown. First thing to try on hardware,
  with the probe attached: set `regulator-initial-mode = <NRF5X_REG_MODE_DCDC>` on `&reg1`
  and see if the chip stays up. Without the inductor the core rail collapses and it resets,
  which is harmless. The gain is about 10 µA connected and 70 µA while advertising, not a
  battery-life question for a 220 mAh cell.
- `J2` pin 2 is the cell voltage. Documented as sense-only; a powered Qwiic device plugged in
  there would charge the cell. There is no silkscreen room for a warning.
- `J1`'s mouth sits about 1.7 mm inside the board edge, so the plug reaches through the case
  wall; the case opening is sized for it.
- `S2_DRV` runs at y = 2.3 beside the antenna keepout, and copper fills the top-right corner
  from y = 0. Slight range cost at most; left as is.
- `BT1` on the back means two-sided assembly at JLCPCB (or hand-soldering the clip).
- The power table above was corrected to the intervals the code actually uses.

## Firmware decisions (firmware/, builds, not flashed)

- **Zephyr app with its own board** (`boards/openrz67/openrz67_nrf`), not an overlay on the
  nRF52840 DK: the pin map lives in one devicetree file next to the code, and `west build
  -b openrz67_nrf` says what it is.
- **GATT copied byte for byte** from the ESP32 firmware, including the legacy 1-byte and
  the 3-byte countdown commands, so both apps keep working.
- **Main loop sleeps as long as it can.** `next_wait()` wakes it for LED edges and the
  countdown only; idle and connected it wakes once a second. The radio runs on its own.
- **System OFF, not deep sleep with a timer**: the button's SENSE wakes the chip, nothing
  else needs to. Advertising runs 5 minutes after boot and after each disconnect.
- **No UART, no console** in the normal build; `debug.conf` adds RTT logging for a probe
  session. The board has no serial pins.
- **Battery from VDD** on the SAADC's internal channel, no divider. 2.5 to 3.0 V = 0 to
  100 % on the Battery Service, raw mV on the custom characteristic.

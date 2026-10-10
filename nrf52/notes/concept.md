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
- **No light pipe** (first pass; replaced, see below). A Ø1.6 hole 3 mm above a 0603 LED shows the light; a pipe can be glued
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
- `J2` pin 2 is the cell voltage; a powered Qwiic device plugged in there with the cell in
  would charge it. There is no silkscreen room for a warning.
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

## Second review (2026-10-04)

Datasheet pass over every part (all pins and footprints matched) plus firmware and case.
Board changes:

- **No paste on the cell's negative pad.** A 10 mm paste disc reflows to an uneven dome with
  flux on the contact surface; ENIG alone is the contact.
- **`VBUS` (pad 27) to GND**, as in nRF52840 PS reference config 6 (supply on VDD, no USB).
  It floated before.
- **Two vias out of pads**: the VDD via sat in both `C1`'s pad and the clip foot, the GND via
  beside `SW1` in its pad. Both wick solder; they now sit beside the pads.
- **Flashing powers the board from the probe, cell out.** The Pico's SWD lines are 3.3 V; on
  a cell at 2.8–3.0 V that is past the nRF52's VDD + 0.3 V limit. With the cell out and the
  red wire on the Pico's 3V3, both sides run at 3.3 V.

Checked and left: P0.09/P0.10 are "standard drive, low frequency I/O only" in the PS; high
drive at DC works and is what the PhotoMOS needs. NFC pins leak up to 10 µA when at
different levels; both idle low. The 100 µF X5R is about 58 µF at 3 V and may leak up to
6 µA by spec; measure sleep current on the first board.

Case changes:

- **Board X mirrored.** `bx()` mapped board X straight into case X while board Y (down in
  KiCad) went toward the back wall: that is a mirror image, not a rotation. Tab, LED hole,
  plug opening and bosses sat over the wrong parts, and the tongue notch lets the lid on one
  way only. Every keepout used the same mapping, so no check saw it. Now `bx` mirrors, and a
  check pins the plug opening to the left half.
- **Button tab tip off the wall.** The tip ended 0.2 mm over the inner wall with 0.6 mm of
  air; the nub needs 0.45 mm (gap 0.3 + B3U travel 0.15), which at the tip is 0.6 mm. The tip
  now ends 0.35 mm inside the cavity (`tab_tip` 1.45).
- **Tab 0.8 thick, not 1.0.** At 1.0 the tab alone takes about 6 N to bend 0.45 mm, 8 N with
  the switch; at 0.8 it is about 5 N. The "0.3 mm the switch needs" above was 0.45.
- **Bosses checked against every top-side part** (footprint bounding boxes); the board-wide
  keepout cut them out, so only a few parts were seen before.

Firmware changes:

- **Long-press power-off waits for a steady release** (three 20 ms reads in a row). It
  stopped at the first released read; a bounce after that pulled the SENSE pin low and woke
  the chip straight out of System OFF.
- **Commands follow the ESP32's `handleCommand()` exactly**: only value 1 starts, `10`/`20` no
  longer cancel a countdown and `30` no longer ends a bulb exposure. The apps never send
  these, but the GATT is meant to be the same device.
- **GAP preferred supervision timeout 4 s** (`BT_PERIPHERAL_PREF_TIMEOUT`), the same as the
  update request; the default was 420 ms until that request goes out 5 s after connecting.

Left as is: a link lost during bulb ends in power-off after the 5 min advertising window,
which closes the shutter. The camera closes it after about 60 s on its own anyway.

## Light pipe (2026-10-04)

The bare Ø1.6 hole was replaced by a printed clear light pipe, the ESP32 case's top hat made
round. The LED top is 4.5 mm under the lid surface and the advertising blink is 40 ms, so
through a hole it shows only from straight above and is easy to miss in daylight. The collar
ends at the pipe's lower end, 0.8 above the board: only `D1` and `R3` (both under 0.6) are
under its ring, `J1`'s body is 0.4 away. `qidi-template.3mf` was rebuilt from the ESP32
case's template (identical print settings) with the objects renamed, so the pipe keeps its
plate 2 / clear filament / per-object profile.

## Cell change with the board in the lid (2026-10-04)

Users put in and change the cell themselves, so the board no longer drops loose out of the
base. Two hooks off the lid ceiling hold it in the lid, and the lid tongue is gone from the
back wall, so the cell slides out of the clip backwards. It cannot go forwards: it needs
14.5 mm of travel to clear the strap, and the front ledge stops it after 7.

Rejected:
- **Coin-twist hatch in the floor**: the clip loads sideways, and no top-loading CR2032 holder
  on JLC fits a 27 × 29 board (all are 28-33 mm tail to tail).
- **Glue the board to the lid bosses**: a broken case would scrap the board. With hooks the
  board comes out and a new case can be mailed.

The hooks hang from the ceiling, not off the tongue: on the tongue the barb would sit 1.6 mm
below the finger root, too stiff to spring 0.5 mm. From the ceiling the finger is 5.6 mm to the
barb, about 2.4 % strain, under the snap fingers' 3.3 %. They need 1.9 mm between the board's
side edge and the wall (was 0.4), so the case is 3 mm wider. The clip keepout was a full box;
the 3D model shows only the solder legs within 2.5 mm of the board, so the check is now strap
plus legs, and the hooks sit in front of the legs.

Untested: the hook click and release force, and the barb's flat face. It prints as a 0.7 mm
overhang, like the snap bead's retention face.

Polarity marking: the nRF52 has no reverse protection, and a cell put in upside down puts
-3 V on VDD. There is a "+" in the base floor under the cell and `CR2032  + SIDE OUT` on
B.SilkS in the strip between the front edge and the cell (`SILK` in design.py).

## Visual pass (2026-10-04)

- Lid text printed fuzzy. "TRIGGER" at 3.2 was too small for a 0.4 nozzle, and the 0.1 bold
  growth closed the counters in "OpenRZ67". Now 5.8 / 4.0 with 0.05 growth. 5.8 is the
  widest the lid allows: caps 4.4 mm, at the ~4.4 mm legibility limit for a 0.4 nozzle;
  lowercase is 3.0. DIN Condensed Bold would give 7.0 / 5.0 at the same width, but Futura
  keeps the ESP32 case's look. Avenir Next Condensed was in between; Futura Condensed
  ExtraBold breaks OCCT's offset. A diagonal text line gains nothing with two lines.
- The ESP32 case's rail added: from the left side into the LED seat. It cannot run past the
  LED as on the ESP32 case: the button tab sits on the same row.
- Base bottom edge got the lid's 1 mm chamfer; the button tab's free end got round corners.
- First-layer line width 0.5 -> 0.42 in `qidi-template.3mf`: the lid text is the first layer, and
  0.5 lines blurred it. It is a print-wide setting in QIDI/Bambu Studio (GCodeConfig), not per
  object, so the base and light pipe get it too. The textured PEI plate also roughens the text
  edges; no smooth plate on hand.

## Third review (2026-10-05)

- C2 -> CL05B104KO5NNNC (C1525, basic) and R3 1 kΩ -> 330 Ω (same part as R1/R2): one
  extended part and one BOM line fewer. The LED gets ~3 mA instead of ~1 mA.
- Firmware: 5 s watchdog, and a disconnect ends a bulb. Before, a hung loop or a lost link
  mid-bulb kept S1/S2 on until the cell was pulled.
- Case: module height 2.0 -> 3.1 (manual: 3.0 ±0.1). Only the lid keepout check uses it;
  it still passes and the meshes do not change.
- Kept as is: R1/R2 at 330 Ω. 220 Ω only helps a worst-case VF at an almost empty cell, and
  costs ~50 % more cell current per channel while the shutter is held. DC/DC off: cell life
  is set by shelf life, not use (see Power behaviour), so the saving is small and an LDO
  boots with or without the module's inductor.
- Cheaper parts checked: LTV-357T-C (C119091) for U2/U3 saves ~1.1 USD per board but conducts
  one way only; measure S1/S2 polarity on the camera first. No cheaper module fits without a
  new layout. Everything stays JLC-assembled, BT1 included.

## Reverse-cell block (2026-10-08)

- `Q1` AO3401A (C15127, basic, the main board's Q3 part and KiCad `SOT-23` footprint) between
  the clip and `VDD`: drain on the new net `VBAT` (both clip feet, the back loop, `C1`), source
  on `VDD`, gate on GND. Before, the "+" marks were the only guard and a cell put in upside down
  put −3 V on the module, a new assembled board. Q1 sits at (5.4, 21.3) rot 90 where the left
  foot's via fed the module; "SWD" moved to (4.3, 24.4) off its pads.
- `C1` stays at the clip, on `VBAT`: a ceramic takes −3 V, and moving it would cost a track
  across the cell rim ring.
- `J2` pin 2 is on `VDD`. With the cell in, the channel is on, so the probe's 3.3 V still
  reaches the cell: the README rule (cell out when the probe powers the board) stands.
- Rotation for JLC: none in `ROT_FIX`. The main board's Q3 with the same footprint matched the
  order preview on 2026-09-25 without one.
- Case: `Q1` added to the boss clearance list; all checks pass, meshes unchanged.

## Surface finish (2026-10-08)

ENIG is no longer a requirement in the READMEs. The argument was oxidation of the bare cell
pad, but tin's oxide film is thin enough that the clip pressure breaks through it, and the
user's other HASL boards show no trouble. Nothing measured says HASL fails here; ENIG stays an
option if the cell contact ever proves flaky.

## Module change: E73-2G4M08S1F / nRF54L15 (2026-10-09)

- Why: the S1F is about 2 USD cheaper per board at JLC (5.66 vs 7.63), 12 × 17.2 mm instead of
  13 × 18, and the nRF54L15 needs roughly half the radio current of the nRF52840 when its DC/DC
  runs (TX 0 dBm 4.8 mA, RX 3.4 mA vs 10.6 / 9.9 mA on the LDO). Nothing was ordered yet, so
  the change costs no extra test boards. USB, the reason for the nRF52840, was never used.
- Rejected: E73-2G4M08S1CX (same footprint, IPEX instead of an antenna), nRF52832/52810
  modules (28.7 mm long, or out of stock), a bare nRF54L15 (own RF design).
- Pins: the button must be on P0/P1, since P2 has no SENSE and cannot wake from System OFF.
  P1.04 on the left column; P1.02/P1.03 (NFC), P1.08 (CLK16M/EXTREF) and P1.11/P1.12 avoided.
  The outputs sit on P2 (P2.00, P2.04, P2.05), which faces the parts. Total GPIO current
  with both PhotoMOS and the LED on is about 14 mA, under the 15 mA the PS recommends.
- Layout: module at (7.0, 11.2), rot 0, antenna at the top edge. Its left column faces the
  board edge, so `VDD` (pad 9) and the button (pad 7) run down two tracks between the module and
  the edge. SWD comes off pads 11/12 in the order SWCLK, SWDIO, so `J2` pins 3/4 swapped to
  SWCLK/SWDIO; the other order crosses. Antenna keepout 15 × 5.3 mm. `SW1`, `D1`, `J1` and the
  case are unchanged; `J2` stays in place.
- DC/DC: the inductor goes on DCC, which the module does not bring out, and Ebyte does not say
  whether it is inside. The firmware reads `VREGMAIN.INDUCTORDET` at boot and enables DC/DC
  only when it is there.
- Crystals are in the module (the S1C had none): LFXO replaces the RC oscillator. Load
  capacitance unknown, DK values used. Check the 32 MHz frequency on the first board.
- Flashing: pyOCD ≥ 0.37 has the `nrf54l` target built in and erases a locked chip itself.
  The Pico debugprobe stays.
- Errata: 114 (SENSE + bouncing button, `latch-detect`), 30 (cold, HFINT calibration).
  Chip revision on Ebyte's parts unknown.
- No nRESET RC as in Ebyte's reference circuit: a reset pulse during power-on prolongs
  anomalies 100/103, and the internal pull-up holds it.
- Risk: new module (datasheet 2025-11), 144 in stock at JLC on 2026-10-08. No 3D model from LCSC or Ebyte;
  `kicad/tools/module_3d.py` draws a box from the manual's dimensions instead.

## Relay drive and module decoupling (2026-10-10)

From `kicad/notes/review-2026-10-10.md`.

- R1/R2 330 Ω -> 220 Ω (C25091, basic). The third review kept 330 Ω on typical figures; with
  the datasheet limits (VOH = VDD − 0.4 V, VF 1.4 V) 330 Ω drops below the TLP172AM's 3 mA
  IFT at about 2.8 V, well before a CR2032 is empty. 220 Ω gives 4.1 mA at 2.7 V and 3.2 mA
  at 2.5 V. The extra cell current only runs while the shutter is held, 3–4 s in normal use.
- R3 330 Ω -> 1 kΩ (C11702, basic): the LED shares Nordic's 15 mA recommended GPIO total with
  both relays. A fresh cell gives about 14 mA for all three. Costs one BOM line back.
- C3 100 nF at module pad 9, GND straight to pad 10, below the module's bottom-left corner.
  C2 sat 8.7 mm away at Q1 with about 20 mm of VDD track to pad 9; it stays for J2 and Q1.
- Open: bulb test at 4 s and 60 s with a used and a cold cell on the first boards.

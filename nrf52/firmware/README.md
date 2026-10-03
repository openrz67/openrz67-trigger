# Firmware for the nRF52 board (Zephyr / nRF Connect SDK)

Zephyr application for the coin-cell trigger in [`../kicad/`](../kicad/). Same Bluetooth
services and command bytes as the ESP32-C3 firmware in the repository root, so the
[Android](https://github.com/openrz67/openrz67-android) and
[iOS](https://github.com/openrz67/openrz67-ios) apps work unchanged. **Not yet built or
flashed on hardware.**

| File | What |
|---|---|
| `src/main.c` | the application: GATT, advertising, shutter, countdown, LED, battery, sleep |
| `prj.conf` | Kconfig: Bluetooth peripheral, BAS, DIS, ADC, GPIO, RC 32 kHz clock, no serial |
| `debug.conf` | add-on: logging over Segger RTT |
| `boards/openrz67/openrz67_nrf/` | the board: pin map (devicetree), SoC, flash runners |

## Behaviour

- Power on (or a button press from sleep): advertises as `OpenRZ67` for 5 minutes. No
  connection in that time: System OFF (about 0.5 µA), the button wakes it.
- Connected: stays on as long as the app holds the link. After a disconnect it advertises
  5 minutes again, then sleeps.
- Commands on the command characteristic, write without response:
  - 1 byte `button * 10 + state`: button 1 trigger, 2 bulb, 3 countdown; state 1 start, 0 stop.
  - 3 bytes `[3, seconds, state]`: countdown with its duration.
- Trigger: S1 on, 10 ms, S2 on, 100 ms, both off. Bulb: S1 then S2 on until stop. Countdown:
  fast LED blink, then a trigger.
- LED: solid while the shutter is held or for 2 s after a trigger, fast blink in a
  countdown, a short blink every 2 s while advertising, off when connected and idle.
- Battery: VDD measured on the internal ADC channel every 60 s; mV on the custom
  characteristic (uint16 LE, notify), percent on the Battery Service, linear 2.5 to 3.0 V.

## Pins

| Function | nRF52840 | Module pad |
|---|---|---|
| S1 PhotoMOS LED | P0.09 | 41 |
| S2 PhotoMOS LED | P0.10 | 43 |
| Status LED | P0.00 | 11 |
| Button, to GND | P0.30 | 10 |
| SWDIO / SWCLK | | 37 / 39, `J2` pads 2 / 3 |

The module has no 32 kHz crystal, so the low-frequency clock runs from the calibrated RC
oscillator. P0.09/P0.10 are NFC pins set to GPIO.

## Build and flash

Needs the nRF Connect SDK (west, Zephyr SDK). From an NCS workspace:

```sh
west build -b openrz67_nrf -s /path/to/openrz67-trigger/nrf52/firmware -d build
west build -b openrz67_nrf -s ... -- -DEXTRA_CONF_FILE=debug.conf   # with RTT logging
```

Flashing is over SWD. A Raspberry Pi Pico running Raspberry Pi's `debugprobe` firmware
(CMSIS-DAP) works through pyOCD; a J-Link through its own runner:

```sh
pip install pyocd && pyocd pack install nrf52840
west flash --runner pyocd
west flash --runner jlink
```

Wire the probe to `J2`: pad 1 VDD (reference voltage), 2 SWDIO, 3 SWCLK, 4 GND. There is no
reset pad; the probe resets the chip over SWD. Power the board from its cell while flashing,
or feed 3 V to pad 1.

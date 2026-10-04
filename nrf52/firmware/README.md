# Firmware for the nRF52 board (Zephyr / nRF Connect SDK)

Zephyr application for the coin-cell trigger in [`../kicad/`](../kicad/). Same Bluetooth
services and command bytes as the ESP32-C3 firmware in the repository root, so the
[Android](https://github.com/openrz67/openrz67-android) and
[iOS](https://github.com/openrz67/openrz67-ios) apps work unchanged. Builds with nRF Connect
SDK v3.4.1 (119 kB flash, 24 kB RAM); not yet flashed on hardware.

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
  5 minutes again (started from the `recycled` connection callback), then sleeps.
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
| S1 PhotoMOS LED, high drive | P0.09 | 41 |
| S2 PhotoMOS LED, high drive | P0.10 | 43 |
| Status LED | P0.00 | 11 |
| Button, to GND (SENSE, no GPIOTE channel) | P0.30 | 10 |
| SWDIO / SWCLK | | 37 / 39, `J2` pins 4 / 3 |

The module has no 32 kHz crystal, so the low-frequency clock runs from the calibrated RC
oscillator. P0.09/P0.10 are NFC pins set to GPIO.

## Build and flash

Needs the nRF Connect SDK (west workspace) and the Zephyr SDK toolchain. One-time setup, as
done on the development Mac:

```sh
brew install cmake ninja dtc
uv venv --python 3.12 ~/ncs/.venv && uv pip install -p ~/ncs/.venv west
cd ~/ncs && source .venv/bin/activate
west init -m https://github.com/nrfconnect/sdk-nrf --mr v3.4.1 . && west update --narrow -o=--depth=1
uv pip install -p .venv -r zephyr/scripts/requirements.txt -r nrf/scripts/requirements-build.txt
# Zephyr SDK 1.0.1 (zephyr/SDK_VERSION): minimal bundle + the arm toolchain into gnu/, then setup.sh -h -c
```

Build (the board lives in this directory, so pass it as `BOARD_ROOT`; no sysbuild, there is
no bootloader):

```sh
cd ~/ncs && source .venv/bin/activate && export ZEPHYR_SDK_INSTALL_DIR=~/zephyr-sdk-1.0.1
FW=/path/to/openrz67-trigger/nrf52/firmware
west build --no-sysbuild -b openrz67_nrf -s $FW -d $FW/build -- -DBOARD_ROOT=$FW
west build --no-sysbuild -b openrz67_nrf -s $FW -d $FW/build -- -DBOARD_ROOT=$FW -DEXTRA_CONF_FILE=debug.conf   # RTT logging
```

The image is `build/zephyr/zephyr.hex`.

Flashing is over SWD through `J2`, a JST SH 1.0 mm connector: a Qwiic / STEMMA QT cable with
female Dupont ends goes straight onto a Raspberry Pi Pico 2 WH (pre-soldered headers) running
Raspberry Pi's `debugprobe_on_pico2.uf2` (CMSIS-DAP; `debugprobe_on_pico.uf2` on a Pico H),
no soldering anywhere. pyOCD drives it; a
J-Link works through its own runner:

```sh
pip install pyocd && pyocd pack install nrf52840
west flash -d $FW/build --runner pyocd
west flash -d $FW/build --runner jlink
```

| `J2` pin | Qwiic wire | Pico pin |
|---|---|---|
| 1 GND | black | GND (pin 3) |
| 2 VDD | red | not connected; the board runs from its cell while flashing. Never feed power into this pin, it would charge the CR2032 |
| 3 SWCLK | blue | GP2 (pin 4) |
| 4 SWDIO | yellow | GP3 (pin 5) |

There is no reset line; the probe resets the chip over SWD.

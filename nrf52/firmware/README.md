# Firmware for the nRF52 board (Zephyr / nRF Connect SDK)

Zephyr application for the coin-cell trigger in [`../kicad/`](../kicad/). Same Bluetooth
services and command bytes as the ESP32-C3 firmware in the repository root, so the
[Android](https://github.com/openrz67/openrz67-android) and
[iOS](https://github.com/openrz67/openrz67-ios) apps work unchanged. Builds with nRF Connect
SDK v3.4.1 (MCUboot 39 kB, app 147 kB flash, 45 kB RAM); not yet flashed on hardware.

| File | What |
|---|---|
| `src/main.c` | the application: GATT, advertising, shutter, countdown, LED, battery, sleep |
| `prj.conf` | Kconfig: Bluetooth peripheral, BAS, DIS, SMP (updates), ADC, GPIO, HFINT calibration, no serial |
| `sysbuild.conf`, `sysbuild/mcuboot.conf` | MCUboot as the bootloader, fed watchdog during a swap |
| `debug.conf` | add-on: logging over Segger RTT |
| `boards/openrz67/openrz67_nrf/` | the board: pin map (devicetree), SoC, flash runners |

## Behaviour

- Power on (or a button press from sleep): advertises as `OpenRZ67` for 5 minutes. No
  connection in that time: System OFF (about 0.7 µA), the button wakes it.
- Connected: stays on as long as the app holds the link. After a disconnect it advertises
  5 minutes again (started from the `recycled` connection callback), then sleeps.
- Button held 3 s: off. It disconnects the app, waits for the button to be released (a held
  button would wake it again at once) and goes to System OFF. A press wakes it.
- Commands on the command characteristic, write without response:
  - 1 byte `button * 10 + state`: button 1 trigger, 2 bulb, 3 countdown; state 1 start, 0 stop.
  - 3 bytes `[3, seconds, state]`: countdown with its duration.
- Trigger: S1 on, 10 ms, S2 on, 100 ms, both off. Bulb: S1 then S2 on until stop or a
  disconnect. Countdown: fast LED blink, then a trigger.
- Watchdog: 5 s. A hung main loop resets the chip, which releases S1/S2.
- LED: solid while the shutter is held or for 2 s after a trigger, fast blink in a
  countdown, a short blink every 2 s while advertising, off when connected and idle.
- Battery: VDD measured on the internal ADC channel every 60 s; mV on the custom
  characteristic (uint16 LE, notify), percent on the Battery Service, linear 2.5 to 3.0 V.

## Pins

| Function | nRF54L15 | Module pad |
|---|---|---|
| S1 PhotoMOS LED, high drive | P2.04 | 27 |
| S2 PhotoMOS LED, high drive | P2.05 | 28 |
| Status LED | P2.00 | 18 |
| Button, to GND (SENSE, latch detect, no GPIOTE channel) | P1.04 | 7 |
| SWCLK / SWDIO | | 11 / 12, `J2` pins 3 / 4 |

Both crystals (32 MHz, 32.768 kHz) are inside the module. Ebyte does not give their load
capacitance; the devicetree uses the nRF54L15 DK values. At boot the firmware asks the chip
whether the module has the DC/DC inductor and turns DC/DC on if so (about half the radio
current); otherwise it stays on the LDO.

Chip anomalies handled: 114 (a bouncing button on a SENSE pin can leave ~300 µA on in idle;
`latch-detect` on the port), 30 (HFINT drifts in the cold and GRTC wake-ups fail;
`CONFIG_CLOCK_CONTROL_NRF_HFINT_CALIBRATION`).

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

Build (the board lives in this directory, so pass it as `BOARD_ROOT`). Sysbuild builds
MCUboot and the app and signs the app:

```sh
cd ~/ncs && source .venv/bin/activate && export ZEPHYR_SDK_INSTALL_DIR=~/zephyr-sdk-1.0.1
FW=/path/to/openrz67-trigger/nrf52/firmware
KEY=~/.openrz67/mcuboot-ed25519.pem
west build -b openrz67_nrf/nrf54l15/cpuapp -s $FW -d $FW/build -- -DBOARD_ROOT=$FW -DSB_CONFIG_BOOT_SIGNATURE_KEY_FILE=\"$KEY\"
west build -b openrz67_nrf/nrf54l15/cpuapp -s $FW -d $FW/build -- -DBOARD_ROOT=$FW -DSB_CONFIG_BOOT_SIGNATURE_KEY_FILE=\"$KEY\" -DEXTRA_CONF_FILE=debug.conf   # RTT logging
```

MCUboot only boots images signed with the key it was built with. Make the key once, outside
the repository, and keep a backup: without it, updates need the probe again.

```sh
mkdir -p ~/.openrz67 && ~/ncs/.venv/bin/python ~/ncs/bootloader/mcuboot/scripts/imgtool.py keygen -t ed25519 -k ~/.openrz67/mcuboot-ed25519.pem
```

Without `SB_CONFIG_BOOT_SIGNATURE_KEY_FILE` the build uses MCUboot's public test key (with a
warning), and anyone could sign an image the board accepts.

Outputs: `build/merged.hex` (MCUboot + app, for the probe) and `build/dfu_application.zip`
(app only, for an update over Bluetooth).

### Update over Bluetooth

Once MCUboot is on the board, the app updates from a phone. Close the OpenRZ67 app first, the
board takes one connection.

1. Copy `build/dfu_application.zip` to the phone.
2. Wake the board (button) so it advertises.
3. In nRF Connect Device Manager (Nordic, iOS and Android): pick `OpenRZ67`, Image, Firmware
   Upgrade, select the zip, mode "Test and Confirm", Start.

The board restarts into the new image. If that image does not come back on Bluetooth, MCUboot
falls back to the old one on the next reset.

### First flash with the probe

Flashing is over SWD through `J2`, a JST SH 1.0 mm connector: a Qwiic / STEMMA QT cable with
female Dupont ends goes straight onto a Raspberry Pi Pico 2 WH (pre-soldered headers) running
Raspberry Pi's `debugprobe_on_pico2.uf2` (CMSIS-DAP; `debugprobe_on_pico.uf2` on a Pico H),
no soldering anywhere. pyOCD drives it; a
J-Link works through its own runner:

```sh
pip install 'pyocd>=0.37'    # nrf54l target built in, no pack
west flash -d $FW/build --runner pyocd
west flash -d $FW/build --runner jlink
```

| `J2` pin | Qwiic wire | Pico pin |
|---|---|---|
| 1 GND | black | GND (pin 3) |
| 2 VDD | red | 3V3(OUT) (pin 36), with the cell **out**: the probe powers the board, so both sides run at 3.3 V. Never with the cell in, it would charge the CR2032 |
| 3 SWCLK | blue | GP2 (pin 4) |
| 4 SWDIO | yellow | GP3 (pin 5) |

There is no reset line; the probe resets the chip over SWD.

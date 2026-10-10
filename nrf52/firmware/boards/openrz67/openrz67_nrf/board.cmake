# Raspberry Pi Pico running debugprobe (CMSIS-DAP) through pyOCD, or a J-Link.
#   west flash --runner pyocd
#   west flash --runner jlink
board_runner_args(pyocd "--target=nrf54l" "--frequency=4000000")
board_runner_args(jlink "--device=nRF54L15_M33" "--speed=4000")
include(${ZEPHYR_BASE}/boards/common/pyocd.board.cmake)
include(${ZEPHYR_BASE}/boards/common/jlink.board.cmake)

"""Single source of truth for the nRF52 trigger board: parts, placement, nets, routing.

gen_pcb.py builds the board from it with pcbnew, gen_sch.py writes the schematic.
Coordinates are board mm, origin top-left, y down. rot is KiCad degrees (CCW on screen).
"""

LIB = "openrz67-nrf"
BOARD_W, BOARD_H, BOARD_R = 31.0, 30.0, 0.8

# ref: (footprint, value, lcsc, mpn, manufacturer, layer, x, y, rot, description)
PARTS = {
    "U1": ("WIRELM-SMD_E73-2G4M08S1C", "E73-2G4M08S1C", "C356849", "E73-2G4M08S1C", "Ebyte",
           "F", 8.0, 11.3, 180, "nRF52840 module, PCB antenna at the board edge"),
    "BT1": ("BAT-SMD_MY-2032-16", "CR2032", "C2902340", "MY-2032-16", "MYOUNG",
            "B", 15.5, 18.0, 0, "CR2032 holder, SMD clip, on the back"),
    "J1": ("CONN-SMD_4P-P1.00_SM04B-SRSS-TB-LF-SN", "Camera", "C160404", "SM04B-SRSS-TB(LF)(SN)", "JST",
           "F", 22.0, 26.8, 0, "SH 1.0 mm side-entry SMD (Qwiic cable fits): 1 GND, 2 NC, 3 S1, 4 S2"),
    "U2": ("SMD-4_L4.6-W3.7-P2.54-LS7.0-BR", "TLP172AM", "C2152276", "TLP172AM(TPL,E)", "TOSHIBA",
           "F", 20.0, 10.0, 90, "PhotoMOS relay, S1"),
    "U3": ("SMD-4_L4.6-W3.7-P2.54-LS7.0-BR", "TLP172AM", "C2152276", "TLP172AM(TPL,E)", "TOSHIBA",
           "F", 25.0, 10.0, 90, "PhotoMOS relay, S2"),
    "R1": ("R0402", "330Ω", "C25104", "0402WGF3300TCE", "UNI-ROYAL",
           "F", 21.27, 4.0, 0, "S1 LED series, 5 mA at 3.0 V"),
    "R2": ("R0402", "330Ω", "C25104", "0402WGF3300TCE", "UNI-ROYAL",
           "F", 25.84, 4.0, 0, "S2 LED series"),
    "R3": ("R0402", "1kΩ", "C11702", "0402WGF1001TCE", "UNI-ROYAL",
           "F", 12.4, 28.0, 270, "status LED series"),
    "C1": ("C1206", "100uF", "C15008", "CL31A107MQHNNNE", "Samsung",
           "F", 29.3, 10.0, 90, "cell bulk at the clip terminal, carries radio and LED peaks"),
    "C2": ("C0402", "100nF", "C77020", "GRM155R71H104KE14D", "muRata",
           "F", 9.27, 20.3, 0, "VDD decoupling at the module"),
    "J2": ("SWD_1x04_P2.54", "SWD", "", "", "",
           "F", 8.2, 25.5, 0, "SWD pads: 1 VDD, 2 SWDIO, 3 SWCLK, 4 GND"),
    "SW1": ("KEY-SMD_B3U-1000PM", "B3U-1000P", "C231329", "B3U-1000P", "OMRON",
            "F", 6.0, 28.5, 0, "wake / user button"),
    "D1": ("LED0603-RD", "LED", "C2286", "KT-0603R", "KENTO",
           "F", 10.4, 28.6, 0, "status LED, red"),
}

# E73 pads -> nRF52840 GPIO. Only outer-row pads: inner pads cannot be routed out on F.Cu.
BTN_PAD, LED_PAD = "10", "11"          # P0.30 (last pad of the left column), P0.00/XL1 (first of the bottom row)
S1_DRV_PAD, S2_DRV_PAD = "41", "43"   # P0.09, P0.10 (NFC pins as GPIO)

NETS = {
    "VDD": [("BT1", "1"), ("BT1", "2"), ("U1", "19"), ("U1", "23"), ("C1", "1"), ("C2", "1"), ("J2", "1")],
    "GND": [("BT1", "3"), ("U1", "5"), ("U1", "21"), ("U1", "24"), ("C1", "2"), ("C2", "2"),
            ("J2", "4"), ("SW1", "2"), ("D1", "1"), ("U2", "2"), ("U3", "2")],
    "S1_DRV": [("U1", S1_DRV_PAD), ("R1", "1")],
    "S1_LED": [("R1", "2"), ("U2", "1")],
    "S2_DRV": [("U1", S2_DRV_PAD), ("R2", "1")],
    "S2_LED": [("R2", "2"), ("U3", "1")],
    "LED_DRV": [("U1", LED_PAD), ("R3", "1")],
    "LED_A": [("R3", "2"), ("D1", "2")],
    "BTN": [("U1", BTN_PAD), ("SW1", "1")],
    "SWDIO": [("U1", "37"), ("J2", "2")],
    "SWCLK": [("U1", "39"), ("J2", "3")],
    "S1": [("U2", "4"), ("J1", "3")],
    "S2": [("U3", "4"), ("J1", "4")],
    "CAM_GND": [("U2", "3"), ("U3", "3"), ("J1", "1")],
}

# copper-free band under the module antenna (both layers)
ANTENNA_KEEPOUT = (0.0, 0.0, 16.5, 3.8)  # x0, y0, x1, y1

T = 0.16   # signal
P = 0.25   # power
# (net, layer, width, [(x, y), ...])
TRACKS = [
    # VDD: left clip via -> module VDD pads (19, 23) + C2 + SWD pad 1
    ("VDD", "B", P, [(4.05, 19.5), (4.05, 20.3)]),
    ("VDD", "F", P, [(4.05, 20.3), (4.05, 21.2), (11.17, 21.2), (11.17, 18.31)]),
    ("VDD", "F", P, [(8.72, 21.2), (8.72, 20.3), (8.63, 18.31)]),
    ("VDD", "F", P, [(4.39, 21.2), (4.39, 24.4)]),
    # VDD: both clip feet tied on the back, below the cell pad, and the right foot -> C1
    ("VDD", "B", 0.3, [(4.05, 19.5), (4.05, 25.2), (26.95, 25.2), (26.95, 20.3)]),
    ("VDD", "B", P, [(26.95, 18.5), (28.0, 19.3)]),
    ("VDD", "F", P, [(28.0, 19.3), (29.3, 18.0), (29.3, 11.59)]),
    # GND stubs
    ("GND", "F", T, [(9.81, 20.3), (9.9, 18.31)]),
    ("GND", "F", T, [(9.6, 28.6), (8.1, 28.6)]),
    # SWD
    ("SWDIO", "F", T, [(14.5, 8.1), (15.75, 8.1), (15.75, 23.3), (6.93, 23.3), (6.93, 24.4)]),
    ("SWCLK", "F", T, [(14.5, 6.83), (16.05, 6.83), (16.05, 23.7), (9.47, 23.7), (9.47, 24.4)]),
    # button and LED down the left side
    ("BTN", "F", T, [(1.5, 15.72), (1.5, 28.5), (4.3, 28.5)]),
    ("LED_DRV", "F", T, [(3.55, 18.31), (3.55, 19.3), (3.1, 19.8), (3.1, 26.9), (12.4, 26.9), (12.4, 27.57)]),
    ("LED_A", "F", T, [(12.4, 28.43), (11.2, 28.6)]),
    # PhotoMOS drive
    ("S1_DRV", "F", T, [(14.5, 5.56), (16.2, 5.56), (17.2, 4.9), (19.7, 4.9), (20.3, 4.0), (20.84, 4.0)]),
    ("S1_LED", "F", T, [(21.7, 4.0), (21.27, 5.3), (21.27, 6.5)]),
    ("S2_DRV", "F", T, [(14.5, 4.29), (16.6, 4.29), (17.9, 2.3), (24.3, 2.3), (25.41, 3.4), (25.41, 4.0)]),
    ("S2_LED", "F", T, [(26.27, 4.0), (26.27, 6.5)]),
    # camera side, isolated from GND
    ("S1", "F", P, [(21.27, 13.5), (21.27, 15.0), (22.5, 16.5), (22.5, 24.1)]),
    ("S2", "F", P, [(26.27, 13.5), (26.27, 16.0), (23.5, 18.8), (23.5, 24.1)]),
    ("CAM_GND", "F", P, [(23.73, 13.5), (23.73, 11.5), (18.73, 11.5), (18.73, 13.5), (18.73, 15.5), (20.5, 17.3), (20.5, 24.1)]),
]
# (net, x, y)
VIAS = [
    ("VDD", 4.05, 20.3),
    ("VDD", 28.0, 19.3),
    ("GND", 12.01, 24.2),
    ("GND", 6.0, 22.3),
    ("GND", 7.7, 29.3),
    ("GND", 29.3, 7.6),
]

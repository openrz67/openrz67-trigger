"""Single source of truth for the nRF52 trigger board: parts, placement, nets, routing.

gen_pcb.py builds the board from it with pcbnew, gen_sch.py writes the schematic.
Coordinates are board mm, origin top-left, y down. rot is KiCad degrees (CCW on screen).
"""

LIB = "openrz67-nrf"
BOARD_W, BOARD_H, BOARD_R = 29.5, 29.0, 0.8

# ref: (footprint, value, lcsc, mpn, manufacturer, layer, x, y, rot, description)
PARTS = {
    "U1": ("WIRELM-SMD_E73-2G4M08S1F", "E73-2G4M08S1F", "C54337734", "E73-2G4M08S1F", "Ebyte",
           "F", 7.0, 11.2, 0, "nRF54L15 module, PCB antenna at the board edge"),
    "BT1": ("BAT-SMD_MY-2032-16", "CR2032", "C2902340", "MY-2032-16", "MYOUNG",
            "B", 13.5, 18.0, 0, "CR2032 holder, SMD clip, on the back"),
    "J1": ("CONN-SMD_4P-P1.00_SM04B-SRSS-TB-LF-SN", "Camera", "C160404", "SM04B-SRSS-TB(LF)(SN)", "JST",
           "F", 23.6, 24.7, 0, "SH 1.0 mm side-entry SMD (Qwiic cable fits): 1 GND, 2 NC, 3 S1, 4 S2"),
    "U2": ("SMD-4_L4.6-W3.7-P2.54-LS7.0-BR", "TLP172AM", "C2152276", "TLP172AM(TPL,E)", "TOSHIBA",
           "F", 18.6, 10.0, 90, "PhotoMOS relay, S1"),
    "U3": ("SMD-4_L4.6-W3.7-P2.54-LS7.0-BR", "TLP172AM", "C2152276", "TLP172AM(TPL,E)", "TOSHIBA",
           "F", 23.0, 10.0, 90, "PhotoMOS relay, S2"),
    "R1": ("R0402", "220Ω", "C25091", "0402WGF2200TCE", "UNI-ROYAL",
           "F", 19.87, 4.0, 0, "S1 LED series, 4 mA at 2.7 V"),
    "R2": ("R0402", "220Ω", "C25091", "0402WGF2200TCE", "UNI-ROYAL",
           "F", 23.84, 4.0, 0, "S2 LED series"),
    "R3": ("R0402", "1kΩ", "C11702", "0402WGF1001TCE", "UNI-ROYAL",
           "F", 17.4, 25.4, 270, "status LED series, about 1 mA: it shares the GPIO budget with R1/R2"),
    "C1": ("C1206", "100uF", "C15008", "CL31A107MQHNNNE", "Samsung",
           "F", 26.5, 17.0, 270, "cell bulk at the clip terminal, ahead of Q1 (ceramic, a reversed cell does not hurt it)"),
    "C2": ("C0402", "100nF", "C1525", "CL05B104KO5NNNC", "Samsung",
           "F", 9.27, 20.3, 0, "VDD decoupling at Q1 and the SWD connector"),
    "C3": ("C0402", "100nF", "C1525", "CL05B104KO5NNNC", "Samsung",
           "F", 1.85, 18.45, 90, "VDD decoupling at module pad 9, GND straight to pad 10"),
    "Q1": ("SOT-23", "AO3401A", "C15127", "AO3401A", "Alpha & Omega Semicon",
           "F", 5.4, 21.3, 90, "reverse-cell block: D on the clip, S on VDD, G on GND"),
    "J2": ("CONN-SMD_4P-P1.00_SM04B-SRSS-TB-LF-SN", "SWD", "C160404", "SM04B-SRSS-TB(LF)(SN)", "JST",
           "F", 12.3, 24.7, 0, "SWD, SH 1.0 mm side-entry (Qwiic cable to the probe): 1 GND, 2 VDD, 3 SWCLK, 4 SWDIO"),
    "SW1": ("KEY-SMD_B3U-1000PM", "B3U-1000P", "C231329", "B3U-1000P", "OMRON",
            "F", 6.0, 27.6, 0, "wake / user button"),
    "D1": ("LED0603-RD", "LED", "C2286", "KT-0603R", "KENTO",
           "F", 18.2, 27.6, 180, "status LED, red"),
}

# E73-2G4M08S1F pads -> nRF54L15 GPIO. The left column faces the board edge, so only a
# track squeezed past the module edge leaves it.
# The button must be on P0/P1: P2 cannot wake the chip from System OFF. P2 is fine for outputs.
BTN_PAD, LED_PAD = "7", "18"          # P1.04, P2.00
S1_DRV_PAD, S2_DRV_PAD = "27", "28"   # P2.04, P2.05
U1_GND = [("U1", p) for p in ("10", "30", "31", "37", "38", "39", "40")]

NETS = {
    "VBAT": [("BT1", "1"), ("BT1", "2"), ("C1", "1"), ("Q1", "3")],
    "VDD": [("Q1", "2"), ("U1", "9"), ("C2", "1"), ("C3", "1"), ("J2", "2")],
    "GND": [("Q1", "1"), ("BT1", "3"), *U1_GND, ("C1", "2"), ("C2", "2"), ("C3", "2"),
            ("J2", "1"), ("SW1", "2"), ("D1", "1"), ("U2", "2"), ("U3", "2")],
    "S1_DRV": [("U1", S1_DRV_PAD), ("R1", "1")],
    "S1_LED": [("R1", "2"), ("U2", "1")],
    "S2_DRV": [("U1", S2_DRV_PAD), ("R2", "1")],
    "S2_LED": [("R2", "2"), ("U3", "1")],
    "LED_DRV": [("U1", LED_PAD), ("R3", "1")],
    "LED_A": [("R3", "2"), ("D1", "2")],
    "BTN": [("U1", BTN_PAD), ("SW1", "1")],
    "SWCLK": [("U1", "11"), ("J2", "3")],
    "SWDIO": [("U1", "12"), ("J2", "4")],
    "S1": [("U2", "4"), ("J1", "3")],
    "S2": [("U3", "4"), ("J1", "4")],
    "CAM_GND": [("U2", "3"), ("U3", "3"), ("J1", "1")],
}

# Silkscreen text. The back labels sit in the free strip between the front edge and the cell:
# the cell's + side faces away from the board. The connector names tell the two identical SH
# connectors apart (their footprints carry the pin-1 dots).
# (text, layer, x, y, height)
SILK = [
    ("CR2032  + SIDE OUT", "B", 14.75, 4.0, 1.2),
    ("OpenRZ67 nRF rev A", "B", 14.75, 1.9, 1.0),
    ("CAM", "F", 23.6, 20.9, 1.0),
    ("SWD", "F", 12.3, 20.9, 1.0),
]

# copper-free band under the module antenna (both layers)
ANTENNA_KEEPOUT = (0.0, 0.0, 15.0, 5.3)  # x0, y0, x1, y1
# B.Cu ring under the rim of the CR2032 (its + can wraps over the edge): no copper of any
# kind there, so a scraped mask cannot short the cell. Inside the ring only GND lives,
# the same potential as the cell face that rests on it.
CELL_KEEPOUT = (13.5, 18.0, 7.5, 10.2)  # cx, cy, r_in, r_out

T = 0.16   # signal
P = 0.25   # power
# (net, layer, width, [(x, y), ...])
TRACKS = [
    # VBAT: left clip via -> Q1 drain; Q1 source -> C2, SWD pin 2 and, down the left edge, module pad 9
    ("VBAT", "B", P, [(3.0, 19.5), (3.0, 20.3)]),
    ("VBAT", "F", P, [(3.0, 20.3), (5.4, 20.3)]),
    ("GND", "F", P, [(4.45, 22.6), (3.8, 22.8)]),
    ("VDD", "F", P, [(1.85, 15.05), (0.85, 15.05), (0.85, 18.995), (0.85, 23.5), (6.35, 23.5), (6.35, 22.24)]),
    ("VDD", "F", P, [(0.85, 18.995), (1.85, 18.995)]),
    ("GND", "F", P, [(1.85, 16.35), (1.85, 17.905)]),
    ("VDD", "F", P, [(6.35, 22.24), (6.35, 21.0), (7.0, 20.3), (8.72, 20.3)]),
    ("VDD", "F", P, [(8.72, 20.3), (8.72, 21.2), (11.8, 21.2), (11.8, 22.76)]),
    # VBAT: both clip feet tied on the back, above the cell pad; right foot -> C1
    ("VBAT", "B", 0.3, [(1.5, 17.0), (1.5, 6.5), (24.95, 6.5), (24.95, 15.8)]),
    ("VBAT", "B", P, [(24.95, 14.1), (26.5, 14.1)]),
    ("VBAT", "F", P, [(26.5, 14.1), (26.5, 15.41)]),
    ("GND", "F", T, [(26.5, 18.59), (26.5, 21.0)]),
    # SWD: bottom-row pads 11/12 nest above the VDD run to J2
    ("SWDIO", "F", T, [(4.25, 16.35), (4.25, 17.95), (13.8, 17.95), (13.8, 22.76)]),
    ("SWCLK", "F", T, [(3.15, 16.35), (3.15, 18.3), (12.8, 18.3), (12.8, 22.76)]),
    # button down the left edge, outside VDD; LED above the SWD run
    ("BTN", "F", T, [(1.85, 12.85), (0.45, 12.85), (0.45, 27.6), (4.3, 27.6)]),
    ("LED_DRV", "F", T, [(10.85, 16.35), (10.85, 17.6), (16.3, 17.6), (16.3, 24.97), (17.4, 24.97)]),
    ("LED_A", "F", T, [(17.4, 25.83), (17.4, 27.6)]),
    # PhotoMOS drive, around the antenna keepout corner
    ("S1_DRV", "F", T, [(12.15, 7.35), (15.4, 7.35), (15.9, 6.85), (15.9, 5.6), (16.5, 5.0), (18.4, 5.0), (19.0, 4.0), (19.44, 4.0)]),
    ("S1_LED", "F", T, [(20.3, 4.0), (19.87, 5.3), (19.87, 6.5)]),
    ("S2_DRV", "F", T, [(12.15, 6.05), (15.0, 6.05), (16.6, 4.45), (17.9, 2.3), (22.3, 2.3), (23.41, 3.4), (23.41, 4.0)]),
    ("S2_LED", "F", T, [(24.27, 4.0), (24.27, 6.5)]),
    # camera side, isolated from GND
    ("S1", "F", P, [(19.87, 13.5), (19.87, 15.0), (21.8, 17.6), (21.8, 19.5), (24.1, 21.8), (24.1, 22.76)]),
    ("S2", "F", P, [(24.27, 13.5), (24.27, 14.3), (25.1, 15.1), (25.1, 22.76)]),
    ("CAM_GND", "F", P, [(21.73, 13.5), (21.73, 11.5), (17.33, 11.5), (17.33, 13.5), (17.33, 15.5), (19.8, 18.7), (19.8, 20.5), (22.1, 22.76)]),
]
# (net, x, y)
VIAS = [
    ("VBAT", 3.0, 20.3),
    ("VBAT", 26.5, 14.1),     # off C1 and the clip foot, so no solder wicks down it
    ("GND", 19.8, 28.3),
    ("GND", 3.8, 22.8),
    ("GND", 7.0, 19.7),    # ties the GND disc under the cell to the top; C2's GND pad reaches it
    ("GND", 21.0, 5.2),    # back-side GND north of the VDD loop, under the module
    ("GND", 20.8, 8.8),    # back-side GND between the VDD loop and the cell ring
    ("GND", 4.0, 9.0),     # under the module, inside its pad ring, off the cell rim ring
    ("GND", 9.5, 8.0),
    ("GND", 3.8, 13.5),
    ("GND", 10.5, 14.0),
    ("GND", 6.8, 26.5),      # beside SW1, not in its pad; outside the cell rim
    ("GND", 26.5, 21.0),
]

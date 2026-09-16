# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d>=0.11.1"]
# ///
"""openrz67-trigger enclosure (build123d).

Two-part snap-fit box for the OpenRZ67 trigger PCB rev 2 (../pcb/kicad/), stacked:
the LiPo cell lies flat under the PCB (foam between), the PCB sits on tall posts,
in a low rib pocket on the floor, and open pockets in front of and behind the board
take the battery lead and fingers. Dimensions come from the KiCad board and its footprints — see README.md.

Parts: base (tub), lid (telescoping ship-lap edge), lid_text (colour-2 inlay),
lightpipe (clear filament).
Print orientation: base floor-down; lid upside-down (the debossed top text
faces the bed — the lid_text inlay is a separate part on filament 2, so the
letters print flat on the bed in the contrast colour, no bridge, no slicer paint);
lightpipe head-down. No supports.

Coordinate system: case coords, origin at the outer box's front-left-bottom
corner, Y toward the back. bx()/by() map board coords into case coords. Board
coords here are the enclosure's: origin at the board's front-left corner, Y
toward the back — the KiCad board measures Y from the other long edge, so
board_y_here = 22 - kicad_y (the two mounting holes are (2,2) and (46,20)).

Run (exports STLs to stl/ and checks the assertions):
    uv run openrz67_case.py

Closure: snap-fit — four cantilever fingers cut free in the lid tongue (two per
long wall) carry a bead that clicks into a pocket in the base lip; the walls
themselves stay rigid (no screws, no heat-set inserts). The PCB is located by two
Ø1.85 pins in its real mounting holes and pressed down by the lid bosses. Open the
lid with a coin in the pry slot on the back wall.

U4 camera cable: the side-entry XH header and its plug stay INSIDE the box; only
the (heat-shrunk) cable leaves through a keyhole slot in the lid's right wall, open
down to the seam, so the cable drops in as the lid closes.

Env overrides: PCB_T, LID_TEXT_SHOW (default true), and
SNAP_TEST=true to also export a cropped corner pair for tuning snap_bead /
lap_gap with a small test print before committing to the full box.
"""

import os
from pathlib import Path

from build123d import *

# --- Board (rev 2, from ../pcb/kicad/) ---------------------------------------
board_w, board_h, board_r = 48.0, 22.0, 2.0
pcb_t = float(os.environ.get("PCB_T", 1.6))
mount_holes = [(2, 2), (46, 20)]     # the real Ø2 holes (board coords)
hole_d = 2.0                         # their diameter
pin_d = hole_d - 0.15                # locating pins: light friction fit in the FR4 holes (was -0.3:
                                     # the PCB rattled during install; a printed pin comes out ~+0.05)
pcb_supports = [(2, 20), (46, 2)]    # solid posts in the screwless corners
pcb_overhang_left = 2.0              # USB-C shell protrudes past the board edge
# U4 camera connector: side-entry S4B-XH-A on the right edge, mouth facing out. Its
# body reaches xh_mouth past the pin row (F.Fab outline), i.e. 5.5 mm past the board
# edge; the mated XHP-4 plug sticks xh_plug_proud further. Both stay inside the box.
xh_x, xh_y, xh_mouth = 44.3, 22 - 11.0, 9.2         # pin row (board), pins -> mouth face
xh_w, xh_h, xh_back, xh_clr = 12.4, 6.1, 2.3, 0.4   # body width, height, pins -> rear face
xh_plug_proud, xh_slack = 2.5, 1.5   # plug rear past the mouth (estimate, measure!); air to the wall
cable_d, cable_clr = 5.0, 0.5        # heat-shrunk 4-wire bundle; slot = cable_d + 2 * cable_clr
# TH solder tails below the PCB: [board_x, board_y, relief_dia] (BAT1 pins)
th_keepouts = [(3.275, 16.189, 3.2), (3.275, 18.189, 3.2)]
th_keepout_depth = 3.5                # PH tails are 3.5 mm (CONN-TH_PH2.00-LI-2P.wrl); pocket reaches the floor
# Component bodies above the PCB the lid bosses must clear: (x0, y0, x1, y1)
comp_keepouts = [(0.0, 4.0, 8.0, 14.5),   # USB-C connector body
                 (xh_x - xh_back - xh_clr, xh_y - xh_w / 2 - xh_clr,
                  xh_x + xh_mouth + xh_plug_proud, xh_y + xh_w / 2 + xh_clr)]
#                ^ U4 body + plug vs the (46,20) hold-down boss (0.3 mm apart nominally)

# --- PCB frame (guide fins on both long edges, reaching across the pockets) ---
frame_clr, frame_proud, frame_cham = 0.2, 0.6, 0.4
frame_rib_l, frame_notch_clr = 8.0, 0.3
frame_ribs_front, frame_ribs_back = [20, 32], [20, 32]  # fin centres in board-X
#   mid-edge, clear of the snap fingers (near the corners) and the lead pocket (back-left)

# --- Fit and walls ----------------------------------------------------------
clr, wall, floor_t, lid_top_t = 0.4, 3.2, 2.0, 2.0   # wall 3.2: lap halves 1.6 (rigid; the fingers flex)
lid_top_r = 2.0                      # 45° chamfer round the lid's top edge (softens the box). Bed-side
#   edge when the lid prints upside-down: a chamfer prints clean, a fillet's first layers overhang > 45°.
pocket_front, pocket_back = 2.0, 4.0  # open air beside the board's long edges: fingers / battery lead
#   (3 / 5 until 2026-09-14; the lead now just crosses the low battery rib)

# --- Vertical stack ---------------------------------------------------------
standoff_h = 8.0                     # cell 6 + foam 1.5 + 0.5 solder/vias under the bare PCB bottom.
#   The BAT1 tails (th_keepouts, board-X ~3.3) lie LEFT of the cell (batt_x0 = 6), so they
#   need no room over it — asserted below. Was 11 (tails counted over the cell) until 2026-09-14.
h_usbc, h_ph_plug = 3.3, 8.0         # USB-C shell; PHR-2 plug + wire bend in the top-entry
#                                      PH headers (BAT1, S3) — the tallest thing on rev 2

# --- Battery: cell flat under the PCB, lengthwise, in a low rib pocket + foam tape ---
batt_w, batt_l, batt_t = 31, 20, 6.0
batt_x0, batt_foam = 6.0, 1.5        # board-X of the cell's left end (between the posts); foam under the tails
batt_clr, batt_rib_t, batt_rib_h = 0.5, 1.6, 2.5   # pocket fit; rib ring on the floor around the cell
#   (as the old battery-beside bay had). Low: the cell may still swell; the lead simply
#   crosses the rib at the left end — the pockets beside the board give it room.

# --- Openings ---------------------------------------------------------------
usb_open_w, usb_open_h, usb_open_r = 10.0, 4.6, 1.8     # lip the cable body stops against; clears the
#   plug's metal shell (8.34 x 2.56) by ~0.8 / 1.0 with the PCB located on pins. Was 11 x 7 R2
#   until 2026-09-15 (a lot of dead room around the receptacle mouth).
usb_recess_w, usb_recess_h, usb_recess_r = 13.0, 9.0, 3.0   # inner: room for the receptacle shell
usb_recess_d = 1.0                   # the mouth sits 0.4 inside the wall's inner face; this is slack
# Outer pocket the plug's overmold sinks into (protects the port, guides the plug in, and
# brings the overmold 1.2 closer to the mouth — the old Fusion case had one, 2026-09-14).
# Fits overmolds up to 13 x 8.5; a 45° bevel of usb_pocket_ch on its outer edge.
usb_pocket_w, usb_pocket_h, usb_pocket_r, usb_pocket_d, usb_pocket_ch = 14.0, 9.5, 3.0, 1.2, 0.6
assert wall - usb_pocket_d - usb_recess_d >= 0.8, "USB lip between the outer pocket and the inner recess too thin"
# The pocket straddles the seam. Below it the base wall is normally only the outer lap half
# (wall/2 = 1.6), so the pocket left a 0.4 skin there and the lip looked thin/ragged on the base
# side (first print, 2026-09-15). Around the USB the base keeps its FULL wall down through the
# lap zone and the lid tongue is notched to match -> the lip is wall - pocket - recess on both sides.
usb_solid_w = usb_pocket_w + 2 * 1.5   # width of that full-wall zone (case-Y)
led_pos = [(20.5, 18.0), (24.224, 20.186)]                 # D3 (charge), D4 (status)
led_win_l, led_win_w, led_win_r = 6.0, 4.4, 1.2   # covers both LED bodies (D3 sits 2.2 mm lower than D4)
led_head_lip, led_head_t, led_pipe_clr, led_pipe_gap = 0.7, 1.4, 0.2, 0.8   # gap 0.8: 0603 LED is ~0.5 tall; closer stem = less light lost sideways (2026-09-16)
# The head seat is a TAPER (funnel), not a step: lid prints upside-down, so a stepped
# counterbore hangs a 1 mm ledge over the bed-side opening -> support crud, ragged edge
# (first stacked print, 2026-09-14). A wall 0.7 out over 1.4 up is 26.6° from vertical:
# under the slicer's 30° support threshold, so nothing gets supported, nothing sags.

# --- FPC antenna (Ebyte TX2400-FPC-2509, 25 x 9 x ~0.2, adhesive, U.FL to A1) -------------
# Stuck to the lid CEILING in the free band between the switch body (front) and the LED
# stem (back): furthest from the cell (metal pouch) and 10 mm over the PCB ground. A shallow
# recess locates it; the cable (~100 mm) drops to A1 near the USB end and coils in the air
# over the board. The lid prints upside-down, so the recess is a pocket in the print's top face.
ant_l, ant_w, ant_clr, ant_depth = 25.0, 9.0, 0.3, 0.3
ant_cx_frac = 0.25   # along the free band (0 = left boss end, 1 = right wall): nearer A1, short cable run

# --- Rocker switch KCD11 (front wall, snap-in, 2.8 mm tabs wired to S3) ----------------
# Replaced the SS12F15 slide switch + screw pillars 2026-09-14: nothing soldered on the
# switch (crimped 2.8 mm receptacles), no screws (spring latches on the body's long sides).
# Vendor drawings disagree by ~0.5 mm — MEASURE the switch at hand before printing.
kcd_body_l, kcd_body_h = 13.5, 8.5   # body behind the flange (X, Z) = the panel cutout, nominal
kcd_hole_clr = 0.3                   # per side; snap-in wants a snug hole
kcd_flange_l, kcd_flange_h = 15.0, 10.0   # bezel, sits proud on the OUTSIDE of the wall
kcd_depth = 10.0                     # flange underside -> body rear (Y)
kcd_tab_l, kcd_tab_pitch = 5.0, 7.0  # 2.8 mm tabs past the body rear; tab centre spacing (X)
kcd_conn_l, kcd_conn_w = 3.0, 4.0    # receptacle past the tab tip: flag (90°) type. A straight
#   insulated FDFN 1.25-110 reaches ~12 past the tip and runs into the S3 plug / light pipe.
kcd_panel_t = 2.0                    # panel the latches grip: the wall is pocketed from INSIDE to this
kcd_gap = 1.6                        # body underside over the PCB (U1 0.9 beneath); also the wall
#   strip left between the hole and the seam
kcd_latch_clr = 1.2                  # free inner wall past the hole edges, where the latches spring out

# --- Snap closure: cantilever fingers in the lid tongue -------------------------
snap_bead = 0.55   # how far the bead on a finger sticks out (0.45 held too loosely, 2026-09-14)
bead_h = 1.4       # bead height
pocket_extra_d, pocket_extra_h = 0.15, 0.3   # base pocket deeper / taller than the bead (lead-in; slop = h/2)
bead_ch_in, bead_ch_out, pocket_ch = 0.4, 0.15, 0.2  # click-in ramp / retention face / pocket ceiling chamfers
finger_l, finger_t, finger_slot = 12.0, 1.0, 0.8   # finger length, thickness (thinned from inside), relief slot
snap_fingers_x = [13.0, 51.0]        # finger centres (case-X), front AND back wall, near the corners
holddown_d = 5.0   # lid bosses that press the PCB onto the posts
pin_proud = 0.8    # locating pins stand this far above the PCB top
pry_w, pry_d, pry_h = 12.0, 1.0, 1.2   # coin slot in the lid's lower edge, back wall

# --- Ship-lap edge / orientation mark / lid text -----------------------------
lap, lap_gap = 7.0, 0.15             # lap <= split_z - floor_t; 7 mm fingers, bead near the tip -> ~2 % strain
orient_mark_x, orient_mark_w, orient_mark_d, orient_mark_h = 8.0, 2.5, 0.8, 9.0
# Debossed (pocket) text in the lid top, per the FDM rules: prints upside-down
# against the bed (crisp), and one filament change at Z = lid_text_depth colours
# the letters. Nameplate lockup below the LED window: the name, then a small tracked
# all-caps subtitle, both centred on the lid's X (the LED is off-centre) and the block
# centred between the LED seat and the front edge. A thin debossed RAIL runs across the
# LED row, broken around the light-pipe seat: the off-centre LED then reads as an
# indicator sitting on a line, not as a hole that missed the middle. Futura Bold (macOS
# system font; OCCT warns and falls back to Arial if it is missing). Restyled 2026-09-14:
# the old Arial "OpenRZ67" / "Trigger" pair had uneven weights and a wide gap.
# (text, font size, letter tracking)
lid_text_show = os.environ.get("LID_TEXT_SHOW", "true") == "true"
lid_font = "Futura"
lid_texts = [("OpenRZ67", 9.5, 0.0), ("TRIGGER", 5.0, 1.0)]
lid_text_gap, lid_text_min_stroke = 1.6, 0.6   # between lines; pockets narrower than this smear
lid_rail_w, lid_rail_end, lid_rail_gap = 0.9, 6.0, 1.5   # rail width, inset from the side walls, air to the LED seat
lid_text_depth = 0.6              # pocket depth = the inlay thickness (3 x 0.2 layers).
                                  # Three layers so the second colour is opaque: the inlay prints
                                  # FIRST, flat against the bed, and the body colour would ghost
                                  # through a single layer.
eps = 0.01

# --- Derived ------------------------------------------------------------------
pcb_overhang_right = xh_x + xh_mouth + xh_plug_proud + xh_slack - board_w - clr
inner_w = board_w + 2 * clr + pcb_overhang_left + pcb_overhang_right
inner_h = pocket_front + clr + board_h + clr + pocket_back
off_y = wall + pocket_front + clr
inner_r = board_r + clr
outer_w, outer_h, outer_r = inner_w + 2 * wall, inner_h + 2 * wall, inner_r + wall
standoff_d = 4.0
comp_clr = max(max(h_ph_plug, xh_h) + 2.0,   # +2: room for the battery lead's loop into BAT1
               kcd_gap + kcd_body_h + 2 * kcd_hole_clr + kcd_latch_clr)   # rocker + latch room under the ceiling
pcb_z = floor_t + standoff_h
pcb_top_z = pcb_z + pcb_t
split_z = pcb_top_z
lid_h = comp_clr + lid_top_t
total_h = split_z + lid_h
bead_z = split_z - lap + 1.1            # bead centre: near the finger tip (long lever, low strain)
assert lap <= split_z - floor_t, "lid lip would reach the floor"
assert lid_top_r <= min(wall, lid_top_t) and lid_top_r < inner_r + wall, "lid top chamfer too big"
assert split_z - lap <= bead_z - bead_h / 2 and bead_z + (bead_h + pocket_extra_h) / 2 < split_z, \
    "snap bead/pocket outside the lap zone"
# Printability: the lap halves must slice as real perimeters (0.4 mm nozzle:
# a two-line freestanding wall 0.87 mm)
assert wall / 2 - (snap_bead + pocket_extra_d) >= 0.87, "base lip behind the snap pocket under two lines"
assert wall / 2 - lap_gap >= 0.87, "lid tongue under two perimeter lines"
assert 0.87 <= finger_t <= wall / 2 - lap_gap, "snap finger thickness"
assert standoff_h >= batt_t + batt_foam - 1e-6, "no foam room over the cell"
for _kx, _ky, _kd in th_keepouts:   # tails beside the cell, not over it (else add th_keepout_depth)
    assert _kx + _kd / 2 <= batt_x0 - batt_clr or _kx - _kd / 2 >= batt_x0 + batt_w + batt_clr, \
        "THT tails over the cell: standoff_h must include th_keepout_depth"


def bx(x):
    return wall + clr + pcb_overhang_left + x


def by(y):
    return off_y + y


led_cx = (bx(led_pos[0][0]) + bx(led_pos[1][0])) / 2
led_cy = (by(led_pos[0][1]) + by(led_pos[1][1])) / 2
sx = outer_w / 2                     # switch centred on the lid (board-X ~27.5)
swz = split_z + kcd_gap + kcd_body_h / 2 + kcd_hole_clr   # switch body centre, case-Z

# --- Helpers -------------------------------------------------------------------
def rrect(w, h, r, x0=0.0, y0=0.0):
    """Rounded rectangle with min-corner at (x0, y0)."""
    return Pos(x0 + w / 2, y0 + h / 2) * RectangleRounded(w, h, r)


def prism(sk, z0, h):
    return extrude(Plane.XY.offset(z0) * sk, amount=h)


def xprism(sk, x0, length):
    """Extrude a YZ-plane sketch (local x -> case Y, local y -> case Z) along +X."""
    return extrude(Plane.YZ.offset(x0) * sk, amount=length)


def box(x0, y0, z0, dx, dy, dz):
    return Pos(x0, y0, z0) * Box(dx, dy, dz, align=Align.MIN)


def cyl(x, y, z0, d, h):
    return Pos(x, y, z0) * Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


outer_sk = rrect(outer_w, outer_h, outer_r)
inner_sk = rrect(inner_w, inner_h, inner_r, wall, wall)
mid_sk = rrect(inner_w + wall, inner_h + wall, inner_r + wall / 2, wall / 2, wall / 2)

# --- Shared cuts -----------------------------------------------------------------
# USB-C (left wall): 10x4.6 R1.8 through-cut (plug shell only) whose outer edge is the
# cable-body lip, plus a 13x9x1 inner recess so the receptacle shell pokes into the wall
# and the mouth reaches the lip. Straddles the split -> cut from BOTH base and lid.
usb_cy, usb_zc = by(22 - 13.259), pcb_top_z + h_usbc / 2
cut_usb = xprism(Pos(usb_cy, usb_zc) * RectangleRounded(usb_open_w, usb_open_h, usb_open_r),
                 -1, wall + 2)
cut_usb += xprism(Pos(usb_cy, usb_zc) * RectangleRounded(usb_recess_w, usb_recess_h, usb_recess_r),
                  wall - usb_recess_d, usb_recess_d + 1)
cut_usb += xprism(Pos(usb_cy, usb_zc) * RectangleRounded(usb_pocket_w, usb_pocket_h, usb_pocket_r),
                  -1, usb_pocket_d + 1)
# Bevelled lead-in: a frustum that is pocket + 2*ch at the outer face, shrinking at 45° inward
cut_usb += extrude(Plane.YZ.offset(-1) * Pos(usb_cy, usb_zc) * RectangleRounded(
    usb_pocket_w + 2 * (usb_pocket_ch + 1), usb_pocket_h + 2 * (usb_pocket_ch + 1), usb_pocket_r + usb_pocket_ch + 1),
    amount=usb_pocket_ch + 1, taper=45)

# Camera cable slot (right wall): header + plug stay inside; the cable leaves at its
# natural height (header centre, xh_h/2 above the PCB) through a keyhole in the lid
# wall — round top of slot_w, open straight down through the tongue to the seam, so
# the cable drops in as the lid closes and the lid lifts off untethered.
xh_cy = by(xh_y)
cable_zc = split_z + xh_h / 2
slot_w = cable_d + 2 * cable_clr
cut_cable = xprism(Pos(xh_cy, cable_zc) * Circle(slot_w / 2), outer_w - wall - 1, wall + 2)
cut_cable += box(outer_w - wall - 1, xh_cy - slot_w / 2, split_z - lap - eps,
                 wall + 2, slot_w, cable_zc - (split_z - lap) + eps)

# Frame-fin tongue notches (cut from the lid tongue where the base fins stand)
fin_ycap = off_y - frame_clr
cut_fin_notches = Part() + [
    box(bx(cx) - frame_rib_l / 2 - frame_notch_clr, y0, split_z - lap - eps,
        frame_rib_l + 2 * frame_notch_clr, fin_ycap + 2 * frame_notch_clr, lap + 2 * eps)
    for cxs, y0 in ((frame_ribs_front, -frame_notch_clr),
                    (frame_ribs_back, outer_h - fin_ycap - frame_notch_clr))
    for cx in cxs
]

# Snap finger bands (case-X range of each finger) on the front (y = 0) and back wall
finger_bands = [(fx - finger_l / 2, fx + finger_l / 2) for fx in snap_fingers_x]
for fx0, fx1 in finger_bands:
    for cx in frame_ribs_front + frame_ribs_back:
        n0, n1 = bx(cx) - frame_rib_l / 2 - frame_notch_clr, bx(cx) + frame_rib_l / 2 + frame_notch_clr
        assert fx1 + finger_slot <= n0 or fx0 - finger_slot >= n1, "snap finger overlaps a fin notch"


def orient_mark_rib(z0):
    """Half of the front-wall orientation rib (base: lower, lid: upper). The halves
    line up only when the lid is on the right way around. Overlaps 0.2 into the wall."""
    return box(bx(orient_mark_x) - orient_mark_w / 2, -orient_mark_d, z0,
               orient_mark_w, orient_mark_d + 0.2, orient_mark_h / 2)


# --- BASE ---------------------------------------------------------------------------
base = prism(outer_sk, 0, split_z)
base -= prism(inner_sk, floor_t, total_h)                    # cavity
usb_zone = box(-1, usb_cy - usb_solid_w / 2, split_z - lap - 1, wall + 2, usb_solid_w, lap + 1)
base -= prism(mid_sk, split_z - lap, lap + 1) - usb_zone     # rabbet: outer wall half only, full wall at the USB

# Posts at the mount holes with Ø1.85 locating pins into the real PCB holes (straight
# through the board, then a cone down to Ø1.4 above it as lead-in), plus solid posts
# in the other corners
import math as _m
pin_taper = _m.degrees(_m.atan((pin_d - 1.4) / 2 / pin_proud))
for hx, hy in mount_holes:
    base += cyl(bx(hx), by(hy), floor_t, standoff_d, standoff_h)
    base += cyl(bx(hx), by(hy), pcb_z - eps, pin_d, pcb_t + eps)
    base += extrude(Plane.XY.offset(pcb_top_z) * Pos(bx(hx), by(hy)) * Circle(pin_d / 2),
                    amount=pin_proud, taper=pin_taper)
for px, py in pcb_supports:
    base += cyl(bx(px), by(py), floor_t, standoff_d, standoff_h)

# Guide fins on both long edges: thick wall-backed fin reaching across the pocket to
# the board edge + thin chamfered lead-in lip above the board top. One YZ profile
# extruded along X. (build123d: keep the polygon CCW, or it extrudes toward -X.)
def fin_profile(yw, s):
    pts = [(yw, floor_t), (yw + s * fin_ycap, floor_t),
           (yw + s * fin_ycap, split_z + frame_proud - frame_cham),
           (yw + s * wall, split_z + frame_proud), (yw + s * wall, split_z), (yw, split_z)]
    return Polygon(*(pts if s > 0 else pts[::-1]), align=None)

for cxs, yw, s in ((frame_ribs_front, 0.0, 1), (frame_ribs_back, outer_h, -1)):
    for cx in cxs:
        base += xprism(fin_profile(yw, s), bx(cx) - frame_rib_l / 2, frame_rib_l)

base += orient_mark_rib(split_z - orient_mark_h / 2)

# Snap pockets in the base lip, only where the lid fingers are: slightly longer,
# taller and deeper than the bead (lead-in). The ceiling keeps a flat retention face;
# only its outer edge is chamfered (pocket_ch) — a 0.5 mm ledge prints fine floor-down.
def finger_boxes(margin, z0, h):
    return Part() + [box(fx0 - margin, -1, z0, fx1 - fx0 + 2 * margin, outer_h + 2, h)
                     for fx0, fx1 in finger_bands]

groove = prism(offset(mid_sk, snap_bead + pocket_extra_d) - offset(mid_sk, -lap_gap - 0.25),
               split_z - lap - eps, bead_z + (bead_h + pocket_extra_h) / 2 - (split_z - lap) + eps) & finger_boxes(0.5, 0, total_h)
base -= chamfer(groove.edges().group_by(Axis.Z)[-1].filter_by(Axis.X), pocket_ch)
# Battery pocket: a low rib ring on the floor around the cell (merges with the posts
# and fins it touches). Locates the cell so the foam tape is not the only thing.
batt_ring = box(bx(batt_x0) - batt_clr - batt_rib_t, by((board_h - batt_l) / 2) - batt_clr - batt_rib_t,
                floor_t - eps, batt_w + 2 * (batt_clr + batt_rib_t), batt_l + 2 * (batt_clr + batt_rib_t),
                batt_rib_h + eps)
batt_ring -= box(bx(batt_x0) - batt_clr, by((board_h - batt_l) / 2) - batt_clr, floor_t - 2 * eps,
                 batt_w + 2 * batt_clr, batt_l + 2 * batt_clr, batt_rib_h + 3 * eps)
base += batt_ring
# TH solder-tail pockets in the post tops (BAT1 pins beside the (2,20) post)
for kx, ky, kd in th_keepouts:
    base -= cyl(bx(kx), by(ky), pcb_z - th_keepout_depth, kd, th_keepout_depth + eps)
base -= cut_usb

# --- LID ----------------------------------------------------------------------------
lid = prism(outer_sk, split_z, lid_h)                        # top + walls
lid = chamfer(lid.edges().group_by(Axis.Z)[-1], lid_top_r)   # chamfered top edge, before any cut
lid += prism(offset(mid_sk, -lap_gap) - inner_sk, split_z - lap, lap) - box(   # tongue, notched at the USB
    -1, usb_cy - usb_solid_w / 2 - lap_gap, split_z - lap - 1, wall + 2, usb_solid_w + 2 * lap_gap, lap + 1)
# Snap beads on the fingers only. Bottom: a big click-in ramp. Top: a small chamfer so
# most of the bead is a flat retention face (a 45° top let the lid pull open too easily);
# the lid prints upside-down, so that face is a 0.4 mm ledge in mid-air — one line, fine.
# (The inner edges' chamfers end up buried in the tongue.)
bead = prism(offset(mid_sk, -lap_gap + snap_bead) - offset(mid_sk, -lap_gap - 0.4),
             bead_z - bead_h / 2, bead_h) & finger_boxes(0, 0, total_h)
bead = chamfer(bead.edges().group_by(Axis.Z)[0], bead_ch_in)
lid += chamfer(bead.edges().group_by(Axis.Z)[-1], bead_ch_out)
lid -= prism(inner_sk, split_z - lap - eps, comp_clr + lap + eps)       # cavity
# Cut the fingers free: a relief slot through the tongue at each end, and thin the
# finger from the cavity side to finger_t so it flexes instead of the wall.
for fx0, fx1 in finger_bands:
    for yin, yout in ((wall, wall / 2), (outer_h - wall, outer_h - wall / 2)):
        ya, yb = min(yin, yout), max(yin, yout)
        for x in (fx0 - finger_slot, fx1):
            lid -= box(x, ya - 0.5, split_z - lap - eps, finger_slot, yb - ya + 1, lap + eps)
        thin = wall / 2 - lap_gap - finger_t
        y0 = yin - thin if yin < yout else yin
        lid -= box(fx0, y0, split_z - lap - eps, fx1 - fx0, thin, lap + eps)

# Hold-down bosses over the mount holes (press the PCB onto the posts)
for hx, hy in mount_holes:
    lid += cyl(bx(hx), by(hy), pcb_top_z, holddown_d, (total_h - lid_top_t) - pcb_top_z)
lid += orient_mark_rib(split_z)

lid -= cut_usb
lid -= cut_cable
# LED light-pipe hole: straight stem window through the top plate + tapered head seat
# (top hat from above, flush top). led_head(clr) builds the funnel / the matching head.
import math
led_taper = math.degrees(math.atan(led_head_lip / led_head_t))
assert led_taper <= 28, f"light-pipe head taper {led_taper:.1f}° would get slicer support (30° threshold)"
assert led_head_t < lid_top_t, "light-pipe head seat goes through the top plate"

def led_head(clr, extra=0.0):
    """Frustum: stem-window size at z = total_h - led_head_t, growing to +2*lip at the top."""
    return extrude(Plane.XY.offset(total_h - led_head_t) * Pos(led_cx, led_cy) * RectangleRounded(
        led_win_l + clr, led_win_w + clr, led_win_r), amount=led_head_t + extra, taper=-led_taper)

lid -= prism(Pos(led_cx, led_cy) * RectangleRounded(
    led_win_l + led_pipe_clr, led_win_w + led_pipe_clr, led_win_r),
    total_h - lid_top_t - eps, lid_top_t + 2 * eps)
lid -= led_head(led_pipe_clr, eps)
# Antenna recess in the ceiling (band: right of the (2,2) boss, in front of the LED stem,
# behind the rocker body). The foil is flush with the ceiling; the rocker top is
# kcd_latch_clr + kcd_hole_clr under it, so only its plan footprint is kept clear.
ceiling_z = total_h - lid_top_t
band_x0 = bx(mount_holes[0][0]) + holddown_d / 2 + 0.5
band_x1 = outer_w - wall - 0.5
band_y0 = kcd_depth + 0.5   # behind the rocker body's rear face (tabs + receptacles sit lower)
band_y1 = led_cy - (led_win_w + led_pipe_clr) / 2 - 0.5
ant_L, ant_W = ant_l + 2 * ant_clr, ant_w + 2 * ant_clr
assert ant_L <= band_x1 - band_x0 and ant_W <= band_y1 - band_y0, \
    f"antenna recess {ant_L}x{ant_W} does not fit the free ceiling band {band_x1 - band_x0:.1f}x{band_y1 - band_y0:.1f}"
assert ant_depth <= lid_top_t - lid_text_depth - 0.8, "antenna recess + lid text leave the top plate too thin"
ant_x0 = band_x0 + (band_x1 - band_x0 - ant_L) * ant_cx_frac
ant_y0 = (band_y0 + band_y1 - ant_W) / 2
lid -= box(ant_x0, ant_y0, ceiling_z - eps, ant_L, ant_W, ant_depth + eps)
# Rocker switch: snap-in hole through the front wall + an inner pocket that thins the
# wall to kcd_panel_t around it (the latches grip that). Flange proud on the outside.
kcd_hole_l, kcd_hole_h = kcd_body_l + 2 * kcd_hole_clr, kcd_body_h + 2 * kcd_hole_clr
lid -= box(sx - kcd_hole_l / 2, -1, swz - kcd_hole_h / 2, kcd_hole_l, wall + 2, kcd_hole_h)
lid -= box(sx - kcd_hole_l / 2 - kcd_latch_clr, kcd_panel_t, swz - kcd_hole_h / 2 - kcd_latch_clr,
           kcd_hole_l + 2 * kcd_latch_clr, wall - kcd_panel_t + eps, kcd_hole_h + 2 * kcd_latch_clr)
# Blind recesses in the hold-down bosses for the locating pins (not through the
# top plate — the .scad's snap variant cut them through, leaving holes in the lid)
for hx, hy in mount_holes:
    lid -= cyl(bx(hx), by(hy), pcb_top_z - eps, 2.6, pin_proud + 0.7 + eps)
# Coin/fingernail pry slot in the lid's lower edge, back wall centre (over the
# back pocket — nothing behind it).
lid -= box(outer_w / 2 - pry_w / 2, outer_h - pry_d, split_z - eps,
           pry_w, pry_d + eps, pry_h + eps)
# Component keepouts (USB-C body vs the (2,2) hold-down boss)
for x0, y0, x1, y1 in comp_keepouts:
    lid -= box(bx(x0), by(y0), pcb_top_z - eps,
               x1 - x0, y1 - y0, (total_h - lid_top_t) - pcb_top_z + 2 * eps)
lid -= cut_fin_notches

def tracked_text(txt, size, tracking):
    """Text sketch with extra letter spacing: the font's own advances plus `tracking` per
    glyph (glyphs sorted by X, one face each — all-caps only). Zero: the plain Text."""
    sk = Text(txt, font=lid_font, font_size=size, font_style=FontStyle.BOLD)
    if not tracking:
        return sk
    faces = sorted(sk.faces(), key=lambda f: f.center().X)
    return Sketch([Pos(i * tracking, 0) * f for i, f in enumerate(faces)])

lid_text = None            # the inlay solid: exactly the pocket volume, printed in colour 2
if lid_text_show:
    text_cut = None
    recess_half = (led_win_w + 2 * led_head_lip + led_pipe_clr) / 2
    lines = [tracked_text(*t) for t in lid_texts]
    heights = [l.bounding_box().size.Y for l in lines]
    block_h = sum(heights) + lid_text_gap * (len(lines) - 1)
    y = (led_cy - recess_half) / 2 + block_h / 2     # block centre: between LED seat and front edge
    for (txt, *_), sk, h in zip(lid_texts, lines, heights):
        tb = sk.bounding_box()
        sk = Pos(outer_w / 2 - (tb.min.X + tb.max.X) / 2, y - h - tb.min.Y) * sk   # centre X, top at y
        tb = sk.bounding_box()
        assert tb.min.X > lid_top_r + 1 and tb.max.X < outer_w - lid_top_r - 1, f"'{txt}' too wide ({tb.size.X:.1f}mm)"
        assert tb.max.Y < led_cy - recess_half - 1, f"'{txt}' hits the LED seat"
        assert tb.min.Y > lid_top_r + 0.5, f"'{txt}' runs into the top-edge chamfer"
        # Printability: every stroke >= lid_text_min_stroke (shrinking a glyph by half of
        # it must neither split nor drop it). build123d 0.11's offset() crashes on glyphs
        # with holes, so shrink outer/inner wires by hand.
        for f in sk.faces():
            try:
                g = Face(f.outer_wire().offset_2d(-lid_text_min_stroke / 2))
                for w in f.inner_wires():
                    g = g.cut(Face(w.offset_2d(lid_text_min_stroke / 2)))
                n = len(g.faces()) if hasattr(g, "faces") else len(g)
            except Exception:   # the wire collapsed: stroke thinner than the offset
                n = 0
            assert n == 1, f"'{txt}' has strokes under {lid_text_min_stroke} mm (a glyph -> {n} faces)"
        c = prism(sk, total_h - lid_text_depth, lid_text_depth + eps)
        text_cut = c if text_cut is None else text_cut + c
        y -= h + lid_text_gap
    seat_half_l = (led_win_l + 2 * led_head_lip + led_pipe_clr) / 2
    for x0, x1 in ((lid_rail_end, led_cx - seat_half_l - lid_rail_gap),
                   (led_cx + seat_half_l + lid_rail_gap, outer_w - lid_rail_end)):
        c = box(x0, led_cy - lid_rail_w / 2, total_h - lid_text_depth, x1 - x0, lid_rail_w, lid_text_depth + eps)
        text_cut = c if text_cut is None else text_cut + c
    # The inlay is the pocket volume clipped BY the lid, so it fills the pockets exactly and
    # inherits the top-edge chamfer instead of standing proud of it. Slicing it as a second
    # part of the lid object (make_3mf.py) puts the colour on the PART, so it survives every
    # re-export -- unlike slicer colour painting, which the fresh mesh wipes, and unlike a
    # height-range modifier, which QIDI Studio cannot store. It also removes the bridge: the
    # letters now print flat on the bed instead of sagging over an open pocket (2026-09-16).
    lid_text = lid & text_cut
    lid -= text_cut

# --- LIGHT PIPE (clear filament, inserted from above as a top hat; the tapered head
# self-centres in the funnel and sits ~0.2 below flush with led_pipe_clr) --------------
lightpipe = led_head(0.0)
lightpipe += prism(Pos(led_cx, led_cy) * RectangleRounded(led_win_l, led_win_w, led_win_r),
                   pcb_top_z + led_pipe_gap, (total_h - led_head_t) - (pcb_top_z + led_pipe_gap) + eps)

# --- Assertions ------------------------------------------------------------------------
for name, p in (("base", base), ("lid", lid), ("lightpipe", lightpipe)):
    assert p.is_valid, f"{name}: invalid solid"

bb = base.bounding_box()
assert abs(bb.size.X - outer_w) < 1e-3, f"base X {bb.size.X}"
assert abs(bb.max.Y - outer_h) < 1e-3 and abs(bb.min.Y + orient_mark_d) < 1e-3, "base Y"
assert abs(bb.max.Z - (pcb_z + pcb_t + pin_proud)) < 1e-3, f"base Z {bb.max.Z}"  # pins on top
assert abs(lightpipe.bounding_box().max.Z - total_h) < 1e-3, "light pipe not flush with the top"
lb = lid.bounding_box()
assert abs(lb.min.Z - (split_z - lap)) < 1e-3 and abs(lb.max.Z - total_h) < 1e-3, "lid Z"
if lid_text is not None:
    assert lid_text.is_valid and lid_text.volume > 1e-3, "lid text inlay: empty or invalid"
    tb = lid_text.bounding_box()
    assert abs(tb.max.Z - total_h) < 1e-3, "inlay not flush with the lid top"
    assert tb.min.Z > total_h - lid_text_depth - 1e-3, "inlay deeper than the pocket"
    assert (lid & lid_text).volume < 1e-6, "inlay overlaps the lid (the two parts must not fight)"

# Holes must actually break through (a wrong axis gives the same volume):
def _open(solid, probe, what):
    v = (solid & probe).volume
    assert v < 1e-6, f"{what} blocked (probe volume {v:.3f})"

_open(base + lid, box(-0.5, usb_cy - 4.3, usb_zc - 1.5, wall + 1, 8.6, 3.0), "USB opening")   # plug shell + 0.25/0.2 slop
_open(base + lid, box(-0.5, usb_cy - usb_pocket_w / 2 + usb_pocket_r / 2, usb_zc - usb_pocket_h / 2 + usb_pocket_r / 2,
                      usb_pocket_d + 0.5, usb_pocket_w - usb_pocket_r, usb_pocket_h - usb_pocket_r), "USB plug pocket")
assert (base + lid & box(usb_pocket_d + 0.05, usb_cy - usb_pocket_w / 2, usb_zc - usb_pocket_h / 2, 0.5,
                         usb_pocket_w, usb_pocket_h)).volume > 0.5 * 0.5 * (usb_pocket_w * usb_pocket_h - usb_open_w * usb_open_h), \
    "USB lip behind the plug pocket missing"
_open(base + lid, box(bx(xh_x - xh_back), xh_cy - xh_w / 2, split_z + eps,
                      xh_mouth + xh_back + xh_plug_proud, xh_w, xh_h), "U4 body + plug inside the box")
_open(base + lid, xprism(Pos(xh_cy, cable_zc) * Circle(cable_d / 2), bx(xh_x + xh_mouth + xh_plug_proud),
                         outer_w), "camera cable out through the right wall")
assert bx(xh_x + xh_mouth + xh_plug_proud) <= outer_w - wall - xh_slack + 1e-6, "U4 plug hits the wall"
# Cell under the PCB (+ pocket fit): inside the rib ring, between the posts, under the THT tails
_open(base, box(bx(batt_x0) - batt_clr, by((board_h - batt_l) / 2) - batt_clr, floor_t + eps,
                batt_w + 2 * batt_clr, batt_l + 2 * batt_clr, batt_t), "cell under the PCB")
assert (base & box(bx(batt_x0) - batt_clr - batt_rib_t, by((board_h - batt_l) / 2) - batt_clr - batt_rib_t,
                   floor_t + eps, batt_w + 2 * (batt_clr + batt_rib_t), batt_l + 2 * (batt_clr + batt_rib_t),
                   batt_rib_h - eps)).volume > 0.9 * batt_ring.volume, "battery rib ring missing"
_open(lid, box(led_cx - 2, led_cy - 1, total_h - lid_top_t + eps, 4, 2, lid_top_t), "LED window")
_open(lid, box(ant_x0 + 0.05, ant_y0 + 0.05, ceiling_z - 0.5, ant_L - 0.1, ant_W - 0.1, 0.5 + ant_depth - 0.02),
      "antenna recess (and the air under it)")
assert (lid & box(ant_x0, ant_y0, ceiling_z + ant_depth + eps, ant_L, ant_W, lid_top_t - ant_depth - lid_text_depth - 2 * eps)
        ).volume > 0.99 * ant_L * ant_W * (lid_top_t - ant_depth - lid_text_depth - 2 * eps), "antenna recess breaks through the top plate"
for hx, hy in mount_holes:
    _open(lid, cyl(bx(hx), by(hy), pcb_top_z + eps, 2.0, pin_proud), "locating-pin recess")
# Rocker switch: hole through, latch pocket open, and the body + tabs + receptacles
# (over the PCB, under the ceiling) end in front of the light pipe and the S3 header
# (PH top-entry at board (28.71, 19.96), body 5.9 x 4.5 — the wires go there).
_open(lid, box(sx - kcd_body_l / 2, -0.5, swz - kcd_body_h / 2, kcd_body_l, wall + 1, kcd_body_h), "switch hole")
_open(lid, box(sx - kcd_hole_l / 2 - kcd_latch_clr + eps, kcd_panel_t + eps,
               swz - kcd_hole_h / 2 - kcd_latch_clr + eps, kcd_hole_l + 2 * kcd_latch_clr - 2 * eps,
               wall - kcd_panel_t - 2 * eps, kcd_hole_h + 2 * kcd_latch_clr - 2 * eps), "switch latch pocket")
assert swz - kcd_hole_h / 2 - kcd_latch_clr >= split_z - 1e-6, "switch latch pocket cuts into the lid tongue"
assert swz + kcd_hole_h / 2 + kcd_latch_clr <= total_h - lid_top_t + 1e-6, "switch latch pocket cuts the ceiling"
assert kcd_flange_h / 2 <= swz - split_z and swz + kcd_flange_h / 2 <= total_h - lid_top_r, \
    "switch flange over the seam / into the top chamfer"
_open(lid, box(sx - kcd_body_l / 2, wall + eps, swz - kcd_body_h / 2, kcd_body_l, kcd_depth - wall, kcd_body_h),
      "switch body inside the lid")
s3_x, s3_y, s3_l, s3_w = 28.71, 19.96, 5.9, 4.5
kcd_y_end = kcd_depth + kcd_tab_l + kcd_conn_l
pipe_y0 = led_cy - (led_win_w + 2 * led_head_lip + led_pipe_clr) / 2
assert kcd_y_end + 0.5 <= min(pipe_y0, by(s3_y - s3_w / 2)), \
    f"switch tabs + receptacles reach Y {kcd_y_end:.1f}: light pipe at {pipe_y0:.1f}, S3 plug at {by(s3_y - s3_w / 2):.1f}"
_open(lid, box(bx(0.5), by(4.5), pcb_top_z + eps, 7, 9.5, 2), "USB-C body keepout")
# J1 (1x4 2.54 mm header, DNP, pads at board x 34.4-42.0, y 1.4): no header envelope —
# the centred switch body ends at the first pad and its tabs run over the row. Flying leads.

# --- Export -------------------------------------------------------------------------------
if __name__ == "__main__":
    # Assembled preview in VS Code's OCP CAD Viewer, when it is open (port 3939).
    # Toggle part visibility in the viewer tree; show() does nothing/raises without it.
    import socket
    try:
        assert socket.socket().connect_ex(("127.0.0.1", 3939)) == 0  # VS Code OCP CAD Viewer open?
        from ocp_vscode import show   # uv run --with ocp_vscode openrz67_case.py
        show(base, lid, lightpipe, names=["base", "lid", "lightpipe"])
    except (AssertionError, ImportError):
        print("OCP-viewer ikke åpen (eller ocp_vscode mangler: uv run --with ocp_vscode), hopper over forhåndsvisning")
    out = Path(os.environ.get("OUTDIR", Path(__file__).resolve().parent / "stl"))
    out.mkdir(parents=True, exist_ok=True)
    parts = [("openrz67-base", base), ("openrz67-lid", lid), ("openrz67-lightpipe", lightpipe)]
    if lid_text is not None:
        parts.append(("openrz67-lid-text", lid_text))
    else:
        (out / "openrz67-lid-text.stl").unlink(missing_ok=True)   # LID_TEXT_SHOW=false: a stale
        # inlay would otherwise be sliced into a lid that no longer has pockets for it
    if os.environ.get("SNAP_TEST", "false") == "true":
        # Front-left corner crop of base + lid: one snap finger, a
        # locating pin and its boss. Print these first to tune snap_bead / lap_gap.
        crop = box(-2, -2, -1, 34, 24, total_h + 2)
        parts += [("openrz67-snaptest-base", base & crop), ("openrz67-snaptest-lid", lid & crop)]
    for name, p in parts:
        export_stl(p, str(out / f"{name}.stl"), ascii_format=True)  # make_3mf.py parses ASCII
        b = p.bounding_box()
        print(f"{name}: {b.size.X:.2f} x {b.size.Y:.2f} x {b.size.Z:.2f} mm, "
              f"{p.volume / 1000:.2f} cm3")
    print(f"STLs in {out}")
    if out.resolve() == Path(__file__).resolve().parent / "stl" and os.environ.get("MAKE_3MF", "true") == "true":
        import subprocess, sys
        here = Path(__file__).resolve().parent
        if (here / "bambu-template.3mf").exists():   # slicer project: swap all fresh STLs into the template
            subprocess.run([sys.executable, "make_3mf.py", "--stl-dir", str(out), "--out", "openrz67-case.3mf"], cwd=here, check=True)
            print("openrz67-case.3mf oppdatert")

# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d>=0.11.1"]
# ///
"""openrz67-trigger enclosure (build123d).

Two-part snap-fit box for the OpenRZ67 trigger PCB rev 2 (../pcb/kicad/), stacked:
the LiPo cell lies flat under the PCB (foam between), the PCB sits on tall posts,
and open pockets in front of and behind the board take the battery lead and
fingers. Dimensions come from the KiCad board and its footprints — see README.md.

Parts: base (tub), lid (telescoping ship-lap edge), lightpipe (clear filament).
Print orientation: base floor-down; lid upside-down (the debossed top text
faces the bed — filament change at Z = lid_text_depth colours the letters);
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
Ø1.7 pins in its real mounting holes and pressed down by the lid bosses. Open the
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
hole_d = 2.0                         # their diameter (locating pins are hole_d - 0.3)
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
pocket_front, pocket_back = 3.0, 5.0  # open air beside the board's long edges: fingers / battery lead

# --- Vertical stack ---------------------------------------------------------
standoff_h = 11.0                    # cell 6 + foam 1.5 + THT tails 3.5 (th_keepout_depth)
h_usbc, h_ph_plug = 3.3, 8.0         # USB-C shell; PHR-2 plug + wire bend in the top-entry
#                                      PH headers (BAT1, S3) — the tallest thing on rev 2

# --- Battery: cell flat under the PCB, lengthwise, fixed with foam tape ------
batt_w, batt_l, batt_t = 31, 20, 6.0
batt_x0, batt_foam = 6.0, 1.5        # board-X of the cell's left end (between the posts); foam under the tails

# --- Openings ---------------------------------------------------------------
usb_open_w, usb_open_h, usb_open_r = 11.0, 7.0, 2.0     # outer lip (stops the cable body)
usb_recess_w, usb_recess_h, usb_recess_r = 13.0, 9.0, 3.0
usb_recess_d = wall - 0.5            # keep a 0.5 lip so the plug still seats fully
led_pos = [(20.5, 18.0), (24.224, 20.186)]                 # D3 (charge), D4 (status)
led_win_l, led_win_w, led_win_r = 6.0, 4.4, 1.2   # covers both LED bodies (D3 sits 2.2 mm lower than D4)
led_head_lip, led_head_t, led_pipe_clr, led_pipe_gap = 1.0, 1.0, 0.2, 1.5

# --- Slide switch SS12F15 (front wall, wired to S3) --------------------------
sw_z = 4.8                           # body underside 1.3 mm over the PCB: clears U1 (0.9) by 0.4
sw_slot_l, sw_slot_h = 10.65, 6.3
sw_body_l, sw_body_h, sw_body_w, sw_body_clr = 11.0, 7.0, 8.0, 0.4
sw_screw_pitch, sw_screw_d = 15.0, 2.4
sw_boss_d, sw_boss_h, sw_boss_pilot, sw_boss_gap = 5.0, 5.0, 1.5, 1.5
sw_plate_w, sw_plate_h, sw_plate_t, sw_plate_clr = 19.45, 5.75, 0.4, 0.3

# --- Snap closure: cantilever fingers in the lid tongue -------------------------
snap_bead = 0.45   # how far the bead on a finger sticks out
bead_h = 1.4       # bead height; the base pocket is 0.5 taller and 0.25 deeper (lead-in)
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
# the letters. Badge layout below the LED window: "OpenRZ67", then "Trigger", both
# centred on the lid's X (the LED is off-centre). (text, cap size, Y offset from LED row)
lid_text_show = os.environ.get("LID_TEXT_SHOW", "true") == "true"
lid_texts = [("OpenRZ67", 8.0, -10.0), ("Trigger", 6.5, -18.5)]
lid_text_depth = 0.6              # pocket depth = the colour-change height (3 x 0.2 layers)
eps = 0.01

# --- Derived ------------------------------------------------------------------
pcb_overhang_right = xh_x + xh_mouth + xh_plug_proud + xh_slack - board_w - clr
inner_w = board_w + 2 * clr + pcb_overhang_left + pcb_overhang_right
inner_h = pocket_front + clr + board_h + clr + pocket_back
off_y = wall + pocket_front + clr
inner_r = board_r + clr
outer_w, outer_h, outer_r = inner_w + 2 * wall, inner_h + 2 * wall, inner_r + wall
standoff_d = 4.0
comp_clr = max(h_ph_plug, xh_h) + 2.0   # +2: room for the battery lead's loop into BAT1
pcb_z = floor_t + standoff_h
pcb_top_z = pcb_z + pcb_t
split_z = pcb_top_z
lid_h = comp_clr + lid_top_t
total_h = split_z + lid_h
bead_z = split_z - lap + 1.1            # bead centre: near the finger tip (long lever, low strain)
assert lap <= split_z - floor_t, "lid lip would reach the floor"
assert split_z - lap <= bead_z - bead_h / 2 and bead_z + (bead_h + 0.5) / 2 < split_z, \
    "snap bead/pocket outside the lap zone"
# Printability: the lap halves must slice as real perimeters (0.4 mm nozzle:
# a two-line freestanding wall 0.87 mm)
assert wall / 2 - (snap_bead + 0.25) >= 0.87, "base lip behind the snap pocket under two lines"
assert wall / 2 - lap_gap >= 0.87, "lid tongue under two perimeter lines"
assert 0.87 <= finger_t <= wall / 2 - lap_gap, "snap finger thickness"
assert standoff_h - th_keepout_depth - batt_t >= batt_foam - 1e-6, "no foam room between cell and THT tails"


def bx(x):
    return wall + clr + pcb_overhang_left + x


def by(y):
    return off_y + y


led_cx = (bx(led_pos[0][0]) + bx(led_pos[1][0])) / 2
led_cy = (by(led_pos[0][1]) + by(led_pos[1][1])) / 2
sx = outer_w / 2                     # switch centred on the lid (board-X ~27.5)
swz = split_z + sw_z                 # switch centre, case-Z

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


def ycyl(x, y0, z, d, length):
    """Cylinder along +Y (for the switch screws)."""
    return Pos(x, y0, z) * Rot(-90, 0, 0) * Cylinder(
        d / 2, length, align=(Align.CENTER, Align.CENTER, Align.MIN))


outer_sk = rrect(outer_w, outer_h, outer_r)
inner_sk = rrect(inner_w, inner_h, inner_r, wall, wall)
mid_sk = rrect(inner_w + wall, inner_h + wall, inner_r + wall / 2, wall / 2, wall / 2)

# --- Shared cuts -----------------------------------------------------------------
# USB-C (left wall): 11x7 R2 through-cut whose outer edge is the cable-body lip,
# plus a 13x9x1.5 inner recess so the receptacle shell pokes into the wall and the
# mouth reaches the outer face. Straddles the split -> cut from BOTH base and lid.
usb_cy, usb_zc = by(22 - 13.259), pcb_top_z + h_usbc / 2
cut_usb = xprism(Pos(usb_cy, usb_zc) * RectangleRounded(usb_open_w, usb_open_h, usb_open_r),
                 -1, wall + 2)
cut_usb += xprism(Pos(usb_cy, usb_zc) * RectangleRounded(usb_recess_w, usb_recess_h, usb_recess_r),
                  wall - usb_recess_d, usb_recess_d + 1)

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
base -= prism(mid_sk, split_z - lap, lap + 1)                # rabbet: outer wall half only

# Posts at the mount holes with Ø1.7 locating pins into the real PCB holes, plus
# solid posts in the other corners
for hx, hy in mount_holes:
    base += cyl(bx(hx), by(hy), floor_t, standoff_d, standoff_h)
    base += cyl(bx(hx), by(hy), pcb_z - eps, hole_d - 0.3, pcb_t + pin_proud + eps)
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
# taller and deeper than the bead (lead-in). The top edges are chamfered so the
# pocket ceiling prints as a ~45° ramp, not a 0.7 mm overhang (base prints floor-down).
def finger_boxes(margin, z0, h):
    return Part() + [box(fx0 - margin, -1, z0, fx1 - fx0 + 2 * margin, outer_h + 2, h)
                     for fx0, fx1 in finger_bands]

groove = prism(offset(mid_sk, snap_bead + 0.25) - offset(mid_sk, -lap_gap - 0.25),
               split_z - lap - eps, bead_z + (bead_h + 0.5) / 2 - (split_z - lap) + eps) & finger_boxes(0.5, 0, total_h)
base -= chamfer(groove.edges().group_by(Axis.Z)[-1].filter_by(Axis.X), 0.5)
# TH solder-tail pockets in the post tops (BAT1 pins beside the (2,20) post)
for kx, ky, kd in th_keepouts:
    base -= cyl(bx(kx), by(ky), pcb_z - th_keepout_depth, kd, th_keepout_depth + eps)
base -= cut_usb

# --- LID ----------------------------------------------------------------------------
lid = prism(outer_sk, split_z, lid_h)                        # top + walls
lid += prism(offset(mid_sk, -lap_gap) - inner_sk, split_z - lap, lap)   # tongue
# Snap beads on the fingers only, chamfered top and bottom: the lid prints upside-
# down, so an unchamfered bead starts as a ledge in mid-air; the ramps also ease
# click-in and coin-open. (The inner edges' chamfers end up buried in the tongue.)
bead = prism(offset(mid_sk, -lap_gap + snap_bead) - offset(mid_sk, -lap_gap - 0.4),
             bead_z - bead_h / 2, bead_h) & finger_boxes(0, 0, total_h)
bead_ends = bead.edges().group_by(Axis.Z)
lid += chamfer(bead_ends[0] + bead_ends[-1], 0.4)
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

# Switch screw bosses: rectangular pillars from sw_boss_gap above the PCB (clears
# Q1/C15 beneath) up into the ceiling; front face at the inner wall plane so the
# screw clamps bracket -> wall -> boss in compression.
for s in (-1, 1):
    lid += box(sx + s * sw_screw_pitch / 2 - sw_boss_d / 2, wall, split_z + sw_boss_gap,
               sw_boss_d, sw_boss_h, (total_h - lid_top_t + 1) - (split_z + sw_boss_gap))
# Hold-down bosses over the mount holes (press the PCB onto the posts)
for hx, hy in mount_holes:
    lid += cyl(bx(hx), by(hy), pcb_top_z, holddown_d, (total_h - lid_top_t) - pcb_top_z)
lid += orient_mark_rib(split_z)

lid -= cut_usb
lid -= cut_cable
# LED light-pipe hole: stem window through the top plate + head recess (flush top)
lid -= prism(Pos(led_cx, led_cy) * RectangleRounded(
    led_win_l + led_pipe_clr, led_win_w + led_pipe_clr, led_win_r),
    total_h - lid_top_t - eps, lid_top_t + 2 * eps)
lid -= prism(Pos(led_cx, led_cy) * RectangleRounded(
    led_win_l + 2 * led_head_lip + led_pipe_clr, led_win_w + 2 * led_head_lip + led_pipe_clr,
    led_win_r + led_head_lip),
    total_h - led_head_t, led_head_t + eps)
# Switch: actuator slot, flush bracket recess in the outer wall, screw holes,
# and the body-envelope keepout (the bosses give way over the body only)
lid -= box(sx - sw_slot_l / 2, -1, swz - sw_slot_h / 2, sw_slot_l, wall + 2, sw_slot_h)
lid -= box(sx - (sw_plate_w + sw_plate_clr) / 2, -0.5, swz - (sw_plate_h + sw_plate_clr) / 2,
           sw_plate_w + sw_plate_clr, sw_plate_t + 0.5, sw_plate_h + sw_plate_clr)
for s in (-1, 1):
    x = sx + s * sw_screw_pitch / 2
    lid -= ycyl(x, -1, swz, sw_screw_d, wall + 1)            # clearance through wall
    lid -= ycyl(x, wall - eps, swz, sw_boss_pilot, sw_boss_h + eps)  # pilot into boss
lid -= box(sx - sw_body_l / 2 - sw_body_clr, wall, swz - sw_body_h / 2 - sw_body_clr,
           sw_body_l + 2 * sw_body_clr, sw_body_w + eps, sw_body_h + 2 * sw_body_clr)
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

if lid_text_show:
    # Each line must stay on its own side of the LED head recess (half-height 2.6 in Y)
    recess_half = (led_win_w + 2 * led_head_lip + led_pipe_clr) / 2
    for txt, size, dy in lid_texts:
        sk = Pos(outer_w / 2, led_cy + dy) * Text(txt, font_size=size, font_style=FontStyle.BOLD)
        tb = sk.bounding_box()
        assert tb.min.X > 3 and tb.max.X < outer_w - 3, f"'{txt}' too wide ({tb.size.X:.1f}mm)"
        assert (tb.min.Y > led_cy + recess_half + 1 if dy > 0
                else tb.max.Y < led_cy - recess_half - 1), f"'{txt}' hits the LED recess"
        assert tb.min.Y > 2 and tb.max.Y < outer_h - 2, f"'{txt}' off the top face"
        lid -= prism(sk, total_h - lid_text_depth, lid_text_depth + eps)

# --- LIGHT PIPE (clear filament, inserted from above as a top hat) --------------------
lightpipe = prism(Pos(led_cx, led_cy) * RectangleRounded(
    led_win_l + 2 * led_head_lip, led_win_w + 2 * led_head_lip, led_win_r + led_head_lip),
    total_h - led_head_t, led_head_t)
lightpipe += prism(Pos(led_cx, led_cy) * RectangleRounded(led_win_l, led_win_w, led_win_r),
                   pcb_top_z + led_pipe_gap, (total_h - led_head_t) - (pcb_top_z + led_pipe_gap) + eps)

# --- Assertions ------------------------------------------------------------------------
for name, p in (("base", base), ("lid", lid), ("lightpipe", lightpipe)):
    assert p.is_valid, f"{name}: invalid solid"

bb = base.bounding_box()
assert abs(bb.size.X - outer_w) < 1e-3, f"base X {bb.size.X}"
assert abs(bb.max.Y - outer_h) < 1e-3 and abs(bb.min.Y + orient_mark_d) < 1e-3, "base Y"
assert abs(bb.max.Z - (pcb_z + pcb_t + pin_proud)) < 1e-3, f"base Z {bb.max.Z}"  # pins on top
lb = lid.bounding_box()
assert abs(lb.min.Z - (split_z - lap)) < 1e-3 and abs(lb.max.Z - total_h) < 1e-3, "lid Z"

# Holes must actually break through (a wrong axis gives the same volume):
def _open(solid, probe, what):
    v = (solid & probe).volume
    assert v < 1e-6, f"{what} blocked (probe volume {v:.3f})"

_open(base + lid, box(-0.5, usb_cy - 4, usb_zc - 2.5, wall + 1, 8, 5), "USB opening")
_open(base + lid, box(bx(xh_x - xh_back), xh_cy - xh_w / 2, split_z + eps,
                      xh_mouth + xh_back + xh_plug_proud, xh_w, xh_h), "U4 body + plug inside the box")
_open(base + lid, xprism(Pos(xh_cy, cable_zc) * Circle(cable_d / 2), bx(xh_x + xh_mouth + xh_plug_proud),
                         outer_w), "camera cable out through the right wall")
assert bx(xh_x + xh_mouth + xh_plug_proud) <= outer_w - wall - xh_slack + 1e-6, "U4 plug hits the wall"
# Cell under the PCB: between the posts, under the THT tails (foam on top)
_open(base, box(bx(batt_x0), by((board_h - batt_l) / 2), floor_t + eps, batt_w, batt_l, batt_t),
      "cell under the PCB")
_open(lid, box(led_cx - 2, led_cy - 1, total_h - lid_top_t + eps, 4, 2, lid_top_t), "LED window")
for hx, hy in mount_holes:
    _open(lid, cyl(bx(hx), by(hy), pcb_top_z + eps, 2.0, pin_proud), "locating-pin recess")
for s in (-1, 1):
    _open(lid, ycyl(sx + s * sw_screw_pitch / 2, eps, swz, 1.0, wall - 2 * eps), "switch screw")
# Fit-critical keepouts stay open (enforced as geometry, not eyeballed in preview):
_open(lid, box(sx - sw_body_l / 2, wall + eps, swz - sw_body_h / 2,
               sw_body_l, sw_body_w - 2 * eps, sw_body_h), "switch body envelope")
_open(lid, box(bx(0.5), by(4.5), pcb_top_z + eps, 7, 9.5, 2), "USB-C body keepout")
# J1 (1x4 2.54 mm header, DNP, pads at board x 34.4-42.0, y 1.4): no header envelope —
# the centred switch's right boss sits over it (2026-09-13). Solder flying leads instead.

# --- Export -------------------------------------------------------------------------------
if __name__ == "__main__":
    # Assembled preview in VS Code's OCP CAD Viewer, when it is open (port 3939).
    # Toggle part visibility in the viewer tree; show() does nothing/raises without it.
    import socket
    if socket.socket().connect_ex(("127.0.0.1", 3939)) == 0:  # VS Code OCP CAD Viewer open?
        from ocp_vscode import show
        show(base, lid, lightpipe, names=["base", "lid", "lightpipe"])
    else:
        print("OCP-viewer ikke åpen, hopper over forhåndsvisning")
    out = Path(os.environ.get("OUTDIR", Path(__file__).resolve().parent / "stl"))
    out.mkdir(parents=True, exist_ok=True)
    parts = [("openrz67-base", base), ("openrz67-lid", lid), ("openrz67-lightpipe", lightpipe)]
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

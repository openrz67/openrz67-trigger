# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d>=0.11.1"]
# ///
"""openrz67 nRF52 trigger enclosure (build123d).

Two-part snap-fit box for the coin-cell board in ../kicad/ (29.5 x 29 mm, CR2032 clip on
the back). The board rests on a ledge around the base cavity with the cell hanging below
it; the lid presses it down with four corner bosses. The lid carries a cantilever button
tab over SW1, a light pipe over D1 and the opening for the JST SH camera plug in its back
wall. The floor is flat and closed for velcro. Two hooks off the lid ceiling clip under the
board's side edges, so for a cell change the board comes off with the lid and the cell slides
out of the clip backwards: the lid tongue is open along the whole back wall.

Parts: base (tub), lid (telescoping tongue with four snap fingers on the side walls) and
light pipe (clear filament, glued into the lid). Print orientation: base floor-down, lid
upside-down, light pipe head-down. No supports.

Coordinate system: case coords, origin at the outer box's front-left-bottom corner.
Board coords are the KiCad coords of ../kicad/openrz67-nrf.kicad_pcb (origin top-left of
the board, Y down in KiCad = toward the back wall here). bx()/by() map them into case
coords. KiCad shows the board from above with the antenna at the top of the screen; with
the antenna at the front wall that view is turned 180 degrees, so board X runs right to
left in case coords (bx mirrors it) while board Y keeps its direction. Antenna end of the module at the front wall (board y = 0), camera connector mouth
at the back wall (board y = 29).

Run (exports STLs to stl/ and checks the assertions):
    uv run openrz67_nrf_case.py

Env overrides: PCB_T, OUTDIR (STL directory, default stl/), SNAP_TEST=true (also export a
cropped corner pair for tuning snap_bead / lap_gap), LID_TEXT_SHOW=false, LID_TEXT,
LID_TEXT_SIZE.
"""

import math
import os
from pathlib import Path

from build123d import *


def check(cond, msg):
    """Keepout / printability guard. Not `assert`: `python -O` would strip those."""
    if not cond:
        raise SystemExit(msg)


# --- Board (from ../kicad/tools/design.py) --------------------------------------------
board_w, board_h, board_r = 29.5, 29.0, 0.8
pcb_t = float(os.environ.get("PCB_T", "1.6"))
cell_c = (13.5, 18.0)                 # CR2032 centre (BT1), on the back
cell_d, cell_t = 20.0, 3.2
clip_l, clip_w, clip_h = 25.9, 9.4, 3.75   # MY-2032-16 clip incl. feet; highest point under the board
# From the clip's 3D model: within 2.5 mm of the board only the two solder legs (pad 2 height)
# are there; the strap and its contact dimples take the lowest clip_strap_h.
clip_leg_w, clip_strap_h = 5.0, 1.3
sw_c, sw_h = (6.0, 27.6), 1.6         # B3U-1000P centre and height
led_c = (18.2, 27.6)                  # D1
conn_c, conn_w, conn_h, conn_mouth = (23.6, 24.7), 6.0, 2.9, 2.47   # SM04B-SRSS-TB (J1): centre, body, height, body past the centre toward the mouth
swd_c = (12.3, 24.7)                  # J2, same connector, same mouth direction, no opening (flashing is a lid-off job)
module = (0.5, 0.0, 15.5, 19.0, 3.1)  # E73 incl. pads: x0, y0, x1, y1, height (3.0 ±0.1 per the manual)
max_part_h = 2.9                      # tallest part above the board (the connector)

# --- Enclosure ---------------------------------------------------------------------------
clr = 0.4                 # board front/back edge to inner wall
wall = 3.2                # splits into two 1.6 mm lap halves (snap needs >= 3.14, see checks)
floor_t = 1.6
lid_top_t = 1.6
edge_r = 1.0              # 45 deg chamfer on the lid top edge and the base bottom edge (both bed side)
under_clr = 0.55          # air under the clip
over_clr = 0.6            # air over the tallest part
ledge_w = 1.4             # board ledge, measured from the inner wall (1.0 under the board)
ledge_h = 1.2
ledge_gap = 0.2           # air between the ledge wall and the lid tongue
# lid hold-down bosses: (board x, y, diameter). Not at the board corners: the module owns
# the front-left one and C1 + J1 the back-right one
bosses = [(1.3, 21.2, 2.4), (28.0, 1.5, 2.4), (1.5, 27.5, 2.4), (28.5, 23.0, 2.0)]
ant_wall_clr = 1.0        # air in front of the antenna end (board y 0)
# Board hooks: a finger off the lid ceiling on each side wall, its barb under the board's side
# edge, so the board stays in the lid when the lid comes off. To take the board out, pull the
# tab below each barb outward (fingernail between tab and clip leg). Between the snap fingers,
# where the clip band has already broken the ledge, in front of the clip's solder legs.
hook_y, hook_w, hook_t = 13.45, 3.4, 1.0      # board y of the centre, width, finger thickness
hook_gap, hook_grip, hook_flex = 0.2, 0.5, 0.7  # finger to board edge, barb under the board, air behind the finger
hook_flat, hook_slack, hook_tab = 0.3, 0.1, 1.5  # flat retention face, board play, release tab below the barb
side_clr = hook_flex + hook_t + hook_gap      # board side edge to inner wall

# Button: cantilever tab in the lid top over SW1, nub underneath
tab_w, tab_l, tab_slot, tab_r = 6.0, 7.45, 0.7, 1.5   # tab_r: free-end corners
tab_tip = 1.45            # switch centre to the tab's free end: the tip stays over the cavity
tab_t = 0.8               # tab thinned from the inside to this: about 5 N to press (8 N at 1.0)
nub_d, nub_gap = 2.4, 0.3  # nub diameter, air over the switch cap at rest
# Light pipe: top hat as on the ESP32 case (../../case/openrz67_case.py has the history):
# tapered head in a funnel, stem in a slip-fit window, glued. The collar off the ceiling
# keeps it from tilting; only D1 and R3 sit under its ring, both under low_part_h.
led_stem_d = 2.2
led_head_lip, led_head_t, led_pipe_clr, led_pipe_gap = 0.7, 1.4, 0.2, 0.8   # gap from the board top
led_collar_w = 0.87       # two perimeter lines
low_part_h = 0.6          # D1 (0603 LED); R3 (0402) is lower
conn_clr = 0.5            # around the connector body in the wall opening
cell_mark_l, cell_mark_w, cell_mark_d = 10.0, 1.5, 0.4   # "+" debossed in the floor under the cell: its + side faces the floor
pry_w, pry_d, pry_h = 10.0, 1.0, 1.2
# Orientation rib on the front wall, half on the base and half on the lid: the halves line
# up only when the lid is on the right way around. Off-centre, clear of the pry slot.
orient_mark_x, orient_mark_w, orient_mark_d, orient_mark_h = 4.0, 2.5, 0.8, 7.0
# Lid text: debossed in the top, filled by an inlay part on filament 2 (make_3mf.py), as on
# the ESP32 case (../../case/openrz67_case.py has the reasoning). Centred in X, and in Y
# between the front edge chamfer and the LED seat. A rail runs from the left wall into the
# light-pipe seat, as on the ESP32 case: the LED reads as an indicator on a line.
# (text, font size, letter tracking)
lid_text_show = os.environ.get("LID_TEXT_SHOW", "true") == "true"
lid_font = "Futura"
lid_texts = [(os.environ.get("LID_TEXT", "OpenRZ67"), float(os.environ.get("LID_TEXT_SIZE", 5.8)), 0.0),
             ("TRIGGER", 4.0, 0.6)]
lid_text_gap, lid_text_min_stroke, lid_text_depth = 1.2, 0.6, 0.8
# At the size this lid allows, Futura Bold's thinnest strokes ("e", "pn") are 0.52 mm; every
# glyph outline is grown by this much per side to clear lid_text_min_stroke. No more: it
# closes the counters.
lid_text_bold = 0.05
lid_rail_w, lid_rail_end, lid_rail_gap = 0.9, 4.0, 1.2   # width, inset from the left wall, air to the LED seat

# Snap (geometry proven on the ESP32 case, see ../../case/notes/design-history.md)
snap_bead = 0.55
bead_h = 1.4
bead_tip_h = 1.1
pocket_extra_d, pocket_extra_h = 0.15, 0.3
bead_ch_in, bead_ch_out, pocket_ch = 0.4, 0.15, 0.2
finger_l, finger_t, finger_slot = 10.0, 1.0, 0.8
lap, lap_gap = 5.0, 0.15
eps = 0.01

# --- Derived --------------------------------------------------------------------------------
inner_w = board_w + 2 * side_clr
inner_h = board_h + 2 * clr + ant_wall_clr
inner_r = board_r + clr
outer_w, outer_h, outer_r = inner_w + 2 * wall, inner_h + 2 * wall, inner_r + wall
pcb_z = floor_t + clip_h + under_clr
pcb_top_z = pcb_z + pcb_t
split_z = pcb_top_z
comp_clr = max_part_h + over_clr
lid_h = comp_clr + lid_top_t
total_h = split_z + lid_h
ceiling_z = total_h - lid_top_t
bead_z = split_z - lap + bead_tip_h
snap_fingers_y = [wall + 7.0, outer_h - wall - 7.0]     # finger centres (case-Y) on the left and right wall

check(lap <= split_z - floor_t, "lid lip would reach the floor")
check(edge_r <= min(wall, lid_top_t) and edge_r < inner_r + wall, "lid top chamfer too big")
check(split_z - lap <= bead_z - bead_h / 2 and bead_z + (bead_h + pocket_extra_h) / 2 < split_z,
      "snap bead/pocket outside the lap zone")
check(wall / 2 - (snap_bead + pocket_extra_d) >= 0.87, "base lip behind the snap pocket under two lines")
check(wall / 2 - lap_gap >= 0.87, "lid tongue under two perimeter lines")
check(0.87 <= finger_t <= wall / 2 - lap_gap, "snap finger thickness")
check(ledge_w - clr >= 0.8, "ledge under the board too narrow")
check(hook_t >= 0.87, "board hook under two perimeter lines")
check(floor_t - cell_mark_d >= 1.0, "floor under the + mark too thin")
check(ledge_h <= clip_h + under_clr, "ledge taller than the room under the board")
check(split_z + orient_mark_h / 2 <= total_h - edge_r, "orientation rib runs into the lid top chamfer")


def bx(x):
    return wall + side_clr + board_w - x


def by(y):
    return wall + ant_wall_clr + clr + y


# --- Helpers ---------------------------------------------------------------------------------
def rrect(w, h, r, x0=0.0, y0=0.0):
    return Pos(x0 + w / 2, y0 + h / 2) * RectangleRounded(w, h, r)


def prism(sk, z0, h):
    return extrude(Plane.XY.offset(z0) * sk, amount=h)


def box(x0, y0, z0, dx, dy, dz):
    return Pos(x0, y0, z0) * Box(dx, dy, dz, align=Align.MIN)


def cyl(x, y, z0, d, h):
    return Pos(x, y, z0) * Cylinder(d / 2, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


outer_sk = rrect(outer_w, outer_h, outer_r)
inner_sk = rrect(inner_w, inner_h, inner_r, wall, wall)
mid_sk = rrect(inner_w + wall, inner_h + wall, inner_r + wall / 2, wall / 2, wall / 2)
board_sk = rrect(board_w, board_h, board_r, bx(board_w), by(0))

# Snap finger bands (case-Y range of each finger) on the left (x = 0) and right wall
finger_bands = [(fy - finger_l / 2, fy + finger_l / 2) for fy in snap_fingers_y]


def orient_mark_rib(z0):
    """Half of the front-wall orientation rib (base: lower, lid: upper). Overlaps 0.2 into the wall."""
    return box(bx(orient_mark_x) - orient_mark_w / 2, -orient_mark_d, z0,
               orient_mark_w, orient_mark_d + 0.2, orient_mark_h / 2)


check(outer_r < bx(orient_mark_x) - orient_mark_w / 2 and bx(orient_mark_x) + orient_mark_w / 2 < outer_w - outer_r
      and abs(bx(orient_mark_x) - outer_w / 2) > (pry_w + orient_mark_w) / 2,
      "orientation rib off the flat front wall or on the pry slot")


def finger_boxes(margin, z0, h):
    return Part() + [box(-1, fy0 - margin, z0, outer_w + 2, fy1 - fy0 + 2 * margin, h)
                     for fy0, fy1 in finger_bands]


# Camera plug opening in the back wall: body width + clearance, from the board top up.
# Along the whole back wall the base keeps its full wall (no rabbet) and the lid has no
# tongue: the plug gets a floor to sit on, like the USB zone on the ESP32 case, and with the
# board hooked into the lid the cell slides out backwards under it.
conn_x0 = bx(conn_c[0]) - conn_w / 2 - conn_clr
conn_open_w = conn_w + 2 * conn_clr
conn_open_h = conn_h + conn_clr
back_zone = box(-1, outer_h - wall - 1, split_z - lap - 1, outer_w + 2, wall + 2, lap + 1)
cut_conn = box(conn_x0, outer_h - wall - 1, split_z - eps, conn_open_w, wall + 2, conn_open_h + eps)

# --- BASE -------------------------------------------------------------------------------------
base = prism(outer_sk, 0, split_z)
base = chamfer(base.edges().group_by(Axis.Z)[0], edge_r)
base -= prism(inner_sk, floor_t, total_h)                               # cavity
base -= prism(mid_sk, split_z - lap, lap + 1) - back_zone              # rabbet: outer half only
# Board ledge: a wall standing on the floor, ledge_gap inside the lid tongue (above
# split_z - lap the base wall is only its outer half, so a ledge hung on it would float).
# Below the tongue the gap is filled so the ledge also joins the wall. Reaches
# ledge_w - clr under the board on every side. Broken on the sides where the clip passes
# over it and the hooks hang, and along the back where the cell comes within 1 mm of the
# board edge.
ledge_in = offset(board_sk, -(ledge_w - clr))
ledge = prism(offset(inner_sk, -ledge_gap) - ledge_in, floor_t - eps, pcb_z - floor_t + eps)
ledge += prism(offset(inner_sk, 0.5) - ledge_in, floor_t - eps, split_z - lap - floor_t + eps)
ledge += prism(offset(inner_sk, -ledge_gap), floor_t - eps, pcb_z - floor_t + eps) & box(   # front: bridge the antenna air gap
    0, 0, 0, outer_w, wall + ant_wall_clr + ledge_w, total_h)
side_y0 = by(min(cell_c[1] - clip_w / 2 - 0.7, hook_y - hook_w / 2 - 0.3))
side_y1 = by(cell_c[1] + clip_w / 2 + 0.7)
side_ledge = side_clr + ledge_w - clr
for x0 in (wall - 1, outer_w - wall - side_ledge):
    ledge -= box(x0, side_y0, floor_t, side_ledge + 1, side_y1 - side_y0, total_h)
ledge -= box(bx(cell_c[0]) - cell_d / 2 - 0.7, outer_h - wall - ledge_w, floor_t, cell_d + 1.4, ledge_w + 1, total_h)
base += ledge
base += orient_mark_rib(split_z - orient_mark_h / 2)
# Snap pockets in the base lip, only where the lid fingers are
groove = prism(offset(mid_sk, snap_bead + pocket_extra_d) - offset(mid_sk, -lap_gap - 0.25),
               split_z - lap - eps, bead_z + (bead_h + pocket_extra_h) / 2 - (split_z - lap) + eps) & finger_boxes(0.5, 0, total_h)
base -= chamfer(groove.edges().group_by(Axis.Z)[-1].filter_by(Axis.Y), pocket_ch)
# "+" in the floor under the cell
for dx, dy in ((cell_mark_l, cell_mark_w), (cell_mark_w, cell_mark_l)):
    base -= box(bx(cell_c[0]) - dx / 2, by(cell_c[1]) - dy / 2, floor_t - cell_mark_d, dx, dy, cell_mark_d + eps)
# Pry slot on the front wall at the seam
base -= box(outer_w / 2 - pry_w / 2, -1, split_z - pry_h, pry_w, pry_d + 1, pry_h + 1)

# --- LID --------------------------------------------------------------------------------------
lid = prism(outer_sk, split_z, lid_h)
lid = chamfer(lid.edges().group_by(Axis.Z)[-1], edge_r)
lid += prism(offset(mid_sk, -lap_gap) - inner_sk, split_z - lap, lap) - back_zone   # tongue: none on the back wall
bead = prism(offset(mid_sk, -lap_gap + snap_bead) - offset(mid_sk, -lap_gap - 0.4),
             bead_z - bead_h / 2, bead_h) & finger_boxes(0, 0, total_h)
bead = chamfer(bead.edges().group_by(Axis.Z)[0], bead_ch_in)
lid += chamfer(bead.edges().group_by(Axis.Z)[-1], bead_ch_out)
lid -= prism(inner_sk, split_z - lap - eps, comp_clr + lap + eps)        # cavity
# Cut the fingers free: relief slots at each end, thinned from the cavity side
for fy0, fy1 in finger_bands:
    for xin, xout in ((wall, wall / 2), (outer_w - wall, outer_w - wall / 2)):
        xa, xb = min(xin, xout), max(xin, xout)
        for y in (fy0 - finger_slot, fy1):
            lid -= box(xa - 0.5, y, split_z - lap - eps, xb - xa + 1, finger_slot, lap + eps)
        thin = wall / 2 - lap_gap - finger_t
        x0 = xin - thin if xin < xout else xin
        lid -= box(x0, fy0, split_z - lap - eps, thin, fy1 - fy0, lap + eps)
# Hold-down bosses at the board corners
for cx, cy, d in bosses:
    lid += cyl(bx(cx), by(cy), pcb_top_z, d, ceiling_z - pcb_top_z + eps)
# Board hooks, built on the x = 0 wall and mirrored. The barb's lower face is a 45 deg lead-in
# (the board edge pushes the finger out); its upper face holds the board.
hook_y0, hook_y1 = by(hook_y - hook_w / 2), by(hook_y + hook_w / 2)
hook_xf = wall + hook_flex + hook_t                  # finger face toward the board
barb_d = hook_gap + hook_grip
barb_top = pcb_z - hook_slack
barb_z0 = barb_top - hook_flat - barb_d
hook_z0 = barb_z0 - hook_tab
hook = box(wall + hook_flex, hook_y0, hook_z0, hook_t, hook_y1 - hook_y0, ceiling_z - hook_z0 + eps)
hook += extrude(Plane.XZ.offset(-hook_y0) * Polygon(
    (hook_xf - eps, barb_top), (hook_xf + barb_d, barb_top), (hook_xf + barb_d, barb_top - hook_flat),
    (hook_xf - eps, barb_z0), align=None), amount=hook_y1 - hook_y0, dir=(0, 1, 0))
lid += hook + mirror(hook, about=Plane.YZ.offset(outer_w / 2))
# Camera plug opening
lid -= cut_conn
# Button: U-slot around a tab hinged at its front end, tab thinned from inside, nub under it
tx, ty = bx(sw_c[0]), by(sw_c[1])
tab_y0 = ty - (tab_l - tab_tip)
tab_x0 = tx - tab_w / 2
tab_sk = rrect(tab_w, tab_l, tab_r, tab_x0, tab_y0) + Pos(tx, tab_y0 + tab_l / 4) * Rectangle(tab_w, tab_l / 2)
slot_sk = (rrect(tab_w + 2 * tab_slot, tab_l + tab_slot, tab_r + tab_slot, tab_x0 - tab_slot, tab_y0)
           + Pos(tx, tab_y0 + tab_l / 4) * Rectangle(tab_w + 2 * tab_slot, tab_l / 2))
lid -= prism(slot_sk - tab_sk, ceiling_z - 1, lid_top_t + 2)
lid -= prism(tab_sk, ceiling_z - eps, lid_top_t - tab_t + eps)   # thin the tab
nub_z0 = pcb_top_z + sw_h + nub_gap
lid += orient_mark_rib(split_z)
lid += cyl(tx, ty, nub_z0, nub_d, (ceiling_z + lid_top_t - tab_t) - nub_z0 + eps)
# LED light pipe: collar off the ceiling, stem window through plate + collar, funnel for the head
lx, ly = bx(led_c[0]), by(led_c[1])
led_taper = math.degrees(math.atan(led_head_lip / led_head_t))
check(led_taper <= 28, f"light-pipe head taper {led_taper:.1f} deg would get slicer support (30 deg threshold)")
check(led_head_t < lid_top_t, "light-pipe head seat goes through the top plate")
pipe_z0 = pcb_top_z + led_pipe_gap
collar_z = pipe_z0
collar_d = led_stem_d + led_pipe_clr + 2 * led_collar_w
check(collar_z - pcb_top_z >= low_part_h + 0.2, "light-pipe collar sits on D1/R3")


def led_head(clr, extra=0.0):
    """Frustum: stem-window size at z = total_h - led_head_t, growing by the lip to the top."""
    return extrude(Plane.XY.offset(total_h - led_head_t) * Pos(lx, ly) * Circle((led_stem_d + clr) / 2),
                   amount=led_head_t + extra, taper=-led_taper)


lid += cyl(lx, ly, collar_z, collar_d, ceiling_z - collar_z + eps)
lid -= cyl(lx, ly, collar_z - eps, led_stem_d + led_pipe_clr, total_h - collar_z + 2 * eps)
lid -= led_head(led_pipe_clr, eps)
lightpipe = led_head(0.0) + cyl(lx, ly, pipe_z0, led_stem_d, total_h - led_head_t - pipe_z0 + eps)


def grow(f, d):
    """Offset a glyph face by d (negative shrinks). By hand: build123d 0.11's offset()
    crashes on glyphs with holes."""
    g = Face(f.outer_wire().offset_2d(d))
    for w in f.inner_wires():
        g = g.cut(Face(w.offset_2d(-d)))
    return g.faces() if hasattr(g, "faces") else [g]


def tracked_text(txt, size, tracking):
    """Text sketch, each glyph emboldened by lid_text_bold and shifted by `tracking` per
    glyph (glyphs sorted by X, one face each). The stroke check runs on the raw glyph: OCCT
    cannot reliably shrink an outline it has just grown."""
    sk = Text(txt, font=lid_font, font_size=size, font_style=FontStyle.BOLD)
    glyphs = []
    for i, f in enumerate(sorted(sk.faces(), key=lambda f: f.center().X)):
        # every stroke >= lid_text_min_stroke once grown: shrinking the raw glyph by half of
        # the rest must keep it one face
        try:
            n = len(grow(f, -(lid_text_min_stroke / 2 - lid_text_bold)))
        except Exception:   # the wire collapsed: stroke too thin
            n = 0
        check(n == 1, f"'{txt}' has strokes under {lid_text_min_stroke} mm (a glyph -> {n} faces)")
        glyphs += [Pos(i * tracking, 0) * x for x in grow(f, lid_text_bold)]
    return Sketch(glyphs)


lid_text = None            # the inlay: exactly the pocket volume, printed in filament 2
if lid_text_show:
    text_cut = None
    lines = [tracked_text(*t) for t in lid_texts]
    heights = [l.bounding_box().size.Y for l in lines]
    block_h = sum(heights) + lid_text_gap * (len(lines) - 1)
    band_y0, band_y1 = edge_r, tab_y0 - tab_slot
    led_seat_r = (led_stem_d + led_pipe_clr) / 2 + led_head_lip
    y = (band_y0 + ly - led_seat_r) / 2 + block_h / 2      # top of the block
    for (txt, *_), sk, h in zip(lid_texts, lines, heights):
        tb = sk.bounding_box()
        sk = Pos(outer_w / 2 - (tb.min.X + tb.max.X) / 2, y - h - tb.min.Y) * sk
        tb = sk.bounding_box()
        check(tb.min.X > edge_r + 1 and tb.max.X < outer_w - edge_r - 1, f"'{txt}' too wide ({tb.size.X:.1f}mm)")
        check(tb.max.Y < band_y1 - 1, f"'{txt}' hits the button tab")
        check(tb.min.Y > band_y0 + 0.5, f"'{txt}' runs into the top-edge chamfer")
        c = prism(sk, total_h - lid_text_depth, lid_text_depth + eps)
        text_cut = c if text_cut is None else text_cut + c
        y -= h + lid_text_gap
    rail_x1 = lx - led_seat_r - lid_rail_gap
    check(rail_x1 - lid_rail_end > 5, "rail too short")
    text_cut += box(lid_rail_end, ly - lid_rail_w / 2, total_h - lid_text_depth, rail_x1 - lid_rail_end, lid_rail_w, lid_text_depth + eps)
    lid_text = lid & text_cut
    lid -= text_cut

# --- Assertions --------------------------------------------------------------------------------
for name, p in (("base", base), ("lid", lid), ("lightpipe", lightpipe)):
    check(p.is_valid, f"{name}: invalid solid")
    check(len(p.solids()) == 1, f"{name}: {len(p.solids())} separate bodies, something floats")
_hb = hook.bounding_box()
check(abs(_hb.min.Y - hook_y0) < 1e-3 and abs(_hb.max.Y - hook_y1) < 1e-3 and abs(_hb.max.X - (hook_xf + barb_d)) < 1e-3, "board hook misplaced")
bb = base.bounding_box()
check(abs(bb.size.X - outer_w) < 1e-3, "base X")
check(abs(bb.max.Y - outer_h) < 1e-3 and abs(bb.min.Y + orient_mark_d) < 1e-3, "base Y")
check(abs(bb.max.Z - split_z) < 1e-3, f"base Z {bb.max.Z}")
lb = lid.bounding_box()
check(abs(lb.min.Z - (split_z - lap)) < 1e-3 and abs(lb.max.Z - total_h) < 1e-3, "lid Z")
if lid_text is not None:
    check(lid_text.is_valid and lid_text.volume > 1e-3, "lid text inlay: empty or invalid")
    tb = lid_text.bounding_box()
    check(abs(tb.max.Z - total_h) < 1e-3 and tb.min.Z > total_h - lid_text_depth - 1e-3, "inlay not in the pocket")
    check((lid & lid_text).volume < 1e-6, "inlay overlaps the lid")


def _open(solid, probe, what):
    v = (solid & probe).volume
    check(v < 1e-6, f"{what} blocked (probe volume {v:.3f})")


def _clear(solid, keep, what):
    v = (solid & keep).volume
    check(v < 1e-6, f"{what} collides (volume {v:.3f})")


# Keepouts: the board itself, the cell + clip below it, the parts above it
_clear(base + lid, prism(board_sk, pcb_z + eps, pcb_t - 2 * eps), "board")
_clear(base + lid, cyl(bx(cell_c[0]), by(cell_c[1]), pcb_z - clip_h - under_clr + eps, cell_d + 1.0, clip_h + under_clr - 2 * eps), "cell")
_clear(base + lid, box(bx(cell_c[0]) - clip_l / 2 - 0.3, by(cell_c[1]) - clip_w / 2 - 0.3, pcb_z - clip_h - under_clr + eps,
                       clip_l + 0.6, clip_w + 0.6, clip_strap_h + under_clr), "clip strap")
_clear(base + lid, box(bx(cell_c[0]) - clip_l / 2 - 0.3, by(cell_c[1]) - clip_leg_w / 2 - 0.3, pcb_z - clip_h - under_clr + eps,
                       clip_l + 0.6, clip_leg_w + 0.6, clip_h + under_clr - 2 * eps), "clip legs")
_clear(lid, box(bx(module[2]), by(module[1]), pcb_top_z, module[2] - module[0], module[3] - module[1], module[4] + 0.3), "module")
_clear(lid, box(bx(conn_c[0]) - conn_w / 2 - 0.3, by(conn_c[1]) - 2.5, pcb_top_z, conn_w + 0.6, 2.5 + conn_mouth + clr + 1, conn_h + 0.3), "connector")
_clear(lid, cyl(bx(led_c[0]), by(led_c[1]), pcb_top_z, 2.4, 0.9), "LED")
_clear(lid, cyl(bx(sw_c[0]), by(sw_c[1]), pcb_top_z, 3.6, sw_h + 0.1), "switch")
# the whole board top stays free up to the tallest part, except under the bosses and the nub
_free = prism(board_sk, pcb_top_z, max_part_h - eps) - cyl(tx, ty, pcb_top_z, nub_d + 0.5, max_part_h)
for cx, cy, d in bosses:
    _free -= cyl(bx(cx), by(cy), pcb_top_z - 1, d + 0.2, max_part_h + 2)
_free -= cyl(lx, ly, pcb_top_z - 1, collar_d + 0.2, max_part_h + 2)
_clear(lid, _free, "parts under the lid")
# Bosses press on bare board: clear of every top-side part (KiCad footprint bboxes, board coords)
top_parts = {"U1": (0.5, 0.17, 15.5, 19.31), "U2": (16.68, 5.67, 21.0, 14.32), "U3": (21.07, 5.67, 25.4, 14.32),
             "R1": (18.85, 3.43, 20.89, 4.57), "R2": (22.82, 3.43, 24.86, 4.57), "R3": (16.83, 24.38, 17.97, 26.42),
             "C1": (25.33, 14.37, 27.67, 19.64), "C2": (8.03, 19.73, 10.51, 20.87), "D1": (16.73, 26.78, 19.76, 28.43),
             "J1": (20.2, 21.98, 27.0, 27.54), "J2": (8.9, 21.98, 15.7, 27.54), "SW1": (3.38, 26.22, 8.62, 28.98),
             "Q1": (3.67, 19.34, 7.12, 23.25)}


def plan_gap(cx, cy, d, x0, y0, x1, y1):
    return ((max(x0 - cx, 0, cx - x1)) ** 2 + (max(y0 - cy, 0, cy - y1)) ** 2) ** 0.5 - d / 2


for cx, cy, d in bosses:
    for ref, bb in top_parts.items():
        gap = plan_gap(cx, cy, d, *bb)
        check(gap >= 0.2, f"boss at ({cx}, {cy}) within {gap:.2f} mm of {ref}")
# Light-pipe collar: clear of the tall parts in plan. J1/J2 by their bodies: the footprint bbox
# includes the flat side pads, which the collar passes over.
_tall = {r: bb for r, bb in top_parts.items() if r not in ("D1", "R3")}
for ref, c in (("J1", conn_c), ("J2", swd_c)):
    _tall[ref] = (c[0] - conn_w / 2, top_parts[ref][1], c[0] + conn_w / 2, top_parts[ref][3])
for ref, bb in _tall.items():
    gap = plan_gap(*led_c, collar_d, *bb)
    check(gap >= 0.2, f"light-pipe collar within {gap:.2f} mm of {ref}")
# J1 sits at board x 23.6, right of centre in KiCad: seen from above with the antenna at the
# front it is on the left. Catches a board mapped without the mirror.
check(conn_x0 + conn_open_w / 2 < outer_w / 2, "camera plug opening not on the left: board mirrored?")
# Button tab: the tip ends over the cavity (no wall under it to bottom out on), the nub sits on the tab
check(tab_y0 + tab_l <= by(board_h + clr) - 0.3, "button tab tip over the wall")
check(ty + nub_d / 2 <= tab_y0 + tab_l - 0.2, "nub overhangs the tab tip")
# Openings break through
_open(base + lid, box(conn_x0 + 0.2, outer_h - wall - 0.5, split_z + 0.1, conn_open_w - 0.4, wall + 1, conn_open_h - 0.3), "plug opening")
_open(lid, cyl(lx, ly, collar_z - 0.5, led_stem_d + led_pipe_clr - 0.1, total_h - collar_z + 1), "light-pipe window")
_clear(lid, lightpipe, "light pipe")
_open(lid, box(tab_x0 + tab_r, tab_y0 + tab_l + 0.1, ceiling_z - 0.5, tab_w - 2 * tab_r, tab_slot - 0.2, lid_top_t + 1), "button slot")
for x0 in (tab_x0 - tab_slot + 0.1, tab_x0 + tab_w + 0.1):
    _open(lid, box(x0, tab_y0 + 0.1, ceiling_z - 0.5, tab_slot - 0.2, tab_l - tab_r, lid_top_t + 1), "button slot side")
_clear(base, lid, "lid")
# Board hooks: clear of the snap finger slots, air behind each finger, the barbs reach under
# the board by hook_grip, and the cell slides out backwards past the lid with the board in it
for fy0, fy1 in finger_bands:
    check(hook_y1 <= fy0 - finger_slot - 0.3 or hook_y0 >= fy1 + finger_slot + 0.3, "board hook on a snap finger slot")
for x0 in (wall, outer_w - wall - hook_flex):
    _open(lid, box(x0 + eps, hook_y0, hook_z0, hook_flex - 2 * eps, hook_y1 - hook_y0, ceiling_z - hook_z0 - 0.5), "air behind a board hook")
_hold = (lid & prism(board_sk, barb_top - hook_flat + eps, hook_flat - 2 * eps)).volume
check(_hold > 0.9 * 2 * hook_grip * hook_w * (hook_flat - 2 * eps), f"board hooks do not reach under the board ({_hold:.2f} mm3)")
_cx, _cy, _cz0 = bx(cell_c[0]), by(cell_c[1]), pcb_z - cell_t - 0.1
_open(lid, cyl(_cx, _cy, _cz0, cell_d, cell_t) + box(_cx - cell_d / 2, _cy, _cz0, cell_d, outer_h - _cy + 1, cell_t), "cell exit (board in the lid)")
_open(base, box(bx(cell_c[0]) - cell_mark_l / 2 + 0.1, by(cell_c[1]) - cell_mark_w / 2 + 0.1, floor_t - cell_mark_d + 0.05,
                cell_mark_l - 0.2, cell_mark_w - 0.2, cell_mark_d), "+ mark in the floor")
# Ledge actually supports the board along the front and back edges
check((base & box(bx(board_w - 5), by(-clr), pcb_z - ledge_h + 0.1, board_w - 10, clr + 0.8, ledge_h - 0.2)).volume > 0.5 * (board_w - 10) * (clr + 0.8) * (ledge_h - 0.2), "front ledge missing")

# --- Export -------------------------------------------------------------------------------------
if __name__ == "__main__":
    out = Path(os.environ.get("OUTDIR", Path(__file__).resolve().parent / "stl"))
    out.mkdir(parents=True, exist_ok=True)
    parts = [("openrz67-nrf-base", base), ("openrz67-nrf-lid", lid), ("openrz67-nrf-lightpipe", lightpipe)]
    stale = out / "openrz67-nrf-lid-text.stl"
    if lid_text is not None:
        parts.append(("openrz67-nrf-lid-text", lid_text))
    elif stale.exists():
        stale.unlink()     # make_3mf.py would otherwise add an old inlay
    if os.environ.get("SNAP_TEST", "false") == "true":
        crop = box(-2, -2, -1, 14, 20, total_h + 2)
        parts += [("openrz67-nrf-snaptest-base", base & crop), ("openrz67-nrf-snaptest-lid", lid & crop)]
    for name, p in parts:
        export_stl(p, str(out / f"{name}.stl"), ascii_format=True)
        b = p.bounding_box()
        print(f"{name}: {b.size.X:.2f} x {b.size.Y:.2f} x {b.size.Z:.2f} mm, {p.volume / 1000:.2f} cm3")
    print(f"outer {outer_w:.1f} x {outer_h:.1f} x {total_h:.1f} mm; STLs in {out}")

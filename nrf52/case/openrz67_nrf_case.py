# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d>=0.11.1"]
# ///
"""openrz67 nRF52 trigger enclosure (build123d).

Two-part snap-fit box for the coin-cell board in ../kicad/ (27 x 29 mm, CR2032 clip on
the back). The board rests on a ledge around the base cavity with the cell hanging below
it; the lid presses it down with four corner bosses. The lid carries a cantilever button
tab over SW1, a light hole over D1 and the opening for the JST SH camera plug in its back
wall. A hole in the floor lets a finger push the board out for a cell change.

Parts: base (tub) and lid (telescoping tongue with four snap fingers on the side walls).
Print orientation: base floor-down, lid upside-down. No supports.

Coordinate system: case coords, origin at the outer box's front-left-bottom corner.
Board coords are the KiCad coords of ../kicad/openrz67-nrf.kicad_pcb (origin top-left of
the board, Y down in KiCad = toward the back wall here). bx()/by() map them into case
coords. Antenna end of the module at the front wall (board y = 0), camera connector mouth
at the back wall (board y = 29).

Run (exports STLs to stl/ and checks the assertions):
    uv run openrz67_nrf_case.py

Env overrides: PCB_T, OUTDIR (STL directory, default stl/), SNAP_TEST=true (also export a
cropped corner pair for tuning snap_bead / lap_gap).
"""

import os
from pathlib import Path

from build123d import *


def check(cond, msg):
    """Keepout / printability guard. Not `assert`: `python -O` would strip those."""
    if not cond:
        raise SystemExit(msg)


# --- Board (from ../kicad/tools/design.py) --------------------------------------------
board_w, board_h, board_r = 27.0, 29.0, 0.8
pcb_t = float(os.environ.get("PCB_T", "1.6"))
cell_c = (13.5, 18.0)                 # CR2032 centre (BT1), on the back
cell_d, cell_t = 20.0, 3.2
clip_l, clip_w, clip_h = 25.9, 9.4, 3.75   # MY-2032-16 clip incl. feet; highest point under the board
sw_c, sw_h = (6.0, 27.6), 1.6         # B3U-1000P centre and height
led_c = (12.0, 27.6)                  # D1
conn_c, conn_w, conn_h, conn_mouth = (21.3, 24.7), 6.0, 2.9, 2.47   # SM04B-SRSS-TB: centre, body, height, body past the centre toward the mouth
module = (0.5, 0.0, 15.5, 19.0, 2.0)  # E73 incl. pads: x0, y0, x1, y1, height
max_part_h = 2.9                      # tallest part above the board (the connector)

# --- Enclosure ---------------------------------------------------------------------------
clr = 0.4                 # board edge to inner wall
wall = 3.2                # splits into two 1.6 mm lap halves (snap needs >= 3.14, see checks)
floor_t = 1.6
lid_top_t = 1.6
lid_top_r = 1.0           # 45 deg chamfer on the lid's top edge (bed side)
under_clr = 0.55          # air under the clip
over_clr = 0.6            # air over the tallest part
ledge_w = 1.4             # board ledge, measured from the inner wall (1.0 under the board)
ledge_h = 1.2
floor_hole_d = 14.0       # push the board out from below
# lid hold-down bosses: (board x, y, diameter). Not at the board corners: the module owns
# the front-left one and C1 + J1 the back-right one
bosses = [(1.3, 21.2, 2.4), (25.5, 1.5, 2.4), (1.5, 27.5, 2.4), (26.0, 23.0, 2.0)]
ant_wall_clr = 1.0        # air in front of the antenna end (board y 0)

# Button: cantilever tab in the lid top over SW1, nub underneath
tab_w, tab_l, tab_slot = 6.0, 8.0, 0.7
tab_t = 1.0               # tab thinned from the inside to this
nub_d, nub_gap = 2.4, 0.3  # nub diameter, air over the switch cap at rest
led_hole_d = 1.6
conn_clr = 0.5            # around the connector body in the wall opening
pry_w, pry_d, pry_h = 10.0, 1.0, 1.2

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
inner_w = board_w + 2 * clr
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
check(lid_top_r <= min(wall, lid_top_t) and lid_top_r < inner_r + wall, "lid top chamfer too big")
check(split_z - lap <= bead_z - bead_h / 2 and bead_z + (bead_h + pocket_extra_h) / 2 < split_z,
      "snap bead/pocket outside the lap zone")
check(wall / 2 - (snap_bead + pocket_extra_d) >= 0.87, "base lip behind the snap pocket under two lines")
check(wall / 2 - lap_gap >= 0.87, "lid tongue under two perimeter lines")
check(0.87 <= finger_t <= wall / 2 - lap_gap, "snap finger thickness")
check(ledge_w - clr >= 0.8, "ledge under the board too narrow")
check(ledge_h <= clip_h + under_clr, "ledge taller than the room under the board")


def bx(x):
    return wall + clr + x


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

# Snap finger bands (case-Y range of each finger) on the left (x = 0) and right wall
finger_bands = [(fy - finger_l / 2, fy + finger_l / 2) for fy in snap_fingers_y]


def finger_boxes(margin, z0, h):
    return Part() + [box(-1, fy0 - margin, z0, outer_w + 2, fy1 - fy0 + 2 * margin, h)
                     for fy0, fy1 in finger_bands]


# Camera plug opening in the back wall: body width + clearance, from the board top up.
# The base keeps its full wall under it (no rabbet) so the plug has a floor to sit on,
# like the USB zone on the ESP32 case.
conn_x0 = bx(conn_c[0]) - conn_w / 2 - conn_clr
conn_open_w = conn_w + 2 * conn_clr
conn_open_h = conn_h + conn_clr
conn_zone = box(conn_x0 - wall, outer_h - wall - 1, split_z - lap - 1, conn_open_w + 2 * wall, wall + 2, lap + 1)
cut_conn = box(conn_x0, outer_h - wall - 1, split_z - eps, conn_open_w, wall + 2, conn_open_h + eps)

# --- BASE -------------------------------------------------------------------------------------
base = prism(outer_sk, 0, split_z)
base -= prism(inner_sk, floor_t, total_h)                               # cavity
base -= prism(mid_sk, split_z - lap, lap + 1) - conn_zone              # rabbet: outer half only
# Board ledge: a ring around the cavity, broken on the sides where the clip passes over
# it and along the back where the cell comes within 1 mm of the board edge
ledge = prism(inner_sk - offset(inner_sk, -ledge_w), pcb_z - ledge_h, ledge_h)
ledge += box(wall, wall, pcb_z - ledge_h, inner_w, ant_wall_clr + ledge_w, ledge_h)   # front: bridge the antenna air gap
clip_y0, clip_y1 = by(cell_c[1] - clip_w / 2 - 0.7), by(cell_c[1] + clip_w / 2 + 0.7)
for x0 in (wall - 1, outer_w - wall - ledge_w):
    ledge -= box(x0, clip_y0, pcb_z - ledge_h - eps, ledge_w + 1, clip_y1 - clip_y0, ledge_h + 2 * eps)
ledge -= box(bx(cell_c[0] - cell_d / 2 - 0.7), outer_h - wall - ledge_w, pcb_z - ledge_h - eps, cell_d + 1.4, ledge_w + 1, ledge_h + 2 * eps)
base += ledge
base -= cyl(bx(cell_c[0]), by(cell_c[1]), -1, floor_hole_d, floor_t + 2)   # push-out hole
# Snap pockets in the base lip, only where the lid fingers are
groove = prism(offset(mid_sk, snap_bead + pocket_extra_d) - offset(mid_sk, -lap_gap - 0.25),
               split_z - lap - eps, bead_z + (bead_h + pocket_extra_h) / 2 - (split_z - lap) + eps) & finger_boxes(0.5, 0, total_h)
base -= chamfer(groove.edges().group_by(Axis.Z)[-1].filter_by(Axis.Y), pocket_ch)
# Pry slot on the front wall at the seam
base -= box(outer_w / 2 - pry_w / 2, -1, split_z - pry_h, pry_w, pry_d + 1, pry_h + 1)

# --- LID --------------------------------------------------------------------------------------
lid = prism(outer_sk, split_z, lid_h)
lid = chamfer(lid.edges().group_by(Axis.Z)[-1], lid_top_r)
lid += prism(offset(mid_sk, -lap_gap) - inner_sk, split_z - lap, lap) - box(   # tongue, notched at the plug
    conn_x0 - lap_gap, outer_h - wall - 1, split_z - lap - 1, conn_open_w + 2 * lap_gap, wall + 2, lap + 1)
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
# Camera plug opening
lid -= cut_conn
# Button: U-slot around a tab hinged at its front end, tab thinned from inside, nub under it
tx, ty = bx(sw_c[0]), by(sw_c[1])
tab_y0 = ty - (tab_l - 2.0)          # the switch sits 2 mm from the free (back) end
tab_x0 = tx - tab_w / 2
slot = box(tab_x0 - tab_slot, tab_y0, ceiling_z - 1, tab_w + 2 * tab_slot, tab_l + tab_slot, lid_top_t + 2)
slot -= box(tab_x0, tab_y0 - 1, ceiling_z - 2, tab_w, tab_l + 1, lid_top_t + 4)
lid -= slot
lid -= box(tab_x0, tab_y0, ceiling_z - eps, tab_w, tab_l, lid_top_t - tab_t + eps)   # thin the tab
nub_z0 = pcb_top_z + sw_h + nub_gap
lid += cyl(tx, ty, nub_z0, nub_d, (ceiling_z + lid_top_t - tab_t) - nub_z0 + eps)
# LED light hole
lid -= cyl(bx(led_c[0]), by(led_c[1]), ceiling_z - 1, led_hole_d, lid_top_t + 2)

# --- Assertions --------------------------------------------------------------------------------
for name, p in (("base", base), ("lid", lid)):
    check(p.is_valid, f"{name}: invalid solid")
bb = base.bounding_box()
check(abs(bb.size.X - outer_w) < 1e-3 and abs(bb.size.Y - outer_h) < 1e-3, "base XY")
check(abs(bb.max.Z - split_z) < 1e-3, f"base Z {bb.max.Z}")
lb = lid.bounding_box()
check(abs(lb.min.Z - (split_z - lap)) < 1e-3 and abs(lb.max.Z - total_h) < 1e-3, "lid Z")


def _open(solid, probe, what):
    v = (solid & probe).volume
    check(v < 1e-6, f"{what} blocked (probe volume {v:.3f})")


def _clear(solid, keep, what):
    v = (solid & keep).volume
    check(v < 1e-6, f"{what} collides (volume {v:.3f})")


# Keepouts: the board itself, the cell + clip below it, the parts above it
_clear(base + lid, prism(rrect(board_w, board_h, board_r, bx(0), by(0)), pcb_z + eps, pcb_t - 2 * eps), "board")
_clear(base, cyl(bx(cell_c[0]), by(cell_c[1]), pcb_z - clip_h - under_clr + eps, cell_d + 1.0, clip_h + under_clr - 2 * eps), "cell")
_clear(base, box(bx(cell_c[0]) - clip_l / 2 - 0.3, by(cell_c[1]) - clip_w / 2 - 0.3, pcb_z - clip_h - under_clr + eps,
                 clip_l + 0.6, clip_w + 0.6, clip_h + under_clr - 2 * eps), "clip")
_clear(lid, box(bx(module[0]), by(module[1]), pcb_top_z, module[2] - module[0], module[3] - module[1], module[4] + 0.3), "module")
_clear(lid, box(bx(conn_c[0]) - conn_w / 2 - 0.3, by(conn_c[1]) - 2.5, pcb_top_z, conn_w + 0.6, 2.5 + conn_mouth + clr + 1, conn_h + 0.3), "connector")
_clear(lid, cyl(bx(led_c[0]), by(led_c[1]), pcb_top_z, 2.4, 0.9), "LED")
_clear(lid, cyl(bx(sw_c[0]), by(sw_c[1]), pcb_top_z, 3.6, sw_h + 0.1), "switch")
# the whole board top stays free up to the tallest part, except under the bosses and the nub
_free = prism(rrect(board_w, board_h, board_r, bx(0), by(0)), pcb_top_z, max_part_h - eps) - cyl(tx, ty, pcb_top_z, nub_d + 0.5, max_part_h)
for cx, cy, d in bosses:
    _free -= cyl(bx(cx), by(cy), pcb_top_z - 1, d + 0.2, max_part_h + 2)
_clear(lid, _free, "parts under the lid")
# Openings break through
_open(base + lid, box(conn_x0 + 0.2, outer_h - wall - 0.5, split_z + 0.1, conn_open_w - 0.4, wall + 1, conn_open_h - 0.3), "plug opening")
_open(lid, cyl(bx(led_c[0]), by(led_c[1]), ceiling_z - 0.5, led_hole_d - 0.2, lid_top_t + 1), "LED hole")
_open(lid, box(tab_x0 - tab_slot + 0.1, tab_y0 + tab_l + 0.1, ceiling_z - 0.5, tab_w + 2 * tab_slot - 0.2, tab_slot - 0.2, lid_top_t + 1), "button slot")
_open(base, cyl(bx(cell_c[0]), by(cell_c[1]), -0.5, floor_hole_d - 0.2, floor_t + 1), "floor hole")
# Ledge actually supports the board along the front and back edges
check((base & box(bx(5), by(-clr), pcb_z - ledge_h + 0.1, board_w - 10, clr + 0.8, ledge_h - 0.2)).volume > 0.5 * (board_w - 10) * (clr + 0.8) * (ledge_h - 0.2), "front ledge missing")

# --- Export -------------------------------------------------------------------------------------
if __name__ == "__main__":
    out = Path(os.environ.get("OUTDIR", Path(__file__).resolve().parent / "stl"))
    out.mkdir(parents=True, exist_ok=True)
    parts = [("openrz67-nrf-base", base), ("openrz67-nrf-lid", lid)]
    if os.environ.get("SNAP_TEST", "false") == "true":
        crop = box(-2, -2, -1, 14, 20, total_h + 2)
        parts += [("openrz67-nrf-snaptest-base", base & crop), ("openrz67-nrf-snaptest-lid", lid & crop)]
    for name, p in parts:
        export_stl(p, str(out / f"{name}.stl"), ascii_format=True)
        b = p.bounding_box()
        print(f"{name}: {b.size.X:.2f} x {b.size.Y:.2f} x {b.size.Z:.2f} mm, {p.volume / 1000:.2f} cm3")
    print(f"outer {outer_w:.1f} x {outer_h:.1f} x {total_h:.1f} mm; STLs in {out}")

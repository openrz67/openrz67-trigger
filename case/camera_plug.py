# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d>=0.11.1"]
# ///
"""Camera-end plug for the Mamiya RZ67 RC-outlet (build123d).

A printed clamshell around four ordinary female jumper-wire ends (2.54 mm Dupont
sleeves) so they go onto the camera's 4-pin remote port as one plug. The nose
fills the port's rectangular pocket (measured 13.91 x 3.57 mm, ~6.3 deep,
Ø0.8 round pins, 2.54 pitch, row centred); two side cheeks give the lateral
location the loose/taped sleeves lack. A front plate with pin holes stops the
sleeves sliding forward on pull-off, a rear wall with wire notches stops them
sliding back on push-on — no glue on the sleeves. The body is as tall as the
nose (only ~0.4 mm skins over and under the sleeves), so each half prints flat
on its outer face with every cavity opening upward: no bridges, no supports.
Assemble: lay the sleeves in the bottom half, wires out the back, press the top
half on: four Ø1.6 pegs in its side walls press into Ø1.7 holes in the bottom
(no glue; a real snap hook is not printable at 1.8 mm half height). Pin order facing the port, left to right: 6 V
(do NOT connect), GND, S1, S2 — a triangle on top marks the 6 V side, like the
camera's own mark.

Coordinates: x along the pin row (+x = right when facing the port), z up
(toward the sliding dust cover), -y = into the camera. z = 0 is the pocket
floor wall. Exports both halves already lying print-side down.

Run (exports stl/openrz67-camera-plug-{bottom,top}.stl):
    uv run camera_plug.py
"""

import os
from pathlib import Path

from build123d import *

# --- Camera port (measured 2026-09-06, calipers) --------------------------------
pocket_w, pocket_h, pocket_d = 13.91, 3.57, 6.3   # depth is uncertain
pin_pitch, pin_d = 2.54, 0.8
pin_z = pocket_h / 2            # row centred: ~3.0 from the left wall, ~1.8 above the floor
# --- Dupont sleeve + wire (measure yours: sleeves are often 2.50, not 2.54) ---------
sleeve, sleeve_len, sleeve_clr = 2.54, 14.0, 0.05
wire_d = 1.5                    # notch for the jumper wire (~1.3 OD)
# --- Fit / walls (tune after the first print) --------------------------------------
nose_fit = 0.05        # per-side clearance of the nose in the pocket; go negative for press
cheek_len = pocket_d - 0.3
wall, plate_t, rear_t = 3.2, 0.8, 1.5   # wall carries the pegs: (wall - peg_d) / 2 >= 0.8 each side
pin_hole = 1.4
mark = 2.0             # triangle side
peg_d, peg_h, peg_clr, peg_ys = 1.6, 1.2, 0.1, [2.0, 8.0]   # pegs on the top half, holes in the bottom
# hole = peg_d + peg_clr on paper; FDM shrinks small vertical holes ~0.2-0.3, which gives the press.
# First print (peg_clr = -0.1) did not go together at all.

z0, z1 = nose_fit, pocket_h - nose_fit               # whole plug lives inside the pocket height
nose_w, body_w = pocket_w - 2 * nose_fit, pocket_w - 2 * nose_fit + 2 * wall
ch_w, ch_h = 4 * sleeve + 2 * sleeve_clr, sleeve + 2 * sleeve_clr
y_plate = -cheek_len + plate_t                       # sleeve fronts
y_rear = y_plate + sleeve_len + 0.2                  # rear wall starts here
body_len = y_rear + rear_t
skin = pin_z - ch_h / 2 - z0
cheek = (nose_w - ch_w) / 2
assert skin >= 0.4, f"skin {skin:.2f} < 0.4: measure the sleeve height, or lower sleeve_clr/nose_fit"
assert cheek >= 1.2, f"cheek {cheek:.2f} too thin to print"
assert (wall - peg_d) / 2 >= 0.8, "too little wall around the pegs"
assert pin_z - z0 - peg_h - 0.1 >= 0.4, "peg holes would break through the bottom skin"
assert pocket_d - 0.3 - plate_t >= 4.0, "too little pin engagement in the sleeves"


def box(x0, y0, z0, dx, dy, dz):
    return Pos(x0 + dx / 2, y0 + dy / 2, z0 + dz / 2) * Box(dx, dy, dz)


def yholes(d, y, length):
    return [Pos((i - 1.5) * pin_pitch, y, pin_z) * Rot(90, 0, 0) * Cylinder(d / 2, length) for i in range(4)]


plug = box(-nose_w / 2, -cheek_len, z0, nose_w, cheek_len, z1 - z0) + box(-body_w / 2, 0, z0, body_w, body_len, z1 - z0)
plug -= box(-ch_w / 2, y_plate, pin_z - ch_h / 2, ch_w, y_rear - y_plate, ch_h)      # sleeve channel
for h in yholes(pin_hole, y_plate - plate_t / 2, plate_t + 1):                        # pins through the front plate
    plug -= h
for h in yholes(wire_d, y_rear + rear_t / 2, rear_t + 1):                             # wires through the rear wall
    plug -= h
tri = Pos(-1.5 * pin_pitch, body_len / 2, z1) * Rot(0, 0, 180) * Triangle(a=mark, b=mark, c=mark)
plug -= extrude(tri, -0.2)                                                            # 6 V mark, apex toward the camera

cut = Plane.XY.offset(pin_z)
bottom = split(plug, bisect_by=cut, keep=Keep.BOTTOM)
top = split(plug, bisect_by=cut, keep=Keep.TOP)
peg_x = nose_w / 2 + wall / 2
for sx in (-1, 1):
    for py in peg_ys:
        top += Pos(sx * peg_x, py, pin_z - peg_h / 2) * Cylinder(peg_d / 2, peg_h)
        bottom -= Pos(sx * peg_x, py, pin_z - (peg_h + 0.1) / 2) * Cylinder((peg_d + peg_clr) / 2, peg_h + 0.1)
bottom_print = Pos(0, 0, -z0) * bottom                       # outer face on z = 0
top_print = Pos(0, 0, z1) * Rot(180, 0, 0) * top             # flipped, outer face on z = 0

if __name__ == "__main__":
    try:  # preview in VS Code's OCP CAD Viewer when it is open (port 3939)
        from ocp_vscode import show
        show(bottom, top, names=["bottom", "top"])
    except Exception as exc:
        print(f"OCP-viewer utilgjengelig ({type(exc).__name__})")
    out = Path(os.environ.get("OUTDIR", Path(__file__).parent / "stl"))
    out.mkdir(parents=True, exist_ok=True)
    export_stl(bottom_print, str(out / "openrz67-camera-plug-bottom.stl"), ascii_format=True)  # make_3mf.py parses ASCII
    export_stl(top_print, str(out / "openrz67-camera-plug-top.stl"), ascii_format=True)
    bb = plug.bounding_box()
    print(f"plug {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, skin {skin:.2f}, cheeks {cheek:.2f}, "
          f"halves z-min {bottom_print.bounding_box().min.Z:.2f}/{top_print.bounding_box().min.Z:.2f}")

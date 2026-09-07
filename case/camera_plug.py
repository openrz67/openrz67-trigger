# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d>=0.11.1"]
# ///
"""Camera-end plug for the Mamiya RZ67 RC-outlet (build123d).

A printed shell around four ordinary female jumper-wire ends (2.54 mm Dupont
sleeves) so they go onto the camera's 4-pin remote port as one plug. The nose
fills the port's rectangular pocket (measured 13.91 x 3.57 mm, ~6.3 deep,
Ø0.8 round pins, pins centred in the pocket); two side cheeks give the lateral
location the loose/taped sleeves lack. A front plate with four pin holes stops
the sleeves sliding forward when the plug is pulled off the camera; the body
behind holds them in a channel and ends in an open chamber: wires bend 90 deg and exit downwards
(along the camera body), then the chamber is filled with hot glue as strain
relief. Pin order facing the port, left to right: 6 V (do NOT connect), GND,
S1, S2 — a triangle on top marks the 6 V side, like the camera's own mark.

Coordinates: x along the pin row (+x = right when facing the port), z up
(toward the sliding dust cover), -y = into the camera. z = 0 is the pocket
floor wall. Print standing on the rear face (nose up), no supports.

Run (exports stl/openrz67-camera-plug.stl):
    uv run camera_plug.py
"""

from pathlib import Path

from build123d import *

# --- Camera port (measured 2026-09-06, calipers) --------------------------------
pocket_w, pocket_h, pocket_d = 13.91, 3.57, 6.3   # depth is uncertain
pin_pitch, pin_d = 2.54, 0.8
pin_z = pocket_h / 2            # row centred: ~3.0 from the left wall, ~1.8 above the floor
# --- Dupont sleeve ----------------------------------------------------------------
sleeve, sleeve_len, sleeve_clr = 2.54, 14.0, 0.15
# --- Fit / walls (tune after the first print) --------------------------------------
nose_fit = 0.10        # per-side clearance of the nose in the pocket; go negative for press
cheek_len = pocket_d - 0.3
wall = 1.5
cover_setback = 1.5    # body above the pocket starts this far back, clearing the cover housing
chamber = 5.0          # glue / wire-bend chamber at the rear
mark = 2.0             # triangle side
plate_t, pin_hole = 0.8, 1.4   # front plate the sleeves butt against; pins pass through

nose_w, nose_h = pocket_w - 2 * nose_fit, pocket_h - 2 * nose_fit
ch_w, ch_h = 4 * sleeve + 2 * sleeve_clr, sleeve + 2 * sleeve_clr
body_w = nose_w + 2 * wall
body_len = sleeve_len - cheek_len + chamber
z_lo, z_hi = -1.0, pin_z + ch_h / 2 + wall
cheek = (nose_w - ch_w) / 2
assert cheek >= 1.2, f"cheek {cheek:.2f} too thin to print"
assert pin_z - ch_h / 2 > nose_fit and pin_z + ch_h / 2 < pocket_h - nose_fit, "sleeves hit the pocket walls"


def box(x0, y0, z0, dx, dy, dz):
    return Pos(x0 + dx / 2, y0 + dy / 2, z0 + dz / 2) * Box(dx, dy, dz)


nose = box(-nose_w / 2, -cheek_len, nose_fit, nose_w, cheek_len, nose_h)
body = box(-body_w / 2, 0, z_lo, body_w, body_len, pocket_h - z_lo)
body += box(-body_w / 2, cover_setback, pocket_h, body_w, body_len - cover_setback, z_hi - pocket_h)
plug = nose + body
plug -= box(-ch_w / 2, -cheek_len + plate_t, pin_z - ch_h / 2, ch_w, body_len + cheek_len + 1, ch_h)  # sleeve channel
for i in range(4):  # pin holes through the front plate
    plug -= Pos((i - 1.5) * pin_pitch, -cheek_len + plate_t / 2, pin_z) * Rot(90, 0, 0) * Cylinder(pin_hole / 2, plate_t + 1)
assert pocket_d - 0.3 - plate_t >= 4.0, "too little pin engagement in the sleeves"
plug -= box(-ch_w / 2, body_len - chamber, z_lo - 1, ch_w, chamber + 1, pin_z + ch_h / 2 - z_lo + 1)  # chamber, open back+bottom
tri = Pos(-1.5 * pin_pitch, body_len / 2 + cover_setback / 2, z_hi) * Rot(0, 0, 180) * Triangle(a=mark, b=mark, c=mark)
plug -= extrude(tri, -0.4)  # debossed 6 V mark, apex toward the camera

if __name__ == "__main__":
    try:  # preview in VS Code's OCP CAD Viewer when it is open (port 3939)
        from ocp_vscode import show
        show(plug, names=["camera-plug"])
    except Exception as exc:
        print(f"OCP-viewer utilgjengelig ({type(exc).__name__})")
    out = Path(__file__).parent / "stl"
    out.mkdir(exist_ok=True)
    export_stl(plug, str(out / "openrz67-camera-plug.stl"))
    bb = plug.bounding_box()
    print(f"plug {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, cheeks {cheek:.2f}, volume {plug.volume:.0f} mm3")

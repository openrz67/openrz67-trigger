# Off-board parts (external BOM)

Everything the trigger needs that is **not soldered on the PCB**. The on-board parts are in
[`pcb/kicad/out/openrz67-bom.csv`](pcb/kicad/out/openrz67-bom.csv). Mating connector part
numbers follow [`pcb/kicad/README.md`](pcb/kicad/README.md); case geometry follows
[`case/README.md`](case/README.md).

| # | Part | Spec | Qty | Mates with | Notes |
|---|------|------|-----|------------|-------|
| 1 | LiPo cell | 250 mAh, 3.7 V, **31 × 20 × 6 mm** (602030 size), with protection PCB, lead terminated in a **JST PHR-2** plug | 1 | `BAT1` (B2B-PH-K-S, top entry) | Lies flat under the PCB in the base pocket. Cell rated ≥ 120 mA charge (charger delivers 111 mA). Lead ~30–40 mm; longer leads must loop in the 2 mm air above the plug. |
| 2 | Power switch | **KCD11** snap-in rocker, SPST, panel cutout 13.5 × 8.5 mm, two 2.8 mm tabs | 1 | `S3` via wire | Snap-in from outside, no screws (merged to `main` 2026-09-16). Vendor drawings disagree by ~0.5 mm: measure the switch before printing the lid. |
| 3 | Switch lead | 2× **2.8 mm flag (90°) crimp receptacle**, 2× wire 26 AWG ~60 mm, 1× **JST PHR-2** housing + 2× **SPH-002T-P0.5S** contacts | 1 set | KCD11 tabs ↔ `S3` header | Flag type, not straight: a straight receptacle plus wire bend does not fit behind the switch. |
| 4 | Antenna | **Ebyte TX2400-FPC-2509**, 2.4 GHz FPC, 25 × 9 mm, 2 dBi, adhesive back, U.FL / IPEX-1 plug, ~100 mm cable | 1 | `A1` (Hirose U.FL-R-SMT-1(80)) | Stuck in the 25.6 × 9.6 × 0.3 recess in the lid ceiling. Board has **no** PCB antenna: BLE does not work without it. Not MHF4/IPEX-4. Fallback: Molex 146153-0050 (34.9 × 9, 50 mm cable). |
| 5 | Camera cable, board end | **JST XHP-4** housing + 4× **SXH-001T-P0.6** contacts, wire 26 AWG | 1 | `U4` (S4B-XH-A side entry, mouth through the right wall) | Mated plug sticks ~2.5 mm past the mouth (estimate, `xh_plug_proud`). |
| 6 | Camera cable, camera end | 4× female **2.54 mm Dupont sleeves** in the printed clamshell plug (`case/camera_plug.py`) | 1 | Mamiya RZ67 RC outlet (Ø0.8 pins, 2.54 pitch) | Triangle-marked position = camera 6 V pin, leave unwired. Camera ground stays isolated from ESP32 ground. |
| 7 | USB-C cable | Any USB 2.0 C cable, plug shell ≤ 10 × 4.6 mm at the case opening | 1 | `USB1` | Charging and flashing. |
| 8 | Foam tape | Double-sided, **1.5 mm** thick | ~40 × 20 mm | cell ↔ PCB underside | Cushions the cell under the board and holds it in the rib pocket. |
| 9 | Printed: base + lid | PLA or PETG, opaque; lid text via colour change at Z 0.6 | 1 each | — | `case/stl/openrz67-base.stl`, `openrz67-lid.stl`. Locating pins Ø1.85 press lightly into the PCB holes. |
| 10 | Printed: light pipe | **Clear** filament, 0.1 mm layers, 100 % infill, slow | 1 | lid funnel seat | `openrz67-lightpipe.stl`. Fix with one drop of clear glue in the funnel. |
| 11 | Printed: camera plug | PETG, two halves, press pegs | 1 pair | item 6 | `openrz67-camera-plug-{bottom,top}.stl`. |
| 12 | Glue | Clear CA or UV glue, one drop | — | light pipe | Optional: removable tack (Blu Tack) to hold the PCB on the pins during assembly. Never CA on the PCB or pins. |
| 13 | Bench only: J1 header | 1×3 2.54 mm pin header (3V3, GND, TX) on rev 3, 1×4 on rev 2 | 0 (DNP) | `J1` | Not fitted; the lid boss sits over it. Solder flying leads if needed. |

Status 2026-09-16: items 1, 4, 5–6 sourced or ordered; switch = KCD11 (item 2), dims unverified.

# PCB archive

Historical PCB material. Nothing here is the source of truth: the live design is
the KiCad project in [`../kicad/`](../kicad/).

## `2025-09-23-rev1/`

The fabrication package for **rev 1**, the revision that was actually manufactured
and assembled, exported from EasyEDA Pro on 2025-09-23. The enclosure in
[`../../case/`](../../case/) was first drawn against it; since 2026-09-05 it follows rev 2.

| File | What |
|---|---|
| `Gerber_…zip` | Gerber and drill files as ordered, including the board outline (`.GKO`) and `Drill_PTH_Through.DRL` |
| `BOM_…csv` | bill of materials as ordered |
| `PickAndPlace_…csv` | component placement as ordered; the source for the case's component positions |
| `3D_…step` | assembled board as STEP |
| `3D_…png` | render |

## `easyeda/`

The EasyEDA Pro project the KiCad port was made from, kept so the port stays
reversible.

| File | What |
|---|---|
| `ProPrj_…epro` | EasyEDA Pro **v2** export. This is the one that imports into KiCad; use it if the port ever has to be redone. |
| `ProPrj_…epro2` | EasyEDA Pro **v3** export. KiCad 10.0.6 imports this as an empty board, so it is kept for EasyEDA's own use only. |

The filenames carry spaces because they are the exports as EasyEDA produced them.
They are left unrenamed so they can be matched against the cloud project.

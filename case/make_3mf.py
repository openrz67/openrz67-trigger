#!/usr/bin/env python3
"""
Build a Bambu Studio / OrcaSlicer project .3mf by swapping fresh STL geometry
into a hand-made template project, keeping ALL slicer settings intact:
print profile, plate layout, and the per-part filament assignment (the light
pipe stays on its clear filament). Only the mesh blocks are replaced, plus the
SUB_PARTS meshes added inside an existing object (the lid text on filament 2).

The template was made once by hand in the slicer (import the STLs, arrange,
assign the light pipe to the clear filament, save project). After that, run
this script whenever the geometry changes instead of redoing that by hand.

How placement is preserved: each object's mesh lives in its own local frame,
centred by the slicer on import (model_vertex = stl_vertex - bbox_centre). The
slicer records that centre as source_offset_{x,y,z} in model_settings.config.
We reproduce that import by recentring each fresh mesh on ITS OWN bounding-box
centre and writing that centre back into source_offset. Recomputing (rather than
reusing the template's stored offset) matters: if the SCAD geometry changes size
later - e.g. back_margin grew the case in Y - the stored offset goes stale and
the part would load shifted off its plate spot. A fresh centre keeps base, lid
and light pipe aligned with each other and on the plate, and inherits the same
filament/extruder mapping.

Usage:
    python3 make_3mf.py [--template bambu-template.3mf] [--stl-dir stl]
                        [--out openrz67-case.3mf]

Pure stdlib (no numpy). ASCII STL in, project .3mf out.
"""
import argparse
import datetime
import os
import re
import shutil
import sys
import tempfile
import uuid
import zipfile

# parent STL -> [(sub-part STL, extruder)]: meshes added INSIDE an existing object as extra
# parts, sharing its frame and plate spot. This is how the lid text gets its own filament:
# the colour lives on the part, so it survives every re-export. Slicer colour painting does
# not (it is stored per triangle, and we replace the mesh), and QIDI Studio segfaults on a
# saved height-range modifier. Missing sub-part STLs are skipped (LID_TEXT_SHOW=false).
SUB_PARTS = {"openrz67-lid.stl": [("openrz67-lid-text.stl", 2)]}
BED = 256.0            # Bambu P2S; plates sit in a row, stride = 1.2 * bed (LOGICAL_PART_PLATE_GAP)


def parse_ascii_stl(path):
    """Return (vertices, triangles): unique vertex list + index triples.

    Vertices are deduplicated by rounded key so the 3mf gets a shared-vertex
    mesh (smaller, and what a hand mesh looks like). Winding is preserved from
    the STL facet order, so outward normals carry over.
    """
    verts = []
    index = {}
    tris = []
    cur = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if s.startswith("vertex"):
                _, x, y, z = s.split()
                cur.append((float(x), float(y), float(z)))
                if len(cur) == 3:
                    tri = []
                    for v in cur:
                        key = (round(v[0], 6), round(v[1], 6), round(v[2], 6))
                        i = index.get(key)
                        if i is None:
                            i = len(verts)
                            index[key] = i
                            verts.append(v)
                        tri.append(i)
                    tris.append(tuple(tri))
                    cur = []
    if cur:
        raise ValueError(f"{path}: dangling vertices (not a multiple of 3)")
    return verts, tris


def bbox_center(verts):
    """Centre of the mesh's axis-aligned bounding box (what the slicer centres on)."""
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)


def mesh_xml(verts, tris, offset):
    """Build the <mesh> block, translating each vertex by -offset."""
    ox, oy, oz = offset
    out = ["   <mesh>", "    <vertices>"]
    for x, y, z in verts:
        out.append(
            f'     <vertex x="{x - ox:.8g}" y="{y - oy:.8g}" z="{z - oz:.8g}"/>'
        )
    out.append("    </vertices>")
    out.append("    <triangles>")
    for a, b, c in tris:
        out.append(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>')
    out.append("    </triangles>")
    out.append("   </mesh>")
    return "\n".join(out)


def build_mapping(model_settings, dmodel):
    """object id -> dict(name, offset, model_path), joined across the two files."""
    objs = {}
    for m in re.finditer(r'<object id="(\d+)">(.*?)</object>', model_settings, re.S):
        oid, body = m.group(1), m.group(2)
        name = re.search(r'key="name" value="([^"]+)"', body)
        ox = re.search(r'source_offset_x" value="([-0-9.eE]+)"', body)
        oy = re.search(r'source_offset_y" value="([-0-9.eE]+)"', body)
        oz = re.search(r'source_offset_z" value="([-0-9.eE]+)"', body)
        if not (name and ox and oy and oz):
            continue
        objs[oid] = {
            "name": name.group(1),
            "offset": (float(ox.group(1)), float(oy.group(1)), float(oz.group(1))),
        }
    for m in re.finditer(
        r'<object id="(\d+)"[^>]*>\s*<components>\s*<component p:path="([^"]+)"',
        dmodel, re.S,
    ):
        oid, path = m.group(1), m.group(2)
        if oid in objs:
            objs[oid]["model_path"] = path.lstrip("/")
    return objs


def add_sub_parts(work, args, names, dmodel, model_settings, oid, parent, offset, next_id):
    """Add SUB_PARTS[parent] inside object `oid` as extra parts on their own extruder.

    The sub-mesh is recentred on the PARENT's bbox centre, not its own, so the two meshes
    stay in the same object frame and the text lands in its pockets. Returns the edited XML
    and the next free id.
    """
    rels_path = os.path.join(work, "3D", "_rels", "3dmodel.model.rels")
    for stl, extruder in SUB_PARTS.get(parent, []):
        path = os.path.join(args.stl_dir, stl)
        if not os.path.isfile(path):
            print(f"  {stl:30} not exported, skipping sub-part")
            continue
        verts, tris = parse_ascii_stl(path)
        mid = next_id
        next_id += 1
        fname = f"3D/Objects/object_{mid}.model"
        open(os.path.join(work, fname), "w").write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
            'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
            'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
            ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
            f'  <object id="{mid}" p:UUID="{uuid.uuid4()}" type="model">\n{mesh_xml(verts, tris, offset)}\n'
            '  </object>\n </resources>\n <build/>\n</model>\n')
        names.append(fname)
        rels = open(rels_path).read().replace(
            "</Relationships>",
            f' <Relationship Target="/{fname}" Id="rel-{mid}" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>')
        open(rels_path, "w").write(rels)

        comp = (f'    <component p:path="/{fname}" objectid="{mid}" p:UUID="{uuid.uuid4()}" '
                'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n')
        m = re.search(rf'(<object id="{oid}"[^>]*>\s*<components>.*?)(   </components>)', dmodel, re.S)
        if not m:
            sys.exit(f"could not find <components> of object {oid} to add {stl}")
        dmodel = dmodel[:m.end(1)] + comp + dmodel[m.end(1):]

        part = (f'    <part id="{mid}" subtype="normal_part">\n'
                f'      <metadata key="name" value="{stl}"/>\n'
                f'      <metadata key="extruder" value="{extruder}"/>\n'
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                f'      <metadata key="source_file" value="{stl}"/>\n'
                '      <metadata key="source_object_id" value="0"/>\n'
                '      <metadata key="source_volume_id" value="0"/>\n'
                + "".join(f'      <metadata key="source_offset_{a}" value="{v:.8g}"/>\n'
                          for a, v in zip("xyz", offset))
                + f'      <mesh_stat face_count="{len(tris)}" edges_fixed="0" degenerate_facets="0" '
                'facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n    </part>\n')
        m = re.search(rf'(<object id="{oid}">.*?</part>\n)(  </object>)', model_settings, re.S)
        if not m:
            sys.exit(f"could not find object {oid} in model_settings to add {stl}")
        model_settings = model_settings[:m.end(1)] + part + model_settings[m.end(1):]
        print(f"  {stl:30} {len(verts)} verts / {len(tris)} tris  -> part of {parent}, extruder {extruder}")
    return dmodel, model_settings, next_id


def main():
    ap = argparse.ArgumentParser(description="Swap STL geometry into a Bambu/Orca project 3mf.")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--template", default=os.path.join(here, "bambu-template.3mf"))
    ap.add_argument("--stl-dir", default=os.path.join(here, "stl"))
    ap.add_argument("--out", default=os.path.join(here, "openrz67-case.3mf"))
    args = ap.parse_args()

    if not os.path.isfile(args.template):
        sys.exit(f"template not found: {args.template}")

    work = tempfile.mkdtemp(prefix="mk3mf_")
    try:
        with zipfile.ZipFile(args.template) as z:
            names = z.namelist()
            z.extractall(work)

        ms_path = os.path.join(work, "Metadata", "model_settings.config")
        dm_path = os.path.join(work, "3D", "3dmodel.model")
        model_settings = open(ms_path).read()
        dmodel = open(dm_path).read()
        mapping = build_mapping(model_settings, dmodel)
        next_id = max(int(i) for i in re.findall(r'<object id="(\d+)"', dmodel)
                      + re.findall(r'<part id="(\d+)"', model_settings)) + 1

        for oid, info in mapping.items():
            stl = os.path.join(args.stl_dir, info["name"])
            if not os.path.isfile(stl):
                sys.exit(f"STL missing for object {oid}: {stl}")
            verts, tris = parse_ascii_stl(stl)
            # Recentre on THIS mesh's own bbox centre (a fresh slicer import), not the
            # template's stored offset, which goes stale when the geometry changes size.
            offset = bbox_center(verts)
            block = mesh_xml(verts, tris, offset)

            mfile = os.path.join(work, info["model_path"])
            txt = open(mfile).read()
            new_txt, n = re.subn(r"   <mesh>.*?</mesh>", block, txt, count=1, flags=re.S)
            if n != 1:
                sys.exit(f"could not locate <mesh> in {info['model_path']}")
            open(mfile, "w").write(new_txt)

            # keep the slicer's metadata honest: face count AND the recorded source offset
            # (the latter so it matches the centre we just recentred the mesh on)
            fc = len(tris)
            model_settings = re.sub(
                rf'(<object id="{oid}">.*?face_count=")\d+(")',
                rf"\g<1>{fc}\g<2>", model_settings, count=1, flags=re.S,
            )
            model_settings = re.sub(
                rf'(<object id="{oid}">.*?<mesh_stat face_count=")\d+(")',
                rf"\g<1>{fc}\g<2>", model_settings, count=1, flags=re.S,
            )
            for axis, val in zip("xyz", offset):
                model_settings = re.sub(
                    rf'(<object id="{oid}">.*?source_offset_{axis}" value=")[-0-9.eE]+(")',
                    rf"\g<1>{val:.8g}\g<2>", model_settings, count=1, flags=re.S,
                )
            # Sit the part ON the bed: the build item's translation was stored for the
            # template's mesh height, so a taller part sinks below the plate and the
            # slicer clips its floor (2026-09-13: the 15.4 mm base lost its 2 mm floor).
            # Apply the item's rotation to the recentred mesh and lift it by -min(z).
            m = re.search(rf'<item objectid="{oid}"[^>]*transform="([^"]+)"', dmodel)
            if m:
                t = [float(v) for v in m.group(1).split()]
                zmin = min(t[2] * (x - offset[0]) + t[5] * (y - offset[1]) + t[8] * (z - offset[2])
                           for x, y, z in verts)
                t[11] = -zmin
                dmodel = dmodel.replace(m.group(0), m.group(0).replace(
                    m.group(1), " ".join(f"{v:.8g}" for v in t)))
            cx, cy, cz = offset
            print(f"  {info['name']:30} {len(verts)} verts / {fc} tris "
                  f"@ ({cx:.3f},{cy:.3f},{cz:.3f}) bed z {-zmin if m else float('nan'):.2f} -> {info['model_path']}")

            dmodel, model_settings, next_id = add_sub_parts(
                work, args, names, dmodel, model_settings, oid, info["name"], offset, next_id)

        open(ms_path, "w").write(model_settings)

        # refresh the dates so the slicer doesn't show a stale project date
        today = datetime.date.today().isoformat()
        dmodel = re.sub(r'(<metadata name="ModificationDate">)[^<]*(</metadata>)',
                        rf"\g<1>{today}\g<2>", dmodel)
        open(dm_path, "w").write(dmodel)

        # rewrite the zip, preserving entry order (Content_Types first)
        tmp_out = args.out + ".tmp"
        with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as z:
            for name in names:
                z.write(os.path.join(work, name), name)
        os.replace(tmp_out, args.out)
        print(f"Wrote {args.out}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()

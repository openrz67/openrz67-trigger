#!/usr/bin/env python3
"""
Build a Bambu Studio / OrcaSlicer project .3mf by swapping fresh STL geometry
into a hand-made template project, keeping ALL slicer settings intact:
print profile, plate layout, and the per-part filament assignment (the light
pipe stays on its clear filament). Only the three mesh blocks are replaced.

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

Objects the template does not know (EXTRA_PLATES below) are appended as new
objects on their own plate, laid out in a row at the plate centre. That is how the
camera plug's two halves ride along on plate 2 without touching the hand-made plate 1.

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

# plate id -> STLs added as new objects (row at the plate centre, resting on the bed)
EXTRA_PLATES = {2: ["openrz67-camera-plug-bottom.stl", "openrz67-camera-plug-top.stl"]}
BED = 256.0            # Bambu P2S; plates sit in a row, stride = 1.2 * bed (LOGICAL_PART_PLATE_GAP)
GAP = 8.0              # between the extra objects


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


def add_extra_objects(work, args, names, dmodel, model_settings):
    """Append EXTRA_PLATES objects (new ids after the template's) and return the edited XML."""
    next_id = max(int(i) for i in re.findall(r'<object id="(\d+)"', dmodel)) + 1
    ident = max([int(i) for i in re.findall(r'identify_id" value="(\d+)"', model_settings)] + [0]) + 1
    rels_path = os.path.join(work, "3D", "_rels", "3dmodel.model.rels")
    rels = open(rels_path).read()
    res, items, cfg = [], [], []
    for plate, stls in EXTRA_PLATES.items():
        meshes = []
        for stl in stls:
            path = os.path.join(args.stl_dir, stl)
            if not os.path.isfile(path):
                sys.exit(f"STL missing for extra object: {path}")
            verts, tris = parse_ascii_stl(path)
            meshes.append((stl, verts, tris))
        row_w = sum(max(v[0] for v in m[1]) - min(v[0] for v in m[1]) for m in meshes) + GAP * (len(meshes) - 1)
        x = (plate - 1) * BED * 1.2 + BED / 2 - row_w / 2
        inst = []
        for stl, verts, tris in meshes:
            mid, oid = next_id, next_id + 1
            next_id += 2
            off = bbox_center(verts)
            w = max(v[0] for v in verts) - min(v[0] for v in verts)
            h = max(v[2] for v in verts) - min(v[2] for v in verts)
            fname = f"3D/Objects/object_{mid}.model"
            open(os.path.join(work, fname), "w").write(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
                'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
                'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
                ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                f'  <object id="{mid}" p:UUID="{uuid.uuid4()}" type="model">\n{mesh_xml(verts, tris, off)}\n'
                '  </object>\n </resources>\n <build/>\n</model>\n')
            names.append(fname)
            rels = rels.replace("</Relationships>",
                                f' <Relationship Target="/{fname}" Id="rel-{oid}" '
                                'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>')
            res.append(f'  <object id="{oid}" p:UUID="{uuid.uuid4()}" type="model">\n   <components>\n'
                       f'    <component p:path="/{fname}" objectid="{mid}" p:UUID="{uuid.uuid4()}" '
                       'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>\n   </components>\n  </object>\n')
            items.append(f'  <item objectid="{oid}" p:UUID="{uuid.uuid4()}" '
                         f'transform="1 0 0 0 1 0 0 0 1 {x + w / 2:.6g} {BED / 2:.6g} {h / 2:.6g}" printable="1"/>\n')
            cfg.append(f'  <object id="{oid}">\n    <metadata key="name" value="{stl}"/>\n    <metadata key="extruder" value="1"/>\n'
                       f'    <metadata face_count="{len(tris)}"/>\n    <part id="{mid}" subtype="normal_part">\n'
                       f'      <metadata key="name" value="{stl}"/>\n      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
                       f'      <metadata key="source_file" value="{stl}"/>\n      <metadata key="source_object_id" value="0"/>\n'
                       f'      <metadata key="source_volume_id" value="0"/>\n'
                       + "".join(f'      <metadata key="source_offset_{a}" value="{v:.8g}"/>\n' for a, v in zip("xyz", off))
                       + f'      <mesh_stat face_count="{len(tris)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" '
                       'facets_reversed="0" backwards_edges="0"/>\n    </part>\n  </object>\n')
            inst.append(f'    <model_instance>\n      <metadata key="object_id" value="{oid}"/>\n'
                        f'      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{ident}"/>\n'
                        '    </model_instance>\n')
            ident += 1
            x += w + GAP
            print(f"  {stl:30} {len(verts)} verts / {len(tris)} tris  -> plate {plate}, {fname}")
        cfg.append(f'  <plate>\n    <metadata key="plater_id" value="{plate}"/>\n    <metadata key="plater_name" value=""/>\n'
                   '    <metadata key="locked" value="false"/>\n    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
                   '    <metadata key="filament_maps" value="1 1 1 1 1"/>\n    <metadata key="filament_volume_maps" value="0 0 0 0 0"/>\n'
                   + "".join(inst) + '  </plate>\n')
    open(rels_path, "w").write(rels)
    dmodel = dmodel.replace(" </resources>", "".join(res) + " </resources>").replace(" </build>", "".join(items) + " </build>")
    model_settings = model_settings.replace("  <assemble>", "".join(cfg) + "  <assemble>")
    return dmodel, model_settings


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
            cx, cy, cz = offset
            print(f"  {info['name']:30} {len(verts)} verts / {fc} tris "
                  f"@ ({cx:.3f},{cy:.3f},{cz:.3f})  -> {info['model_path']}")

        dmodel, model_settings = add_extra_objects(work, args, names, dmodel, model_settings)
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

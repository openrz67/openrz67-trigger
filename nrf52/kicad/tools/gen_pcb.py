"""Build openrz67-nrf.kicad_pcb from design.py with KiCad's pcbnew.

Run with KiCad's bundled python from nrf52/kicad/:
  $KICAD_PY tools/gen_pcb.py [--dump]
--dump prints every pad position after placement (used while routing).
"""
import os, sys
import math
import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
import design as D
import gen_sch

MM = pcbnew.FromMM
V = pcbnew.VECTOR2I_MM
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(HERE, "openrz67-nrf.kicad_pcb")
PRETTY = os.path.join(HERE, f"{D.LIB}.pretty")
LAYER = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}


def rules(b):
    ds = b.GetDesignSettings()
    ds.m_MinClearance = MM(0.127); ds.m_TrackMinWidth = MM(0.127)
    ds.m_ViasMinSize = MM(0.40); ds.m_MinThroughDrill = MM(0.20)
    ds.m_HoleClearance = MM(0.175); ds.m_HoleToHoleMin = MM(0.30)
    ds.m_CopperEdgeClearance = MM(0.30); ds.m_SolderMaskExpansion = MM(0.051)
    ds.m_MinSilkTextHeight = MM(1.0); ds.m_MinSilkTextThickness = MM(0.15)
    ns = ds.m_NetSettings
    nc = pcbnew.NETCLASS("Default")
    nc.SetClearance(MM(0.127)); nc.SetTrackWidth(MM(0.2))
    nc.SetViaDiameter(MM(0.45)); nc.SetViaDrill(MM(0.25))
    ns.SetDefaultNetclass(nc)


def edge(b):
    w, h, r = D.BOARD_W, D.BOARD_H, D.BOARD_R
    def seg(a, c):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)
    def arc(start, mid, end):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(V(*start), V(*mid), V(*end)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)
    k = r * (1 - 0.70710678)
    seg((r, 0), (w - r, 0)); seg((w, r), (w, h - r)); seg((w - r, h), (r, h)); seg((0, h - r), (0, r))
    arc((w - r, 0), (w - k, k), (w, r)); arc((w, h - r), (w - k, h - k), (w - r, h))
    arc((r, h), (k, h - k), (0, h - r)); arc((0, r), (k, k), (r, 0))


def place(b):
    nets = {}
    for name in D.NETS:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
    padnet = {(ref, pad): net for net, pins in D.NETS.items() for ref, pad in pins}
    lib = open(os.path.join(HERE, f"{D.LIB}.kicad_sym"), encoding="utf-8").read()
    blocks = dict(gen_sch.symbol_blocks(lib))
    for ref, name in gen_sch.SYMBOL.items():
        for num, pname in gen_sch.pin_names(blocks[name]):
            if (ref, num) not in padnet:
                tag = f"{ref}-Pad{num}" if pname == num or pname.startswith("Pin_") else f"{ref}-{pname}-Pad{num}"
                padnet[(ref, num)] = f"unconnected-({tag})"
    for net in set(padnet.values()):
        if net not in nets:
            n = pcbnew.NETINFO_ITEM(b, net); b.Add(n); nets[net] = n
    fps = {}
    for ref, (fp, value, lcsc, mpn, mfr, layer, x, y, rot, descr) in D.PARTS.items():
        f = pcbnew.FootprintLoad(PRETTY, fp)
        if f is None:
            raise SystemExit(f"footprint {fp} not found")
        f.SetReference(ref); f.SetValue(value)
        f.SetFPIDAsString(f"{D.LIB}:{fp}")
        for k, v in (("Datasheet", ""), ("LCSC", lcsc), ("MPN", mpn), ("Manufacturer", mfr), ("Description", descr)):
            f.SetField(k, v)
            f.GetField(k).SetVisible(False)
        f.GetField("Description").SetLayer(pcbnew.F_Fab)
        b.Add(f)
        if layer == "B":
            f.Flip(V(0, 0), False)
        f.SetOrientationDegrees(rot)
        f.SetPosition(V(x, y))
        if not lcsc:
            f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        f.Reference().SetVisible(False)
        for p in f.Pads():
            net = padnet.get((ref, p.GetNumber()))
            if net:
                p.SetNet(nets[net])
            if ref == "U1" and net == "GND":   # edge pads: a thermal relief cannot get two spokes
                p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        fps[ref] = f
    for ref, pad in padnet:
        if ref not in fps or not any(p.GetNumber() == pad for p in fps[ref].Pads()):
            raise SystemExit(f"net references missing pad {ref}.{pad}")
    return nets, fps


def zones(b, nets):
    w, h = D.BOARD_W, D.BOARD_H
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(nets["GND"])
        z.Outline().NewOutline()
        for x, y in ((0, 0), (w, 0), (w, h), (0, h)):
            z.AppendCorner(V(x, y), -1)
        z.SetLocalClearance(MM(0.127)); z.SetMinThickness(MM(0.127))
        z.SetThermalReliefGap(MM(0.152)); z.SetThermalReliefSpokeWidth(MM(0.254))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(0)
        b.Add(z)
    x0, y0, x1, y1 = D.ANTENNA_KEEPOUT
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True)
    ls = pcbnew.LSET(); ls.addLayer(pcbnew.F_Cu); ls.addLayer(pcbnew.B_Cu); k.SetLayerSet(ls)
    k.SetDoNotAllowZoneFills(True); k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True)
    k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    k.SetZoneName("antenna")
    k.Outline().NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        k.AppendCorner(V(x, y), -1)
    b.Add(k)
    cx, cy, r_in, r_out = D.CELL_KEEPOUT
    c = pcbnew.ZONE(b); c.SetIsRuleArea(True); c.SetLayer(pcbnew.B_Cu)
    c.SetDoNotAllowZoneFills(True); c.SetDoNotAllowTracks(True); c.SetDoNotAllowVias(True)
    c.SetDoNotAllowPads(False); c.SetDoNotAllowFootprints(False)
    c.SetZoneName("cell rim")
    c.Outline().NewOutline()
    for i in range(72):
        a = math.tau * i / 72
        c.AppendCorner(V(cx + r_out * math.cos(a), cy + r_out * math.sin(a)), -1)
    hole = c.Outline().NewHole(0)
    for i in range(72):
        a = -math.tau * i / 72
        c.AppendCorner(V(cx + r_in * math.cos(a), cy + r_in * math.sin(a)), hole)
    b.Add(c)


def route(b, nets):
    for net, layer, width, pts in D.TRACKS:
        for a, c in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c))
            t.SetWidth(MM(width)); t.SetLayer(LAYER[layer]); t.SetNet(nets[net]); b.Add(t)
    for net, x, y in D.VIAS:
        v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetDrill(MM(0.25)); v.SetWidth(MM(0.45)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(nets[net]); b.Add(v)


def main():
    b = pcbnew.CreateEmptyBoard()
    b.SetCopperLayerCount(2)
    tb = b.GetTitleBlock(); tb.SetTitle("OpenRZ67 trigger, nRF52 / coin cell"); tb.SetRevision("A")
    rules(b); edge(b)
    nets, fps = place(b)
    zones(b, nets); route(b, nets)
    b.Save(PCB)
    b = pcbnew.LoadBoard(PCB)          # refill with the saved rules compiled
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    b.Save(PCB)
    if "--dump" in sys.argv:
        for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
            for p in f.Pads():
                pos = p.GetPosition()
                print(f"{f.GetReference()}.{p.GetNumber():>3} {p.GetNetname():8} "
                      f"({pcbnew.ToMM(pos.x):6.2f},{pcbnew.ToMM(pos.y):6.2f})")
    print("saved", PCB)


main()

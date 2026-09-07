"""Apply the EasyEDA-derived design rules and zone settings to the KiCad board.

This script is AUTHORITATIVE for design rules, net classes and zone settings: it
overwrites whatever the project file holds, so rule changes made in the KiCad GUI
are reverted the next time it runs. Edit the values here, not in Board Setup.

It saves both BOARD.kicad_pcb and the project's .kicad_pro in place, and is
idempotent: a second run on an unchanged project produces byte-identical files.
Close KiCad before running it.

Run with KiCad's bundled python:
  $KICAD_PY tools/post_import.py openrz67.kicad_pcb
"""
import sys, pcbnew

MM = pcbnew.FromMM
board_path = sys.argv[1]


def set_all(obj, **values):
    """Assign attributes, failing loudly if one does not exist.

    The SWIG wrapper accepts unknown attributes silently, so a typo or an API
    rename would otherwise turn a rule into a no-op instead of an error.
    """
    for name, value in values.items():
        if not hasattr(obj, name):
            raise AttributeError(f"{type(obj).__name__} has no attribute {name!r} "
                                 f"- the pcbnew API changed, check this script")
        setattr(obj, name, value)


def apply_rules(b):
    """Board-level limits (EasyEDA rules 1/2/5/9, mil -> mm) and net classes."""
    ds = b.GetDesignSettings()
    set_all(
        ds,
        m_MinClearance=MM(0.127),        # EasyEDA pour-to-track minimum
        m_TrackMinWidth=MM(0.127),
        m_ViasMinSize=MM(0.40),
        m_MinThroughDrill=MM(0.20),
        m_HoleClearance=MM(0.175),       # EasyEDA "Hole to Track"
        m_HoleToHoleMin=MM(0.30),
        m_CopperEdgeClearance=MM(0.30),  # JLCPCB recommendation
        m_SolderMaskExpansion=MM(0.051),
        m_SolderMaskMinWidth=MM(0.0),
        m_SolderPasteMargin=0,
        m_MinSilkTextHeight=MM(1.0),     # JLCPCB minimum silkscreen text height
        m_MinSilkTextThickness=MM(0.15),  # JLCPCB minimum silkscreen line width
    )

    # net classes (EasyEDA rule "3" widths, "5" vias, RULE_SELECTOR)
    ns = ds.m_NetSettings

    def netclass(name, clearance, track, via, drill, assign=()):
        nc = pcbnew.NETCLASS(name)
        nc.SetClearance(MM(clearance)); nc.SetTrackWidth(MM(track))
        nc.SetViaDiameter(MM(via)); nc.SetViaDrill(MM(drill))
        if name == "Default":
            ns.SetDefaultNetclass(nc)
        else:
            ns.SetNetclass(name, nc)
            for net in assign:
                ns.SetNetclassPatternAssignment(net, name)

    netclass("Default", 0.127, 0.16, 0.45, 0.20)
    netclass("gnd", 0.127, 0.13, 0.45, 0.20, ["GND"])
    netclass("3v", 0.127, 0.20, 0.45, 0.20, ["VCC", "VDDA"])
    netclass("5v", 0.127, 0.254, 0.50, 0.30, ["VBUS", "BAT+", "VSYS", "SW_SYS", "SW1", "SW2"])

    # the importer kept EasyEDA's layer names; restore KiCad's
    for lid, name in {
        pcbnew.F_Cu: "F.Cu", pcbnew.B_Cu: "B.Cu",
        pcbnew.F_SilkS: "F.SilkS", pcbnew.B_SilkS: "B.SilkS",
        pcbnew.F_Mask: "F.Mask", pcbnew.B_Mask: "B.Mask",
        pcbnew.F_Paste: "F.Paste", pcbnew.B_Paste: "B.Paste",
        pcbnew.Edge_Cuts: "Edge.Cuts", pcbnew.F_Fab: "F.Fab", pcbnew.B_Fab: "B.Fab",
        pcbnew.F_CrtYd: "F.Courtyard", pcbnew.B_CrtYd: "B.Courtyard",
    }.items():
        b.SetLayerName(lid, name)


def apply_zones(b):
    """Zone settings, then refill with KiCad's own filler."""
    for z in b.Zones():
        z.SetLocalClearance(MM(0.127))
        z.SetThermalReliefGap(MM(0.152))         # EasyEDA copperRegion gap, 6 mil
        z.SetThermalReliefSpokeWidth(MM(0.254))  # spoke, 10 mil
        z.SetMinThickness(MM(0.127))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_AREA)
        z.SetMinIslandArea(int(10 * 1e12))       # drop pour scraps under 10 mm2
        if z.GetNetname() == "VBUS":   # small pour at USB1: spokes do not fit
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


# The zone filler evaluates the DRC rules that were compiled when the board was
# loaded, not the ones just assigned. Save the rules, reload so the filler picks
# them up, then fill. Without this, the first run after a rule change fills with
# the previous clearances and only a second run converges.
b = pcbnew.LoadBoard(board_path)
apply_rules(b)
b.Save(board_path)

b = pcbnew.LoadBoard(board_path)
apply_zones(b)
b.Save(board_path)
print(f"saved {board_path}")

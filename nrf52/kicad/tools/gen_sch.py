"""Write openrz67-nrf.kicad_sch from design.py.

A netlist-style schematic: every symbol sits on a grid, every connected pin carries a
global label with the net name, every unused pin a no-connect. Pins come from the
project symbol library, so the schematic always matches the board the same model built.

  python3 tools/gen_sch.py
"""
import os, re, sys, uuid

sys.path.insert(0, os.path.dirname(__file__))
import design as D

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBFILE = os.path.join(HERE, f"{D.LIB}.kicad_sym")
SCH = os.path.join(HERE, "openrz67-nrf.kicad_sch")
PROJECT_UUID = "5d1c1d2e-0a3b-4c4d-9e5f-6a7b8c9d0e1f"

# ref -> library symbol name
SYMBOL = {
    "U1": "E73-2G4M08S1C", "BT1": "MY-2032-16", "J1": "SM04B-SRSS-TB",
    "U2": "TLP172AM", "U3": "TLP172AM", "R1": "R", "R2": "R", "R3": "R",
    "C1": "CL31A107MQHNNNE", "C2": "GRM155R71H104KE14D", "J2": "Conn_01x04",
    "SW1": "B3U-1000P", "D1": "KT-0603R", "Q1": "AO3401A",
}
# sheet positions (mm), symbol rotation
PLACE = {
    "U1": (60, 90, 0), "BT1": (150, 40, 0), "C1": (175, 40, 0), "C2": (195, 40, 0),
    "J2": (230, 40, 0), "SW1": (150, 80, 0), "D1": (175, 80, 0), "R3": (195, 80, 0),
    "R1": (150, 120, 0), "U2": (175, 120, 0), "R2": (150, 150, 0), "U3": (175, 150, 0),
    "J1": (230, 135, 0), "Q1": (210, 60, 0),
}


def tokenize(s):
    return re.findall(r'"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+', s)


def parse(tokens, i=0):
    out = []
    while i < len(tokens):
        t = tokens[i]
        if t == "(":
            sub, i = parse(tokens, i + 1); out.append(sub)
        elif t == ")":
            return out, i + 1
        else:
            out.append(t[1:-1] if t.startswith('"') else t); i += 1
    return out, i


def symbol_blocks(text):
    """Top-level symbol blocks of a .kicad_sym as (name, raw_text)."""
    for m in re.finditer(r'^\(symbol "([^"]+)"', text, re.M):
        depth = 0; j = m.start()
        while True:
            c = text[j]
            if c == '(': depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0: break
            j += 1
        yield m.group(1), text[m.start():j + 1]


def pins(block):
    """(number, x, y, angle) per pin, all units, lib coordinates (y up)."""
    tree, _ = parse(tokenize(block))
    found = []
    def walk(node):
        if isinstance(node, list):
            if node and node[0] == "pin":
                at = next(n for n in node if isinstance(n, list) and n[0] == "at")
                num = next(n for n in node if isinstance(n, list) and n[0] == "number")[1]
                found.append((num, float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0))
            for n in node: walk(n)
    walk(tree)
    return found


def pin_names(block):
    """(number, name) per pin."""
    tree, _ = parse(tokenize(block))
    found = []
    def walk(node):
        if isinstance(node, list):
            if node and node[0] == "pin":
                name = next(n for n in node if isinstance(n, list) and n[0] == "name")[1]
                num = next(n for n in node if isinstance(n, list) and n[0] == "number")[1]
                found.append((num, name))
            for n in node: walk(n)
    walk(tree)
    return found


def rot(x, y, deg):
    return {0: (x, y), 90: (-y, x), 180: (-x, -y), 270: (y, -x)}[deg % 360]


def u():
    return str(uuid.uuid4())


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')


def main():
    lib = open(LIBFILE, encoding="utf-8").read()
    blocks = dict(symbol_blocks(lib))
    for name in set(SYMBOL.values()) | {"PWR_FLAG"}:
        if name not in blocks:
            raise SystemExit(f"symbol {name} missing from {LIBFILE}")
    padnet = {(ref, pad): net for net, pl in D.NETS.items() for ref, pad in pl}

    out = []
    w = out.append
    w('(kicad_sch (version 20250114) (generator "gen_sch") (generator_version "10.0")')
    w(f'  (uuid "{PROJECT_UUID}")')
    w('  (paper "A4")')
    w('  (title_block (title "OpenRZ67 trigger, nRF52 / coin cell") (rev "A") (company "openrz67"))')
    w('  (lib_symbols')
    for name in sorted(set(SYMBOL.values()) | {"PWR_FLAG"}):
        blk = blocks[name].replace(f'(symbol "{name}"', f'(symbol "{D.LIB}:{name}"', 1)
        w("    " + blk.replace("\n", "\n    "))
    w('  )')

    labels, ncs = [], []
    for ref, (fp, value, lcsc, mpn, mfr, layer, *_rest, descr) in D.PARTS.items():
        name = SYMBOL[ref]; X, Y, R = PLACE[ref]
        w(f'  (symbol (lib_id "{D.LIB}:{name}") (at {X} {Y} {R}) (unit 1)')
        w(f'    (in_bom {"yes" if lcsc else "no"}) (on_board yes) (dnp no)')
        w(f'    (uuid "{u()}")')
        props = [("Reference", ref, False, -6), ("Value", value, False, 6),
                 ("Footprint", f"{D.LIB}:{fp}", True, 0), ("Datasheet", "", True, 0),
                 ("Description", descr, True, 0), ("LCSC", lcsc, True, 0),
                 ("MPN", mpn, True, 0), ("Manufacturer", mfr, True, 0)]
        for k, v, hide, dy in props:
            w(f'    (property "{k}" "{esc(v)}" (at {X} {Y + dy} 0)')
            w(f'      (effects (font (size 1.27 1.27)){" hide" if hide else ""})')
            w('    )')
        for num, px, py, pa in pins(blocks[name]):
            w(f'    (pin "{num}" (uuid "{u()}"))')
            rx, ry = rot(px, -py, R)        # lib y up -> sheet y down
            lx, ly = round(X + rx, 4), round(Y + ry, 4)
            la = int((pa + 180) % 360) if R == 0 else int((pa + 180 + R) % 360)
            net = padnet.get((ref, num))
            if net:
                labels.append((net, lx, ly, la))
            else:
                ncs.append((lx, ly))
        w('    (instances')
        w(f'      (project "openrz67-nrf" (path "/{PROJECT_UUID}" (reference "{ref}") (unit 1)))')
        w('    )')
        w('  )')

    # power flags so ERC sees the cell, VDD (through Q1) and GND driven
    for i, (net, X, Y) in enumerate((("VDD", 150, 20), ("GND", 175, 20), ("VBAT", 200, 20))):
        w(f'  (symbol (lib_id "{D.LIB}:PWR_FLAG") (at {X} {Y} 0) (unit 1)')
        w('    (in_bom no) (on_board no) (dnp no)')
        w(f'    (uuid "{u()}")')
        w(f'    (property "Reference" "#FLG{i+1}" (at {X} {Y - 4} 0) (effects (font (size 1.27 1.27)) hide))')
        w(f'    (property "Value" "PWR_FLAG" (at {X} {Y - 2} 0) (effects (font (size 1.27 1.27))))')
        w(f'    (property "Footprint" "" (at {X} {Y} 0) (effects (font (size 1.27 1.27)) hide))')
        w(f'    (property "Datasheet" "" (at {X} {Y} 0) (effects (font (size 1.27 1.27)) hide))')
        w(f'    (pin "1" (uuid "{u()}"))')
        w(f'    (instances (project "openrz67-nrf" (path "/{PROJECT_UUID}" (reference "#FLG{i+1}") (unit 1))))')
        w('  )')
        labels.append((net, X, Y, 270))

    for net, x, y, a in labels:
        just = {0: "left", 180: "right", 90: "left", 270: "right"}[a]
        w(f'  (global_label "{net}" (shape passive) (at {x} {y} {a}) (fields_autoplaced yes)')
        w(f'    (effects (font (size 1.27 1.27)) (justify {just}))')
        w(f'    (uuid "{u()}")')
        w('  )')
    for x, y in ncs:
        w(f'  (no_connect (at {x} {y}) (uuid "{u()}"))')
    w('  (sheet_instances (path "/" (page "1")))')
    w('  (embedded_fonts no)')
    w(')')
    open(SCH, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("saved", SCH, f"{len(labels)} labels, {len(ncs)} no-connects")


if __name__ == "__main__":
    main()

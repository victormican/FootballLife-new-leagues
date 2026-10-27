"""limits.py -- what is used, what the caps are, and which cap binds first.

The caps are not one number in one place.  The block's arrays are sized by
patches/layout.json (tools/patchset.py generates sider/fl26caps.<set>.lua from it); the Edit's
club list, the Cup menu list, the Select Team slots and the competition ids each have their own
ceiling in a native module or in the data.  This reads all of them and prints them next to what
the world in the livecpk actually holds, so the answer to "can I add another league?" is a
measurement.

    python tools/limits.py
    python tools/limits.py --root <livecpk root> --layout patches/layout.json

The used counts come from the .bin sizes in the root (pesdb.py's record sizes), so a table that
is packaged (WESYS) is unpacked first.  Nothing here writes anything.
"""

import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import pesdb

DEFAULT_ROOT = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26All"

# Caps that do not live in layout.json, with the file that holds them.
OTHER_CAPS = [
    ("clubes del Edit", 4700, "tools/native/fl26edit.c (TEAMS)"),
    ("slots de Select Team", 250, "sider/experimental/fl26slots250.lua"),
    ("copas del menu", 512, "tools/native/fl26swiss.c (MAX_CCUP)"),
    ("ids de competicion", 511, "sider/experimental/fl26cid16.lua"),
    ("clubes por regulacion", 48, "estructural: lista de 48 en fl26clubs.c"),
]


def read_table(root, name):
    """the bytes of a pesdb table, unpacked, or None"""
    p = os.path.join(root, "common", "etc", "pesdb", name)
    if not os.path.exists(p):
        return None
    d = open(p, "rb").read()
    if d[:8].startswith(b"WESYS") or d[3:8] == b"WESYS":
        try:
            return pesdb.wesys_unpack(d)
        except Exception:
            return None
    return d


def count(root, name):
    d = read_table(root, name)
    if d is None:
        return None
    rec = pesdb.REC.get(name[:-4])
    return len(d) // rec if rec else len(d)


def world(root):
    p = os.path.join(os.path.dirname(root.rstrip("\\/")), "modules", "fl26world.txt")
    if not os.path.exists(p):
        p = os.path.join(root, "fl26world.txt")
    if not os.path.exists(p):
        return {"lines": [], "leagues": 0, "cups": 0, "slots": set()}
    out = {"lines": [], "leagues": 0, "cups": 0, "slots": set()}
    for line in open(p, encoding="utf-8-sig", errors="replace"):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out["lines"].append(s)
        w = s.split()
        if not w:
            continue
        if w[0] == "league":
            out["leagues"] += 1
        elif w[0] in ("cup", "knockout"):
            out["cups"] += 1
        for tok in w:
            if tok.startswith("slot="):
                try:
                    out["slots"].add(int(tok[5:]))
                except ValueError:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--layout", default=os.path.join(ROOT, "patches", "layout.json"))
    a = ap.parse_args()

    L = json.load(open(a.layout))
    H = lambda s: int(s, 16) if isinstance(s, str) else s

    rows = []  # (what, used, cap, where)
    arrays = L["arrays"]
    for name, table in (
        ("players", "Player.bin"),
        ("teams", "Team.bin"),
        ("coaches", "Coach.bin"),
        ("regulations", "CompetitionRegulation.bin"),
    ):
        if name in arrays and "cap_new" in arrays[name]:
            rows.append(
                (
                    name,
                    count(a.root, table),
                    arrays[name]["cap_new"],
                    "layout.json (%s)" % table,
                )
            )
    if "rec596" in arrays:
        rows.append(
            (
                "partidos del calendario",
                None,
                arrays["rec596"]["cap_new"],
                "layout.json (rec596)",
            )
        )
    if "fixtures" in arrays:
        rows.append(
            (
                "rondas (fixtures)",
                None,
                arrays["fixtures"]["cap_new"],
                "layout.json (fixtures)",
            )
        )

    w = world(a.root)
    rows.append(("ligas del world", w["leagues"], None, "fl26world.txt"))
    rows.append(("copas del world", w["cups"], None, "fl26world.txt"))
    rows.append(
        ("slots usados", len(w["slots"]) or None, 250, "fl26world.txt + fl26slots250")
    )
    rows.append(
        (
            "clubes en entradas",
            count(a.root, "CompetitionEntry.bin"),
            None,
            "CompetitionEntry.bin",
        )
    )
    rows.append(
        (
            "asignaciones de jugador",
            count(a.root, "PlayerAssignment.bin"),
            None,
            "PlayerAssignment.bin",
        )
    )
    for name, cap, where in OTHER_CAPS:
        used = None
        if name == "clubes del Edit":
            used = count(a.root, "Team.bin")
        rows.append((name, used, cap, where))

    def fmt(v):
        return "-" if v is None else str(v)

    print("%-28s %9s %9s %9s  %s" % ("tope", "usado", "limite", "libre", "fuente"))
    print("-" * 100)
    binding = None
    for what, used, cap, where in rows:
        free = "-"
        if used is not None and cap:
            free = str(cap - used)
            if binding is None or (cap - used) < binding[1]:
                binding = ("%s (%s)" % (what, where), cap - used)
        elif cap is not None:
            free = str(cap)
        print("%-28s %9s %9s %9s  %s" % (what, fmt(used), fmt(cap), free, where))

    print()
    print("root: %s" % a.root)
    print("world: %d lineas" % len(w["lines"]))
    if binding:
        print("el siguiente muro es: %s -- quedan %d" % binding)
    else:
        print("el siguiente muro es: el primero con 'libre' a 0")
    print()
    print(
        "Para subir un tope de layout.json: edita cap_new y genera el set completo con"
    )
    print(
        "  python tools/patchset.py teams-coaches-regs-players-dates-matches-upper-mlcopy-fixtures-calendar"
    )
    print(
        "y reinstala sider/fl26caps.<set>.lua como modules/fl26caps.lua.  Es todo o nada:"
    )
    print(
        "el aplicador no escribe si un solo byte no coincide (asi que ningun otro modulo"
    )
    print("puede tocar esas direcciones).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""python build_leagues.py --base <world pesdb> --worldfile <fl26world.txt> [--dry]

Free generic test leagues and put real ones in their place.

The world of this branch is full (255 of 255 competitions) and 64 of its leagues are
"Generic League NN" scaffolding. This frees the ones the new leagues need (highest regulation
id first, and only leagues whose competition id is theirs alone) and adds the new leagues in
their place, on free slots (`slot=-1`, `fl26comptab` picks). The clubs are filled afterwards
with `fill_group.py`, which keeps what the game already shipped for that country and only
makes generic clubs for the shortfall.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

# name, region(id), country(flag id), conf, clubs, prototype code
SPECS = [
    ("Copa Colombia", 38, 148, 4, 48, "COLOMBIA_D1_LEAGUE"),
    ("Copa Especial Colombia", 38, 148, 4, 30, "COLOMBIA_D1_LEAGUE"),
    ("Copa Argentina", 29, 144, 4, 48, "ARGENTINA_D1_LEAGUE"),
    ("Italia Serie D", 104, 215, 2, 30, "ITALY_D2_LEAGUE"),
    ("Espa\u00f1a Segunda Federaci\u00f3n", 105, 236, 2, 30, "SPAIN_D2_LEAGUE"),
    ("Croacia Prva NL", 100, 200, 2, 20, "ENGLAND_D1_LEAGUE"),
    ("Croacia Druga NL", 100, 200, 2, 20, "ENGLAND_D1_LEAGUE"),
    ("Portugal 2", 6, 228, 2, 20, "PORTUGAL_D1_LEAGUE"),
    ("Pa\u00edses Bajos KKD", 7, 224, 2, 20, "NETHERLANDS_D1_LEAGUE"),
    ("B\u00e9lgica CPL", 8, 197, 2, 20, "BELGIUM_D1_LEAGUE"),
    ("Grecia SL2", 10, 211, 2, 20, "GREECE_D1_LEAGUE"),
    ("Serbia 2", 94, 303, 2, 20, "ENGLAND_D1_LEAGUE"),
]


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    dry = "--dry" in a

    comp = M.load(base, "Competition.bin")
    regs = M.load(base, "CompetitionRegulation.bin")
    ents = M.load(base, "CompetitionEntry.bin")
    lines = io.open(wf, encoding="utf-8", errors="replace").read().splitlines()

    world = []
    for n, line in enumerate(lines):
        w = line.split()
        if len(w) > 1 and w[0] == "league" and w[1].isdigit():
            kv = dict(x.split("=", 1) for x in w[2:] if "=" in x)
            if "name=" in line:
                kv["name"] = line.split("name=", 1)[1]
            world.append((n, int(w[1]), kv))
    cid_count = {}
    for _n, _reg, kv in world:
        c = int(kv["cid"])
        cid_count[c] = cid_count.get(c, 0) + 1

    need = len(SPECS)
    genc = [
        (reg, int(kv["cid"]), n)
        for n, reg, kv in world
        if kv.get("name", "").startswith("Generic League")
        and cid_count[int(kv["cid"])] == 1
    ]
    genc.sort(reverse=True)
    if len(genc) < need:
        print("only %d freeable generic league(s), need %d" % (len(genc), need))
        return 1
    free = genc[:need]
    print("freeing %d generic league(s):" % need)
    for reg, cid, _n in free:
        print("  reg %d cid %d" % (reg, cid))
    if dry:
        for name, region, country, conf, clubs, proto in SPECS:
            print(
                "  + %-28s cid=%d reg=%d %d clubs (proto %s)"
                % (name, 0, 0, clubs, proto)
            )
        print("dry run: nothing written")
        return 0

    drop_cids = {c for _r, c, _n in free}
    drop_regs = {r for r, _c, _n in free}
    drop_lines = {n for _r, _c, n in free}

    comp = bytearray(
        b"".join(
            comp[i : i + M.COMP]
            for i in range(0, len(comp), M.COMP)
            if comp[i + M.CID_OFF] not in drop_cids
        )
    )
    regs = bytearray(
        b"".join(
            regs[i : i + M.REG]
            for i in range(0, len(regs), M.REG)
            if int.from_bytes(regs[i + M.R_ID : i + M.R_ID + 2], "little")
            not in drop_regs
        )
    )
    ents = bytearray(
        b"".join(
            ents[i : i + M.ENT]
            for i in range(0, len(ents), M.ENT)
            if ents[i + M.E_CID] not in drop_cids
        )
    )
    lines = [l for n, l in enumerate(lines) if n not in drop_lines]

    cids = [c for _r, c, _n in free]
    reg_ids = [r for r, _c, _n in free]
    made = []
    for k, (name, region, country, conf, clubs, proto) in enumerate(SPECS):
        cid, reg = cids[k], reg_ids[k]
        code = "FL_" + "".join(ch for ch in name.upper() if ch.isalnum())[:12]
        M.add_league(
            comp,
            regs,
            ents,
            cid,
            reg,
            M.enc_region(region),
            name,
            code,
            [],
            proto_code=proto,
        )
        lines.append(
            "league %d cid=%d region=%d country=%d conf=%d slot=-1 tier=1 promote=0 demote=0 "
            "clubs=0 legs=2 kickoff=99 name=%s"
            % (reg, cid, region, country, conf, name)
        )
        made.append((reg, cid, name))
        print("  + %-28s cid=%d reg=%d" % (name, cid, reg))

    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(
        "wrote %d league(s); fill them with fill_group.py --reg <id> --to <clubs>"
        % len(made)
    )
    for reg, cid, name in made:
        print("  reg %d cid %d %s" % (reg, cid, name))
    return 0


if __name__ == "__main__":
    sys.exit(main())

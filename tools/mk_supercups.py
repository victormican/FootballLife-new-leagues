r"""python mk_supercups.py --world <pesdb dir> --worldfile <fl26world.txt>
                         [--go] [--dry] [--limit N] [--only TEXT]

Give every country of the world a super cup: the league's champion against the national cup's
winner, one match, before the season.

How it is built
    Each one is a two-club knockout copied from the game's own Pro League Supercup
    (regulation 128, cid 113, code BELGIUM_SUPER_CUP): a Competition row, a Regulation row
    (type 3, two teams, format 2) and two entries (the league's first two clubs as a stand-in).
    fl26swiss fills them at run time from the world file line, which is what makes it a super
    cup and not a fixed match:

        ccup <reg> ko=<reg> groups=0 entry=<league reg>:1,<cup reg>:0 cid=<cid>
             fill=2 national=1 like=128 name=Supercopa de <country>

    entry `<league>:1` is the league's champion, `<cup>:0` the winner of the national cup --
    the same pair the game's own Supercopa de EspaÃ±a line uses.

Which countries
    A top division (tier 1) that has a national cup whose entries all come from that league
    (`entry=<league>:<position>,...`).  A country that already has a super cup for that pair
    is left alone.

    --dry (default) prints the plan; --go writes the tables and both copies of the world file,
    after copying them to *.before-supercups.
"""

import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M
import pesdb

COMP, REG, ENT = 36, 2352, 12
SUPER_LIKE = "BELGIUM_SUPER_CUP"
TEMPLATE_REG = 128  # the game's Pro League Supercup
R_RID, R_CID, R_TYPE, R_TEAMS = 0x02, 0x08, 0x09, 0x0B
R_CID_HI = 0x492


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def cstr(b):
    return bytes(b).split(b"\0")[0].decode("utf-8", "replace").strip()


def read_world(path):
    leagues, cups, lines = {}, {}, []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.split()
            lines.append(line.rstrip("\n"))
            if not parts:
                continue
            if parts[0] == "league":
                d = {"reg": parts[1]}
                for tok in parts[2:]:
                    if "=" in tok:
                        k, v = tok.split("=", 1)
                        d[k] = v
                m = re.search(r"name=(.*)$", line)
                if m:
                    d["name"] = m.group(1).strip()
                leagues[d["reg"]] = d
            elif parts[0] == "ccup":
                d = {"reg": parts[1]}
                for tok in parts[2:]:
                    if "=" in tok:
                        k, v = tok.split("=", 1)
                        d[k] = v
                m = re.search(r"name=(.*)$", line)
                if m:
                    d["name"] = m.group(1).strip()
                cups[d["reg"]] = d
    return leagues, cups, lines


def set_reg_name(r, name):
    """the 20 language slots of a regulation: 0..9 from 0x14, a 0x20-byte gap, 10..19 from
    0x4B2 (pesdb.reg_set_name writes them in a row and lands on the cid's high byte)"""
    b = pesdb.game_text(name).encode("utf-8")[:114]
    b = b.decode("utf-8", "ignore").encode("utf-8")
    for k in range(10):
        o = 0x14 + k * 115
        r[o:o + 115] = b + bytes(115 - len(b))
    for k in range(10):
        o = 0x4B2 + k * 115
        r[o:o + 115] = b + bytes(115 - len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--worldfile", required=True)
    ap.add_argument("--go", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    leagues, cups, lines = read_world(a.worldfile)
    comp = load(a.world, "Competition.bin")
    regs = load(a.world, "CompetitionRegulation.bin")
    ents = load(a.world, "CompetitionEntry.bin")

    used_c = {
        comp[o + 5] | (comp[o + 7] << 8) for o in range(0, len(comp) - COMP + 1, COMP)
    }
    used_r = {
        int.from_bytes(regs[o + R_RID : o + R_RID + 2], "little")
        for o in range(0, len(regs) - REG + 1, REG)
    }
    max_eid = max(
        int.from_bytes(ents[o + 4 : o + 8], "little")
        for o in range(0, len(ents) - ENT + 1, ENT)
    )

    # the super cups that already exist, by the pair they fill
    have = set()
    for c in cups.values():
        e = c.get("entry", "")
        m = re.match(r"^\s*(\d+):1\s*,\s*(\d+):0\s*$", e)
        if m:
            have.add((m.group(1), m.group(2)))

    pairs = []
    for reg, cup in cups.items():
        name = cup.get("name", "")
        if not name.endswith(" Cup"):
            continue
        refs = re.findall(r"(\d+):(\d+)", cup.get("entry", ""))
        if not refs:
            continue
        lrs = {r for r, _p in refs}
        if len(lrs) != 1:
            continue
        lr = lrs.pop()
        L = leagues.get(lr)
        if not L or L.get("tier") != "1":
            continue
        if (lr, reg) in have:
            continue
        country = name[:-4].strip()
        if a.only and a.only.lower() not in country.lower():
            continue
        pairs.append((lr, reg, country))
    pairs.sort(key=lambda x: x[2])
    if a.limit:
        pairs = pairs[: a.limit]
    print("super cups to build: %d" % len(pairs))
    if not pairs:
        return

    tpl_c = next(
        o
        for o in range(0, len(comp) - COMP + 1, COMP)
        if (comp[o + 5] | (comp[o + 7] << 8)) == 113
    )
    tpl_r = next(
        o
        for o in range(0, len(regs) - REG + 1, REG)
        if int.from_bytes(regs[o + R_RID : o + R_RID + 2], "little") == TEMPLATE_REG
    )
    tpl_e = next(
        o
        for o in range(0, len(ents) - ENT + 1, ENT)
        if (ents[o + 8] | (ents[o + 0x0B] << 8)) == 113
    )

    free_c = [c for c in range(256, 1024) if c not in used_c and (c & 0xFF)]
    free_r = [r for r in range(1, 1201) if r not in used_r]
    if len(free_c) < len(pairs) or len(free_r) < len(pairs):
        raise SystemExit(
            "not enough free ids: %d cids, %d regulations for %d cups"
            % (len(free_c), len(free_r), len(pairs))
        )

    new_cups, new_lines, made = [], [], []
    for i, (lr, creg, country) in enumerate(pairs):
        cid, rid = free_c[i], free_r[i]
        region = int(leagues[lr].get("region", 0))
        code = ("FL_SUP_%d" % cid).encode()[:27]

        c = bytearray(comp[tpl_c : tpl_c + COMP])
        M.set_comp_cid(c, 0, cid)
        c[M.REGION_OFF] = M.enc_region(region)
        c[M.CODE_OFF : M.CODE_OFF + 28] = code.ljust(28, b"\0")
        c[0x14:0x24] = ("Supercopa %s" % country).encode("utf-8")[:15].ljust(16, b"\0")

        r = bytearray(regs[tpl_r : tpl_r + REG])
        r[R_RID : R_RID + 2] = rid.to_bytes(2, "little")
        r[R_CID] = cid & 0xFF
        r[R_CID_HI] = (cid >> 8) & 0xFF
        r[R_TYPE] = 3
        r[R_TEAMS] = (r[R_TEAMS] & 0xC0) | 2
        set_reg_name(r, "Supercopa %s" % country)
        r[R_CID_HI] = (cid >> 8) & 0xFF

        top = sorted(
            (ents[o + 9], int.from_bytes(ents[o : o + 4], "little"))
            for o in range(0, len(ents) - ENT + 1, ENT)
            if (ents[o + 8] | (ents[o + 0x0B] << 8))
            == int(leagues[lr].get("cid", "0") or 0)
        )
        teams = [t for _p, t in top][:2]
        if len(teams) < 2:
            print("  SKIP %-22s league %s has no entries" % (country, lr))
            continue
        rows = []
        for n, t in enumerate(teams, 1):
            e = bytearray(ents[tpl_e : tpl_e + ENT])
            max_eid += 1
            e[0:4] = t.to_bytes(4, "little")
            e[4:8] = max_eid.to_bytes(4, "little")
            e[8] = cid & 0xFF
            e[9] = n
            e[0x0B] = (cid >> 8) & 0xFF
            rows.append(e)

        line = (
            "ccup %d ko=%d groups=0 entry=%s:1,%s:0 cid=%d fill=2 national=1 like=%d "
            "name=Supercopa %s" % (rid, rid, lr, creg, cid, TEMPLATE_REG, country)
        )
        made.append((country, cid, rid, lr, creg, line))
        new_cups.append((c, r, rows))
        new_lines.append(line)
        used_c.append(cid) if False else None

    print("built: %d" % len(made))
    for country, cid, rid, lr, creg, _line in made[:8]:
        print(
            "   %-24s cid %-4d reg %-4d  liga %s + copa %s"
            % (country, cid, rid, lr, creg)
        )
    if len(made) > 8:
        print("   ... y %d mas" % (len(made) - 8))

    if not a.go:
        print("dry run: nothing written (pass --go)")
        return

    for n in ("Competition.bin", "CompetitionRegulation.bin", "CompetitionEntry.bin"):
        dst = os.path.join(a.world, n + ".before-supercups")
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.world, n), dst)
    for c, r, rows in new_cups:
        comp += c
        regs += r
        for e in rows:
            ents += e
    with open(os.path.join(a.world, "Competition.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(comp)))
    with open(os.path.join(a.world, "CompetitionRegulation.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(regs)))
    with open(os.path.join(a.world, "CompetitionEntry.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(ents)))

    # the ccup block stays in name order
    first = next((i for i, l in enumerate(lines) if l.startswith("ccup ")), None)
    body = [l for l in lines if l.startswith("ccup ")]
    body += new_lines
    body.sort(key=lambda l: (l.split("name=", 1)[-1].strip().lower(), l))
    rest = [l for l in lines if not l.startswith("ccup ")]
    if first is None:
        out = rest + body
    else:
        out = rest[:first] + body + rest[first:]
    text = "\n".join(out) + "\n"
    dst = a.worldfile + ".before-supercups"
    if not os.path.exists(dst):
        shutil.copy2(a.worldfile, dst)
    with open(a.worldfile, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    live = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(a.world)))),
        "fl26world.txt",
    )
    if os.path.abspath(live) != os.path.abspath(a.worldfile):
        with open(live, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print("written: %d cups, world file (livecpk and modules)" % len(made))


if __name__ == "__main__":
    main()



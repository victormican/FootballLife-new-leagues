"""python other_groups.py --base <world pesdb> --worldfile <fl26world.txt> [--dry]

Give the exe's "other" buckets a league of their own, on the slot the game draws them from.

The game keeps these clubs apart with the high nibble of Team.bin +0x4f (1 Classics, 2 Other
European, 5 ML defaults, 6 Other Latin American) and shows them in the sections named after
the slots in fl26slotnames. That means a club of those buckets can be in no competition at all
(the section still lists it) or in one it does not belong to (a cup took it by country).

This script frees one generic test league per bucket, makes a league with the game's own name
on that bucket's slot (`slot=` in the world line) and moves the bucket's clubs into it, taking
them out of whatever competition had them. Whatever is missing to the target size is cloned
afterwards with `fill_group.py --reg <id> --to <size>`, and the competitions that lost clubs
are refilled the same way, so no club is ever in two of them.

Clubs named like one of our own old experiments ("Otros UEFA 01", "Other Clubs (Asia) Club 05",
"Generic League 03 Club 07") are not shipped clubs: they are kept as filler up to the target
and the leftovers are moved out of every bucket, so the sections stop listing them twice.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import mkleague as M

T_REC, T_NAME, T_NAME_LEN, T_POOL = 1532, 0x170, 70, 0x4F

# name, slot, pool nibble, target clubs, region, country flag, conf, prototype code
#
# Classic Teams (nibble 1) is NOT here on purpose: its section is the game's own and lists the
# shipped classics (10 real + 24 `CLASSICS NN`) on its own, so those clubs stay in no
# competition. Putting a league on slot 5 or 6 would take the section away (fl26comptab keeps
# them PROTECTED) and hide it from Select Team.
SPECS = [
    ("Other European Leagues", 69, 2, 48, 29, 200, 2, "ENGLAND_D1_LEAGUE"),
    ("Other", 71, 5, 48, 29, 200, 2, "ENGLAND_D1_LEAGUE"),
    ("Other Latin American Teams", 73, 6, 48, 29, 148, 4, "ENGLAND_D1_LEAGUE"),
]

OURS = ("Otros ", "OTROS ", "Other Clubs (", "Generic League", "Classic Teams Club")


def text(raw, o):
    return (
        raw[o + T_NAME : o + T_NAME + T_NAME_LEN]
        .split(b"\0")[0]
        .decode("utf-8", "replace")
    )


def is_ours(name):
    return any(name.startswith(p) for p in OURS)


def set_count(regs, lines, cid, n):
    ri = next(i for i in range(0, len(regs), M.REG) if regs[i + M.R_CID] == cid)
    regs[ri + M.R_TEAMS] = (regs[ri + M.R_TEAMS] & 0xC0) | (n & 0x3F)
    for i, l in enumerate(lines):
        if l.startswith("league ") and ("cid=%d " % cid) in l:
            a = l.index("clubs=") + 6
            b = l.index(" ", a)
            lines[i] = l[:a] + str(n) + l[b:]


def entries_of(ents, cid):
    idx = [i for i in range(0, len(ents), M.ENT) if ents[i + M.E_CID] == cid]
    idx.sort(key=lambda i: ents[i + M.E_ORDER])
    return idx


def drop_entry(ents, i):
    return bytearray(
        b"".join(ents[k : k + M.ENT] for k in range(0, len(ents), M.ENT) if k != i)
    )


def add_entry(ents, cid, tid, order):
    eid = (
        max(
            int.from_bytes(ents[i : i + 4], "little")
            for i in range(0, len(ents), M.ENT)
        )
        + 1
    )
    e = bytearray(M.ENT)
    e[M.E_TEAM : M.E_TEAM + 4] = tid.to_bytes(4, "little")
    e[M.E_EID : M.E_EID + 4] = eid.to_bytes(4, "little")
    e[M.E_CID], e[M.E_ORDER] = cid, order
    return ents + e


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, wf = get("--base"), get("--worldfile")
    if not base or not wf:
        print(__doc__)
        return 1
    dry = "--dry" in a

    raw = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )
    comp = bytearray(M.load(base, "Competition.bin"))
    regs = bytearray(M.load(base, "CompetitionRegulation.bin"))
    ents = bytearray(M.load(base, "CompetitionEntry.bin"))
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
    for _n, _r, kv in world:
        cid_count[int(kv["cid"])] = cid_count.get(int(kv["cid"]), 0) + 1
    genc = [
        (reg, int(kv["cid"]), n)
        for n, reg, kv in world
        if kv.get("name", "").startswith("Generic League")
        and cid_count[int(kv["cid"])] == 1
    ]
    genc.sort(reverse=True)
    if len(genc) < len(SPECS):
        print("only %d freeable generic league(s), need %d" % (len(genc), len(SPECS)))
        return 1
    free = genc[: len(SPECS)]

    drop_cids = {c for _r, c, _n in free}
    drop_regs = {r for r, _c, _n in free}
    drop_lines = {n for _r, _c, n in free}
    if not dry:
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

    # who is where, before anything moves
    where = {}
    for i in range(0, len(ents), M.ENT):
        where.setdefault(int.from_bytes(ents[i : i + 4], "little"), []).append(
            ents[i + M.E_CID]
        )
    cid_name = {}
    for i in range(0, len(regs), M.REG):
        cid_name[regs[i + M.R_CID]] = (
            regs[i + M.R_NAME : i + M.R_NAME + 0x73]
            .split(b"\0")[0]
            .decode("utf-8", "replace")
        )

    bucket = {nib: [] for _nm, _s, nib, _t, _r, _c, _cf, _p in SPECS}
    for o in range(0, len(raw), T_REC):
        if raw[o + T_POOL] >> 4 & 0xF not in bucket:
            continue
        tid = int.from_bytes(raw[o + 8 : o + 12], "little")
        bucket[raw[o + T_POOL] >> 4 & 0xF].append(
            (tid, text(raw, o), is_ours(text(raw, o)))
        )

    report = []
    for k, (name, slot, nib, target, region, country, conf, proto) in enumerate(SPECS):
        clubs = bucket[nib]
        shipped = [t for t, nm, ours in clubs if not ours]
        filler = [(t, nm) for t, nm, ours in clubs if ours]
        keep = shipped + [t for t, _nm in filler][: max(0, target - len(shipped))]
        extra = [t for t, _nm in filler][max(0, target - len(shipped)) :]
        report.append(
            (name, slot, nib, target, len(shipped), len(filler), len(keep), len(extra))
        )
    print(
        "%-28s %4s %3s %6s %8s %7s %5s %6s"
        % ("group", "slot", "nib", "target", "shipped", "filler", "keep", "orphan")
    )
    for r in report:
        print("%-28s %4d %3d %6d %8d %7d %5d %6d" % r)

    movers = set()
    for name, slot, nib, target, region, country, conf, proto in SPECS:
        clubs = bucket[nib]
        shipped = [t for t, nm, ours in clubs if not ours]
        filler = [t for t, nm, ours in clubs if ours]
        keep = shipped + filler[: max(0, target - len(shipped))]
        extra = filler[max(0, target - len(shipped)) :]
        movers.update(keep)
        if dry:
            continue
        reg, cid, _n = free[
            SPECS.index((name, slot, nib, target, region, country, conf, proto))
        ]
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
            "league %d cid=%d region=%d country=%d conf=%d slot=%d tier=1 promote=0 "
            "demote=0 clubs=0 legs=2 kickoff=99 name=%s"
            % (reg, cid, region, country, conf, slot, name)
        )
        for k, tid in enumerate(keep, 1):
            ents = add_entry(ents, cid, tid, k)
        set_count(regs, lines, cid, len(keep))
        print(
            "  + %-28s cid=%-3d reg=%d slot=%d clubs=%d"
            % (name, cid, reg, slot, len(keep))
        )

    # take the movers out of every other competition, and remember the sizes to restore
    lost = {}
    for cid in sorted({c for t in movers for c in where.get(t, [])}):
        gone = {
            int.from_bytes(ents[i : i + 4], "little") for i in entries_of(ents, cid)
        }
        gone &= movers
        if not gone:
            continue
        lost[cid] = len(gone)
        ents = bytearray(
            b"".join(
                ents[i : i + M.ENT]
                for i in range(0, len(ents), M.ENT)
                if not (
                    ents[i + M.E_CID] == cid
                    and int.from_bytes(ents[i : i + 4], "little") in gone
                )
            )
        )
        idx = entries_of(ents, cid)
        for k, i in enumerate(idx, 1):
            ents[i + M.E_ORDER] = k
        set_count(regs, lines, cid, len(idx))

    # leftovers of our own experiments leave the buckets
    orphan = 0
    for name, slot, nib, target, region, country, conf, proto in SPECS:
        clubs = bucket[nib]
        shipped = [t for t, nm, ours in clubs if not ours]
        filler = [t for t, nm, ours in clubs if ours]
        extra = filler[max(0, target - len(shipped)) :]
        for t in extra:
            for o in range(0, len(raw), T_REC):
                if int.from_bytes(raw[o + 8 : o + 12], "little") == t:
                    raw[o + T_POOL] &= 0x0F
                    orphan += 1
                    break
    print("orphans moved out of the buckets:", orphan)

    if dry:
        print("dry run: nothing written")
        return 0

    print("competitions that lost clubs (refill them to their old size):")
    for cid, n in sorted(lost.items()):
        print("  cid %-3d -%d  %s" % (cid, n, cid_name.get(cid, "?")))

    open(os.path.join(base, "Competition.bin"), "wb").write(
        pesdb.wesys_pack(bytes(comp))
    )
    open(os.path.join(base, "CompetitionRegulation.bin"), "wb").write(
        pesdb.wesys_pack(bytes(regs))
    )
    open(os.path.join(base, "CompetitionEntry.bin"), "wb").write(
        pesdb.wesys_pack(bytes(ents))
    )
    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))
    io.open(wf, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print("written")
    for name, slot, nib, target, region, country, conf, proto in SPECS:
        ri = next(
            i
            for i in range(0, len(regs), M.REG)
            if regs[i + M.R_NAME : i + M.R_NAME + 0x73]
            .split(b"\0")[0]
            .decode("utf-8", "replace")
            == name
        )
        reg = int.from_bytes(regs[ri + M.R_ID : ri + M.R_ID + 2], "little")
        cid = regs[ri + M.R_CID]
        print(
            "  reg %d cid %d %-28s -> fill_group --reg %d --to %d"
            % (reg, cid, name, reg, target)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""python add_missing_nations.py --base <world pesdb> [--countries <pesdb with Country.bin>]
                               [--dry] [--rename-only]

Give a national team to every country of a confederation (2..7) that has none.

The world of this branch reaches 211 FIFA nations plus the non-FIFA sides, but a country can
still be left without a Team.bin row: measured 2026-10-30, SOUTH SUDAN (flag 312, CAF) and
CHINESE TAIPEI (flag 298, AFC) had a Country.bin row and no national team. This clones a
national team of the same confederation (a squad of at least eleven), sets the country and a
Spanish name, and gives it the template's squad with new player ids.

`--rename-only` rewrites the Spanish names of the nations it knows and writes nothing else.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import playeredit as E

T_REC, T_ID, T_ALT = 1532, 0x08, 0x00
T_NATIONAL, T_COUNTRY, T_NAME, T_ABBR = 0x53, 0x46, 0x170, 0x372
T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 70, 20, 70
T_ABBR_LEN = 4
A_REC, A_EID, A_PID, A_TID = 16, 0x00, 0x04, 0x08
C_REC, C_CONF, C_EN = 1420, 5, 288

# Spanish (title case) names and three-letter codes for the nations this tool knows
NAMES = {
    298: ("China Taip\u00e9i", "TPE"),
    312: ("Sud\u00e1n del Sur", "SSD"),
}


def title_es(s):
    """fallback: an English country name to a Spanish-looking title-case one"""
    small = {"of", "and", "the", "del", "de", "la", "las", "los", "y"}
    out = []
    for i, w in enumerate(s.split()):
        lw = w.lower()
        out.append(lw if (i and lw in small) else lw[:1].upper() + lw[1:])
    return " ".join(out)


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    if not base:
        print(__doc__)
        return 1
    countries = get("--countries") or base
    dry = "--dry" in a

    raw = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Team.bin"), "rb").read())
    )
    players = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Player.bin"), "rb").read())
    )
    assigns = bytearray(
        pesdb.wesys_unpack(
            open(os.path.join(base, "PlayerAssignment.bin"), "rb").read()
        )
    )
    cty = pesdb.wesys_unpack(open(os.path.join(countries, "Country.bin"), "rb").read())

    conf, en = {}, {}
    for o in range(0, len(cty), C_REC):
        fid = (int.from_bytes(cty[o : o + 4], "little") >> 10) & 0x1FF
        conf[fid] = cty[o + C_CONF]
        en[fid] = (
            cty[o + C_EN : o + C_EN + 70]
            .split(b"\0")[0]
            .decode("utf-8", "replace")
            .strip()
        )

    by_team = {}
    for i in range(0, len(assigns), A_REC):
        by_team.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(i)

    nats = {}
    for o in range(0, len(raw), T_REC):
        if raw[o + T_NATIONAL] & 0x80:
            cid = (
                int.from_bytes(raw[o + T_COUNTRY : o + T_COUNTRY + 2], "little") >> 2
            ) & 0x1FF
            nats.setdefault(cid, []).append(o)

    missing = [f for f in sorted(conf) if conf[f] >= 2 and f not in nats]
    print("countries with a national team: %d; missing: %d" % (len(nats), len(missing)))
    for f in missing:
        name, code = NAMES.get(
            f, (title_es(en[f]), "".join(c for c in en[f] if c.isalpha())[:3].upper())
        )
        print(
            "  +\u00a0%s (flag %d, conf %d) -> %s / %s"
            % (en[f], f, conf[f], name, code)
        )

    if dry:
        print("dry run: nothing written")
        return 0

    top = max(
        int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    top_alt = max(
        int.from_bytes(raw[o + T_ALT : o + T_ALT + 4], "little")
        for o in range(0, len(raw), T_REC)
    )
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    pid_top = max(
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little")
        for i in range(0, len(players), E.P_REC)
    )

    made = 0
    for k, f in enumerate(missing):
        name, code = NAMES.get(
            f, (title_es(en[f]), "".join(c for c in en[f] if c.isalpha())[:3].upper())
        )
        # template: a national team of the same confederation with a squad, else New Zealand
        cand = [
            o
            for c, offs in nats.items()
            if conf.get(c) == conf[f]
            for o in offs
            if len(
                by_team.get(int.from_bytes(raw[o + T_ID : o + T_ID + 4], "little"), [])
            )
            >= 11
        ]
        tpl = cand[0] if cand else nats[1141][0]
        squad = by_team[int.from_bytes(raw[tpl + T_ID : tpl + T_ID + 4], "little")][:23]
        tid = top + 1 + k
        row = bytearray(raw[tpl : tpl + T_REC])
        row[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
        row[T_ALT : T_ALT + 4] = (top_alt + 1 + k).to_bytes(4, "little")
        for s in range(T_NAME_SLOTS):
            o = T_NAME + s * T_NAME_STEP
            if o + T_NAME_LEN <= T_REC:
                b = name.encode("utf-8")[: T_NAME_LEN - 1]
                row[o : o + T_NAME_LEN] = b + bytes(T_NAME_LEN - len(b))
        row[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[
            : T_ABBR_LEN - 1
        ].ljust(T_ABBR_LEN, b"\0")
        old = int.from_bytes(row[T_COUNTRY : T_COUNTRY + 2], "little")
        row[T_COUNTRY : T_COUNTRY + 2] = ((old & ~(0x1FF << 2)) | (f << 2)).to_bytes(
            2, "little"
        )
        row[T_NATIONAL] |= 0x80
        raw += row
        free = E.free_ids(players, len(squad))
        for n, ai in enumerate(squad, 1):
            pid = free[n - 1]
            e = bytearray(assigns[ai : ai + A_REC])
            e[A_EID : A_EID + 4] = (eid_top + 1 + made).to_bytes(4, "little")
            e[A_PID : A_PID + 4] = pid.to_bytes(4, "little")
            e[A_TID : A_TID + 4] = tid.to_bytes(4, "little")
            assigns += e
            tpid = int.from_bytes(assigns[ai + A_PID : ai + A_PID + 4], "little")
            po = next(
                o
                for o in range(0, len(players), E.P_REC)
                if int.from_bytes(players[o + E.P_ID : o + E.P_ID + 4], "little")
                == tpid
            )
            pr = bytearray(players[po : po + E.P_REC])
            pr[E.P_ID : E.P_ID + 4] = pid.to_bytes(4, "little")
            pr[E.P_NAME : E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS] = E.name_slots(
                "%s Jugador %02d" % (name, n)
            )
            E.setf(pr, "Nationality", f)
            players += pr
            made += 1
        print("  team %d: %s, %d player(s)" % (tid, name, len(squad)))

    open(os.path.join(base, "Team.bin"), "wb").write(pesdb.wesys_pack(bytes(raw)))
    open(os.path.join(base, "Player.bin"), "wb").write(pesdb.wesys_pack(bytes(players)))
    open(os.path.join(base, "PlayerAssignment.bin"), "wb").write(
        pesdb.wesys_pack(bytes(assigns))
    )
    print("added %d nation(s), %d player(s)" % (len(missing), made))
    return 0


if __name__ == "__main__":
    sys.exit(main())

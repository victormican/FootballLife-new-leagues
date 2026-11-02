"""python add_nation.py --base <world pesdb> --nation "<flag>,<conf>,<NAME>,<ENGLISH>,<ABBR>"
                       [--nation ...] [--squad 23] [--dry]

Add national teams the game does not ship, one per `--nation`, to a built world.

A nation needs three things and this writes all three:

- a Country.bin row: the flag id in bits 10-18 of its first dword, the confederation byte at
  +0x05 (2 UEFA, 3 AFC, 4 CONMEBOL, 5 CAF, 6 CONCACAF, 7 OFC) and the name in the eighteen
  language columns (70 bytes each, from 148) plus the English one at 288.  The row is cloned
  from a country of the same confederation, so whatever else it carries stays plausible.
- a Team.bin row: cloned from a national team of the same confederation that has a squad, with a
  new team id and alt id, the name in every language slot, a three-letter code, the country id
  at +0x46 and the national bit of +0x53 set.
- a squad: the template's players cloned with new ids and generic names ("<NAME> Player 01"…),
  their nationality set to the country, and a PlayerAssignment row for the new team.

The name writer keeps 24 bytes for slot 10: that slot's text ends at 0x371 and the three-letter
code sits at 0x372, so a 30-character name poured into it eats the code and the game aborts on
load (see abreviatura-de-equipo.md).  Slots 0..9 and 11..19 take the whole name.

The flag art is not created here: drop the pictures in sider/flags and run
`mkcountryflag.py --from sider/flags --ids <ids>` and `--emblems`.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
import playeredit as E

T_REC, T_ID, T_ALT = 1532, 0x08, 0x0C
T_NATIONAL, T_COUNTRY = 0x53, 0x46
T_NAME, T_NAME_LEN, T_NAME_SLOTS, T_NAME_STEP = 0x9E, 70, 20, 70
T_ABBR, T_ABBR_LEN = 0x372, 4
T_SHORT = 0x35A  # slot 10's text: 24 bytes, then the code
T_SHORT_MAX = T_ABBR - T_SHORT
A_REC, A_EID, A_PID, A_TID = 16, 0x00, 0x04, 0x08
C_REC, C_CONF = 1420, 0x05
C_NAMES = list(range(148, C_REC - 69, 70))
C_EN = 288
CONF = {2: "UEFA", 3: "AFC", 4: "CONMEBOL", 5: "CAF", 6: "CONCACAF", 7: "OFC"}


def cstr(b):
    return b.split(b"\0")[0].decode("utf-8", "replace")


def country_rows(raw):
    """[(row index, flag id, name, conf)] of the named rows"""
    out = []
    for i in range(0, len(raw), C_REC):
        r = raw[i : i + C_REC]
        n = cstr(r[148:218]).strip()
        if n:
            out.append(
                (
                    i // C_REC,
                    (int.from_bytes(r[:4], "little") >> 10) & 0x1FF,
                    n,
                    r[C_CONF],
                )
            )
    return out


def put_name(row, text):
    """the name in every localised slot and in the English one, without touching the code"""
    b = text.encode("utf-8")
    for k in range(T_NAME_SLOTS):
        o = T_NAME + k * T_NAME_STEP
        if o + T_NAME_LEN > T_REC:
            continue
        limit = T_SHORT_MAX if o == T_SHORT else T_NAME_LEN - 1
        chunk = b[:limit]
        row[o : o + limit] = chunk + bytes(limit - len(chunk))
        if o != T_SHORT:
            row[o + limit] = 0


def abbr_of(text, taken):
    t = text.strip().upper()
    if len(t) == 3 and t.isalnum():
        base = t
    else:
        words = [w for w in text.replace("-", " ").split() if w]
        letters = [w[0] for w in words if w[0].isalnum()]
        base = ("".join(letters[:3]) or text[:3]).upper()
        if len(base) < 3:
            base = (base + "".join(c for c in text.upper() if c.isalnum()))[:3]
    for k in range(1000):
        cand = base if k == 0 else ("%s%02d" % (base[0], k % 100))[:3]
        if cand not in taken:
            return cand
    return "ZZZ"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base = get("--base")
    specs = [a[i + 1] for i, v in enumerate(a) if v == "--nation"]
    if not base or not specs:
        print(__doc__)
        return 2
    dry = "--dry" in a
    squad_size = int(get("--squad", "23"))

    cty = bytearray(
        pesdb.wesys_unpack(open(os.path.join(base, "Country.bin"), "rb").read())
    )
    teams = bytearray(
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

    rows = country_rows(cty)
    have_flags = {f for _r, f, _n, _c in rows}
    have_names = {n.strip().upper() for _r, _f, n, _c in rows}

    by_team = {}
    for i in range(0, len(assigns), A_REC):
        by_team.setdefault(
            int.from_bytes(assigns[i + A_TID : i + A_TID + 4], "little"), []
        ).append(i)

    nats = []
    for o in range(0, len(teams), T_REC):
        r = teams[o : o + T_REC]
        if not r[T_NATIONAL] & 0x80:
            continue
        tid = int.from_bytes(r[T_ID : T_ID + 4], "little")
        fid = (int.from_bytes(r[T_COUNTRY : T_COUNTRY + 2], "little") >> 2) & 0x1FF
        nats.append((tid, fid, o, len(by_team.get(tid, []))))

    top = max(
        int.from_bytes(teams[o + T_ID : o + T_ID + 4], "little")
        for o in range(0, len(teams), T_REC)
    )
    top_alt = max(
        int.from_bytes(teams[o + T_ALT : o + T_ALT + 4], "little")
        for o in range(0, len(teams), T_REC)
    )
    eid_top = max(
        int.from_bytes(assigns[i + A_EID : i + A_EID + 4], "little")
        for i in range(0, len(assigns), A_REC)
    )
    pid_top = max(
        int.from_bytes(players[i + E.P_ID : i + E.P_ID + 4], "little")
        for i in range(0, len(players), E.P_REC)
    )
    taken = {
        bytes(teams[o + T_ABBR : o + T_ABBR + 3])
        for o in range(0, len(teams), T_REC)
        if teams[o + T_ABBR] != 0
    }

    conf_of_flag = {f: c for _r, f, _n, c in rows}
    made = []
    for n, spec in enumerate(specs):
        parts = [p.strip() for p in spec.split(",")]
        if len(parts) < 4:
            raise SystemExit(
                "--nation needs <flag>,<conf>,<NAME>,<ENGLISH>[,<ABBR>]: %r" % spec
            )
        fid, conf, name, en = int(parts[0]), int(parts[1]), parts[2], parts[3]
        if conf not in CONF:
            raise SystemExit("confederation %d is not one of %s" % (conf, sorted(CONF)))
        if fid in have_flags:
            raise SystemExit("flag id %d is already used" % fid)
        if name.strip().upper() in have_names:
            raise SystemExit("%r is already a country" % name)

        tpl_country = next((r for r in rows if r[3] == conf), rows[0])
        crow = bytearray(cty[tpl_country[0] * C_REC : (tpl_country[0] + 1) * C_REC])
        crow[0:4] = (
            (int.from_bytes(crow[0:4], "little") & ~(0x1FF << 10)) | (fid << 10)
        ).to_bytes(4, "little")
        crow[C_CONF] = conf
        for o in C_NAMES + [C_EN]:
            b = (en if o == C_EN else name).encode("utf-8")[: C_REC - o - 1]
            crow[o : o + 69] = b + bytes(69 - len(b))
        cty += crow

        tpl = next(
            (t for t in nats if conf_of_flag.get(t[1]) == conf and t[3] >= 11), None
        )
        if tpl is None:
            tpl = next(t for t in nats if t[3] >= 11)
        tid = top + 1 + n
        trow = bytearray(teams[tpl[2] : tpl[2] + T_REC])
        trow[T_ID : T_ID + 4] = tid.to_bytes(4, "little")
        trow[T_ALT : T_ALT + 4] = (top_alt + 1 + n).to_bytes(4, "little")
        put_name(trow, name)
        code = abbr_of(parts[4] if len(parts) > 4 else name, taken)
        taken.add(code.encode("ascii"))
        trow[T_ABBR : T_ABBR + T_ABBR_LEN] = code.encode("ascii")[:3].ljust(4, b"\0")
        old = int.from_bytes(trow[T_COUNTRY : T_COUNTRY + 2], "little")
        trow[T_COUNTRY : T_COUNTRY + 2] = ((old & ~(0x1FF << 2)) | (fid << 2)).to_bytes(
            2, "little"
        )
        trow[T_NATIONAL] |= 0x80
        teams += trow

        squad = by_team[tpl[0]][:squad_size]
        free = E.free_ids(players, len(squad))
        for j, ai in enumerate(squad, 1):
            pid = free[j - 1] if j - 1 < len(free) else pid_top + j
            e = bytearray(assigns[ai : ai + A_REC])
            e[A_EID : A_EID + 4] = (eid_top + len(made) * squad_size + j).to_bytes(
                4, "little"
            )
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
                "%s Player %02d" % (name, j)
            )
            E.setf(pr, "Nationality", fid)
            players += pr

        made.append((tid, fid, conf, name, code, len(squad)))
        have_flags.add(fid)
        have_names.add(name.strip().upper())

    print("adding %d national teams (squad %d)" % (len(made), squad_size))
    for tid, fid, conf, name, code, sq in made:
        print(
            "  team %-6d flag %-4d %-8s %-28s %s  %d players"
            % (tid, fid, CONF[conf], name, code, sq)
        )

    if dry:
        print("dry run: nothing written")
        return 0

    for table, data in (
        ("Country.bin", cty),
        ("Team.bin", teams),
        ("Player.bin", players),
        ("PlayerAssignment.bin", assigns),
    ):
        open(os.path.join(base, table), "wb").write(pesdb.wesys_pack(bytes(data)))
    print("written to %s" % base)
    return 0


if __name__ == "__main__":
    sys.exit(main())

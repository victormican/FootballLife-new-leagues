r"""python mkcwc.py --base <pesdb dir> --out <livecpk root> [--cid N] [--reg N] [--ko N]
                   [--name "Club World Cup"] [--dry]

Build the FIFA Club World Cup in the 2025 format as a competition of its own: 32 clubs in eight
groups of four played once round, then a single-match knockout of sixteen.

The game already has a Club World Cup: its competition 1, a small annual tournament in
mid-December.  That one is left exactly as it is.  This adds a second competition beside it, so
a world can carry both, and this is the one that plays the 2025 format.  How often it is played
is fl26swiss's business, not this script's: it writes the rows and stops.

Two shapes are borrowed, because the engine already plays both:

  the group stage   copied from the Copa Libertadores group stage (regulation 9: a CLUB
                    competition, 32 clubs, eight groups, eight replicas), with one change:
                    rounds (+0x10 bits 12-14) 2 -> 1, so each group is played once round.
                    Its replicas become <reg> + 1024 * (group + 1), each pointing back at
                    <reg> on +0x06.
  the knockout      copied from the shipped regulation 1 row -- the single-match template the
                    Club World Cup's own annual knockout uses -- with its club count 4 -> 16.

Nothing is taken from competition 1 except its identity: the competition row carries its code
and the name in all twenty language slots, so the cup reads as the Club World Cup and not as a
placeholder.  Every regulation row is new, with its own id, and competition 1 is not touched.

Entries (CompetitionEntry) are not written: the field is chosen from league tables at run time
by fl26swiss's CWC access list, not from a fixed list.  That is why this script needs ids and no
club list.

fl26swiss.c looks both regulation ids up by number, so the ids given here have to be the ones
the module has compiled in.  KO is that number for the knockout; the group stage's is read from
the world's own `cwc` line, which leaguebuilder.py writes.

--dry prints the plan and writes nothing.
"""

import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mkleague as M

R_BACK, R_GROUP, R_ROUNDS_DW = 0x06, 0x0A, 0x10
REPLICA_STEP, NO_GROUP = 1024, 255
NAMES = slice(M.R_NAME, M.R_NAME + M.NAME_SLOTS * M.NAME_SLOT)
CWC_CID, CWC_REG_SHIPPED, GROUPS_FROM = 1, 1, 9  # 9 = Copa Libertadores group stage
GROUPS, CLUBS, KO_CLUBS = 8, 32, 16
# The knockout's regulation id, and the one fl26swiss.c has compiled in as CWC_KO.  The two have
# to agree: the DLL looks the knockout up by that number at run time, so a world built with a
# different id here would hold the rows with nothing reading them.  A constant, so
# leaguebuilder.py reserves this id and the builder and the module cannot drift apart.
KO = 200


def rid(r):
    return int.from_bytes(r[M.R_ID : M.R_ID + 2], "little")


def rep_id(reg, group):
    """the regulation id of one group of the group stage.

    The same arithmetic fl26swiss.c does in cwc_rep(): master + (group + 1) * 1024.  Kept here
    so the builder and its test cannot drift from the module that reads these rows.
    """
    return reg + (group + 1) * REPLICA_STEP


def rows(regs):
    return [bytearray(regs[i : i + M.REG]) for i in range(0, len(regs), M.REG)]


def put_names(row, name):
    """write a name into all twenty language slots; the game reads whichever it wants"""
    b = name.encode("utf-8")[: M.NAME_SLOT - 1]
    row[M.R_NAME : M.R_NAME + M.NAME_SLOTS * M.NAME_SLOT] = (
        b + bytes(M.NAME_SLOT - len(b))
    ) * M.NAME_SLOTS


def ids_of(base):
    """the competition and regulation ids this world already uses"""
    comp, regs = (
        M.load(base, "Competition.bin"),
        M.load(base, "CompetitionRegulation.bin"),
    )
    used_c = {comp[i + M.CID_OFF] for i in range(0, len(comp), M.COMP)}
    used_r = {rid(r) for r in rows(regs)}
    return used_c, used_r


def ladder(reg):
    """the group stage's master and its eight replicas"""
    return [reg] + [rep_id(reg, g) for g in range(GROUPS)]


def free_reg(used_r, ko):
    """the lowest regulation id whose whole replica ladder is free.

    Checking only the master is not enough: the replicas sit at +1024 per group, so a league on
    2224 does not collide with a master on 176 and yet is the second replica.  Found on
    2026-10-09 while writing this: the first cut tested the master alone and would have handed a
    six-league world a group stage sitting on its own clubs.
    """
    for r in range(176, REPLICA_STEP):
        if r != ko and not (set(ladder(r)) & used_r):
            return r
    raise SystemExit(
        "no regulation id in 176..%d has its whole replica ladder free in this world; pass --reg "
        "with one that does, or one of ours is already taken" % (REPLICA_STEP - 1)
    )


def build(base, cid, reg, ko, name):
    """the competition row and the regulation rows to add. Raises if the world is not the shape
    this copies from, or if an id asked for is taken."""
    comp, regs = (
        M.load(base, "Competition.bin"),
        M.load(base, "CompetitionRegulation.bin"),
    )
    R = rows(regs)
    used_c, used_r = ids_of(base)

    if cid is None:
        cid = next(c for c in range(1, 256) if c not in used_c)
    if reg is None:
        reg = free_reg(used_r, ko)
    if cid in used_c:
        raise SystemExit("competition id %d is taken in this world" % cid)
    if cid == CWC_CID:
        raise SystemExit(
            "competition %d is the game's own Club World Cup.  This script adds a second one "
            "beside it so the annual tournament stays; it needs a different id."
            % CWC_CID
        )
    if ko in used_r:
        raise SystemExit(
            "knockout id %d is taken in this world; pick another with --ko" % ko
        )
    for i, what in ((reg, "regulation"), (ko, "knockout")):
        if not 175 < i < REPLICA_STEP:
            raise SystemExit(
                "%s id %d wants to be between 176 and %d" % (what, i, REPLICA_STEP - 1)
            )
    if reg + REPLICA_STEP * GROUPS > 65535:
        raise SystemExit("regulation id %d leaves no room for its eight replicas" % reg)
    clash = sorted(set(ladder(reg)) & used_r)
    if clash:
        raise SystemExit(
            "a group stage on %d puts its groups on %s, and %s already in this world"
            % (
                reg,
                ", ".join(str(rep_id(reg, g)) for g in range(GROUPS)),
                ", ".join(str(x) for x in clash),
            )
        )

    # the identity: the game's own Club World Cup row, copied and given a new id
    src = [
        i // M.COMP
        for i in range(0, len(comp), M.COMP)
        if comp[i + M.CID_OFF] == CWC_CID
    ]
    if len(src) != 1:
        raise SystemExit(
            "the game has no single Club World Cup row (found %d)" % len(src)
        )
    c = bytearray(comp[src[0] * M.COMP : (src[0] + 1) * M.COMP])
    c[M.CID_OFF] = cid

    # the knockout template: the shipped regulation 1 row, the single-match shape
    tmpl = [r for r in R if rid(r) == CWC_REG_SHIPPED and r[M.R_CID] == CWC_CID]
    if len(tmpl) != 1:
        raise SystemExit(
            "regulation %d is not the one Club World Cup row here (%d found)"
            % (CWC_REG_SHIPPED, len(tmpl))
        )

    # the group stage: the Libertadores group stage, 32 clubs in eight replicas
    gs = [r for r in R if rid(r) & 0x3FF == GROUPS_FROM and r[M.R_CID] == 5]
    master = [r for r in gs if r[R_GROUP] == NO_GROUP]
    reps = sorted((r for r in gs if r[R_GROUP] != NO_GROUP), key=lambda r: r[R_GROUP])
    if (
        len(master) != 1
        or len(reps) != GROUPS
        or (master[0][M.R_TEAMS] & 0x3F) != CLUBS
    ):
        raise SystemExit(
            "the Libertadores group stage is not %d clubs in %d replicas here "
            "(%d master, %d replicas)" % (CLUBS, GROUPS, len(master), len(reps))
        )

    out = []
    for r in master + reps:
        g = bytearray(r)
        g[M.R_BELOW : M.R_BELOW + 2] = bytes(2)
        g[M.R_CID] = cid
        grp = g[R_GROUP]
        g[M.R_ID : M.R_ID + 2] = (
            reg if grp == NO_GROUP else rep_id(reg, grp)
        ).to_bytes(2, "little")
        if grp != NO_GROUP:
            g[R_BACK : R_BACK + 2] = reg.to_bytes(2, "little")
        dw = int.from_bytes(g[R_ROUNDS_DW : R_ROUNDS_DW + 4], "little")
        dw = (dw & ~(7 << 12)) | (1 << 12)  # once round
        g[R_ROUNDS_DW : R_ROUNDS_DW + 4] = dw.to_bytes(4, "little")
        # the twenty name slots come from the shipped Club World Cup regulation row, not from
        # the competition row: a Competition record is 36 bytes and R_NAME .. R_NAME+2300 is
        # not inside it, so copying from `c` leaves the group stage with 16 bytes of one record's
        # code in its first slot and the Libertadores' names in the other nineteen.  The first
        # buildcheck check is what caught that, on the six-league recipe, 2026-10-09.
        g[NAMES] = tmpl[0][NAMES]
        # +0x0f bits 0-5 (runtime +0x310 bits 0-5) differ per competition and not per shape --
        # 1 Champions League, 5 Europa League, 7 Libertadores, 13 AFC, 0 the Club World Cup and
        # the World Cup -- so they are the competition's own, not the borrowed stage's
        g[0x0F] = (g[0x0F] & 0xC0) | (tmpl[0][0x0F] & 0x3F)
        if name:
            put_names(g, name)
        out.append(g)

    k = bytearray(tmpl[0])
    k[M.R_ID : M.R_ID + 2] = ko.to_bytes(2, "little")
    k[M.R_CID] = cid
    k[M.R_TEAMS] = (k[M.R_TEAMS] & ~0x3F) | KO_CLUBS
    if name:
        put_names(k, name)
    out.append(k)
    return c, out


def describe(new_regs, cid):
    print("Club World Cup, its own competition %d, %d rows:" % (cid, len(new_regs)))
    for g in new_regs:
        dw = int.from_bytes(g[R_ROUNDS_DW : R_ROUNDS_DW + 4], "little")
        print(
            "   reg %5d  kind %d  clubs %2d  group %3d  back %d  groups %d  rounds %d  single %d"
            % (
                rid(g),
                g[M.R_TYPE],
                g[M.R_TEAMS] & 0x3F,
                g[R_GROUP],
                int.from_bytes(g[R_BACK : R_BACK + 2], "little"),
                dw & 0x1F,
                (dw >> 12) & 7,
                (dw >> 29) & 1,
            )
        )


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    base, out = get("--base"), get("--out")
    if not base or (not out and "--dry" not in a):
        print(__doc__)
        return 1
    num = lambda k, d=None: int(get(k, d)) if get(k, d) is not None else None

    c, new_regs = build(
        base, num("--cid"), num("--reg"), num("--ko", KO), get("--name")
    )
    cid, reg = c[M.CID_OFF], rid(new_regs[0])
    describe(new_regs, cid)
    if "--dry" in a:
        print("dry run: nothing written")
        return 0

    comp, regs, ents = (
        M.load(base, n)
        for n in (
            "Competition.bin",
            "CompetitionRegulation.bin",
            "CompetitionEntry.bin",
        )
    )
    comp += c
    regs += bytearray(b"".join(bytes(g) for g in new_regs))
    M.write_tables(out, comp, regs, ents)
    print(
        "written to %s: competition %d, regulations %d and %d..%d plus %d"
        % (out, cid, reg, reg + 1024, reg + 1024 * GROUPS, len(new_regs))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

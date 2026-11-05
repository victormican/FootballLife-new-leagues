r"""python newlife_apply.py --release <NewLife folder> --world <pesdb dir>
                        [--base <pesdb dir>] [--go] [--limit N] [--only TEXT] [--dry]

Put a NewLife release's squads into a world that is already built, in place: the teams and
players the release has are the world's, with its ratings, names, positions and squads.

What it touches
    Player.bin and PlayerAssignment.bin of --world, nothing else.  The leagues, the cups, the
    club ids, the names and the crests stay as they are: this is a squad update, not a rebuild.

How a club is found
    1. by id: a release club whose newlife_id (or game_id) is a team id of the world;
    2. by name and country: a world club with the same name, when that name is unique.
    National teams are left out (the release has none).

How a player is found
    1. by game_id, then by newlife_id, when that id is a player of the world;
    2. by name, first among the club's own players, then anywhere in the world when the name
       is unique;
    3. otherwise he is a new player: `lbplayers.apply` gives him a free id below 262144.

What a club gets
    The release's best 30 (goalkeepers kept to three, `Release.squad`), the old players that
    are not in it leave the club as free agents, and the best eleven is picked again for the
    formation the game plays.  A club the release does not have is not touched.

    --dry (default) prints the plan and writes nothing.  --go writes; the two tables are
    copied first to Player.bin.before-nl<version> / PlayerAssignment.bin.before-nl<version>.
"""

import argparse
import os
import shutil
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "modstudio"))

# the world's player ids are dense up to 260k: the gaps below have to be usable, or there is
# no room for the release's new players (lbplayers reads this at import time)
os.environ.setdefault("FL26_FREE_PLAYER_IDS", "1")

import lbplayers as L
import pesdb
import playeredit as E
import newlife as NL

T_REC, T_ID, T_NATIONAL, T_COUNTRY, T_NAME = 1532, 0x08, 0x53, 0x40, 0x170
T_NAME_LEN = 70
P_REC = 312
A_REC, A_PID, A_TID, A_PACK = 16, 0x04, 0x08, 0x0C
PLAYER_CAP = 123825
SQUAD = 30


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return " ".join("".join(c if c.isalnum() else " " for c in s.lower()).split())


def u32(b, o):
    return int.from_bytes(b[o : o + 4], "little")


def load(d, n):
    with open(os.path.join(d, n), "rb") as f:
        return bytearray(pesdb.wesys_unpack(f.read()))


def cstr(b):
    return bytes(b).split(b"\0")[0].decode("utf-8", "replace").strip()


def world_teams(raw):
    out = {}
    for o in range(0, len(raw) - T_REC + 1, T_REC):
        tid = u32(raw, o + T_ID)
        out[tid] = {
            "id": tid,
            "name": cstr(raw[o + T_NAME : o + T_NAME + T_NAME_LEN]),
            "country": raw[o + T_COUNTRY],
            "national": bool(raw[o + T_NATIONAL] & 0x80),
        }
    return out


def player_index(players, assigns):
    by_pid, by_name, by_club = {}, {}, {}
    for o in range(0, len(players), P_REC):
        pid = u32(players, o + E.P_ID)
        name = cstr(
            players[o + E.P_NAME : o + E.P_NAME + E.P_NAME_LEN * E.P_NAME_SLOTS]
        )
        by_pid[pid] = o
        by_name.setdefault(norm(name), []).append(pid)
    for o in range(0, len(assigns) - A_REC + 1, A_REC):
        by_club.setdefault(u32(assigns, o + A_TID), []).append(u32(assigns, o + A_PID))
    return by_pid, by_name, by_club


def similar(a, b):
    """the same club's name written two ways: equal, or one's words all inside the other's
    ("Boca" / "CA Boca Juniors", "Velez" / "CA Velez Sarsfield"). Ids alone are not enough:
    this world has reused team ids (2730 is Atletico Grau here and Sarmiento in the release)."""
    wa, wb = norm(a).split(), norm(b).split()
    if not wa or not wb:
        return False
    if wa == wb:
        return True
    small, big = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    return all(w in big for w in small)


def match_clubs(rel, teams):
    """[(release club id, world team id, how)] -- the id when the names agree, else the name"""
    by_name = {}
    for t in teams.values():
        if not t["national"]:
            by_name.setdefault(norm(t["name"]), []).append(t)

    out, seen = [], set()
    for cid, c in sorted(rel.clubs.items(), key=lambda kv: kv[1]["name"]):
        tid = None
        for k in (cid, str(c.get("game_id") or "").strip()):
            if (
                k.isdigit()
                and int(k) in teams
                and not teams[int(k)]["national"]
                and int(k) not in seen
                and similar(teams[int(k)]["name"], c["name"])
            ):
                tid, how = int(k), "id"
                break
        if tid is None:
            same = [
                t for t in (by_name.get(norm(c["name"])) or []) if t["id"] not in seen
            ]
            if len(same) == 1:
                tid, how = same[0]["id"], "name"
            elif len(same) > 1:
                cty = str(c.get("country") or "").strip()
                mine = [t for t in same if cty.isdigit() and t["country"] == int(cty)]
                if len(mine) == 1:
                    tid, how = mine[0]["id"], "name+country"
        if tid is None or tid in seen:
            continue
        seen.add(tid)
        out.append((cid, tid, how))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    ap.add_argument("--world", required=True)
    ap.add_argument("--base", default=None, help="the game's tables (default: --world)")
    ap.add_argument(
        "--go", action="store_true", help="write the tables (otherwise a dry run)"
    )
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()

    log = (lambda *x: None) if a.quiet else print
    rel = NL.Release(a.release)
    version = (
        "".join(c for c in str(rel.version) if c.isalnum() or c in ".-") or "newlife"
    )
    base = a.base or a.world

    teams_raw = load(a.world, "Team.bin")
    teams = world_teams(teams_raw)
    players = load(a.world, "Player.bin")
    assigns = load(a.world, "PlayerAssignment.bin")
    by_pid, by_name, by_club = player_index(players, assigns)

    log(
        "NewLife %s: %d clubs, %d with a squad; world %d teams, %d players"
        % (version, len(rel.clubs), len(rel.squads), len(teams), len(by_pid))
    )

    pairs = match_clubs(rel, teams)
    if a.only:
        want = norm(a.only)
        pairs = [p for p in pairs if want in norm(rel.clubs[p[0]]["name"])]
    if a.limit:
        pairs = pairs[: a.limit]
    how = {}
    for _cid, _tid, h in pairs:
        how[h] = how.get(h, 0) + 1
    log(
        "clubs to update: %d  (%s)"
        % (len(pairs), ", ".join("%s: %d" % kv for kv in sorted(how.items())))
    )

    changes = {}
    claimed = {}
    stat = {"keep": 0, "join": 0, "new": 0, "out": 0, "free_kept": 0}
    for cid, tid, _h in pairs:
        sq = rel.squad(cid)
        if not sq:
            continue
        old = list(by_club.get(tid) or [])
        used, keep, join, add = set(), [], [], []
        ch_edits = {}
        for r in sq:
            ch = {"name": r.get("name", "")}
            ch.update(NL.release_fields(r))
            ch.update(NL.who(r))
            pid = None
            for k in (
                str(r.get("game_id") or "").strip(),
                str(r.get("newlife_id") or "").strip(),
            ):
                if k.isdigit() and int(k) in by_pid:
                    pid = int(k)
                    break
            if pid is None:
                n = norm(r.get("name"))
                mine = [
                    p
                    for p in old
                    if p in by_pid
                    and norm(
                        cstr(
                            players[
                                by_pid[p] + E.P_NAME : by_pid[p]
                                + E.P_NAME
                                + E.P_NAME_LEN * E.P_NAME_SLOTS
                            ]
                        )
                    )
                    == n
                ]
                if len(mine) == 1:
                    pid = mine[0]
                elif len(by_name.get(n) or []) == 1:
                    pid = by_name[n][0]
            if pid is not None and (
                pid in used or (pid in claimed and claimed[pid] != tid)
            ):
                pid = None
            if pid is not None:
                used.add(pid)
                claimed[pid] = tid
                ch_edits[str(pid)] = ch
                if pid in old:
                    keep.append(pid)
                else:
                    join.append(str(pid))
            else:
                add.append(ch)
        out = [p for p in old if p not in used]
        # a club never drops below eleven plus a bench: the last of the old squad stay
        room = max(0, L.MIN_SQUAD - len(keep) - len(join) - len(add))
        stay = [p for p in out if p in by_pid][:room]
        out = [p for p in out if p not in stay]
        # an "add" copies a real record: one of the club's own, else anyone
        like = (keep + join + old or list(by_pid))[0]
        for ch in add:
            ch["like"] = like
        changes[str(tid)] = {
            "edits": ch_edits,
            "join": join,
            "remove": [str(p) for p in out],
            "add": add,
        }
        stat["keep"] += len(keep)
        if a.debug:
            print(
                "  club %-6d %-34s old %2d keep %2d join %2d add %2d out %2d"
                % (
                    tid,
                    rel.clubs[cid]["name"][:34],
                    len(old),
                    len(keep),
                    len(join),
                    len(add),
                    len(out),
                )
            )
        stat["join"] += len(join)
        stat["new"] += len(add)
        stat["out"] += len(out)
        stat["free_kept"] += len(stay)

    n_new = stat["new"]
    log(
        "players: %d stay (same id), %d move in, %d new, %d leave their club, %d old kept as bench"
        % (stat["keep"], stat["join"], n_new, stat["out"], stat["free_kept"])
    )
    log(
        "player table: %d now, %d after (cap %d)"
        % (len(by_pid), len(by_pid) + n_new, PLAYER_CAP)
    )
    if len(by_pid) + n_new > PLAYER_CAP:
        raise SystemExit(
            "the player table would overflow: raise the cap first (layout.json)"
        )
    if not a.go:
        log("dry run: nothing written (pass --go)")
        return

    for n in ("Player.bin", "PlayerAssignment.bin"):
        dst = os.path.join(a.world, "%s.before-nl%s" % (n, version))
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(a.world, n), dst)
    log("backups: *.before-nl%s" % version)

    L.SQUAD = SQUAD
    pl = {"leagues": [], "players": changes}
    total = L.apply(pl, base, a.world, PLAYER_CAP, log)
    log("lbplayers.apply: %d change(s)" % total)

    # a club left short by transfers out (a release squad that is the game's too, with players
    # going elsewhere) gets free agents, the way a Build does
    filled = L.sign_keepers(a.world, log)
    log("clubs filled with free agents: %d" % len(filled))

    # the best eleven for each club that changed, on the formation the game plays
    players = load(a.world, "Player.bin")
    assigns = load(a.world, "PlayerAssignment.bin")
    by_pid, _by_name, by_club = player_index(players, assigns)
    lined = 0
    for _cid, tid, _h in pairs:
        rows = []
        for o in range(0, len(assigns) - A_REC + 1, A_REC):
            if u32(assigns, o + A_TID) != tid:
                continue
            pid = u32(assigns, o + A_PID)
            if pid not in by_pid:
                continue
            rec = players[by_pid[pid] : by_pid[pid] + P_REC]
            order = (u32(assigns, o + A_PACK) & 0xFC00) >> 10
            r = {"player": o, "order": str(order)}
            for f in E.FIELDS:
                r[f] = E.show(f, E.getf(rec, f))
            rows.append(r)
        if len(rows) < 11:
            continue
        for o, order in L.best_eleven(rows).items():
            o = int(o)
            pack = u32(assigns, o + A_PACK) & ~0xFC00 | int(order) << 10
            assigns[o + A_PACK : o + A_PACK + 4] = pack.to_bytes(4, "little")
        lined += 1
    with open(os.path.join(a.world, "PlayerAssignment.bin"), "wb") as f:
        f.write(pesdb.wesys_pack(bytes(assigns)))
    log("best eleven picked for %d clubs" % lined)
    log("done")


if __name__ == "__main__":
    main()

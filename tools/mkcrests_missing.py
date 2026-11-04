"""python mkcrests_missing.py --team-bin <Team.bin> --flags <livecpk root> [--dry]

Fill in the placeholder crest only where the livecpk tree has no `e_<id>_r.png` yet.

`mkcrests.py --flags` renders every club of the deployed Team.bin, which is fine on a fresh
tree but wasteful once a world has 2.600 added clubs: a re-run only needs the ids that were
appended after the last render (the eight leagues of 2026-11-04 added 96 and kept the crests
of the clubs they replaced, so in game their badges came out as whatever the shipped tables
fall back to -- the cup emblems the owner saw). This writes just those, at the same three
sizes and with the same deterministic colour of `mkcrests.py`.

It never overwrites: an id that already has `e_<id>_r.png` keeps every file it has. The ids
come from the Team.bin of the world that is being played, so run it against the livecpk copy.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pesdb
from mkcrests import FIRST_OURS, FLAG_SIZES, crest, roster
from PIL import Image

REC = 1532


def main():
    a = sys.argv[1:]
    get = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    team_bin, flags = get("--team-bin"), get("--flags")
    if not team_bin or not flags:
        print(__doc__)
        return 1
    dry = "--dry" in a

    fd = os.path.join(flags, "common", "render", "symbol", "flag")
    clubs = [c for c in roster(team_bin) if c[0] >= FIRST_OURS]
    missing = [
        c for c in clubs if not os.path.exists(os.path.join(fd, "e_%06d_r.png" % c[0]))
    ]
    print("%d club(s) of ours, %d without a crest" % (len(clubs), len(missing)))
    if dry or not missing:
        for cid, name, _abbr in missing[:20]:
            print("  %6d %s" % (cid, name))
        return 0

    os.makedirs(fd, exist_ok=True)
    for cid, _name, abbr in missing:
        master = crest(cid, abbr if abbr.strip() else str(cid), 512)
        for suf, px in FLAG_SIZES:
            im = master if px == 512 else master.resize((px, px), Image.LANCZOS)
            im.save(os.path.join(fd, "e_%06d%s.png" % (cid, suf)))
    print("wrote %d crest(s) x%d sizes to %s" % (len(missing), len(FLAG_SIZES), fd))
    return 0


if __name__ == "__main__":
    sys.exit(main())

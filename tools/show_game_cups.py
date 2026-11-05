import io
import os
import shutil

WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
LIVE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"

# ccup lines that are really the game's leagues, written as straight knockouts: they hijack the
# cup competition ids of the big countries, so the country had no cup to show.
LEAGUES = {
    "Premier League",
    "LaLiga",
    "Serie A TIM",
    "Ligue 1",
    "Trendyol Süper Lig",
    "CFA Super League",
    "Tanzanian Mainland Premier Division",
    "Ivorian Ligue 1",
    "Brazilian National Third Division",
    "Colombian Second Division",
}

# the game's own domestic cups and super cups (Competition.bin codes *_CUP): they are played by
# the game, so only their ids are needed for Kick Off > Cup.
SHOW = [
    15,
    73,
    17,
    74,
    16,
    76,
    18,
    75,
    19,
    77,
    20,
    78,
    42,
    82,
    49,
    79,
    24,
    123,
    124,
    112,
    113,
    129,
    138,
    118,
    84,
    120,
    121,
    126,
    127,
    140,
    141,
    115,
    116,
]

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
keep, dropped = [], []
for line in lines:
    if line.startswith("ccup "):
        name = line.split("name=", 1)[-1].strip()
        if name in LEAGUES:
            dropped.append((name, line.split()[1]))
            continue
    if line.startswith("showcup "):
        continue
    keep.append(line)

at = next(i for i, l in enumerate(keep) if l.startswith("ccup "))
block = ["showcup %d" % c for c in SHOW]
out = keep[:at] + block + keep[at:]
text = "\n".join(out) + "\n"
for p in (WF, LIVE):
    bak = p + ".before-showcups"
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
print("ligas-como-copa quitadas:", len(dropped))
for n, r in dropped:
    print("   reg %-5s %s" % (r, n))
print("showcup anadidos:", len(SHOW))
print("ccup ahora:", len([l for l in out if l.startswith("ccup ")]))

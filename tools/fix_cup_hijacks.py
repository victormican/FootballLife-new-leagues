import io
import os
import re
import shutil

WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
LIVE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"

# our lines that are copies of the game's own national-team cups (the shipped Cup list already
# shows them: EURO 33, Copa America 34, Asian Cup 35, World Cup 27), a straight duplicate
# ("Russian Cup" next to "Russia Cup") and a friendly competition that is not a cup.
DROP = {
    "AFC Asian Cup",
    "AFC Champions League",
    "Copa America",
    "UEFA EURO",
    "국제 친선 경기",
    "Russian Cup",
}

# cup -> the competition id its own country's cup has in Competition.bin
REMAPPED = {
    "Coppa Italia": 16,  # ITALY_D1_CUP (was 24, Brazil's)
    "Copa BetPlay Dimayor": 123,  # COLOMBIA_CUP (was 126, China's)
    "Russian Supercup": 116,  # RUSSIA_SUPER_CUP (was 129, Denmark's)
}

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
out, dropped, changed = [], [], []
for line in lines:
    if line.startswith("showcup "):
        continue
    if line.startswith("ccup "):
        name = line.split("name=", 1)[-1].strip()
        if name in DROP:
            dropped.append(name)
            continue
        if name in REMAPPED:
            new = REMAPPED[name]
            line2 = re.sub(r"\bcid=\d+", "cid=%d" % new, line, count=1)
            if line2 != line:
                changed.append((name, re.search(r"\bcid=(\d+)", line).group(1), new))
                line = line2
    out.append(line)

text = "\n".join(out) + "\n"
for p in (WF, LIVE):
    bak = p + ".before-hijacks"
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)

print("quitadas:", len(dropped))
for n in dropped:
    print("   ", n)
print("remapeadas:")
for n, a, b in changed:
    print("   %-24s %s -> %d" % (n, a, b))
print("ccup ahora:", len([l for l in out if l.startswith("ccup ")]))

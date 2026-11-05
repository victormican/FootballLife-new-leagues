import io
import os
import shutil

WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
LIVE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
keep, dropped = [], []
for line in lines:
    if line.startswith("ccup ") and line.split("name=", 1)[-1].strip().endswith(" II"):
        dropped.append(line.split("name=", 1)[-1].strip())
        continue
    keep.append(line)

if not dropped:
    print("no hay copias II")
    raise SystemExit(0)

text = "\n".join(keep) + "\n"
for p in (WF, LIVE):
    bak = p + ".before-nodup"
    if not os.path.exists(bak):
        shutil.copy2(p, bak)
    io.open(p, "w", encoding="utf-8", newline="\n").write(text)
print(
    "quitadas %d lineas II; quedan %d ccup"
    % (len(dropped), len([l for l in keep if l.startswith("ccup ")]))
)
print("primera:", dropped[0], "| ultima:", dropped[-1])

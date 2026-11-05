import io
import os
import re

WF = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
LIVE = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
BAK = WF + ".before-names"

lines = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
have = {l.split()[1] for l in lines if l.startswith("ccup ")}
old = io.open(BAK, encoding="utf-8", errors="replace").read().splitlines()

restored = []
for line in old:
    p = line.split()
    if not p or p[0] != "ccup" or p[1] in have:
        continue
    restored.append(line)
    have.add(p[1])

if not restored:
    print("no falta ninguna linea ccup")
    raise SystemExit(0)

body = [l for l in lines if l.startswith("ccup ")] + restored
body.sort(key=lambda l: (l.split("name=", 1)[-1].strip().lower(), l))
rest = [l for l in lines if not l.startswith("ccup ")]
first = next((i for i, l in enumerate(lines) if l.startswith("ccup ")), len(lines))
out = rest[:first] + body + rest[first:]
text = "\n".join(out) + "\n"
io.open(WF, "w", encoding="utf-8", newline="\n").write(text)
io.open(LIVE, "w", encoding="utf-8", newline="\n").write(text)
for l in restored:
    print("restaurada:", l.split("name=")[-1], "|", " ".join(l.split()[:3]))
print("ccup ahora:", len(body))

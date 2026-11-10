import io, re, shutil
WF  = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
WF2 = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
ls = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(ls) if l.startswith("ccup ")]
if not idx:
    raise SystemExit("no hay ccup")
a, b = idx[0], idx[-1] + 1
block = ls[a:b]
assert all(l.startswith("ccup ") for l in block), "bloque ccup no contiguo"
block.sort(key=lambda l: l.split("name=", 1)[1].lower())
ls[a:b] = block
io.open(WF, "w", encoding="utf-8", newline="\n").write("\n".join(ls) + "\n")
shutil.copy2(WF, WF2)
print("copas ordenadas por nombre:", len(block))
for l in block[:5]: print("  " + l.split("name=",1)[1])

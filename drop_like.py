import io, re, shutil
WF  = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
WF2 = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26world.txt"
ls = io.open(WF, encoding="utf-8", errors="replace").read().splitlines()
n = 0
for i, l in enumerate(ls):
    if not l.startswith("ccup ") or " clubs=" not in l: continue
    cid = int(re.search(r"\bcid=(\d+)", l).group(1))
    if cid >= 146: continue
    if " like=" not in l: continue
    ls[i] = re.sub(r"\s+like=\d+", "", l)
    n += 1
io.open(WF, "w", encoding="utf-8", newline="\n").write("\n".join(ls) + "\n")
shutil.copy2(WF, WF2)
print("copas del juego sin like=:", n)

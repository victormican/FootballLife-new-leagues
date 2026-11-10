import io, re
wf = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26MyWorld\fl26world.txt"
SHIPPED = [33, 5, 8, 27, 36, 34, 35, 37]
rows = [(i + 1, c, "(%d) del juego" % c) for i, c in enumerate(SHIPPED)]
n = len(rows) + 1
seen = set(SHIPPED)
for line in io.open(wf, encoding="utf-8", errors="replace").read().splitlines():
    if not line.startswith("ccup ") or line.lstrip().startswith("#"): continue
    m = re.search(r"\bcid=(\d+)", line)
    if not m: continue
    cid = int(m.group(1))
    if cid in seen:
        print("  (saltada, ya estaba) cid", cid, line.split("name=", 1)[1])
        continue
    seen.add(cid)
    rows.append((n, cid, line.split("name=", 1)[1]))
    n += 1
print("total filas esperadas:", len(rows))
print()
for pos, cid, nm in rows[-24:]:
    print("%3d  cid %3d  %s" % (pos, cid, nm))

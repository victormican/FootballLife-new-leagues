#!/usr/bin/env python
import sys, os, collections, struct

sys.path.insert(0, r"tools")
import mkcoaches
import pesdb

# Cargar datos actuales
root = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26All\common\etc\pesdb"
team_data = open(os.path.join(root, "Team.bin"), "rb").read()
if team_data[3:8] == b"WESYS":
    team_data = pesdb.wesys_unpack(team_data)
coach_data = open(os.path.join(root, "Coach.bin"), "rb").read()
if coach_data[3:8] == b"WESYS":
    coach_data = pesdb.wesys_unpack(coach_data)

nteams = len(team_data) // 1532
ncoach = len(coach_data) // 100

# IDs de entrenadores existentes
existing_ids = set()
for i in range(ncoach):
    cid = struct.unpack_from("<I", coach_data, i * 100)[0]
    existing_ids.add(cid)

# Manager ids actuales en teams
mgr = []
for i in range(nteams):
    mi = struct.unpack_from("<I", team_data, i * 1532)[0]
    mgr.append(mi)

# Count sharing
from collections import Counter

cm = Counter(m for m in mgr if 0 < m < ncoach)
print("Entrenadores distintos usados:", len(cm))
print("Clubes que comparten entrenador:", sum(c for c in cm.values()))
print("Ids de entrenador sin usar:", ncoach - len(cm))

# Generar nuevos entrenadores para los clubs que no tienen uno válido
needed = nteams - len([m for m in mgr if 0 < m < ncoach])
print("Clubes sin entrenador válido:", needed)

# Ejecutar mkcoaches para añadir entrenadores
# --coach usa el Coach.bin existente, --out escribe uno nuevo
coach_in = root + "\\Coach.bin"
outpath = root + "\\Coach_new.bin"
sys.argv = ["mkcoaches.py", root, "--coach", coach_in, "--out", outpath]
try:
    mkcoaches.main()
    print("mkcoaches completed")
except SystemExit as e:
    print("mkcoaches exit:", e)

# Verificar nuevo Coach.bin
new_coach = open(outpath, "rb").read()
if new_coach[3:8] == b"WESYS":
    new_coach = pesdb.wesys_unpack(new_coach)
new_ncoach = len(new_coach) // 100
print("Nuevo Coach.bin:", new_ncoach, "entrenadores")

# Verificar ids nuevos
new_ids = set()
for i in range(new_ncoach):
    cid = struct.unpack_from("<I", new_coach, i * 100)[0]
    new_ids.add(cid)
print("Ids nuevos totales:", len(new_ids))
print("Ids superpuestos con los existentes:", len(new_ids & existing_ids))
print("Ids totalmente nuevos:", len(new_ids - existing_ids))

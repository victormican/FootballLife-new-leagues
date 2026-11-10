#!/usr/bin/env python
import sys, os, struct, collections

sys.path.insert(0, r"tools")
import pesdb

root = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\livecpk\_FL26All\common\etc\pesdb"

# 1. Cargar Coach.bin
coach_raw = open(os.path.join(root, "Coach.bin"), "rb").read()
ncoach = len(coach_raw) // 100
print("Coach.bin:", ncoach, "registros")

# 2. Obtener ids existentes y cuáles están "sin usar" (no asignados a ningún club)
team_raw = open(os.path.join(root, "Team.bin"), "rb").read()
if team_raw[3:8] == b"WESYS":
    team_raw = pesdb.wesys_unpack(team_raw)
nteams = len(team_raw) // 1532
print("Equipos:", nteams)

# Manager ids actuales en teams
mgr = []
for i in range(nteams):
    mi = struct.unpack_from("<I", team_raw, i * 1532)[0]
    mgr.append(mi)

# IDs de entrenador que ya existen en Coach.bin
coach_ids = set()
for i in range(ncoach):
    cid = struct.unpack_from("<I", coach_raw, i * 100)[0]
    coach_ids.add(cid)

# IDs "sin usar" = en Coach.bin pero ningún club los usa
unused_ids = coach_ids - set(m for m in mgr if m != 0)
print("IDs en Coach.bin sin usar por ningun club:", len(unused_ids))
print("Ejemplos:", sorted(unused_ids)[:10])

# Clubs sin entrenador válido (manager id fuera de rango o =0)
# manager id válido = 0 < id < ncoach (1078)
valid_ids = set(m for m in mgr if 0 < m < ncoach)
clubs_without_valid_mgr = [i for i, m in enumerate(mgr) if not (0 < m < ncoach)]
print("Clubes sin manager válido:", len(clubs_without_valid_mgr))

# Seleccionar los primeros N clubs sin manager válido (N = min(len(unused_ids), len(clubs_without_valid_mgr)))
N = min(len(unused_ids), len(clubs_without_valid_mgr))
print("Reasignaremos", N, "entrenadores")

# Ordenar ids sin usar para consistencia
sorted_unused = sorted(unused_ids)

# 3. Reescribir Coach.bin: para los primeros N ids sin usar, los mantendremos,
# pero los remapearemos a nuevos posiciones si es necesario.
# Como ya hay 1078 entrenadores y el tope es 1300, podemos reutilizar ids sin usar
# asignándolos a clubs que carecen de entrenador.

# Crear nuevo array de ids en Coach.bin: remapear los N ids a nuevas posiciones
# o simplemente asignarlos tal cual; los ids son valores dispersos, no índices.
# Lo que haremos: para los N clubs sin manager, asignaremos un id de los sin usar.

# Primero, construir mapping: club_index -> nuevo id de entrenador
mapping = {}
for idx in range(N):
    club_idx = clubs_without_valid_mgr[idx]
    new_id = sorted_unused[idx]
    mapping[club_idx] = new_id

print("Mapeo creado para", len(mapping), "clubs")

# 4. Actualizar Team.bin: para los clubs en el mapping, cambiar su manager id
team_updated = bytearray(team_raw)
clubs_updated = 0
for club_idx, new_id in mapping.items():
    # El offset del manager id en Team.bin es +0x00, un entero de 4 bytes
    offset = club_idx * 1532 + 0  # +0x00 dentro del registro
    # Escribir el nuevo id (little-endian 32-bit)
    struct.pack_into("<I", team_updated, offset, new_id)
    clubs_updated += 1

print("Actualizando Team.bin para", clubs_updated, "clubs")

# 5. Escribir Team.bin actualizado
team_out_path = root + "\\Team_new.bin"
with open(team_out_path, "wb") as f:
    f.write(bytes(team_updated))
print("Team.new.bin escrito")

# 6. Verificar: contar clubs con manager id válido después
new_mgr = []
for i in range(nteams):
    mi = struct.unpack_from("<I", team_updated, i * 1532)[0]
    new_mgr.append(mi)
new_cm = collections.Counter(m for m in new_mgr if 0 < m < ncoach)
print("Después de reasignación:")
print("  Entrenadores distintos usados:", len(new_cm))
print("  Clubs que comparten entrenador:", sum(c for c in new_cm.values()))
print(
    "  Clubs con manager id fuera de rango o 0:",
    sum(1 for m in new_mgr if m >= ncoach or m == 0),
)

# 7. Verificar que ningún id exceda el tope de 1300
max_id = max(new_mgr)
print("Max manager id asignado:", max_id, "(tope permitido: 1300)")

# Opcional: también escribir Coach.bin nueva versión (copia exacta, ids inalterados)
# coach_out_path = root + "\\Coach_new.bin"
# with open(coach_out_path, "wb") as f:
#     f.write(coach_raw)
# print("Coach.new.bin escrito (copia)")

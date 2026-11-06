"""fix_cid2_entries.py -- arregla la lista de entradas de la competicion 2 (la copa europea).

El defecto viene de los datapacks del juego: en 4 de los 5, `CompetitionEntry.bin` trae para
el cid 2 una fila con equipo 0 (plaza 28) y dos filas en la plaza 32. `check_world` lo avisaba
como "competition 2 has two clubs at position 32 (a shipped cup with several stages)".

Que hace, con copia de seguridad:
  * quita la fila del equipo 0,
  * renumera las filas del cid 2 a plazas 1..N conservando el orden y la fila original (solo
    cambia el byte de la plaza, +9; el cid alto de +0x0b no se toca),
  * vuelve a empaquetar el WESYS con la misma cabecera.

  python tools/fix_cid2_entries.py --pesdb <world .../common/etc/pesdb> [--cid 2] [--dry-run]
"""

import argparse
import os
import shutil
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pesdb


def fields(row):
    team, rowid = struct.unpack_from("<II", row, 0)
    return team, row[8] | (row[11] << 8), row[9]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pesdb", required=True)
    ap.add_argument("--cid", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    path = os.path.join(a.pesdb, "CompetitionEntry.bin")
    d = open(path, "rb").read()
    hdr = d[:3]
    raw = pesdb.wesys_unpack(d)
    rows = pesdb.rows(raw, 12)

    mine = [(i, r) for i, r in enumerate(rows) if fields(r)[1] == a.cid]
    print("cid %d: %d filas" % (a.cid, len(mine)))
    for _, r in mine:
        t, c, s = fields(r)
        print("   plaza %-3d equipo %s" % (s, t if t else "(vacio)"))
    if not mine:
        raise SystemExit("no hay filas para ese cid")

    valid = [r for _, r in mine if fields(r)[0] != 0]
    order = {id(r): k for k, (_, r) in enumerate(mine)}
    valid.sort(key=lambda r: (fields(r)[2], order[id(r)]))
    fixed = []
    for k, r in enumerate(valid, 1):
        b = bytearray(r)
        b[9] = k
        fixed.append(bytes(b))

    first = mine[0][0]
    new_rows = [r for i, r in enumerate(rows) if fields(r)[1] != a.cid]
    new_rows[first:first] = fixed
    print(
        "despues: %d filas, plazas %s" % (len(fixed), [fields(r)[2] for r in fixed][:8])
    )
    if a.dry_run:
        print("dry-run: no se escribe nada")
        return
    bak = path + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(path, bak)
    open(path, "wb").write(pesdb.wesys_pack(b"".join(new_rows), hdr))
    print("escrito %s (backup %s)" % (path, os.path.basename(bak)))


if __name__ == "__main__":
    main()

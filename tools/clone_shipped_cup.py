"""clone_shipped_cup.py -- convierte una copa nativa en "nuestra": mismo id, otras entradas y nombre.

  python tools/clone_shipped_cup.py --base <pesdb> --out <livecpk> --cid 56 --reg 68
         --code COPA_TEST --name "Copa Test" --teams 17:1,17:2,...

Todo lo que hace falta para que sea jugable (id, slot, fechas, reglas, info) se queda como esta;
solo cambian las entradas y el nombre.
"""

import argparse
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pesdb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cid", type=int, required=True)
    ap.add_argument("--reg", type=int, required=True)
    ap.add_argument("--code", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--teams", required=True)
    a = ap.parse_args()

    comp_raw = pesdb.load("Competition", a.base)
    reg_raw = pesdb.load("CompetitionRegulation", a.base)
    ent_raw = pesdb.load("CompetitionEntry", a.base)
    base_ents = pesdb.entry_rows(ent_raw)

    # resolver posiciones (reg:slot) a ids de equipo
    bycid = {}
    for e in base_ents:
        bycid.setdefault(e["comp"], []).append(e)
    want = []
    for tok in a.teams.split(","):
        reg, slot = tok.split(":")
        reg, slot = int(reg), int(slot)
        # la regulacion reg pertenece a un cid: buscar su competicion
        rows = pesdb.reg_rows(reg_raw)
        cid = next((r["cid"] for r in rows if r["id"] == reg), None)
        if cid is None:
            raise SystemExit("regulacion %d sin cid" % reg)
        pool = sorted(bycid.get(cid, []), key=lambda e: e["slot"])
        if slot < 1 or slot > len(pool):
            raise SystemExit("reg %d no tiene plaza %d (%d)" % (reg, slot, len(pool)))
        want.append(pool[slot - 1]["team"])
    print("equipos:", want)

    # filas nuevas: fuera las del cid, dentro las nuestras con plaza 1..N
    others = [r for r in pesdb.rows(ent_raw, 12) if (r[8] | (r[11] << 8)) != a.cid]
    new_rows = []
    rowid = 0x18300000
    for i, t in enumerate(want, 1):
        new_rows.append(struct.pack("<III", t, rowid + i, a.cid | (i << 8)))
    raw_e = b"".join(others + new_rows)

    # fila de competicion: codigo nuevo (16 B desde +0x14) y el resto intacto
    comps = pesdb.rows(comp_raw, 36)
    out_c = []
    for r in comps:
        if r[5] == a.cid:
            b = bytearray(r)
            code = a.code.encode("ascii")[:15]
            b[0x14 : 0x14 + 16] = code + b"\0" * (16 - len(code))
            out_c.append(bytes(b))
        else:
            out_c.append(r)
    raw_c = b"".join(out_c)

    # regulacion: nombre "Copa Test" en el primer slot (115 B desde +0x14)
    regs = pesdb.rows(reg_raw, 2352)
    out_r = []
    for r in regs:
        if (r[2] | (r[3] << 8)) == a.reg:
            b = bytearray(r)
            nm = a.name.encode("utf-8")[:114]
            for k in range(20):
                o = 0x14 + k * 115
                b[o : o + 115] = nm + b"\0" * (115 - len(nm))
            out_r.append(bytes(b))
        else:
            out_r.append(r)
    raw_r = b"".join(out_r)

    for tbl, raw in (
        ("Competition", raw_c),
        ("CompetitionRegulation", raw_r),
        ("CompetitionEntry", raw_e),
    ):
        d = os.path.join(a.out, "common", "etc", "pesdb")
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, tbl + ".bin")
        hdr = b"\x00\x01\x01"
        if os.path.exists(os.path.join(a.base, tbl + ".bin")):
            hdr = open(os.path.join(a.base, tbl + ".bin"), "rb").read()[:3]
        open(p, "wb").write(pesdb.wesys_pack(raw, hdr))
        print("escrito", p, len(raw))


if __name__ == "__main__":
    main()

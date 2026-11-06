"""fl26dis.py -- indice de desensamblado de FL_2026.exe (solo lectura).

  python tools/fl26dis.py --db <salida.sqlite> [--summary <salida.txt>]

Que hace, en una pasada:
  * lee la cabecera PE (secciones, imports, .pdata),
  * desensambla .text entero con capstone (39 MB),
  * delimita funciones con .pdata,
  * guarda en SQLite: funciones, aristas de llamada, referencias rip-relative (datos e IAT),
    cadenas alcanzadas y unas cuantas direcciones conocidas (landmarks).

El mapa VA -> fichero de este exe es VA = offset + 0x140000a00 (comprobado).
"""

import argparse
import os
import sqlite3
import struct
import sys
import time

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_RIP

EXE = r"D:\SP Football Life 2026 - copia - copia\FL_2026.exe"
BASE = 0x140000000
DELTA = 0x140000A00
TEXT_OFF, TEXT_SIZE = 0x600, 0x252D800

LANDMARKS = {
    0x143705E10: ("owner_global", "global del dueno; [this+0x48] = bloque de edicion"),
    0x1414B6A60: ("owner_getter", "devuelve el objeto dueno (una instruccion)"),
    0x1414B6D75: ("?", "lectura cerca del accessor del dueno"),
    0x1414F1480: ("census", "censo de Select Team: lee Competition y CompetitionEntry"),
    0x1414F1500: (
        "census_cid_read",
        "cid de la fila de competicion, byte (parche cid)",
    ),
    0x1414F1609: ("census_entry_pack", "empaqueta la clave de entrada (parche pack)"),
    0x1414F1D6A: ("census_key_a", "clave del censo, primer bucle (parche map)"),
    0x1414F1E5A: ("census_key_b", "clave del censo, segundo bucle (parche map)"),
    0x1414F1D8B: ("census_find_a", "busqueda del censo, primer bucle (parche map)"),
    0x1414F1EA1: ("census_find_b", "busqueda del censo, segundo bucle (parche map)"),
    0x1414F1576: ("census_insert", "inserta en el mapa del censo (parche map)"),
    0x1414F7533: (
        "slot_list_build",
        "constructor de la lista de slots de Select Team (parche build)",
    ),
    0x1414F7E80: (
        "reg_list_build",
        "lista de clubs del registro de regulacion (+0x170) (parche list)",
    ),
    0x1419221F0: ("set_record_cid", "mov [rcx+0x80], edx"),
    0x1414CB030: ("slot_for_cid", "cid -> plaza"),
    0x1414CB660: (
        "slot_walk",
        "recorre la tabla de plazas y compara el cid del registro",
    ),
    0x14158DF30: ("comp_resolver", "resuelve competicion por id u16"),
    0x1414BB000: ("reg_by_id", "regulacion por id"),
    0x141EEE1C0: ("reg_by_cid", "regulacion por cid (contenedor de filas)"),
    0x141EEE27C: ("reg_by_cid_read", "cid de la fila de regulacion, byte (parche reg)"),
    0x1414C9A10: ("list_add_club", "anade un club a la lista"),
    0x1414C9740: ("list_clear", "limpia la lista"),
    0x141029CE0: ("list_push", "otro push de lista"),
}


def load():
    with open(EXE, "rb") as f:
        return f.read()


def pe_sections(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    sectab = opt + (240 if magic == 0x20B else 224)
    secs = []
    for i in range(nsec):
        o = sectab + i * 40
        name = data[o : o + 8].rstrip(b"\0").decode("latin1")
        vs, va, rs, ra = struct.unpack_from("<IIII", data, o + 8)
        secs.append(dict(name=name, va=BASE + va, vsize=vs, raw=ra, rsize=rs))
    dirs = [struct.unpack_from("<II", data, dd + 8 * i) for i in range(16)]
    return secs, dirs


def read_va(data, secs, va, n):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            off = s["raw"] + (va - s["va"])
            return data[off : off + n]
    return None


def read_cstr(data, secs, va, maxlen=120):
    b = read_va(data, secs, va, maxlen)
    if not b:
        return None
    b = b.split(b"\0")[0]
    if not b:
        return None
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("latin1")


def imports_map(data, secs, dirs):
    """{iat_va: 'dll!func'}"""
    rva, size = dirs[1]
    if not rva:
        return {}
    out = {}
    va = BASE + rva
    while True:
        desc = read_va(data, secs, va, 20)
        if not desc or desc == b"\0" * 20:
            break
        oft, ts, fc, name_rva, ft = struct.unpack("<IIIII", desc)
        dll = read_cstr(data, secs, BASE + name_rva, 60) or "?"
        thunk_va = BASE + (oft or ft)
        iat_va = BASE + ft
        k = 0
        while True:
            t = read_va(data, secs, thunk_va + 8 * k, 8)
            if not t:
                break
            v = struct.unpack("<Q", t)[0]
            if v == 0:
                break
            if v & 0x8000000000000000:
                out[iat_va + 8 * k] = "%s!#%d" % (dll, v & 0xFFFF)
            else:
                nm = read_cstr(data, secs, BASE + (v & 0x7FFFFFFF) + 2, 80) or "?"
                out[iat_va + 8 * k] = "%s!%s" % (dll, nm)
            k += 1
        va += 20
    return out


def pdata_functions(data, secs, dirs):
    rva, size = dirs[3]
    if not rva:
        return []
    raw = read_va(data, secs, BASE + rva, size)
    fns = []
    for i in range(0, len(raw) - 11, 12):
        b, e, u = struct.unpack_from("<III", raw, i)
        if b == 0 and e == 0:
            continue
        fns.append((BASE + b, BASE + e))
    fns.sort()
    return fns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--summary", default=None)
    args = ap.parse_args()

    t0 = time.time()
    data = load()
    secs, dirs = pe_sections(data)
    iat = imports_map(data, secs, dirs)
    fns = pdata_functions(data, secs, dirs)
    print(
        "secciones %d, imports %d, funciones %d" % (len(secs), len(iat), len(fns)),
        flush=True,
    )

    # funcion que contiene cada direccion
    starts = [f[0] for f in fns]

    def func_of(va):
        lo, hi = 0, len(starts) - 1
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            if starts[mid] <= va:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if best is None:
            return None
        return fns[best] if va < fns[best][1] else None

    if os.path.exists(args.db):
        os.remove(args.db)
    con = sqlite3.connect(args.db)
    con.executescript("""
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        CREATE TABLE funcs(start INTEGER PRIMARY KEY, end INTEGER, ninstr INTEGER DEFAULT 0,
                           nrefs INTEGER DEFAULT 0, ncalls INTEGER DEFAULT 0);
        CREATE TABLE calls(site_func INTEGER, site INTEGER, target INTEGER, target_func INTEGER);
        CREATE TABLE refs(site_func INTEGER, site INTEGER, target INTEGER, kind TEXT, text TEXT);
        CREATE TABLE landmarks(va INTEGER PRIMARY KEY, name TEXT, note TEXT);
        CREATE TABLE strings(va INTEGER, text TEXT);
    """)
    con.executemany("INSERT INTO funcs(start,end) VALUES (?,?)", fns)
    con.executemany(
        "INSERT INTO landmarks(va,name,note) VALUES (?,?,?)",
        [(k, v[0], v[1]) for k, v in LANDMARKS.items()],
    )
    con.commit()

    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True
    code = data[TEXT_OFF : TEXT_OFF + TEXT_SIZE]
    text_va = TEXT_OFF + DELTA

    cur = None
    cur_idx = 0
    ninstr = nrefs = ncalls = 0
    calls, refs, strings = [], [], []
    seen_strings = set()
    fi = 0
    n = 0

    def flush_func():
        if cur is not None:
            con.execute(
                "UPDATE funcs SET ninstr=?, nrefs=?, ncalls=? WHERE start=?",
                (ninstr, nrefs, ncalls, cur[0]),
            )

    CHUNK = 1 << 22
    pos = 0
    while pos < len(code):
        chunk = code[pos:pos + CHUNK]
        base = text_va + pos
        i = 0
        while i < len(chunk):
            progressed = False
            for ins in md.disasm(chunk[i:], base + i):
                if ins.address + ins.size > base + len(chunk):
                    break
                progressed = True
                i = ins.address - base + ins.size
                n += 1
                if cur is None or not (cur[0] <= ins.address < cur[1]):
                    flush_func()
                    cur = func_of(ins.address)
                    fi += 1
                    ninstr = nrefs = ncalls = 0
                    if cur is None:
                        continue
                ninstr += 1
                m = ins.mnemonic
                if m in ("call", "jmp"):
                    for op in ins.operands:
                        if op.type == X86_OP_IMM:
                            tgt = op.imm & 0xFFFFFFFFFFFFFFFF
                            tf = func_of(tgt) if BASE <= tgt < BASE + 0x20000000 else None
                            calls.append((cur[0], ins.address, tgt, tf[0] if tf else None))
                            ncalls += 1
                        elif op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
                            tgt = (ins.address + ins.size + op.mem.disp) & 0xFFFFFFFFFFFFFFFF
                            if tgt in iat:
                                refs.append((cur[0], ins.address, tgt, "iat", iat[tgt]))
                                nrefs += 1
                    continue
                for op in ins.operands:
                    if op.type != X86_OP_MEM or op.mem.base != X86_REG_RIP:
                        continue
                    tgt = (ins.address + ins.size + op.mem.disp) & 0xFFFFFFFFFFFFFFFF
                    nrefs += 1
                    if tgt in iat:
                        refs.append((cur[0], ins.address, tgt, "iat", iat[tgt]))
                    else:
                        s = read_cstr(data, secs, tgt, 80) if tgt else None
                        if s and len(s) >= 4 and s.isprintable():
                            refs.append((cur[0], ins.address, tgt, "str", s))
                            if tgt not in seen_strings:
                                seen_strings.add(tgt)
                                strings.append((tgt, s))
                        else:
                            refs.append((cur[0], ins.address, tgt, "data", None))
                if len(refs) > 200000 or len(calls) > 200000:
                    con.executemany("INSERT INTO refs VALUES (?,?,?,?,?)", refs)
                    con.executemany("INSERT INTO strings VALUES (?,?)", strings)
                    con.executemany("INSERT INTO calls VALUES (?,?,?,?)", calls)
                    refs, strings, calls = [], [], []
                    con.commit()
                if n % 2000000 == 0:
                    print(
                        "  %d M instrucciones, %.0f s" % (n // 1000000, time.time() - t0),
                        flush=True,
                    )

            if not progressed:
                i += 1
        pos = base - text_va + i
    flush_func()
    con.executemany("INSERT INTO refs VALUES (?,?,?,?,?)", refs)
    con.executemany("INSERT INTO strings VALUES (?,?)", strings)
    con.executemany("INSERT INTO calls VALUES (?,?,?,?)", calls)
    con.execute("CREATE INDEX i_refs_func ON refs(site_func)")
    con.execute("CREATE INDEX i_refs_target ON refs(target)")
    con.execute("CREATE INDEX i_calls_func ON calls(site_func)")
    con.execute("CREATE INDEX i_calls_target ON calls(target)")
    con.commit()

    # resumen
    stats = {}
    stats["funciones"] = con.execute("SELECT COUNT(*) FROM funcs").fetchone()[0]
    stats["instrucciones"] = n
    stats["referencias"] = con.execute("SELECT COUNT(*) FROM refs").fetchone()[0]
    stats["llamadas"] = con.execute("SELECT COUNT(*) FROM calls").fetchone()[0]
    stats["cadenas"] = con.execute("SELECT COUNT(*) FROM strings").fetchone()[0]
    stats["imports"] = len(iat)
    stats["segundos"] = round(time.time() - t0, 1)

    lines = ["# Indice de FL_2026.exe", ""]
    for k, v in stats.items():
        lines.append("- %s: %s" % (k, v))
    lines.append("")
    lines.append("## Secciones")
    for s in secs:
        lines.append(
            "- %-8s va %#010x vsize %#x raw %#x"
            % (s["name"], s["va"], s["vsize"], s["raw"])
        )
    lines.append("")
    lines.append("## Funciones mas grandes")
    for st, en, ni, nr, nc in con.execute(
        "SELECT start,end,ninstr,nrefs,ncalls FROM funcs ORDER BY ninstr DESC LIMIT 40"
    ):
        lines.append(
            "- %#010x..%#010x  %5d instr  %4d refs  %4d calls" % (st, en, ni, nr, nc)
        )
    lines.append("")
    lines.append("## Landmarks: quien los llama")
    for va, (name, note) in sorted(LANDMARKS.items()):
        rows = con.execute(
            "SELECT DISTINCT site_func FROM calls WHERE target=?", (va,)
        ).fetchall()
        callers = [r[0] for r in rows if r[0]]
        if callers:
            lines.append(
                "- %s %#x: %d llamadores: %s"
                % (name, va, len(callers), ", ".join("%#x" % c for c in callers[:12]))
            )
    lines.append("")
    lines.append("## Landmarks: funciones que los referencian (datos/IAT)")
    for va, (name, note) in sorted(LANDMARKS.items()):
        rows = con.execute(
            "SELECT DISTINCT site_func FROM refs WHERE target=?", (va,)
        ).fetchall()
        funcs_ref = [r[0] for r in rows if r[0]]
        if funcs_ref:
            lines.append(
                "- %s %#x: %d funciones: %s"
                % (
                    name,
                    va,
                    len(funcs_ref),
                    ", ".join("%#x" % c for c in funcs_ref[:12]),
                )
            )
    txt = "\n".join(lines)
    if args.summary:
        open(args.summary, "w", encoding="utf-8").write(txt)
    print(txt[:4000])
    con.close()
    print("listo en %.1f s -> %s" % (time.time() - t0, args.db), flush=True)


if __name__ == "__main__":
    main()

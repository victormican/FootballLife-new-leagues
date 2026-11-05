"""livereg.py -- lee el bloque de edicion vivo de FL_2026.exe. No escribe nada.

  python livereg.py              estado del bloque, escaneo del array y ligas de interes
  python livereg.py --all        vuelca todas las regulaciones del array
  python livereg.py --scan N     escanea N registros del array (por defecto 1500)

Direcciones (el exe no tiene ASLR):

  0x143705e10        global del dueno
  [dueno + 0x48]     bloque de edicion
  bloque + 0xd0bcf4  u32 numero de registros
  bloque + 0xc131b0  registros, paso 0x314
  registro + 0x00    u16 id de regulacion
  registro + 0x80    u32 cid
  registro + 0x170   u32 handles de club, equipo = handle >> 14

Aviso medido el 2026-11-06: en la pantalla Jugar > Liga > Nuevo el bloque NO esta cargado
(jugadores 0, equipos 0, regulaciones 65535), asi que el panel "Informacion de la Liga" no lee
este array sino las tablas pesdb. Por eso este volcado sirve para el censo de Select Team y para
comprobar el bloque, no para explicar el panel.
"""

import ctypes
import ctypes.wintypes as w
import sys

K32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
TH32CS_SNAPPROCESS = 0x00000002


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", w.DWORD),
        ("cntUsage", w.DWORD),
        ("th32ProcessID", w.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", w.DWORD),
        ("cntThreads", w.DWORD),
        ("th32ParentProcessID", w.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", w.DWORD),
        ("szExeFile", ctypes.c_char * 260),
    ]


def find_pid(name=b"FL_2026.exe"):
    snap = K32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    e = PROCESSENTRY32()
    e.dwSize = ctypes.sizeof(e)
    out = []
    ok = K32.Process32First(snap, ctypes.byref(e))
    while ok:
        if e.szExeFile.lower() == name.lower():
            out.append(e.th32ProcessID)
        ok = K32.Process32Next(snap, ctypes.byref(e))
    K32.CloseHandle(snap)
    return out


class Mem:
    def __init__(self, pid):
        self.h = K32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
        )
        if not self.h:
            raise OSError(
                "OpenProcess fallo (error %d). El juego corre elevado: lanza esto tambien elevado."
                % ctypes.get_last_error()
            )

    def read(self, addr, n):
        buf = ctypes.create_string_buffer(n)
        got = ctypes.c_size_t(0)
        if not K32.ReadProcessMemory(
            self.h, ctypes.c_void_p(addr), buf, n, ctypes.byref(got)
        ):
            return None
        return buf.raw if got.value == n else None

    def u16(self, a):
        b = self.read(a, 2)
        return None if b is None else int.from_bytes(b, "little")

    def u32(self, a):
        b = self.read(a, 4)
        return None if b is None else int.from_bytes(b, "little")

    def u64(self, a):
        b = self.read(a, 8)
        return None if b is None else int.from_bytes(b, "little")


OWNER = 0x143705E10
OFF_BLOCK = 0x48
OFF_ARRAY = 0xC131B0
OFF_COUNT = 0xD0BCF4
OFF_PLAYERS = 0xD0BCE8
OFF_TEAMS = 0xD0BCEC
OFF_COACHES = 0xD0BCF0
STRIDE = 0x314
CLUBS = 0x170

TARGETS = [
    351,
    111,
    904,
    907,
    126,
    250,
    470,
    181,
    364,
    256,
    362,
    76,
    9000,
    178,
    182,
    900,
    901,
    902,
    903,
    905,
    906,
    908,
]


def clubs(m, rec, cap=128):
    ids, raw = [], []
    for k in range(cap):
        v = m.u32(rec + CLUBS + 4 * k)
        if v is None:
            break
        raw.append(v)
        if v in (0, 0xFFFFFFFF):
            break
        ids.append(v >> 14)
    return ids, raw


def show(m, rec, tag):
    rid = m.u16(rec)
    cid = m.u32(rec + 0x80)
    ids, raw = clubs(m, rec)
    print(
        "%-10s rec %#010x id %-5s cid %-5s n %-3d ids %s"
        % (tag, rec, rid, cid, len(ids), ",".join(str(x) for x in ids[:40]))
    )
    print("           raw %s" % " ".join("%08x" % v for v in raw[:20]))


def main():
    pids = find_pid()
    if not pids:
        raise SystemExit("FL_2026.exe no esta corriendo")
    m = Mem(pids[0])
    owner = m.u64(OWNER)
    print("pid %d dueno %#x" % (pids[0], owner or 0))
    if not owner:
        raise SystemExit("el global del dueno esta a cero")
    block = m.u64(owner + OFF_BLOCK)
    print("bloque %#x" % (block or 0))
    if not block:
        raise SystemExit("el bloque de edicion esta a cero")
    print(
        "jugadores %s  equipos %s  entrenadores %s  regulaciones %s"
        % (
            m.u32(block + OFF_PLAYERS),
            m.u32(block + OFF_TEAMS),
            m.u32(block + OFF_COACHES),
            m.u32(block + OFF_COUNT),
        )
    )

    n = m.u32(block + OFF_COUNT) or 0
    scan = 1500
    if "--scan" in sys.argv:
        scan = int(sys.argv[sys.argv.index("--scan") + 1])
    seen = {}
    for i in range(min(n, scan)):
        rec = block + OFF_ARRAY + i * STRIDE
        rid = m.u16(rec)
        if rid is not None and rid not in seen:
            seen[rid] = rec
            if "--all" in sys.argv or rid in TARGETS:
                show(m, rec, "idx%d" % i)
    print("\nids vistos: %d" % len(seen))
    print(",".join(str(x) for x in sorted(seen)))
    m.close()


if __name__ == "__main__":
    main()

"""inventory_game.py -- listado de una instalacion del juego (sin tocar nada).

python tools/inventory_game.py --game "D:\\SP Football Life 2026 - copia" --out LISTADO.txt
"""

import argparse
import hashlib
import os
import subprocess


def size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def gb(n):
    return "%.2f GB" % (n / (1024**3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    g = a.game
    L = []
    L.append("LISTADO DE LA INSTALACION")
    L.append("carpeta: " + g)
    L.append("")

    exe = os.path.join(g, "FL_2026.exe")
    if os.path.exists(exe):
        st = os.stat(exe)
        h = hashlib.sha256(open(exe, "rb").read()).hexdigest()
        L.append("FL_2026.exe  %d bytes  sha256 %s" % (st.st_size, h))
    L.append("")

    L.append("CARPETAS")
    for name in sorted(os.listdir(g)):
        p = os.path.join(g, name)
        if os.path.isdir(p):
            L.append("  %-24s %10s" % (name, gb(size(p))))
    L.append("")

    sider = os.path.join(g, "SiderAddons")
    L.append("SIDERADDONS")
    if os.path.isdir(sider):
        for name in sorted(os.listdir(sider)):
            p = os.path.join(sider, name)
            if os.path.isdir(p):
                L.append("  %-24s %10s" % (name, gb(size(p))))
        ini = os.path.join(sider, "sider.ini")
        if os.path.exists(ini):
            import io

            mods = []
            roots = []
            for line in io.open(ini, encoding="utf-8", errors="replace"):
                s = line.strip()
                if s.startswith("lua.module"):
                    mods.append(s)
                elif s.startswith("cpk.root"):
                    roots.append(s)
            L.append("")
            L.append("sider.ini: %d lua.module, %d cpk.root" % (len(mods), len(roots)))
            for m in mods:
                L.append("  " + m)
            for r in roots:
                L.append("  " + r)
        lp = os.path.join(sider, "livecpk")
        if os.path.isdir(lp):
            L.append("")
            L.append("livecpk:")
            for name in sorted(os.listdir(lp)):
                L.append("  " + name)
        md = os.path.join(sider, "modules")
        if os.path.isdir(md):
            L.append("")
            L.append("modules:")
            for name in sorted(os.listdir(md)):
                L.append("  " + name)
    L.append("")

    saves = os.path.join(
        os.path.expanduser("~"), "Documents", "KONAMI", "SP Football Life 2026"
    )
    L.append("PARTIDAS")
    L.append(
        "  "
        + saves
        + ("  (%s)" % gb(size(saves)) if os.path.isdir(saves) else "  (no existe)")
    )
    if os.path.isdir(saves):
        for name in sorted(os.listdir(saves)):
            L.append("    " + name)

    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()

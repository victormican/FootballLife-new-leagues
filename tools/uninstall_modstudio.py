"""uninstall_modstudio.py -- deja el juego como estaba antes de FL Mod Studio.

Quita lo que instala Mod Studio, sin tocar Sider ni los packs base:
  * mundos de `SiderAddons\\livecpk\\_FL26*` (y cualquiera con marca `.modstudio`),
  * modulos `fl26*.lua`, `fl26world.txt`, `fl26*.dll`, `fl26regen_faces.bin`,
  * `SiderAddons\\ModStudio` (perfiles y copias),
  * las lineas `fl26` / `_FL26` de `sider.ini` (con copia de seguridad),
  * `%APPDATA%\\FL26ModStudio` (tablas, recetas, packs).

Por defecto **mueve** a `<juego>\\_uninstall_modstudio_<fecha>\\` en vez de borrar; `--purge` borra.
No toca las partidas (`Documents\\KONAMI`) salvo `--saves`.

  python tools/uninstall_modstudio.py --game "D:\\SP Football Life 2026 - copia" [--dry-run] [--purge] [--saves]
"""

import argparse
import glob
import os
import shutil
import time

MARKERS = ("_FL26",)
MODULE_GLOBS = ("fl26*.lua", "fl26*.dll", "fl26world.txt", "fl26regen_faces.bin")


def move(path, dest_root, game, purge, log):
    rel = os.path.relpath(path, game)
    dest = os.path.join(dest_root, rel)
    if purge:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                os.remove(path)
            except OSError:
                pass
        log.append("borrado   " + rel)
    else:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.isdir(path):
            shutil.move(path, dest)
        else:
            shutil.move(path, dest)
        log.append("movido    " + rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=r"D:\SP Football Life 2026 - copia")
    ap.add_argument(
        "--apdata", default=os.path.join(os.environ.get("APPDATA", ""), "FL26ModStudio")
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--purge", action="store_true")
    ap.add_argument("--saves", action="store_true")
    a = ap.parse_args()

    game = os.path.abspath(a.game)
    if not os.path.exists(os.path.join(game, "FL_2026.exe")) and not os.path.exists(
        os.path.join(game, "FL_2027.exe")
    ):
        raise SystemExit("no parece la carpeta del juego: " + game)
    sider = os.path.join(game, "SiderAddons")
    if not os.path.isdir(sider):
        raise SystemExit("no hay SiderAddons en " + game)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest_root = os.path.join(game, "_uninstall_modstudio_" + stamp)
    log = []

    # 1. mundos
    livecpk = os.path.join(sider, "livecpk")
    worlds = []
    if os.path.isdir(livecpk):
        for name in os.listdir(livecpk):
            p = os.path.join(livecpk, name)
            if not os.path.isdir(p):
                continue
            marked = os.path.exists(os.path.join(p, ".modstudio"))
            if (
                marked
                or name.startswith(MARKERS)
                or name in ("_FL26MyWorld", "_FL26MyWorld.building")
            ):
                worlds.append(p)
    # 2. modulos
    mods = []
    mdir = os.path.join(sider, "modules")
    if os.path.isdir(mdir):
        for pat in MODULE_GLOBS:
            mods.extend(glob.glob(os.path.join(mdir, pat)))

    # 3. sider.ini
    ini = os.path.join(sider, "sider.ini")
    drop = set()
    if os.path.exists(ini):
        with open(ini, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                s = line.strip().lower()
                if s.startswith("; lua.module") or s.startswith("lua.module"):
                    if "fl26" in s:
                        drop.add(i)
                elif s.startswith("cpk.root") and "_fl26" in s:
                    drop.add(i)

    # 4. ModStudio y appdata
    ms = os.path.join(sider, "ModStudio")
    apdata = a.apdata if os.path.isdir(a.apdata) else None

    if a.dry_run:
        print("MUNDOS:", [os.path.basename(w) for w in worlds])
        print("MODULOS:", len(mods))
        print("LINEAS sider.ini:", len(drop))
        print("ModStudio:", ms, os.path.isdir(ms))
        print("APPDATA:", apdata)
        print("saves:", a.saves)
        return

    for w in worlds:
        move(w, dest_root, game, a.purge, log)
    for m in mods:
        move(m, dest_root, game, a.purge, log)
    if os.path.isdir(ms):
        move(ms, dest_root, game, a.purge, log)
    if apdata:
        # fuera del juego: se mueve al destino tambien
        rel = os.path.join("_appdata", os.path.basename(apdata))
        dest = os.path.join(dest_root, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if a.purge:
            shutil.rmtree(apdata, ignore_errors=True)
            log.append("borrado   " + apdata)
        else:
            shutil.move(apdata, dest)
            log.append("movido    " + apdata)

    # sider.ini
    if drop:
        bak = ini + ".bak-uninstall-" + stamp
        shutil.copy2(ini, bak)
        with open(ini, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        keep = [l for i, l in enumerate(lines) if i not in drop]
        with open(ini, "w", encoding="utf-8", newline="") as f:
            f.writelines(keep)
        log.append(
            "sider.ini: %d lineas fuera (copia %s)" % (len(drop), os.path.basename(bak))
        )

    # saves (opcional)
    if a.saves:
        saves = os.path.join(
            os.path.expanduser("~"), "Documents", "KONAMI", "SP Football Life 2026"
        )
        if os.path.isdir(saves):
            for name in os.listdir(saves):
                p = os.path.join(saves, name)
                if name.startswith("save_") and os.path.isdir(p):
                    move(p, dest_root, game, a.purge, log)
            marker = os.path.join(saves, "modstudio-saves.json")
            if os.path.exists(marker):
                move(marker, dest_root, game, a.purge, log)

    for l in log:
        print(l)
    print(
        "\n%d cambios. Destino: %s"
        % (len(log), dest_root if not a.purge else "(borrado)")
    )


if __name__ == "__main__":
    main()

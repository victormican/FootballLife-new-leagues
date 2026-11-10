import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26comptab.lua"
s = io.open(p, encoding="utf-8").read()
a = s.index("  -- PRUEBA TEMPORAL (2026-11-04")
b = s.index('log("fl26comptab: PRUEBA -- Sudamericana/GoldCup/OFC Nations/OFC WCQ con OFF_NAME 0..3")')
end = s.index("  end\n", b) + len("  end\n")
s = s[:a] + s[end:]
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("prueba eliminada:", "PRUEBA" not in s)

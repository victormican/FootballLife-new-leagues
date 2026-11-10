import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26comptab.lua"
s = io.open(p, encoding="utf-8").read()
old = "    local probe = { [700] = 0, [701] = 1, [702] = 2, [703] = 3 }"
new = "    local probe = { [513] = 0, [96] = 1, [250] = 2, [251] = 3 }"
assert old in s
s = s.replace(old, new, 1)
s = s.replace('log("fl26comptab: PRUEBA -- 4 copas con OFF_NAME 0..3")',
              'log("fl26comptab: PRUEBA -- Sudamericana/GoldCup/OFC Nations/OFC WCQ con OFF_NAME 0..3")')
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("prueba movida a las 4 primeras copas (filas 9-12 de la lista)")

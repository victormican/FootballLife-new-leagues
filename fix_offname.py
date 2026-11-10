import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26comptab.lua"
s = io.open(p, encoding="utf-8").read()
# 1. la fila de copa nace con OFF_NAME = 1 (no resuelve -> nombre inline)
old = """        rows[#rows + 1] = row_set(row_set(tmpl, OFF_ID, u32le(id)), OFF_SLOT, u32le(123))"""
new = """        rows[#rows + 1] = row_set(row_set(row_set(tmpl, OFF_ID, u32le(id)), OFF_SLOT, u32le(123)),
                                  OFF_NAME, u32le(1))"""
assert old in s
s = s.replace(old, new, 1)
# 2. el bucle de limpieza no debe volver a poner 0xffffffff en las de copa
old2 = """    local ids = {}
    for _, id in ipairs(OUR_IDS) do ids[#ids + 1] = id end
    for _, id in ipairs(WORLD_CUPS) do ids[#ids + 1] = id end
    for _, id in ipairs(ids) do"""
new2 = """    local ids = {}
    for _, id in ipairs(OUR_IDS) do ids[#ids + 1] = id end
    for _, id in ipairs(ids) do"""
assert old2 in s
s = s.replace(old2, new2, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("copas con OFF_NAME = 1")

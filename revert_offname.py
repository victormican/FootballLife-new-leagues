import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26comptab.lua"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""        rows[#rows + 1] = row_set(row_set(row_set(tmpl, OFF_ID, u32le(id)), OFF_SLOT, u32le(123)),
                                  OFF_NAME, u32le(1))""",
"""        rows[#rows + 1] = row_set(row_set(tmpl, OFF_ID, u32le(id)), OFF_SLOT, u32le(123))""")
s = s.replace("""    local ids = {}
    for _, id in ipairs(OUR_IDS) do ids[#ids + 1] = id end
    for _, id in ipairs(ids) do""",
"""    local ids = {}
    for _, id in ipairs(OUR_IDS) do ids[#ids + 1] = id end
    for _, id in ipairs(WORLD_CUPS) do ids[#ids + 1] = id end
    for _, id in ipairs(ids) do""")
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("vuelta a NO_LABEL:", "OFF_NAME, u32le(1)" not in s)

import io
p = r"D:\SP Football Life 2026 - copia - copia\SiderAddons\modules\fl26regcid.lua"
s = io.open(p, encoding="utf-8").read()
old = """  local owner = memory.read(BLOCK_PTR, 8)"""
new = """  -- la cadena que usa phkind: el bloque sale de 0x1414b6a60(), no del global de antes
  if ffi then
    ffi.cdef[[ void* fl26_ctx(void*); ]]
    local fn = ffi.cast("void* (*)(void*)", 0x1414b6a60)
    local arg = ffi.new("uint32_t[1]", 0)
    local ctx = fn(arg)
    local cval = tonumber(ffi.cast("uint64_t", ctx))
    if cval ~= 0 then
      local bptr = ffi.cast("uint64_t*", cval + 0x48)
      local bval = tonumber(bptr[0])
      if bval ~= 0 then
        local cnt = memory.read(bval + COUNT_OFF, 4)
        local first = memory.read(bval + ARRAY_OFF, 4)
        log(string.format("fl26regcid: ctx=%#x block=%#x count=%s firstid=%s", cval, bval,
          cnt and u32(cnt, 0) or "?", first and (first:byte(1) + first:byte(2) * 256) or "?"))
        if cnt and u32(cnt, 0) > 8 and u32(cnt, 0) <= MAX then
          fix_at(bval)
          return
        end
      end
    end
  end
  local owner = memory.read(BLOCK_PTR, 8)"""
assert old in s
s = s.replace(old, new, 1)

# separar el cuerpo de fix() en fix_at(bb) para poder llamarlo con la base buena
old2 = """local function fix()
  if done then return end"""
new2 = """local function fix_at(bb)
  local cntb = memory.read(bb + COUNT_OFF, 4)
  if not cntb then return end
  local n = u32(cntb, 0)
  if n == 0 or n > MAX then return end
  local arr = bb + ARRAY_OFF
  local fixed, seen = 0, 0
  for i = 0, n - 1 do
    local rec = memory.read(arr + i * STRIDE, 4)
    if rec and #rec == 4 then
      local rid = rec:byte(1) + rec:byte(2) * 256
      local want = map[rid]
      if want then
        seen = seen + 1
        local cur = memory.read(arr + i * STRIDE + 0x80, 4)
        if cur and u32(cur, 0) ~= want then
          memory.write(arr + i * STRIDE + 0x80, string.char(want % 256,
            math.floor(want / 256) % 256, math.floor(want / 65536) % 256,
            math.floor(want / 16777216) % 256))
          fixed = fixed + 1
        end
      end
    end
  end
  if seen > 0 then
    log(string.format("fl26regcid: %d regulation(s) seen, %d got their full cid (+0x80)", seen, fixed))
    if fixed == 0 then done = true end
  end
end

local function fix()
  if done then return end"""
assert old2 in s
s = s.replace(old2, new2, 1)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("cadena de phkind anadida")

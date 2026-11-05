--[[
fl26regcid -- put the whole competition id in every live regulation record.

Measured 2026-11-04 with a probe inside the cup handler: phkind (0x14150af30) is what turns a
competition id into its regulation for the Cup menu, and it scans the live regulation array
comparing dword [record+0x80] with the id.  That field only carries the low byte, so a
competition above 255 never matches:

    cid  96 -> k3 = 179  (its regulation)      ok
    cid 250 -> k3 = 183                        ok
    cid 513 -> k3 = 65535  (not found)         <- the Cup menu then shows the first
                                                  competition ("FIFA Club World Cup") and
                                                  has no draw size for it

Whoever writes +0x80 does it with the byte at CompetitionRegulation.bin +0x08 and ignores the
high byte at +0x492 (the same file that fl26cid16 widens for other readers).  Rather than hunt
that instruction, this module rewrites the field once the array exists, from the world file's
own numbers: every `league`/`ccup` line carries `cid=`, and the regulation id is the line's
first field.

How: the live array is `[[0x143705e10]+0x48] + 0xc12e9c`, 0x314 bytes per record, count at
+0xd0bcf4 (the same addresses fl26clubs.lua and the census use).  A record is matched by the
word at +0x00, its regulation id.  Nothing is written unless the count looks sane.
Requires sider.ini: luajit.ext.enabled = 1 (global ffi and `memory`).
--]]

local m = {}

local BLOCK_PTR = 0x143705e10
local ARRAY_OFF, COUNT_OFF, STRIDE, MAX = 0xc12e9c, 0xd0bcf4, 0x314, 1200

local function u32(s, o)
  return s:byte(o + 1) + s:byte(o + 2) * 256 + s:byte(o + 3) * 65536 + s:byte(o + 4) * 16777216
end

local function world_cids(ctx)
  local sep = string.char(92)
  local path = ctx.sider_dir:gsub("[/" .. sep .. "]+$", "") .. sep .. "modules" .. sep .. "fl26world.txt"
  local f = io.open(path, "r")
  if not f then return nil end
  local map = {}
  for line in f:lines() do
    local reg = line:match("^%s*league%s+(%d+)") or line:match("^%s*ccup%s+(%d+)")
    if reg then
      local cid = line:match("%scid=(%d+)")
      if cid then map[tonumber(reg)] = tonumber(cid) end
    end
  end
  f:close()
  return map
end

local map, done, told = nil, false, false
local ticks = 0

local function fix_at(bb)
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
  if done then return end
  -- la cadena que usa phkind: el bloque sale de 0x1414b6a60(), no del global de antes
  if ffi then
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
  local owner = memory.read(BLOCK_PTR, 8)
  if not owner then return end
  local ob = owner:byte(1) + owner:byte(2) * 256 + owner:byte(3) * 65536
            + owner:byte(4) * 16777216 + owner:byte(5) * 4294967296
            + owner:byte(6) * 1099511627776 + owner:byte(7) * 281474976710656
            + owner:byte(8) * 72057594037927936
  if ob == 0 then return end
  local blk = memory.read(ob + 0x48, 8)
  if not blk then return end
  local bb = blk:byte(1) + blk:byte(2) * 256 + blk:byte(3) * 65536
           + blk:byte(4) * 16777216 + blk:byte(5) * 4294967296
           + blk:byte(6) * 1099511627776 + blk:byte(7) * 281474976710656
           + blk:byte(8) * 72057594037927936
  if bb == 0 then return end
  local cntb = memory.read(bb + COUNT_OFF, 4)
  if not cntb then return end
  local n = u32(cntb, 0)
  if not told then
    told = true
    local first = memory.read(bb + ARRAY_OFF, 4)
    log(string.format("fl26regcid: owner=%#x block=%#x count=%d firstid=%s", ob, bb, n,
                      first and (first:byte(1) + first:byte(2) * 256) or "?"))
  end
  if n == 0 or n > MAX then return end
  local arr = bb + ARRAY_OFF
  local fixed, seen = 0, 0
  for i = 0, n - 1 do
    local rec = memory.read(arr + i * STRIDE, 4)
    if rec and #rec == 4 then
      local rid = rec:byte(1) + rec:byte(2) * 256
      local want = rid and map[rid]
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

function m.make_key(ctx, filename)
  if done then return nil end
  ticks = ticks + 1
  if ticks % 16 == 0 then fix() end
  return nil
end

function m.init(ctx)
  if ffi == nil then log("fl26regcid: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  ffi.cdef[[ void* fl26_ctx(void*); ]]
  map = world_cids(ctx)
  if not map then log("fl26regcid: no world file -- nothing to do"); return end
  local n = 0
  for _ in pairs(map) do n = n + 1 end
  log(string.format("fl26regcid: %d competition(s) in the world file to check", n))
  ctx.register("livecpk_make_key", m.make_key)
end

return m

--[[
fl26cid16 -- competition ids above 255.

Why: the engine keeps a competition id in 16 bits (the live record at +0 is a word, the array
has 600 holes, `0x14158df9d cmp word [rax], di`), but three reads in the Select Team census and
the EDIT set-up take it as a **byte**, and one of them packs it into a 16-bit sort key with the
entry's order.  See docs/research/competition-id-16-bit.md for the measurements.

What this does, at boot, runtime only:

  in place (same instruction length, no jump moves):
    0x1414f1500  0f b6 4f 05  ->  0f b7 4f 04   the id is a word at +4 (Competition.bin)
    0x1414f1504  88 4d 68     ->  89 4d 68      the census key is stored as a dword
    0x1414f1518  38 48 20     ->  39 48 20      the map compares dwords
    0x1414f1534  3a 4b 20     ->  39 4b 20      the map compares dwords (the other side)

  in a cave of its own (the read does not fit in place):
    0x1414f1609  the entry pack: the id becomes  byte[+8] | byte[+0xb] << 8, and the sort key
                 is id << 6 | (order-1) -- orders never reach 64, the longest shipped league is
                 48 clubs
    0x141eee27c  the regulation looked up by competition id: the high byte comes from +0x910

The data side has to write those bytes: Competition.bin's id as a word at +4, the entry's high
byte at +0xb and the regulation's high byte at +0x910.  A world that keeps every id below 256
behaves exactly as before.

Nothing is written unless every byte checked first matches the expected exe.
Requires sider.ini: luajit.ext.enabled = 1 (the global ffi and `memory`), like fl26comptab.
--]]

local m = {}

local function hex(s)
  return (s:gsub(".", function(c) return string.format("%02x", c:byte()) end))
end
local function bin(h)
  return (h:gsub("%x%x", function(b) return string.char(tonumber(b, 16)) end))
end
local function u32(v)
  return string.char(v % 256, math.floor(v / 256) % 256, math.floor(v / 65536) % 256,
                     math.floor(v / 16777216) % 256)
end
local function rel32(from_next, to)
  local d = to - from_next
  if d >= 0x80000000 or d < -0x80000000 then return nil end
  if d < 0 then d = d + 0x100000000 end
  return u32(d)
end

local INPLACE = {
  { 0x1414f1500, "0fb64f05", "0fb74f04", "the competition id is a word at +4" },
  { 0x1414f1504, "884d68",   "894d68",   "the census key is stored as a dword" },
  { 0x1414f1518, "384820",   "394820",   "the map compares dwords" },
  { 0x1414f1534, "3a4b20",   "394b20",   "the map compares dwords, other side" },
}

local PACK, PACK_BYTES, PACK_NEXT = 0x1414f1609, "0fb60f66ffc90fb647ff66c1e0086609c166894c2448", 0x1414f161f
local REG,  REG_BYTES,  REG_NEXT  = 0x141eee27c, "0fb650088b4d77", 0x141eee283

local function cave()
  ffi.cdef([[ void* VirtualAlloc(void*, unsigned long, unsigned long, unsigned long); ]])
  for _, pref in ipairs({ 0x15e100000, 0x15f100000, 0x161100000, 0x171100000 }) do
    local p = ffi.C.VirtualAlloc(ffi.cast("void*", pref), 0x1000, 0x3000, 0x40)
    if p ~= nil then return tonumber(ffi.cast("uint64_t", p)) end
  end
  return nil
end

function m.init(ctx)
  if ffi == nil then log("fl26cid16: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  -- verify everything first
  local ok = true
  for _, p in ipairs(INPLACE) do
    local got = memory.read(p[1], #p[2] / 2)
    if got == nil or hex(got) ~= p[2] then
      log(string.format("fl26cid16: bytes at %#x are %s, expected %s -- nothing written",
                        p[1], tostring(got and hex(got)), p[2]))
      ok = false
    end
  end
  local pack = memory.read(PACK, #PACK_BYTES / 2)
  local reg = memory.read(REG, #REG_BYTES / 2)
  if pack == nil or hex(pack) ~= PACK_BYTES then
    log("fl26cid16: the entry pack is not the expected code -- nothing written"); ok = false
  end
  if reg == nil or hex(reg) ~= REG_BYTES then
    log("fl26cid16: the regulation lookup is not the expected code -- nothing written"); ok = false
  end
  if not ok then return end

  for _, p in ipairs(INPLACE) do
    memory.write(p[1], bin(p[3]))
  end
  log("fl26cid16: the census reads competition ids as 16-bit words")

  local cv = cave()
  if not cv then log("fl26cid16: no cave -- the two reads are left alone"); return end

  -- entry pack: id = byte[+8] | byte[+0xb] << 8 ; key = id << 6 | (order - 1)
  local entry_stub = bin("0fb60f" .. "66ffc9" .. "0fb647ff" .. "0fb65702" .. "c1e208" ..
                         "09d0" .. "66c1e006" .. "6609c1" .. "66894c2448")
  local back = rel32(cv + #entry_stub + 5, PACK_NEXT)
  if not back then log("fl26cid16: entry cave out of range"); return end
  memory.write(cv, entry_stub .. "\233" .. back)
  local j = rel32(PACK + 5, cv)
  if not j then log("fl26cid16: entry jump out of range"); return end
  memory.write(PACK, "\233" .. j .. string.rep("\144", #PACK_BYTES / 2 - 5))

  -- regulation lookup by competition id: the high byte is at +0x910
  local reg_stub = bin("0fb65008" .. "0fb688" .. "10090000" .. "c1e108" .. "09ca" .. "8b4d77")
  local back2 = rel32(cv + 0x80 + #reg_stub + 5, REG_NEXT)
  if not back2 then log("fl26cid16: reg cave out of range"); return end
  memory.write(cv + 0x80, reg_stub .. "\233" .. back2)
  local j2 = rel32(REG + 5, cv + 0x80)
  if not j2 then log("fl26cid16: reg jump out of range"); return end
  memory.write(REG, "\233" .. j2 .. string.rep("\144", #REG_BYTES / 2 - 5))

  if memory.read(PACK, 1):byte(1) ~= 0xE9 or memory.read(REG, 1):byte(1) ~= 0xE9 then
    log("fl26cid16: a cave jump did not stick -- the byte reads stay")
    return
  end
  log("fl26cid16: competition ids above 255 are read from the tables (entry +0xb, regulation +0x910)")
end

return m

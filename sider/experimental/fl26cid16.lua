--[[
fl26cid16 -- competition ids above 255.

Why: the engine keeps a competition id in 16 bits (the live record at +0 is a word, the array has
600 holes, `0x14158df9d cmp word [rax], di`), but three reads in the Select Team census and the
EDIT set-up take it as a **byte**, and one of them packs it into a 16-bit sort key with the entry's
order.  See docs/research/competition-id-16-bit.md for the measurements and
docs/developers/fork/cids-16-bit.md for the recipe and the test.

Where the extra byte lives (measured 2026-11-03, 249 rows of the live world):

  Competition.bin +0x07   free (zero in every row).  NOT +0x20: the name field is 16 bytes from
                          +0x14, so +0x20..+0x23 are the tail of the name -- the earlier plan's
                          "free word at +0x20" would have overwritten it.
  CompetitionEntry.bin +0x0b   free (zero in every row)
  CompetitionRegulation.bin +0x910   free (zero in every row; the row is 0x930 bytes)

What this does, at boot, runtime only:

  in place (same instruction length, no jump moves):
    0x1414f1518  38 48 20  ->  39 48 20   the census map compares dwords
    0x1414f1534  3a 4b 20  ->  39 4b 20   the same, other side

  in a cave of its own:
    0x1414f1500 (7 bytes, to 0x1414f1507)  the competition id becomes
        byte[+5] | byte[+7] << 8, and the census key is stored as a dword
    0x1414f1609  the entry pack: the id becomes byte[+8] | byte[+0xb] << 8, and the sort key is
                 id << 6 | (order - 1) -- orders never reach 64, the longest shipped league is 48
    0x141eee27c  the regulation looked up by competition id: the high byte comes from +0x910

The data side is written by `tools/cid16_migrate.py`; a world where every id stays below 256
behaves exactly as before (all the high bytes are zero).  Ids above 1023 do not fit the entry sort
key.

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
  { 0x1414f1518, "384820", "394820", "the census map compares dwords" },
  { 0x1414f1534, "3a4b20", "394b20", "the same, other side" },
}

-- bisection switches: what to patch, to find which read a crash comes from
local ENABLE = { cmp = false, cid = false, pack = true, reg = true }

-- the id read and the census key, seven bytes wide (0x1414f1500..0x1414f1506)
local CID, CID_BYTES, CID_NEXT = 0x1414f1500, "0fb64f05884d68", 0x1414f1507
local PACK, PACK_BYTES, PACK_NEXT = 0x1414f1609, "0fb60f66ffc90fb647ff66c1e008660bc866894c2448", 0x1414f161f
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
  for _, p in ipairs({ { CID, CID_BYTES, "the competition id read" },
                       { PACK, PACK_BYTES, "the entry pack" },
                       { REG, REG_BYTES, "the regulation lookup" } }) do
    local got = memory.read(p[1], #p[2] / 2)
    if got == nil or hex(got) ~= p[2] then
      log(string.format("fl26cid16: %s at %#x is %s, expected %s -- nothing written",
                        p[3], p[1], tostring(got and hex(got)), p[2]))
      ok = false
    end
  end
  if not ok then return end

  for _, p in ipairs(INPLACE) do
    if ENABLE.cmp then memory.write(p[1], bin(p[3])) end
  end

  local cv = cave()
  if not cv then log("fl26cid16: no cave -- the three reads are left alone"); return end

  if ENABLE.cid then
  -- competition id: byte[+5] | byte[+7] << 8, then the census key as a dword
  local cid_stub = bin("0fb64f05" .. "0fb65707" .. "c1e208" .. "09d1" .. "894d68")
  local back0 = rel32(cv + #cid_stub + 5, CID_NEXT)
  if not back0 then log("fl26cid16: cid cave out of range"); return end
  memory.write(cv, cid_stub .. "\233" .. back0)
  local j0 = rel32(CID + 5, cv)
  if not j0 then log("fl26cid16: cid jump out of range"); return end
  memory.write(CID, "\233" .. j0 .. string.rep("\144", #CID_BYTES / 2 - 5))
  end

  if ENABLE.pack then
  -- entry pack: id = byte[+8] | byte[+0xb] << 8 ; key = id << 6 | (order - 1)
  -- only eax and ecx, like the bytes it replaces: edx is live in the caller's loop (the vector
  -- write pointer) and clobbering it crashed the team selector.  ah carries the high byte so the
  -- 16-bit shift drops its top two bits: (high<<8|low) << 6 = high<<14 | low<<6.
  local entry_stub = bin("0fb60f" .. "66ffc9" .. "0fb647ff" .. "8a6702" .. "66c1e006" ..
                         "6609c1" .. "66894c2448")
  local back = rel32(cv + 0x40 + #entry_stub + 5, PACK_NEXT)
  if not back then log("fl26cid16: entry cave out of range"); return end
  memory.write(cv + 0x40, entry_stub .. "\233" .. back)
  local j = rel32(PACK + 5, cv + 0x40)
  if not j then log("fl26cid16: entry jump out of range"); return end
  memory.write(PACK, "\233" .. j .. string.rep("\144", #PACK_BYTES / 2 - 5))
  end

  if ENABLE.reg then
  -- regulation lookup by competition id: the high byte is at +0x492 (the 32 zero bytes between
  -- the two name runs; +0x910 looked free but is inside the twentieth name slot)
  local reg_stub = bin("0fb65008" .. "0fb688" .. "92040000" .. "c1e108" .. "09ca" .. "8b4d77")
  local back2 = rel32(cv + 0x80 + #reg_stub + 5, REG_NEXT)
  if not back2 then log("fl26cid16: reg cave out of range"); return end
  memory.write(cv + 0x80, reg_stub .. "\233" .. back2)
  local j2 = rel32(REG + 5, cv + 0x80)
  if not j2 then log("fl26cid16: reg jump out of range"); return end
  memory.write(REG, "\233" .. j2 .. string.rep("\144", #REG_BYTES / 2 - 5))
  end

  local want = {}
  if ENABLE.cid then want[#want + 1] = { CID, "cid" } end
  if ENABLE.pack then want[#want + 1] = { PACK, "entry" } end
  if ENABLE.reg then want[#want + 1] = { REG, "regulation" } end
  for _, p in ipairs(want) do
    if memory.read(p[1], 1):byte(1) ~= 0xE9 then
      log("fl26cid16: the " .. p[2] .. " jump did not stick -- that read stays 8-bit")
      return
    end
  end
  log("fl26cid16: patched cid=" .. tostring(ENABLE.cid) .. " pack=" .. tostring(ENABLE.pack) ..
      " reg=" .. tostring(ENABLE.reg))
end

return m

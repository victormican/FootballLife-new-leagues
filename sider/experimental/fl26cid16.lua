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
    0x1414f7533  the club-list builder:  movzx r14d, byte [rax+0x08]  becomes the 16-bit id.
                 This is the one that keeps a league with cid > 255 out of Select Team -- the
                 builder asks 0x1414cb030 for the entry's slot and the byte id answers with the
                 slot of the competition that shares its low byte, so our slot is left with count
                 0 and the list walker skips it.

The data side is written by `tools/cid16_migrate.py`; a world where every id stays below 256
behaves exactly as before (all the high bytes are zero).  Ids above 1023 do not fit the entry sort
key.

The census map (2026-11-04).  The census of Select Team keeps a `std::map<byte, competition row*>`
and both of its loops look a competition up by the entry's id.  The container is the trap: the
insert (0x1414e36f0) de-duplicates on that single byte, so two competitions that share a low byte
can never both live in it -- widening the compares alone (what this file used to try) crashed at
25 s because the high byte was never written and the tree compared garbage.  So the map is left
alone and the look-ups are answered from a flat table of our own instead:

  0x1414f1d6a / 0x1414f1e5a   the key becomes byte[+8] | byte[+0xb] << 8 (same field as the pack)
  0x1414f1576                 the insert also stores  table[cid] = row
  0x1414f1d8b / 0x1414f1ea1   the two finds return  table[cid] - 0x28  (the caller reads +0x28)

The table is 1024 entries at cave+0x1000 and the id is masked to 0x3ff.  With this the twelve free
low bytes stop being a limit: a league or a cup with cid 256..1023 owns its club list.

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
local ENABLE = { cmp = false, cid = false, pack = true, reg = true, build = true, map = true }

-- the id read and the census key, seven bytes wide (0x1414f1500..0x1414f1506)
local CID, CID_BYTES, CID_NEXT = 0x1414f1500, "0fb64f05884d68", 0x1414f1507
local PACK, PACK_BYTES, PACK_NEXT = 0x1414f1609, "0fb60f66ffc90fb647ff66c1e008660bc866894c2448", 0x1414f161f
local REG,  REG_BYTES,  REG_NEXT  = 0x141eee27c, "0fb650088b4d77", 0x141eee283
local BUILD, BUILD_BYTES, BUILD_NEXT = 0x1414f7533, "440fb67008", 0x1414f7538

local function cave()
  ffi.cdef([[ void* VirtualAlloc(void*, unsigned long, unsigned long, unsigned long); ]])
  for _, pref in ipairs({ 0x15e100000, 0x15f100000, 0x161100000, 0x171100000 }) do
    local p = ffi.C.VirtualAlloc(ffi.cast("void*", pref), 0x8000, 0x3000, 0x40)
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
                       { REG, REG_BYTES, "the regulation lookup" },
                       { BUILD, BUILD_BYTES, "the club-list builder" },
                       { 0x1414f1d6a, "0fb64808884d68", "the census key (first loop)" },
                       { 0x1414f1e5a, "0fb64808884d68", "the census key (second loop)" },
                       { 0x1414f1d8b, "e800c1ffff", "the census lookup (first loop)" },
                       { 0x1414f1ea1, "e8eabfffff", "the census lookup (second loop)" },
                       { 0x1414f1576, "48897b2848", "the census insert" } }) do
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

  if ENABLE.build then
  -- club-list builder: the entry's id is a byte at +0x08; the high byte sits at +0x0b, the same
  -- field the entry pack reads.  rax is dead at the jump target (it is reloaded from [rbx] at
  -- 0x1414f7577) and ecx is left alone because 0x1414f7538 compares against it immediately.
  local build_stub = bin("440fb67008" .. "0fb6400b" .. "c1e008" .. "4109c6")
  local back3 = rel32(cv + 0x100 + #build_stub + 5, BUILD_NEXT)
  if not back3 then log("fl26cid16: builder cave out of range"); return end
  memory.write(cv + 0x100, build_stub .. "\233" .. back3)
  local j3 = rel32(BUILD + 5, cv + 0x100)
  if not j3 then log("fl26cid16: builder jump out of range"); return end
  memory.write(BUILD, "\233" .. j3)
  end

  if ENABLE.map then
  -- The census keeps `std::map<byte, row*>`, so two competitions that share a low byte cannot both
  -- live in it: the insert de-duplicates on that one byte inside 0x1414e36f0, which is why the
  -- earlier attempt (widening the compares) crashed at 25 s.  The map is left alone; look-ups are
  -- answered from a flat table of our own, and anything the table does not know (an entry whose cid
  -- has no competition row) goes to the original map find -- without that fallback the lookup
  -- answers 0 and 0x1414f7e80 dereferences it (crash at 0x1414f7ffc, 2026-11-04 11:45).
  --   key   0x1414f1d6a / 0x1414f1e5a : entry id = byte[+0x08] | byte[+0x0b] << 8 -> [rbp+0x68]
  --   find  0x1414f1d8b / 0x1414f1ea1 : iterator = table[id] - 0x28  (the caller reads +0x28)
  --   store 0x1414f1576               : table[row cid] = row, then the original two instructions
  local TBL = cv + 0x1000
  local function emit(at, prefix, back)
    local s = prefix
    local r = rel32(at + #s + 5, back)
    if not r then return nil end
    memory.write(at, s .. "\233" .. r)
    return true
  end
  local key_body = bin("0fb64808" .. "0fb6500b" .. "c1e208" .. "09d1" .. "66894d68")
  -- find: the iterator the caller expects is `&slot - 0x28`, because it does `r8 = it + 0x28`
  -- and then passes r8 on as a **pointer to the row pointer** (0x1414f7e80 reads `[r15]` and
  -- then `[rax+0x04]`).  Answering the row itself crashed at 0x1414f7ffc, twice.
  local function find_body(at, back)
    local head = bin("410fb600" .. "410fb64801" .. "c1e108" .. "09c8" .. "25ff030000")
    local lea_at = at + 19
    local ok_at, jmp_at = at + 37, at + 48
    local fall_at, call_at = at + 53, at + 57
    return head
      .. bin("488d0d") .. u32(TBL - (lea_at + 7))
      .. bin("48833cc100")
      .. bin("0f84") .. u32(fall_at - ok_at)
      .. bin("488d04c1" .. "4883e828" .. "488902")
      .. "\233" .. u32(back - (jmp_at + 5))
      .. bin("488d4da0")
      .. "\232" .. u32(0x1414ede90 - (call_at + 5))
      .. "\233" .. u32(back - (call_at + 10))
  end
  local function store_body(at)
    local pre = bin("48897b28" .. "0fb64705" .. "0fb64f07" .. "c1e108" .. "09c8" .. "25ff030000")
    local lea_at = at + #pre
    local tail = bin("48893cc1" .. "4883c724")
    return pre .. bin("488d0d") .. u32(TBL - (lea_at + 7)) .. tail
  end
  local KA, KB, FA, FB, ST = cv + 0x200, cv + 0x240, cv + 0x300, cv + 0x380, cv + 0x400
  local okmap = emit(KA, key_body, 0x1414f1d71)
             and emit(KB, key_body, 0x1414f1e61)
             and emit(FA, find_body(FA, 0x1414f1d90), 0x1414f1d90)
             and emit(FB, find_body(FB, 0x1414f1ea6), 0x1414f1ea6)
             and emit(ST, store_body(ST), 0x1414f157e)
  if not okmap then log("fl26cid16: map caves out of range"); return end
  local function hook(site, at, len)
    local j = rel32(site + 5, at)
    if not j then return false end
    memory.write(site, "\233" .. j .. string.rep("\144", len - 5))
    return true
  end
  if not (hook(0x1414f1d6a, KA, 7) and hook(0x1414f1e5a, KB, 7) and
          hook(0x1414f1d8b, FA, 5) and hook(0x1414f1ea1, FB, 5) and
          hook(0x1414f1576, ST, 5)) then
    log("fl26cid16: map jumps out of range")
    return
  end
  end

  local want = {}
  if ENABLE.cid then want[#want + 1] = { CID, "cid" } end
  if ENABLE.pack then want[#want + 1] = { PACK, "entry" } end
  if ENABLE.reg then want[#want + 1] = { REG, "regulation" } end
  if ENABLE.build then want[#want + 1] = { BUILD, "builder" } end
  if ENABLE.map then want[#want + 1] = { 0x1414f1d6a, "map" } end
  for _, p in ipairs(want) do
    if memory.read(p[1], 1):byte(1) ~= 0xE9 then
      log("fl26cid16: the " .. p[2] .. " jump did not stick -- that read stays 8-bit")
      return
    end
  end
  log("fl26cid16: patched cid=" .. tostring(ENABLE.cid) .. " pack=" .. tostring(ENABLE.pack) ..
      " reg=" .. tostring(ENABLE.reg) .. " build=" .. tostring(ENABLE.build) ..
      " map=" .. tostring(ENABLE.map))
end

return m

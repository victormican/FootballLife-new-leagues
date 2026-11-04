--[[
fl26diag -- temporary probe: what does the live regulation array hold for our leagues?

Press F9 while the game is running (title screen or Select Team) and read sider.log.

It prints, for the regulations of the eight leagues we cannot see:
  * the record id (word at +0x00)
  * the competition id the record carries at +0x80 (the field 0x1414cb030 matches against)
  * the slot that 0x1414cb030 answers for that id
and a summary of the ids >= 250 it finds in the array.

Nothing is written.
--]]

local m = {}

local BLOCKGLOBAL = 0x143705e10      -- 0x1414b6a60 returns [this]
local OFF_BLOCK = 0x48
local OFF_ARRAY = 0xc12e9c
local OFF_COUNT = 0xd0bcf4
local STRIDE = 0x314
local SLOTFN = 0x1414cb030

local function u16(s, i) return s:byte(i) + s:byte(i + 1) * 256 end
local function u32(s, i)
  return s:byte(i) + s:byte(i + 1) * 256 + s:byte(i + 2) * 65536 + s:byte(i + 3) * 16777216
end

local function dump()
  local g = memory.read(BLOCKGLOBAL, 8)
  if g == nil then log("fl26diag: cannot read the global") return end
  local gv = 0
  for i = 8, 1, -1 do gv = gv * 256 + g:byte(i) end
  if gv == 0 then log("fl26diag: the global is null") return end
  local bk = memory.read(gv + OFF_BLOCK, 8)
  local bv = 0
  for i = 8, 1, -1 do bv = bv * 256 + bk:byte(i) end
  if bv == 0 then log("fl26diag: the edit block is null") return end
  local n = u32(memory.read(bv + OFF_COUNT, 4), 1)
  log(string.format("fl26diag: edit block %#x, %d regulation records", bv, n))

  local fn = ffi.cast("int (*)(void*)", SLOTFN)
  local big = {}
  for i = 0, math.min(n, 1400) - 1 do
    local rec = bv + OFF_ARRAY + i * STRIDE
    local s = memory.read(rec, 0x84)
    if s ~= nil then
      local id, cid = u16(s, 1), u32(s, 0x81)
      local slot = -1
      if cid ~= 0xffffffff and cid ~= 0 then
        local box = ffi.new("uint32_t[1]", cid)
        slot = fn(box)
      end
      if (id >= 890 and id <= 910) or cid >= 250 then
        log(string.format("fl26diag: reg %4d cid %5d slot %3d", id, cid, slot))
      end
      if cid >= 250 then big[#big + 1] = string.format("%d:%d->%d", id, cid, slot) end
    end
  end
  log("fl26diag: ids with cid >= 250 -- " .. table.concat(big, " "))
end

function m.key_down(ctx, vkey)
  if vkey == 0x78 then dump() end            -- F9
end

local ticks = 0
local marks = { [2] = true, [8] = true, [32] = true, [128] = true, [512] = true, [2048] = true }
function m.make_key(ctx, filename)
  ticks = ticks + 1
  local name = tostring(filename or "?")
  if name:find("Competition") then
    log("fl26diag: tick " .. ticks .. " served " .. name)
    dump()
  elseif marks[ticks] then
    log("fl26diag: tick " .. ticks .. " (no competition file yet)")
    dump()
  end
  return nil
end

function m.init(ctx)
  if ffi == nil then log("fl26diag: no global ffi") return end
  ctx.register("livecpk_make_key", m.make_key)
  ctx.register("key_down", m.key_down)
  log("fl26diag: press F9 to dump the live regulation array")
end

return m

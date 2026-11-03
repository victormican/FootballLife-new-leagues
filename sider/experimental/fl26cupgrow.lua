--[[
fl26cupgrow -- more than 13 cups in Kick Off > Cup.

Measured 2026-11-03 (Frida, live menu): the cup list is a heap vector of 12-byte items
{cid, 0xffff, 0} with room for 13. The game fills 8 (its own cups) and fl26swiss appends the
world's cups until it is full, then drops the rest ("5 world cup(s) added, no room for the rest").
So only the first five `ccup` lines of a world are offered.

This wraps the menu's init in the vtable (0x142692d18, where fl26swiss put its handler) with a stub
that, before anything else, moves the list to a buffer of 64 items: begin at +0x90, end +0x98,
capacity +0xa0. With room, fl26swiss appends every cup of the world by itself.

The buffer comes from the game's own allocator (0x140227930), so the menu's destructor frees it
with the same heap. Nothing is written unless the vtable holds a pointer and the stub page is
within reach. Needs luajit.ext.enabled = 1 (global ffi).
--]]

local m = {}

local VT      = 0x142692d18      -- the slot fl26swiss patched; holds its handler at run time
local ALLOC   = 0x140227930      -- the game's allocator, size in rcx, pointer in rax
local WANT    = 64               -- items we make room for (12 bytes each)

-- the stub (190 bytes), with the previous handler patched in at +0xa8
local STUB = "535657415441554883ec28488bd9524150415148" ..
             "8b8398000000482b83900000004885c07478488b93a0000000482b9390000000" ..
             "4881fa000300007361b90003000048b83079224001000000ffd04885c0744b4c" ..
             "8be04c8bab90000000488b8b980000004c29e94c89ee4889c7f3a4488b939800" ..
             "0000482b93900000004c89a390000000498d041448898398000000498d842400" ..
             "030000488983a0000000415941585a4889d948b8PREVIOUSffd04883c428415d41" ..
             "5c5f5e5bc3"

local function bin(h) return (h:gsub("%x%x", function(b) return string.char(tonumber(b, 16)) end)) end
local function hex64(v)
  local t = {}
  for i = 0, 7 do t[#t + 1] = string.format("%02x", math.floor(v / 2 ^ (8 * i)) % 256) end
  return table.concat(t)
end
local function u64(v)
  local t = {}
  for i = 0, 7 do t[#t + 1] = string.char(math.floor(v / 2 ^ (8 * i)) % 256) end
  return table.concat(t)
end

local installed = false

function m.init(ctx)
  if ffi == nil then log("fl26cupgrow: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  ffi.cdef([[ void* VirtualAlloc(void*, unsigned long, unsigned long, unsigned long);
              void* LoadLibraryA(const char*);
              void* GetProcAddress(void*, const char*); ]])
  local prev = tonumber(ffi.cast("uint64_t*", VT)[0])
  if not prev or prev == 0 then log("fl26cupgrow: the vtable slot is empty -- nothing written"); return end
  local h = ffi.C.LoadLibraryA("ucrtbase.dll")
  local pm = h ~= nil and ffi.C.GetProcAddress(h, "malloc") or nil
  if pm == nil then log("fl26cupgrow: no ucrtbase malloc -- nothing written"); return end
  local malloc_addr = tonumber(ffi.cast("uint64_t", pm))
  local page = nil
  for _, pref in ipairs({ 0x15e100000, 0x15f100000, 0x161100000, 0x171100000 }) do
    page = ffi.C.VirtualAlloc(ffi.cast("void*", pref), 0x1000, 0x3000, 0x40)
    if page ~= nil then break end
  end
  if page == nil then log("fl26cupgrow: no stub page"); return end
  local code = tonumber(ffi.cast("uint64_t", page)) + 0x100
  local raw = bin((STUB:gsub("PREVIOUS", hex64(prev))))
  -- the allocator immediate sits at byte 0x44: patch it with ucrtbase's malloc
  memory.write(code, raw:sub(1, 0x44) .. u64(malloc_addr) .. raw:sub(0x4d))
  -- point the vtable slot at the stub
  memory.write(VT, u64(code))
  local back = tonumber(ffi.cast("uint64_t*", VT)[0])
  if back ~= code then
    log(string.format("fl26cupgrow: the vtable write did not stick (%#x, wanted %#x)", back or 0, code))
    return
  end
  installed = true
  log(string.format("fl26cupgrow: menu init wrapped (%#x -> %#x), room for %d cups", prev, code, WANT))
end

return m

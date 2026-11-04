--[[
fl26cupgrow -- que quepan mas de 13 copas en Kick Off > Cup.

Medido el 2026-11-03: la lista del menu es un vector de items de 12 bytes {cid, 0xffff, 0} con
capacidad 13. Ocho los pone el juego y fl26swiss añade los del mundo hasta llenarla. Su ensanche
propio (VirtualAlloc) solo actua si el array vive dentro del objeto; con el vector en el heap lo
deja quieto, y eso cambia de un arranque a otro.

Esto quita la loteria: al arrancar se piden 16 buffers de 768 bytes (64 items) al CRT del juego y
se guardan en un anillo. El constructor del menu (0x140b1c6f0) recibe un stub que, si la lista esta
vacia, la pone sobre uno de esos buffers. El propio juego y fl26swiss llenan la lista despues con
sitio de sobra, y el destructor la libera con su mismo heap.

Nada se escribe si los buffers no se consiguen. Necesita luajit.ext.enabled = 1 (ffi global).
--]]

local m = {}

local CTOR  = 0x140b1c6f0
local CTOR_OLD = "48894c2408"     -- mov [rsp+8], rcx
local WANT  = 64
local RING  = 16

local STUB = "48894c240848890d000000004883b990000000000f854b000000" ..
             "48b800000000000000004c8b90800000004983fa100f8330000000" ..
             "4e8b1cd04d85db0f842300000048ff80800000004c8999900000004c" ..
             "899998000000498d8300030000488981a0000000e900000000"

local function bin(h) return (h:gsub("%x%x", function(b) return string.char(tonumber(b, 16)) end)) end
local function u32(v)
  v = v % 0x100000000
  return string.char(v % 256, math.floor(v / 256) % 256,
                     math.floor(v / 65536) % 256, math.floor(v / 16777216) % 256)
end
local function u64(v)
  local t = {}
  for i = 0, 7 do t[#t + 1] = string.char(math.floor(v / 2 ^ (8 * i)) % 256) end
  return table.concat(t)
end

function m.init(ctx)
  if ffi == nil then log("fl26cupgrow: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  ffi.cdef([[ void* VirtualAlloc(void*, unsigned long, unsigned long, unsigned long);
              void* LoadLibraryA(const char*);
              void* GetProcAddress(void*, const char*); ]])
  local got = memory.read(CTOR, #CTOR_OLD / 2)
  if got == nil or got:gsub(".", function(c) return string.format("%02x", c:byte()) end) ~= CTOR_OLD then
    log("fl26cupgrow: the menu constructor is not the expected code -- nothing written"); return
  end
  -- el asignador del propio ejecutable (0x140227930 -> 0x1403fb2e0, tamaño en rcx):
  -- es el que despues libera el destructor del menu, asi que el bloque tiene que venir de ahi
  local malloc = ffi.cast("void* (*)(unsigned long)", 0x140227930)

  local page = nil
  for _, pref in ipairs({ 0x15e100000, 0x15f100000, 0x161100000, 0x171100000 }) do
    page = ffi.C.VirtualAlloc(ffi.cast("void*", pref), 0x2000, 0x3000, 0x40)
    if page ~= nil then break end
  end
  if page == nil then log("fl26cupgrow: no page"); return end
  local base = tonumber(ffi.cast("uint64_t", page))
  local selfptr, ring, idx, code = base, base + 0x100, base + 0x180, base + 0x200

  local n = 0
  for i = 0, RING - 1 do
    local b = malloc(WANT * 12)
    if b == nil then break end
    ffi.cast("uint64_t*", ring + i * 8)[0] = ffi.cast("uint64_t", b)
    n = n + 1
  end
  if n < 2 then log(string.format("fl26cupgrow: only %d buffer(s)", n)); return end
  ffi.cast("uint64_t*", idx)[0] = 0

  local s = bin(STUB)
  s = s:sub(1, 8) .. u32(selfptr - (code + 12)) .. s:sub(13)
  s = s:sub(1, 28) .. u64(ring) .. s:sub(37)
  s = s:sub(1, 102) .. u32((CTOR + 5) - (code + 0x65 + 5)) .. s:sub(107)
  memory.write(code, s)
  local j = u32((code) - (CTOR + 5))
  memory.write(CTOR, "\233" .. j)

  if memory.read(CTOR, 1):byte(1) ~= 0xE9 then
    log("fl26cupgrow: the jump did not stick"); return
  end
  log(string.format("fl26cupgrow: %d buffers of %d items, constructor hooked (stub %#x)", n, WANT, code))
end

return m

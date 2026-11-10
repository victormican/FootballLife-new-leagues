--[[
fl26zcupdates -- da a la regulacion 200 el calendario de copa en el stub de fechas.

fl26caps instala el stub de fechas (tools/datecave.py) en la pagina 0x163000000: 119 bytes de
codigo y una tabla de 256 bytes, un byte por id de regulacion (0xff = sin calendario). El stub
solo mira la tabla para ids 1..255; los ids 256+ caen en el calendario de LIGA. Nuestra copa vivia
en la 317: no podia llevar fechas de copa nunca.

Ahora la copa es la regulacion 200 (fila de CompetitionRegulation con cid 131) y este modulo pone
la tabla[200] a 0x10: bit de copa, desplazamiento 0 -> los diez dias del cuadro de 16.

Carga despues de fl26caps (nombre con z) y no toca nada mas.
--]]

local m = {}

local CAVE = 0x163000000
local TABLE_OFF = 119      -- bytes de codigo del stub antes de la tabla
local ID = 200
local CUP_BIT = 0x10

function m.init(ctx)
  local addr = CAVE + TABLE_OFF + ID
  local got = memory.read(addr, 1)
  if got == nil then
    log("fl26zcupdates: la pagina del stub de fechas no esta (fl26caps no cargo?)")
    return
  end
  local before = got:byte(1)
  if before == CUP_BIT then
    log("fl26zcupdates: reg 200 ya tiene el calendario de copa")
    return
  end
  memory.write(addr, string.char(CUP_BIT))
  local after = memory.read(addr, 1):byte(1)
  log(string.format("fl26zcupdates: reg 200, byte de tabla %02x -> %02x (calendario de copa)",
                    before, after))
end

return m

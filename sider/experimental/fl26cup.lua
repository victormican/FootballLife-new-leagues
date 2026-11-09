--[[
fl26cup -- the cup list, and nothing else.

Loader of fl26cup.dll: a minimal DLL that only appends the competitions named by `showcup` in
modules\fl26world.txt to Kick Off > Cup.  It exists to test, with no other mod in the way,
whether the game builds the phase record and draws a competition that is not one of its ten.

Install: copy to <game>\SiderAddons\modules\fl26cup.lua and add to sider.ini:
    lua.module = "fl26cup.lua"
Requires luajit.ext.enabled = 1.
--]]

local m = {}

local dll_log, logbuf

local function drain()
  if not dll_log then return end
  local n = tonumber(dll_log(logbuf, 4096))
  if n > 0 then
    for line in ffi.string(logbuf, n):gmatch("[^\n]+") do log("fl26cup: " .. line) end
  end
end

local function load_dll(path)
  local n = ffi.C.fl26cup_MultiByteToWideChar(65001, 0, path, -1, nil, 0)
  if n > 0 then
    local w = ffi.new("uint16_t[?]", n)
    ffi.C.fl26cup_MultiByteToWideChar(65001, 0, path, -1, w, n)
    local h = ffi.C.fl26cup_LoadLibraryW(w)
    if h ~= nil then return h end
  end
  return ffi.C.LoadLibraryA(path)
end

function m.init(ctx)
  if ffi == nil then log("fl26cup: global ffi is nil -- set luajit.ext.enabled = 1"); return end
  ffi.cdef([[
    void*    LoadLibraryA(const char*);
    void*    fl26cup_LoadLibraryW(const uint16_t*) __asm__("LoadLibraryW");
    int      fl26cup_MultiByteToWideChar(unsigned int, unsigned long, const char*, int, uint16_t*, int) __asm__("MultiByteToWideChar");
    void*    GetProcAddress(void*, const char*);
    typedef int (*fl26cup_ids_t)(const uint16_t*, int);
    typedef int (*fl26cup_log_t)(char*, int);
  ]])

  local sep = string.char(92)
  local root = ctx.sider_dir:gsub("[/" .. sep .. "]+$", "")
  local dllpath = root .. sep .. "modules" .. sep .. "fl26cup.dll"
  local h = load_dll(dllpath)
  if h == nil then log("fl26cup: LoadLibrary failed: " .. dllpath); return end
  local pc = ffi.C.GetProcAddress(h, "fl26_swiss_cup_cids")
  local pl = ffi.C.GetProcAddress(h, "fl26_swiss_log")
  if pc == nil or pl == nil then log("fl26cup: GetProcAddress failed"); return end
  local ids = ffi.cast("fl26cup_ids_t", pc)
  dll_log = ffi.cast("fl26cup_log_t", pl)
  logbuf = ffi.new("char[4096]")

  local f = io.open(root .. sep .. "modules" .. sep .. "fl26world.txt", "r")
  if f == nil then log("fl26cup: no fl26world.txt"); return end
  local list = {}
  for line in f:lines() do
    local sc = line:match("^%s*showcup%s+(%d+)")
    if sc then list[#list + 1] = tonumber(sc) end
  end
  f:close()
  if #list == 0 then log("fl26cup: the world file has no showcup line"); return end
  local buf = ffi.new("uint16_t[?]", #list)
  for i, v in ipairs(list) do buf[i - 1] = v end
  local n = tonumber(ids(buf, #list))
  log(string.format("fl26cup: %d showcup id(s), %d exposed", #list, n))
  drain()
end

function m.make_key(ctx, filename)
  drain()
  return nil
end

function m.key_down(ctx, vkey)
  drain()
end

return m

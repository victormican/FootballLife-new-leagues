import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
anchor = "static int regcid_fix(void)"
helper = """/* log propio a fichero: el buffer de Sider se drena cada 32 ficheros y se come lineas */
static void rlog(const char* fmt, ...)
{
  FILE* f = fopen("C:/Users/viarm/AppData/Local/Temp/opencode/regcid.txt", "a");
  if (!f) return;
  va_list ap; va_start(ap, fmt);
  vfprintf(f, fmt, ap);
  va_end(ap);
  fputc('\\n', f);
  fclose(f);
}

static int regcid_fix(void)"""
assert anchor in s
s = s.replace(anchor, helper, 1)
s = s.replace('logf("fl26swiss: regcid -- name scan: %llu bytes, %d found", sc, found);',
              'rlog("name scan: %llu bytes, %d found", sc, found); logf("fl26swiss: regcid -- name scan: %llu bytes, %d found", sc, found);')
s = s.replace('logf("fl26swiss: regcid -- name at %p; rec id=%u cid80=%u name=%s", (void*)r,',
              'rlog("name at %p id=%u cid80=%u %s", (void*)r, (unsigned)*(uint16_t*)(r-0x14), *(uint32_t*)(r-0x14+0x80), (char*)r);\n          logf("fl26swiss: regcid -- name at %p; rec id=%u cid80=%u name=%s", (void*)r,')
s = s.replace('logf("fl26swiss: regcid -- ctx=%p blk=%p n=%u", ctx, (void*)blk, n);',
              'rlog("ctx=%p blk=%p n=%u", ctx, (void*)blk, n); logf("fl26swiss: regcid -- ctx=%p blk=%p n=%u", ctx, (void*)blk, n);')
s = s.replace('logf("fl26swiss: regcid -- array starts at %p (offset %#llx in the block)",',
              'rlog("array starts %p off %#llx", (void*)st, (unsigned long long)(st - blk));\n      logf("fl26swiss: regcid -- array starts at %p (offset %#llx in the block)",')
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("rlog anadido")

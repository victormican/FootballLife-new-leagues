import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """  uint32_t zero = 0;
  void *ctx = ((void* (*)(void*))(uintptr_t)(g_base + PHDATA_RVA))(&zero);
  if (!ctx) return -1;
  unsigned char* blk = *(unsigned char**)((unsigned char*)ctx + 0x48);
  if (!blk) return -1;
  uint32_t n = *(uint32_t*)(blk + 0xd0bcf4);
  if (n == 0 || n > 1200) return -1;"""
new = """  uint32_t probe = 27;   /* un cid que resuelve seguro: la funcion depende del que se le pasa */
  void *ctx = ((void* (*)(void*))(uintptr_t)(g_base + PHDATA_RVA))(&probe);
  unsigned char* blk = ctx ? *(unsigned char**)((unsigned char*)ctx + 0x48) : 0;
  uint32_t n = blk ? *(uint32_t*)(blk + 0xd0bcf4) : 0;
  logf("fl26swiss: regcid -- ctx=%p blk=%p n=%u", ctx, (void*)blk, n);
  if (!ctx || !blk || n == 0 || n > 1200) return -1;"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("cid 27 + log siempre")

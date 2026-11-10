import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """  void *ctx = ((void* (*)(void))(uintptr_t)(g_base + PHDATA_RVA))();"""
new = """  /* phkind la llama con rcx = puntero al cid; sin argumento el registro queda con basura y
     revienta (0x140025963, 2026-11-04).  Se le pasa un puntero a un cero. */
  uint32_t zero = 0;
  void *ctx = ((void* (*)(void*))(uintptr_t)(g_base + PHDATA_RVA))(&zero);"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("llamada con argumento")

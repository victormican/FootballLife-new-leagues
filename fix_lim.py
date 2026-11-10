import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """  logf("fl26swiss: regcid -- ctx=%p blk=%p n=%u", ctx, (void*)blk, n);
  if (!ctx || !blk || n == 0 || n > 1200) return -1;
  int fixed = 0, seen = 0;
  for (uint32_t i = 0; i < n; i++) {"""
new = """  logf("fl26swiss: regcid -- ctx=%p blk=%p n=%u", ctx, (void*)blk, n);
  if (!ctx || !blk || n == 0) return -1;
  /* la cuenta puede ser 65535 (phkind tambien la ve asi): mas alla de 1200 el registro es el
     centinela de +0xd0b77c, que no es de nadie.  El tope real lo pone fl26caps (300 -> 1200). */
  uint32_t lim = n > 1200 ? 1200 : n;
  int fixed = 0, seen = 0;
  for (uint32_t i = 0; i < lim; i++) {"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace('logf("fl26swiss: regcid -- %u regulations, %d ours seen, %d got the full cid", n, seen, fixed);',
              'logf("fl26swiss: regcid -- %u regulations (scanning %u), %d ours seen, %d got the full cid", n, lim, seen, fixed);')
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("tope corregido")

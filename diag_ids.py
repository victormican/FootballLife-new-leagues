import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """  int fixed = 0, seen = 0;
  for (uint32_t i = 0; i < lim; i++) {"""
new = """  int fixed = 0, seen = 0, nz = 0;
  char ids[160]; int il = 0;
  for (uint32_t i = 0; i < lim; i++) {
    uint16_t pid = *(uint16_t*)(blk + 0xc12e9c + (size_t)i * 0x314);
    if (pid) { nz++; if (il < 140) il += snprintf(ids + il, sizeof ids - il, " %u", (unsigned)pid); }
  }
  logf("fl26swiss: regcid -- %d record(s) with an id, first ones:%s", nz, ids);
  for (uint32_t i = 0; i < lim; i++) {"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("diagnostico de ids")

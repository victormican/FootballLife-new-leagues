import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """    int shows = 0;
    for (unsigned char* q = lo; q < hi; q++) {
      if (*(uint32_t*)(q + 0x80) != 2) continue;
      uint16_t id = *(uint16_t*)q;
      if (id == 0 || id > 9000) continue;
      logf("fl26swiss: regcid -- cid2 row at %p (offset %#llx): id=%u kind=%u",
           (void*)q, (unsigned long long)(q - blk), (unsigned)id, *(uint32_t*)(q + 0x84));
      if (!hit) hit = q;
      if (++shows >= 4) break;
    }
    logf("fl26swiss: regcid -- record cid2 at %p", (void*)hit);"""
new = """    int shows = 0;
    /* sondeo a lo bruto: donde aparezca 96 (Gold Cup) como dword en +0x80, 0x84 o 0x7c,
       registrar el entorno para ver donde esta de verdad el cid dentro del registro */
    for (unsigned char* q = lo; q < hi && shows < 6; q++) {
      int rel = -1;
      if (*(uint32_t*)(q + 0x80) == 96) rel = 0x80;
      else if (*(uint32_t*)(q + 0x84) == 96) rel = 0x84;
      else if (*(uint32_t*)(q + 0x7c) == 96) rel = 0x7c;
      if (rel < 0) continue;
      logf("fl26swiss: regcid -- cid96 at %p rel %#x off %#llx: w0=%u w2=%u d78=%u d88=%u",
           (void*)q, rel, (unsigned long long)(q - blk),
           (unsigned)*(uint16_t*)q, (unsigned)*(uint16_t*)(q + 2),
           *(uint32_t*)(q + 0x78), *(uint32_t*)(q + 0x88));
      if (!hit) hit = q - (rel - 0x80);
      shows++;
    }
    logf("fl26swiss: regcid -- record cid96 at %p", (void*)hit);"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("sondeo cid96")

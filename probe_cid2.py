import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """    unsigned char* hit = 0;
    for (unsigned char* q = lo; q < hi; q++) {
      if (*(uint16_t*)q != 34) continue;
      if (*(uint32_t*)(q + 0x80) != 27) continue;
      hit = q; break;
    }
    logf("fl26swiss: regcid -- record 34/27 at %p", (void*)hit);"""
new = """    unsigned char* hit = 0;
    /* se busca la fila del Champions (cid 2) sin suponer la base: cualquier punto donde el
       dword de +0x80 valga 2 y el word de +0x00 sea un id de regulacion plausible */
    int shows = 0;
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
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("sondeo por cid 2")

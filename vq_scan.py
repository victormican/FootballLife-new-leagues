import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """    int shows = 0;
    /* sondeo a lo bruto: donde aparezca 96 (Gold Cup) como dword en +0x80, 0x84 o 0x7c,
       registrar el entorno para ver donde esta de verdad el cid dentro del registro */
    for (unsigned char* q = lo; q < hi && shows < 6; q++) {"""
new = """    int shows = 0;
    /* Barrido solo por memoria comprometida y legible: leer a lo bruto cerraba el juego
       (0x140025c03, 2026-11-04). */
    unsigned char* q = lo;
    unsigned long long scanned = 0;
    while (q < hi && shows < 6 && scanned < 0x2000000ULL) {
      MEMORY_BASIC_INFORMATION mbi;
      if (VirtualQuery(q, &mbi, sizeof mbi) == 0) break;
      unsigned char* rbase = (unsigned char*)mbi.BaseAddress;
      unsigned char* rend = rbase + mbi.RegionSize;
      int readable = (mbi.State == MEM_COMMIT)
                  && !(mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD));
      if (!readable) { q = rend; continue; }
      if (rbase < lo) rbase = lo;
      if (rend > hi) rend = hi;
      for (unsigned char* r = rbase; r < rend && shows < 6; r++) {
        scanned++;
        if (*(uint32_t*)(r + 0x80) == 96) { shows++; logf("fl26swiss: regcid -- cid96 at %p rel 0x80 off %#llx id=%u kind=%u", (void*)r, (unsigned long long)(r - blk), (unsigned)*(uint16_t*)r, *(uint32_t*)(r + 0x84)); if (!hit) hit = r; continue; }
        if (*(uint32_t*)(r + 0x84) == 96) { shows++; logf("fl26swiss: regcid -- cid96 at %p rel 0x84 off %#llx id=%u", (void*)r, (unsigned long long)(r - blk), (unsigned)*(uint16_t*)r); if (!hit) hit = r - 4; continue; }
        if (*(uint32_t*)(r + 0x7c) == 96) { shows++; logf("fl26swiss: regcid -- cid96 at %p rel 0x7c off %#llx id=%u", (void*)r, (unsigned long long)(r - blk), (unsigned)*(uint16_t*)r); if (!hit) hit = r + 4; continue; }
      }
      q = rend;
    }
    logf("fl26swiss: regcid -- scanned %llu bytes, %d hit(s)", scanned, shows);
    for (unsigned char* qq = lo; 0 && qq < hi; qq++) {"""
assert old in s
s = s.replace(old, new, 1)
# anular el bucle viejo (queda tras el nuevo con 0 && ...)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("barrido con VirtualQuery")

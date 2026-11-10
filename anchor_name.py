import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """    int shows = 0;
    /* Barrido solo por memoria comprometida y legible"""
new = """    int shows = 0;
    /* Ancla por nombre: "Kosovo Cup" solo existe en nuestra regulacion 918.  Si aparece, el
       registro empieza 0x14 antes (ahi esta el nombre en las tablas), y en +0x00 su id. */
    {
      const char* needle = "Kosovo Cup";
      size_t nl = 10;
      unsigned char* q = lo;
      unsigned long long sc = 0;
      int found = 0;
      while (q < hi && found < 3 && sc < 0x2000000ULL) {
        MEMORY_BASIC_INFORMATION mbi;
        if (VirtualQuery(q, &mbi, sizeof mbi) == 0) break;
        unsigned char* rb = (unsigned char*)mbi.BaseAddress;
        unsigned char* re = rb + mbi.RegionSize;
        int rd = (mbi.State == MEM_COMMIT) && !(mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD));
        if (!rd) { q = re; continue; }
        if (rb < lo) rb = lo;
        if (re > hi) re = hi;
        for (unsigned char* r = rb; r + nl < re && found < 3; r++) {
          sc++;
          if (memcmp(r, needle, nl) != 0) continue;
          unsigned char* rec0 = r - 0x14;
          logf("fl26swiss: regcid -- name at %p; rec id=%u cid80=%u name=%s", (void*)r,
               (unsigned)*(uint16_t*)rec0, *(uint32_t*)(rec0 + 0x80), (char*)r);
          found++;
        }
        q = re;
      }
      logf("fl26swiss: regcid -- name scan: %llu bytes, %d found", sc, found);
    }
    /* Barrido solo por memoria comprometida y legible"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("ancla por nombre")

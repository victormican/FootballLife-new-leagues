import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """  int fixed = 0, seen = 0, nz = 0;"""
new = """  /* El bloque de arriba no es el array (sus ids son basura).  Se localiza el array por un
     registro conocido: el del Mundial (id de regulacion 34, cid 27) y se camina hacia atras
     hasta el primer registro.  Despues se aplica el mapa sobre esa base. */
  {
    unsigned char* lo = blk;
    unsigned char* hi = blk + 0xE00000;
    unsigned char* hit = 0;
    for (unsigned char* q = lo; q < hi; q++) {
      if (*(uint16_t*)q != 34) continue;
      if (*(uint32_t*)(q + 0x80) != 27) continue;
      hit = q; break;
    }
    logf("fl26swiss: regcid -- record 34/27 at %p", (void*)hit);
    if (hit) {
      unsigned char* st = hit;
      while (st - 0x314 >= lo && *(uint16_t*)(st - 0x314) > 0 && *(uint16_t*)(st - 0x314) < 9000)
        st -= 0x314;
      logf("fl26swiss: regcid -- array starts at %p (offset %#llx in the block)",
           (void*)st, (unsigned long long)(st - blk));
      int fx = 0, sn = 0;
      for (int i = 0; i < 1200; i++) {
        unsigned char* rec = st + (size_t)i * 0x314;
        uint16_t rid = *(uint16_t*)rec;
        if (rid == 0 || rid >= 9000) break;
        for (int k = 0; k < g_nregcid; k++) {
          if (g_regcid[2 * k] != rid) continue;
          sn++;
          uint32_t want = g_regcid[2 * k + 1];
          if (*(uint32_t*)(rec + 0x80) != want) { *(uint32_t*)(rec + 0x80) = want; fx++; }
          break;
        }
      }
      logf("fl26swiss: regcid -- array: %d ours seen, %d got the full cid", sn, fx);
      if (sn > 0) return fx;
    }
  }
  int fixed = 0, seen = 0, nz = 0;"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("escaneo del array anadido")

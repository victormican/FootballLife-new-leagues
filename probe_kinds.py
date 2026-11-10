import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
old = """        uint32_t k2 = cid;
        uint16_t g2 = (uint16_t)((phkind_fn)(uintptr_t)(g_base + PHKIND_RVA))(&k2, 2);
        unsigned char* r2 = g2 != 0xffff ? find_rec(g2) : 0;"""
new = """        uint32_t k2 = cid;
        uint16_t g2 = 0xffff;
        unsigned char* r2 = 0;
        char kinds[64]; int kl = 0;
        for (int kk = 1; kk <= 6; kk++) {
          uint16_t gk = (uint16_t)((phkind_fn)(uintptr_t)(g_base + PHKIND_RVA))(&k2, kk);
          kl += snprintf(kinds + kl, sizeof kinds - kl, " k%d=%u", kk, (unsigned)gk);
          if (kk == 2) g2 = gk;
        }
        r2 = g2 != 0xffff ? find_rec(g2) : 0;"""
assert old in s
s = s.replace(old, new, 1)
old2 = """        logf("fl26swiss: CUPRES cid=%u group=%u rec=%p name=%s", cid, (unsigned)g2, (void*)r2, r2 ? nm2 : "(none)");"""
new2 = """        logf("fl26swiss: CUPRES cid=%u group=%u rec=%p name=%s vols:%s", cid, (unsigned)g2, (void*)r2, r2 ? nm2 : "(none)", kinds);"""
assert old2 in s
s = s.replace(old2, new2, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("sonda de kinds lista")

import io
p = "tools/native/fl26swiss.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()
anchor = "static uint16_t g_cupcid[MAX_CCUP];\nstatic int g_ncupcid = 0;"
assert anchor in s
add = anchor + """

/* el cid completo en el registro vivo de regulacion (+0x80).  phkind (0x14150af30) compara ese
   dword con el cid, y el registro solo lleva el byte bajo: un cid >= 256 no se encuentra (menu de
   copas: nombre de otra competicion y sin tamano de sorteo).  El contexto hay que pedirlo desde el
   hilo del juego, por eso esto vive aqui y no en Lua: llamar 0x1414b6a60 desde el hilo de Sider da
   otro contexto y alli la cuenta sale 0xffff (medido 2026-11-04). */
#define PHDATA_RVA 0x14b6a60
#define REG_MAX    2048
static uint32_t g_regcid[REG_MAX * 2];
static int g_nregcid = 0;

__declspec(dllexport) int fl26_swiss_regcid(const uint32_t* v, int n)
{
  g_nregcid = 0;
  for (int i = 0; i + 1 < n && g_nregcid < REG_MAX; i += 2) {
    g_regcid[2 * g_nregcid] = v[i];
    g_regcid[2 * g_nregcid + 1] = v[i + 1];
    g_nregcid++;
  }
  return g_nregcid;
}

static int regcid_fix(void)
{
  if (g_nregcid == 0) return -1;
  void *ctx = ((void* (*)(void))(uintptr_t)(g_base + PHDATA_RVA))();
  if (!ctx) return -1;
  unsigned char* blk = *(unsigned char**)((unsigned char*)ctx + 0x48);
  if (!blk) return -1;
  uint32_t n = *(uint32_t*)(blk + 0xd0bcf4);
  if (n == 0 || n > 1200) return -1;
  int fixed = 0, seen = 0;
  for (uint32_t i = 0; i < n; i++) {
    unsigned char* rec = blk + 0xc12e9c + (size_t)i * 0x314;
    uint16_t rid = *(uint16_t*)rec;
    for (int k = 0; k < g_nregcid; k++) {
      if (g_regcid[2 * k] != rid) continue;
      seen++;
      uint32_t want = g_regcid[2 * k + 1];
      if (*(uint32_t*)(rec + 0x80) != want) {
        *(uint32_t*)(rec + 0x80) = want;
        fixed++;
      }
      break;
    }
  }
  logf("fl26swiss: regcid -- %u regulations, %d ours seen, %d got the full cid", n, seen, fixed);
  return fixed;
}"""
s = s.replace(anchor, add, 1)
# llamarlo al principio del handler de copas (hilo del juego)
old = "  unsigned char** pb = (unsigned char**)(self + 0x90);"
new = "  regcid_fix();\n  unsigned char** pb = (unsigned char**)(self + 0x90);"
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8", errors="surrogateescape", newline="\n").write(s)
print("regcid_fix anadido al DLL")

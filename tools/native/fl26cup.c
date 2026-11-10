/* fl26cup -- the cup list, and nothing else.
 *
 * The full fl26swiss.dll hooks the schedule, the draw, the calendars and a dozen menus.  Any
 * cup of the game that is opened with it loaded ends in the same crash, so this DLL exists to
 * answer one question with no other variable: if the only thing we do is append our
 * competition to Kick Off > Cup, does the game build its phase record and draw it?
 *
 * It replaces the list constructor of MenuModeCupSelect (vtable slot 0x142692c40 + 0xd8) and
 * appends one 12-byte item per competition id given by fl26_swiss_cup_cids(), copying the
 * first item as the template the menu uses for the name and logo.  The vector has room for 13
 * items and the game fills 10, so nothing is allocated and nothing outlives the menu.  The
 * original constructor runs afterwards, exactly as before.
 *
 * Build:
 *   zig cc -shared -target x86_64-windows-gnu -O2 -s -o fl26cup.dll fl26cup.c -lkernel32
 */
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

#define CUPSEL_VT_RVA   0x2692d18   /* 0x142692c40 + 0xd8 */
#define CUPSEL_INIT_RVA 0xb1c990
#define DATE_RVA        0x157f810
#define DATE_SITE_RVA   0x157f81e   /* movzx edi, cx */
#define DATE_RESUME_RVA 0x157f826   /* after the owner() call */
#define OWNER_RVA       0x14b6a60

static uint64_t g_base;
static char g_log_path[MAX_PATH];
static char g_log[1 << 16];
static int g_log_len;
static int (*g_orig)(void*, uint64_t, uint64_t, uint64_t);
static uint16_t g_cid[16];
static int g_ncid;

static void lf(const char* fmt, ...)
{
  char line[256];
  va_list ap;
  int n;
  va_start(ap, fmt);
  n = vsnprintf(line, sizeof line, fmt, ap);
  va_end(ap);
  if (n <= 0) return;
  if (n >= (int)sizeof line) n = sizeof line - 1;
  if (g_log_len + n + 1 >= (int)sizeof g_log) return;
  memcpy(g_log + g_log_len, line, n);
  g_log_len += n;
  g_log[g_log_len++] = '\n';
}

static void lfile(const char* fmt, ...)
{
  char line[512];
  va_list ap;
  int n;
  HANDLE f;
  DWORD wrote = 0;
  va_start(ap, fmt);
  n = vsnprintf(line, sizeof line, fmt, ap);
  va_end(ap);
  if (n <= 0 || !g_log_path[0]) return;
  if (n >= (int)sizeof line) n = sizeof line - 1;
  line[n++] = '\n';
  f = CreateFileA(g_log_path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                  NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
  if (f == INVALID_HANDLE_VALUE) return;
  WriteFile(f, line, (DWORD)n, &wrote, NULL);
  CloseHandle(f);
}

__declspec(dllexport) int fl26_swiss_cup_cids(const uint16_t* v, int n)
{
  int i;
  g_ncid = 0;
  for (i = 0; i < n && g_ncid < 16; i++)
    if (v[i]) g_cid[g_ncid++] = v[i];
  lf("cup_cids: %d competition(s)", g_ncid);
  return g_ncid;
}

__declspec(dllexport) int fl26_swiss_log(char* out, int cap)
{
  int n = g_log_len < cap - 1 ? g_log_len : cap - 1;
  if (n <= 0) return 0;
  memcpy(out, g_log, n);
  out[n] = 0;
  memmove(g_log, g_log + n, g_log_len - n);
  g_log_len -= n;
  return n;
}

static void find_our_record(void);

static char cup_handler(void* self, uint64_t a, uint64_t b, uint64_t c){
  unsigned char** pb = (unsigned char**)((unsigned char*)self + 0x90);
  unsigned char** pe = (unsigned char**)((unsigned char*)self + 0x98);
  unsigned char** cp = (unsigned char**)((unsigned char*)self + 0xa0);
  size_t have = (*pb && *pe > *pb) ? (size_t)(*pe - *pb) / 12 : 0;
  size_t room = (*cp && *cp > *pb) ? (size_t)(*cp - *pb) / 12 : have;
  int added = 0, i;
  char r;
  find_our_record();

  for (i = 0; i < g_ncid && have + (size_t)added < room; i++) {
    uint32_t cid = g_cid[i];
    unsigned char* p;
    int there = 0;
    for (p = *pb; p && p + 12 <= *pe; p += 12)
      if (*(uint32_t*)p == cid) there = 1;
    if (there) continue;
    if (have > 0) {
      unsigned char* w = *pb + (have + (size_t)added) * 12;
      memcpy(w, *pb, 12);
      *(uint32_t*)w = cid;
      added++;
    }
  }
  if (added) *pe = *pb + (have + (size_t)added) * 12;
  lf("menu: self=%p have=%u room=%u added=%d", self, (unsigned)have, (unsigned)room, added);
  lfile("menu: self=%p have=%u room=%u added=%d", self, (unsigned)have, (unsigned)room, added);

  r = g_orig(self, a, b, c);
  lf("menu: init -> %d items=%u", (int)r,
     (unsigned)((*pb && *pe > *pb) ? (size_t)(*pe - *pb) / 12 : 0));
  {
    unsigned char* b0 = *(unsigned char**)((unsigned char*)self + 0x90);
    unsigned char* e0 = *(unsigned char**)((unsigned char*)self + 0x98);
    int n0 = (b0 && e0 > b0) ? (int)((e0 - b0) / 12) : 0;
    for (int i = 0; i < n0 && i < 14; i++) {
      unsigned char* p0 = b0 + i * 12;
      lfile("menu item %d cid=%u bytes=%02x%02x%02x%02x %02x%02x%02x%02x %02x%02x%02x%02x",
            i, (unsigned)*(uint32_t*)p0, p0[0], p0[1], p0[2], p0[3], p0[4], p0[5],
            p0[6], p0[7], p0[8], p0[9], p0[10], p0[11]);
    }
    /* the source vectors of the object: {begin,end,cap} every 8 bytes.  Dump any that hold
       12-byte entries, so we can see which one feeds the base list builder. */
    for (int off = 0x50; off <= 0xc0; off += 8) {
      unsigned char* vb = *(unsigned char**)((unsigned char*)self + off);
      unsigned char* ve = *(unsigned char**)((unsigned char*)self + off + 8);
      if (!vb || !ve || ve <= vb) continue;
      size_t bytes = (size_t)(ve - vb);
      if (bytes % 12 || bytes / 12 > 16) continue;
      int n = (int)(bytes / 12);
      char line[512]; int q = 0;
      q += snprintf(line + q, sizeof line - q, "vec +%02x n=%d:", off, n);
      for (int i = 0; i < n && q < (int)sizeof line - 12; i++)
        q += snprintf(line + q, sizeof line - q, " %u", (unsigned)*(uint32_t*)(vb + i * 12));
      lfile("%s", line);
    }
  }
  return r;
}

/* The game's fixture-date function knows regulations 2..175 and returns nothing above that.
   Our cup lives in the game's own "Custom Cup" slot (regulation 1071, competition 131), so it
   gets no dates and is never drawn.  This detour changes the id to 122 (a shipped 16-team cup)
   before the function's switch: the calendar is the one a cup of 16 already gets. */
static int date_patch(void)
{
  unsigned char* site = (unsigned char*)(uintptr_t)(g_base + DATE_SITE_RVA);
  unsigned char* resume = (unsigned char*)(uintptr_t)(g_base + DATE_RESUME_RVA);
  uint64_t target = g_base + OWNER_RVA;
  unsigned char* cave = NULL;
  int n = 0;
  DWORD old = 0;

  /* The cave must be within +-2 GB of the exe or the rel32 jumps cannot reach it (a cave at
     0x033F0000 is 5 GB away and crashed the game).  Ask for a page just past the image, then
     walk up in 64 MB steps until VirtualAlloc accepts one. */
  for (uint64_t off = 0x20000000; off < 0x70000000; off += 0x04000000) {
    cave = (unsigned char*)VirtualAlloc((void*)(uintptr_t)(g_base + off), 64,
                                        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (cave) break;
  }
  if (!cave) return 1;

  cave[n++] = 0x0f; cave[n++] = 0xb7; cave[n++] = 0xf9;              /* movzx edi, cx */
  cave[n++] = 0x81; cave[n++] = 0xff;                                 /* cmp edi, imm32 */
  *(uint32_t*)(cave + n) = 1071; n += 4;
  cave[n++] = 0x75; cave[n++] = 0x05;                                 /* jne +5 */
  cave[n++] = 0xbf; *(uint32_t*)(cave + n) = 122; n += 4;             /* mov edi, 122 */
  cave[n++] = 0xe8;                                                   /* call owner */
  *(int32_t*)(cave + n) = (int32_t)(target - (uintptr_t)(cave + n + 4)); n += 4;
  cave[n++] = 0xe9;                                                   /* jmp resume */
  *(int32_t*)(cave + n) = (int32_t)((uintptr_t)resume - (uintptr_t)(cave + n + 4)); n += 4;

  if (!VirtualProtect(site, 5, PAGE_EXECUTE_READWRITE, &old)) return 2;
  site[0] = 0xe9;
  *(int32_t*)(site + 1) = (int32_t)((uintptr_t)cave - (uintptr_t)(site + 5));
  VirtualProtect(site, 5, old, &old);
  FlushInstructionCache(GetCurrentProcess(), site, 5);
  lfile("load: date 1071 -> 122 detour at %p (cave %p)", (void*)site, (void*)cave);
  return 0;
}

/* Who calls the session-table recount?  The recount (0x1414bc0a0) is the tail of the loader
   that fills the phase table for the selected cup.  This patch stores the caller's return
   address on every call and a small thread writes it to the log; no debugger, no timing. */
static volatile uint64_t g_recount_ra;
static volatile uint64_t g_mode_state;
static volatile uint64_t g_loader_self, g_loader_begin, g_loader_end, g_loader_cap;
static volatile uint32_t g_loader_key;
static volatile uint64_t g_our_record;

static int readable_span(const void* p, size_t n)
{
  MEMORY_BASIC_INFORMATION m;
  if (!p) return 0;
  if (VirtualQuery(p, &m, sizeof m) == 0) return 0;
  if (m.State != MEM_COMMIT) return 0;
  if (m.Protect & (PAGE_NOACCESS | PAGE_GUARD)) return 0;
  return ((const unsigned char*)p + n) <= ((const unsigned char*)m.BaseAddress + m.RegionSize);
}

static void find_our_record(void)
{
  g_our_record = 0;
  if (!readable_span((void*)(uintptr_t)(g_base + 0x3705e10), 8)) return;
  uint64_t owner = *(uint64_t*)(uintptr_t)(g_base + 0x3705e10);
  if (!owner || !readable_span((void*)(uintptr_t)(owner + 0x48), 8)) return;
  uint64_t block = *(uint64_t*)(uintptr_t)(owner + 0x48);
  if (!block || !readable_span((void*)(uintptr_t)(block + 0xd0bcf4), 4)) return;
  uint32_t cnt = *(uint32_t*)(uintptr_t)(block + 0xd0bcf4);
  if (!cnt || cnt > 400) return;
  for (uint32_t i = 0; i < cnt; i++) {
    uint64_t r = block + 0xc12e9c + (uint64_t)i * 0x314;
    if (!readable_span((void*)(uintptr_t)r, 0x314)) return;
    if (*(uint16_t*)(uintptr_t)r == 200) {
      g_our_record = r;
      lfile("find: owner=%llx block=%llx cnt=%u found=%llx", (unsigned long long)owner,
            (unsigned long long)block, (unsigned)cnt, (unsigned long long)r);
      return;
    }
  }
  lfile("find: owner=%llx block=%llx cnt=%u NOT FOUND", (unsigned long long)owner,
        (unsigned long long)block, (unsigned)cnt);
}

static DWORD WINAPI recount_watch(LPVOID arg)
{
  uint64_t last = 0, last_state = 0;
  uint64_t ls = 0, lb = 0, le = 0, lk = 0;
  (void)arg;
  for (;;) {
    uint64_t ra = g_recount_ra;
    if (ra && ra != last) {
      last = ra;
      lfile("recount caller %llx (base+%llx)", (unsigned long long)ra,
            (unsigned long long)(ra - g_base));
    }
    uint64_t st = g_mode_state;
    if (st != last_state) {
      last_state = st;
      lfile("mode state %llu", (unsigned long long)st);
    }
    uint64_t s = g_loader_self;
    if (s != ls) {
      ls = s;
      lfile("loader self %llx", (unsigned long long)s);
    }
    uint64_t b = g_loader_begin, e = g_loader_end, k = g_loader_key;
    if (b != lb || e != le || k != lk) {
      lb = b; le = e; lk = k;
      lfile("loader vec begin=%llx end=%llx count=%lld key=%u",
            (unsigned long long)b, (unsigned long long)e,
            (long long)((int64_t)(e - b) / 0x314), (unsigned)k);
    }
    Sleep(100);
  }
  return 0;
}

static int recount_patch(void)
{
  unsigned char* site = (unsigned char*)(uintptr_t)(g_base + 0x14bc0a0);
  unsigned char* resume = site + 5;
  unsigned char* cave = NULL;
  int n = 0;
  DWORD old = 0;

  for (uint64_t off = 0x20000000; off < 0x70000000; off += 0x04000000) {
    cave = (unsigned char*)VirtualAlloc((void*)(uintptr_t)(g_base + off), 64,
                                        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (cave) break;
  }
  if (!cave) return 1;

  cave[n++] = 0x48; cave[n++] = 0x8b; cave[n++] = 0x04; cave[n++] = 0x24; /* mov rax,[rsp] */
  cave[n++] = 0x48; cave[n++] = 0xa3;                                     /* mov [imm64],rax */
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_recount_ra; n += 8;
  cave[n++] = 0x41; cave[n++] = 0x8b; cave[n++] = 0x47; cave[n++] = 0x78; /* mov eax,[r15+0x78] */
  cave[n++] = 0x48; cave[n++] = 0xa3;                                     /* mov [imm64],rax */
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_mode_state; n += 8;
  cave[n++] = 0x48; cave[n++] = 0x89; cave[n++] = 0x5c; cave[n++] = 0x24; cave[n++] = 0x18;
  cave[n++] = 0xe9;
  *(int32_t*)(cave + n) = (int32_t)((uintptr_t)resume - (uintptr_t)(cave + n + 4)); n += 4;

  if (!VirtualProtect(site, 5, PAGE_EXECUTE_READWRITE, &old)) return 2;
  site[0] = 0xe9;
  *(int32_t*)(site + 1) = (int32_t)((uintptr_t)cave - (uintptr_t)(site + 5));
  VirtualProtect(site, 5, old, &old);
  FlushInstructionCache(GetCurrentProcess(), site, 5);
  lfile("recount watcher at %p (cave %p)", site, cave);
  return 0;
}

static int state_patch(void)
{
  unsigned char* site = (unsigned char*)(uintptr_t)(g_base + 0x1267104);
  unsigned char* resume = (unsigned char*)(uintptr_t)(g_base + 0x126710b);
  unsigned char want[7] = { 0x48, 0x8b, 0x0d, 0x3d, 0x7c, 0x49, 0x02 };
  unsigned char* cave = NULL;
  int n = 0;
  DWORD old = 0;

  if (memcmp(site, want, 7)) { lfile("state: site mismatch"); return 3; }
  for (uint64_t off = 0x20000000; off < 0x70000000; off += 0x04000000) {
    cave = (unsigned char*)VirtualAlloc((void*)(uintptr_t)(g_base + off), 64,
                                        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (cave) break;
  }
  if (!cave) return 1;

  cave[n++] = 0x48; cave[n++] = 0xb8;                          /* mov rax, imm64 */
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)(g_base + 0x36fed48); n += 8;
  cave[n++] = 0x48; cave[n++] = 0x8b; cave[n++] = 0x08;        /* mov rcx, [rax] */
  cave[n++] = 0x8b; cave[n++] = 0x41; cave[n++] = 0x78;        /* mov eax, [rcx+0x78] */
  cave[n++] = 0x48; cave[n++] = 0xa3;                          /* mov [imm64], rax */
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_mode_state; n += 8;
  cave[n++] = 0xe9;
  *(int32_t*)(cave + n) = (int32_t)((uintptr_t)resume - (uintptr_t)(cave + n + 4)); n += 4;

  if (!VirtualProtect(site, 7, PAGE_EXECUTE_READWRITE, &old)) return 2;
  site[0] = 0xe9;
  *(int32_t*)(site + 1) = (int32_t)((uintptr_t)cave - (uintptr_t)(site + 5));
  site[5] = 0x90; site[6] = 0x90;
  VirtualProtect(site, 7, old, &old);
  FlushInstructionCache(GetCurrentProcess(), site, 7);
  lfile("state watcher at %p (cave %p)", site, cave);
  return 0;
}

static int loader_patch(void)
{
  unsigned char* site = (unsigned char*)(uintptr_t)(g_base + 0x126f000);
  unsigned char* resume = site + 5;
  unsigned char want[5] = { 0x48, 0x89, 0x4c, 0x24, 0x08 };
  unsigned char* cave = NULL;
  int n = 0;
  DWORD old = 0;

  if (memcmp(site, want, 5)) { lfile("loader: site mismatch"); return 3; }
  for (uint64_t off = 0x20000000; off < 0x70000000; off += 0x04000000) {
    cave = (unsigned char*)VirtualAlloc((void*)(uintptr_t)(g_base + off), 128,
                                        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (cave) break;
  }
  if (!cave) return 1;

  cave[n++] = 0x50;                                       /* push rax */
  cave[n++] = 0x52;                                       /* push rdx */
  /* if the cup's record vector is empty, point it at our regulation 200 record */
  cave[n++] = 0x48; cave[n++] = 0x8b; cave[n++] = 0x41; cave[n++] = 0x48;
  cave[n++] = 0x48; cave[n++] = 0x3b; cave[n++] = 0x41; cave[n++] = 0x50;
  cave[n++] = 0x75; cave[n++] = 0x25;                     /* jne over the fill */
  cave[n++] = 0x48; cave[n++] = 0xa1;                      /* mov rax,[imm64] */
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_our_record; n += 8;
  cave[n++] = 0x48; cave[n++] = 0x85; cave[n++] = 0xc0;   /* test rax,rax */
  cave[n++] = 0x74; cave[n++] = 0x16;                     /* jz over the writes */
  cave[n++] = 0x66; cave[n++] = 0x81; cave[n++] = 0x38;   /* cmp word [rax],200 */
  *(uint16_t*)(cave + n) = 200; n += 2;
  cave[n++] = 0x75; cave[n++] = 0x0f;                     /* jne over the writes */
  cave[n++] = 0x48; cave[n++] = 0x89; cave[n++] = 0x41; cave[n++] = 0x48;
  cave[n++] = 0x48; cave[n++] = 0x8d; cave[n++] = 0x90;   /* lea rdx,[rax+0x314] */
  *(uint32_t*)(cave + n) = 0x314; n += 4;
  cave[n++] = 0x48; cave[n++] = 0x89; cave[n++] = 0x51; cave[n++] = 0x50;
  cave[n++] = 0x48; cave[n++] = 0xba;                      /* mov rdx, imm64 */
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_loader_self; n += 8;
  cave[n++] = 0x48; cave[n++] = 0x89; cave[n++] = 0x0a;    /* mov [rdx], rcx */
  cave[n++] = 0x48; cave[n++] = 0x8b; cave[n++] = 0x41; cave[n++] = 0x48;
  cave[n++] = 0x48; cave[n++] = 0xa3;
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_loader_begin; n += 8;
  cave[n++] = 0x48; cave[n++] = 0x8b; cave[n++] = 0x41; cave[n++] = 0x50;
  cave[n++] = 0x48; cave[n++] = 0xa3;
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_loader_end; n += 8;
  cave[n++] = 0x48; cave[n++] = 0x8b; cave[n++] = 0x41; cave[n++] = 0x58;
  cave[n++] = 0x48; cave[n++] = 0xa3;
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_loader_cap; n += 8;
  cave[n++] = 0x48; cave[n++] = 0x8b; cave[n++] = 0x41; cave[n++] = 0x48;
  cave[n++] = 0x48; cave[n++] = 0x85; cave[n++] = 0xc0;   /* test rax,rax */
  cave[n++] = 0x74; cave[n++] = 0x0f;                     /* jz over the key read */
  cave[n++] = 0x0f; cave[n++] = 0xb7; cave[n++] = 0x10;   /* movzx edx,[rax] */
  cave[n++] = 0x48; cave[n++] = 0xb8;                      /* mov rax, imm64 */
  *(uint64_t*)(cave + n) = (uint64_t)(uintptr_t)&g_loader_key; n += 8;
  cave[n++] = 0x89; cave[n++] = 0x10;                      /* mov [rax], edx */
  cave[n++] = 0x5a;                                       /* pop rdx */
  cave[n++] = 0x58;                                       /* pop rax */
  memcpy(cave + n, want, 5); n += 5;                       /* original */
  cave[n++] = 0xe9;
  *(int32_t*)(cave + n) = (int32_t)((uintptr_t)resume - (uintptr_t)(cave + n + 4)); n += 4;

  if (!VirtualProtect(site, 5, PAGE_EXECUTE_READWRITE, &old)) return 2;
  site[0] = 0xe9;
  *(int32_t*)(site + 1) = (int32_t)((uintptr_t)cave - (uintptr_t)(site + 5));
  VirtualProtect(site, 5, old, &old);
  FlushInstructionCache(GetCurrentProcess(), site, 5);
  lfile("loader watcher at %p (cave %p)", site, cave);
  return 0;
}

BOOL WINAPI DllMain(HINSTANCE h, DWORD reason, LPVOID r)
{
  uint64_t* slot;
  DWORD old = 0;
  (void)r;
  if (reason != DLL_PROCESS_ATTACH) return TRUE;
  DisableThreadLibraryCalls(h);

  if (GetModuleFileNameA(h, g_log_path, MAX_PATH)) {
    char* dot = strrchr(g_log_path, '.');
    if (dot) strcpy(dot, ".log");
  }

  g_base = (uint64_t)(uintptr_t)GetModuleHandleA(NULL);
  slot = (uint64_t*)(uintptr_t)(g_base + CUPSEL_VT_RVA);
  lf("load: base=%llx slot=%p value=%llx expected=%llx", (unsigned long long)g_base,
     (void*)slot, (unsigned long long)*slot, (unsigned long long)(g_base + CUPSEL_INIT_RVA));
  lfile("load: base=%llx slot value=%llx expected=%llx", (unsigned long long)g_base,
        (unsigned long long)*slot, (unsigned long long)(g_base + CUPSEL_INIT_RVA));

  if (*slot != g_base + CUPSEL_INIT_RVA) {
    lfile("load: vtable slot is not the constructor -- not patched");
    return TRUE;
  }
  if (!VirtualProtect(slot, sizeof *slot, PAGE_READWRITE, &old)) {
    lfile("load: VirtualProtect failed %lu", (unsigned long)GetLastError());
    return TRUE;
  }
  g_orig = (int (*)(void*, uint64_t, uint64_t, uint64_t))(uintptr_t)*slot;
  *slot = (uint64_t)(uintptr_t)cup_handler;
  VirtualProtect(slot, sizeof *slot, old, &old);
  lfile("load: CupSelect constructor replaced");
  date_patch();
  recount_patch();
  loader_patch();
  CreateThread(NULL, 0, recount_watch, NULL, 0, NULL);
  return TRUE;
}

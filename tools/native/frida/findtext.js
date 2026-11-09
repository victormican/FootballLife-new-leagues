// findtext -- locate "Custom Cup" in memory and rewrite it as "Copa Nueva" (same length).
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function main() {
  const needle = Memory.alloc(32);
  const from = 'Custom Cup';
  const to = 'Copa Nueva';
  for (let i = 0; i < from.length; i++) needle.add(i * 2).writeU16(from.charCodeAt(i));
  needle.add(from.length * 2).writeU16(0);
  const pat = '43 00 75 00 73 00 74 00 6f 00 6d 00 20 00 43 00 75 00 70 00';
  let hits = 0, patched = 0;
  for (const r of Process.enumerateRanges('rw-')) {
    if (r.size > 64 * 1024 * 1024) continue;
    let found;
    try { found = Memory.scanSync(r.base, r.size, pat); } catch (e) { continue; }
    for (const f of found) {
      hits++;
      const a = f.address;
      log('hit ' + a + ' range=' + r.base + ' prot=' + r.protection);
      // try to patch: need write access
      try {
        Memory.protect(a, 32, 'rw-');
        for (let i = 0; i < to.length; i++) a.add(i * 2).writeU16(to.charCodeAt(i));
        patched++;
        log('  patched -> ' + a.readUtf16String(10));
      } catch (e) { log('  patch failed ' + e); }
    }
  }
  log('hits=' + hits + ' patched=' + patched);
}
main();

// dateone -- only ask for the dates of 1071 (and 46 as control), to verify the detour.
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  const b = exe.base;
  const fn = new NativeFunction(b.add(0x157f810), 'uint64', ['uint64', 'pointer']);
  for (const reg of [46, 1071]) {
    const vec = Memory.alloc(24);
    vec.writePointer(ptr(0)); vec.add(8).writePointer(ptr(0)); vec.add(16).writePointer(ptr(0));
    let n = -1, first = '';
    try {
      fn(reg, vec);
      const p = vec.readPointer(), q = vec.add(8).readPointer();
      if (!p.isNull() && q.compare(p) >= 0) {
        n = q.sub(p).toInt32() / 12;
        for (let i = 0; i < Math.min(n, 3); i++) {
          const d = p.add(i * 12);
          first += ' [' + d.readU32() + '/' + d.add(4).readU32() + '/' + d.add(8).readU32() + ']';
        }
      }
    } catch (e) { log('call ' + reg + ' threw ' + e); }
    log('dates reg=' + reg + ' n=' + n + first);
  }
  log('done');
}
main();

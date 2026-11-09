// dateprobe -- how many dates does the game's own fixture-date function return for a regulation?
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const fn = new NativeFunction(b.add(0x157f810), 'uint64', ['uint64', 'pointer']);

  for (const reg of [46, 122, 200, 1071, 6, 10]) {
    const vec = Memory.alloc(24);
    vec.writePointer(ptr(0));
    vec.add(8).writePointer(ptr(0));
    vec.add(16).writePointer(ptr(0));
    let rv = -1, n = -1, first = '';
    try {
      rv = fn(reg, vec).toNumber();
      const p = vec.readPointer();
      const q = vec.add(8).readPointer();
      if (!p.isNull() && q.compare(p) >= 0) {
        n = q.sub(p).toInt32() / 12;
        if (n > 0) {
          let s = '';
          for (let i = 0; i < Math.min(n, 4); i++) {
            const d = p.add(i * 12);
            s += ' [' + d.readU32() + '/' + d.add(4).readU32() + '/' + d.add(8).readU32() + ']';
          }
          first = s;
        }
      }
    } catch (e) { rv = -2; }
    log('dates reg=' + reg + ' rv=' + rv + ' n=' + n + first);
  }
  log('done');
}

main();

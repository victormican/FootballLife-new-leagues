// keysrc -- what vector does the menu base hand to the key-list builder?
//
// Hooks the call at 0x140c6b0f7 (and the builder 0x140eae260): rcx points to a vector of
// 12-byte elements; +0 of each element is the u16 regulation key.  Dumps begin/end/count and
// the first elements, plus the menu object (from the vtable-injected handler log).

'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;

  function dump(tag, v) {
    try {
      const p = v.readPointer();
      const q = v.add(8).readPointer();
      const c = v.add(0x10).readPointer();
      let n = -1;
      if (!p.isNull() && q.compare(p) >= 0) n = q.sub(p).toInt32() / 12;
      let s = tag + ' vec=' + v + ' begin=' + p + ' end=' + q + ' cap=' + c + ' n=' + n;
      if (n >= 0 && n <= 32) {
        for (let i = 0; i < n; i++) {
          const e = p.add(i * 12);
          const bytes = new Uint8Array(e.readByteArray(12));
          s += '\n    [' + i + '] ' + Array.from(bytes).map((x) => x.toString(16).padStart(2, '0')).join('');
        }
      }
      log(s);
    } catch (e) { log(tag + ' dump failed ' + e); }
  }

  try {
    Interceptor.attach(b.add(0xc6b0f7), { onEnter(args) { dump('CALLSITE rcx', args[0]); } });
    log('hook callsite');
  } catch (e) { log('callsite failed ' + e); }

  try {
    Interceptor.attach(b.add(0xeae260), { onEnter(args) { dump('BUILDER rcx', args[0]); } });
    log('hook builder');
  } catch (e) { log('builder failed ' + e); }

  log('ready');
}

main();

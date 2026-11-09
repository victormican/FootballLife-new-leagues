// appendcup -- add our competition as an 11th item to the cup list vector, in place.
// The base builder receives a vector of 12-byte items with 3 free slots; only the cup menu
// (the one that contains 36 and 37) is touched.
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  let calls = 0;

  Interceptor.attach(b.add(0xeae260), {
    onEnter(args) {
      try {
        const v = args[0];
        const begin = v.readPointer();
        const end = v.add(8).readPointer();
        const cap = v.add(0x10).readPointer();
        if (begin.isNull() || end.compare(begin) < 0) return;
        const n = end.sub(begin).toInt32() / 12;
        if (n < 1 || n > 32) return;
        const ids = [];
        for (let i = 0; i < n; i++) ids.push(begin.add(i * 12).readU32());
        if (calls++ < 6) log('BUILDER n=' + n + ' ids=[' + ids.join(',') + '] cap=' + cap);
        // only the cup menu: the shipped list carries 36 (Africa Cup) and 37 (Custom Cup)
        if (!ids.includes(36) || !ids.includes(37)) return;
        if (ids.includes(131)) return;
        if (end.add(12).compare(cap) > 0) { log('no room n=' + n); return; }
        const e = end;
        e.writeByteArray(new Uint8Array(begin.readByteArray(12)));
        e.writeU32(131);
        v.add(8).writePointer(end.add(12));
        log('APPEND cid=131 -> n=' + (n + 1) + ' begin=' + begin + ' cap=' + cap);
      } catch (err) { log('append err ' + err); }
    },
  });

  Interceptor.attach(b.add(0xb1c990), { onEnter(args) { log('CTOR self=' + args[0]); } });
  log('ready');
}

main();

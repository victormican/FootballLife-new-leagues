// ab2 -- A/B of the cup entry: Africa Cup (works) vs our 11th cup.
// Appends our item, then logs the session block/count, the recount caller (the loader's tail),
// findrec, phkind, the gate and the draw.
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);
  const watch = [1071, 200, 46, 131, 36];

  Interceptor.attach(b.add(0xeae260), {
    onEnter(args) {
      try {
        const v = args[0];
        const begin = v.readPointer(), end = v.add(8).readPointer(), cap = v.add(0x10).readPointer();
        if (begin.isNull() || end.compare(begin) < 0) return;
        const n = end.sub(begin).toInt32() / 12;
        if (n < 1 || n > 32) return;
        const ids = [];
        for (let i = 0; i < n; i++) ids.push(begin.add(i * 12).readU32());
        if (!ids.includes(36) || !ids.includes(37) || ids.includes(131)) return;
        if (end.add(12).compare(cap) > 0) return;
        end.writeByteArray(new Uint8Array(begin.readByteArray(12)));
        end.writeU32(131);
        v.add(8).writePointer(end.add(12));
        log('APPEND cid=131 n=' + (n + 1));
      } catch (e) { }
    },
  });
  Interceptor.attach(b.add(0xeadca0), {
    onEnter(args) {
      let keys = [];
      try {
        const p = args[0].readPointer(), q = args[0].add(8).readPointer();
        if (!p.isNull() && q.compare(p) >= 0 && q.sub(p).toInt32() <= 128) {
          const n = q.sub(p).toInt32() / 2;
          for (let i = 0; i < n; i++) keys.push(p.add(i * 2).readU16());
        }
      } catch (e) { }
      log('KEYLIST [' + keys.join(',') + ']');
    },
  });

  // the recount is called after the session table is (re)filled; its caller is the loader's tail
  Interceptor.attach(b.add(0x14bc0a0), {
    onEnter(args) {
      log('RECOUNT from=' + this.returnAddress.sub(b).toString(16) + ' block=' + args[0]);
    },
  });

  Interceptor.attach(b.add(0x150af30), {
    onEnter(args) {
      const cid = args[0].readU32();
      if (watch.includes(cid)) log('phkind cid=' + cid + ' k=' + args[1].toInt32());
    },
  });
  Interceptor.attach(b.add(0x14bc860), {
    onEnter(args) {
      const id = args[1].toInt32() & 0xffff;
      if (watch.includes(id)) log('findrec ' + id + ' from=' + this.returnAddress.sub(b).toString(16));
    },
  });
  Interceptor.attach(b.add(0x150d2b0), {
    onEnter(args) { this.reg = args[0].readU16() & 0x3ff; },
    onLeave(retval) { if (watch.includes(this.reg) || retval.toInt32() === 2) log('GATE reg=' + this.reg + ' -> ' + retval.toInt32()); },
  });
  Interceptor.attach(b.add(0x15485c0), {
    onEnter(args) { log('DRAW reg=' + (args[0].toInt32() & 0xffff)); },
  });

  log('hooks ready');

  let last = '';
  function tick() {
    try {
      const c = owner();
      if (c.isNull()) return;
      const blk = c.add(0x48).readPointer();
      if (blk.isNull()) return;
      const mode = blk.add(0x183789c).readU32();
      const cnt = blk.add(0xd0bcf4).readU32();
      const rows = [];
      for (let i = 0; i < 0x12c; i++) {
        const r = blk.add(0xc12e9c).add(i * 0x314);
        const key = r.readU16();
        if (key === 0xffff || key === 0) continue;
        const rid = key & 0x3ff;
        const cid = r.add(0x80).readU32();
        if (rid === 1071 || rid === 200 || cid === 131 || cid === 36)
          rows.push(i + ':k=' + key + '/c=' + cid + '/s=' + r.add(0x84).readU32());
      }
      const line = 'mode=' + mode + ' block=' + blk + ' count=' + cnt + ' [' + rows.join(' ') + ']';
      if (line !== last) { last = line; log(line); }
    } catch (e) { }
  }
  tick();
  setInterval(tick, 1500);
  log('ready');
}

main();

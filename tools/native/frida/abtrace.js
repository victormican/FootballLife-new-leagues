// abtrace -- capture the whole cup entry: phkind/findrec callers, the key-list resolver,
// the draw gate, the draw, and the session table.  Works for the shipped Africa Cup and ours.
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);

  function where(p) {
    try {
      const m = Process.findModuleByAddress(p);
      if (m && m.name.toLowerCase().includes('fl_2026')) return '+' + p.sub(m.base).toString(16);
      return m ? m.name + '+' + p.sub(m.base) : p.toString();
    } catch (e) { return '?'; }
  }

  Interceptor.attach(b.add(0x150af30), {
    onEnter(args) {
      const cid = args[0].readU32();
      const k = args[1].toInt32();
      if ([131, 36, 130, 11].includes(cid))
        log('phkind cid=' + cid + ' k=' + k + ' from=' + where(this.returnAddress));
    },
  });

  Interceptor.attach(b.add(0x14bc860), {
    onEnter(args) {
      const id = args[1].toInt32() & 0xffff;
      if ([200, 46, 36, 11].includes(id))
        log('findrec reg=' + id + ' from=' + where(this.returnAddress));
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
      log('KEYLIST [' + keys.join(',') + '] from=' + where(this.returnAddress));
    },
  });

  Interceptor.attach(b.add(0x150d2b0), {
    onEnter(args) { this.reg = args[0].readU16() & 0x3ff; },
    onLeave(retval) { if (this.reg === 200 || this.reg === 46 || retval.toInt32() === 2) log('GATE reg=' + this.reg + ' -> ' + retval.toInt32()); },
  });

  Interceptor.attach(b.add(0x15485c0), {
    onEnter(args) { log('DRAW reg=' + (args[0].toInt32() & 0xffff)); },
  });

  log('hooks ready');

  let last = '';
  function tick() {
    try {
      const ctx = owner();
      if (ctx.isNull()) return;
      const block = ctx.add(0x48).readPointer();
      if (block.isNull()) return;
      const mode = block.add(0x183789c).readU32();
      const count = block.add(0xd0bcf4).readU32();
      const rows = [];
      for (let i = 0; i < 0x12c; i++) {
        const r = block.add(0xc12e9c).add(i * 0x314);
        const key = r.readU16();
        if (key === 0xffff || key === 0) continue;
        const cid = r.add(0x80).readU32();
        if (cid === 131 || key === 200 || cid === 36 || key === 46)
          rows.push(i + ':k=' + key + '/c=' + cid + '/s=' + r.add(0x84).readU32());
      }
      const line = 'mode=' + mode + ' count=' + count + ' block=' + block + ' [' + rows.join(' ') + ']';
      if (line !== last) { last = line; log(line); }
    } catch (e) { }
  }
  tick();
  setInterval(tick, 1500);
  log('ready');
}

main();

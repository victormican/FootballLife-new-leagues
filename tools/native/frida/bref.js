// bref -- find the session loader: follow a working cup (Africa Cup) and the 11th item.
// Adds our item to the cup list, then logs the menu enter, phkind/findrec callers, the recount
// (whose caller is the loader's tail), the gate/draw and the session table.
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

  // add our cup as an 11th item
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
        log('APPEND cid=131 ids=[' + ids.join(',') + ',131]');
      } catch (e) { }
    },
  });

  // menu enter (shared): what does the selected cup look like?
  Interceptor.attach(b.add(0xe43450), {
    onEnter(args) {
      log('ENTER self=' + args[0] + ' a=' + args[1] + ' b=' + args[2] + ' c=' + args[3] +
          ' from=' + where(this.returnAddress));
    },
  });

  Interceptor.attach(b.add(0x150af30), {
    onEnter(args) {
      const cid = args[0].readU32();
      if ([131, 36, 37, 200, 1071].includes(cid))
        log('phkind cid=' + cid + ' k=' + args[1].toInt32() + ' from=' + where(this.returnAddress));
    },
  });
  Interceptor.attach(b.add(0x14bc860), {
    onEnter(args) {
      const id = args[1].toInt32() & 0xffff;
      if ([200, 1071, 46, 36, 131].includes(id))
        log('findrec ' + id + ' from=' + where(this.returnAddress));
    },
  });

  // recount: called after the session table is (re)filled
  Interceptor.attach(b.add(0x14bc0a0), {
    onEnter(args) {
      log('RECOUNT from=' + where(this.returnAddress) + ' block=' + args[0]);
    },
  });

  Interceptor.attach(b.add(0x150d2b0), {
    onEnter(args) { this.reg = args[0].readU16() & 0x3ff; },
    onLeave(retval) { if ([200, 1071, 46].includes(this.reg) || retval.toInt32() === 2) log('GATE reg=' + this.reg + ' -> ' + retval.toInt32()); },
  });
  Interceptor.attach(b.add(0x15485c0), { onEnter(args) { log('DRAW reg=' + (args[0].toInt32() & 0xffff)); } });

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
        const cid = r.add(0x80).readU32();
        if (cid === 131 || key === 200 || key === 1071 || cid === 36 || key === 46)
          rows.push(i + ':k=' + key + '/c=' + cid + '/s=' + r.add(0x84).readU32());
      }
      const line = 'mode=' + mode + ' count=' + cnt + ' block=' + blk + ' [' + rows.join(' ') + ']';
      if (line !== last) { last = line; log(line); }
    } catch (e) { }
  }
  tick();
  setInterval(tick, 1500);
  log('ready');
}

main();

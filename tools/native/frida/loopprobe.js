// loopprobe -- who is calling findrec(1071) in a loop?
'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;

  function where(p) {
    try {
      const m = Process.findModuleByAddress(p);
      if (m && m.name.toLowerCase().includes('fl_2026')) return '+' + p.sub(m.base).toString(16);
      return m ? m.name + '+' + p.sub(m.base) : p.toString();
    } catch (e) { return '?'; }
  }

  const seen = {};

  Interceptor.attach(b.add(0x14bc860), {
    onEnter(args) {
      const id = args[1].toInt32() & 0xffff;
      if (id !== 1071 && id !== 200) return;
      const ra = this.returnAddress;
      const k = where(ra);
      seen[k] = (seen[k] || 0) + 1;
      if (seen[k] === 1) {
        let bt = '';
        try {
          const frames = Thread.backtrace(this.context, Backtracer.ACCURATE);
          bt = frames.slice(0, 6).map(where).join(' <- ');
        } catch (e) { bt = '?'; }
        log('findrec ' + id + ' from=' + k + ' bt=' + bt);
      } else if (seen[k] === 100 || seen[k] === 1000 || seen[k] === 10000) {
        log('findrec ' + id + ' from=' + k + ' count=' + seen[k]);
      }
    },
  });

  Interceptor.attach(b.add(0x150d2b0), {
    onEnter(args) { this.reg = args[0].readU16() & 0x3ff; },
    onLeave(retval) { if (this.reg === 1071 || this.reg === 200) log('GATE reg=' + this.reg + ' -> ' + retval.toInt32()); },
  });

  log('ready');
}

main();

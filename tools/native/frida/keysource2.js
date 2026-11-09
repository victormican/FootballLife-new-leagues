// keysource2 -- capture the source vector of the base list builder (no owner() calls).
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  const b = exe.base;
  Interceptor.attach(b.add(0xc6b076), {
    onEnter() {
      try {
        const c = this.context;
        const r12 = c.r12, r13 = c.r13, r14 = c.r14;
        let ids = '';
        try {
          for (let i = 0; i < 12; i++) ids += ' ' + r12.add(i * 12).readU32();
        } catch (e) { ids = ' ?'; }
        log('COPY r12=' + r12 + ' r13=' + r13 + ' r14=' + r14 + ' ids:' + ids);
      } catch (e) { log('COPY err ' + e); }
    },
  });
  log('ready');
}
main();

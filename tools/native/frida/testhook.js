// testhook -- does the phkind interceptor fire at all?  Calls it once from here.
'use strict';
const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };
function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  const b = exe.base;
  const phkind = new NativeFunction(b.add(0x150af30), 'uint64', ['pointer', 'uint64']);
  let fired = 0;
  Interceptor.attach(b.add(0x150af30), {
    onEnter(args) { fired++; },
    onLeave(retval) { log('HOOK fired cid -> ' + retval.toNumber()); },
  });
  const buf = Memory.alloc(4);
  buf.writeU32(131);
  log('direct call -> ' + phkind(buf, 3).toNumber());
  log('fired=' + fired);
}
main();

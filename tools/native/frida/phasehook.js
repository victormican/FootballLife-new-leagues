// phasehook -- how does the game invoke the phase processor (0x141348210) for a cup that works?
//
// The clone's cup (cid 36) reaches its bracket; our own never does.  This logs every call to the
// phase case with its regulation and the four arguments, so the same call can be replayed for our
// regulation afterwards.

'use strict';

const log = (s) => {
  const t = String(s);
  console.log(t);
  send({ kind: 'log', text: t });
};

function fmt(a) {
  const m = Process.findModuleByAddress(a);
  return m ? (m.name + '+' + a.sub(m.base)) : a.toString();
}

function main() {
  const exe = Process.enumerateModules().find(
    (m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }

  try {
    Interceptor.attach(exe.base.add(0x13481f3), {
      onEnter(args) {
        log('PHASE a0=' + args[0] + ' reg=' + args[1].and(0xffff) +
            ' a2=' + args[2] + ' a3=' + args[3] + ' ret=' + fmt(this.returnAddress));
      },
      onLeave(retval) { log('PHASE -> ' + retval); },
    });
    log('hook phase installed');
  } catch (e) { log('hook phase failed ' + e); }

  try {
    Interceptor.attach(exe.base.add(0x15485c0), {
      onEnter(args) {
        try {
          const v = args[1];
          const b = v.readPointer();
          const e2 = v.add(8).readPointer();
          const n = b.isNull() ? -1 : e2.sub(b).toInt32() / 4;
          log('DRAW reg=' + args[0].and(0xffff) + ' clubs=' + n + ' ret=' + fmt(this.returnAddress));
        } catch (e) { }
      },
    });
    log('hook draw installed');
  } catch (e) { log('hook draw failed ' + e); }

  log('ready');
}

main();

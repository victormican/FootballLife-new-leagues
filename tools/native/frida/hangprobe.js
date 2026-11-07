// hangprobe -- when the game freezes, say where every thread is.
//
// A freeze leaves the process alive but not drawing.  This walks the threads, takes each context
// and resolves the program counter to module+offset, plus a backtrace of the thread that is not
// idle.  Run it while frozen.

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
  const threads = Process.enumerateThreads();
  log('threads: ' + threads.length);
  for (const t of threads) {
    try {
      const c = t.context;
      log('T' + t.id + ' pc=' + fmt(c.pc) + ' sp=' + c.sp);
      const bt = Thread.backtrace(c, Backtracer.ACCURATE).slice(0, 12).map(fmt).join(' ');
      log('   bt ' + bt);
    } catch (e) {
      log('T' + t.id + ' <no context: ' + e + '>');
    }
  }
  log('done');
}

main();

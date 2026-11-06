// cupmenu_rea -- Kick Off > Cup from inside FL_2026, driven by REA's frida provider.
//
// Facts this probe is built on (2026-11-06, from the sessions before it):
//   * the Cup panel's list is filled by the vtable slot +0xd8 of the menu object, which is our
//     cupsel_handler in fl26swiss.dll (it filters cups with more than 32 clubs in their group
//     phase, appends the world cups and calls the game's init 0x140b1c990);
//   * init returns 1 and the list keeps 9 items (33,5,8,27,36,34,35,37,131) -- ours is the last;
//   * right after that the game either goes black or leaves to the desktop, so the transition is
//     what has to be watched: 0x140e43450 is the menu's enter handler, and it is the only caller of
//     the vtable slot (return address 0x140e43462).
//
// Everything is logged through console.log so REA returns it as script messages.

'use strict';

const MODULE = 'FL_2026.exe';

// REA's frida provider collects the script's send() messages, not console output.
const log = (text) => {
  const s = String(text);
  console.log(s);
  send({ kind: 'log', text: s });
};

// A message sent from inside ExitProcess can lose the race with the process dying, so the exit
// trace is written by the agent itself, before the game is allowed to go.
const EXIT_LOG = 'C:\\Users\\viarm\\AppData\\Local\\Temp\\opencode\\exit-trace.txt';
const note = (text) => {
  const s = String(text);
  try {
    const f = new File(EXIT_LOG, 'a');
    f.write(s + '\n');
    f.flush();
    f.close();
  } catch (e) { /* the file is a nicety, the log line still goes out */ }
  log(s);
};

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase() === MODULE.toLowerCase());
  if (!exe) {
    log('FL_2026.exe not loaded');
    return;
  }
  log('base ' + exe.base + ' size ' + exe.size);

  const fmt = (a) => {
    const m = Process.findModuleByAddress(a);
    return m ? (m.name + '+' + a.sub(m.base)) : a.toString();
  };

  const wstr = (p) => {
    try {
      const cap = p.add(0x18).readU64().toNumber();
      const size = p.add(0x10).readU64().toNumber();
      if (size === 0 || size > 200) return '<size ' + size + '>';
      const data = cap >= 8 ? p.readPointer() : p;
      return data.readUtf16String(Math.min(size, 120));
    } catch (e) {
      return '<unreadable>';
    }
  };

  const qwords = (p, n) => {
    const out = [];
    for (let i = 0; i < n; i++) {
      try { out.push(p.add(i * 8).readPointer().toString()); } catch (e) { out.push('?'); }
    }
    return out.join(' ');
  };

  // The game's own resolver: phkind(cid*, kind) -> group id;  owner() -> edit owner, its +0x48 is
  // the block findrec(block, id) searches.  cupsel_handler uses exactly these to filter the list.
  let phkind, owner, findrec;
  try {
    phkind = new NativeFunction(exe.base.add(0x150af30), 'uint64', ['pointer', 'uint64']);
    owner = new NativeFunction(exe.base.add(0x14b6a60), 'pointer', []);
    findrec = new NativeFunction(exe.base.add(0x14bc860), 'pointer', ['pointer', 'uint64']);
  } catch (e) {
    log('resolver functions unavailable: ' + e);
  }

  const probe = (cid) => {
    if (!phkind) return;
    const buf = Memory.alloc(4);
    buf.writeU32(cid);
    const out = [];
    for (let k = 1; k <= 6; k++) {
      let v = 0;
      try { v = phkind(buf, k).toNumber(); } catch (e) { v = -1; }
      out.push('k' + k + '=' + v);
    }
    let rec = null;
    let name = '';
    try {
      const o = owner();
      const blk = o.isNull() ? null : o.add(0x48).readPointer();
      const g = phkind(buf, 2).toNumber();
      if (blk && !blk.isNull() && g !== 0xffff) {
        rec = findrec(blk, g);
        if (!rec.isNull()) {
          name = rec.add(0x14).readUtf8String(40) || '';
        }
      }
      log('CID ' + cid + ' ' + out.join(' ') + ' rec=' + (rec ? rec.toString() : 'null') +
          ' name="' + name + '"' +
          (rec && !rec.isNull() ? ' r30c=' + rec.add(0x30c).readU32().toString(16) : ''));
    } catch (e) {
      log('CID ' + cid + ' ' + out.join(' ') + ' probe error ' + e);
    }
  };

  // expose our competition to the DLL (it is the list fl26_swiss_cup_cids keeps).
  // WANT_CUPS is the A/B switch: [] leaves only the game's own cups, null leaves the world's own
  // ccup line alone (what the Lua read at boot).
  const want = null;
  log('cups to append: [' + (want ? want.join(',') : 'world') + ']');
  try {
    const dll = Process.findModuleByName('fl26swiss.dll');
    if (dll) {
      const fn = new NativeFunction(dll.findExportByName('fl26_swiss_cup_cids'), 'int',
                                    ['pointer', 'int']);
      if (want === null) {
        log('setcups skipped (the world line decides)');
      } else if (want.length === 0) {
        log('setcups -> ' + fn(ptr(0), 0));
      } else {
        const buf = Memory.alloc(want.length * 2);
        want.forEach((c, i) => buf.add(i * 2).writeU16(c));
        log('setcups -> ' + fn(buf, want.length));
      }
    } else {
      log('fl26swiss.dll not loaded');
    }
  } catch (e) {
    log('setcups failed: ' + e);
  }

  // --- the menu -------------------------------------------------------------------------------
  try {
    Interceptor.attach(exe.base.add(0xb1c990), {
      onEnter(args) {
        try {
          const self = args[0];
          const b = self.add(0x90).readPointer();
          const e2 = self.add(0x98).readPointer();
          const cap = self.add(0xa0).readPointer();
          const n = b.isNull() || e2.compare(b) < 0 ? -1 : e2.sub(b).toInt32() / 12;
          log('INIT enter self=' + self + ' begin=' + b + ' end=' + e2 + ' cap=' + cap +
                      ' n=' + n);
          if (n > 0 && n < 64) {
            const item = [];
            for (let i = 0; i < n; i++) {
              try {
                const p = b.add(i * 12);
                item.push(p.readU32() + ':' + p.add(4).readByteArray(8).hex);
              } catch (e) { item.push('?'); }
            }
            log('  items ' + item.join(' '));
            for (let i = 0; i < n; i++) {
              try { probe(b.add(i * 12).readU32()); } catch (e) { log('  probe ' + i + ' ' + e); }
            }
          }
        } catch (e) {
          log('INIT hook error ' + e);
        }
      },
      onLeave(retval) {
        log('INIT leave -> ' + retval);
      },
    });
    log('hook init installed');
  } catch (e) {
    log('hook init failed: ' + e);
  }

  const steps = [
    [0xe43450, 'ENTER'],
    [0xe3f4c0, 'modebuild'],
    [0xe32980, 'getA'],
    [0xe32ad0, 'checkA'],
    [0xe52850, 'step52850'],
    [0xe4c240, 'row'],
  ];
  let rowCalls = 0;
  for (const [rva, name] of steps) {
    try {
      Interceptor.attach(exe.base.add(rva), {
        onEnter(args) {
          if (name === 'row' && rowCalls++ > 40) return;
          log('STEP ' + name + ' in rcx=' + args[0] + ' rdx=' + args[1] +
                      ' r8=' + args[2] + ' r9=' + args[3] + ' ret=' + this.returnAddress);
        },
        onLeave(retval) {
          if (name !== 'row') log('STEP ' + name + ' out -> ' + retval);
        },
      });
      log('hook ' + name + ' installed');
    } catch (e) {
      log('hook ' + name + ' failed: ' + e);
    }
  }

  for (const [modName, fnName] of [['kernel32.dll', 'ExitProcess'],
                                   ['kernel32.dll', 'TerminateProcess'],
                                   ['ntdll.dll', 'RtlExitUserProcess'],
                                   ['ucrtbase.dll', 'abort']]) {
    try {
      const m = Process.findModuleByName(modName);
      if (!m) { log('exit hook: ' + modName + ' not loaded'); continue; }
      const addr = m.findExportByName(fnName);
      if (!addr) { log('exit hook: ' + modName + '!' + fnName + ' missing'); continue; }
      Interceptor.attach(addr, {
        onEnter(args) {
          const bt = Thread.backtrace(this.context, Backtracer.ACCURATE)
            .map((a) => {
              const mm = Process.findModuleByAddress(a);
              return mm ? mm.name + '+' + a.sub(mm.base) : a.toString();
            }).join(' ');
          note('EXIT ' + modName + '!' + fnName + ' code=' + args[0] + ' from ' +
               this.returnAddress + ' bt ' + bt);
          // let the agent write the file and flush the message before the process goes
          try { Thread.sleep(1); } catch (e) { }
        },
      });
      log('hook ' + modName + '!' + fnName + ' installed');
    } catch (e) {
      log('exit hook ' + modName + '!' + fnName + ' failed: ' + e);
    }
  }

  // C++ exceptions do not surface as access violations: they are RaiseException with the MSVC
  // code and the throw site is in the backtrace.  A fatal unhandled one ends in the CRT's exit
  // path, which is where the process-path map was seen faulting at shutdown.
  for (const [modName, fnName] of [['kernel32.dll', 'RaiseException'],
                                   ['ucrtbase.dll', '_CxxThrowException']]) {
    try {
      const m = Process.findModuleByName(modName);
      if (!m) { log('throw hook: ' + modName + ' not loaded'); continue; }
      const addr = m.findExportByName(fnName);
      if (!addr) { log('throw hook: ' + modName + '!' + fnName + ' missing'); continue; }
      Interceptor.attach(addr, {
        onEnter(args) {
          const bt = Thread.backtrace(this.context, Backtracer.ACCURATE)
            .map((a) => {
              const mm = Process.findModuleByAddress(a);
              return mm ? mm.name + '+' + a.sub(mm.base) : a.toString();
            }).join(' ');
          note('THROW ' + modName + '!' + fnName + ' arg0=' + args[0] + ' from ' +
               this.returnAddress + ' bt ' + bt);
          try { Thread.sleep(0.3); } catch (e) { }
        },
      });
      log('hook ' + modName + '!' + fnName + ' installed');
    } catch (e) {
      log('throw hook ' + modName + '!' + fnName + ' failed: ' + e);
    }
  }

  Process.setExceptionHandler((details) => {
    if (details.type !== 'access-violation') return false;
    try {
      const c = details.context;
      log('EXC address=' + details.address + ' rip=' + c.pc + ' (base+' +
                  c.pc.sub(exe.base) + ')');
      log('  rax=' + c.rax + ' rbx=' + c.rbx + ' rcx=' + c.rcx + ' rdx=' + c.rdx +
                  ' rsi=' + c.rsi + ' rdi=' + c.rdi);
      log('  r8=' + c.r8 + ' r9=' + c.r9 + ' r10=' + c.r10 + ' r11=' + c.r11 +
                  ' r12=' + c.r12 + ' r13=' + c.r13 + ' r14=' + c.r14 + ' r15=' + c.r15);
      log('  backtrace ' + Thread.backtrace(c, Backtracer.ACCURATE).map(fmt).join(' '));
    } catch (e) {
      log('EXC handler error ' + e);
    }
    return false;
  });
  log('ready');
}

main();

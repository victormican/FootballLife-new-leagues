// cupmenu_probe -- Kick Off > Cup, 2026-11-06.
//
// The cup list is built when the cursor reaches the panel.  cupsel_handler (fl26swiss) filters,
// adds our competition and calls the menu's init; init returns, and then the game dereferences a
// null tree node (cmp byte [r10+0x19],0 with [r10]=0 at 0x141ae48ae).  This probe does three
// things, all from inside the process:
//   1. hooks the crashing function (0x141ae4870, a std::map<wstring,...>::find walker) and, when
//      the head it is about to read has a null parent, dumps the backtrace and the map object;
//   2. hooks the menu init (0x140b1c990) to log the list it is given and what it returns;
//   3. catches the access violation itself (Process.setExceptionHandler) and prints the full
//      register set and an accurate backtrace, then lets the game die as before.
//
// Run elevated (the game is), via node:
//   node tools/native/frida/run_probe.mjs <pid> <out-file> <seconds>

'use strict';

const MODULE = 'FL_2026.exe';
const RVA_FIND = 0x1ae4870;
const RVA_INIT = 0xb1c990;

function main() {
  const lines = [];
  const log = (s) => {
    lines.push(s);
    send({ kind: 'log', text: s });
  };

  const mods = Process.enumerateModules();
  const exe = mods.find((m) => m.name.toLowerCase() === MODULE.toLowerCase());
  if (!exe) {
    send({ kind: 'fatal', text: 'FL_2026.exe is not loaded' });
    return;
  }
  log('base ' + exe.base + ' size ' + exe.size);

  let findHits = 0;
  try {
    Interceptor.attach(exe.base.add(RVA_FIND), {
      onEnter(args) {
        findHits++;
        try {
          const map = args[0];
          const head = map.readPointer();
          const root = head.add(8).readPointer();
          if (root.compare(ptr('0x10000')) >= 0) return;
          const nil = head.add(0x19).readU8();
          let text = '';
          try { text = wstr(args[3]); } catch (e) { text = '<unreadable>'; }
          log('FIND(bad) #' + findHits + ' ret=' + this.returnAddress + ' map=' + map +
              ' head=' + head + ' root=' + root + ' nil=' + nil + ' keyw="' + text + '"');
          const bt = Thread.backtrace(this.context, Backtracer.ACCURATE);
          log('  backtrace ' + bt.map(fmt).join(' '));
        } catch (e) {
          log('FIND hook error ' + e);
        }
      },
    });
    log('hook find installed');
  } catch (e) {
    log('hook find failed: ' + e);
  }

  try {
    Interceptor.attach(exe.base.add(RVA_INIT), {
      onEnter(args) {
        try {
          const self = args[0];
          const b = self.add(0x90).readPointer();
          const e2 = self.add(0x98).readPointer();
          const cap = self.add(0xa0).readPointer();
          const n = b.isNull() || e2.compare(b) < 0 ? -1 : e2.sub(b).toInt32() / 12;
          log('INIT enter self=' + self + ' begin=' + b + ' end=' + e2 + ' cap=' + cap + ' n=' + n);
          if (n > 0 && n < 64) {
            const item = [];
            for (let i = 0; i < n; i++) item.push(b.add(i * 12).readU32());
            log('  cids ' + item.join(','));
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

  function qwords(p, n) {
    const out = [];
    for (let i = 0; i < n; i++) out.push(p.add(i * 8).readPointer().toString());
    return out.join(' ');
  }

  function fmt(a) {
    const m = Process.findModuleByAddress(a);
    return m ? (m.name + '+' + a.sub(m.base)) : a.toString();
  }

  // MSVC std::wstring: at +0 the buffer pointer (when the string does not fit in the 16-byte
  // inline buffer), +0x10 the size, +0x18 the capacity.
  function wstr(p) {
    const cap = p.add(0x18).readU64().toNumber();
    const size = p.add(0x10).readU64().toNumber();
    if (size === 0 || size > 200) return '<size ' + size + '>';
    const data = cap >= 8 ? p.readPointer() : p;
    return data.readUtf16String(Math.min(size, 120));
  }

  Process.setExceptionHandler((details) => {
    if (details.type !== 'access-violation') return false;
    try {
      const c = details.context;
      log('EXC type=' + details.type + ' address=' + details.address +
          ' rip=' + c.pc + ' (base+' + c.pc.sub(exe.base) + ')');
      log('  rax=' + c.rax + ' rbx=' + c.rbx + ' rcx=' + c.rcx + ' rdx=' + c.rdx);
      log('  rsi=' + c.rsi + ' rdi=' + c.rdi + ' rbp=' + c.rbp + ' rsp=' + c.rsp);
      log('  r8=' + c.r8 + ' r9=' + c.r9 + ' r10=' + c.r10 + ' r11=' + c.r11 +
          ' r12=' + c.r12 + ' r13=' + c.r13 + ' r14=' + c.r14 + ' r15=' + c.r15);
      const bt = Thread.backtrace(c, Backtracer.ACCURATE);
      log('  backtrace ' + bt.map(fmt).join(' '));
      if (c.pc.equals(exe.base.add(0x1ae48ae))) {
        try {
          log('  walk mapq ' + qwords(c.rcx, 4) + ' | headq ' + qwords(c.r13, 5) +
              ' | r10=' + c.r10 + ' keyw="' + c.r9.readUtf16String(48) + '"');
        } catch (e) { log('  walk dump error ' + e); }
      }
      for (let i = 0; i < 16; i++) {
        try { log('  rsp+' + (i * 8) + ' ' + c.rsp.add(i * 8).readPointer()); } catch (e) { break; }
      }
    } catch (e) {
      log('EXC handler error ' + e);
    }
    send({ kind: 'flush' });
    return false;
  });
  // --- the cup mode transition -------------------------------------------------------------
  // 0x140e43450 is the menu's "enter" handler: it calls the vtable slot +0xd8 (our cupsel_handler),
  // and when that returns non-zero it walks the rows, builds the mode and runs the transition.  The
  // game leaves to the desktop from here with the world cup in the list, so every step is logged.
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
          if (name === 'row' && rowCalls++ > 60) return;
          try {
            log('STEP ' + name + ' in rcx=' + args[0] + ' rdx=' + args[1] + ' r8=' + args[2] +
                ' r9=' + args[3] + ' ret=' + this.returnAddress);
          } catch (e) { log('STEP ' + name + ' log error ' + e); }
        },
        onLeave(retval) {
          try {
            log('STEP ' + name + ' out -> ' + retval);
          } catch (e) { /* ignore */ }
        },
      });
      log('hook ' + name + ' installed');
    } catch (e) {
      log('hook ' + name + ' failed: ' + e);
    }
  }

  // who asks Windows to end the process?  a clean exit from the cup flow shows the caller.
  const exits = [
    ['kernel32.dll', 'ExitProcess'],
    ['kernel32.dll', 'TerminateProcess'],
    ['kernel32.dll', 'RtlExitUserProcess'],
    ['ucrtbase.dll', 'abort'],
    ['msvcrt.dll', 'abort'],
  ];
  for (const [modName, fnName] of exits) {
    try {
      const m = Process.findModuleByName(modName);
      if (!m) { log('exit hook: ' + modName + ' not loaded'); continue; }
      const addr = m.findExportByName(fnName);
      if (!addr) { log('exit hook: ' + modName + '!' + fnName + ' not found'); continue; }
      Interceptor.attach(addr, {
        onEnter(args) {
          log('EXIT ' + modName + '!' + fnName + ' code=' + args[0] + ' from ' +
              this.returnAddress);
          const bt = Thread.backtrace(this.context, Backtracer.ACCURATE);
          log('  backtrace ' + bt.map(fmt).join(' '));
        },
      });
      log('hook ' + modName + '!' + fnName + ' installed');
    } catch (e) {
      log('exit hook ' + modName + '!' + fnName + ' failed: ' + e);
    }
  }

  log('exception handler installed');

  // A/B switch: fl26_swiss_cup_cids is the DLL's list of world cups to append.  Calling it with
  // an empty list turns the append off without rebuilding or restarting, so the same session can
  // try the menu with the shipped 8 cups and then with ours.
  rpc.exports = {
    setcups(cids) {
      const mod = Process.findModuleByName('fl26swiss.dll');
      if (!mod) return 'fl26swiss.dll not loaded';
      const fn = new NativeFunction(mod.findExportByName('fl26_swiss_cup_cids'), 'int',
                                    ['pointer', 'int']);
      if (!cids || cids.length === 0) return 'set ' + fn(ptr(0), 0);
      const buf = Memory.alloc(cids.length * 2);
      cids.forEach((c, i) => buf.add(i * 2).writeU16(c));
      return 'set ' + fn(buf, cids.length);
    },
  };

  send({ kind: 'ready' });
}

main();

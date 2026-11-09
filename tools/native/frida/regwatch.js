// regwatch -- follow the session phase table while the cup is opened.
//
// Every second: ask the game for its current context (owner()), read the block's
// phase table (0x314 records, count at +0xd0bcf4) and report the slots that carry
// our competition (cid 131) or our regulation (key 200), plus the slot count.
// Only changes are logged.

'use strict';

const log = (s) => { const t = String(s); console.log(t); send({ kind: 'log', text: t }); };

function main() {
  const exe = Process.enumerateModules().find((m) => m.name.toLowerCase().includes('fl_2026'));
  if (!exe) { log('FL_2026.exe not loaded'); return; }
  const b = exe.base;
  const owner = new NativeFunction(b.add(0x14b6a60), 'pointer', []);

  let last = '';

  function tick() {
    try {
      const ctx = owner();
      if (ctx.isNull()) return;
      const block = ctx.add(0x48).readPointer();
      if (block.isNull()) return;
      const mode = block.add(0x183789c).readU32();
      let count = block.add(0xd0bcf4).readU32();
      const scan = Math.min(count, 0x12c);
      const found = [];
      for (let i = 0; i < scan; i++) {
        const r = block.add(0xc12e9c).add(i * 0x314);
        const key = r.readU16();
        const cid = r.add(0x80).readU32();
        if (cid === 131 || key === 200 || cid === 36 || key === 46) {
          found.push(i + ':key=' + key + '/cid=' + cid + '/st=' + r.add(0x84).readU32());
        }
      }
      const line = 'block=' + block + ' mode=' + mode + ' count=' + (count === 0xffffffff ? 'x' : count) +
        ' scan=' + scan + ' [' + found.join(' ') + ']';
      if (line !== last) { last = line; log(line); }
    } catch (e) { /* memory moved while reading; next tick */ }
  }

  tick();
  setInterval(tick, 1000);
  log('watching');
}

main();

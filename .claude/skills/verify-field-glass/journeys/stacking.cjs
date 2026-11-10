// The unit panels (hover tip and card), moved over the caption strip and over the tick tip, must be topmost at every
// sampled point. The app moves the card back to its unit on the next frame, so each check samples inside one evaluate,
// before any frame.
// Run: bash fg.sh drive <dir> journeys/stacking.cjs
const puppeteer = require('puppeteer-core');
const [exe, base, dir] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
const NAME = { caption: 'caption strip', 'tick-tip': 'tick tip' };
(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const p = await br.newPage(); await p.setViewport({ width: 1536, height: 830, deviceScaleFactor: 1.25 });
  for (const [id, sel] of [['first-manassas', 'va33'], ['sidi-bou-zid', null], ['cowpens', 'howard']]) {
    await p.goto(`${base}#${id}${sel ? `@14:32,play,select=${sel}` : ',play'}`, { waitUntil: 'networkidle0' }); // ,play opens with the drawer closed
    await p.waitForFunction(() => document.querySelector('#splash').hidden && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 });
    await p.click('#play'); await new Promise(r => setTimeout(r, 1500));
    const x = await p.$eval('#marks i', i => { const r = i.getBoundingClientRect(); return (r.left + r.right) / 2; });
    const y = await p.$eval('#scrub', s => { const r = s.getBoundingClientRect(); return (r.top + r.bottom) / 2; });
    await p.mouse.move(x, y); await new Promise(r => setTimeout(r, 200)); // the tip over the first tick
    const res = await p.evaluate(() => {
      const out = {};
      for (const k of ['caption', 'tick-tip']) {
        const target = document.querySelector(`#${k}`), m = target.getBoundingClientRect();
        out[k] = { shown: !target.hidden && +getComputedStyle(target).opacity > 0 && m.width > 0 };
        const hv = document.querySelector('#hover'); hv.hidden = false; hv.innerHTML = '<b>Test</b><br>a unit<br>over the chrome'; hv.style.left = `${m.left + 10}px`; hv.style.top = `${m.top - 40}px`; hv.style.pointerEvents = 'auto'; // elementFromPoint skips pointer-events: none
        const cd = document.querySelector('#card'); cd.style.opacity = 1; cd.style.pointerEvents = 'auto'; cd.style.transform = `translate(${m.left + Math.min(m.width, 400) - 160}px, ${m.top - 30}px)`;
        for (const el of [hv, cd]) { // one at a time: the hover tip rightly sits over the card
          const other = el === hv ? cd : hv, keep = other.style.visibility; other.style.visibility = 'hidden';
          const r = el.getBoundingClientRect();
          const pts = [[0.5, 0.5], [0.2, 0.8], [0.8, 0.8], [0.2, 0.2], [0.8, 0.2]].map(([fx, fy]) => document.elementFromPoint(r.left + r.width * fx, r.top + r.height * fy));
          out[k][el.id] = pts.filter(t => t && !el.contains(t)).map(t => t.id || t.tagName);
          other.style.visibility = keep;
        }
      }
      return out;
    });
    await p.screenshot({ path: `${dir}/stacking-${id}.png` });
    for (const k of ['caption', 'tick-tip']) {
      ok(res[k].shown, `${id}: the ${NAME[k]} is showing`);
      for (const el of ['hover', 'card']) ok(!res[k][el].length, `${id}: #${el} over the ${NAME[k]} is on top${res[k][el].length ? ', but under ' + res[k][el].join(', ') : ''}`);
    }
  }
  await br.close();
})().catch(e => { console.log('FAIL ' + e.message); process.exit(1); });

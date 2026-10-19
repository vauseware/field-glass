// The unit panels (hover tip and card), moved over the chapter labels, must be topmost at every sampled point.
// The app moves the card back to its unit on the next frame, so each check samples inside one evaluate, before any frame.
// Run: bash fg.sh drive <dir> journeys/stacking.cjs
const puppeteer = require('puppeteer-core');
const [exe, base, dir] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const p = await br.newPage(); await p.setViewport({ width: 1536, height: 830, deviceScaleFactor: 1.25 });
  for (const [id, sel] of [['first-manassas', 'va33'], ['sidi-bou-zid', null], ['cowpens', 'howard']]) {
    await p.goto(`${base}#${id}${sel ? `@14:32,select=${sel}` : ''}`, { waitUntil: 'networkidle0' });
    await p.waitForFunction(() => document.querySelector('#splash').hidden && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 });
    await new Promise(r => setTimeout(r, 1500));
    const res = await p.evaluate(() => {
      const m = document.querySelector('#marks button').getBoundingClientRect(), out = {};
      const hv = document.querySelector('#hover'); hv.hidden = false; hv.innerHTML = '<b>Test</b><br>a unit<br>over the chapters'; hv.style.left = `${m.left}px`; hv.style.top = `${m.top - 60}px`; hv.style.pointerEvents = 'auto'; // elementFromPoint skips pointer-events: none
      const cd = document.querySelector('#card'); cd.style.opacity = 1; cd.style.pointerEvents = 'auto'; cd.style.transform = `translate(${m.left + 360}px, ${m.top - 80}px)`;
      for (const el of [hv, cd]) {
        const r = el.getBoundingClientRect();
        const pts = [[0.5, 0.5], [0.2, 0.8], [0.8, 0.8], [0.2, 0.2], [0.8, 0.2]].map(([fx, fy]) => document.elementFromPoint(r.left + r.width * fx, r.top + r.height * fy));
        out[el.id] = pts.filter(t => t && !el.contains(t)).map(t => t.id || t.tagName);
      }
      return out;
    });
    for (const k of ['hover', 'card']) ok(!res[k].length, `${id}: #${k} over the chapter labels is on top${res[k].length ? ', but under ' + res[k].join(', ') : ''}`);
  }
  await br.close();
})();

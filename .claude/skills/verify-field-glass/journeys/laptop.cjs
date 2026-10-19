// The target laptop: no page scroll, every control on screen, text 16 px or more, hit targets 44 px or more, and a canvas
// backed at the full device pixel ratio. Runs the start screen and one battle per skin at each viewport.
// Run: bash fg.sh drive <dir> journeys/laptop.cjs [battle ids, comma separated]
const puppeteer = require('puppeteer-core');
const [exe, base, dir, ids = 'cowpens,first-manassas,sidi-bou-zid'] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
const VIEWS = [{ width: 1536, height: 830, deviceScaleFactor: 1.25 }, { width: 1280, height: 700, deviceScaleFactor: 1.5 }];
const MIN_TEXT = 16, MIN_HIT = 44;

const audit = (MIN_TEXT, MIN_HIT) => {
  const W = innerWidth, H = innerHeight, de = document.documentElement;
  const splash = document.querySelector('#splash:not([hidden])'); // while it is up, the battle's controls lie unused behind it
  const shown = el => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.pointerEvents !== 'none' && !el.closest('[hidden]') && (!splash || splash.contains(el)); };
  const name = el => el.id ? `#${el.id}` : `${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/)[0] : ''}`;
  const small = new Map();
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = tw.nextNode());) {
    const el = n.parentElement, t = n.textContent.trim();
    if (!t || !el || !shown(el) || el.closest('script,style,option')) continue;
    const px = parseFloat(getComputedStyle(el).fontSize);
    if (px < MIN_TEXT - 0.01) { const k = `${name(el)} ${px}px`; if (!small.has(k)) small.set(k, t.slice(0, 30)); }
  }
  const hits = [...document.querySelectorAll('button, select, input:not([type=checkbox]), a[href], summary, [role=button], #splash .row, #bar label')].filter(shown).map(el => {
    const r = el.getBoundingClientRect();
    const over = [[0.5, 0.5], [0.25, 0.25], [0.75, 0.25], [0.25, 0.75], [0.75, 0.75]].map(([fx, fy]) => document.elementFromPoint(r.left + r.width * fx, r.top + r.height * fy))
      .find(t => t && !el.contains(t) && !t.contains(el));
    // the chapter marks slant at 50°, so their box samples bare map, and they overlap each other by design
    return { el: name(el), w: Math.round(r.width), h: Math.round(r.height), off: r.left < 0 || r.top < 0 || r.right > W + 0.5 || r.bottom > H + 0.5, hid: over && !el.closest('#marks') ? name(over) : null };
  });
  // #fx holds soft ambient textures, stretched on purpose
  const cv = [...document.querySelectorAll('canvas')].filter(c => shown(c) && !c.closest('#fx')).map(c => ({ el: name(c), want: Math.round(c.clientWidth * devicePixelRatio), have: c.width }));
  return { scroll: [de.scrollWidth - W, de.scrollHeight - H], small: [...small].map(([k, t]) => `${k} "${t}"`),
    tiny: hits.filter(h => h.w < MIN_HIT || h.h < MIN_HIT).map(h => `${h.el} ${h.w}x${h.h}`), off: hits.filter(h => h.off).map(h => h.el), covered: hits.filter(h => h.hid).map(h => `${h.el} under ${h.hid}`),
    canvases: cv.map(c => `${c.el} ${c.have}/${c.want}`), blurry: cv.filter(c => Math.abs(c.want - c.have) > 1).map(c => `${c.el} ${c.have} for ${c.want}`) };
};

(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const p = await br.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  const report = (tag, a) => {
    ok(a.scroll[0] <= 0 && a.scroll[1] <= 0, `${tag}: no page scroll (overflow ${a.scroll.join(' x ')} px)`);
    ok(!a.off.length, `${tag}: every control on screen${a.off.length ? ': ' + a.off.join(', ') : ''}`);
    ok(!a.covered.length, `${tag}: no control covered at its centre${a.covered.length ? ': ' + a.covered.join(', ') : ''}`);
    ok(!a.small.length, `${tag}: text ${MIN_TEXT} px or more${a.small.length ? ': ' + a.small.join('; ') : ''}`);
    ok(!a.tiny.length, `${tag}: hit targets ${MIN_HIT} px or more${a.tiny.length ? ': ' + a.tiny.join(', ') : ''}`);
    ok(a.canvases.length && !a.blurry.length, `${tag}: canvas at full DPR (${a.canvases.join(', ') || 'none found'})`);
  };
  for (const v of VIEWS) {
    await p.setViewport(v); const vt = `${v.width}x${v.height}@${v.deviceScaleFactor}`;
    await p.goto(`${base}#civil-war`, { waitUntil: 'networkidle0' }); await new Promise(r => setTimeout(r, 1500));
    await p.screenshot({ path: `${dir}/laptop-${vt}-start.png` });
    report(`${vt} start screen`, await p.evaluate(audit, MIN_TEXT, MIN_HIT));
    for (const id of ids.split(',')) {
      await p.goto(`${base}#${id}`, { waitUntil: 'networkidle0' });
      const t0 = Date.now();
      await p.waitForFunction(() => document.querySelector('#splash').hidden && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 });
      await new Promise(r => setTimeout(r, 1500));
      await p.screenshot({ path: `${dir}/laptop-${vt}-${id}.png` });
      report(`${vt} ${id} (opened in ${Date.now() - t0} ms)`, await p.evaluate(audit, MIN_TEXT, MIN_HIT));
    }
  }
  ok(!errs.length, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await br.close();
})();

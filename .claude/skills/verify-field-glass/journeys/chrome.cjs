// The battle chrome (#73, option B): the scrubber's width and the bar's height, how much of the window the chrome covers,
// the clock in the right of the window, a tick a chapter with the tip that names it, every caption page fitting the strip,
// and the volume sliders by pointer, keys and reload.
// Run: bash fg.sh drive <dir> journeys/chrome.cjs
const puppeteer = require('puppeteer-core');
const [exe, base, dir] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
const LAPTOP = { width: 1536, height: 830, deviceScaleFactor: 1.25 }, SMALL = { width: 1280, height: 700, deviceScaleFactor: 1.5 };
const vt = v => `${v.width}x${v.height}`;
const TICKS = ['sidi-bou-zid', 'new-orleans', 'antietam', 'somme'];

(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const p = await br.newPage(); await p.setViewport(LAPTOP);
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]); // page turns and fades land at once
  const shot = n => p.screenshot({ path: `${dir}/chrome-${n}.png` });
  const frames = n => p.evaluate(n => new Promise(r => { const f = () => (--n ? requestAnimationFrame(f) : r()); requestAnimationFrame(f); }), n);
  const open = async hash => {
    await p.goto('about:blank'); await p.goto(`${base}#${hash}`, { waitUntil: 'networkidle0' });
    await p.waitForFunction(() => window.fg && document.querySelector('#splash').hidden && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 });
    await p.evaluate(() => document.fonts.ready); await frames(3);
  };
  const titles = () => p.$$eval('#chapter-list .ch > button', bs => bs.map(b => b.lastChild.textContent)); // in the page's order, by time
  const row = async i => (await p.$$('#chapter-list .ch > button'))[i].click();
  const box = sel => p.$eval(sel, el => { const r = el.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height }; });

  // 1-3: the scrubber, the bar, the coverage and the clock's place
  for (const v of [LAPTOP, SMALL]) {
    await p.setViewport(v);
    await open('antietam@1862-09-17T08:00'); await p.click('#top-close'); await frames(3); await new Promise(r => setTimeout(r, 600));
    const scrub = await box('#scrub'), bar = await box('#bar'), clock = await box('#clock-box');
    const need = v.width === 1536 ? 1250 : 1000;
    ok(scrub.w >= need && bar.h <= 60, `${vt(v)}: the scrubber is ${Math.round(scrub.w)} px wide (at least ${need}), the bar ${bar.h} px high (at most 60)`);
    ok(clock.l >= 0.6 * v.width && clock.r <= v.width, `${vt(v)}: the clock cluster spans ${Math.round(clock.l)} to ${Math.round(clock.r)}, inside the right 40% (from ${0.6 * v.width})`);
    const cover = await p.evaluate(() => { // the visible [data-clear] rects, rasterised on a 4 px grid so overlaps count once
      const rs = [...document.querySelectorAll('[data-clear]')].filter(el => { const cs = getComputedStyle(el); return cs.visibility !== 'hidden' && +cs.opacity > 0; })
        .map(el => ({ id: el.id, r: el.getBoundingClientRect() }));
      let n = 0, all = 0;
      for (let y = 2; y < innerHeight; y += 4) for (let x = 2; x < innerWidth; x += 4) { all++; if (rs.some(({ r }) => x >= r.left && x < r.right && y >= r.top && y < r.bottom)) n++; }
      return { pct: (100 * n) / all, parts: rs.map(({ id, r }) => `${id} ${Math.round(r.width)}x${Math.round(r.height)}`) };
    });
    await shot(`1-antietam-0800-${vt(v)}`);
    if (v.width === 1536) ok(cover.pct <= 22 && cover.parts.some(s => s.startsWith('caption')), `${vt(v)} Antietam at 8 AM, drawer closed, caption showing: the chrome covers ${cover.pct.toFixed(1)}% of the window (at most 22%): ${cover.parts.join(', ')}`);
    else console.log(`note ${vt(v)} Antietam at 8 AM: the chrome covers ${cover.pct.toFixed(1)}%`);
  }

  // 4: a tick a chapter, no labels over the map, and the tip on a tick names it
  await p.setViewport(LAPTOP);
  for (const id of TICKS) {
    await open(id); const names = await titles(), n = names.length;
    await p.click('#top-close'); await frames(2);
    const st = await p.evaluate(() => {
      const bar = document.querySelector('#bar').getBoundingClientRect(), m = document.querySelector('#marks').getBoundingClientRect();
      return { buttons: document.querySelectorAll('#marks button, #marks [tabindex]').length, ticks: document.querySelectorAll('#marks i').length, rows: document.querySelectorAll('#chapter-list .ch').length,
        inBar: m.top >= bar.top && m.bottom <= bar.bottom && m.left >= bar.left && m.right <= bar.right };
    });
    const events = await p.evaluate(id => fetch(`battles/${id}/battle.json`).then(r => r.json()).then(b => b.events.length), id);
    ok(!st.buttons && st.inBar && st.ticks === events && st.rows === events, `${id}: ${st.ticks} ticks and ${st.rows} rows for ${events} chapters in battle.json, ticks inside the bar (${st.inBar}), none a control (${st.buttons})`);
    const xs = await p.$$eval('#marks i', is => is.map(i => { const r = i.getBoundingClientRect(); return (r.left + r.right) / 2; }));
    const sc = await box('#scrub'), y = (sc.t + sc.b) / 2;
    let pick = [0, n >> 1, n - 1];
    if (id === 'somme') { // its dense run: every tick closer than 12 px to the next
      const dense = xs.map((x, i) => i).filter(i => (i > 0 && xs[i] - xs[i - 1] < 12) || (i + 1 < n && xs[i + 1] - xs[i] < 12));
      pick = [...new Set([...pick, ...dense])];
    }
    const bad = [];
    for (const i of pick) {
      await p.mouse.move(xs[i], y); await frames(1);
      const tip = await p.evaluate(bar => { const t = document.querySelector('#tick-tip'), r = t.getBoundingClientRect(); return { hidden: t.hidden, text: t.textContent, bottom: r.bottom, bar }; }, (await box('#bar')).t);
      if (tip.hidden || !tip.text.startsWith(names[i]) || tip.text.length <= names[i].length || tip.bottom > tip.bar) bad.push(`${i}: "${tip.text}"${tip.hidden ? ' hidden' : ''}`);
    }
    if (id === 'somme') { await p.mouse.move(xs[pick.at(-1)], y); await frames(1); await shot('4-somme-tip'); }
    else if (id === 'antietam') { await p.mouse.move(xs[n >> 1], y); await frames(1); await shot('4-antietam-tip'); }
    ok(!bad.length, `${id}: the pointer on ${pick.length} ticks shows each one's name and time above the bar${bad.length ? '; wrong at ' + bad.join(', ') : ''}`);
    await p.mouse.move(sc.l + 40, sc.t - 120); await frames(1);
    ok(await p.$eval('#tick-tip', t => t.hidden), `${id}: the tip goes when the pointer leaves the scrubber`);
  }

  // 5: every page of every chapter fits the strip, unclipped, at both sizes, with the drawer closed and open
  for (const v of [LAPTOP, SMALL]) {
    await p.setViewport(v);
    for (const id of TICKS) {
      await open(id);
      const n = (await titles()).length, bad = [];
      let pages = 0, chapters = 0, grown = 0;
      for (const drawer of [true, false]) {
        for (let i = 0; i < n; i++) {
          if (!(await p.$eval('#top', t => t.classList.contains('open')))) await p.click('#chapters-btn');
          await row(i); await frames(2);
          if (!drawer) { await p.click('#top-close'); await frames(2); }
          const r = await p.evaluate(async () => {
            const { sentences } = await import('./sim.js');
            const cap = document.querySelector('#caption'), ps = [...document.querySelectorAll('#cap-text > p')], was = ps.map(q => q.hidden), out = [];
            const line = ps.length && parseFloat(getComputedStyle(ps[0]).lineHeight);
            ps.forEach((q, k) => { ps.forEach((o, j) => (o.hidden = j !== k)); const c = cap.getBoundingClientRect(), e = q.getBoundingClientRect();
              out.push({ len: q.textContent.length, clause: sentences(q.textContent).length === 1 && !/;\s/.test(q.textContent), lines: Math.round(q.offsetHeight / line), clipped: cap.scrollHeight > cap.clientHeight + 1 || e.bottom > c.bottom || e.top < c.top || q.scrollWidth > q.clientWidth + 1 }); });
            ps.forEach((q, j) => (q.hidden = was[j]));
            return { title: document.querySelector('#cap-title').textContent, out };
          });
          chapters++; pages += r.out.length;
          r.out.forEach((q, k) => { if (q.lines > 3 && q.clause) grown++; if (q.clipped || (q.lines > 3 && !q.clause) || (r.out.length > 1 && q.len < 25)) bad.push(`"${r.title}" page ${k + 1}/${r.out.length}: ${q.len} chars, ${q.lines} lines${q.clipped ? ', clipped' : ''}`); });
        }
      }
      ok(!bad.length && chapters === 2 * n, `${vt(v)} ${id}: ${pages} pages over ${chapters} chapter views (drawer open and closed) fit unclipped in three lines (${grown} grow past it, each one clause with no semicolon), none under 25 characters${bad.length ? '; but ' + bad.slice(0, 6).join('; ') : ''}`);
    }
  }
  await p.setViewport(LAPTOP);

  // 6: the volume sliders, by pointer, by keys, and kept on reload
  await p.goto(base, { waitUntil: 'networkidle0' }); await p.evaluate(() => localStorage.clear());
  await open('cowpens@07:45'); await p.click('#settings-btn'); await frames(2);
  const ids = ['#vol-sound', '#vol-music', '#vol-narration'], got = {};
  const start = await p.evaluate(ids => ids.map(s => +document.querySelector(s).value), ids);
  for (const s of ids) {
    const r = await box(s), th = 16; // the knob's width: the value runs from its half-width in from each end
    await p.mouse.click(r.l + th / 2 + 0.25 * (r.w - th), (r.t + r.b) / 2); await frames(1);
    const a = await p.$eval(s, el => +el.value);
    await p.keyboard.press('ArrowRight'); await p.keyboard.press('ArrowRight'); await p.keyboard.press('ArrowRight'); await frames(1);
    got[s] = [a, await p.$eval(s, el => +el.value)];
  }
  await shot('6-settings');
  ok(ids.every(s => Math.abs(got[s][0] - 25) <= 2 && got[s][1] === got[s][0] + 3), `the sliders start at ${start.join(', ')}; a click at a quarter of each gives ${ids.map(s => got[s][0]).join(', ')}, and three ArrowRight presses ${ids.map(s => got[s][1]).join(', ')}`);
  await p.reload({ waitUntil: 'networkidle0' }); await p.waitForFunction(() => document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 });
  const kept = await p.evaluate(ids => ({ vals: ids.map(s => +document.querySelector(s).value), stored: JSON.parse(localStorage.getItem('fieldglass.volume')) }), ids);
  ok(ids.every((s, i) => kept.vals[i] === got[s][1]) && kept.stored.sound === got['#vol-sound'][1] && kept.stored.music === got['#vol-music'][1] && kept.stored.narration === got['#vol-narration'][1],
    `after a reload the sliders read ${kept.vals.join(', ')}, and fieldglass.volume holds ${JSON.stringify(kept.stored)}`);
  await p.evaluate(() => localStorage.clear());

  ok(!errs.length, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await br.close();
})().catch(e => { console.log('FAIL ' + e.message); process.exit(1); });

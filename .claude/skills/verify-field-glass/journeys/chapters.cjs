// The Chapters switch and the chapter title: the switch's start by chapter count, click, `c`, the stored choice and
// blocked storage; the title on play, label click and page open, not on a drag or arrow key; its place at the laptop
// and phone sizes; the bar on one row; no title during the opening shot, and one when it ends or is skipped.
// Run: bash fg.sh drive <dir> journeys/chapters.cjs
// Timing checks read the page's own frames (per-frame opacity of #chapter-title), so a slow frame never fails them.
const puppeteer = require('puppeteer-core');
const [exe, base, dir] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
const wait = ms => new Promise(r => setTimeout(r, ms));
const LAPTOP = { width: 1536, height: 830, deviceScaleFactor: 1.25 }, SMALL = { width: 1280, height: 700, deviceScaleFactor: 1.5 }, PHONE = { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true };
const SBZ = 'sidi-bou-zid@1943-02-14T10:00';

(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const errs = [];
  const page = async (blocked = false) => {
    const p = await br.newPage(); await p.setViewport(LAPTOP);
    p.on('pageerror', e => errs.push(e.message));
    await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);
    if (blocked) await p.evaluateOnNewDocument(() => Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('blocked', 'SecurityError'); } }));
    return p;
  };
  let p = await page();
  const shot = n => p.screenshot({ path: `${dir}/chapters-${n}.png` });
  const frames = n => p.evaluate(n => new Promise(r => { const f = () => (--n ? requestAnimationFrame(f) : r()); requestAnimationFrame(f); }), n);
  const open = async hash => {
    await p.goto('about:blank'); await p.goto(`${base}#${hash}`, { waitUntil: 'networkidle0' });
    await p.waitForFunction(() => window.fg && document.querySelector('#splash').hidden && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 });
    await frames(3);
  };
  const blur = () => p.evaluate(() => document.activeElement?.blur());
  const labels = () => p.evaluate(() => ({ checked: document.querySelector('#chapters').checked,
    shown: [...document.querySelectorAll('#marks button')].filter(b => !b.hidden && b.getBoundingClientRect().width).length,
    ticks: [...document.querySelectorAll('#marks path')].filter(l => /^M[\d.]+ 23V15/.test(l.getAttribute('d'))).length, chapters: document.querySelectorAll('#marks button').length }));
  const record = () => p.evaluate(() => {
    window.trec = [];
    const el = document.querySelector('#chapter-title');
    const f = () => {
      const cs = getComputedStyle(el), s = fg.state();
      trec.push({ now: performance.now(), op: cs.visibility === 'hidden' ? 0 : +cs.opacity, text: el.textContent, t: s.t, opening: !!s.opening, cap: document.querySelector('#cap-title').textContent });
      requestAnimationFrame(f);
    };
    requestAnimationFrame(f);
  });
  const log = () => p.evaluate(() => trec);
  const rises = R => R.filter((r, i) => i && r.op > 0 && R[i - 1].op === 0).length;
  const battle = id => p.evaluate(id => fetch(`battles/${id}/battle.json`).then(r => r.json()), id);
  await p.goto(base, { waitUntil: 'networkidle0' }); await p.evaluate(() => localStorage.clear());

  // 1: no stored choice
  await open('cowpens@07:45'); const c1 = await labels(); await shot('1-cowpens-on');
  await open(SBZ); const s1 = await labels(); await shot('1-sbz-off');
  ok(c1.checked && c1.shown > 0 && !s1.checked && s1.shown === 0,
    `no stored choice: Cowpens (${c1.chapters} chapters) checked ${c1.checked}, ${c1.shown} labels; Sidi Bou Zid (${s1.chapters}) checked ${s1.checked}, ${s1.shown} labels`);

  // 2-3: click and the c key
  await open('cowpens@07:45'); await p.click('#chapters'); await frames(2); const c2 = await labels(); await shot('2-cowpens-off');
  ok(!c2.checked && c2.shown === 0 && c2.ticks === c2.chapters, `a click on Chapters: checked ${c2.checked}, ${c2.shown} labels, ${c2.ticks} of ${c2.chapters} ticks left`);
  await blur(); await p.keyboard.press('c'); await frames(2); const c3 = await labels();
  ok(c3.checked && c3.shown === c1.shown, `c turns them back on: checked ${c3.checked}, ${c3.shown} labels`);

  // 4: the choice is kept
  await p.click('#chapters'); await p.reload({ waitUntil: 'networkidle0' });
  await p.waitForFunction(() => document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 }); await frames(2); const c4 = await labels();
  await open(SBZ); await p.click('#chapters'); await open('cowpens@07:45'); const c4b = await labels();
  ok(!c4.checked && c4.shown === 0 && c4b.checked && c4b.shown > 0, `off on Cowpens, reloaded: checked ${c4.checked}; on on Sidi Bou Zid, then Cowpens: checked ${c4b.checked}, ${c4b.shown} labels`);
  await p.evaluate(() => localStorage.clear());

  // 5: storage blocked
  const p0 = p; p = await page(true);
  await open('cowpens@07:45'); const b1 = await labels(); await open(SBZ); const b2 = await labels();
  await p.click('#chapters'); await frames(2); const b3 = await labels();
  const thrown = await p.evaluate(() => { try { localStorage; return false; } catch { return true; } });
  ok(thrown && b1.checked && !b2.checked && b3.checked && b3.shown > 0, `storage blocked (${thrown}): Cowpens checked ${b1.checked}, Sidi Bou Zid ${b2.checked}, after a click ${b3.checked} with ${b3.shown} labels`);
  await p.close(); p = p0;

  // 6: play across a chapter at 20x
  const cow = await battle('cowpens'), adv = cow.events[3];
  await open('cowpens@07:14:30'); await wait(4000); await record();
  await p.select('#speed', '20'); await p.click('#play'); await wait(6500);
  let R = await log();
  const cross = R.find(r => r.text === adv.title && r.op > 0), within = cross && R.filter(r => r.now - cross.now <= 1000), late = cross && R.find(r => r.now - cross.now >= 4000);
  ok(cross && Math.max(...within.map(r => r.op)) > 0.9 && late && late.op === 0,
    `play into "${adv.title}" at 20x: opacity ${cross && Math.max(...within.map(r => r.op)).toFixed(2)} within 1 s, ${late?.op} at ${late && ((late.now - cross.now) / 1000).toFixed(2)} s, text "${cross?.text}"`);

  // 7: a drag on the scrubber and the arrow keys
  await open('cowpens@07:00'); await wait(4000); await record();
  const sc = await p.$eval('#scrub', el => { const r = el.getBoundingClientRect(); return { l: r.left, w: r.width, y: r.top + r.height / 2, min: +el.min, max: +el.max, v: +el.value }; });
  const xAt = v => sc.l + 13 + ((v - sc.min) / (sc.max - sc.min)) * (sc.w - 26), toT = s => { const [h, m] = s.split(':').map(Number); return h * 3600 + m * 60; };
  await p.mouse.move(xAt(sc.v), sc.y); await p.mouse.down();
  for (let i = 1; i <= 20; i++) { await p.mouse.move(xAt(sc.v + ((toT('07:28') - sc.v) * i) / 20), sc.y); await frames(2); }
  await p.mouse.up(); await blur();
  for (let i = 0; i < 6; i++) { await p.keyboard.press('ArrowRight'); await frames(3); }
  await wait(1000); R = await log();
  const caps = [...new Set(R.map(r => r.cap))];
  ok(caps.length >= 4 && R.every(r => r.op === 0), `drag and arrow keys through ${caps.length - 1} chapter changes (${caps.join(' > ')}): highest title opacity ${Math.max(...R.map(r => r.op))}`);

  // 8: a click on a chapter label
  await record();
  const lab = await p.evaluate(() => { const b = [...document.querySelectorAll('#marks button')].filter(b => !b.hidden && !b.classList.contains('on'))[1]; b.id = 'pick'; return b.textContent; });
  await p.click('#pick'); await wait(1000); R = await log(); await shot('8-label-click');
  ok(R.some(r => r.text === lab && r.op > 0.9), `a click on "${lab}": title "${R.at(-1).text}", opacity up to ${Math.max(...R.map(r => r.op)).toFixed(2)} within 1 s`);

  // 9: the title's place
  const place = () => p.evaluate(() => {
    const el = document.querySelector('#chapter-title'), r = el.getBoundingClientRect(), cut = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
    const panels = ['#top', '#bar', '#caption', '#card'].map(s => document.querySelector(s)).filter(e => +getComputedStyle(e).opacity > 0 && e.getBoundingClientRect().width);
    const marks = [...document.querySelectorAll('#marks button')].filter(b => !b.hidden && b.getBoundingClientRect().width).map(b => b.getBoundingClientRect());
    const phone = innerWidth <= 640, cap = document.querySelector('#caption').getBoundingClientRect();
    const anchor = phone ? cap.top : marks.length ? Math.min(...marks.map(m => m.top)) : document.querySelector('#bar').getBoundingClientRect().top;
    return { op: +getComputedStyle(el).opacity, box: [r.left, r.top, r.right, r.bottom].map(Math.round), gap: Math.round(anchor - r.bottom), marks: marks.length,
      over: [...panels.filter(e => cut(r, e.getBoundingClientRect())).map(e => '#' + e.id), ...marks.filter(m => cut(r, m)).map(() => 'label')] };
  });
  for (const v of [LAPTOP, SMALL, PHONE]) {
    await p.setViewport(v); const vt = `${v.width}x${v.height}`;
    for (const h of ['cowpens@07:45', SBZ]) {
      await p.evaluate(() => localStorage.clear()); await open(`${h},warp,title`);
      const id = h.split('@')[0];
      for (const turn of [false, true]) {
        if (turn) { await blur(); await p.keyboard.press('c'); await frames(2); }
        const a = await place(), sh = `9-${id}-${vt}-${a.marks ? 'on' : 'off'}`; await shot(sh);
        ok(a.op === 1 && !a.over.length && a.gap >= 0 && a.gap <= 30, `${vt} ${id}, ${a.marks} labels: title ${a.box.join(',')}, ${a.gap} px above ${v === PHONE ? 'the story' : a.marks ? 'the labels' : 'the bar'}${a.over.length ? ', over ' + a.over.join(' ') : ', over nothing'}`);
      }
    }
  }
  await p.evaluate(() => localStorage.clear());

  // 10: the bar on one row at the laptop sizes
  for (const v of [LAPTOP, SMALL]) {
    await p.setViewport(v); await open('antietam@1862-09-17T09:00');
    const b = await p.evaluate(() => {
      const kids = [...document.querySelector('#bar').children].map(e => e.getBoundingClientRect()), lab = document.querySelector('#bar label.chapters').getBoundingClientRect();
      return { rows: Math.max(...kids.map(k => k.top)) < Math.min(...kids.map(k => k.bottom)), lab: [Math.round(lab.width), Math.round(lab.height)], right: Math.round(lab.right) };
    });
    await shot(`10-bar-${v.width}x${v.height}`);
    ok(b.rows && b.lab[1] >= 44 && b.right <= v.width, `${v.width}x${v.height}@${v.deviceScaleFactor} Antietam: the bar on one row (${b.rows}), Chapters ${b.lab.join('x')} ending at ${b.right}`);
  }
  await p.setViewport(LAPTOP);

  // 11: the opening shot
  await p.goto('about:blank'); await p.goto(base, { waitUntil: 'networkidle0' });
  await p.waitForFunction(() => window.fg && document.querySelector('.row[data-id="cowpens"]'), { timeout: 60000 });
  await record(); await p.click('.row[data-id="cowpens"]');
  await p.waitForFunction(() => trec.some(r => r.opening) && !fg.state().opening, { timeout: 60000, polling: 'raf' });
  await wait(4500); R = await log();
  const during = R.filter(r => r.opening), end = R.findIndex((r, i) => i && !r.opening && R[i - 1].opening), firstUp = R.slice(end).find(r => r.op > 0.9);
  const upIn = firstUp ? ((firstUp.now - R[end].now) / 1000).toFixed(2) : '-';
  const a1 = during.length > 100 && during.every(r => r.op === 0) && firstUp && +upIn <= 1 && firstUp.text === cow.events[0].title && rises(R) === 1;
  await open('cowpens'); await wait(4000); await record(); await p.click('#play');
  await p.waitForFunction(() => fg.state().opening?.e >= 2, { polling: 'raf' }); await p.mouse.click(60, 415); await wait(1200); R = await log();
  const skip = R.findIndex((r, i) => i && !r.opening && R[i - 1].opening), skipUp = R.slice(skip).find(r => r.op > 0.9);
  const a2 = R.filter(r => r.opening).every(r => r.op === 0) && skipUp && skipUp.now - R[skip].now <= 1000 && rises(R) === 1;
  await open('cowpens,opening'); await record(); await wait(1500); R = await log();
  const a3 = R.every(r => r.op === 0 && r.opening); await shot('11-opening-held');
  await open('cowpens@07:45,play,warp'); await record(); await wait(2500); R = await log();
  const a4 = R.length > 60 && R.every(r => r.op === 0);
  ok(a1 && a2 && a3 && a4, `opening from the start screen: title 0 over ${during.length} frames, then "${firstUp?.text}" ${upIn} s after it ends, shown once (${a1}); skipped by a click: shown once after (${a2}); ,opening holds with no title (${a3}); ,play,warp shows none (${a4})`);

  // 12: reduced motion
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  await open('cowpens@07:45'); await wait(4000); await record();
  await p.evaluate(() => { const b = [...document.querySelectorAll('#marks button')].find(b => !b.hidden && !b.classList.contains('on')); b.id = 'pick'; });
  await p.click('#pick'); await wait(4200); R = await log();
  ok(R.some(r => r.op === 1) && R.every(r => r.op === 0 || r.op === 1) && R.at(-1).op === 0, `reduced motion: opacities ${[...new Set(R.map(r => r.op))].join(', ')} only, ${R.filter(r => r.op === 1).length} frames shown, then gone`);

  ok(!errs.length, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await br.close();
})().catch(e => { console.log('FAIL ' + e.message); process.exit(1); });

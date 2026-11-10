// The drawer and its chapter list, the Settings panel and its stored switches, and the chapter title: a row click, Play and
// Esc on the drawer and Settings; Chapter titles (key c) and Captions kept across reloads and through blocked storage; the
// title on play, a row click and page open, not on a drag or arrow key; its place at the laptop sizes; no title during
// the opening shot, and one when it ends or is skipped; reduced motion.
// Run: bash fg.sh drive <dir> journeys/chapters.cjs
// Timing checks read the page's own frames (per-frame opacity of #chapter-title), so a slow frame never fails them.
const puppeteer = require('puppeteer-core');
const [exe, base, dir] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
const wait = ms => new Promise(r => setTimeout(r, ms));
const LAPTOP = { width: 1536, height: 830, deviceScaleFactor: 1.25 }, SMALL = { width: 1280, height: 700, deviceScaleFactor: 1.5 };
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
  const reload = async () => { await p.reload({ waitUntil: 'networkidle0' }); await p.waitForFunction(() => document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 }); await frames(3); };
  const blur = () => p.evaluate(() => document.activeElement?.blur());
  const row = async i => (await p.$$('#chapter-list .ch > button'))[i].click();
  const state = () => p.evaluate(() => ({ open: document.querySelector('#top').classList.contains('open'), settings: !document.querySelector('#settings').hidden,
    titles: document.querySelector('#titles').checked, captions: document.querySelector('#captions').checked, capVis: getComputedStyle(document.querySelector('#caption')).visibility,
    stored: (() => { try { return [localStorage.getItem('fieldglass.titles'), localStorage.getItem('fieldglass.captions')]; } catch { return 'blocked'; } })() }));
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

  // 1: a row click seeks to its chapter, turns Follow on and opens the row with the whole story; the drawer stays open
  const anti = await battle('antietam');
  await open('antietam@1862-09-17T07:00'); await blur(); await p.keyboard.press('f'); await frames(2);
  const before = await p.evaluate(() => fg.state());
  await record(); await row(8); await wait(1000);
  const r1 = await p.evaluate(() => {
    const on = document.querySelector('#chapter-list .ch.on'), story = on?.querySelector('p'), L = document.querySelector('#chapter-list').getBoundingClientRect(), r = on?.getBoundingClientRect();
    return { t: fg.state().t, follow: fg.state().follow, name: on?.querySelector('button').lastChild.textContent, story: story && getComputedStyle(story).display !== 'none' ? story.textContent : null,
      open: document.querySelector('#top').classList.contains('open'), count: document.querySelector('#ch-count').textContent, days: [...document.querySelectorAll('#chapter-list .day')].map(d => d.textContent),
      inList: r && r.top >= L.top - 1 && r.top < L.bottom };
  });
  const ev8 = anti.events.map(e => ({ ...e, t: Date.parse(`${e.t.replace(' ', 'T')}Z`) / 1000 })).sort((a, b) => a.t - b.t)[8];
  let R = await log(); await shot('1-row-click');
  ok(!before.follow && r1.t === ev8.t && r1.follow && r1.name === ev8.title && r1.story === ev8.text && r1.open && r1.inList,
    `Antietam, Follow off (${before.follow}), a click on row 9: the clock at ${r1.t} (chapter start ${ev8.t}), Follow ${r1.follow}, the row "${r1.name}" open with its whole story (${r1.story?.length} of ${ev8.text.length} characters), drawer open (${r1.open})`);
  ok(R.some(r => r.text === ev8.title && r.op > 0.9), `the row click shows the title "${ev8.title}" within 1 s (opacity up to ${Math.max(...R.map(r => r.op)).toFixed(2)})`);
  ok(r1.count === 'Chapters 9 of 24' && r1.days.length >= 2 && r1.days.every(d => /^\d+ [A-Z][a-z]{2}$/.test(d)),
    `the heading counts "${r1.count}"; the multi-day list has day headings ${r1.days.join(', ')}`);
  await row(23); await frames(3);
  const last = await p.evaluate(() => { const L = document.querySelector('#chapter-list').getBoundingClientRect(), r = document.querySelector('#chapter-list .ch.on').getBoundingClientRect();
    return { box: [r.top, r.bottom].map(Math.round), list: [L.top, L.bottom].map(Math.round), count: document.querySelector('#ch-count').textContent, scroll: document.documentElement.scrollTop + document.body.scrollTop }; });
  ok(last.box[0] >= last.list[0] - 1 && last.box[0] < last.list[1] && !last.scroll, `a click on the last row: "${last.count}", its row at ${last.box.join('-')} inside the list ${last.list.join('-')}, the page unscrolled (${last.scroll})`);

  // 2: Play closes the drawer and a pause leaves it shut; Chapters reopens it; Esc closes Settings, then the drawer
  await p.click('#play'); await frames(2); const a2 = await state();
  await p.click('#play'); await p.click('#chapters-btn'); await frames(2); const b2 = await state();
  await p.click('#settings-btn'); await frames(2); await p.focus('#captions'); const c2 = await state();
  await p.keyboard.press('Escape'); await frames(2); const d2 = await state();
  await p.keyboard.press('Escape'); await frames(2); const e2 = await state(); await shot('2-closed');
  ok(!a2.open && b2.open && c2.settings && !d2.settings && d2.open && !e2.open,
    `Play closes the drawer (${!a2.open}); Chapters opens it (${b2.open}); with Settings open and #captions focused, Esc closes Settings (${!d2.settings}) and leaves the drawer (${d2.open}); Esc again closes the drawer (${!e2.open})`);
  await p.click('#settings-btn'); await frames(2); const f2 = await state();
  await p.mouse.click(700, 300); await frames(2); const g2 = await state();
  ok(f2.settings && !g2.settings, `Settings opens over its button (${f2.settings}) and a click on the map closes it (${!g2.settings})`);

  // 3: c turns Chapter titles off, kept on reload; titles off shows none when play runs into a chapter
  const cow = await battle('cowpens'), adv = cow.events[3];
  await open('cowpens@07:14:30'); await blur(); await p.keyboard.press('c'); await frames(2); const a3 = await state();
  await open('cowpens@07:14:30'); const b3 = await state(); // a fresh load, which reads the stored choice
  await p.select('#speed', '20'); await record(); await p.click('#play'); await wait(6500); R = await log();
  ok(!a3.titles && a3.stored[0] === 'off' && !b3.titles && R.some(r => r.cap === adv.title) && R.every(r => r.op === 0),
    `c turns Chapter titles off (${!a3.titles}, stored ${a3.stored[0]}); after a reload still off (${!b3.titles}); play into "${adv.title}" shows no title (highest opacity ${Math.max(...R.map(r => r.op))})`);
  await blur(); await p.keyboard.press('c'); await frames(2); const c3 = await state();
  ok(c3.titles && c3.stored[0] === 'on', `c turns them back on (${c3.titles}, stored ${c3.stored[0]})`);

  // 4: Captions hides the strip, kept on reload
  await open('cowpens@07:45'); await p.click('#settings-btn'); await p.click('#captions'); await frames(2); const a4 = await state(); await shot('4-captions-off');
  await reload(); const b4 = await state();
  await p.click('#settings-btn'); await p.click('#captions'); await frames(2); const c4 = await state();
  ok(!a4.captions && a4.capVis === 'hidden' && a4.stored[1] === 'off' && !b4.captions && b4.capVis === 'hidden' && c4.captions && c4.capVis === 'visible',
    `Captions off hides the strip (${a4.capVis}, stored ${a4.stored[1]}); after a reload still hidden (${b4.capVis}); on again shows it (${c4.capVis})`);
  await p.evaluate(() => localStorage.clear());

  // 5: storage blocked
  const p0 = p; p = await page(true);
  await open('cowpens@07:45'); const a5 = await state();
  await blur(); await p.keyboard.press('c'); await p.click('#settings-btn'); await p.click('#captions'); await frames(2); const b5 = await state();
  ok(a5.stored === 'blocked' && a5.titles && a5.captions && !b5.titles && !b5.captions, `storage blocked: opens with Chapter titles and Captions on (${a5.titles}, ${a5.captions}); c and a click turn them off (${!b5.titles}, ${!b5.captions})`);
  await p.close(); p = p0;

  // 6: play across a chapter at 20x
  await open('cowpens@07:14:30'); await wait(4000); await record();
  await p.select('#speed', '20'); await p.click('#play'); await wait(6500);
  R = await log();
  const cross = R.find(r => r.text === adv.title && r.op > 0), within = cross && R.filter(r => r.now - cross.now <= 1000), late = cross && R.find(r => r.now - cross.now >= 4000);
  ok(cross && Math.max(...within.map(r => r.op)) > 0.9 && late && late.op === 0,
    `play into "${adv.title}" at 20x: opacity ${cross && Math.max(...within.map(r => r.op)).toFixed(2)} within 1 s, ${late?.op} at ${late && ((late.now - cross.now) / 1000).toFixed(2)} s, text "${cross?.text}"`);

  // 7: a drag on the scrubber and the arrow keys
  await open('cowpens@07:00'); await wait(4000); await record();
  const sc = await p.$eval('#scrub', el => { const r = el.getBoundingClientRect(), th = parseFloat(getComputedStyle(el.parentElement).getPropertyValue('--thumb'));
    return { l: r.left, w: r.width, th, y: r.top + r.height / 2, min: +el.min, max: +el.max, v: +el.value }; });
  const xAt = v => sc.l + sc.th / 2 + ((v - sc.min) / (sc.max - sc.min)) * (sc.w - sc.th), toT = s => { const [h, m] = s.split(':').map(Number); return h * 3600 + m * 60; };
  await p.mouse.move(xAt(sc.v), sc.y); await p.mouse.down();
  for (let i = 1; i <= 20; i++) { await p.mouse.move(xAt(sc.v + ((toT('07:28') - sc.v) * i) / 20), sc.y); await frames(2); }
  await p.mouse.up(); await blur();
  for (let i = 0; i < 6; i++) { await p.keyboard.press('ArrowRight'); await frames(3); }
  await wait(1000); R = await log();
  const caps = [...new Set(R.map(r => r.cap))];
  ok(caps.length >= 4 && R.every(r => r.op === 0), `drag and arrow keys through ${caps.length - 1} chapter changes (${caps.join(' > ')}): highest title opacity ${Math.max(...R.map(r => r.op))}`);

  // 8: the title's place: above the strip, or the bar with Captions off, clear of every panel; narrowed past the open drawer
  const place = () => p.evaluate(() => {
    const el = document.querySelector('#chapter-title'), r = el.getBoundingClientRect(), cut = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
    const vis = e => { const cs = getComputedStyle(e); return +cs.opacity > 0 && cs.visibility !== 'hidden' && e.getBoundingClientRect().width; };
    const panels = [...document.querySelectorAll('[data-clear], #card, #settings')].filter(vis);
    const cap = document.querySelector('#caption'), anchor = (vis(cap) ? cap : document.querySelector('#bar')).getBoundingClientRect().top;
    return { op: +getComputedStyle(el).opacity, box: [r.left, r.top, r.right, r.bottom].map(Math.round), gap: Math.round(anchor - r.bottom), under: vis(cap) ? 'the strip' : 'the bar',
      over: panels.filter(e => cut(r, e.getBoundingClientRect())).map(e => '#' + e.id), drawer: document.querySelector('#top').classList.contains('open'), right: Math.round(document.querySelector('#top').getBoundingClientRect().right) };
  });
  for (const v of [LAPTOP, SMALL]) {
    await p.setViewport(v); const vt = `${v.width}x${v.height}`;
    for (const h of ['cowpens@07:45', SBZ]) {
      const id = h.split('@')[0];
      for (const play of [true, false]) {
        await p.evaluate(() => localStorage.clear()); await open(`${h}${play ? ',play' : ''},warp,title`);
        for (const capsOff of [false, true]) {
          if (capsOff) { await p.click('#settings-btn'); await p.click('#captions'); await p.keyboard.press('Escape'); await frames(2); }
          const a = await place(), sh = `8-${id}-${vt}-${a.drawer ? 'drawer' : 'closed'}-${a.under === 'the bar' ? 'bar' : 'strip'}`; await shot(sh);
          ok(a.op === 1 && !a.over.length && a.gap >= 0 && a.gap <= 30 && (!a.drawer || a.box[0] >= a.right),
            `${vt} ${id}, drawer ${a.drawer ? 'open' : 'closed'}: title ${a.box.join(',')}, ${a.gap} px above ${a.under}${a.drawer ? `, right of the drawer (${a.right})` : ''}${a.over.length ? ', over ' + a.over.join(' ') : ', over nothing'}`);
        }
      }
    }
  }
  await p.evaluate(() => localStorage.clear());
  await p.setViewport(LAPTOP);

  // 9: the opening shot
  await p.goto('about:blank'); await p.goto(base, { waitUntil: 'networkidle0' });
  await p.waitForFunction(() => window.fg && document.querySelector('.row[data-id="cowpens"]'), { timeout: 60000 });
  await record(); await p.click('.row[data-id="cowpens"]');
  await p.waitForFunction(() => trec.some(r => r.opening) && !fg.state().opening, { timeout: 60000, polling: 'raf' });
  await wait(4500); R = await log();
  const during = R.filter(r => r.opening), end = R.findIndex((r, i) => i && !r.opening && R[i - 1].opening), firstUp = R.slice(end).find(r => r.op > 0.9);
  const upIn = firstUp ? ((firstUp.now - R[end].now) / 1000).toFixed(2) : '-';
  const o1 = during.length > 100 && during.every(r => r.op === 0) && firstUp && +upIn <= 1 && firstUp.text === cow.events[0].title && rises(R) === 1;
  await open('cowpens'); await wait(4000); await record(); await p.click('#play');
  await p.waitForFunction(() => fg.state().opening?.e >= 2, { polling: 'raf' }); await p.mouse.click(60, 415); await wait(1200); R = await log();
  const skip = R.findIndex((r, i) => i && !r.opening && R[i - 1].opening), skipUp = R.slice(skip).find(r => r.op > 0.9);
  const o2 = R.filter(r => r.opening).every(r => r.op === 0) && skipUp && skipUp.now - R[skip].now <= 1000 && rises(R) === 1;
  await open('cowpens,opening'); await record(); await wait(1500); R = await log();
  const o3 = R.every(r => r.op === 0 && r.opening); await shot('9-opening-held');
  await open('cowpens@07:45,play,warp'); await record(); await wait(2500); R = await log();
  const o4 = R.length > 60 && R.every(r => r.op === 0);
  ok(o1 && o2 && o3 && o4, `opening from the start screen: title 0 over ${during.length} frames, then "${firstUp?.text}" ${upIn} s after it ends, shown once (${o1}); skipped by a click: shown once after (${o2}); ,opening holds with no title (${o3}); ,play,warp shows none (${o4})`);

  // 10: reduced motion
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  await open('cowpens@07:45'); await wait(4000); await record();
  await row(5); await wait(4200); R = await log();
  ok(R.some(r => r.op === 1) && R.every(r => r.op === 0 || r.op === 1) && R.at(-1).op === 0, `reduced motion: opacities ${[...new Set(R.map(r => r.op))].join(', ')} only, ${R.filter(r => r.op === 1).length} frames shown, then gone`);

  ok(!errs.length, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await br.close();
})().catch(e => { console.log('FAIL ' + e.message); process.exit(1); });

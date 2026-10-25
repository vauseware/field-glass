// The opening shot: the whole field, the title, the camera closing in, the clock held until it lands; what starts it and
// what skips it; reduced motion; the dawn cap on the night wash; the title at the laptop sizes. Then the field, title and
// landing frames of each battle named, shot at fixed moments. `clip` also writes 15 fps frames of the first battle's
// opening to <dir>/clip/ for ffmpeg.
// Run: bash fg.sh drive <dir> journeys/opening.cjs [battle ids, default cowpens,sidi-bou-zid] [clip]
// The page exposes window.fg only under navigator.webdriver: fg.state() reads the camera and clock, fg.hold(e) holds the
// opening at e seconds. Timing checks read the page's own frames, so a slow frame never fails them.
const puppeteer = require('puppeteer-core');
const [exe, base, dir, ids = 'cowpens,sidi-bou-zid', clip] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
const wait = ms => new Promise(r => setTimeout(r, ms));
const f2 = v => (v == null ? '-' : v.toFixed(2));

(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const p = await br.newPage(); await p.setViewport({ width: 1536, height: 830 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]); // the host's own setting may ask for reduced motion
  const shot = (n, o = {}) => p.screenshot({ path: `${dir}/opening-${n}.png`, ...o });
  const frames = n => p.evaluate(n => new Promise(r => { const f = () => (--n ? requestAnimationFrame(f) : r()); requestAnimationFrame(f); }), n);
  const st = () => p.evaluate(() => fg.state());
  const open = async hash => {
    await p.goto('about:blank'); await p.goto(`${base}${hash}`, { waitUntil: 'networkidle0' });
    await p.waitForFunction(() => window.fg && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 });
    await frames(2);
  };
  const battle = id => p.evaluate(id => fetch(`battles/${id}/battle.json`).then(r => r.json()), id);
  // one entry per frame: the opening's clock, the battle clock, the camera, the title's opacity and the panels' state
  const record = () => p.evaluate(() => {
    window.rec = [];
    const title = document.querySelector('#opening'), bar = document.querySelector('#bar');
    const f = () => {
      const s = fg.state();
      rec.push({ now: performance.now(), e: s.opening?.e ?? null, wide: s.opening?.wide, target: s.opening?.target, t: s.t, cam: s.cam, playing: s.playing,
        op: title.hidden ? 0 : +getComputedStyle(title).opacity, text: document.querySelector('#op-name').textContent, cls: document.body.classList.contains('opening'), bar: getComputedStyle(bar).filter });
      requestAnimationFrame(f);
    };
    requestAnimationFrame(f);
  });
  const log = () => p.evaluate(() => rec);
  const px = (a, b) => Math.max(Math.abs(a.x - b.x) * b.zoom, Math.abs(a.y - b.y) * b.zoom, Math.abs(a.zoom / b.zoom - 1) * 1536); // how far apart two frames are, in screen pixels at 1536 wide
  const panelsBack = () => p.evaluate(() => ['#top', '#bar', '#caption'].map(s => getComputedStyle(document.querySelector(s))).every(cs => cs.filter === 'none' && cs.pointerEvents !== 'none'));

  // 1-3: from the start screen
  await p.goto(base, { waitUntil: 'networkidle0' });
  const cow = await battle('cowpens');
  await p.waitForFunction(() => window.fg && document.querySelector('.row[data-id="cowpens"]'), { timeout: 60000 });
  await record();
  await p.click('.row[data-id="cowpens"]');
  await p.waitForFunction(() => fg.state().opening, { timeout: 60000 });
  const clock0 = await p.$eval('#clock', el => el.textContent);
  await p.waitForFunction(() => !fg.state().opening && fg.state().t > rec.find(r => r.e != null).t, { timeout: 30000, polling: 'raf' });
  await wait(1400);
  const back1 = await panelsBack();
  const L = await log(), first = L.findIndex(r => r.e != null), run = L.slice(first).filter(r => r.e != null), land = L.findIndex((r, i) => i > first && r.e == null);
  const o0 = run[0], startT = o0.t, moved = L.findIndex((r, i) => i > first && r.t !== startT);
  const wideZ = Math.min(1536, 830) / cow.extent;
  ok(o0.cls && o0.bar === 'opacity(0)' && Math.abs(o0.cam.zoom / wideZ - 1) < 1e-9 && run.every(r => r.t === startT) && L[moved].now - o0.now >= 9000,
    `choosing Cowpens: panels hidden (${o0.bar}), zoom ${o0.cam.zoom.toFixed(5)} = wide ${wideZ.toFixed(5)}, clock held at ${clock0} for ${((L[moved].now - o0.now) / 1000).toFixed(2)} s (opening e 0 to ${f2(run.at(-1).e)})`);
  const at3 = run.reduce((a, r) => (Math.abs(r.e - 3) < Math.abs(a.e - 3) ? r : a)), at55 = run.find(r => r.e >= 5.5);
  ok(at3.op > 0.95 && at3.text === cow.name && at55 && at55.op === 0, `title at e ${f2(at3.e)}: opacity ${at3.op}, "${at3.text}"; at e ${f2(at55?.e)}: opacity ${at55?.op}`);
  const target = run.at(-1).target, after = L[land];
  ok(px(after.cam, target) < 1 && !after.cls && back1 && L[moved].t > startT,
    `landing (first frame after e ${f2(run.at(-1).e)}): camera ${px(after.cam, target).toFixed(3)} px from the follow target, panels back (${back1}), clock ${startT} -> ${L.at(-1).t}`);
  const easing = run.filter(r => r.e > 5.2 && r.e < 9.2), steady = easing.every((r, i) => !i || (r.cam.zoom >= easing[i - 1].cam.zoom) === (target.zoom >= o0.cam.zoom));
  ok(easing.length > 30 && steady, `the ease is one move: ${easing.length} frames, zoom ${o0.cam.zoom.toFixed(4)} -> ${target.zoom.toFixed(4)} without turning back`);

  // 4: what does not start it, and what does
  await open('#cowpens@07:45'); await record(); await p.click('#play'); await wait(1500);
  let R = await log();
  const late = !R.some(r => r.e != null) && R.at(-1).t > R[0].t;
  await open('#cowpens'); await record();
  await p.$eval('#scrub', el => { el.value = String(+el.min + (+el.max - +el.min) / 3); el.dispatchEvent(new Event('input', { bubbles: true })); });
  await p.click('#play'); await wait(1500); R = await log();
  const seeked = !R.some(r => r.e != null) && R.at(-1).t > R[0].t;
  await open('#cowpens'); await record(); await p.click('#play'); await wait(500); R = await log();
  const bare = R.some(r => r.e != null);
  await open('#cowpens@07:45,play,warp'); await record(); await wait(500); R = await log();
  const warp = !R.some(r => r.e != null);
  ok(late && seeked && warp && bare, `#cowpens@07:45 + Play: no opening (${late}); Play after a seek: none (${seeked}); ,play,warp: none (${warp}); bare #cowpens + Play: runs (${bare})`);

  // 5: a click skips it
  await open('#cowpens'); await p.click('#play');
  await p.waitForFunction(() => fg.state().opening?.e >= 2, { polling: 'raf' });
  const before = await st();
  await p.mouse.click(60, 415);
  const next = await p.evaluate(() => new Promise(r => requestAnimationFrame(() => r({ s: fg.state(), cls: document.body.classList.contains('opening') }))));
  await wait(1400); const back5 = await panelsBack();
  ok(!next.s.opening && !next.cls && px(next.s.cam, before.opening.target) < 1 && back5 && next.s.playing,
    `a click at e ${f2(before.opening.e)} ends it: next frame ${px(next.s.cam, before.opening.target).toFixed(3)} px from the target, page back (${back5}), playing (${next.s.playing})`);

  // 6: reduced motion
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]);
  await open('#cowpens'); await record(); await p.click('#play');
  await p.waitForFunction(() => rec.some(r => r.e != null) && !fg.state().opening, { timeout: 20000, polling: 'raf' });
  await frames(3); R = await log();
  const rm = R.filter(r => r.e != null), w0 = rm[0].wide, t0 = rm[0].target, mids = rm.filter(r => px(r.cam, w0) > 1e-6), rl = R[R.findIndex(r => r.e != null) + rm.length];
  const rt = rm.reduce((a, r) => (Math.abs(r.e - 2.5) < Math.abs(a.e - 2.5) ? r : a));
  ok(!mids.length && px(rl.cam, t0) < 1 && rt.op === 1, `reduced motion: ${rm.length} frames all at the wide frame (${mids.length} elsewhere), e ${f2(rm[0].e)} to ${f2(rm.at(-1).e)}, then a cut to the target (${px(rl.cam, t0).toFixed(3)} px); title ${rt.op} at e ${f2(rt.e)}`);
  await p.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'no-preference' }]);

  // 7: the first frame is not black
  const lum = () => p.evaluate(ext => {
    const c = document.querySelector('#map'), g = c.getContext('2d'), k = c.width / innerWidth, s = Math.min(innerWidth, innerHeight), z = fg.state().cam.zoom * ext;
    const x0 = Math.max(0, (innerWidth - Math.min(z, innerWidth)) / 2) * k, y0 = Math.max(0, (innerHeight - Math.min(z, innerHeight)) / 2) * k, d = g.getImageData(x0, y0, Math.min(z, innerWidth) * k, Math.min(z, innerHeight) * k).data;
    let sum = 0; for (let i = 0; i < d.length; i += 4) sum += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
    return sum / (d.length / 4);
  }, cow.extent);
  await open('#cowpens'); await p.click('#play'); await p.evaluate(() => fg.hold(0)); await frames(2);
  const lOpen = await lum();
  await p.evaluate(() => fg.hold(9.19)); await frames(2); const lLand = await lum();
  ok(lOpen > 60 && lOpen > lLand, `first frame on Cowpens: mean luminance ${lOpen.toFixed(1)} of 255 under the dawn cap, against ${lLand.toFixed(1)} at the landing in the true dark`);

  // 8: the title at the laptop sizes
  for (const v of [{ width: 1536, height: 830, deviceScaleFactor: 1.25 }, { width: 1280, height: 700, deviceScaleFactor: 1.5 }]) {
    await p.setViewport(v);
    for (const id of ids.split(',')) {
      await open(`#${id},opening`);
      const a = await p.evaluate(() => {
        const el = document.querySelector('#opening'), r = el.getBoundingClientRect(), px = s => parseFloat(getComputedStyle(document.querySelector(s)).fontSize);
        return { r: [r.left, r.top, r.right, r.bottom].map(Math.round), name: px('#op-name'), date: px('#op-date'), op: +getComputedStyle(el).opacity, scroll: document.documentElement.scrollWidth - innerWidth };
      });
      ok(a.op === 1 && a.r[0] >= 0 && a.r[2] <= v.width && a.name >= 16 && a.date >= 16 && a.scroll <= 0,
        `${v.width}x${v.height}@${v.deviceScaleFactor} ${id},opening: title at ${a.r.join(',')}, ${a.name}/${a.date} px, opacity ${a.op}, no scroll`);
    }
  }

  // the frames for the PR: field, title and landing, then the title on a phone
  await p.setViewport({ width: 1536, height: 830 });
  for (const id of ids.split(',')) {
    await open(`#${id}`); await p.click('#play');
    for (const [n, e] of [['field', 0.5], ['title', 3.2]]) { await p.evaluate(e => fg.hold(e), e); await frames(3); await shot(`${id}-${n}`); }
    await p.evaluate(() => fg.hold(9.2)); await wait(1500); await shot(`${id}-landing`);
  }
  await p.setViewport({ width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await open(`#${ids.split(',')[0]},opening`); await frames(3); await shot(`${ids.split(',')[0]}-title-phone`);

  if (clip) { // 15 fps, the panels' fade held to the same clock
    await p.setViewport({ width: 1536, height: 830 });
    const fs = require('fs'); fs.mkdirSync(`${dir}/clip`, { recursive: true });
    await open(`#${ids.split(',')[0]}`); await p.click('#play');
    for (let i = 0; i <= 150; i++) {
      const e = i / 15;
      await p.evaluate(e => {
        fg.hold(e);
        for (const a of document.getAnimations()) { a.pause(); a.currentTime = Math.max(0, (e - 8) * 1000); }
      }, e);
      await frames(2);
      await p.screenshot({ path: `${dir}/clip/f${String(i).padStart(3, '0')}.jpg`, type: 'jpeg', quality: 88 });
    }
    console.log(`clip: 151 frames in ${dir}/clip`);
  }
  ok(!errs.length, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await br.close();
})().catch(e => { console.log('FAIL ' + e.message); process.exit(1); });

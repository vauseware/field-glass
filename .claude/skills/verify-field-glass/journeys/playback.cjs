// Battle playback: play and pause, Space, the scrubber, the arrow keys, speed, and the Legend and Sources dialogs.
// Run: bash fg.sh drive <dir> journeys/playback.cjs [battle id, default cowpens]
const puppeteer = require('puppeteer-core');
const [exe, base, dir, id = 'cowpens'] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
const wait = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const p = await br.newPage(); await p.setViewport({ width: 1440, height: 900 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  const shot = n => p.screenshot({ path: `${dir}/playback-${id}-${n}.png` });
  const hud = () => p.evaluate(() => ({ play: document.querySelector('#play').getAttribute('aria-label'), clock: document.querySelector('#clock').textContent,
    scrub: +document.querySelector('#scrub').value, min: +document.querySelector('#scrub').min, cap: document.querySelector('#cap-title').textContent }));

  await p.goto(`${base}#${id}`, { waitUntil: 'networkidle0' });
  ok(await p.waitForFunction(() => document.querySelector('#splash').hidden && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 }).then(() => true, () => false), `#${id} opens the battle`);
  let s = await hud(); await shot('1-open');
  ok(s.play === 'Play' && s.scrub === s.min, `it opens paused at the start (${s.clock}, caption "${s.cap}")`);
  const blur = () => p.evaluate(() => document.activeElement?.blur()); // the app ignores keys aimed at a button, and Space on a focused button is the button's own click
  await p.click('#play'); const op = await p.$eval('#opening', el => !el.hidden); // the first Play from the start runs the opening shot
  await p.waitForFunction(() => document.querySelector('#opening').hidden, { timeout: 30000 }); await wait(3000); const a = await hud();
  ok(op && a.play === 'Pause' && a.scrub > s.scrub, `Play runs the opening shot, then the clock (+${a.scrub - s.scrub} s of battle time)`);
  await p.click('#play'); const b = await hud(); await wait(1500); const c = await hud();
  ok(b.play === 'Play' && c.scrub === b.scrub, `Pause holds the clock at ${c.clock}`);
  await blur(); await p.keyboard.press('Space'); await wait(1000); const d = await hud(); await p.keyboard.press('Space');
  ok(d.play === 'Pause' && d.scrub > c.scrub, `Space toggles play (+${d.scrub - c.scrub} s)`);
  await p.$eval('#scrub', el => { el.value = String(+el.min + (+el.max - +el.min) / 2); el.dispatchEvent(new Event('input', { bubbles: true })); });
  await wait(300); const e = await hud(); await shot('2-midway');
  ok(e.scrub > d.scrub && e.cap !== s.cap, `dragging the scrubber halfway seeks and changes the chapter (${e.clock}, "${e.cap}")`);
  await blur(); await p.keyboard.press('ArrowRight'); await wait(300); const f = await hud();
  ok(f.scrub > e.scrub, `ArrowRight steps forward (+${f.scrub - e.scrub} s)`);
  const speeds = await p.$$eval('#speed option', o => o.map(x => x.value));
  await p.select('#speed', speeds.at(-1));
  ok(await p.$eval('#speed', el => el.value) === speeds.at(-1), `Speed offers ${speeds.join(', ')} and takes ${speeds.at(-1)}`);
  await p.click('#legend-btn'); await wait(300);
  ok(await p.$eval('#legend-dlg', d => d.open && document.querySelector('#legend-list').children.length > 0), 'Legend opens a dialog with entries'); await shot('3-legend');
  await p.keyboard.press('Escape'); await p.click('#src-btn'); await wait(300);
  ok(await p.$eval('#sources', d => d.open && document.querySelector('#src-list').children.length > 0), 'Sources opens a dialog listing the sources'); await shot('4-sources');
  ok(!errs.length, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await br.close();
})().catch(e => { console.log('FAIL ' + e.message); process.exit(1); });

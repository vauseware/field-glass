// Loads each skin over the three preview frames, fails on any page error, and saves a shot of each.
// Run: bash .claude/skills/verify-field-glass/fg.sh drive <dir> .claude/skills/war-skin/shoot-skins.cjs <skin id>...
const puppeteer = require('puppeteer-core');
const [exe, base, dir, ...skins] = process.argv.slice(2);
const FRAMES = [['guilford', '14:02'], ['fort-fisher', '1865-01-15T15:25'], ['yorktown', '1781-10-14T20:10']];
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);
(async () => {
  if (!skins.length) return ok(false, 'name at least one skin id');
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  for (const skin of skins) for (const [id, at] of FRAMES) {
    const p = await br.newPage(), errors = [];
    await p.setViewport({ width: 1536, height: 830, deviceScaleFactor: 1.25 });
    p.on('pageerror', e => errors.push(e.message));
    await p.goto(`${base}?theme=${skin}#${id}@${at},play,warp`, { waitUntil: 'networkidle0' });
    const drawn = await p.waitForFunction(() => document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 }).then(() => true, () => false);
    await new Promise(r => setTimeout(r, 2500));
    await p.screenshot({ path: `${dir}/${skin}-${id}.png` });
    ok(drawn && !errors.length, `${skin} on ${id}: ${drawn ? 'drawn' : 'stuck on Loading…'}${errors.length ? `, errors: ${errors.join('; ')}` : ''}`);
    await p.close();
  }
  await br.close();
})();

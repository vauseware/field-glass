// Start screen: the war timeline, opening a battle, All battles back to its war, Back to the battle.
// Run: bash fg.sh drive <dir> journeys/start-screen.cjs   (args from fg.sh: <chrome> <base url> <dir>)
const puppeteer = require('puppeteer-core');
const [exe, base, dir] = process.argv.slice(2);
const ok = (c, m) => console.log(`${c ? 'PASS' : 'FAIL'} ${m}`);

(async () => {
  const br = await puppeteer.launch({ executablePath: exe, headless: 'shell', args: ['--no-sandbox'] });
  const p = await br.newPage(); await p.setViewport({ width: 1440, height: 900 });
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  const shot = n => p.screenshot({ path: `${dir}/start-screen-${n}.png` });
  const state = () => p.evaluate(() => {
    const el = document.querySelector('#splash');
    return { hash: location.hash, war: el.className, hidden: el.hidden, tag: el.querySelector('.tag')?.textContent, rows: [...el.querySelectorAll('.row')].map(b => b.dataset.id),
      empty: !!el.querySelector('.empty'), pressed: [...el.querySelectorAll('.tl-war[aria-pressed="true"]')].map(b => b.dataset.war).join(), hist: history.length,
      body: document.body.className, title: document.querySelector('#title').textContent };
  });
  const battleUp = id => p.waitForFunction(i => document.querySelector('#splash').hidden && location.hash.startsWith('#' + i) && document.querySelector('#title').textContent !== 'Loading…', { timeout: 60000 }, id).then(() => true, () => false);
  const n = (await (await fetch(`${base}battles/index.json`)).json()).filter(b => b.war === 'American Revolutionary War').length;

  await p.goto(base, { waitUntil: 'networkidle0' });
  let s = await state(); const h0 = s.hist; await shot('1-bare');
  ok(!s.hidden && s.war === 'war-revolution' && s.pressed === 'revolution' && s.rows.length === n, `bare URL opens the Revolution with its ${n} battles (${s.war}, ${s.rows.length} rows)`);
  await p.click('.tl-war[data-war="ww2"]'); s = await state(); await shot('2-ww2');
  ok(s.hash === '#ww2' && s.war === 'war-ww2' && s.pressed === 'ww2' && /Second World War/.test(s.tag) && s.rows.includes('sidi-bou-zid'), `timeline click switches to the Second World War card and hash (${s.hash}, rows ${s.rows})`);
  await p.click('.tl-war[data-war="civil-war"]'); s = await state(); await shot('3-civil-war');
  ok(s.hash === '#civil-war' && s.war === 'war-civil-war' && (s.empty ? !s.rows.length : s.rows.length > 0), `Civil War shows its list or the in-preparation card (${s.hash}, ${s.rows.length} rows)`);
  ok(s.hist === h0, `war clicks add no history entries (history.length ${h0} -> ${s.hist})`);
  await p.click('.tl-war[data-war="ww2"]'); await p.click('.row[data-id="sidi-bou-zid"]');
  ok(await battleUp('sidi-bou-zid'), 'clicking a battle row opens the battle');
  s = await state(); await shot('4-battle');
  ok(/theme-ww2/.test(s.body) && /Sidi Bou Zid/i.test(s.title), `the battle wears its skin (${s.body}; ${s.title})`);
  ok(await p.$eval('#play', b => b.getAttribute('aria-label')) === 'Pause', 'a battle opened from the list plays, so the page did not reload');
  await p.goBack(); await p.waitForFunction(() => !document.querySelector('#splash').hidden, { timeout: 30000 }).catch(() => {}); await p.waitForNetworkIdle();
  s = await state(); ok(s.hash === '#ww2' && !s.hidden && s.war === 'war-ww2', `Back from a battle opened on the list returns to its war (${s.hash})`);

  await p.goto('about:blank'); await p.goto(`${base}#sidi-bou-zid`, { waitUntil: 'networkidle0' });
  ok(await battleUp('sidi-bou-zid'), '#sidi-bou-zid opens the battle directly');
  await Promise.all([new Promise(r => p.once('load', r)), p.$eval('#home', b => b.click())]); await p.waitForNetworkIdle();
  s = await state(); await shot('5-all-battles');
  ok(s.hash === '#ww2' && !s.hidden && s.war === 'war-ww2', `All battles from #sidi-bou-zid lands on #ww2 with the WW2 card (${s.hash}, ${s.war})`);
  await p.goBack();
  ok(await battleUp('sidi-bou-zid'), 'Back from the war list returns to the battle');
  ok(!errs.length, `no page errors${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await br.close();
})().catch(e => { console.log('FAIL ' + e.message); process.exit(1); });

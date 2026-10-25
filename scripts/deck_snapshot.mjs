// Snapshot every slide of a deck, for before/after comparison.
//
// Per slide it writes NNN.png (the 1280x720 stage, chrome hidden) and records a
// hash of the stage's HTML and its text in manifest.json. Run it on the same
// build before and after a change to how decks are authored; deck_compare.py
// then says which slides differ. Same headless-Chrome-over-CDP approach as
// deck_pdf.mjs, for the same reason: the Browser pane suspends layout.
//
//   node scripts/deck_snapshot.mjs day8 8352 --out=DIR [--student] [--notes]
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';

const deck = process.argv[2];
const port = process.argv[3] || '8352';
const arg = (n, d) => { const a = process.argv.find(x => x.startsWith(`--${n}=`)); return a ? a.slice(n.length + 3) : d; };
const outdir = join(arg('out', 'output/baseline'), deck);
const student = process.argv.includes('--student');
const notes = process.argv.includes('--notes');
mkdirSync(outdir, { recursive: true });

const profile = mkdtempSync(join(tmpdir(), 'decksnap-'));
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
  '--window-size=1280,720', '--hide-scrollbars', '--force-device-scale-factor=1',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-gpu', '--no-first-run', '--no-default-browser-check', 'about:blank',
], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const cleanup = () => { try { chrome.kill(); } catch {} try { rmSync(profile, { recursive: true, force: true }); } catch {} };
process.on('exit', cleanup);

async function wsUrl() {
  for (let i = 0; i < 80; i++) {
    try {
      const p = readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
      const j = await (await fetch(`http://127.0.0.1:${p}/json/version`)).json();
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl;
    } catch {}
    await sleep(150);
  }
  throw new Error('chrome never came up');
}
const ws = new WebSocket(await wsUrl());
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let id = 0; const pending = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id != null && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
const send = (method, params = {}, sessionId) => new Promise(res => {
  const mid = ++id; pending.set(mid, res);
  ws.send(JSON.stringify({ id: mid, method, params, ...(sessionId ? { sessionId } : {}) }));
});
const { result: { targetId } } = await send('Target.createTarget', { url: 'about:blank' });
const { result: { sessionId: S } } = await send('Target.attachToTarget', { targetId, flatten: true });
await send('Page.enable', {}, S); await send('Runtime.enable', {}, S);
await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false }, S);
await send('Emulation.setEmulatedMedia', { media: 'screen' }, S);
const ev = async expr => {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }, S);
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
  return r.result?.result?.value;
};

const qs = `deck=${encodeURIComponent(deck)}${student ? '&student' : ''}${notes ? '&notes' : ''}`;
await send('Page.navigate', { url: `http://127.0.0.1:${port}/external/class.html?${qs}` }, S);
await sleep(2500);
await ev(`(() => { const s = document.createElement('style');
  s.textContent = '*,*::before,*::after{transition:none!important;animation:none!important} #bar,#ink,#toast,#slideedit,#review,#reviewbar,#comment{display:none!important} #stage-wrap{inset:0!important}';
  document.head.appendChild(s); })()`);
const count = await ev(`(() => { const m = ((document.getElementById('pos')||{}).textContent||'').match(/\\/\\s*(\\d+)/); return m ? Number(m[1]) : 0 })()`);
if (!count) { console.error(`${deck}: no slides`); process.exit(1); }

const sha = s => createHash('sha1').update(s).digest('hex').slice(0, 12);
const manifest = [];
for (let i = 1; i <= count; i++) {
  await ev(`location.hash = '${i}'`);
  await sleep(340);
  await ev(`(async () => { if (window.MathJax && MathJax.typesetPromise) { try { await MathJax.typesetPromise() } catch(e){} } return true })()`);
  await ev(`(async () => {
    const d = ms => new Promise(r => setTimeout(r, ms));
    const imgs = [...document.querySelectorAll('#stage img')].filter(im => !im.complete);
    await Promise.race([Promise.all(imgs.map(im => new Promise(r => { im.addEventListener('load', r, {once:true}); im.addEventListener('error', r, {once:true}); }))), d(4000)]);
    if (document.fonts && document.fonts.ready) { try { await Promise.race([document.fonts.ready, d(2000)]) } catch (e) {} }
    return true })()`);
  await sleep(120);
  // MathJax numbers its element ids per run, and the player stamps ?_r=<time> on image URLs;
  // both differ between two runs of the same slide.
  const html = (await ev(`document.getElementById('stage').outerHTML`)).replace(/MJX[-_]\d+/gi, 'MJX-N').replace(/\?_r=\d+/g, '');
  writeFileSync(join(outdir, `${String(i).padStart(3, '0')}.html`), html);
  const text = await ev(`document.getElementById('stage').innerText`);
  const title = await ev(`(document.querySelector('#stage h1, #stage h2, #stage .slide-title')||{}).textContent||''`);
  const shot = await send('Page.captureScreenshot', { format: 'png' }, S);
  const f = `${String(i).padStart(3, '0')}.png`;
  writeFileSync(join(outdir, f), Buffer.from(shot.result.data, 'base64'));
  manifest.push({ n: i, title: title.trim().slice(0, 80), html: sha(html), text: sha(text), png: sha(shot.result.data) });
  process.stderr.write(`\r${deck}: ${i}/${count}`);
}
process.stderr.write('\n');
writeFileSync(join(outdir, 'manifest.json'), JSON.stringify(manifest, null, 1));
console.log(`${deck}: ${count} slides -> ${outdir}`);
try { ws.close(); } catch {}
process.exit(0);

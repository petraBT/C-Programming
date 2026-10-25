// Fit sweep over a deck, driven through raw CDP against headless Chrome.
//
// Why not the Browser pane: when the pane is hidden the browser suspends
// layout, every clientHeight reads 0, and a slide 200 px over reports "fits"
// (plans/style-sweep.md N-7).  Headless Chrome over raw CDP always lays out.
//
// Reports the LAST ITEM'S CLEARANCE, not just body overflow: a room="yes"
// slide can report 17 px "over" with its final bullet clear by 6 px, which is
// the writing space below it and not a clip.  Only last.getBoundingClientRect()
// .bottom > body.bottom is a real loss.  CLIP = real, SOFT = padding only.
//
// INSTRUCTOR-ONLY slides are flagged `scroll`, never CLIP (Petra, 2026-09-21:
// "Don't worry about page overrun on instructor only slides.  They scroll.").
// They are read at the laptop rather than projected past the bottom of the
// wall, so an overrun there is not a loss.  They are still measured and their
// clearance still printed — the flag is the only thing that changes — so a
// deliberate check of one is still possible, without the committee or a fit
// sweep re-raising it every time.
//
// The deck player must be served somewhere; ./preview-slides.sh puts it on 8352.
// Slide indices match the counter in the player's bottom-right corner.
//
//   node scripts/deck_fit.mjs day9 8352 --count=54
//   node scripts/deck_fit.mjs day1 8352 --count=36 --shot=12,27 --outdir=/tmp/shots
import { spawn } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const deck = process.argv[2];
const port = process.argv[3] && /^\d+$/.test(process.argv[3]) ? process.argv[3] : '8352';
const shotArg = process.argv.find(a => a.startsWith('--shot='));
const outArg = process.argv.find(a => a.startsWith('--outdir='));
const wantShots = shotArg ? new Set(shotArg.slice(7).split(',').map(Number)) : null;
const outdir = outArg ? outArg.slice(9) : null;
if (outdir) mkdirSync(outdir, { recursive: true });

const CDP_PORT = 9333 + Math.floor(Math.random() * 300);
const profile = mkdtempSync(join(tmpdir(), 'fitsweep-'));
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1600,900', '--hide-scrollbars', '--force-device-scale-factor=1',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-gpu', '--no-first-run', '--no-default-browser-check', 'about:blank',
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function wsUrl() {
  for (let i = 0; i < 80; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`);
      const j = await r.json();
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl;
    } catch {}
    await sleep(150);
  }
  throw new Error('chrome never came up');
}

const browserWs = await wsUrl();
const ws = new WebSocket(browserWs);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let id = 0;
const pending = new Map();
const events = [];
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id != null && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  else events.push(m);
};
function send(method, params = {}, sessionId) {
  const mid = ++id;
  return new Promise(res => {
    pending.set(mid, res);
    ws.send(JSON.stringify({ id: mid, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
}

const { result: { targetId } } = await send('Target.createTarget', { url: 'about:blank' });
const { result: { sessionId } } = await send('Target.attachToTarget', { targetId, flatten: true });
const S = sessionId;
await send('Page.enable', {}, S);
await send('Runtime.enable', {}, S);
await send('Emulation.setDeviceMetricsOverride',
  { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false }, S);

async function evaluate(expr) {
  const r = await send('Runtime.evaluate',
    { expression: expr, returnByValue: true, awaitPromise: true }, S);
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
  return r.result?.result?.value;
}

const base = `http://127.0.0.1:${port}/external/class.html?deck=${deck}`;
await send('Page.navigate', { url: base }, S);
await sleep(2500);

// Kill the crossfade so a measurement never lands mid-transition.
await evaluate(`(() => {
  const s = document.createElement('style');
  s.textContent = '*,*::before,*::after{transition:none!important;animation:none!important}';
  document.head.appendChild(s);
  return true;
})()`);

const count = await evaluate(`(window.SLIDES && SLIDES.length) || (window.deck && deck.slides && deck.slides.length) || document.querySelectorAll('#bar .dot').length || 0`);
const total = await evaluate(`(() => {
  for (const k of ['slides','SLIDES','deckSlides']) if (Array.isArray(window[k])) return window[k].length;
  return null;
})()`) ?? count;

const MEASURE = `(() => {
  const ref = document.querySelector('#ref');
  const title = (document.querySelector('#ref .deck-title') || document.querySelector('#stage h1, #stage h2') || {}).textContent || '';
  if (!ref || getComputedStyle(ref).display === 'none') {
    const g = document.querySelector('#glue');
    const gt = (document.querySelector('#glue .section-main, #glue .title-main, #glue h2')
                || document.querySelector('#stage h1,#stage h2,#stage .title') || {}).textContent || '';
    if (!g || getComputedStyle(g).display === 'none') return { kind: 'glue', title: gt };
    if (g.clientHeight === 0) return { kind: 'SUSPENDED', title: gt };
    const gout = [];
    const gdy = g.scrollHeight - g.clientHeight;
    if (gdy > 2) gout.push('body overflows ' + gdy + 'px down');
    const gitems = g.querySelectorAll(':scope > ul > li, :scope > p, :scope > div');
    const glast = gitems.length ? gitems[gitems.length - 1] : null;
    let gclear = null;
    const bar = document.querySelector('#bar');
    const floor = bar ? bar.getBoundingClientRect().top
                      : Math.min(g.getBoundingClientRect().bottom, window.innerHeight);
    if (glast) gclear = Math.round(floor - glast.getBoundingClientRect().bottom);
    if (gclear != null && gclear < 0) gout.push('last item ' + (-gclear) + 'px below the bar');
    return { kind: 'ref', title: gt, problems: gout, clearance: gclear,
             cls: 'glue ' + (g.className || '').replace(/\bslide\b|\bon\b/g, '').trim() };
  }
  const b = document.querySelector('#ref .ref-body');
  const out = [];
  const shown = b && getComputedStyle(b).display !== 'none';
  if (shown && b.clientHeight === 0) return { kind: 'SUSPENDED', title };
  let clearance = null, lastText = null;
  if (shown) {
    const dy = b.scrollHeight - b.clientHeight, dx = b.scrollWidth - b.clientWidth;
    if (dy > 2) out.push('body overflows ' + dy + 'px down');
    if (dx > 2) out.push('body overflows ' + dx + 'px across');
    // The real clip test (N-7): is the LAST rendered item below the body box?
    const items = b.querySelectorAll(':scope > ul > li, :scope > ol > li, :scope > p, :scope > .para, :scope > .task, :scope > div');
    const last = items.length ? items[items.length - 1] : null;
    if (last) {
      const lb = last.getBoundingClientRect().bottom;
      const bb = b.getBoundingClientRect().bottom;
      clearance = Math.round(bb - lb);
      lastText = (last.textContent || '').trim().slice(0, 70);
    }
  }
  document.querySelectorAll('#ref pre').forEach((p, i) => {
    const dx = p.scrollWidth - p.clientWidth, dy = p.scrollHeight - p.clientHeight;
    if (dx > 2) out.push('code block ' + (i+1) + ': ' + dx + 'px CLIPPED ACROSS');
    if (dy > 2) out.push('code block ' + (i+1) + ': ' + dy + 'px clipped down');
  });
  const cls = ref.className || '';
  return { kind: 'ref', title, cls, problems: out, clearance, lastText,
           roomy: !!b && /roomy/.test(b.className || '') };
})()`;

// Which runtime indices are instructor-only, read from the deck file itself.
// The player numbers slides from 1 in the order the JSON lists them, so the
// entry at 0-based n is slide n+1.
const instructorSlides = (() => {
  try {
    const raw = readFileSync(`assets/decks/${deck}.json`, 'utf8');
    const parsed = JSON.parse(raw);
    const list = Array.isArray(parsed) ? parsed : parsed.slides;
    return new Set(
      list.flatMap((entry, n) => (entry && entry.instructor ? [n + 1] : [])),
    );
  } catch {
    // No deck file to hand (a different working directory, say). Report every
    // overrun as a clip, which is the safe direction to be wrong in.
    return new Set();
  }
})();

const countArg = process.argv.find(a => a.startsWith('--count='));
const limit = countArg ? Number(countArg.slice(8)) : (total || 60);
const rows = [];
for (let i = 1; i <= limit; i++) {
  await evaluate(`location.hash = '${i}'`);
  await sleep(320);
  await evaluate(`(async () => { if (window.MathJax && MathJax.typesetPromise) { try { await MathJax.typesetPromise() } catch(e){} } return true })()`);
  await sleep(120);
  const m = await evaluate(MEASURE);
  if (m == null) break;
  rows.push({ i, ...m });
  if (wantShots && wantShots.has(i) && outdir) {
    const shot = await send('Page.captureScreenshot', { format: 'png' }, S);
    writeFileSync(join(outdir, `${deck}-${String(i).padStart(2, '0')}.png`),
      Buffer.from(shot.result.data, 'base64'));
  }
}

for (const r of rows) {
  const t = (r.title || '').replace(/\s+/g, ' ').trim().slice(0, 58);
  if (r.kind === 'glue') { console.log(`${String(r.i).padStart(2)}  glue        ${t}`); continue; }
  if (r.kind === 'SUSPENDED') { console.log(`${String(r.i).padStart(2)}  SUSPENDED   ${t}`); continue; }
  const probs = r.problems.length ? r.problems.join('; ') : 'fits';
  const cl = r.clearance == null ? '    n/a' : `${String(r.clearance).padStart(5)}px`;
  const flag = !r.problems.length
    ? '      '
    : instructorSlides.has(r.i)
      ? 'scroll'
      : r.clearance != null && r.clearance >= 0
        ? 'SOFT  '
        : 'CLIP  ';
  console.log(`${String(r.i).padStart(2)}  ${flag} last-clear ${cl}  ${probs}  | ${t}${r.cls ? '  [' + r.cls.trim() + ']' : ''}`);
}

ws.close();
chrome.kill();
process.exit(0);

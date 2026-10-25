// For each review comment in the queue, report the words her bbox circles and
// the block that encloses them.
//
// Two thirds of Petra's comments are one or two words typed against circled
// text ("capacitor", "in", "then", "contains"), and the comment means nothing
// without the words under the circle.  Cropping screenshots is the slow way;
// this walks the text nodes, Ranges each word, and keeps the words whose rect
// overlaps the stage-scaled bbox (plans/style-sweep.md N-8).  It also prints
// the enclosing <p>/<li>, so the replacement lands in the right sentence.
//
// Reads reviews/slide-comments.jsonl, sorted by ts.  The deck player must be
// served (./preview-slides.sh, port 8352) and the comments' own urls are used,
// so this works for slide comments; book comments carry document-pixel bboxes
// and need the web-edit preview instead.
//
//   node scripts/read_comments.mjs reviews/slide-comments.jsonl
//   node scripts/read_comments.mjs reviews/slide-comments.jsonl 3,7,11 /tmp/crops
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const queue = process.argv[2];
const only = process.argv[3] ? new Set(process.argv[3].split(',')) : null;
const shotDir = process.argv[4] || null;
if (shotDir) mkdirSync(shotDir, { recursive: true });

const rows = readFileSync(queue, 'utf8').split('\n').filter(Boolean).map(JSON.parse)
  .sort((a, b) => (a.ts || '').localeCompare(b.ts || ''));

const CDP_PORT = 9600 + Math.floor(Math.random() * 300);
const profile = mkdtempSync(join(tmpdir(), 'readc-'));
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`,
  '--window-size=1600,900', '--hide-scrollbars', '--force-device-scale-factor=1',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-gpu', '--no-first-run', '--no-default-browser-check', 'about:blank',
], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function wsUrl() {
  for (let i = 0; i < 80; i++) {
    try { const j = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`)).json();
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl; } catch {}
    await sleep(150);
  }
  throw new Error('chrome never came up');
}
const ws = new WebSocket(await wsUrl());
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let id = 0; const pending = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data);
  if (m.id != null && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
function send(method, params = {}, sessionId) {
  const mid = ++id;
  return new Promise(res => { pending.set(mid, res);
    ws.send(JSON.stringify({ id: mid, method, params, ...(sessionId ? { sessionId } : {}) })); });
}
const { result: { targetId } } = await send('Target.createTarget', { url: 'about:blank' });
const { result: { sessionId: S } } = await send('Target.attachToTarget', { targetId, flatten: true });
await send('Page.enable', {}, S); await send('Runtime.enable', {}, S);
await send('Emulation.setDeviceMetricsOverride', { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false }, S);
async function ev(expr) {
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }, S);
  return r.result?.result?.value;
}

const EXTRACT = bb => `(() => {
  const bb = ${JSON.stringify(bb)};
  const stage = document.getElementById('stage');
  if (!stage) return { err: 'no stage' };
  const sr = stage.getBoundingClientRect();
  const box = { l: sr.left + bb.x*sr.width, t: sr.top + bb.y*sr.height,
                r: sr.left + (bb.x+bb.w)*sr.width, b: sr.top + (bb.y+bb.h)*sr.height };
  const hit = (q) => !(q.right < box.l || q.left > box.r || q.bottom < box.t || q.top > box.b);
  const words = []; const blocks = new Set();
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walk.nextNode())) {
    let p = n.parentElement, skip = false;
    for (let e = p; e; e = e.parentElement) {
      if (e.id === 'bar' || e.tagName === 'SCRIPT' || e.tagName === 'STYLE') { skip = true; break; }
      const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden') { skip = true; break; }
    }
    if (skip) continue;
    const txt = n.nodeValue;
    const re = /\\S+/g; let m;
    while ((m = re.exec(txt))) {
      const rg = document.createRange();
      rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].length);
      const rects = [...rg.getClientRects()];
      if (rects.some(hit)) {
        words.push(m[0]);
        let blk = p;
        while (blk && !['P','LI','TD','TH','CAPTION','H1','H2','H3','PRE','DIV'].includes(blk.tagName)) blk = blk.parentElement;
        if (blk) blocks.add(blk.textContent.replace(/\\s+/g,' ').trim());
      }
    }
  }
  return { words, blocks: [...blocks] };
})()`;

for (let i = 0; i < rows.length; i++) {
  if (only && !only.has(String(i))) continue;
  const r = rows[i];
  await send('Page.navigate', { url: r.url }, S);
  await sleep(1400);
  await ev(`(()=>{const s=document.createElement('style');s.textContent='*,*::before,*::after{transition:none!important;animation:none!important}';document.head.appendChild(s);return 1})()`);
  await ev(`(async()=>{if(window.MathJax&&MathJax.typesetPromise){try{await MathJax.typesetPromise()}catch(e){}}return 1})()`);
  await sleep(150);
  const out = await ev(EXTRACT(r.bbox));
  console.log(`=== ${String(i).padStart(2,'0')}  ${r.deck} slide ${r.slide}  "${r.title}"`);
  console.log(`    COMMENT: ${r.text}`);
  console.log(`    CIRCLED: ${(out?.words||[]).join(' ') || '(nothing — check the shot)'}`);
  for (const b of (out?.blocks||[])) console.log(`    BLOCK  : ${b.slice(0,300)}`);
  if (shotDir) {
    const sr = await ev(`(()=>{const s=document.getElementById('stage').getBoundingClientRect();return {x:s.left,y:s.top,w:s.width,h:s.height}})()`);
    const pad = 40;
    const clip = { x: Math.max(0, sr.x + r.bbox.x*sr.w - pad), y: Math.max(0, sr.y + r.bbox.y*sr.h - pad),
                   width: Math.min(1600, r.bbox.w*sr.w + 2*pad), height: Math.min(900, r.bbox.h*sr.h + 2*pad), scale: 2 };
    const shot = await send('Page.captureScreenshot', { format: 'png', clip }, S);
    if (shot.result?.data) writeFileSync(join(shotDir, `c${String(i).padStart(2,'0')}.png`), Buffer.from(shot.result.data,'base64'));
  }
}
ws.close(); chrome.kill(); process.exit(0);

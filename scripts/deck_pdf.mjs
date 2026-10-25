// Print a deck to a note-taking PDF: one landscape 16:9 page per slide.
//
// Student view only.  Two independent reasons a slide can be instructor-only,
// and this relies on BOTH: the web-deck build strips those slides out of the
// HTML, and filter_student_decks.py drops them from the deck JSON beside it.
// The `&student` flag is added on top as a third.  A handout is the one artifact
// where a leaked solution cannot be taken back, so the belt and the braces and
// the third thing all stay.
//
// Why headless Chrome over raw CDP rather than the Browser pane: a hidden pane
// suspends layout, every clientHeight reads 0, and the slide lays out wrong.
// Same reason deck_fit.mjs does it this way, and most of the plumbing here is
// lifted from it.
//
// Why Page.printToPDF rather than screenshots: the page box is 13.333x7.5in,
// which is 1280x720 CSS px -- exactly 16:9, so #stage's `min(100vw, 100vh*16/9)`
// resolves to the full page and the slide lays out at projection proportions.
// The text stays vector (selectable, searchable, sharp at any zoom) and a deck
// comes out a few MB instead of a few hundred.  13.333x7.5in is also
// PowerPoint's own 16:9 page, so printing to letter landscape just works.
//
// The deck player must be served somewhere; make-slide-pdfs.sh handles that.
//
//   node scripts/deck_pdf.mjs day1 8352 --out=output/slide-pdfs
//   node scripts/deck_pdf.mjs day1 8352 --out=… --keep-pages
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync, statSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const deck = process.argv[2];
if (!deck) {
  console.error('usage: node scripts/deck_pdf.mjs <deck> [port] [--out=DIR] [--keep-pages]');
  process.exit(2);
}
const port = process.argv[3] && /^\d+$/.test(process.argv[3]) ? process.argv[3] : '8352';
const arg = (name, dflt) => {
  const a = process.argv.find(x => x.startsWith(`--${name}=`));
  return a ? a.slice(name.length + 3) : dflt;
};
const outdir = arg('out', 'output/slide-pdfs');
const keepPages = process.argv.includes('--keep-pages');
mkdirSync(outdir, { recursive: true });

// 16:9 at PowerPoint's own 16:9 page size.  At 96 CSS px/in this is 1280x720,
// so the stage fills the page exactly -- see the header note.
const PAGE_W_IN = 13.333;
const PAGE_H_IN = 7.5;
const VIEW_W = 1280;
const VIEW_H = 720;

const profile = mkdtempSync(join(tmpdir(), 'deckpdf-'));
const pagedir = mkdtempSync(join(tmpdir(), 'deckpdf-pages-'));
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  // Port 0: Chrome picks a free one and writes it to DevToolsActivePort in the
  // profile. A random fixed port collided when make-slide-pdfs.sh -j ran decks
  // side by side, and one job then drove (and killed) another's browser.
  '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`,
  `--window-size=${VIEW_W},${VIEW_H}`, '--hide-scrollbars', '--force-device-scale-factor=1',
  '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  '--disable-gpu', '--no-first-run', '--no-default-browser-check', 'about:blank',
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));
const cleanup = () => {
  try { chrome.kill(); } catch {}
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
  if (!keepPages) { try { rmSync(pagedir, { recursive: true, force: true }); } catch {} }
};
process.on('exit', cleanup);
process.on('SIGINT', () => { cleanup(); process.exit(130); });

async function wsUrl() {
  for (let i = 0; i < 80; i++) {
    try {
      const cdpPort = readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
      const r = await fetch(`http://127.0.0.1:${cdpPort}/json/version`);
      const j = await r.json();
      if (j.webSocketDebuggerUrl) return j.webSocketDebuggerUrl;
    } catch {}
    await sleep(150);
  }
  throw new Error('chrome never came up');
}

const ws = new WebSocket(await wsUrl());
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

let id = 0;
const pending = new Map();
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id != null && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
function send(method, params = {}, sessionId) {
  const mid = ++id;
  return new Promise(res => {
    pending.set(mid, res);
    ws.send(JSON.stringify({ id: mid, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
}

const { result: { targetId } } = await send('Target.createTarget', { url: 'about:blank' });
const { result: { sessionId: S } } = await send('Target.attachToTarget', { targetId, flatten: true });
await send('Page.enable', {}, S);
await send('Runtime.enable', {}, S);
await send('Emulation.setDeviceMetricsOverride',
  { width: VIEW_W, height: VIEW_H, deviceScaleFactor: 1, mobile: false }, S);
// printToPDF lays out with print media rules by default; the player is a screen
// app and has no print stylesheet, so force screen media and supply the page box
// ourselves below.
await send('Emulation.setEmulatedMedia', { media: 'screen' }, S);

async function evaluate(expr) {
  const r = await send('Runtime.evaluate',
    { expression: expr, returnByValue: true, awaitPromise: true }, S);
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
  return r.result?.result?.value;
}

const url = `http://127.0.0.1:${port}/external/class.html?deck=${encodeURIComponent(deck)}&student`;
await send('Page.navigate', { url }, S);
await sleep(2500);

// Everything that is chrome rather than slide, plus the page box.  Injected at
// runtime and never added to assets/class.html: the player is hers, and a print
// stylesheet in it would be one more thing to keep true.
const PRINT_CSS = [
  `@page { size: ${PAGE_W_IN}in ${PAGE_H_IN}in; margin: 0 }`,
  `*,*::before,*::after { transition: none !important; animation: none !important }`,
  `html, body { width: ${VIEW_W}px !important; height: ${VIEW_H}px !important;`,
  `             margin: 0 !important; overflow: hidden !important; background: #fff }`,
  // The projector furniture: slide counter, nav, badges, pen palette, review UI.
  `#bar, #ink, #toast, #slideedit, #review, #reviewbar, #comment { display: none !important }`,
  // With #bar gone the stage should own the whole page.
  `#stage-wrap { inset: 0 !important }`,
  /* Deliberately NOT overriding the code font.  A missing `|` in a code block
     looked like a font-embedding problem and is not: Chrome embeds the glyph
     correctly and the loss happened later, in concatenation.  Forcing a font
     here would only make the handout differ from the projector.  See the note
     on pdf_concat.py at the bottom of this file. */
].join('\n');

await evaluate(`(() => {
  const s = document.createElement('style');
  s.textContent = ${JSON.stringify(PRINT_CSS)};
  document.head.appendChild(s);
  return getComputedStyle(document.body).height;
})()`);

/* The player keeps its `deck` inside a closure -- nothing is on `window` -- so
   the count comes off the slide counter it renders, "3 / 35".  That is also the
   one number guaranteed to match what the player will actually page through,
   which a re-read of the deck JSON would not be if the two ever disagreed. */
const count = await evaluate(`(() => {
  const t = (document.getElementById('pos') || {}).textContent || '';
  const m = t.match(/\\/\\s*(\\d+)/);
  return m ? Number(m[1]) : 0;
})()`);
if (!count) {
  const err = await evaluate(`((document.getElementById('err') || {}).textContent || '').trim()`);
  console.error(`${deck}: no slides found${err ? ` -- the player says: ${err}` : ''}`);
  console.error('  (is the web-deck build being served on this port?)');
  process.exit(1);
}

const pages = [];
for (let i = 1; i <= count; i++) {
  await evaluate(`location.hash = '${i}'`);
  await sleep(340);
  // MathJax typesets lazily; printing mid-typeset drops the formula.
  await evaluate(`(async () => { if (window.MathJax && MathJax.typesetPromise) { try { await MathJax.typesetPromise() } catch(e){} } return true })()`);
  /* Any figure on this slide must have decoded, or it prints as a blank box.
     Every wait here is RACED against a deadline: an <img> that is lazy, hidden
     or already failed can fire neither load nor error, and an unraced await on
     it hangs the run forever with no output (it did, on slide 1 of day1). */
  await evaluate(`(async () => {
    const deadline = ms => new Promise(r => setTimeout(r, ms));
    const imgs = [...document.querySelectorAll('#stage img')].filter(im => !im.complete);
    await Promise.race([
      Promise.all(imgs.map(im => new Promise(r => {
        im.addEventListener('load', r, { once: true });
        im.addEventListener('error', r, { once: true });
      }))),
      deadline(4000),
    ]);
    if (document.fonts && document.fonts.ready) {
      try { await Promise.race([document.fonts.ready, deadline(2000)]) } catch (e) {}
    }
    return true;
  })()`);
  await sleep(120);

  const r = await send('Page.printToPDF', {
    paperWidth: PAGE_W_IN, paperHeight: PAGE_H_IN,
    marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0,
    printBackground: true, preferCSSPageSize: true, scale: 1,
    transferMode: 'ReturnAsBase64',
  }, S);
  if (!r.result?.data) { console.error(`${deck}: slide ${i} did not print`); process.exit(1); }
  const p = join(pagedir, `${String(i).padStart(3, '0')}.pdf`);
  writeFileSync(p, Buffer.from(r.result.data, 'base64'));
  pages.push(p);
  process.stderr.write(`\r${deck}: ${i}/${count} slides`);
}
process.stderr.write('\n');

/* One PDF per deck.  NOT with ghostscript, though it is right here and is the
   obvious tool: `gs -sDEVICE=pdfwrite` rebuilds each embedded font subset and
   gets it wrong on Chrome's, which cost the `|` in the bitwise-OR listing on
   day1 slide 20 -- a tofu box in place of the operator, in a deck teaching
   that operator.  pdf_concat.py copies the page objects instead, so the font
   programs arrive exactly as Chrome wrote them, and re-encodes only the
   oversized rasters (13.6 MB -> 2.1 MB on day1).  Its header has the evidence. */
const out = join(outdir, `${deck}.pdf`);
const listFile = join(pagedir, 'pages.txt');
writeFileSync(listFile, pages.join('\n') + '\n');
const cat = spawnSync('python3', ['scripts/pdf_concat.py', out, '--from-list', listFile],
  { stdio: ['ignore', 'inherit', 'inherit'] });
if (cat.status !== 0) { console.error(`${deck}: concatenation failed (${cat.status})`); process.exit(1); }

const kb = Math.round(statSync(out).size / 1024);
console.log(`${deck}: ${count} slides -> ${out} (${kb} kB)`);
if (keepPages) console.log(`  per-slide pages kept in ${pagedir}`);

/* Exit explicitly.  The open WebSocket to Chrome is a live handle, so without
   this the event loop never drains and the process sits there FINISHED -- PDF
   written, success line printed -- but never exiting.  In a loop over decks
   that reads as a hang on the NEXT deck (make-slide-pdfs.sh blocked ~13 min on
   an already-complete day1 before this was found), which is a much more
   confusing symptom than a crash. */
try { ws.close(); } catch {}
process.exit(0);

// Book review comments: circle part of a page, type what should change, and
// the comment queues for a Claude session — the book-side twin of the deck
// player's review mode (see the "slide review" block in assets/class.html).
//
//   ◎ Review button (bottom right) or R  -> arm/disarm review mode
//   drag a lasso around anything          -> comment box pops up
//   ⌘⏎ / Send                             -> queued in reviews/slide-comments.jsonl
//   ← / →                                 -> previous/next page, without leaving
//                                            review mode (see navPage below)
//
// Loaded by assets/ptx-edit.js (one html.js.extra slot, two layers), so it
// exists only in the web-edit authoring build, never in a deployed book. It
// is also inert on its own: the button appears only when the review server
// (scripts/review-server.py, port 8928) answers.
//
// A book page scrolls and reflows, so — unlike the deck's fixed 16:9 stage —
// coordinates alone would rot. Comments therefore anchor three ways at once:
//   1. bbox + stroke in DOCUMENT pixels, plus the viewport width at comment
//      time, so a headless render at that width reproduces the layout;
//   2. the PreTeXt blocks under the lasso (id + tag + text excerpt);
//   3. best-effort, the edit server's /locate answer for the primary block —
//      the exact source/*.ptx file and line, when :8927 is up.
(function () {
  'use strict'
  if (!/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return

  var REVIEW_SERVER = 'http://127.0.0.1:' + ((window.COURSE || {}).reviewPort || 8928)
  var EDIT_SERVER = 'http://127.0.0.1:' + ((window.COURSE || {}).editPort || 8927)
  // Blocks worth anchoring a comment to. Innermost wins; see anchorsFor().
  var ANCHORS = '.para, li, figure, .figure-like, .image-box, table, pre, blockquote, article, h1, h2, h3, h4, h5, h6, .heading, .sim-embed'

  var css = document.createElement('style')
  css.textContent =
    '#ptx-review-btn { position: fixed; right: 16px; bottom: 16px; z-index: 3000; display: none;' +
    '  font: 14px system-ui, sans-serif; padding: 6px 14px; border-radius: 20px; cursor: pointer;' +
    '  background: #fff; color: #1a1a19; border: 1.5px solid #d98324; box-shadow: 0 2px 10px rgba(0,0,0,.15); }' +
    '#ptx-review-btn.on { background: #d98324; color: #fff; }' +
    '#ptx-review-overlay { position: fixed; inset: 0; z-index: 2990; display: none; cursor: crosshair; }' +
    '#ptx-review-overlay.on { display: block; }' +
    '#ptx-review-overlay canvas { position: absolute; inset: 0; width: 100%; height: 100%; }' +
    '#ptx-review-box { position: fixed; z-index: 3010; width: 24em; max-width: 80vw; background: #fff;' +
    '  border: 1px solid #d98324; border-radius: 8px; box-shadow: 0 6px 24px rgba(0,0,0,.25);' +
    '  padding: .6em; display: none; font: 14px system-ui, sans-serif; }' +
    '#ptx-review-box.on { display: block; }' +
    '#ptx-review-box textarea { width: 100%; height: 5em; box-sizing: border-box; resize: vertical;' +
    '  font: inherit; border: 1px solid #ccc9c0; border-radius: 5px; padding: .45em .55em; }' +
    '#ptx-review-box .rv-row { display: flex; gap: .5em; align-items: center; margin-top: .5em; }' +
    '#ptx-review-box .rv-hint { flex: 1; color: #86847c; font-size: .85em; }' +
    '#ptx-review-box button { font: inherit; border-radius: 5px; padding: .3em .9em; cursor: pointer;' +
    '  border: 1px solid #ccc9c0; background: #f4f2ee; }' +
    '#ptx-review-box button.rv-send { background: #d98324; border-color: #d98324; color: #fff; font-weight: 600; }' +
    '#ptx-review-toast { position: fixed; z-index: 3020; left: 50%; transform: translateX(-50%); bottom: 60px;' +
    '  background: rgba(20,20,19,.92); color: #f2f2f2; padding: .5em 1em; border-radius: 6px;' +
    '  font: 13px system-ui, sans-serif; display: none; max-width: 80vw; }' +
    '#ptx-review-toast.err { background: #8e2a20; }' +
    '#ptx-review-pins { position: absolute; top: 0; left: 0; width: 0; height: 0; z-index: 2980; }' +
    '.ptx-review-pin { position: absolute; width: 22px; height: 22px; margin: -11px 0 0 -11px;' +
    '  border-radius: 50%; background: #d98324; color: #fff; font: 700 12px system-ui, sans-serif;' +
    '  display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 4px rgba(0,0,0,.4);' +
    '  cursor: help; }'
  document.head.appendChild(css)

  var overlay = document.createElement('div')
  overlay.id = 'ptx-review-overlay'
  var canvas = document.createElement('canvas')
  overlay.appendChild(canvas)
  var ctx = canvas.getContext('2d')
  var box = document.createElement('div')
  box.id = 'ptx-review-box'
  box.innerHTML =
    '<textarea placeholder="What should change here?"></textarea>' +
    '<div class="rv-row"><span class="rv-hint">⌘⏎ sends · Esc cancels</span>' +
    '<button type="button" class="rv-cancel">Cancel</button>' +
    '<button type="button" class="rv-send">Send</button></div>'
  var toastEl = document.createElement('div')
  toastEl.id = 'ptx-review-toast'
  // Persistent markers for comments still waiting in the queue for THIS
  // page — so a comment that's been sent (and thus cleared from the lasso)
  // doesn't disappear from view. A marker vanishes on its own once "check
  // my review comments" archives the line out of reviews/slide-comments.jsonl.
  var pinsLayer = document.createElement('div')
  pinsLayer.id = 'ptx-review-pins'
  var btn = document.createElement('button')
  btn.id = 'ptx-review-btn'
  btn.type = 'button'
  btn.title = 'Review mode — circle something and comment; queues for Claude (R)'
  btn.innerHTML = '◎ Review'
  document.body.appendChild(overlay)
  document.body.appendChild(box)
  document.body.appendChild(toastEl)
  document.body.appendChild(pinsLayer)
  document.body.appendChild(btn)
  var field = box.querySelector('textarea')

  var reviewOn = false
  var lasso = null      // stroke in progress, DOCUMENT px
  var pending = null    // finished lasso awaiting its comment

  var toastTimer = null
  function toast (message, isErr) {
    toastEl.textContent = message
    toastEl.className = isErr ? 'err' : ''
    toastEl.style.display = 'block'
    clearTimeout(toastTimer)
    toastTimer = setTimeout(function () { toastEl.style.display = 'none' }, isErr ? 6000 : 3200)
  }

  // Document coords survive scrolling; the canvas is repainted per scroll.
  function docPoint (e) {
    return [Math.round(e.clientX + window.scrollX), Math.round(e.clientY + window.scrollY)]
  }
  function sizeCanvas () {
    var dpr = window.devicePixelRatio || 1
    var w = Math.max(1, Math.round(overlay.clientWidth * dpr))
    var h = Math.max(1, Math.round(overlay.clientHeight * dpr))
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.lineCap = ctx.lineJoin = 'round'
  }
  function drawLasso () {
    sizeCanvas()
    ctx.clearRect(0, 0, overlay.clientWidth, overlay.clientHeight)
    var pts = (lasso || pending || {}).pts
    if (!pts || pts.length < 2) return
    ctx.strokeStyle = '#d98324'
    ctx.lineWidth = 2.5
    ctx.setLineDash([7, 5])
    ctx.beginPath()
    ctx.moveTo(pts[0][0] - window.scrollX, pts[0][1] - window.scrollY)
    for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0] - window.scrollX, pts[i][1] - window.scrollY)
    ctx.stroke()
    ctx.setLineDash([])
  }
  function clearLasso () {
    lasso = null
    pending = null
    box.classList.remove('on')
    drawLasso()
  }

  /* Review mode is STICKY across page turns (sessionStorage): reviewing a
     chapter means walking its pages, and re-arming on every page would make
     the walk miserable. Per-tab on purpose — a fresh tab starts clean. */
  function setReview (on) {
    reviewOn = on
    overlay.classList.toggle('on', on)
    btn.classList.toggle('on', on)
    if (!on) clearLasso()
    else toast('Review mode — circle something, then type. ← → turn the page. R or Esc leaves.')
    try { sessionStorage.setItem('ptx:review:on', on ? '1' : '') } catch (e) {}
  }
  btn.addEventListener('click', function () { setReview(!reviewOn) })

  // Pins are independent of review mode — they show whether or not you're
  // actively circling, so reopening or reloading a page surfaces what's
  // still outstanding on it. Book pages reflow, so a pin's position is
  // rescaled by the ratio between the page's current width and the width
  // it was captured at; close enough after reflow, and click-to-reveal
  // covers the rest.
  var pinComments = []
  function renderPins () {
    pinsLayer.innerHTML = ''
    pinComments.forEach(function (c, i) {
      if (!c.bbox) return
      var scale = c.viewportWidth ? window.innerWidth / c.viewportWidth : 1
      var pin = document.createElement('div')
      pin.className = 'ptx-review-pin'
      pin.style.left = (c.bbox.x * scale) + 'px'
      pin.style.top = (c.bbox.y * scale) + 'px'
      pin.textContent = String(i + 1)
      pin.title = c.text
      pin.addEventListener('click', function (e) {
        e.stopPropagation()
        toast((i + 1) + ': ' + c.text)
      })
      pinsLayer.appendChild(pin)
    })
  }
  function refreshPins () {
    var page = location.pathname.split('/').pop()
    fetch(REVIEW_SERVER + '/slide-comments').then(function (r) { return r.json() }).then(function (all) {
      pinComments = all.filter(function (c) { return c.kind === 'book' && c.page === page })
      renderPins()
    }).catch(function () {})
  }

  overlay.addEventListener('pointerdown', function (e) {
    if (box.classList.contains('on')) return   // finish the open comment first
    e.preventDefault()
    try { overlay.setPointerCapture(e.pointerId) } catch (err) {}
    lasso = { pts: [docPoint(e)] }
  })
  overlay.addEventListener('pointermove', function (e) {
    if (!lasso) return
    e.preventDefault()
    var p = docPoint(e)
    var last = lasso.pts[lasso.pts.length - 1]
    if (Math.abs(p[0] - last[0]) > 3 || Math.abs(p[1] - last[1]) > 3) {
      if (lasso.pts.length < 400) lasso.pts.push(p)
      drawLasso()
    }
  })
  overlay.addEventListener('pointerup', function (e) {
    if (!lasso) return
    if (lasso.pts.length < 3) { clearLasso(); return }   // a stray click
    pending = lasso
    lasso = null
    openBox(e)
  })
  overlay.addEventListener('touchmove', function (e) { e.preventDefault() }, { passive: false })
  window.addEventListener('scroll', function () { if (reviewOn) drawLasso() }, { passive: true })
  window.addEventListener('resize', function () { if (reviewOn) drawLasso() })

  function openBox (e) {
    box.classList.add('on')
    var bw = box.offsetWidth, bh = box.offsetHeight
    var x = Math.min(Math.max(8, e.clientX + 14), window.innerWidth - bw - 8)
    var y = Math.min(Math.max(8, e.clientY - bh / 2), window.innerHeight - bh - 8)
    box.style.left = x + 'px'
    box.style.top = y + 'px'
    field.value = ''
    field.focus()
  }

  function bboxOf (pts) {
    var xs = pts.map(function (p) { return p[0] }), ys = pts.map(function (p) { return p[1] })
    var x0 = Math.min.apply(null, xs), y0 = Math.min.apply(null, ys)
    return { x: x0, y: y0, w: Math.max.apply(null, xs) - x0, h: Math.max.apply(null, ys) - y0 }
  }

  /* The PreTeXt blocks under the lasso, innermost first. Intersection is
     tested in document coords against each candidate's rect; a block that
     contains another hit is dropped, so circling one word of a list item
     names the <li>, not also the list, the section and the page. */
  function anchorsFor (bb) {
    var content = document.getElementById('ptx-content') || document.body
    var hits = []
    var nodes = content.querySelectorAll(ANCHORS)
    for (var i = 0; i < nodes.length; i++) {
      var r = nodes[i].getBoundingClientRect()
      var x = r.left + window.scrollX, y = r.top + window.scrollY
      var ix = Math.max(0, Math.min(bb.x + bb.w, x + r.width) - Math.max(bb.x, x))
      var iy = Math.max(0, Math.min(bb.y + bb.h, y + r.height) - Math.max(bb.y, y))
      var inter = ix * iy
      if (!inter) continue
      var overBlock = inter / Math.max(1, r.width * r.height)
      var overLasso = inter / Math.max(1, bb.w * bb.h)
      if (overBlock > 0.3 || overLasso > 0.5) hits.push(nodes[i])
    }
    hits = hits.filter(function (n) {
      return !hits.some(function (m) { return m !== n && n.contains(m) })
    })
    return hits.slice(0, 6).map(function (n) {
      var withId = n
      while (withId && !withId.id) withId = withId.parentElement
      return {
        id: withId ? withId.id : '',
        tag: n.tagName.toLowerCase() + (n.className ? '.' + String(n.className).split(' ')[0] : ''),
        excerpt: (n.innerText || n.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 140),
      }
    })
  }

  // Best-effort: the edit server can name the source file and line for the
  // primary anchored block. Waits briefly, never blocks the comment.
  function locateSource (anchor) {
    if (!anchor || !anchor.excerpt) return Promise.resolve(null)
    var url = EDIT_SERVER + '/locate?text=' + encodeURIComponent(anchor.excerpt) +
      '&id=' + encodeURIComponent(anchor.id)
    return Promise.race([
      fetch(url).then(function (r) { return r.json() }).then(function (b) {
        return b && b.file ? { file: b.file, line: b.line } : null
      }),
      new Promise(function (resolve) { setTimeout(function () { resolve(null) }, 1500) }),
    ]).catch(function () { return null })
  }

  function send () {
    var text = field.value.trim()
    if (!text || !pending) return
    var bb = bboxOf(pending.pts)
    var anchors = anchorsFor(bb)
    var payload = {
      ts: new Date().toISOString(),
      kind: 'book',
      page: location.pathname.split('/').pop(),
      docTitle: document.title,
      url: location.href,
      viewportWidth: window.innerWidth,
      bbox: bb,
      stroke: pending.pts,
      anchors: anchors,
      text: text,
    }
    locateSource(anchors[0]).then(function (src) {
      if (src) payload.source = src
      post(payload)
        .then(function (queued) {
          clearLasso()
          refreshPins()
          toast('✓ queued for Claude — ' + queued + ' waiting')
        })
        .catch(function () {
          // Same offline outbox as the deck player: buffer in this browser,
          // flush when the review server answers again.
          try {
            var out = outbox()
            out.push(payload)
            localStorage.setItem(OUTBOX_KEY, JSON.stringify(out))
            clearLasso()
            toast('⏳ saved in this browser (' + out.length + ') — sends itself when the review server is back')
            scheduleFlush()
          } catch (err) {
            toast('Could not send or save — start the review server: python3 scripts/review-server.py', true)
          }
        })
    })
  }
  function post (payload) {
    // No Content-Type header: a "simple" CORS request, no preflight to fail.
    return fetch(REVIEW_SERVER + '/slide-comment', { method: 'POST', body: JSON.stringify(payload) })
      .then(function (res) { return res.json() })
      .then(function (body) {
        if (!body.ok) throw new Error(body.error || 'refused')
        return body.queued
      })
  }

  var OUTBOX_KEY = 'ptx:review:outbox'
  function outbox () {
    try {
      var p = JSON.parse(localStorage.getItem(OUTBOX_KEY) || '[]')
      return Array.isArray(p) ? p : []
    } catch (e) { return [] }
  }
  var flushTimer = null
  function scheduleFlush () {
    clearTimeout(flushTimer)
    flushTimer = setTimeout(flushOutbox, 15000)
  }
  function flushOutbox () {
    clearTimeout(flushTimer)
    var out = outbox()
    if (!out.length) return
    post(out[0])
      .then(function (queued) {
        var rest = outbox().filter(function (c) { return c.ts !== out[0].ts })
        localStorage.setItem(OUTBOX_KEY, JSON.stringify(rest))
        if (rest.length) flushOutbox()
        else { refreshPins(); toast('✓ saved comments sent — ' + queued + ' waiting for Claude') }
      })
      .catch(function () { scheduleFlush() })
  }

  box.querySelector('.rv-send').addEventListener('click', send)
  box.querySelector('.rv-cancel').addEventListener('click', clearLasso)
  field.addEventListener('keydown', function (e) {
    e.stopPropagation()
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); send() }
    else if (e.key === 'Escape') clearLasso()
  })
  /* Page turns from the keyboard, so reviewing a chapter never means leaving
     review mode. The overlay covers the viewport, so PreTeXt's own Next and
     Previous buttons are unclickable while armed; ← and → follow the same
     links instead. Up/Down are left alone — they still scroll the page. */
  function navPage (dir) {
    var link = document.querySelector('a.' + (dir > 0 ? 'next' : 'previous') + '-button[href]')
    if (!link) { toast(dir > 0 ? 'Last page of the book.' : 'First page of the book.'); return }
    location.href = link.getAttribute('href')
  }

  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return
    var t = e.target
    if (t && (t.tagName === 'TEXTAREA' || t.tagName === 'INPUT' || t.isContentEditable)) return
    if (e.key === 'r' || e.key === 'R') setReview(!reviewOn)
    else if (e.key === 'Escape' && reviewOn) setReview(false)
    else if (reviewOn && (e.key === 'ArrowRight' || e.key === 'ArrowLeft')) {
      // An unsent comment comes first — turning the page would lose it.
      if (box.classList.contains('on')) return
      e.preventDefault()
      navPage(e.key === 'ArrowRight' ? 1 : -1)
    }
  })

  window.addEventListener('resize', function () { renderPins() })
  // Reasserting focus (e.g. coming back from a Claude session that just
  // archived a comment) is the cheapest moment to notice a pin should now
  // be gone.
  window.addEventListener('focus', refreshPins)

  // Appear only when the review server answers (nothing here works without
  // it); re-arm if this tab was already reviewing or the URL asks for it.
  fetch(REVIEW_SERVER + '/health').then(function (r) { return r.json() }).then(function (body) {
    if (!body.ok) return
    btn.style.display = 'block'
    var sticky = false
    try { sticky = sessionStorage.getItem('ptx:review:on') === '1' } catch (e) {}
    if (sticky || new URLSearchParams(location.search).has('review')) setReview(true)
    flushOutbox()
    refreshPins()
  }).catch(function () {
    if (outbox().length) scheduleFlush()   // server down: stay inert, outbox keeps trying
  })
})()

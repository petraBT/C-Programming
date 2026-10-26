// In-class "follow me" mode and the line to the live session (polls, written answers).
// Shared slide tooling: edit it in slide-tooling and sync, never in a book. Per-course
// settings come from window.COURSE (assets/course.js), so a page that loads this must load
// course.js first (the book's html.js.extra points at a two-line loader that does).
//
// Completely inert for normal readers: it only does anything when this browser TAB is
// part of a class session.
//
// Instructor: open any book page or deck with  ?classroom=start   -> becomes the
//   session lead, gets a short code + join link in a bottom banner. Every
//   page they navigate to is broadcast to the session.
// Students: open any book page or deck with    ?classroom=<CODE>  -> banner appears
//   and their tab follows the instructor's navigation until they Leave (or
//   close the tab - the session is per-tab, so a link opened in a NEW tab,
//   like a popped-out coding window, is intentionally not dragged along).
// Second device: the lead's banner has a "Copy second-device link" button; opened elsewhere
//   (?classroom=<CODE>&presenter=<KEY>) it follows like a student but also sees poll answers
//   privately and can reveal them (the deck player does that part; see window.DeckSession).
//
// Transport: WebSocket to /session/<CODE>. Where to is COURSE.sessionOrigin ("wss://host"),
// or the page's own origin when unset (ENGS 20: a Pages Function forwarding to the Durable
// Object, functions/session/[code].js). On localhost, where there is no such function, it
// uses COURSE.localSessionOrigin (or sessionOrigin) so the feature is still testable.
//
// Security note: the only power a lead has over followers is navigation, and
// both the server and this client require the target to be a same-origin
// PATH ("/...", never "//..." or a full URL) - so even a hijacked session
// code can only flip pages within the book itself.
(function () {
  'use strict'

  var COURSE_CFG = window.COURSE || {}
  var STORE_KEY = 'classroom-session'
  var CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789' // no 0/O/1/I/L lookalikes

  // --- join / start via URL parameter, then hide it from the URL ---------

  var params = new URLSearchParams(location.search)
  var requested = params.get('classroom')
  var presenterKey = params.get('presenter')
  // A second device (a tablet, say) that the instructor joins as a PRESENTER: it follows the
  // lead's slides like a student, but also sees the poll answers as they arrive and can
  // reveal them. It proves itself with the key the lead's banner hands out, never with the
  // session code alone, which students know.
  var KEY_ALPHABET = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  function randomKey(n) {
    var out = '', bytes = new Uint8Array(n)
    ;(window.crypto || window.msCrypto).getRandomValues(bytes)
    for (var i = 0; i < n; i++) out += KEY_ALPHABET[bytes[i] % KEY_ALPHABET.length]
    return out
  }
  if (requested) {
    var sess
    if (requested === 'start') {
      var code = ''
      for (var i = 0; i < 4; i++) code += CODE_ALPHABET[Math.floor(Math.random() * CODE_ALPHABET.length)]
      sess = {code: code, role: 'lead', key: randomKey(20)}
    } else if (presenterKey && /^[A-Za-z0-9]{8,64}$/.test(presenterKey)) {
      sess = {code: requested.toUpperCase(), role: 'presenter', key: presenterKey}
    } else {
      sess = {code: requested.toUpperCase(), role: 'follow'}
    }
    sessionStorage.setItem(STORE_KEY, JSON.stringify(sess))
    params.delete('classroom')
    params.delete('presenter')
    var qs = params.toString()
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash)
  }

  var raw = sessionStorage.getItem(STORE_KEY)
  if (!raw) return // not in a session: this script is a no-op
  var session
  try {
    session = JSON.parse(raw)
  } catch (e) {
    sessionStorage.removeItem(STORE_KEY)
    return
  }
  if (!session || !/^[A-Z0-9]{4,8}$/.test(session.code || '')) return
  var isLead = session.role === 'lead'
  var isPresenter = session.role === 'presenter'

  // --- banner ------------------------------------------------------------

  var banner = document.createElement('div')
  banner.style.cssText =
    'position:fixed;left:0;right:0;bottom:0;z-index:99999;' +
    'background:#1a1a19;color:#f2f2f2;border-top:1px solid #383835;' +
    'font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:13px;' +
    'padding:8px 16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;'

  var dot = document.createElement('span')
  dot.style.cssText = 'width:9px;height:9px;border-radius:50%;background:#d9a441;flex:none;'
  banner.appendChild(dot)

  var label = document.createElement('span')
  banner.appendChild(label)

  var countEl = document.createElement('span')
  countEl.style.color = '#c3c2b7'
  banner.appendChild(countEl)

  var spacer = document.createElement('span')
  spacer.style.flex = '1'
  banner.appendChild(spacer)

  var exitBtn = document.createElement('button')
  exitBtn.type = 'button'
  exitBtn.textContent = isLead ? 'End session' : 'Leave'
  exitBtn.style.cssText =
    'font-size:12px;color:#ccc;background:transparent;border:1px solid #444;' +
    'border-radius:4px;padding:4px 10px;cursor:pointer;'
  banner.appendChild(exitBtn)

  if (isLead) {
    label.innerHTML = ''
    var strong = document.createElement('strong')
    strong.textContent = 'Leading class session ' + session.code
    label.appendChild(strong)
    var join = document.createElement('span')
    join.style.color = '#c3c2b7'
    // Deliberately the CURRENT page's path (with its query), not the site
    // root: the root index.html is a bare PreTeXt redirect page that carries
    // no scripts and drops the query string, so a root join link would
    // silently do nothing. Keeping location.search means a deck link carries
    // its ?deck=<code>, so a student lands on the right deck rather than the
    // deck chooser. (Followers also snap to the lead's page once the socket
    // connects, but starting on the deck avoids a chooser flash.)
    var joinParams = new URLSearchParams(location.search)
    joinParams.set('classroom', session.code)
    join.textContent = ' · students join at ' +
      location.origin + location.pathname + '?' + joinParams.toString()
    label.appendChild(join)
    // The second-device link: opens this deck as a presenter (see above). It carries the
    // key, so it is shown only as a button, never written on the screen, because the
    // banner is on the projector.
    var secondBtn = document.createElement('button')
    secondBtn.type = 'button'
    secondBtn.textContent = 'Copy second-device link'
    secondBtn.title = 'Open this on your tablet or phone to see poll answers privately and reveal them'
    secondBtn.style.cssText =
      'font-size:12px;color:#ccc;background:transparent;border:1px solid #444;' +
      'border-radius:4px;padding:4px 10px;cursor:pointer;'
    secondBtn.addEventListener('click', function () {
      var pp = new URLSearchParams(location.search)
      pp.set('classroom', session.code)
      pp.set('presenter', session.key)
      var link = location.origin + location.pathname + '?' + pp.toString()
      var done = function (ok) {
        secondBtn.textContent = ok ? 'Copied - send it to your other device' : 'Copy failed: select it from the prompt'
        if (!ok) window.prompt('Second-device link (keep it private):', link)
        setTimeout(function () { secondBtn.textContent = 'Copy second-device link' }, 4000)
      }
      try { navigator.clipboard.writeText(link).then(function () { done(true) }, function () { done(false) }) }
      catch (err) { done(false) }
    })
    banner.insertBefore(secondBtn, spacer)
  } else if (isPresenter) {
    label.textContent = 'Second device for class session ' + session.code + ' (private view)'
  } else {
    label.textContent = 'Following class session ' + session.code
  }

  function mountBanner() {
    document.body.appendChild(banner)
    // Keep the page's own bottom content reachable above the fixed bar.
    document.body.style.paddingBottom = '46px'
    // On the deck player (assets/class.html) the stage is absolutely positioned, so padding
    // does nothing and the fixed banner would sit on top of the player's own bar (draw, colours,
    // eraser, undo, arrows). The player reserves --stage-inset-bottom for exactly this.
    if (document.getElementById('stage')) {
      var reserve = function () {
        document.documentElement.style.setProperty('--stage-inset-bottom', banner.offsetHeight + 'px')
      }
      reserve()
      if (window.ResizeObserver) new ResizeObserver(reserve).observe(banner)
      else window.addEventListener('resize', reserve)
    }
  }
  if (document.body) mountBanner()
  else document.addEventListener('DOMContentLoaded', mountBanner)

  var ended = false
  exitBtn.addEventListener('click', function () {
    ended = true
    sessionStorage.removeItem(STORE_KEY)
    try { ws && ws.close() } catch (e) {}
    banner.remove()
    window.DeckSession = undefined
    document.body.style.paddingBottom = ''
    document.documentElement.style.removeProperty('--stage-inset-bottom')
  })

  // --- websocket ---------------------------------------------------------

  // Where the session server is. A deployed page uses COURSE.sessionOrigin if set, else its own
  // origin (a doorway on the same site). A page on localhost has no doorway, so it uses the
  // deployed server named in the course settings. ?wsorigin= (localhost pages only, and only to a
  // localhost server) points it at a worker started with `wrangler dev`, for testing.
  var testOrigin = params.get('wsorigin')
  var isLocal = /^(localhost|127\.0\.0\.1)$/.test(location.hostname)
  var wsOrigin = isLocal
    ? (testOrigin && /^wss?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(testOrigin)
        ? testOrigin
        : (COURSE_CFG.sessionOrigin || COURSE_CFG.localSessionOrigin || location.origin.replace(/^http/, 'ws')))
    : (COURSE_CFG.sessionOrigin || location.origin.replace(/^http/, 'ws'))

  var ws = null
  var retryDelay = 1000

  // --- the page's own line to the session (polls) -------------------------
  // The deck player (a different script) shows poll slides and needs to vote, reveal and
  // hear tallies, over this same socket. It gets window.DeckSession: send(obj) (queued
  // until connected), and on(type, fn). Messages that describe the CURRENT state (the
  // snapshot, tallies, reveals) are kept and replayed to a listener that registers late.
  var outbox = []
  var listeners = {}
  var kept = {}
  function deliver(msg) {
    if (msg.type === 'state' || msg.type === 'tally' || msg.type === 'reveal' || msg.type === 'reset' ||
        msg.type === 'shared' || msg.type === 'pick') {
      var k = msg.type + ':' + (msg.slide || '')
      if (msg.type === 'reset') {
        ;['tally:', 'reveal:', 'shared:', 'pick:'].forEach(function (pre) { delete kept[pre + msg.slide] })
      } else kept[k] = msg
    }
    ;(listeners[msg.type] || []).forEach(function (fn) { try { fn(msg) } catch (err) { console.error(err) } })
  }
  window.DeckSession = {
    code: session.code,
    role: session.role,
    wsUrl: wsOrigin + '/session/' + session.code,
    send: function (obj) {
      if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj))
      else outbox.push(obj)
    },
    on: function (type, fn) {
      ;(listeners[type] = listeners[type] || []).push(fn)
      Object.keys(kept).forEach(function (k) { if (kept[k].type === type) { try { fn(kept[k]) } catch (err) { console.error(err) } } })
    }
  }

  function currentPath() {
    // Includes the query string: the deck player identifies its slide deck by
    // ?deck=<code>, so a path without it would drop a follower onto the deck
    // chooser instead of the lead's deck. (Book pages carry no query, so this
    // is a no-op there.)
    return location.pathname + location.search + location.hash
  }

  function safePath(p) {
    return typeof p === 'string' && p.charAt(0) === '/' && p.charAt(1) !== '/'
  }

  function setConnected(ok) {
    dot.style.background = ok ? '#0ca30c' : '#d9a441'
  }

  function connect() {
    if (ended) return
    ws = new WebSocket(wsOrigin + '/session/' + session.code)

    ws.onopen = function () {
      retryDelay = 1000
      setConnected(true)
      ws.send(JSON.stringify({type: 'hello', role: session.role, key: session.key}))
      if (isLead) ws.send(JSON.stringify({type: 'navigate', path: currentPath()}))
      while (outbox.length) ws.send(JSON.stringify(outbox.shift()))
    }

    ws.onmessage = function (e) {
      var msg
      try { msg = JSON.parse(e.data) } catch (err) { return }
      if (!isLead && (msg.type === 'navigate' || msg.type === 'state') && safePath(msg.path)) {
        if (msg.path !== currentPath()) location.href = msg.path
      }
      deliver(msg)
      if (msg.type === 'count' || msg.type === 'state') {
        if (isLead) countEl.textContent = '· ' + msg.count + ' following'
      }
    }

    ws.onclose = function () {
      setConnected(false)
      if (ended) return
      setTimeout(connect, retryDelay)
      retryDelay = Math.min(retryDelay * 2, 10000)
    }
    ws.onerror = function () {
      try { ws.close() } catch (err) {}
    }
  }
  connect()

  // Reconnect promptly when a laptop lid reopens rather than waiting out
  // the backoff timer.
  document.addEventListener('visibilitychange', function () {
    if (!ended && document.visibilityState === 'visible' && (!ws || ws.readyState === WebSocket.CLOSED)) {
      retryDelay = 1000
      connect()
    }
  })

  // PreTeXt navigation is full page loads (each one re-announces itself via
  // the hello/navigate on connect), but in-page anchor jumps only change the
  // hash - broadcast those too so followers land on the same spot.
  if (isLead) {
    window.addEventListener('hashchange', function () {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({type: 'navigate', path: currentPath()}))
      }
    })
  }
})()

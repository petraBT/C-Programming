// Realtime session backend for the book's in-class "follow me" mode.
// One Durable Object per session code; browsers connect over WebSocket.
// Protocol (all JSON):
//   client -> server:
//     {type: "hello", role: "lead"|"presenter"|"follow", key?}   first message after connect
//     {type: "vote", slide, cid, choice}      a student's poll answer (anonymous)
//     {type: "reveal"|"reset"|"export", ...}   instructor devices only (they say hello with the key)
//     {type: "navigate", path: "/..."}         lead only: current book page
//   server -> client:
//     {type: "state", path, count}    on hello: current page + follower count
//     {type: "navigate", path}        to follows when the lead turns the page
//     {type: "count", count}          follower count changed
//
// The only thing a lead can make followers do is navigate to a same-origin
// PATH (must start with "/", not "//") - the client re-checks this too, so a
// malicious "lead" who guessed a session code still can't send anyone to an
// external site, just to some page of the book.

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    const m = url.pathname.match(/^\/session\/([A-Za-z0-9]{4,8})$/)
    if (m) {
      const id = env.SESSIONS.idFromName(m[1].toUpperCase())
      return env.SESSIONS.get(id).fetch(request)
    }
    return new Response('ENGS 20 classroom session worker - see classroom-worker/ in the C-Programming repo', {
      headers: {'Content-Type': 'text/plain'},
    })
  },
}

// --- announcements board (UNUSED since 2026-10-25) -------------------------
// Announcements are now <slide kind="notice"> blocks in the book source. The Pages
// function and binding that reached this class are gone; the class itself stays only
// because deleting a Durable Object class needs a migration and a worker redeploy.
// A second, persistent Durable Object, one instance per DECK (not per session
// code, and it does not expire): it holds the "today" announcement slides an
// instructor adds to the front of a deck right before class. This is the
// server-side, browser-editable store the classroom design always intended
// for per-term ephemera, so those slides never have to be a source edit +
// build + deploy five minutes before class.
//
// Reached from the Pages origin through functions/announce/[deck].js and the
// BOARDS binding, exactly as sessions are reached through SESSIONS. GET is
// open (students load it too); the doorway checks the instructor passphrase
// before any write reaches here.
//
// Announcements are rendered ESCAPED on the client, unlike deck text, so this
// stores plain strings: the deck JSON is protected by git and the build, but
// this store is protected only by a shared passphrase, and a leaked one must
// not become stored HTML/script in every student's browser.
const ANN_MAX_ITEMS = 12          // announcement slides per deck
const ANN_MAX_LINES = 20          // bullet lines per slide
const ANN_MAX_LEN = 400           // chars per title / bullet line
const ANN_MAX_BODY = 2000         // chars in a paragraph body (roomier than a bullet)
const ANN_MAX_IMG = 500 * 1024    // chars in an image data URL (client downscales to fit)
// Only these image data URLs are ever stored or rendered. base64 alphabet
// only, so the value cannot contain a quote to break out of the img src.
const ANN_IMG_RE = /^data:image\/(png|jpe?g|gif|webp);base64,[A-Za-z0-9+/=]+$/

function annClamp(v) {
  return typeof v === 'string' ? v.slice(0, ANN_MAX_LEN) : ''
}

function sanitizeAnnouncements(input) {
  if (!Array.isArray(input)) return []
  return input.slice(0, ANN_MAX_ITEMS).map(a => {
    a = a && typeof a === 'object' ? a : {}
    const out = {type: 'announcement', title: annClamp(a.title)}
    if (Array.isArray(a.items)) {
      out.items = a.items.slice(0, ANN_MAX_LINES).map(annClamp).filter(s => s.length)
    }
    const body = typeof a.body === 'string' ? a.body.slice(0, ANN_MAX_BODY) : ''
    if (body) out.body = body
    const note = annClamp(a.note)
    if (note) out.note = note
    // Images are validated strictly (a data:image URL, base64 only) and size
    // capped. Anything else is dropped rather than stored.
    if (typeof a.image === 'string' && a.image.length <= ANN_MAX_IMG && ANN_IMG_RE.test(a.image)) {
      out.image = a.image
    }
    return out
  }).filter(a => a.title || (a.items && a.items.length) || a.body || a.image)
}

function annJson(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {'Content-Type': 'application/json', 'Cache-Control': 'no-store'},
  })
}

export class DeckBoard {
  constructor(state) {
    this.state = state
    // Stored in a SQLite row, NOT the key-value storage API: an announcement
    // may carry an embedded image, and the KV API caps a single value at
    // 128 KiB. A SQLite TEXT value has no such limit. The class is already
    // SQLite-backed (wrangler migration v2), so this needs no new migration;
    // the old KV 'announcements' value, if any, is simply left unread.
    state.storage.sql.exec('CREATE TABLE IF NOT EXISTS board (id INTEGER PRIMARY KEY, data TEXT)')
  }

  // One-time carry-over from the earlier key-value storage to the SQLite row.
  // Announcements saved before the storage switch live under the KV key
  // 'announcements'; move them into the row the first time we find the row
  // empty, then delete the old key so this runs at most once.
  async migrateLegacy(sql) {
    const legacy = await this.state.storage.get('announcements')
    if (Array.isArray(legacy) && legacy.length) {
      sql.exec('INSERT OR REPLACE INTO board (id, data) VALUES (1, ?)', JSON.stringify(legacy))
      await this.state.storage.delete('announcements')
    }
  }

  async fetch(request) {
    const sql = this.state.storage.sql
    if (request.method === 'GET') {
      let rows = sql.exec('SELECT data FROM board WHERE id = 1').toArray()
      if (!rows.length) {
        await this.migrateLegacy(sql)
        rows = sql.exec('SELECT data FROM board WHERE id = 1').toArray()
      }
      let list = []
      if (rows.length) { try { list = JSON.parse(rows[0].data) } catch { list = [] } }
      return annJson({announcements: list})
    }
    if (request.method === 'POST') {
      // The passphrase was already checked by the Pages Function doorway; a
      // request that reaches here is authorised. Sanitize anyway - the DO is
      // the last line before storage.
      let body
      try {
        body = await request.json()
      } catch {
        return annJson({error: 'bad json'}, 400)
      }
      const list = sanitizeAnnouncements(body && body.announcements)
      sql.exec('INSERT OR REPLACE INTO board (id, data) VALUES (1, ?)', JSON.stringify(list))
      return annJson({announcements: list, ok: true})
    }
    return annJson({error: 'method not allowed'}, 405)
  }
}

const PATH_OK = /^\/(?!\/)/

// --- polls (multiple choice) ------------------------------------------------
// Students vote anonymously: a vote is {slide, cid, choice}, where cid is a random id
// the student's own browser made up, so a student can change an answer and still count
// once. Nothing else identifies a vote, and the votes are never sent to students: only
// the instructor's devices (see below) see counts, and everyone sees them only after
// a reveal. Everything is deleted POLL_TTL_MS after the last activity (an alarm).
const POLL_TTL_MS = 14 * 24 * 3600 * 1000
const MAX_SLIDES = 200
const MAX_VOTERS = 3000
const KEY_OK = /^[A-Za-z0-9]{8,64}$/
const SLIDE_OK = /^[A-Za-z0-9_.:-]{1,120}$/
const CID_OK = /^[A-Za-z0-9]{6,40}$/
const CHOICE_OK = /^[A-H]$/

export class ClassSession {
  constructor(state) {
    this.state = state
    this.clients = new Map() // WebSocket -> {role, priv}
    this.path = undefined // lazily loaded from storage; null = no page yet
    this.loaded = false
    this.key = null       // the instructor key: set by the first lead to say hello
    this.votes = {}       // slide -> {cid: choice}
    this.revealed = {}    // slide -> true
  }

  async load() {
    if (this.loaded) return
    this.path = (await this.state.storage.get('path')) ?? null
    this.key = (await this.state.storage.get('key')) ?? null
    this.votes = (await this.state.storage.get('votes')) ?? {}
    this.revealed = (await this.state.storage.get('revealed')) ?? {}
    this.loaded = true
  }

  async fetch(request) {
    if (request.headers.get('Upgrade') !== 'websocket') {
      return new Response('expected a websocket', {status: 426})
    }
    await this.load()
    const pair = new WebSocketPair()
    const [client, server] = Object.values(pair)
    this.accept(server)
    return new Response(null, {status: 101, webSocket: client})
  }

  accept(ws) {
    ws.accept()
    this.clients.set(ws, {role: 'follow', priv: false})
    ws.addEventListener('message', e => this.onMessage(ws, e))
    const drop = () => {
      if (this.clients.delete(ws)) this.broadcastCount()
    }
    ws.addEventListener('close', drop)
    ws.addEventListener('error', drop)
  }

  // Counts for one slide: {A: n, B: n, ...} and the total.
  tallyOf(slide) {
    const counts = {}
    let total = 0
    for (const c of Object.values(this.votes[slide] || {})) {
      counts[c] = (counts[c] || 0) + 1
      total++
    }
    return {counts, total}
  }

  // Everything a device needs to catch up when it connects.
  snapshot(meta) {
    const reveals = {}
    for (const slide of Object.keys(this.revealed)) reveals[slide] = this.tallyOf(slide)
    const msg = {type: 'state', path: this.path, count: this.followCount(), priv: meta.priv, reveals}
    if (meta.priv) {
      msg.tallies = {}
      for (const slide of Object.keys(this.votes)) msg.tallies[slide] = this.tallyOf(slide)
    }
    return msg
  }

  async persist(what) {
    // Delete everything two weeks after the last thing that happened here.
    await this.state.storage.setAlarm(Date.now() + POLL_TTL_MS)
    if (what === 'votes') await this.state.storage.put('votes', this.votes)
    if (what === 'revealed') await this.state.storage.put('revealed', this.revealed)
  }

  async alarm() {
    for (const ws of this.clients.keys()) { try { ws.close() } catch {} }
    this.clients.clear()
    await this.state.storage.deleteAll()
    this.loaded = false
  }

  toPriv(obj) {
    for (const [sock, m] of this.clients) if (m.priv) this.send(sock, obj)
  }

  onMessage(ws, e) {
    let msg
    try {
      msg = JSON.parse(e.data)
    } catch {
      return
    }
    const meta = this.clients.get(ws)
    if (!meta || !msg || typeof msg.type !== 'string') return

    if (msg.type === 'hello') {
      if (msg.role === 'follow') {
        meta.role = 'follow'
      } else if (msg.role === 'lead' || msg.role === 'presenter') {
        const key = typeof msg.key === 'string' && KEY_OK.test(msg.key) ? msg.key : null
        if (msg.role === 'lead' && !this.key && key) {
          // The first lead to arrive with a key owns the session.
          this.key = key
          this.state.storage.put('key', key)
        }
        const keyed = !!key && key === this.key
        if (msg.role === 'lead') {
          // A lead with no key at all is an older page: it may still turn pages (as before)
          // but sees no answers.
          if (keyed || (!this.key && !key)) { meta.role = 'lead'; meta.priv = keyed }
          else meta.role = 'follow'
        } else if (keyed) {
          meta.role = 'presenter'; meta.priv = true
        } else {
          meta.role = 'follow'
        }
      } else {
        return
      }
      this.send(ws, this.snapshot(meta))
      this.broadcastCount()
      return
    }

    if (msg.type === 'navigate' && meta.role === 'lead') {
      if (typeof msg.path !== 'string' || msg.path.length > 500 || !PATH_OK.test(msg.path)) return
      this.path = msg.path
      this.state.storage.put('path', msg.path)
      for (const [sock, m] of this.clients) {
        if (m.role !== 'lead') this.send(sock, {type: 'navigate', path: msg.path})
      }
      return
    }

    if (msg.type === 'vote') {
      const {slide, cid, choice} = msg
      if (!SLIDE_OK.test(slide || '') || !CID_OK.test(cid || '') || !CHOICE_OK.test(choice || '')) return
      if (this.revealed[slide]) return   // answers are closed once the results are shown
      if (!this.votes[slide]) {
        if (Object.keys(this.votes).length >= MAX_SLIDES) return
        this.votes[slide] = {}
      }
      if (!(cid in this.votes[slide]) && Object.keys(this.votes[slide]).length >= MAX_VOTERS) return
      this.votes[slide][cid] = choice
      this.persist('votes')
      this.send(ws, {type: 'voted', slide, choice})
      this.toPriv({type: 'tally', slide, ...this.tallyOf(slide)})
      return
    }

    // Everything below is for the instructor's devices only.
    if (!meta.priv) return

    if (msg.type === 'reveal') {
      if (!SLIDE_OK.test(msg.slide || '')) return
      if (msg.on) this.revealed[msg.slide] = true
      else delete this.revealed[msg.slide]
      this.persist('revealed')
      const t = this.tallyOf(msg.slide)
      for (const sock of this.clients.keys()) {
        this.send(sock, {type: 'reveal', slide: msg.slide, on: !!msg.on, ...(msg.on ? t : {counts: {}, total: 0})})
      }
    } else if (msg.type === 'reset') {
      if (!SLIDE_OK.test(msg.slide || '')) return
      delete this.votes[msg.slide]
      delete this.revealed[msg.slide]
      this.persist('votes'); this.persist('revealed')
      for (const sock of this.clients.keys()) this.send(sock, {type: 'reset', slide: msg.slide})
    } else if (msg.type === 'export') {
      const slides = {}
      for (const slide of Object.keys(this.votes)) slides[slide] = this.tallyOf(slide)
      this.send(ws, {type: 'export', slides})
    }
  }

  followCount() {
    let n = 0
    for (const m of this.clients.values()) if (m.role === 'follow') n++
    return n
  }

  broadcastCount() {
    const count = this.followCount()
    for (const sock of this.clients.keys()) this.send(sock, {type: 'count', count})
  }

  send(ws, obj) {
    try {
      ws.send(JSON.stringify(obj))
    } catch {
      // Socket already dead - the close/error handler will clean it up.
    }
  }
}

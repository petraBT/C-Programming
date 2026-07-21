// Realtime session backend for the book's in-class "follow me" mode.
// One Durable Object per session code; browsers connect over WebSocket.
// Protocol (all JSON):
//   client -> server:
//     {type: "hello", role: "lead"|"follow"}   first message after connect
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

// --- announcements board ---------------------------------------------------
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
const ANN_MAX_ITEMS = 12   // announcement slides per deck
const ANN_MAX_LINES = 20   // bullet lines per slide
const ANN_MAX_LEN = 400    // chars per field / line

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
    const body = annClamp(a.body)
    if (body) out.body = body
    const note = annClamp(a.note)
    if (note) out.note = note
    return out
  }).filter(a => a.title || (a.items && a.items.length) || a.body)
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
  }

  async fetch(request) {
    if (request.method === 'GET') {
      const list = (await this.state.storage.get('announcements')) ?? []
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
      await this.state.storage.put('announcements', list)
      return annJson({announcements: list, ok: true})
    }
    return annJson({error: 'method not allowed'}, 405)
  }
}

const PATH_OK = /^\/(?!\/)/

export class ClassSession {
  constructor(state) {
    this.state = state
    this.clients = new Map() // WebSocket -> {role}
    this.path = undefined // lazily loaded from storage; null = no page yet
  }

  async fetch(request) {
    if (request.headers.get('Upgrade') !== 'websocket') {
      return new Response('expected a websocket', {status: 426})
    }
    if (this.path === undefined) {
      this.path = (await this.state.storage.get('path')) ?? null
    }
    const pair = new WebSocketPair()
    const [client, server] = Object.values(pair)
    this.accept(server)
    return new Response(null, {status: 101, webSocket: client})
  }

  accept(ws) {
    ws.accept()
    this.clients.set(ws, {role: 'follow'})
    ws.addEventListener('message', e => this.onMessage(ws, e))
    const drop = () => {
      if (this.clients.delete(ws)) this.broadcastCount()
    }
    ws.addEventListener('close', drop)
    ws.addEventListener('error', drop)
  }

  onMessage(ws, e) {
    let msg
    try {
      msg = JSON.parse(e.data)
    } catch {
      return
    }
    const meta = this.clients.get(ws)
    if (!meta) return

    if (msg.type === 'hello' && (msg.role === 'lead' || msg.role === 'follow')) {
      meta.role = msg.role
      this.send(ws, {type: 'state', path: this.path, count: this.followCount()})
      this.broadcastCount()
    } else if (msg.type === 'navigate' && meta.role === 'lead') {
      if (typeof msg.path !== 'string' || msg.path.length > 500 || !PATH_OK.test(msg.path)) return
      this.path = msg.path
      this.state.storage.put('path', msg.path)
      for (const [sock, m] of this.clients) {
        if (m.role === 'follow') this.send(sock, {type: 'navigate', path: msg.path})
      }
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

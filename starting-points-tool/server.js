#!/usr/bin/env node
// Small local authoring tool for C starting points - browse everything in
// CMeCodeDir/ (book) and CanvasStartDir/ (Canvas one-offs: short
// assignments, quizzes, tests), create new ones, and generate Canvas embed
// HTML for any of them. No dependencies - plain Node http/fs/path only, so
// `node starting-points-tool/server.js` is the entire setup. Binds to
// 127.0.0.1 only: this reads and writes the book repo's working tree, so
// it's not meant to be reachable from anywhere but this machine.
//
// This only ever writes into CMeCodeDir/ or CanvasStartDir/ - it doesn't
// touch git (no add/commit/push) and doesn't touch source/**/*.ptx. For a
// new BOOK starting point, this gets the .c file in place; you still add
// the actual <cmecode startPoint="..."> to the relevant chapter yourself -
// that's authoring the book's content, not something this tool should
// guess at.

const http = require('http')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const CME_CODE_DIR = path.join(ROOT, 'CMeCodeDir')
const CANVAS_START_DIR = path.join(ROOT, 'CanvasStartDir')
const SOURCE_DIR = path.join(ROOT, 'source')
const PORT = 5050

// Keeps names usable as filenames, URL path segments, and (for book mode)
// PreTeXt startPoint values all at once - deliberately conservative rather
// than trying to allow-and-escape a wider character set.
const SAFE_NAME = /^[A-Za-z0-9_-]+$/

// Categories are a folder name too, but they're meant to be read as a label
// ("Short Assignment", "Canvas Quiz") rather than a code identifier, so this
// allows spaces - still excludes "/", ".", and other path-traversal-risky
// characters. Embed URLs percent-encode each path segment separately (see
// urlForRelPath in index.html) so a space here doesn't produce a broken URL.
const SAFE_CATEGORY = /^[A-Za-z0-9 _-]+$/

function assertSafe(value, label, pattern, allowedDesc) {
  if (typeof value !== 'string' || value.trim() === '' || !pattern.test(value)) {
    throw new Error(`${label} must contain only ${allowedDesc} (got: ${JSON.stringify(value)})`)
  }
}

function assertSafeName(name, label) {
  assertSafe(name, label, SAFE_NAME, 'letters, digits, "_", "-"')
}

function assertSafeCategory(category, label) {
  assertSafe(category, label, SAFE_CATEGORY, 'letters, digits, spaces, "_", "-"')
}

// --- listing -----------------------------------------------------------

// Scans every source/**/*.ptx for startPoint="..." so a book starting point's
// "topic" can be derived from whatever chapter actually embeds it, rather
// than needing a second place to keep that in sync by hand.
function findStartPointReferences() {
  const refs = {}
  for (const file of walk(SOURCE_DIR)) {
    if (!file.endsWith('.ptx')) continue
    const text = fs.readFileSync(file, 'utf8')
    const title = (text.match(/<title>([^<]*)<\/title>/) || [])[1]
    const re = /startPoint="([^"]+)"/g
    let m
    while ((m = re.exec(text))) {
      const name = m[1]
      if (!refs[name]) refs[name] = []
      const rel = path.relative(ROOT, file)
      if (!refs[name].some(r => r.file === rel)) {
        refs[name].push({file: rel, title: title || null})
      }
    }
  }
  return refs
}

function walk(dir) {
  let results = []
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) results = results.concat(walk(full))
    else results.push(full)
  }
  return results
}

function listBookStartingPoints() {
  const refs = findStartPointReferences()
  return fs.readdirSync(CME_CODE_DIR)
    .filter(f => f.endsWith('.c'))
    .map(f => {
      const name = f.slice(0, -2)
      return {name, path: `CMeCodeDir/${f}`, referencedBy: refs[name] || []}
    })
    .sort((a, b) => a.name.localeCompare(b.name))
}

function listCanvasStartingPoints() {
  const byCategory = {}
  if (!fs.existsSync(CANVAS_START_DIR)) return byCategory
  for (const entry of fs.readdirSync(CANVAS_START_DIR, {withFileTypes: true})) {
    if (!entry.isDirectory()) continue
    const categoryDir = path.join(CANVAS_START_DIR, entry.name)
    byCategory[entry.name] = fs.readdirSync(categoryDir)
      .filter(f => f.endsWith('.c'))
      .map(f => ({name: f.slice(0, -2), path: `CanvasStartDir/${entry.name}/${f}`}))
      .sort((a, b) => a.name.localeCompare(b.name))
  }
  return byCategory
}

// --- saving --------------------------------------------------------------

function saveStartingPoint({scope, category, name, code, overwrite}) {
  assertSafeName(name, 'Name')
  if (typeof code !== 'string' || code.trim().length === 0) throw new Error('Code is empty')

  let full, relPath
  if (scope === 'book') {
    full = path.join(CME_CODE_DIR, `${name}.c`)
    relPath = `CMeCodeDir/${name}.c`
  } else if (scope === 'canvas') {
    assertSafeCategory(category, 'Category')
    const categoryDir = path.join(CANVAS_START_DIR, category)
    fs.mkdirSync(categoryDir, {recursive: true})
    full = path.join(categoryDir, `${name}.c`)
    relPath = `CanvasStartDir/${category}/${name}.c`
  } else {
    throw new Error('scope must be "book" or "canvas"')
  }

  if (fs.existsSync(full) && !overwrite) {
    throw new Error(`${relPath} already exists - pass overwrite to replace it`)
  }
  fs.writeFileSync(full, code)
  return {path: relPath}
}

function resolveContentPath(rel) {
  // rel is always one of the paths this same server just handed back from
  // /api/starting-points or /api/file - not an arbitrary client-supplied
  // path - still double-checked here rather than trusted blindly.
  const full = path.resolve(ROOT, rel)
  if (!full.startsWith(CME_CODE_DIR + path.sep) && !full.startsWith(CANVAS_START_DIR + path.sep)) {
    throw new Error('Refusing to read outside CMeCodeDir/CanvasStartDir')
  }
  return full
}

// --- HTTP plumbing ---------------------------------------------------------

function sendJson(res, status, data) {
  const body = JSON.stringify(data)
  res.writeHead(status, {'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body)})
  res.end(body)
}

const STATIC_TYPES = {'.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript'}

function serveStatic(req, res) {
  // Path only. A query string is for the page's own JS to read - index.html uses
  // ?file=... to open straight onto one starting point - and leaving it attached
  // would make "/?file=x" look like a request for a file literally named that.
  const {pathname} = new URL(req.url, 'http://localhost')
  const reqPath = pathname === '/' ? '/index.html' : pathname
  const full = path.join(__dirname, path.normalize(reqPath))
  if (!full.startsWith(__dirname)) {
    res.writeHead(403)
    res.end()
    return
  }
  fs.readFile(full, (err, data) => {
    if (err) {
      res.writeHead(404)
      res.end('Not found')
      return
    }
    res.writeHead(200, {'Content-Type': STATIC_TYPES[path.extname(full)] || 'application/octet-stream'})
    res.end(data)
  })
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = ''
    req.on('data', chunk => {
      body += chunk
      if (body.length > 2_000_000) req.destroy(new Error('Request body too large'))
    })
    req.on('end', () => resolve(body))
    req.on('error', reject)
  })
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost')

    if (url.pathname === '/api/starting-points' && req.method === 'GET') {
      sendJson(res, 200, {book: listBookStartingPoints(), canvas: listCanvasStartingPoints()})
      return
    }

    if (url.pathname === '/api/file' && req.method === 'GET') {
      const full = resolveContentPath(url.searchParams.get('path') || '')
      sendJson(res, 200, {content: fs.readFileSync(full, 'utf8')})
      return
    }

    if (url.pathname === '/api/save' && req.method === 'POST') {
      sendJson(res, 200, saveStartingPoint(JSON.parse(await readBody(req))))
      return
    }

    // Overwrites an EXISTING file in place, given one of the paths this same
    // server already handed back from /api/starting-points or /api/file -
    // separate from /api/save, which is about creating a new entry (name/
    // category validation, collision checks) rather than editing one that's
    // already there.
    if (url.pathname === '/api/file' && req.method === 'POST') {
      const body = JSON.parse(await readBody(req))
      const full = resolveContentPath(body.path || '')
      if (!fs.existsSync(full)) throw new Error(`${body.path} doesn't exist - use /api/save to create it`)
      if (typeof body.code !== 'string' || body.code.trim().length === 0) throw new Error('Code is empty')
      fs.writeFileSync(full, body.code)
      sendJson(res, 200, {path: body.path})
      return
    }

    serveStatic(req, res)
  } catch (e) {
    sendJson(res, 400, {error: e.message})
  }
})

server.listen(PORT, '127.0.0.1', () => {
  console.log(`Starting points tool: http://localhost:${PORT}`)
})

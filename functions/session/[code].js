// WebSocket endpoint for in-class "follow me" sessions, on the book's own
// origin (wss://<site>/session/<CODE>). This is just a doorway: the actual
// session state lives in a Durable Object hosted by the separate
// engs20-classroom Worker (classroom-worker/), reached through the SESSIONS
// binding declared in the repo-root wrangler.toml. Committed as a real file,
// unlike functions/_middleware.js which deploy-client-preview.sh regenerates
// from the build output every deploy - the two coexist; Pages runs the
// middleware first, and it passes non-allow-listed paths like this one
// through untouched.
export async function onRequest({request, env, params}) {
  if (!env.SESSIONS) {
    return new Response('classroom sessions not configured (SESSIONS binding missing - is the engs20-classroom Worker deployed?)', {status: 503})
  }
  const code = String(params.code || '').toUpperCase()
  if (!/^[A-Z0-9]{4,8}$/.test(code)) {
    return new Response('bad session code', {status: 400})
  }
  const id = env.SESSIONS.idFromName(code)
  return env.SESSIONS.get(id).fetch(request)
}

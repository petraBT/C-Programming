// WebSocket endpoint for in-class sessions -- follow-me, polls and written
// answers -- on the book's own origin (wss://<site>/session/<CODE>).
//
// This is only a doorway. The session state lives in a Durable Object in the
// separate classroom-sessions Worker (slide-tooling/worker/, shared by every
// course), reached through the SESSIONS binding declared in the repo-root
// wrangler.toml. The client side is assets/classroom.js.
//
// Committed as a real file, unlike functions/_middleware.js which the deploy
// regenerates from the build output every time. The two coexist: Pages runs
// the middleware first, and it passes a path like this one through untouched.
//
// The room name is "ENGS20:" + code, NOT the bare code: ENGS 28 uses the same
// Worker and the same four-letter alphabet, so without the prefix a class in
// each course could pick WXYZ on the same morning and land in one room, each
// turning the other's slides. The prefix is added here rather than in the
// client because the client is shared source and a student's browser is not
// where a security boundary belongs.
export async function onRequest({request, env, params}) {
  if (!env.SESSIONS) {
    return new Response(
      'classroom sessions not configured (the SESSIONS binding is missing -- is the classroom-sessions Worker deployed?)',
      {status: 503},
    )
  }
  const code = String(params.code || '').toUpperCase()
  if (!/^[A-Z0-9]{4,8}$/.test(code)) {
    return new Response('bad session code', {status: 400})
  }
  const id = env.SESSIONS.idFromName('ENGS20:' + code)
  return env.SESSIONS.get(id).fetch(request)
}

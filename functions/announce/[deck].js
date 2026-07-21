// Same-origin doorway to a deck's announcements board (GET/POST
// /announce/<DECK>), the twin of functions/session/[code].js. The board state
// lives in the DeckBoard Durable Object hosted by the engs20-classroom Worker,
// reached through the BOARDS binding declared in the repo-root wrangler.toml.
//
// GET is open: students load a deck's announcements the same way they load the
// deck itself. POST is the instructor saving them, and is gated HERE, before
// anything reaches the Durable Object, by a shared passphrase.
//
// The passphrase is a Pages secret (ANNOUNCE_KEY), set once by the instructor:
//   npx wrangler pages secret put ANNOUNCE_KEY --project-name=cprog-client-preview
// Until it is set, writes are refused (503) and the deck still works read-only.
// The secret is compared here, on the server; the client never holds anything
// but the passphrase the instructor typed, and only sends it on a save.

// Length-limited constant-time-ish compare, so a wrong passphrase does not
// leak its length through timing. Not a hard security boundary - it guards
// classroom announcements, not secrets - but cheap to do properly.
function safeEqual(a, b) {
  a = String(a)
  b = String(b)
  let diff = a.length ^ b.length
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i % b.length || 1)
  return diff === 0
}

export async function onRequest({request, env, params}) {
  if (!env.BOARDS) {
    return new Response('announcements not configured (BOARDS binding missing - is the engs20-classroom Worker deployed with the DeckBoard class?)', {status: 503})
  }

  const deck = String(params.deck || '')
  // Same shape a deck id can take (see the deck files); keep it tight so a
  // stray path cannot spin up arbitrary Durable Object instances.
  if (!/^[A-Za-z0-9_-]{1,40}$/.test(deck)) {
    return new Response('bad deck id', {status: 400})
  }

  if (request.method === 'POST') {
    if (!env.ANNOUNCE_KEY) {
      return new Response('announcements editing is not set up (ANNOUNCE_KEY secret missing)', {status: 503})
    }
    const key = request.headers.get('X-Announce-Key') || ''
    if (!safeEqual(key, env.ANNOUNCE_KEY)) {
      return new Response('wrong passphrase', {status: 401})
    }
  } else if (request.method !== 'GET') {
    return new Response('method not allowed', {status: 405})
  }

  // One Durable Object instance per deck. Upper-cased so W1C3 and w1c3 are the
  // same board, matching how session codes are normalised.
  const id = env.BOARDS.idFromName(deck.toUpperCase())
  return env.BOARDS.get(id).fetch(request)
}

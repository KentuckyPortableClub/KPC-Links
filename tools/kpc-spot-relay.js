/**
 * KPC spot relay  (Kentucky Portable Club)
 *
 * Reads the POTA spot list at most once every 2 minutes and serves that saved
 * copy to everyone else. POTA gets asked about 720 times a day no matter how
 * many members have the map open.
 *
 * It does this one job only. The address it reads is fixed in this file and
 * nothing in a request can change it, so the relay can never be used to fetch
 * anything else.
 *
 * Needs no key, no token and no account details.
 *
 * LIVE at: https://kpc-spots.kentuckyportableclub.workers.dev/spots
 *
 * This file is the record of what is deployed. Editing it here does NOT deploy
 * anything: the owner pastes it into the Cloudflare editor and presses Deploy.
 * Change this file and the Worker together, or they drift apart.
 *
 * Tested 2026-11-16: four requests in a row returned identical bytes with the
 * age counter ticking (POTA asked once); after 2 minutes the age reset with
 * fresh content; /nonsense and /secret-proxy?url=... both answered 404.
 */

const POTA_SPOTS = 'https://api.pota.app/spot/activator';
const SECONDS = 120;   // how long a saved copy is served before POTA is asked again

export default {
  async fetch(request) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: headers() });
    }
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      return json({ error: 'GET only' }, 405);
    }

    const path = new URL(request.url).pathname;
    if (path !== '/spots' && path !== '/') {
      return json({ error: 'Not found. This relay serves /spots only.' }, 404);
    }

    let upstream;
    try {
      upstream = await fetch(POTA_SPOTS, {
        cf: { cacheTtl: SECONDS, cacheEverything: true },
        headers: {
          accept: 'application/json',
          'user-agent': 'KPC-spot-relay (Kentucky Portable Club)',
        },
      });
    } catch (err) {
      return json({ error: 'POTA could not be reached' }, 502);
    }

    if (!upstream.ok) {
      return json({ error: 'POTA answered ' + upstream.status }, 502);
    }

    return new Response(upstream.body, {
      status: 200,
      headers: headers(upstream.headers.get('age') || '0'),
    });
  },
};

function headers(age) {
  return {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'public, max-age=' + SECONDS,
    'access-control-allow-origin': '*',
    'x-kpc-spot-age': age || '0',   // seconds since POTA was last asked
    'x-kpc-relay': 'kpc-spots',
  };
}

function json(body, status) {
  return new Response(JSON.stringify(body), { status, headers: headers() });
}

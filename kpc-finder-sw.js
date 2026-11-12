/* KPC Activation Finder — offline helper (service worker).
   Only handles the finder's own files, the Leaflet map library and OpenStreetMap tiles.
   Every other page on the site goes straight to the network as normal.
   Strategy: network first (so the site always updates when you have signal),
   fall back to the saved copy when there is no signal (or when the site itself answers 5xx).
   Nov 11 review: a released map file (data/released/...?v=hash) is kept under its own ?v= address, so a new index never
   pairs with an older saved file; the tile limit no longer depends on how long this worker happens to stay awake;
   only a plain 200 answer is saved (not 204 / 206). The two cache names below are never renamed or deleted. */
const APP = 'kpc-finder-v1';
const TILES = 'kpc-tiles-v1';
const MAX_TILES = 2500; // about 40–60 MB of map tiles at most
const SAME = /\/(finder\.html|finder\.css|finder\.js|gis-overlays\.js|kpc-offline\.js|kpc-map-extras\.js|kpc-my-parks\.js|kpc-us-states\.json|locations(?:-ky)?\.json|official-[a-z0-9-]+\.json|wwff-unmapped\.json|kpc-ky-data\.json|ky-trail-parks\.json|ky-[a-z-]+\.geojson|KPC-logo\.png|kpc-icon-(?:32|180)\.png|kpc-kit\.html|kpc-kit\.js|kpc-in-park\.html|kpc-in-park\.js|kpc-bounds\.js|kpc-map-tools\.js|kpc-padus-layer\.js|kpc-place-suggest\.js|kpc-trails-layer\.js|kpc-va-birding-layer\.js|data\/va-birding-sites\.json|kpc-tools\.css|kpc-theme\.js|kpc-gate\.js|kpc-search\.js|kpc-conditions\.json|kpc-park-notes\.json|kpc-campgrounds\.json|kpc-logger\.html|kpc-logger\.js|kpc-logger\.css|kpc-logger\.webmanifest|kpc-fx\.js|kpc-cat\.js|kpc-ft8\.js|kpc-ft8\.wasm|kpc-logger-ft8\.js|kpc-ft8\.css|kpc-digi\.js|kpc-digi-ui\.js|kpc-voicekeyer\.js|kpc-gdrive\.js|bg-lodge(?:-mobile)?\.jpg|bg-night(?:-mobile)?\.jpg|hero-founders(?:-mobile)?\.jpg|bg-group(?:-mobile)?\.jpg|KPC26-Group-Photo(?:-web)?\.jpg|kpc-icon-(?:192|512)\.png|data\/parkinfo\/index\.json|data\/(?:wwff|sota)\/t\/-?\d+_-?\d+\.json)$/; /* Oct 15: + Activation Kit / Am I in the Park? · Oct 16: + Activator Logger */
const CDN = /^https:\/\/(?:unpkg\.com\/leaflet@1\.9\.4\/dist\/|cdnjs\.cloudflare\.com\/ajax\/libs\/leaflet\/1\.9\.4\/)/;   /* Oct 16: + cdnjs copy used by the trip planners */
const TILE = /^https:\/\/(?:[abc]\.)?tile\.openstreetmap\.org\/\d+\/\d+\/\d+\.png$/;
const tileKey = h => h.replace(/^https:\/\/[abc]\.tile\./, 'https://tile.');   /* a./b./c. tiles share one saved copy */

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k.startsWith('kpc-') && k !== APP && k !== TILES) await caches.delete(k);
  await self.clients.claim();
})()));

const timeout = (p, ms) => new Promise((ok, no) => { const t = setTimeout(() => no(new Error('timeout')), ms); p.then(v => { clearTimeout(t); ok(v); }, e => { clearTimeout(t); no(e); }); });
/* the saved-copy address: the ?v= part is dropped (the file is checked on the network first), except for released map files,
   whose ?v= is their version: an index that names ?v=B must never be answered with the copy saved for ?v=A */
const RELEASED = /\/data\/released\//;
const keyFor = req => { const u = new URL(req.url); if (!RELEASED.test(u.pathname)) u.search = ''; u.hash = ''; return u.href; };

async function networkFirst(req, cacheName, ms, key) {
  const cache = await caches.open(cacheName);
  const net = fetch(req).then(async res => {
    if (res && res.status >= 500) { const hit = await cache.match(key); if (hit) return hit; }   /* the site is down but a saved copy exists */
    else if (res && res.status === 200 && res.type !== 'opaque') cache.put(key, res.clone()).then(() => { if (cacheName === TILES) return trimTiles(); }).catch(() => {});
    return res;
  });
  try { return await timeout(net, ms); }
  catch (e) {
    const hit = await cache.match(key);
    if (hit) return hit;
    try { return await net; } catch (_) { return offline(req); }
  }
}

async function trimTiles() {
  if (Math.random() * 40 >= 1) return;   /* about one save in 40 (a counter here was lost every time the worker went to sleep) */
  const c = await caches.open(TILES); const keys = await c.keys();
  for (let i = 0; i < keys.length - MAX_TILES; i++) await c.delete(keys[i]);
}

function offline(req) {
  if (req.mode === 'navigate') return new Response('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline | KPC</title><body style="margin:0;font:16px/1.5 Arial,sans-serif;background:#070707;color:#f5f0e4;display:grid;place-items:center;min-height:100vh;text-align:center;padding:24px"><div><h1 style="font-family:Georgia,serif;color:#f0c96b">No signal</h1><p>This page hasn\'t been saved for offline use yet.<br>Next time you have signal, open it and tap its save button (Park Commander: <b>Save for offline</b>; the trip planners: <b>Save my trip for no signal</b>).</p></div>', { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  return Response.error();
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    if (SAME.test(url.pathname)) { e.respondWith(networkFirst(req, APP, req.mode === 'navigate' ? 6000 : 8000, keyFor(req))); return; }
    /* Oct 16 (trip planners' SAVE MY TRIP FOR NO SIGNAL): any other file of ours goes to the network as normal and
       only falls back to a saved copy when there is no signal at all */
    e.respondWith(fetch(req).then(async res => (res.status >= 500 && (await (await caches.open(APP)).match(keyFor(req)))) || res, async () => (await (await caches.open(APP)).match(keyFor(req))) || offline(req)));
    return;
  }
  if (CDN.test(url.href)) { e.respondWith(networkFirst(req, APP, 8000, url.href)); return; }
  if (TILE.test(url.href)) { e.respondWith(networkFirst(req, TILES, 5000, tileKey(url.href))); return; }
});

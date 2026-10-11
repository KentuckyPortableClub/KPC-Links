/* KPC Activation Finder — offline helper (service worker).
   Only handles the finder's own files, the Leaflet map library and OpenStreetMap tiles.
   Every other page on the site goes straight to the network as normal.
   Strategy: network first (so the site always updates when you have signal),
   fall back to the saved copy when there is no signal. */
const APP = 'kpc-finder-v1';
const TILES = 'kpc-tiles-v1';
const MAX_TILES = 2500; // about 40–60 MB of map tiles at most
const SAME = /\/(finder\.html|finder\.css|finder\.js|gis-overlays\.js|kpc-offline\.js|kpc-map-extras\.js|locations\.json|official-[a-z0-9-]+\.json|wwff-unmapped\.json|kpc-ky-data\.json|ky-trail-parks\.json|ky-[a-z-]+\.geojson|KPC-logo\.png|kpc-icon-(?:32|180)\.png)$/;
const CDN = /^https:\/\/unpkg\.com\/leaflet@1\.9\.4\/dist\//;
const TILE = /^https:\/\/tile\.openstreetmap\.org\/\d+\/\d+\/\d+\.png$/;

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k.startsWith('kpc-') && k !== APP && k !== TILES) await caches.delete(k);
  await self.clients.claim();
})()));

const timeout = (p, ms) => new Promise((ok, no) => { const t = setTimeout(() => no(new Error('timeout')), ms); p.then(v => { clearTimeout(t); ok(v); }, e => { clearTimeout(t); no(e); }); });
const keyFor = req => { const u = new URL(req.url); u.search = ''; u.hash = ''; return u.href; };

async function networkFirst(req, cacheName, ms, key) {
  const cache = await caches.open(cacheName);
  const net = fetch(req).then(res => {
    if (res && res.ok && res.type !== 'opaque') cache.put(key, res.clone()).then(() => { if (cacheName === TILES) trimTiles(); }).catch(() => {});
    return res;
  });
  try { return await timeout(net, ms); }
  catch (e) {
    const hit = await cache.match(key);
    if (hit) return hit;
    try { return await net; } catch (_) { return offline(req); }
  }
}

let puts = 0;
async function trimTiles() {
  if (++puts % 40) return;
  const c = await caches.open(TILES); const keys = await c.keys();
  for (let i = 0; i < keys.length - MAX_TILES; i++) await c.delete(keys[i]);
}

function offline(req) {
  if (req.mode === 'navigate') return new Response('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline | KPC</title><body style="margin:0;font:16px/1.5 Arial,sans-serif;background:#070707;color:#f5f0e4;display:grid;place-items:center;min-height:100vh;text-align:center;padding:24px"><div><h1 style="font-family:Georgia,serif;color:#f0c96b">No signal</h1><p>This page hasn\'t been saved for offline use yet.<br>Next time you have signal, open KY Park Commander and tap <b>Save for offline</b>.</p></div>', { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  return Response.error();
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    if (SAME.test(url.pathname)) e.respondWith(networkFirst(req, APP, req.mode === 'navigate' ? 6000 : 8000, keyFor(req)));
    return;
  }
  if (CDN.test(url.href)) { e.respondWith(networkFirst(req, APP, 8000, url.href)); return; }
  if (TILE.test(url.href)) { e.respondWith(networkFirst(req, TILES, 5000, url.href)); return; }
});

/* KPC Activation Finder — "Save for offline" panel + offline banner. Works with kpc-finder-sw.js */
(function () {
  'use strict';
  const APP = 'kpc-finder-v1', TILES = 'kpc-tiles-v1', KEY = 'kpcFinderOffline';
  const FILES = ['finder.html', 'finder.css', 'finder.js', 'gis-overlays.js', 'kpc-offline.js', 'kpc-map-extras.js', 'ky-overlaps.geojson',
    'locations.json', 'official-2fer-evidence.json', 'official-park-access.json', 'official-trail-maps.json', 'wwff-unmapped.json',
    'kpc-ky-data.json', 'ky-trail-parks.json',
    'ky-state-parks.geojson', 'ky-hunting-areas.geojson', 'ky-nature-preserves.geojson', 'ky-natural-areas.geojson', 'ky-dbnf.geojson',
    'ky-wild-rivers.geojson', 'ky-nps.geojson', 'ky-wilderness.geojson', 'ky-sheltowee.geojson', 'ky-pine-mountain.geojson', 'ky-dawkins.geojson',
    'KPC-logo.png', 'kpc-icon-32.png'];
  const LF = 'https://unpkg.com/leaflet@1.9.4/dist/';
  const CDN = ['leaflet.css', 'leaflet.js', 'images/marker-icon.png', 'images/marker-icon-2x.png', 'images/marker-shadow.png', 'images/layers.png', 'images/layers-2x.png'].map(f => LF + f);
  const supported = 'serviceWorker' in navigator && 'caches' in window && window.isSecureContext;
  const get = () => { try { return JSON.parse(localStorage.getItem(KEY)) || null; } catch (_) { return null; } };
  const set = v => { try { v ? localStorage.setItem(KEY, JSON.stringify(v)) : localStorage.removeItem(KEY); } catch (_) {} };
  const mb = b => (b / 1048576).toFixed(b > 10485760 ? 0 : 1) + ' MB';
  const when = t => new Date(t).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

  if (supported) navigator.serviceWorker.register('kpc-finder-sw.js').catch(() => {});

  /* ---------- styles ---------- */
  const css = document.createElement('style');
  css.textContent = `.kpc-off{border-left:4px solid #d5a63a}.kpc-off h2{margin-top:0}.kpc-off .toolbuttons{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0 4px}
.kpc-off-bar{height:8px;border-radius:99px;background:rgba(255,255,255,.12);overflow:hidden;margin:10px 0 2px;display:none}.kpc-off-bar i{display:block;height:100%;width:0;background:#3ecf6e;transition:width .2s}
.kpc-off #kpcOffSave{background:#d5a63a;color:#111;font-weight:800}.kpc-off #kpcOffSave:disabled{opacity:.6;cursor:wait}
.kpc-off-ok{color:#7ff0a6;font-weight:800}.kpc-off ul{margin:8px 0 0;padding-left:20px}.kpc-off li{margin:3px 0}
.kpc-offline-banner{position:relative;z-index:2100;background:#5a3b00;color:#fff;border-bottom:2px solid #d5a63a;padding:10px 16px;text-align:center;font:700 14px/1.4 Arial,Helvetica,sans-serif}
.kpc-offline-banner b{color:#f0c96b}`;
  document.head.appendChild(css);

  /* ---------- offline banner ---------- */
  const banner = document.createElement('div');
  banner.className = 'kpc-offline-banner'; banner.setAttribute('role', 'status'); banner.hidden = true;
  banner.innerHTML = '<b>No signal — offline mode.</b> Park search, park details, saved trips and the Kentucky “Am I inside a park?” check work from your saved copy. Town search, live spots and live map layers need a signal. The map shows only areas you viewed while online.';
  document.body.insertBefore(banner, document.body.firstChild);
  const net = () => { banner.hidden = navigator.onLine; };
  addEventListener('online', net); addEventListener('offline', net); net();

  /* ---------- panel ---------- */
  const panel = document.createElement('section');
  panel.className = 'panel kpc-off'; panel.id = 'finder-offline'; panel.setAttribute('aria-label', 'Use the finder with no signal');
  panel.innerHTML = `<h2>No signal at the park? Save it first.</h2>
<p class="meta">Save KY Park Commander on this phone or computer before you leave home. After saving, these work with <b>no signal</b>:</p>
<ul class="meta"><li>Park, summit and KFF search by name or reference, with park details</li><li>Your favorites and trip stops</li><li>“Am I inside a park?” with GPS — Kentucky boundaries, trails and wilderness</li></ul>
<p class="meta"><b>Map tip:</b> before you go, open the map and zoom in around the park you’re heading to. Map areas you look at while online are kept for offline use (the whole map can’t be downloaded). Town search, live POTA spots and live GIS layers still need a signal.</p>
<div class="toolbuttons"><button id="kpcOffSave" type="button">Save for offline (about 10 MB)</button><button id="kpcOffClear" class="secondary" type="button">Remove offline copy</button></div>
<div class="kpc-off-bar" id="kpcOffBar"><i></i></div><p class="meta" id="kpcOffStatus" aria-live="polite"></p>`;
  const below = document.querySelector('#finder-planner') || document.querySelector('.mapgrid') || document.querySelector('#finder-results') || document.querySelector('#finder-map');
  const anchor = document.querySelector('#finder-search') || document.querySelector('main');
  if (below) below.insertAdjacentElement('afterend', panel); else if (anchor && anchor.id === 'finder-search') anchor.insertAdjacentElement('beforebegin', panel); else if (anchor) anchor.prepend(panel);
  const jump = document.querySelector('.finder-jump');
  if (jump && !jump.querySelector('a[href="#finder-offline"]')) { const a = document.createElement('a'); a.href = '#finder-offline'; a.textContent = 'Offline'; jump.appendChild(a); }

  const $ = id => document.getElementById(id), stat = $('kpcOffStatus'), bar = $('kpcOffBar'), saveBtn = $('kpcOffSave'), clearBtn = $('kpcOffClear');
  async function tileCount() { try { return (await (await caches.open(TILES)).keys()).length; } catch (_) { return 0; } }
  async function show() {
    if (!supported) { stat.textContent = 'This browser can’t save pages for offline use. Try Chrome, Safari, Edge or Firefox.'; saveBtn.disabled = clearBtn.disabled = true; return; }
    const s = get(); let have = false;
    try { have = !!(await caches.match('locations.json', { ignoreSearch: true })) || !!(await (await caches.open(APP)).match(new URL('locations.json', location.href).href)); } catch (_) {}
    const t = await tileCount();
    if (s && have) { stat.innerHTML = `<span class="kpc-off-ok">✓ Saved for offline</span> on ${when(s.t)} • ${mb(s.b)}${s.miss ? ` • ${s.miss} item${s.miss > 1 ? 's' : ''} couldn’t be saved` : ''} • ${t} map tile${t === 1 ? '' : 's'} kept. Tap Save again any time to refresh it.`; saveBtn.textContent = 'Refresh offline copy'; }
    else { stat.textContent = t ? `Not saved yet • ${t} map tiles kept from browsing.` : 'Not saved yet.'; saveBtn.textContent = 'Save for offline (about 10 MB)'; if (s && !have) set(null); }
  }
  saveBtn.addEventListener('click', async () => {
    if (!navigator.onLine) { stat.textContent = 'You need a signal to save. Try again when you’re connected.'; return; }
    saveBtn.disabled = clearBtn.disabled = true; bar.style.display = 'block';
    const cache = await caches.open(APP), list = FILES.map(f => new URL(f, location.href).href).concat(CDN);
    let done = 0, bytes = 0, miss = 0;
    for (const url of list) {
      stat.textContent = `Saving ${done + 1} of ${list.length}…`;
      try {
        const res = await fetch(url, { cache: 'reload', mode: url.startsWith(location.origin) ? 'same-origin' : 'cors', credentials: 'omit' });
        if (!res.ok) throw new Error(res.status);
        const blob = await res.blob(); bytes += blob.size;
        await cache.put(url, new Response(blob, { status: 200, headers: { 'Content-Type': res.headers.get('content-type') || 'application/octet-stream' } }));
      } catch (e) { miss++; }
      done++; bar.firstElementChild.style.width = (done / list.length * 100) + '%';
    }
    set({ t: Date.now(), b: bytes, miss });
    try { if (navigator.storage && navigator.storage.persist) await navigator.storage.persist(); } catch (_) {}
    saveBtn.disabled = clearBtn.disabled = false; setTimeout(() => { bar.style.display = 'none'; bar.firstElementChild.style.width = 0; }, 800);
    await show();
  });
  clearBtn.addEventListener('click', async () => {
    try { await caches.delete(APP); await caches.delete(TILES); } catch (_) {}
    set(null); stat.textContent = 'Offline copy removed.'; setTimeout(show, 1500);
  });
  show();
})();

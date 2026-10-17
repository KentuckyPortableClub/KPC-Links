/* KPC conditions bar (Oct 17 2026, Brandon: 'the scrolling conditions bar under the hero on Parks, Map Room, Activation Board;
   replace the 3 bars on Happening Now'). Same as the Hunters Lounge bar: the sun (NOAA SWPC solar flux, Kp, GOES X-ray, HF verdict),
   the weather where you are (Open-Meteo, sunrise/sunset) and WSPR reports by band for the 3x3 grid squares around you
   (db1.wspr.live, last 30 minutes). Where = GPS (if already allowed or after 📍), else a grid saved by the KPC Logger / Lounge,
   else the middle of Kentucky. Mount: <div id="kpc-cx"></div>. Your location only goes to those services. */
(function () {
  const mount = document.getElementById('kpc-cx'); if (!mount) return;
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const css = document.createElement('style');
  css.textContent = `
.kcx{position:sticky!important;top:var(--kcx-top,0px);z-index:900!important;display:flex;align-items:stretch;min-height:34px;background:linear-gradient(180deg,#0f1410,#0a0d0a);border-top:1px solid rgba(240,201,107,.35);border-bottom:1px solid rgba(240,201,107,.45);box-shadow:0 6px 16px rgba(0,0,0,.35);font:13px Arial,Helvetica,sans-serif;color:#e8e1cf}
.kcx-k{flex:0 0 auto;display:flex;align-items:center;padding:0 12px;font:900 11px Arial;letter-spacing:1.6px;color:#2a1a05;background:linear-gradient(180deg,#f6d58a,#d5a63a)}
.kcx-run{flex:1;overflow:hidden;-webkit-mask-image:linear-gradient(90deg,transparent,#000 3%,#000 97%,transparent);mask-image:linear-gradient(90deg,transparent,#000 3%,#000 97%,transparent)}
.kcx-track{display:inline-flex;align-items:center;white-space:nowrap;height:100%;padding-left:20px;animation:kcxRun 90s linear infinite}
.kcx-run:hover .kcx-track{animation-play-state:paused}
@keyframes kcxRun{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.kcx .ci{display:inline-flex;align-items:center;gap:5px;padding:0 4px}.kcx .ci b{color:#fff}
.kcx .cs{color:#d5a63a;padding:0 12px;opacity:.7}
.kcx i{font-style:normal;font-size:11px;font-weight:900;letter-spacing:.6px;padding:1px 6px;border-radius:99px}
.kcx i.ok{background:rgba(61,220,132,.18);color:#7ff0b0}.kcx i.meh{background:rgba(240,201,107,.2);color:#ffd27a}.kcx i.bad{background:rgba(255,107,90,.22);color:#ffb3a8}
.kcx .wb{display:inline-block;margin:0 3px;padding:1px 7px;border-radius:6px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1)}
.kcx .wb.hot{border-color:#d5a63a;background:rgba(240,201,107,.14)}.kcx .wb.q{opacity:.5}.kcx .wb small{color:#a59e8c;font-size:11px}
.kcx-b{flex:0 0 auto;border:0;border-left:1px solid rgba(240,201,107,.35);background:transparent;color:#f0c96b;font:900 11px Arial;letter-spacing:1px;padding:0 12px;cursor:pointer}
.kcx-b:hover{background:rgba(240,201,107,.1)}
@media(max-width:1099px){.kcx{min-height:30px;font-size:12px}.kcx-k{padding:0 8px;font-size:10px;letter-spacing:1px}.kcx-b{padding:0 9px;font-size:0}.kcx-b::before{content:'📍';font-size:14px}.kcx .cs{padding:0 8px}.kcx-track{padding-left:12px}}
@media(prefers-reduced-motion:reduce){.kcx-track{animation:none!important}.kcx-run{overflow-x:auto}}`;
  document.head.appendChild(css);
  mount.className = 'kcx'; mount.setAttribute('data-keep-light', ''); mount.setAttribute('aria-label', 'Solar, weather and band conditions');
  mount.innerHTML = '<span class="kcx-k" id="kcxK">📡 CONDITIONS</span><div class="kcx-run"><div class="kcx-track" id="kcxT"><span>Checking the sun, your weather and WSPR reports near you…</span></div></div><button type="button" class="kcx-b" id="kcxLoc" title="Use my location for the weather and band reports">📍 MY SPOT</button>';
  /* under the hero, and once you scroll it sticks right under the site header (Brandon Oct 17) */
  const hdr = () => { const h = document.querySelector('header.site-nav') || document.querySelector('header'); if (!h) return 0; const cs = getComputedStyle(h); return /sticky|fixed/.test(cs.position) ? Math.max(0, Math.round(h.getBoundingClientRect().height)) : 0; };
  const topSet = () => mount.style.setProperty('--kcx-top', hdr() + 'px'); topSet(); addEventListener('resize', topSet); addEventListener('load', topSet);
  const $ = id => document.getElementById(id);
  const jget = async (u, ms) => { const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 20000); try { const r = await fetch(u, { cache: 'no-store', signal: c.signal }); if (!r.ok) throw Error(r.status); return await r.json(); } finally { clearTimeout(t); } };
  const one = (u, ms) => jget(u, ms).catch(() => null);
  const g2ll = g => { g = String(g || '').toUpperCase(); if (!/^[A-R]{2}\d{2}/.test(g)) return null; return [(g.charCodeAt(1) - 65) * 10 - 90 + (+g[3]) + .5, (g.charCodeAt(0) - 65) * 20 - 180 + (+g[2]) * 2 + 1]; };
  const ll2g = (la, lo) => { lo += 180; la += 90; return String.fromCharCode(65 + Math.floor(lo / 20)) + String.fromCharCode(65 + Math.floor(la / 10)) + Math.floor((lo % 20) / 2) + Math.floor(la % 10); };
  const around = g => { const c = g2ll(g); if (!c) return [g]; const o = new Set(); for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) o.add(ll2g(c[0] + a, c[1] + b * 2)); return [...o]; };
  const WX = { 0: '☀️ Clear', 1: '🌤 Mostly clear', 2: '⛅ Partly cloudy', 3: '☁️ Cloudy', 45: '🌫 Fog', 48: '🌫 Fog', 51: '🌦 Drizzle', 53: '🌦 Drizzle', 55: '🌦 Drizzle', 61: '🌧 Rain', 63: '🌧 Rain', 65: '🌧 Heavy rain', 71: '🌨 Snow', 73: '🌨 Snow', 75: '🌨 Heavy snow', 80: '🌦 Showers', 81: '🌦 Showers', 82: '⛈ Heavy showers', 95: '⛈ Thunderstorms', 96: '⛈ Storms + hail', 99: '⛈ Storms + hail' };
  const BN = [[1, '160m'], [3, '80m'], [5, '60m'], [7, '40m'], [10, '30m'], [14, '20m'], [18, '17m'], [21, '15m'], [24, '12m'], [28, '10m'], [50, '6m']];
  let LOC = get('kpcHuntCx', null), busy = false, last = 0;
  function gps() { return new Promise((ok, no) => navigator.geolocation ? navigator.geolocation.getCurrentPosition(p => { const la = p.coords.latitude, lo = p.coords.longitude; LOC = { la, lo, g: ll2g(la, lo), src: 'gps', t: Date.now() }; put('kpcHuntCx', LOC); ok(LOC); }, no, { timeout: 12000, maximumAge: 6e5 }) : no()); }
  async function where() {
    if (LOC && LOC.src === 'gps' && Date.now() - LOC.t < 6 * 36e5) return LOC;
    try { const p = navigator.permissions && await navigator.permissions.query({ name: 'geolocation' }); if (p && p.state === 'granted') return await gps(); } catch (e) {}
    const lg = get('kpcLgSet', {}) || {}, hq = get('kpcHuntQSO', {}) || {};
    const g = String(lg.grid || hq.grid || '').slice(0, 4).toUpperCase(); if (/^[A-R]{2}\d{2}$/.test(g)) { const c = g2ll(g); return { la: c[0], lo: c[1], g, src: 'grid' }; }
    if (LOC) return LOC; return { la: 37.6, lo: -85.2, g: 'EM77', src: 'ky' };
  }
  async function load() {
    if (busy) return; busy = true; last = Date.now();
    try {
      const L = await where(), sq = around(L.g), IN = "('" + sq.join("','") + "')";
      const sql = `SELECT band, count(*) AS c, max(distance) AS d FROM wspr.rx WHERE time > now() - INTERVAL 30 MINUTE AND band IN (${BN.map(b => b[0]).join(',')}) AND (substring(tx_loc,1,4) IN ${IN} OR substring(rx_loc,1,4) IN ${IN}) GROUP BY band ORDER BY band FORMAT JSON`;
      const [ws, kp, sf, xr, wx] = await Promise.all([one('https://db1.wspr.live/?query=' + encodeURIComponent(sql), 25000), one('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json'),
        one('https://services.swpc.noaa.gov/products/summary/10cm-flux.json'), one('https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json'),
        one(`https://api.open-meteo.com/v1/forecast?latitude=${L.la.toFixed(3)}&longitude=${L.lo.toFixed(3)}&current=temperature_2m,weather_code,wind_speed_10m,wind_gusts_10m&daily=sunrise,sunset&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto&forecast_days=1`)]);
      const it = [];
      const sfi = sf ? Number((Array.isArray(sf) ? sf[0] : sf).flux) : NaN, k = kp && kp.length ? Number(kp[kp.length - 1].Kp) : NaN;
      if (isFinite(sfi)) it.push(`☀ Solar flux <b>${Math.round(sfi)}</b>`);
      if (isFinite(k)) it.push(`🧲 Kp <b>${k.toFixed(k % 1 ? 1 : 0)}</b> ${k >= 5 ? '<i class="bad">STORM</i>' : k >= 4 ? '<i class="meh">unsettled</i>' : '<i class="ok">calm</i>'}`);
      if (xr && xr.length) { const f = (xr.filter(x => x.energy === '0.1-0.8nm').pop() || {}).flux; if (f) { const c = f >= 1e-4 ? 'X' : f >= 1e-5 ? 'M' : f >= 1e-6 ? 'C' : f >= 1e-7 ? 'B' : 'A', m = (f / { X: 1e-4, M: 1e-5, C: 1e-6, B: 1e-7, A: 1e-8 }[c]).toFixed(1); it.push(`💥 X-ray <b>${c}${m}</b>${c === 'X' || c === 'M' ? ' <i class="bad">flare: low bands may fade</i>' : ''}`); } }
      if (isFinite(sfi) && isFinite(k)) { const sc = (sfi >= 150 ? 3 : sfi >= 110 ? 2 : sfi >= 80 ? 1 : 0) - (k >= 5 ? 3 : k >= 4 ? 2 : k >= 3 ? 1 : 0); it.push(`📻 HF <b>${sc >= 3 ? 'GREAT' : sc >= 2 ? 'GOOD' : sc >= 1 ? 'FAIR' : sc >= 0 ? 'SO-SO' : 'ROUGH'}</b>`); }
      const here = L.src === 'gps' ? 'at your spot' : L.src === 'grid' ? 'near ' + L.g : 'in Kentucky';
      if (wx && wx.current) { const c = wx.current; it.push(`${WX[c.weather_code] || '🌡'} <b>${Math.round(c.temperature_2m)}°F</b> ${esc(here)} · wind ${Math.round(c.wind_speed_10m)} mph${c.wind_gusts_10m > 25 ? ` <i class="meh">gusts ${Math.round(c.wind_gusts_10m)}</i>` : ''}`);
        const ft = v => { try { return new Date(v).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }); } catch (e) { return ''; } };
        if (wx.daily && wx.daily.sunrise) it.push(`🌅 Sunrise ${ft(wx.daily.sunrise[0])} · 🌇 sunset ${ft(wx.daily.sunset[0])}`); }
      const rows = (ws && ws.data) || [], m = {}; rows.forEach(r => { m[Number(r.band)] = [Number(r.c), Number(r.d)]; });
      const max = Math.max(0, ...rows.map(r => Number(r.c)));
      if (ws) it.push(`📡 WSPR near ${esc(L.g)} (last 30 min): ` + BN.map(([b, n]) => { const v = m[b]; return v ? `<span class="wb${v[0] >= max * .6 ? ' hot' : ''}">${n} <b>${v[0].toLocaleString()}</b>${v[1] ? ` <small>to ${Math.round(v[1] * .621).toLocaleString()} mi</small>` : ''}</span>` : `<span class="wb q">${n} quiet</span>`; }).join(' '));
      else it.push('📡 WSPR reports are not answering right now');
      it.push('⛈ <i class="meh">Forecasts can be wrong: watch the sky, and take the antenna down if you hear thunder</i>');
      const html = it.map(x => `<span class="ci">${x}</span>`).join('<span class="cs">•</span>');
      $('kcxT').innerHTML = html + '<span class="cs">•</span>' + html;
      $('kcxT').style.animationDuration = Math.max(40, Math.round($('kcxT').scrollWidth / 2 / 45)) + 's';
      $('kcxK').textContent = '📡 ' + (L.src === 'gps' ? 'YOUR SPOT' : L.g);
      $('kcxLoc').hidden = L.src === 'gps';
    } catch (e) { console.error('kpc-cx', e); } finally { busy = false; }
  }
  $('kcxLoc').onclick = () => gps().then(() => load()).catch(() => { $('kcxK').textContent = '📍 LOCATION OFF'; setTimeout(load, 2500); });
  load(); setInterval(() => { if (Date.now() - last > 10 * 6e4 && !document.hidden) load(); }, 60000);
})();

/* KPC Field Weather (kpc-weather.html)
   Your spot (GPS, a Kentucky park / summit / KFF number or name, a town or ZIP): NWS alerts, current conditions,
   the next 24 hours, 7 days, animated radar + lightning, and the NOAA Weather Radio transmitters for your county.
   Sources, all read straight from the browser with no keys:
   - Open-Meteo forecast + geocoding        current, hourly and daily numbers
   - National Weather Service (api.weather.gov)  alerts, forecast text, county, forecast office
   - Iowa Environmental Mesonet NEXRAD tiles, NOAA nowCOAST lightning strike density
   - kpc-nwr.json (refreshed monthly from weather.gov/nwr) and kpc-ky-data.json (parks, summits, KFF, towns) */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LS = 'kpcWxLoc';
  const DEF = { name: 'Frankfort, KY', la: 38.2009, lo: -84.8733, kind: 'default' };
  let KY = null, NWR = null, here = null, map = null, mk = null, warnLayer = null, radar = [], lightning = null, loop = null, fi = 0, req = 0;

  /* ---------- small helpers ---------- */
  async function jget(u, o) { const r = await fetch(u, o); if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); }
  const NWSH = { headers: { Accept: 'application/geo+json' } };
  function save(p) { try { localStorage.setItem(LS, JSON.stringify(p)); } catch (e) {} }
  function saved() { try { const p = JSON.parse(localStorage.getItem(LS) || 'null'); return p && isFinite(p.la) && isFinite(p.lo) ? p : null; } catch (e) { return null; } }
  function status(t) { $('wxStatus').textContent = t || ''; }
  const DIRS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
  const dir = d => isFinite(d) ? DIRS[Math.round(d / 22.5) % 16] : '';
  const r0 = v => isFinite(v) ? Math.round(v) : '--';
  function km(a, b, c, d) { const R = Math.PI / 180, x = Math.sin((c - a) * R / 2) ** 2 + Math.cos(a * R) * Math.cos(c * R) * Math.sin((d - b) * R / 2) ** 2; return 12742 * Math.asin(Math.sqrt(x)); }
  const mi = k => Math.round(k * 0.6214);
  // WMO weather codes (Open-Meteo)
  function wx(code, day) {
    const c = +code, d = day !== 0;
    if (c === 0) return [d ? '☀️' : '🌙', 'Clear'];
    if (c === 1) return [d ? '🌤️' : '🌙', 'Mostly clear'];
    if (c === 2) return ['⛅', 'Partly cloudy'];
    if (c === 3) return ['☁️', 'Cloudy'];
    if (c === 45 || c === 48) return ['🌫️', 'Fog'];
    if (c >= 51 && c <= 57) return ['🌦️', c >= 56 ? 'Freezing drizzle' : 'Drizzle'];
    if (c >= 61 && c <= 67) return ['🌧️', c >= 66 ? 'Freezing rain' : c === 65 ? 'Heavy rain' : 'Rain'];
    if (c >= 71 && c <= 77) return ['🌨️', c === 75 ? 'Heavy snow' : 'Snow'];
    if (c >= 80 && c <= 82) return ['🌧️', c === 82 ? 'Heavy showers' : 'Showers'];
    if (c === 85 || c === 86) return ['🌨️', 'Snow showers'];
    if (c >= 95) return ['⛈️', c >= 96 ? 'Thunderstorms, hail possible' : 'Thunderstorms'];
    return ['🌡️', ''];
  }
  const tm = s => { const d = new Date(s); return d.toLocaleTimeString([], { hour: 'numeric' }).replace(':00', '').replace(' ', ''); };
  const tmm = s => new Date(s).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  const dayName = (s, i) => i === 0 ? 'Today' : new Date(s + 'T12:00').toLocaleDateString([], { weekday: 'short' });

  /* ---------- finding a place ---------- */
  async function kyData() { if (!KY) { try { KY = await jget('kpc-ky-data.json'); } catch (e) { KY = { parks: [], summits: [], kff: [], towns: [] }; } } return KY; }
  async function nwr() { if (!NWR) { try { NWR = await jget('kpc-nwr.json'); } catch (e) { NWR = { tx: [] }; } } return NWR; }
  function refNorm(q) {
    q = q.trim().toUpperCase().replace(/\s+/g, '');
    if (/^\d{1,5}$/.test(q)) return ['US-' + q.padStart(4, '0'), 'KFF-' + q.padStart(4, '0')];
    if (/^(US|K)-?\d+$/.test(q)) return ['US-' + q.replace(/^(US|K)-?/, '').padStart(4, '0')];
    if (/^KFF-?\d+$/.test(q)) return ['KFF-' + q.replace(/^KFF-?/, '').padStart(4, '0')];
    if (/^W4K\//.test(q)) return [q];
    return [];
  }
  async function search(q) {
    q = q.trim(); if (!q) return [];
    const d = await kyData(), refs = refNorm(q), t = q.toLowerCase(), out = [];
    const add = (x, kind) => out.push({ name: x.n, ref: x.c, sub: kind + (x.co ? ' · ' + x.co + ' Co.' : ''), la: x.la, lo: x.lo, kind: 'ref' });
    if (!/^\d{5}$/.test(q)) {
      d.parks.forEach(x => { if (refs.includes(x.c) || x.n.toLowerCase().includes(t)) add(x, 'POTA park'); });
      d.summits.forEach(x => { if (refs.includes(x.c.toUpperCase()) || x.n.toLowerCase().includes(t)) add(x, 'SOTA summit'); });
      d.kff.forEach(x => { if (refs.includes(x.c) || x.n.toLowerCase().includes(t)) add(x, 'WWFF (KFF)'); });
    }
    if (out.length < 8 && !refs.length) {
      try {
        const g = await jget('https://geocoding-api.open-meteo.com/v1/search?name=' + encodeURIComponent(q.replace(/,?\s*(KY|Kentucky)$/i, '')) + '&count=8&language=en&format=json&countryCode=US');
        (g.results || []).forEach(x => out.push({ name: x.name + (x.admin1 ? ', ' + x.admin1 : ''), sub: (x.admin2 ? x.admin2 + ' · ' : '') + (x.postcodes && x.postcodes[0] ? x.postcodes[0] : 'Town'), la: x.latitude, lo: x.longitude, kind: 'town',
          ky: x.admin1 === 'Kentucky' }));
      } catch (e) {}
    }
    // Kentucky places first
    return out.sort((a, b) => (b.kind === 'ref') - (a.kind === 'ref') || (b.ky ? 1 : 0) - (a.ky ? 1 : 0)).slice(0, 12);
  }
  function showResults(list) {
    const box = $('wxResults');
    if (!list.length) { box.innerHTML = ''; status('Nothing found. Try a park number like 1277, a park name, or a town and state.'); return; }
    status(list.length === 1 ? '' : 'Pick one:');
    if (list.length === 1) { box.innerHTML = ''; go(list[0]); return; }
    box.innerHTML = list.map((x, i) => `<button type="button" class="wx-res" data-i="${i}"><b>${x.ref ? esc(x.ref) + ' ' : ''}${esc(x.name)}</b><span>${esc(x.sub || '')}</span></button>`).join('');
    box.querySelectorAll('.wx-res').forEach(b => b.onclick = () => { box.innerHTML = ''; status(''); go(list[+b.dataset.i]); });
  }
  function useGPS() {
    if (!navigator.geolocation) { status('This browser cannot share its location. Search for a town or park instead.'); return; }
    status('Finding you…');
    navigator.geolocation.getCurrentPosition(p => { status(''); go({ name: 'Your location', la: p.coords.latitude, lo: p.coords.longitude, kind: 'gps' }); },
      e => status(e.code === 1 ? 'Location is blocked for this site. Allow it in your browser settings, or search for a town or park.' : 'Could not get your location. Search for a town or park instead.'),
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 600000 });
  }

  /* ---------- load everything for a place ---------- */
  async function go(p, keep) {
    here = p; save(p); const my = ++req;
    $('wxPlace').textContent = (p.ref ? p.ref + ' ' : '') + p.name;
    $('wxMeta').textContent = p.la.toFixed(4) + ', ' + p.lo.toFixed(4) + (p.kind === 'default' ? ' · default spot — tap USE MY LOCATION or search' : '');
    if (!keep) { ['wxNowBody', 'wxHours', 'wxDays', 'wxNwrBody'].forEach(id => $(id).innerHTML = '<p class="small">Loading…</p>'); $('wxAlerts').innerHTML = ''; mapTo(p); }
    const om = 'https://api.open-meteo.com/v1/forecast?latitude=' + p.la + '&longitude=' + p.lo +
      '&current=temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,is_day' +
      '&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m,wind_gusts_10m,is_day,cape' +
      '&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,sunrise,sunset,uv_index_max' +
      '&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=auto&forecast_days=7';
    const pts = jget('https://api.weather.gov/points/' + p.la.toFixed(4) + ',' + p.lo.toFixed(4), NWSH).catch(() => null);
    alerts(p, my);
    jget(om).then(j => { if (my === req) { now(j); hours(j); days(j, pts); } }).catch(() => { if (my === req) { $('wxNowBody').innerHTML = '<p class="small">The forecast service did not answer. Try again in a minute.</p>'; $('wxHours').innerHTML = ''; $('wxDays').innerHTML = ''; } });
    pts.then(pt => { if (my === req) office(pt, p); });
  }

  /* ---------- NWS alerts ---------- */
  const SEV = { Extreme: 'ex', Severe: 'sv', Moderate: 'md', Minor: 'mn' };
  async function alerts(p, my) {
    let j = null;
    try { j = await jget('https://api.weather.gov/alerts/active?point=' + p.la.toFixed(4) + ',' + p.lo.toFixed(4), NWSH); } catch (e) {}
    if (my !== req) return;
    const box = $('wxAlerts');
    if (!j) { box.innerHTML = '<div class="wx-al none">⚠ Could not reach the National Weather Service for alerts right now. Check <a href="https://www.weather.gov/" target="_blank" rel="noopener">weather.gov</a>.</div>'; return; }
    const f = (j.features || []).filter(x => x.properties && x.properties.status === 'Actual');
    drawWarn(f);
    if (!f.length) { box.innerHTML = '<div class="wx-al none ok">✅ No active NWS watches, warnings or advisories for this spot.</div>'; return; }
    const order = { Extreme: 0, Severe: 1, Moderate: 2, Minor: 3 };
    f.sort((a, b) => (order[a.properties.severity] ?? 9) - (order[b.properties.severity] ?? 9));
    box.innerHTML = f.map(x => {
      const a = x.properties, cls = SEV[a.severity] || 'mn';
      const ends = a.ends || a.expires;
      return `<details class="wx-al ${cls}"><summary><b>⚠ ${esc(a.event)}</b><span>${ends ? 'until ' + esc(new Date(ends).toLocaleString([], { weekday: 'short', hour: 'numeric', minute: '2-digit' })) : ''}${a.senderName ? ' · ' + esc(a.senderName) : ''}</span></summary>` +
        `<p class="wx-al-h">${esc(a.headline || '')}</p><pre>${esc((a.description || '').trim())}</pre>${a.instruction ? `<p class="wx-al-i"><b>What to do:</b> ${esc(a.instruction)}</p>` : ''}<p class="small">Areas: ${esc(a.areaDesc || '')}</p></details>`;
    }).join('');
    const top = f[0].properties; if (top.severity === 'Extreme' || top.severity === 'Severe') box.querySelector('details').open = true;
  }

  /* ---------- current conditions + field call ---------- */
  function now(j) {
    const c = j.current || {}, [ic, txt] = wx(c.weather_code, c.is_day), H = j.hourly || {};
    const t0 = H.time ? Math.max(0, H.time.findIndex(t => t >= (c.time || ''))) : 0;
    const next = k => (H[k] || []).slice(t0, t0 + 6);
    const storm = next('weather_code').some(v => v >= 95) || Math.max(0, ...next('cape').filter(isFinite)) >= 1500;
    const rain = Math.max(0, ...next('precipitation_probability').filter(isFinite));
    const gust = Math.max(c.wind_gusts_10m || 0, ...next('wind_gusts_10m').filter(isFinite));
    const calls = [];
    if (storm) calls.push(['bad', '⚡ Storms possible in the next 6 hours: plan to drop antennas and get off ridgelines.']);
    if (gust >= 30) calls.push(['bad', '💨 Gusts to ' + r0(gust) + ' mph: masts and tall verticals need guying, or wait it out.']);
    else if (gust >= 20) calls.push(['warn', '💨 Gusts to ' + r0(gust) + ' mph: guy that mast.']);
    if (rain >= 60) calls.push(['warn', '🌧️ ' + rain + '% chance of rain in the next 6 hours: bring a tarp and keep the radio dry.']);
    if (c.apparent_temperature >= 95) calls.push(['warn', '🥵 Feels like ' + r0(c.apparent_temperature) + '°F: shade, water and short sessions.']);
    if (c.apparent_temperature <= 32) calls.push(['warn', '🥶 Feels like ' + r0(c.apparent_temperature) + '°F: batteries lose capacity in the cold.']);
    if (!calls.length) calls.push(['good', '👍 Looks good for a portable setup right now.']);
    const vis = isFinite(c.visibility) ? (c.visibility / 1609).toFixed(c.visibility < 16090 ? 1 : 0) + ' mi' : '--';
    $('wxNowBody').innerHTML = `<div class="wx-now"><div class="wx-big"><span class="wx-ic">${ic}</span><span class="wx-t">${r0(c.temperature_2m)}°</span><span class="wx-d">${esc(txt)}<br><small>Feels like ${r0(c.apparent_temperature)}°F</small></span></div>
      <div class="wx-grid">
        <div><span>WIND</span><b>${dir(c.wind_direction_10m)} ${r0(c.wind_speed_10m)} mph</b><small>gusts ${r0(c.wind_gusts_10m)}</small></div>
        <div><span>HUMIDITY</span><b>${r0(c.relative_humidity_2m)}%</b><small>dew point ${r0(c.dew_point_2m)}°</small></div>
        <div><span>PRESSURE</span><b>${isFinite(c.pressure_msl) ? (c.pressure_msl * 0.02953).toFixed(2) : '--'} in</b><small>${r0(c.pressure_msl)} mb</small></div>
        <div><span>CLOUDS</span><b>${r0(c.cloud_cover)}%</b><small>visibility ${vis}</small></div>
        <div><span>SUNRISE</span><b>${j.daily && j.daily.sunrise ? tmm(j.daily.sunrise[0]) : '--'}</b><small>sunset ${j.daily && j.daily.sunset ? tmm(j.daily.sunset[0]) : '--'}</small></div>
        <div><span>UV TODAY</span><b>${j.daily && j.daily.uv_index_max ? r0(j.daily.uv_index_max[0]) : '--'}</b><small>${j.daily && j.daily.uv_index_max && j.daily.uv_index_max[0] >= 6 ? 'high: sunscreen' : 'max for today'}</small></div>
      </div></div>
      <div class="wx-calls">${calls.map(x => `<div class="wx-call ${x[0]}">${esc(x[1])}</div>`).join('')}</div>
      <p class="small">Updated ${esc(new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }))} · numbers from Open-Meteo (NOAA and other weather models).</p>`;
  }

  /* ---------- next 24 hours ---------- */
  function hours(j) {
    const H = j.hourly; if (!H || !H.time) { $('wxHours').innerHTML = ''; return; }
    const nowIso = (j.current && j.current.time) || '';
    let i0 = H.time.findIndex(t => t >= nowIso.slice(0, 13)); if (i0 < 0) i0 = 0;
    const cells = [];
    for (let i = i0; i < Math.min(H.time.length, i0 + 24); i++) {
      const [ic] = wx(H.weather_code[i], H.is_day[i]), pp = H.precipitation_probability[i];
      cells.push(`<div class="wx-h${H.weather_code[i] >= 95 ? ' ts' : ''}"><span>${i === i0 ? 'Now' : tm(H.time[i])}</span><i>${ic}</i><b>${r0(H.temperature_2m[i])}°</b><small class="pp${pp >= 50 ? ' hi' : ''}">💧${r0(pp)}%</small><small>${r0(H.wind_speed_10m[i])}<em>/${r0(H.wind_gusts_10m[i])}</em> mph</small></div>`);
    }
    $('wxHours').innerHTML = cells.join('');
  }

  /* ---------- 7 days + NWS text ---------- */
  function days(j, ptsP) {
    const D = j.daily; if (!D || !D.time) { $('wxDays').innerHTML = ''; return; }
    const lo = Math.min(...D.temperature_2m_min), hi = Math.max(...D.temperature_2m_max), span = Math.max(1, hi - lo);
    $('wxDays').innerHTML = '<div class="wx-days">' + D.time.map((d, i) => {
      const [ic, txt] = wx(D.weather_code[i], 1), a = (D.temperature_2m_min[i] - lo) / span * 100, b = (D.temperature_2m_max[i] - lo) / span * 100;
      return `<div class="wx-day"><b class="n">${dayName(d, i)}</b><i title="${esc(txt)}">${ic}</i><span class="pp${D.precipitation_probability_max[i] >= 50 ? ' hi' : ''}">💧${r0(D.precipitation_probability_max[i])}%</span>` +
        `<span class="lo">${r0(D.temperature_2m_min[i])}°</span><span class="bar"><em style="left:${a.toFixed(0)}%;right:${(100 - b).toFixed(0)}%"></em></span><span class="hi">${r0(D.temperature_2m_max[i])}°</span>` +
        `<small class="w">💨 ${r0(D.wind_gusts_10m_max[i])}</small></div>`;
    }).join('') + '</div><div id="wxNwsText"></div>';
    ptsP.then(async pt => {
      const box = $('wxNwsText'); if (!box) return;
      if (!pt || !pt.properties || !pt.properties.forecast) { box.innerHTML = ''; return; }
      try {
        const f = await jget(pt.properties.forecast, NWSH), P = (f.properties && f.properties.periods) || [];
        const pp = x => `<p><b>${esc(x.name)}:</b> ${esc(x.detailedForecast)}</p>`;
        box.innerHTML = `<div class="wx-nws"><b class="t">National Weather Service forecast, in words</b>${P.slice(0, 2).map(pp).join('')}${P.length > 2 ? `<details><summary>Next ${Math.min(P.length, 10) - 2} periods</summary>${P.slice(2, 10).map(pp).join('')}</details>` : ''}</div>`;
      } catch (e) { box.innerHTML = ''; }
    });
  }

  /* ---------- forecast office, county and NOAA Weather Radio ---------- */
  const SFIPS = { AL: '01', AR: '05', GA: '13', IL: '17', IN: '18', KY: '21', MO: '29', MS: '28', NC: '37', OH: '39', TN: '47', VA: '51', WV: '54' };
  async function office(pt, p) {
    const P = pt && pt.properties, box = $('wxNwrBody'), o = $('wxOffice');
    let same = '', county = '';
    if (P) {
      const cz = (P.county || '').split('/').pop();          // e.g. KYC227
      const m = /^([A-Z]{2})C(\d{3})$/.exec(cz); if (m && SFIPS[m[1]]) same = '0' + SFIPS[m[1]] + m[2];
      const rl = P.relativeLocation && P.relativeLocation.properties;
      if (rl && here && here.kind === 'gps') { $('wxPlace').textContent = 'Near ' + rl.city + ', ' + rl.state; }
      if (P.cwa) o.innerHTML = `Your NWS office: <a href="https://www.weather.gov/${esc(P.cwa.toLowerCase())}/" target="_blank" rel="noopener">${esc(P.cwa)} ↗</a> · <a href="https://forecast.weather.gov/product.php?site=${esc(P.cwa)}&issuedby=${esc(P.cwa)}&product=AFD&format=txt&glossary=1" target="_blank" rel="noopener">Forecast discussion ↗</a> · <a href="https://forecast.weather.gov/MapClick.php?lat=${p.la.toFixed(4)}&lon=${p.lo.toFixed(4)}" target="_blank" rel="noopener">NWS point forecast ↗</a>`;
      try { if (P.county) { const cj = await jget(P.county, NWSH); county = cj.properties && cj.properties.name; } } catch (e) {}
    } else o.innerHTML = '';
    const N = await nwr(), tx = (N.tx || []).map(t => Object.assign({}, t, { d: km(p.la, p.lo, t.la, t.lo) }));
    const cover = same ? tx.filter(t => t.same.includes(same)).sort((a, b) => a.d - b.d) : [];
    const near = tx.filter(t => !cover.includes(t)).sort((a, b) => a.d - b.d).slice(0, Math.max(0, 4 - cover.length));
    const LIVE = { KIH43: 27092, KIH44: 35436, KIH39: 40866 };   // volunteer streams on Broadcastify (sometimes offline)
    const row = (t, why) => `<div class="wx-tx${t.status !== 'NORMAL' ? ' off' : ''}"><div class="f">${esc(t.freq)}<small>MHz</small></div><div class="i"><b>${esc(t.call)} · ${esc(t.site)}, ${esc(t.st)}</b>` +
      `<span>${why} · ${mi(t.d)} mi away · ${esc(t.wfo)}${t.status !== 'NORMAL' ? ' · <em>' + esc(t.status) + '</em>' : ''}</span>` +
      (LIVE[t.call] ? `<a href="https://www.broadcastify.com/listen/feed/${LIVE[t.call]}" target="_blank" rel="noopener">▶ LISTEN ONLINE ↗</a>` : '') + '</div></div>';
    box.innerHTML = (cover.length ? `<p class="small">${county ? esc(county) + ' County' : 'Your county'} is covered by:</p>` + cover.map(t => row(t, 'covers your county')).join('') : '') +
      (near.length ? `<p class="small">${cover.length ? 'Also nearby' : 'Nearest transmitters'}:</p>` + near.map(t => row(t, 'nearby')).join('') : '') +
      (!cover.length && !near.length ? '<p class="small">No transmitter list loaded.</p>' : '') +
      `<p class="small">Most ham HTs and scanners have a <b>WX</b> button (162.400–162.550 MHz). Set the county code <b>${same || 'for your county'}</b> in a SAME weather radio to get alerts only for this county. ` +
      `Online streams are run by volunteers and are sometimes off: <a href="https://www.broadcastify.com/listen/stid/21" target="_blank" rel="noopener">Kentucky feeds on Broadcastify ↗</a>. Transmitter list from <a href="https://www.weather.gov/nwr/" target="_blank" rel="noopener">weather.gov/nwr</a> (${esc(N.updated || '')}).</p>`;
  }

  /* ---------- radar map ---------- */
  const RT = m => 'https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/nexrad-n0q-900913' + (m ? '-m' + String(m).padStart(2, '0') + 'm' : '') + '/{z}/{x}/{y}.png';
  const OFFS = [50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0];
  function initMap() {
    if (map || typeof L === 'undefined' || !$('wxMap')) return;
    map = L.map('wxMap', { scrollWheelZoom: false, zoomControl: true }).setView([37.8, -85.7], 7);
    const base = {
      'Streets': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '© OpenStreetMap' }),
      'Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 18, attribution: 'Esri' }),
      'Terrain': L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { maxZoom: 17, attribution: '© OpenTopoMap' })
    };
    base.Streets.addTo(map); L.control.layers(base, null, { position: 'topright' }).addTo(map);
    map.createPane('radar').style.zIndex = 420; map.createPane('light').style.zIndex = 430; map.createPane('warn').style.zIndex = 440;
    radar = OFFS.map((o, i) => L.tileLayer(RT(o), { pane: 'radar', opacity: i === OFFS.length - 1 ? .7 : 0, maxZoom: 12, attribution: 'NEXRAD: Iowa Environmental Mesonet' }).addTo(map));
    fi = OFFS.length - 1; frameLabel();
    lightning = L.tileLayer.wms('https://nowcoast.noaa.gov/geoserver/ows', { pane: 'light', layers: 'lightning_detection:ldn_lightning_strike_density', format: 'image/png', transparent: true, version: '1.3.0', opacity: .85, attribution: 'Lightning: NOAA nowCOAST' });
    warnLayer = L.geoJSON(null, { pane: 'warn', style: f => ({ color: WCOL(f.properties.event), weight: 3, fillOpacity: .08 }), onEachFeature: (f, l) => l.bindPopup('<b>' + esc(f.properties.event) + '</b><br>' + esc(f.properties.headline || '')) }).addTo(map);
    $('wxPlay').onclick = () => { if (loop) { clearInterval(loop); loop = null; $('wxPlay').textContent = '▶ PLAY LOOP'; show(OFFS.length - 1); } else { $('wxPlay').textContent = '⏸ PAUSE'; loop = setInterval(() => show((fi + 1) % OFFS.length), 650); } };
    $('wxLight').onchange = e => e.target.checked ? lightning.addTo(map) : map.removeLayer(lightning);
    $('wxWarnT').onchange = e => e.target.checked ? warnLayer.addTo(map) : map.removeLayer(warnLayer);
    $('wxMe').onclick = () => { if (here) map.setView([here.la, here.lo], 9); };
    setInterval(() => radar.forEach(l => l.redraw()), 5 * 60 * 1000);
  }
  const WCOL = e => /Tornado/.test(e) ? '#ff2a2a' : /Severe Thunderstorm/.test(e) ? '#ffa500' : /Flood/.test(e) ? '#2ecc71' : /Winter|Ice|Snow|Freez/.test(e) ? '#7fb2ff' : /Heat/.test(e) ? '#ff6f61' : '#f4c542';
  function show(i) { radar[fi] && radar[fi].setOpacity(0); fi = i; radar[fi].setOpacity(.7); frameLabel(); }
  function frameLabel() { const m = OFFS[fi]; $('wxFrame').textContent = m ? m + ' min ago' : 'Latest'; }
  function mapTo(p) {
    initMap(); if (!map) return;
    if (mk) map.removeLayer(mk);
    mk = L.circleMarker([p.la, p.lo], { radius: 8, color: '#fff', weight: 3, fillColor: '#1378ff', fillOpacity: 1 }).addTo(map).bindTooltip((p.ref ? p.ref + ' ' : '') + p.name);
    map.setView([p.la, p.lo], 8);
  }
  function drawWarn(features) { if (!warnLayer) return; warnLayer.clearLayers(); features.filter(f => f.geometry).forEach(f => { try { warnLayer.addData(Object.assign({ type: 'Feature' }, f)); } catch (e) {} }); }

  /* ---------- start ---------- */
  $('wxGeo').onclick = useGPS;
  const doSearch = async () => { const q = $('wxQ').value; if (!q.trim()) return; status('Searching…'); try { showResults(await search(q)); } catch (e) { status('Search failed. Try again.'); } };
  $('wxGo').onclick = doSearch;
  $('wxQ').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  const qs = new URLSearchParams(location.search), la = +qs.get('lat'), lo = +qs.get('lon');
  if (qs.has('lat') && isFinite(la) && isFinite(lo)) go({ name: qs.get('name') || 'Chosen spot', ref: qs.get('ref') || '', la, lo, kind: 'link' });
  else if (qs.get('ref')) search(qs.get('ref')).then(l => l[0] ? go(l[0]) : go(saved() || DEF));
  else {
    const s = saved();
    if (s && s.kind !== 'default' && s.kind !== 'gps') go(s);
    else if (navigator.permissions && navigator.permissions.query) navigator.permissions.query({ name: 'geolocation' }).then(r => r.state === 'granted' ? useGPS() : go(s || DEF), () => go(s || DEF));
    else go(s || DEF);
  }
  // refresh alerts and numbers every 10 minutes while the page is open
  setInterval(() => { if (here && document.visibilityState === 'visible') go(here, true); }, 10 * 60 * 1000);
})();

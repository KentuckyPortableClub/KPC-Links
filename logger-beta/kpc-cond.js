/* KPC app: ☀ CONDITIONS TAB (to-do 11, Nov 17; Brandon approved the mockup 'KPC Conditions tab — mockup': 'Perfect!').
   SPOTS gets two tabs at the top: SPOTS | CONDITIONS. Cards, top to bottom:
   - WEATHER HERE: my spot (GPS when the device has it, else my grid) → the National Weather Service (api.weather.gov, US
     only, free, no key): temperature, sky, wind + gusts, rain chance for the next 6 hours, and a THUNDER line. Honest about
     what it is: the NWS forecast + warnings for this point, NOT a live lightning detector. A thunderstorm / tornado WARNING
     here also goes to the alerts (AP.notify) and shows as a red line on the LOG screen. Sunset, the grey line and UTC.
   - SPACE WEATHER: solar flux, Kp, A, X-ray, Bz, solar wind — each with a plain word, tap a tile for what it means.
     NOAA SWPC (services.swpc.noaa.gov, the same feeds the website's space weather page and Lounges read), every 5 minutes
     while the tab is open, kept on the device so the last reading shows with no signal.
   - WHERE SHOULD I START: band · now · in 3 hours · what to expect = the app's rule of thumb (KPCProp.bands: flux, Kp,
     day or night at my grid) + how many spots each band has had in the last 30 minutes (real activity). Not a promise.
   - BAND PLAN: band chips, my class from STATION (Tech / General / Advanced / Extra, can be changed here to look), the band
     as a bar with what my class may use (AP.bandPlan, the same table the licence checks use), FT8 / FT4 dials; tap a
     part = the radio goes there (CAT) and the LOG line follows. 'Always check the full FCC chart.'
   - PLAN AN ACTIVATION: the next 3 days: NWS daytime forecast here + NOAA's 3-day geomagnetic / radio-blackout outlook.
   - NOAA ALERTS: NOAA space-weather scales (R / S / G) now, and NWS weather warnings here; big ones also as a phone alert.
   The old ☀ CONDITIONS sheet's day / night map stays: a button here opens it. */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id);
  if (!AP) return;
  const esc = AP.esc, SW = 'https://services.swpc.noaa.gov/';
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const UA = { 'user-agent': 'KPC app (kentuckyportableclub.github.io)', accept: 'application/geo+json, application/json' };
  async function getJ(url, o) {
    o = o || {};
    const r = AP.net.raw ? await AP.net.raw(url, { ms: o.ms || 15000, headers: o.h }) : null;
    if (r) { if (!r.ok) throw new Error('HTTP ' + (r.status || r.err || '?')); return JSON.parse(r.text || 'null'); }
    const x = await AP.net.fetch(url, {}, o.ms || 15000); if (!x.ok) throw new Error('HTTP ' + x.status); return x.json();
  }
  /* NOAA tables come as [[header…], [row…]] or as [{…}]: the last row as an object */
  function lastRow(j, want) {
    if (!Array.isArray(j) || !j.length) return null;
    const rows = Array.isArray(j[0]) ? j.slice(1).map(r => Object.fromEntries(j[0].map((h, i) => [h, r[i]]))) : j;
    for (let i = rows.length - 1; i >= 0; i--) { const r = rows[i]; if (want.every(k => r[k] != null && r[k] !== '' && isFinite(+r[k]))) return r; }
    return null;
  }
  const xClass = f => { f = +f; if (!(f > 0)) return null; const c = f >= 1e-4 ? 'X' : f >= 1e-5 ? 'M' : f >= 1e-6 ? 'C' : f >= 1e-7 ? 'B' : 'A', base = { X: 1e-4, M: 1e-5, C: 1e-6, B: 1e-7, A: 1e-8 }[c]; return c + (f / base).toFixed(1); };

  /* ---------------- space weather ---------------- */
  async function space(force) {
    const c = LS('kpcAppSpace', null);
    if (!force && c && Date.now() - c.t < 5 * 60000) return c;
    if (!AP.net.online()) return c;
    const v = { t: Date.now() };
    const tries = [
      getJ(SW + 'products/summary/10cm-flux.json').then(j => { const r = Array.isArray(j) ? j[0] : j; v.sfi = +(r && (r.flux ?? r.Flux)); }),
      getJ(SW + 'products/noaa-planetary-k-index.json').then(j => { const r = lastRow(j, ['Kp']); if (r) { v.kp = +r.Kp; if (r.a_running != null) v.a = +r.a_running; } }),
      getJ(SW + 'json/goes/primary/xrays-6-hour.json').then(j => { const L = (j || []).filter(x => /0\.1-0\.8/.test(x.energy || '') && +x.flux > 0); if (L.length) v.xf = +L[L.length - 1].flux; }),
      getJ(SW + 'products/solar-wind/mag-5-minute.json').then(j => { const r = lastRow(j, ['bz_gsm']); if (r) v.bz = +r.bz_gsm; }),
      getJ(SW + 'products/solar-wind/plasma-5-minute.json').then(j => { const r = lastRow(j, ['speed']); if (r) v.sw = +r.speed; }),
      getJ(SW + 'products/noaa-scales.json').then(j => { v.sc = j; })
    ];
    await Promise.allSettled(tries);
    ['sfi', 'kp', 'a', 'xf', 'bz', 'sw'].forEach(k => { if (!isFinite(v[k])) delete v[k]; });
    if (v.sfi == null && v.kp == null && !v.sc) return c;
    const out = Object.assign({}, c || {}, v); SV('kpcAppSpace', out);
    if (G.KPCProp && v.sfi != null && v.kp != null) SV('kpcAppSun', { kp: v.kp, sfi: v.sfi, t: v.t });   /* the old sheet reads this */
    return out;
  }
  const TILE = {
    sfi: ['Solar flux', v => Math.round(v), v => v >= 150 ? 'great' : v >= 100 ? 'good' : v >= 80 ? 'fair' : 'low', 'How much the sun is lighting up the high bands. Over 100 = 15, 12 and 10 m wake up in the day; under 80 = stick to 40 and 20.'],
    kp: ['Kp', v => (+v).toFixed(v % 1 ? 1 : 0), v => v >= 5 ? 'storm' : v >= 4 ? 'active' : v >= 3 ? 'unsettled' : 'quiet', 'How shaken up the earth\'s magnetic field is, 0 to 9. 0–2 quiet (good), 4 active (noisy, fading), 5 and up = a storm: high bands and long paths suffer.'],
    a: ['A index', v => Math.round(v), v => v >= 30 ? 'storm' : v >= 16 ? 'active' : v >= 8 ? 'unsettled' : 'quiet', 'The day\'s average of the same shaking as Kp. Under 8 = calm bands; over 15 = expect noise and fading.'],
    xf: ['X-ray', v => xClass(v), v => v >= 1e-4 ? 'big flare' : v >= 1e-5 ? 'flare' : v >= 1e-6 ? 'normal' : 'quiet', 'Flares from the sun. An M or X flare can wipe out the bands on the daylight side for minutes to an hour (a radio blackout), lowest bands first.'],
    bz: ['Bz', v => (v > 0 ? '+' : '') + (+v).toFixed(1), v => v <= -10 ? 'storm fuel' : v <= -3 ? 'south: watch' : 'fine', 'The direction of the sun\'s magnetic field arriving here. Pointing south (minus) for hours lets storms build; near zero or plus is fine.'],
    sw: ['Solar wind', v => Math.round(v), v => v >= 600 ? 'fast' : v >= 450 ? 'brisk' : 'calm', 'Speed of the solar wind in km/s. Over 500 with a southward Bz often means a storm is on the way.']
  };
  const overall = v => { if (!v) return ['?', '']; const k = v.kp ?? 2, s = v.sfi ?? 100; if (k >= 5 || (v.xf || 0) >= 1e-4) return ['rough', 'bad']; if (k >= 4) return ['fair', 'mid']; return s >= 100 ? ['good', 'ok'] : s >= 80 ? ['fair', 'mid'] : ['so-so', 'mid']; };

  /* ---------------- where am I ---------------- */
  let POS = null;
  async function here() {
    if (POS && Date.now() - POS.t < 30 * 60000) return POS;
    let p = null, how = 'grid';
    if (!AP.pc && AP.gps) { try { const g = await AP.gps({ maxAge: 30 * 60000, ms: 8000 }); p = { la: g.la, lo: g.lo }; how = 'GPS'; } catch (e) {} }
    if (!p) { const g = AP.gridLL && AP.gridLL(AP.myGrid()); if (g) p = { la: g.la, lo: g.lo }; }
    POS = p ? Object.assign(p, { how, t: Date.now() }) : null;
    return POS;
  }
  /* ---------------- weather (NWS, US) ---------------- */
  async function weather(force) {
    const c = LS('kpcAppWx', null), p = await here();
    if (!p) return { err: 'Set your grid in STATION → My station (or allow location) for the weather here.' };
    const key = p.la.toFixed(2) + ',' + p.lo.toFixed(2);
    if (!force && c && c.key === key && Date.now() - c.t < 15 * 60000) return c;
    if (!AP.net.online()) return c && c.key === key ? c : { err: 'No signal: the weather comes back with it.' };
    try {
      const pt = await getJ('https://api.weather.gov/points/' + p.la.toFixed(4) + ',' + p.lo.toFixed(4), { h: UA });
      const pr = pt && pt.properties; if (!pr || !pr.forecastHourly) throw new Error('no forecast');
      const [hr, dy, al] = await Promise.all([getJ(pr.forecastHourly, { h: UA }), getJ(pr.forecast, { h: UA }).catch(() => null), getJ('https://api.weather.gov/alerts/active?point=' + p.la.toFixed(4) + ',' + p.lo.toFixed(4), { h: UA }).catch(() => null)]);
      const H = ((hr && hr.properties && hr.properties.periods) || []).slice(0, 6), h0 = H[0] || {};
      const wx = { t: Date.now(), key, how: p.how, place: (pr.relativeLocation && pr.relativeLocation.properties && [pr.relativeLocation.properties.city, pr.relativeLocation.properties.state].filter(Boolean).join(', ')) || '',
        temp: h0.temperature, unit: h0.temperatureUnit || 'F', sky: h0.shortForecast || '', wind: [h0.windDirection, h0.windSpeed].filter(Boolean).join(' '),
        rain: Math.max(0, ...H.map(x => +((x.probabilityOfPrecipitation || {}).value) || 0)),
        thunder: H.filter(x => /thunder|t-storm/i.test(x.shortForecast || '')).map(x => x.startTime)[0] || '',
        days: (((dy && dy.properties && dy.properties.periods) || []).filter(x => x.isDaytime).slice(0, 4)).map(x => ({ name: x.name, temp: x.temperature, sky: x.shortForecast, pop: +((x.probabilityOfPrecipitation || {}).value) || 0, start: x.startTime })),
        alerts: (((al && al.features) || []).map(f => f.properties || {})).map(a => ({ ev: a.event, sev: a.severity, head: a.headline, end: a.ends || a.expires })).slice(0, 6) };
      SV('kpcAppWx', wx); warnCheck(wx); return wx;
    } catch (e) { return c && c.key === key ? c : { err: /404/.test(e.message) ? 'The National Weather Service covers the US only.' : 'Weather did not load (' + e.message + ').' }; }
  }
  /* a thunderstorm / tornado warning here: the alerts system + a red line on LOG */
  function warnCheck(wx) {
    const now = Date.now(), w = (wx.alerts || []).find(a => /thunderstorm warning|tornado warning|special marine/i.test(a.ev || '') && !(a.end && Date.parse(a.end) < now));   /* Nov 18 (Opus review): a saved forecast (no signal) kept showing a warning that had already ended */
    let bar = $('lgWx');
    if (!w) { if (bar) bar.hidden = true; return; }
    if (!bar && $('lgStrip')) { $('lgStrip').insertAdjacentHTML('afterend', '<div class="wxbar" id="lgWx" role="alert"></div>'); bar = $('lgWx'); }
    if (bar) { bar.hidden = false; bar.textContent = '⚡ ' + w.ev + ' for your spot (NWS). Get the antenna down and get inside.'; }
    if (AP.notify) AP.notify('wx', '⚡ ' + w.ev + ' for your spot (NWS)', { key: 'wx' + w.ev + w.end, every: 60 * 60000 });
  }
  /* ---------------- where should I start ---------------- */
  const BANDS = ['80m', '40m', '30m', '20m', '17m', '15m', '12m', '10m'];
  function start(v) {
    const P = G.KPCProp; if (!P) return [];
    const me = AP.gridLL && AP.gridLL(AP.myGrid()), now = Date.now(), later = now + 3 * 3600000;
    const dayAt = t => me ? P.elev(me.la, me.lo, t) > -0.833 : (h => h >= 7 && h < 19)(new Date(t).getHours());
    const g0 = P.bands(v && v.sfi, v && v.kp, dayAt(now)), g1 = P.bands(v && v.sfi, v && v.kp, dayAt(later));
    const cut = now - 30 * 60000, sp = G.KPCSpots ? KPCSpots.all().filter(s => s.t >= cut) : [], n = {};
    sp.forEach(s => { n[s.band] = (n[s.band] || 0) + 1; });
    const NOTE = { '80m': 'nights and close-in (under 300 mi)', '40m': 'the all-day workhorse, regional by day', '30m': 'CW / FT8 only, day and night', '20m': 'the main daytime DX band', '17m': 'like 20 m, quieter', '15m': 'daytime, needs flux over ~100', '12m': 'daytime, needs good flux', '10m': 'short skip in summer, DX with high flux' };
    return BANDS.map(b => ({ b, now: g0[b], later: g1[b], n: n[b] || 0, note: NOTE[b] })).sort((x, y) => (y.now * 10 + Math.min(9, y.n)) - (x.now * 10 + Math.min(9, x.n)));
  }
  /* ---------------- band plan ---------------- */
  const PB = [['160m', 1800, 2000], ['80m', 3500, 4000], ['60m', 5330, 5407], ['40m', 7000, 7300], ['30m', 10100, 10150], ['20m', 14000, 14350], ['17m', 18068, 18168], ['15m', 21000, 21450], ['12m', 24890, 24990], ['10m', 28000, 29700], ['6m', 50000, 54000], ['2m', 144000, 148000]];
  const FT8 = { '160m': 1840, '80m': 3573, '60m': 5357, '40m': 7074, '30m': 10136, '20m': 14074, '17m': 18100, '15m': 21074, '12m': 24915, '10m': 28074, '6m': 50313, '2m': 144174 };
  const FT4 = { '80m': 3575, '40m': 7047.5, '30m': 10140, '20m': 14080, '17m': 18104, '15m': 21140, '12m': 24919, '10m': 28180, '6m': 50318 };
  const KIND = { cw: 'CW + data', cwo: 'CW only', ph: 'phone', all: 'all modes' };
  let BP = { band: '20m', cls: '' };
  function planHtml() {
    const cls = BP.cls || AP.S.cls || 'E', b = PB.find(x => x[0] === BP.band) || PB[5], [, lo, hi] = b, W = hi - lo;
    const segs = (AP.bandPlan ? AP.bandPlan.segments(cls) : []).filter(s => s[1] > lo && s[0] < hi).map(s => [Math.max(lo, s[0]), Math.min(hi, s[1]), s[3]]).sort((x, y) => x[0] - y[0])
      .reduce((a, s) => { const p = a[a.length - 1]; if (p && p[2] === s[2] && s[0] <= p[1] + 0.01) p[1] = Math.max(p[1], s[1]); else a.push(s.slice()); return a; }, []);   /* the table splits by class: join touching parts of one kind */
    const pct = k => ((k - lo) / W * 100).toFixed(2);
    const bar = segs.map(s => `<button type="button" class="bps k-${esc(s[2])}" style="left:${pct(s[0])}%;width:${Math.max(1.2, (s[1] - s[0]) / W * 100).toFixed(2)}%" data-tune="${s[0] + Math.min(5, (s[1] - s[0]) / 2)}" data-kind="${esc(s[2])}" title="${esc(KIND[s[2]] || s[2])} ${s[0]}–${s[1]} kHz"></button>`).join('');
    const marks = [FT8[b[0]] && ['FT8', FT8[b[0]]], FT4[b[0]] && ['FT4', FT4[b[0]]]].filter(Boolean);
    return `<div class="chips bpb">${PB.map(x => `<button type="button" class="chip${x[0] === b[0] ? ' on' : ''}" data-bpband="${x[0]}">${x[0]}</button>`).join('')}</div>
      <label class="e">CLASS<select id="cdCls">${Object.entries(AP.bandPlan ? AP.bandPlan.classes : { E: 'Extra' }).map(([k, n]) => `<option value="${k}"${k === cls ? ' selected' : ''}>${n}${k === AP.S.cls ? ' (mine)' : ''}</option>`).join('')}</select></label>
      <div class="bpbar">${bar || '<span class="bpnone">No privileges for this class here.</span>'}${marks.map(m => `<i class="bpm" style="left:${pct(m[1])}%" title="${m[0]}"></i>`).join('')}</div>
      <div class="bpax"><span>${(lo / 1000).toFixed(3)}</span><span>${(hi / 1000).toFixed(3)} MHz</span></div>
      <div class="bpkey"><span><i class="k-cw"></i>CW + data</span><span><i class="k-ph"></i>phone</span><span><i class="k-all"></i>all modes</span><span><i class="bpm0"></i>FT8 / FT4</span></div>
      <ul class="hint bpl">${segs.map(s => `<li><button type="button" class="lnk" data-tune="${s[0] + Math.min(5, (s[1] - s[0]) / 2)}" data-kind="${esc(s[2])}">${(s[0] / 1000).toFixed(3)}–${(s[1] / 1000).toFixed(3)}</button> ${esc(KIND[s[2]] || s[2])}</li>`).join('')}
        ${marks.map(m => `<li><button type="button" class="lnk" data-tune="${m[1]}" data-kind="${m[0]}">${(m[1] / 1000).toFixed(3)}</button> ${m[0]} dial</li>`).join('')}</ul>`;
  }
  function tune(khz, kind) {
    khz = +khz; const mode = /FT8|FT4/.test(kind) ? kind : /cw/.test(kind) ? 'CW' : khz < 10000 ? 'LSB' : 'USB';
    const L = G.KPCLog; if (L && L.dock) { L.dock.khz = khz; L.dock.mode = mode === 'LSB' || mode === 'USB' ? 'SSB' : mode; if (L.saveDock) L.saveDock(); }
    if (G.KPCCat && KPCCat.connected()) KPCCat.tune(khz, mode);
    AP.toast('📻 ' + (khz / 1000).toFixed(3) + ' MHz ' + mode + (G.KPCCat && KPCCat.connected() ? '' : ' (on the LOG line; connect the radio to tune it)'), 2500);
  }
  /* ---------------- drawing ---------------- */
  const age = t => { const m = Math.round((Date.now() - t) / 60000); return m < 1 ? 'just now' : m < 60 ? m + ' min ago' : Math.round(m / 60) + ' h ago'; };
  const lt = t => new Date(t).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  const W3 = ['poor', 'fair', 'good'];
  function card(id, title, body) { return `<section class="card cdc" id="${id}"><h2>${title}</h2>${body}</section>`; }
  function sunLine() {
    const P = G.KPCProp, me = AP.gridLL && AP.gridLL(AP.myGrid()), now = Date.now();
    if (!P || !me) return `<p class="hint">UTC <b>${new Date().toISOString().slice(11, 16)}</b>. Set your grid for sunset and the grey line.</p>`;
    const rs = P.riseSet(me.la, me.lo, now), nx = [rs.rise, rs.set].filter(t => t && t > now).sort((a, b) => a - b)[0];
    const gl = nx ? Math.round((nx - now) / 60000) : null;
    return `<div class="cdrow"><span><i>SUNRISE</i><b>${rs.rise ? lt(rs.rise) : '—'}</b></span><span><i>SUNSET</i><b>${rs.set ? lt(rs.set) : '—'}</b></span><span><i>GREY LINE</i><b>${gl == null ? '—' : gl <= 30 ? 'now' : gl < 90 ? 'in ' + gl + ' min' : 'in ' + Math.round(gl / 60) + ' h'}</b></span><span><i>UTC</i><b>${new Date().toISOString().slice(11, 16)}</b></span></div>`;
  }
  function wxHtml(wx) {
    if (!wx || wx.err) return `<p class="hint">${esc((wx && wx.err) || 'Loading the weather…')}</p>` + sunLine();
    const th = (wx.alerts || []).find(a => /thunderstorm warning|tornado warning/i.test(a.ev || ''));
    const tl = th ? `<p class="cdbad">⚡ ${esc(th.ev)}: get the antenna down and get inside.</p>` : wx.thunder ? `<p class="cdmid">⚡ Thunderstorms in the forecast from about ${esc(lt(wx.thunder))}. Keep an eye on the sky.</p>` : '<p class="cdok">No thunderstorms in the forecast for the next 6 hours.</p>';
    return `<div class="cdwx"><b class="cdt">${wx.temp != null ? esc(String(wx.temp)) + '°' + esc(wx.unit === 'C' ? 'C' : '') : '—'}</b><span><b>${esc(wx.sky)}</b><br>Wind ${esc(wx.wind || '—')} · Rain ${wx.rain}% next 6 h</span></div>${tl}${sunLine()}
      <p class="hint">National Weather Service forecast for ${esc(wx.place || 'your spot')} (from ${esc(wx.how)}), ${esc(age(wx.t))}. This is the forecast and the warnings, not a lightning detector: if you hear thunder, you are close enough to be struck.</p>`;
  }
  function spaceHtml(v) {
    if (!v) return '<p class="hint">Loading NOAA\'s numbers…</p>';
    const [w, c] = overall(v);
    return `<p>Bands: <b class="cd-${c}">${w}</b></p><div class="cdtiles">${Object.entries(TILE).map(([k, t]) => v[k] == null ? '' : `<button type="button" class="cdtile" data-tile="${k}"><i>${esc(t[0])}</i><b>${esc(String(t[1](v[k])))}</b><span>${esc(t[2](v[k]))}</span></button>`).join('')}</div>
      <p class="hint">NOAA Space Weather Prediction Center, ${esc(age(v.t))}. Tap a tile for what it means.</p>`;
  }
  function startHtml(v) {
    const R = start(v); if (!R.length) return '';
    return `<table class="cdtab"><thead><tr><th>BAND</th><th>NOW</th><th>IN 3 H</th><th>WHAT TO EXPECT</th></tr></thead><tbody>${R.map(r => `<tr><td><b>${r.b}</b></td><td class="q${r.now}">${W3[r.now]}</td><td class="q${r.later}">${W3[r.later]}</td><td>${esc(r.note)}${r.n ? ` · <b>${r.n}</b> spot${r.n > 1 ? 's' : ''} in 30 min` : ''}</td></tr>`).join('')}</tbody></table>
      <p class="hint">A KPC rule of thumb from the flux, Kp and day or night at ${esc(AP.myGrid() || 'your grid')}, sorted with the busiest bands from SPOTS. Not a promise: the band itself is the real test (📡 WHO HEARD ME).</p>`;
  }
  function planActHtml(v, wx) {
    const sc = v && v.sc, days = (wx && wx.days) || [];
    const sp = i => { const d = sc && sc[String(i)]; if (!d) return null; const g = +((d.G || {}).Scale) || 0, r = +((d.R || {}).MinorProb) || 0; return { g, r, word: g >= 2 ? 'storm likely' : g >= 1 ? 'minor storm' : r >= 50 ? 'flares likely' : 'quiet' }; };
    const today = new Date().toDateString(), next = days.filter(d => new Date(d.start).toDateString() !== today);
    const rows = [1, 2, 3].map(i => { const d = next[i - 1] || null, dt = new Date(Date.now() + i * 864e5); return { name: (d && d.name) || dt.toLocaleDateString([], { weekday: 'long' }), d, s: sp(i) }; });
    return `<div class="cdplan">${rows.map(r => `<div class="cdday"><b>${esc(r.name)}</b><span>${r.d ? esc(r.d.sky) + ' · ' + esc(String(r.d.temp)) + '° · rain ' + r.d.pop + '%' : 'weather: —'}</span><span class="${r.s && r.s.g >= 1 ? 'cdmid' : ''}">space: ${r.s ? esc(r.s.word) + (r.s.g ? ' (G' + r.s.g + ')' : '') : '—'}</span></div>`).join('')}</div>
      <p class="hint">Daytime forecast for your spot (NWS) and NOAA's 3-day space weather outlook (G = geomagnetic storm level, flares = radio blackout chance).</p>`;
  }
  function alertsHtml(v, wx) {
    const out = [], d0 = v && v.sc && v.sc['0'];
    if (d0) [['R', 'Radio blackout'], ['S', 'Solar radiation storm'], ['G', 'Geomagnetic storm']].forEach(([k, n]) => { const s = +((d0[k] || {}).Scale) || 0; if (s > 0) out.push(`<li class="cdmid"><b>${n} ${k}${s}</b>${(d0[k] || {}).Text ? ' (' + esc(d0[k].Text) + ')' : ''}</li>`); });
    ((wx && wx.alerts) || []).forEach(a => out.push(`<li class="${/warning/i.test(a.ev) ? 'cdbad' : 'cdmid'}"><b>${esc(a.ev)}</b>${a.end ? ' until ' + esc(lt(a.end)) : ''}</li>`));
    return out.length ? `<ul class="cdal">${out.join('')}</ul>` : '<p class="cdok">No space-weather storms or weather warnings for your spot right now.</p>';
  }
  function bigAlerts(v) {
    const d0 = v && v.sc && v.sc['0']; if (!d0 || !AP.notify) return;
    const g = +((d0.G || {}).Scale) || 0, r = +((d0.R || {}).Scale) || 0;
    if (g >= 2) AP.notify('space', '🌐 Geomagnetic storm G' + g + ' now: high bands and long paths will be rough.', { key: 'G' + g + (d0.DateStamp || ''), every: 6 * 3600000 });
    if (r >= 2) AP.notify('space', '☀ Radio blackout R' + r + ': the daylight side of HF may be wiped out for a while.', { key: 'R' + r + (d0.DateStamp || '') + (d0.TimeStamp || ''), every: 3600000 });
  }
  let V = LS('kpcAppSpace', null), WX = LS('kpcAppWx', null);
  function draw() {
    const box = $('spCond'); if (!box) return;
    box.innerHTML = card('cdWx', '🌦 Weather here', wxHtml(WX)) + card('cdSpace', '☀ Space weather', spaceHtml(V)) + card('cdStart', '🎯 Where should I start?', startHtml(V))
      + card('cdPlan', '📻 Band plan', `<div id="cdBp">${planHtml()}</div><p class="hint">US privileges in short, for the class picked (yours is set in STATION → My station). Tap a part to tune there. Always check the full FCC chart: there are mode, power and Advanced-class details not shown here.</p>`)
      + card('cdAct', '🗓 Plan an activation', planActHtml(V, WX)) + card('cdAl', '⚠ Alerts', alertsHtml(V, WX))
      + '<div class="row"><button type="button" class="b" id="cdMap">🗺 DAY / NIGHT MAP</button><button type="button" class="b" id="cdRe">↻ REFRESH</button></div>';
    wire();
  }
  function wire() {
    const box = $('spCond');
    box.onclick = e => {
      const t = e.target.closest('[data-tile]'); if (t) { const k = TILE[t.dataset.tile]; AP.toast('<b>' + esc(k[0]) + '</b>: ' + esc(k[3]), 8000); return; }
      const bb = e.target.closest('[data-bpband]'); if (bb) { BP.band = bb.dataset.bpband; $('cdBp').innerHTML = planHtml(); wireCls(); return; }
      const tu = e.target.closest('[data-tune]'); if (tu) { tune(tu.dataset.tune, tu.dataset.kind || ''); return; }
      if (e.target.id === 'cdMap' && G.KPCProp) KPCProp.open();
      if (e.target.id === 'cdRe') refresh(true);
    };
    wireCls();
  }
  function wireCls() { const s = $('cdCls'); if (s) s.onchange = () => { BP.cls = s.value; $('cdBp').innerHTML = planHtml(); wireCls(); }; }
  let busy = false;
  async function refresh(force) {
    if (busy) return; busy = true;
    try { const [v, w] = await Promise.all([space(force), weather(force)]); if (v) V = v; WX = w; bigAlerts(V); } finally { busy = false; }
    if (shown()) draw();
  }
  /* ---------------- the two tabs on SPOTS ---------------- */
  const scr = $('scrSpots');
  const shown = () => scr && scr.dataset.sub === 'cond';
  function sub(which) {
    if (!scr) return;
    scr.dataset.sub = which; try { localStorage.setItem('kpcAppSpSub', which); } catch (e) {}
    document.querySelectorAll('#spSub [data-sub]').forEach(b => { b.classList.toggle('on', b.dataset.sub === which); b.setAttribute('aria-selected', b.dataset.sub === which); });
    if (which === 'cond') { draw(); refresh(false); }
  }
  if (scr && !$('spSub')) {
    scr.insertAdjacentHTML('afterbegin', '<div class="subtabs" id="spSub" role="tablist"><button type="button" role="tab" class="on" data-sub="spots">📍 SPOTS</button><button type="button" role="tab" data-sub="cond">☀ CONDITIONS</button></div>');
    scr.insertAdjacentHTML('beforeend', '<div class="cdbox" id="spCond"></div>');
    $('spSub').onclick = e => { const b = e.target.closest('[data-sub]'); if (b) sub(b.dataset.sub); };
    const old = $('spProp'); if (old) { old.onclick = () => sub('cond'); old.title = 'The CONDITIONS tab: weather here, space weather, where to start, band plan'; }
    if (!document.getElementById('kpcCondCss')) document.head.insertAdjacentHTML('beforeend', `<style id="kpcCondCss">
#spSub{display:flex;gap:6px;margin:0 0 8px}#spSub button{flex:1;height:38px;border-radius:12px;border:1px solid var(--line);background:var(--panel2);color:var(--sub);font:800 12px var(--sans);letter-spacing:.12em}
#spSub button.on{background:linear-gradient(180deg,#f6d58a,#d5a63a);color:var(--onGold);border-color:var(--gold)}
#scrSpots[data-sub=cond]>*:not(#spSub):not(#spCond){display:none!important}#scrSpots:not([data-sub=cond]) #spCond{display:none}
.cdbox{padding-bottom:16px}.cdc p{margin:6px 0}.cdwx{display:flex;gap:14px;align-items:center}.cdt{font:900 40px var(--mono);color:var(--goldT)}
.cdok{color:var(--ok)}.cdmid{color:var(--gold)}.cdbad{color:var(--red);font-weight:700}.cd-ok{color:var(--ok)}.cd-mid{color:var(--gold)}.cd-bad{color:var(--red)}
.cdrow{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.cdrow span{flex:1 1 70px;display:flex;flex-direction:column;padding:6px 8px;border-radius:10px;background:var(--panel2)}.cdrow i{font:700 10px var(--sans);letter-spacing:.1em;color:var(--sub);font-style:normal}.cdrow b{font:800 14px var(--mono)}
.cdtiles{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.cdtile{display:flex;flex-direction:column;align-items:center;padding:8px 4px;border-radius:12px;border:1px solid var(--line);background:var(--panel2);color:var(--text)}
.cdtile i{font:700 10px var(--sans);letter-spacing:.08em;color:var(--sub);font-style:normal;text-transform:uppercase}.cdtile b{font:900 18px var(--mono);color:var(--goldT)}.cdtile span{font-size:11px;color:var(--sub)}
.cdtab{width:100%;border-collapse:collapse;font-size:12px}.cdtab th{text-align:left;font:700 10px var(--sans);letter-spacing:.1em;color:var(--sub);padding:4px}.cdtab td{padding:5px 4px;border-top:1px solid var(--line);vertical-align:top}
.cdtab td.q2{color:var(--ok);font-weight:700}.cdtab td.q1{color:var(--gold)}.cdtab td.q0{color:var(--sub)}
.bpb{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px}.bpb .chip{height:30px;padding:0 9px}
.bpbar{position:relative;height:34px;margin-top:10px;border-radius:8px;background:var(--panel2);border:1px solid var(--line);overflow:hidden}
.bps{position:absolute;top:0;bottom:0;border:0;border-right:1px solid var(--bg);padding:0}.bps.k-cw,.bps.k-cwo{background:rgba(109,180,245,.55)}.bps.k-ph{background:rgba(232,184,74,.6)}.bps.k-all{background:rgba(95,211,155,.5)}
.bpm{position:absolute;top:-2px;bottom:-2px;width:2px;background:#fff;box-shadow:0 0 4px #fff}.bpnone{display:block;padding:8px;color:var(--sub);font-size:12px}
.bpkey{display:flex;flex-wrap:wrap;gap:10px;font-size:11px;color:var(--sub);margin-top:4px}.bpkey i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:-1px}.bpkey .k-cw{background:rgba(109,180,245,.7)}.bpkey .k-ph{background:rgba(232,184,74,.75)}.bpkey .k-all{background:rgba(95,211,155,.65)}.bpkey .bpm0{width:2px;background:#fff}
.bpax{display:flex;justify-content:space-between;font:11px var(--mono);color:var(--sub)}.bpl{padding-left:18px}.lnk{background:none;border:0;color:var(--rx);font:700 12px var(--mono);padding:0;text-decoration:underline}
.cdplan{display:grid;gap:6px}.cdday{display:flex;flex-direction:column;padding:8px;border-radius:10px;background:var(--panel2)}.cdday span{font-size:12px;color:var(--sub)}
.cdal{margin:4px 0;padding-left:18px}.wxbar{margin:0 0 8px;padding:8px 12px;border-radius:12px;background:rgba(224,92,92,.18);border:1px solid var(--red);color:#ffd9d9;font-weight:700}
</style>`);
    sub((() => { try { return localStorage.getItem('kpcAppSpSub'); } catch (e) { return ''; } })() === 'cond' ? 'cond' : 'spots');
  }
  setInterval(() => { if (shown() && document.visibilityState !== 'hidden') refresh(false); }, 5 * 60000);
  /* the weather warning check also runs in the background now and then (every 15 min, only with signal) */
  setInterval(() => { if (AP.net.online() && document.visibilityState !== 'hidden') weather(false).then(w => { if (w && !w.err) { WX = w; warnCheck(w); } }).catch(() => {}); }, 15 * 60000);
  G.KPCCond = { open: () => { if (AP.go) AP.go('spots'); sub('cond'); }, sub, refresh, space, weather, start, planHtml, _tile: TILE, xClass, _bp: BP, _set: (v, w) => { if (v) V = v; if (w) WX = w; draw(); } };
})(window);

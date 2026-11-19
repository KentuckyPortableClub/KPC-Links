/* KPC app: ONE ALERTS PLACE (Fable, Oct 22). Everything that wants Brandon's attention goes through AP.notify(kind, text):
     watch    a call on the watchlist is on the air (the spot frame)
     need     a spot for a park you still need (never hunted / never activated)
     closure  the club bots' park closure warnings (kpc-conditions.json, ids 'pa-…', every 3 h when online)
     hunters  'hunters are out' windows (app/hunters.json on the website, when that job exists: {windows:[{days:[1-7], from:'17:00', to:'21:00', note}]})
     calling  someone is calling you on FT8 · clock  the clock is off · info  anything else
   Each kind has a switch; an alert = a toast here, a buzz on the phone, and a real notification (Android through the native
   plugin, Windows through the desktop's own) so it reaches you with the screen off. The last 100 are kept in STATION → Alerts. */
(function (G) {
  'use strict';
  const $ = id => document.getElementById(id);
  const AP = G.KPCApp, esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const KINDS = { hear: '👂 A park you need, and your radio hears it', wx: '⚡ Weather warnings for your spot', space: '☀ Space weather storms', ptt: '⚠ The radio may still be transmitting', watch: '👀 Watchlist: a friend is on the air', need: '🌲 A park you still need is spotted', closure: '🚧 Park closures from the club bots', hunters: '🏹 Hunters are out', calling: '📞 Someone is calling you', clock: '⏱ Clock warnings', info: 'ℹ️ Other' };
  /* Nov 19 2026 (to-do 1): the toast says WHAT KIND of alert it is, not just an emoji */
  const LBL = { hear: 'Park you need, heard here', wx: 'Weather warning', space: 'Space weather', ptt: 'Radio check', watch: 'Watchlist', need: 'Park you need', closure: 'Park closure', hunters: 'Hunters are out', calling: 'Calling you', clock: 'Clock', info: '' };
  /* a park's name: from the spots (KPCParkNames, kpc-sources.js), else '' (packs are asked separately, they are async) */
  const pn = r => { const n = G.KPCParkNames && G.KPCParkNames[String(r || '').toUpperCase()]; return n ? r + ' ' + n : String(r || ''); };
  /* Nov 19 2026 (to-do 2, Brandon: 'new' + 'leave weather on'): a NEW user starts with every alert OFF except weather warnings and
     'the radio may still be transmitting' (a safety check, not a nice-to-know). Someone who already has alert settings keeps them. */
  const FRESH = LS('kpcAppAlerts', null) == null;
  const S = Object.assign({ on: FRESH ? { hear: 0, wx: 1, space: 0, ptt: 1, watch: 0, need: 0, closure: 0, hunters: 0, calling: 0, clock: 0, info: 0 } : { watch: 1, need: 0, closure: 1, hunters: 1, calling: 1, clock: 1, info: 1 }, buzz: 1, push: 1 }, LS('kpcAppAlerts', {}));
  if (FRESH) SV('kpcAppAlerts', Object.assign({}, S, { nv: 1 }));
  /* Oct 23 (Brandon: 'new park alerts lets set to default off'): the 'park you still need' alert starts OFF (once for everyone) */
  if (S.nv !== 1) { S.on.need = 0; S.nv = 1; SV('kpcAppAlerts', S); }
  /* Nov 18: new kinds start ON for everyone (a saved list from before does not have them) */
  ['hear', 'wx', 'space', 'ptt'].forEach(k => { if (S.on[k] == null) S.on[k] = 1; });
  const save = () => SV('kpcAppAlerts', S);
  let LOG = LS('kpcAlertLog', []);
  const SEEN = LS('kpcAlertSeen', {});
  const KA = G.KPCNative && G.KPCNative.native && G.Capacitor && G.Capacitor.registerPlugin ? G.Capacitor.registerPlugin('KpcAudio') : null;

  async function push(title, text) {
    if (!S.push) return;
    if (KA && KA.notify) { try { await KA.notify({ title, text }); return; } catch (e) {} }
    try { if (typeof Notification === 'function') { if (Notification.permission === 'default') await Notification.requestPermission(); if (Notification.permission === 'granted') new Notification(title, { body: text, silent: false }); } } catch (e) {}
  }
  let BURST = [], HELD = 0, HELDT = 0;
  function notify(kind, text, o) {
    o = o || {}; kind = KINDS[kind] ? kind : 'info';
    if (!S.on[kind]) return false;
    if (o.key) { const k = kind + ':' + o.key; if (SEEN[k] && Date.now() - SEEN[k] < (o.every || 3600000)) return false; SEEN[k] = Date.now(); const ks = Object.keys(SEEN); if (ks.length > 500) ks.slice(0, 200).forEach(x => delete SEEN[x]); SV('kpcAlertSeen', SEEN); }
    LOG.push({ kind, text, t: Date.now(), ref: o.ref || '' }); if (LOG.length > 100) LOG = LOG.slice(-100); SV('kpcAlertLog', LOG);
    /* Nov 18 (Opus review, alert storms): a burst (a band opening with 20 watched calls, a pile of closures) gave 20 toasts, 20 buzzes and
       20 notifications in a row. Now at most 3 in any 10 s show and buzz; the rest still go in the list (STATION → Alerts) and one line
       says how many more. 'The radio may still be transmitting' always shows. */
    const now = Date.now(); BURST = BURST.filter(t => now - t < 10000);
    /* Fable (merge, 0.9.8): a weather / lightning warning and anything marked bad (red) are never held back either */
    if (kind !== 'ptt' && kind !== 'wx' && !o.bad && BURST.length >= 3) {
      HELD++; if (!HELDT) HELDT = setTimeout(() => { if (HELD) AP.toast('🔔 ' + HELD + ' more alert' + (HELD > 1 ? 's' : '') + ': see STATION → Alerts.', 5000, 'log'); HELD = 0; HELDT = 0; }, Math.max(500, 10000 - (now - BURST[0])));
      draw(); AP.fire('alert', { kind, text, held: true }); return true;
    }
    BURST.push(now);
    AP.toast(KINDS[kind].slice(0, 2) + ' ' + (LBL[kind] ? '<b>' + esc(LBL[kind]) + ':</b> ' : '') + esc(text), o.ms || 7000, o.bad ? 'bad' : 'log');
    if (S.buzz) { try { if (navigator.vibrate) navigator.vibrate(kind === 'calling' ? [200, 80, 200, 80, 200] : [120, 60, 120]); } catch (e) {} }
    if (!o.quiet && (document.hidden || o.push)) push(KINDS[kind].replace(/^\S+\s/, ''), text);
    draw(); AP.fire('alert', { kind, text }); return true;
  }
  /* ---------------- sources ---------------- */
  const SITE = 'https://kentuckyportableclub.github.io/KPC-Links/';
  let COND = LS('kpcCond', { items: [], at: 0 });
  async function closures() {
    if (!AP.net.online() || Date.now() - (COND.at || 0) < 3 * 3600000) return;
    try {
      const r = await AP.net.fetch(SITE + 'kpc-conditions.json?v=' + Date.now().toString(36).slice(0, 7), {}, 15000); if (!r.ok) return;
      /* Oct 25 (HQ hand-off): 'pa-' = Kentucky state parks (the club's own, as before) + 'uc-' = chat 2's US closure watcher (173 in 10
         states on Oct 25). A US one only buzzes for MY PARK or a park in a state pack downloaded on this device, not for the whole country. */
      const j = await r.json(), today = new Date().toISOString().slice(0, 10), items = (j.items || []).filter(x => /^(pa|uc)-/.test(x.id || '') && (!x.expires || x.expires >= today));
      const old = new Set((COND.items || []).map(x => x.id)), first = !COND.at;
      COND = { items, at: Date.now() }; SV('kpcCond', COND);
      const mine = new Set(String(AP.S.ref || '').toUpperCase().split(/[\s,;+]+/).filter(Boolean)), packed = new Set();
      try { if (G.KPCParks && KPCParks.loaded) (await KPCParks.loaded()).forEach(pk => (pk.parks || []).forEach(p => packed.add(p.ref))); } catch (e) {}
      const care = x => /^pa-/.test(x.id) || (x.ref && (mine.has(x.ref) || packed.has(x.ref)));
      /* Nov 19 2026 (to-do 1): name the park, and say why this one reached you */
      const why = x => x.ref && mine.has(x.ref) ? 'It is your park.' : x.ref && packed.has(x.ref) ? 'It is in a state you downloaded.' : /^pa-/.test(x.id) ? 'A Kentucky state park (the club watches them all).' : '';
      const nm = async x => { if (!x.ref) return ''; if (x.name) return x.ref + ' ' + x.name; const p = pn(x.ref); if (p !== x.ref) return p; try { const n = G.KPCParks && await KPCParks.name(x.ref); if (n) return x.ref + ' ' + n; } catch (e) {} return x.ref; };
      if (!first) for (const x of items.filter(x => !old.has(x.id) && care(x)).slice(0, 5)) { const n = await nm(x); notify('closure', (n ? n + ': ' : '') + String(x.details || x.kind || '').slice(0, 160) + (why(x) ? ' ' + why(x) : ''), { key: x.id, every: 7 * 86400000, ref: x.ref }); }
      draw();
    } catch (e) {}
  }
  const closuresFor = ref => (COND.items || []).filter(x => x.ref === ref);
  let HUNT = LS('kpcHunters', { windows: [], at: 0 }), huntT = null;
  async function hunters() {
    if (!AP.net.online() || Date.now() - (HUNT.at || 0) < 12 * 3600000) return;
    try { const r = await AP.net.fetch(SITE + 'app/hunters.json?v=' + Date.now().toString(36).slice(0, 7), {}, 10000); if (!r.ok) { HUNT.at = Date.now(); SV('kpcHunters', HUNT); return; } const j = await r.json(); HUNT = { windows: j.windows || [], note: j.note || '', at: Date.now() }; SV('kpcHunters', HUNT); draw(); } catch (e) {}
  }
  function huntTick() {
    const now = new Date(), day = now.getDay() || 7, hm = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
    for (const w of HUNT.windows || []) if ((w.days || [1, 2, 3, 4, 5, 6, 7]).includes(day) && hm >= (w.from || '00:00') && hm <= (w.to || '23:59')) notify('hunters', (w.note || 'Most Kentucky hunters are about now') + ' (' + w.from + '–' + w.to + ').', { key: 'win' + w.from + w.to, every: 20 * 3600000, quiet: true });
  }
  /* spots: a park you still need */
  AP.on('spots', ev => {
    if (!G.KPCSpots || !G.KPCLog) return;
    const recent = KPCSpots.all().filter(s => Date.now() - s.t < 20 * 60000 && s.refs.length && s.src.includes(ev.src));
    const all = [...KPCLog.all().values()].filter(q => !q.d);
    for (const s of recent.slice(-5)) { const need = s.refs.filter(r => KPCLog.hunted ? !KPCLog.hunted(r) : !all.some(q => (q.refs || []).includes(r))); if (need.length) notify('need', s.call + ' is at ' + need.map(pn).join(' + ') + ' on ' + (s.khz / 1000).toFixed(3) + ' ' + s.mode + ' — you have not hunted it yet.', { key: need[0], every: 2 * 3600000, ref: need[0] }); }
  });

  /* ---------------- the card ---------------- */
  function draw() {
    const el = $('alList'); if (!el) return;
    el.innerHTML = LOG.length ? LOG.slice(-20).reverse().map(a => `<div class="op"><b>${esc(KINDS[a.kind].slice(0, 2))}</b> <span>${esc(a.text)}</span><i>${esc(AP.utc(a.t))}</i></div>`).join('') : '<p class="hint">Nothing yet. When a friend on your watchlist is spotted, a park you need comes up, or a park closes, it lands here and on your phone.</p>';
    const c = $('alCond'); if (c) { const n = (COND.items || []).length; c.textContent = n ? '🚧 ' + n + ' park notice' + (n > 1 ? 's' : '') + ' up right now (from the club bots, checked ' + (COND.at ? new Date(COND.at).toISOString().slice(11, 16) + ' UTC' : 'never') + ').' : 'No park notices up right now.'; }
    const h = $('alHunt'); if (h) h.textContent = HUNT.windows && HUNT.windows.length ? '🏹 Hunters are usually out: ' + HUNT.windows.map(w => w.from + '–' + w.to).join(', ') + (HUNT.note ? ' · ' + HUNT.note : '') : '🏹 "Hunters are out" times come from the website once that job runs.';
    const sw = $('alSw'); if (sw && !sw.children.length) {
      sw.innerHTML = Object.keys(KINDS).map(k => `<label class="ck" style="display:flex;margin:6px 0"><input type="checkbox" data-al="${k}"${S.on[k] ? ' checked' : ''}> <span>${esc(KINDS[k])}</span></label>`).join('') +
        `<label class="ck" style="display:flex;margin:6px 0"><input type="checkbox" id="alBuzz"${S.buzz ? ' checked' : ''}> <span>📳 Buzz the phone</span></label><label class="ck" style="display:flex;margin:6px 0"><input type="checkbox" id="alPush"${S.push ? ' checked' : ''}> <span>🔔 Show as a notification (reaches you with the screen off)</span></label>`;
      sw.querySelectorAll('[data-al]').forEach(x => { x.onchange = () => { S.on[x.dataset.al] = x.checked ? 1 : 0; save(); }; });
      $('alBuzz').onchange = () => { S.buzz = $('alBuzz').checked ? 1 : 0; save(); }; $('alPush').onchange = () => { S.push = $('alPush').checked ? 1 : 0; save(); if (S.push) push('KPC alerts are on', 'This is how they will look.'); };
    }
  }
  const bt = $('alTest'); if (bt) bt.onclick = () => notify('info', 'This is a test alert from KPC.', { push: true });
  const bc = $('alClear'); if (bc) bc.onclick = () => { LOG = []; SV('kpcAlertLog', LOG); draw(); };
  draw(); closures(); hunters(); huntTick();
  setInterval(() => { closures(); hunters(); huntTick(); }, 10 * 60000);
  AP.on('online', on => { if (on) { closures(); hunters(); } });
  AP.notify = notify;
  G.KPCAlerts = { S, save, notify, log: () => LOG, _held: () => HELD, closuresFor, conditions: () => COND, hunters: () => HUNT, KINDS };
})(window);

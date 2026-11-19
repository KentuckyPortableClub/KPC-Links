/* KPC app: 🏕 READY FOR THE FIELD + 📴 OFFLINE (Nov 18 2026; to-do 3; Brandon Nov 17: 'offline mode saving spots not needed they be old
   time you got there'). STATION → Parks → 🏕 GET READY FOR THE FIELD, one press while you still have signal:
     1. the park lists for your state, MY PARK's state and every state on your 🚗 trip (downloaded, or checked for a newer list)
     2. the forecast + space weather for the CONDITIONS tab (kept: the last reading shows with no signal)
     3. the clock checked against the internet (FT8 needs it right; no internet at the park)
     4. a copy of your log + settings saved as a file (💾 the same file as STATION → SAVE MY SETTINGS + LOG)
   It says what it did, line by line. No spots snapshot. 📴 OFFLINE in the top bar whenever the device has no signal. */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id); if (!AP) return;
  const esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  /* 📴 OFFLINE */
  function badge() { const b = $('offB'); if (b) b.hidden = AP.net.online(); }
  AP.on('online', badge); setInterval(badge, 5000); badge();
  /* which states this trip needs */
  async function states() {
    const P = G.KPCParks; if (!P) return [];
    const out = new Set();
    try { const p = await AP.gps({ maxAge: 3600000, ms: 8000 }); const st = P.stateNear(p.la, p.lo); if (st) out.add(st); }
    catch (e) { const g = AP.gridLL && AP.gridLL(AP.myGrid()); if (g) { const st = P.stateNear(g.la, g.lo); if (st) out.add(st); } }
    const T = LS('kpcAppTrip', { stops: [] }); (T.stops || []).forEach(s => { const st = P.stateNear(s.la, s.lo); if (st) out.add(st); });
    const have = await P.loaded(); String(AP.S.ref || '').toUpperCase().split(/[\s,]+/).forEach(r => { const pk = have.find(h => h.parks.some(x => x.ref === r)); if (pk) out.add(pk.state); });
    return [...out].filter(s => P.STATES.includes(s));
  }
  async function go() {
    const out = $('fdOut'), lines = [], say = (ok, t) => { lines.push((ok === true ? '✅ ' : ok === false ? '⚠ ' : '• ') + t); out.innerHTML = lines.map(x => '<div>' + x + '</div>').join(''); };
    out.hidden = false; out.className = 'st'; out.innerHTML = '⏳ Getting ready…';
    if (!AP.net.online()) { out.className = 'st bad'; out.textContent = '📴 No signal right now: do this at home or wherever you have signal.'; return { ok: false }; }
    const res = { parks: [], ok: true };
    if (G.KPCParks) {
      const need = await states(), have = Object.keys(KPCParks.have());
      for (const st of need) { if (!have.includes(st)) { const ok = await KPCParks.download(st); say(ok, 'Parks of ' + st + (ok ? ' downloaded' : ' did not download')); if (ok) res.parks.push(st); else res.ok = false; } }
      const r = await KPCParks.refresh(true).catch(() => ({ checked: 0, updated: [] }));
      say(true, 'Park lists on this device: ' + (Object.keys(KPCParks.have()).join(', ') || 'none') + (r.updated && r.updated.length ? ' (newer list for ' + r.updated.join(', ') + ')' : ' (up to date)'));
      const T = LS('kpcAppTrip', { stops: [] }); if ((T.stops || []).length) say(true, 'Your trip (' + T.stops.length + ' stops) is on this device');
    } else say(null, 'Park lists are not in this version of the app (Lite)');
    if (G.KPCCond) { try { const v = await KPCCond.space(true), w = await KPCCond.weather(true); say(!!v, 'Space weather saved' + (v ? '' : ': did not load')); say(!!(w && !w.err), w && !w.err ? 'Forecast for your spot saved' : 'Forecast: ' + esc((w && w.err) || 'did not load')); } catch (e) { say(false, 'Conditions did not load'); } }
    if (AP.clockCheck) { try { const c = await AP.clockCheck(); say(c !== false, c === false ? 'Clock: could not check it' : 'Clock checked against the internet'); } catch (e) {} }
    if (AP.backupText && AP.saveFile) { AP.saveFile(AP.backupText(), 'KPC-backup-' + String(AP.myCall() || 'app').replace(/[^A-Z0-9]/gi, '') + '-' + new Date().toISOString().slice(0, 10) + '.kpcbackup', 'application/json'); say(true, 'A copy of your log + settings is saved (the .kpcbackup file)'); }
    say(null, 'Spots are not saved: they are old by the time you get there.');
    SV('kpcAppField', { at: Date.now(), states: Object.keys((G.KPCParks && KPCParks.have()) || {}) });
    out.className = res.ok ? 'st ok' : 'st'; lines.unshift('<b>' + (res.ok ? '🏕 Ready for the field.' : '🏕 Mostly ready: see the ⚠ lines.') + '</b>'); out.innerHTML = lines.map(x => '<div>' + x + '</div>').join('');
    return res;
  }
  const b = $('fdGo'); if (b) b.onclick = go;
  const last = LS('kpcAppField', null); if (last && $('fdOut')) { $('fdOut').hidden = false; $('fdOut').textContent = 'Last got ready ' + new Date(last.at).toLocaleString() + ' (parks: ' + (last.states || []).join(', ') + ').'; }
  if (!$('kpcFieldCss')) document.head.insertAdjacentHTML('beforeend', '<style id="kpcFieldCss">.offb{font:800 11px var(--sans);letter-spacing:.08em;color:#ffd7a8;background:#5a3a0a;border:1px solid #f39a55;border-radius:10px;padding:3px 8px;margin-left:6px}</style>');
  G.KPCField = { go, states, badge };
})(window);

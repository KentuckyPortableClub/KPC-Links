/* KPC park closures + notices, one shared reader (Oct 25, HQ hand-off; chat 3).
   - kpc-conditions.json items: Kentucky state-park alerts + member reports, and 'uc-' entries = US state agencies' closures
     (chat 2's kpc_us_closures.py, every 6 h).
   - data/alerts/us-parks.json sources {id: {agency, st, page, ok}} = WHICH agencies are watched, so a page can say plainly
     what is covered. A park with no notice in a state we do not watch is NOT 'open'.
   KPCClos.get(ref, st) -> Promise {items, cover: [{agency, page, ok}], ky}
   KPCClos.html(ref, st, opts) -> Promise<string> (opts.print = plain sheet style, opts.quiet = say nothing when nothing to say)
   Styles are inline-free: pages style .kcl, .kcl-i, .kcl-c (a few defaults are added once). */
(function () {
  'use strict';
  if (window.KPCClos) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  // Step B6 (Oct 27): data/alerts lives in KPC-Data now; KPC.dataUrl tries it first, then this site's copy
  const j = u => ((/^data\/alerts\//.test(u) && window.KPC && typeof KPC.dataUrl === 'function') ? KPC.dataUrl(u, { cache: 'no-cache' }) : fetch(u, { cache: 'no-cache' })).then(r => r.ok ? r.json() : null).catch(() => null);
  let C = null, S = null;
  const cond = () => C || (C = j('kpc-conditions.json'));
  const srcs = () => S || (S = j('data/alerts/us-parks.json'));
  const css = document.createElement('style');
  css.textContent = '.kcl{margin:12px 0 0;padding:10px 12px;border-radius:10px;border:1px solid #e3b4ad;background:#fdf1ef;color:#3a1f1a;font:14px/1.45 Arial,sans-serif}' +
    '.kcl b.kcl-h{display:block;font:900 11px Arial,sans-serif;letter-spacing:1.2px;color:#a5281b;margin-bottom:4px}.kcl-i{padding:4px 0;border-top:1px solid rgba(0,0,0,.08)}.kcl-i:first-of-type{border-top:0}' +
    '.kcl-i small{display:block;color:#6b5a55}.kcl a{color:#a5281b;font-weight:700}.kcl-c{margin:6px 0 0;font-size:12.5px;color:#5c5450}.kcl.none{background:#f4f1ea;border-color:#ddd3c0;color:#3b372d}.kcl.none b.kcl-h{color:#5c5450}' +
    'html[data-theme="dark"] .kcl{background:#2a1714;border-color:#6b2f27;color:#f3e3df}html[data-theme="dark"] .kcl.none{background:#1f2328;border-color:#30363d;color:#e6edf3}html[data-theme="dark"] .kcl-c,html[data-theme="dark"] .kcl-i small{color:#b9b2a5}html[data-theme="dark"] .kcl a{color:#ff9b8c}';
  css.textContent += '.kcl-hunt{margin:12px 0 0;padding:10px 12px;border-radius:10px;border:1px solid #d9c49a;background:#fbf5e6;color:#3b2f17;font:14px/1.45 Arial,sans-serif}.kcl-hunt b.kcl-h{display:block;font:900 11px Arial,sans-serif;letter-spacing:1.2px;color:#8a5a00;margin-bottom:4px}.kcl-hunt.orange b.kcl-h{color:#c2410c}.kcl-hunt a{color:#8a5a00;font-weight:700}.kcl-hunt small{display:block;color:#6b5f48;margin-top:4px}' +
    '.kcl-i.note{color:#4a3d22}.kcl-i.note b{color:#8a5a00}.kcl-i.real{margin:4px -6px;padding:6px;border-radius:8px;background:#fde3d6;border:2px solid #e8590c}.kcl-i.real b{color:#c2410c}' +
    'html[data-theme="dark"] .kcl-hunt{background:#2a2414;border-color:#6b5a2a;color:#f1e7cf}html[data-theme="dark"] .kcl-hunt b.kcl-h,html[data-theme="dark"] .kcl-hunt a{color:#f0c96b}html[data-theme="dark"] .kcl-hunt small{color:#c9bc9c}html[data-theme="dark"] .kcl-i.real{background:#3a1d10;border-color:#e8590c}';
  document.head.appendChild(css);
  /* HQ + Brandon Oct 29 9:23 AM: Kentucky HUNTING SEASONS on every KY park card that hunters use (WMAs, state + national forests,
     wildlife refuges, recreation areas, wild river / wilderness areas, or any park with a KDFWR area page in data/ky-hunting.json):
     each season from 7 days before it starts until it ends, gun seasons first (blaze orange). Same lines as the Activation Kit. KY only. */
  let KYD = null, HUNT = null;
  const kyPark = ref => (KYD || (KYD = j('kpc-ky-data.json'))).then(d => ((d && d.parks) || []).find(p => p.c === ref) || null);
  const huntData = () => HUNT || (HUNT = j('data/ky-hunting.json'));
  async function hunt(ref) {
    if (window.KPCGate && typeof KPCGate.member === 'function' && !KPCGate.member()) return '';   // members-only beta first (HQ: the usual train)
    const [H, P] = await Promise.all([huntData(), kyPark(ref)]); if (!H) return '';
    const w = (H.wma || {})[ref], typ = ((P && P.t) || '') + ' ' + ((P && P.n) || '');
    if (!/WMA|Forest|Recreation Area|River \/ Wilderness|Wildlife|Wilderness/i.test(typ) && !w) return '';
    const iso = d => d.toISOString().slice(0, 10), today = iso(new Date()), soon = iso(new Date(Date.now() + 7 * 864e5));
    const fmt = x => new Date(x + 'T12:00:00').toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    const L = []; (H.seasons || []).forEach(x => (x.seg || []).forEach(g => { if (g[1] >= today && g[0] <= soon) L.push({ x, g, now: g[0] <= today }); }));
    L.sort((a, b) => (b.x.orange - a.x.orange) || a.g[0].localeCompare(b.g[0]));
    const md = today.slice(5), cl = ((w && w.closed) || []).filter(c => c[0] <= c[1] ? (md >= c[0] && md <= c[1]) : (md >= c[0] || md <= c[1]));
    if (!L.length && !cl.length && !(w && w.note)) return '';
    const gun = L.some(o => o.x.orange && o.now);
    return '<div class="kcl-hunt' + (gun ? ' orange' : '') + '"><b class="kcl-h">🦌 HUNTING ' + (gun ? 'SEASON NOW: WEAR BLAZE ORANGE' : 'SEASONS') + '</b>' +
      L.slice(0, 6).map(o => (o.now ? '' : 'Starts soon: ') + esc(o.x.name) + ' ' + fmt(o.g[0]) + '–' + fmt(o.g[1]) + (o.x.where !== 'statewide' ? ' (' + esc(o.x.where) + ')' : '')).join('<br>') +
      cl.map(c => '<br><b>Closed here now:</b> ' + esc(c[2])).join('') + (w && w.note ? '<br>' + esc(w.note) : '') +
      '<small>From Kentucky Fish &amp; Wildlife. ' + (w && w.link ? '<a href="' + esc(w.link) + '" target="_blank" rel="noopener">This area\'s hunting rules ↗</a>' : '<a href="https://fw.ky.gov/Hunt/Pages/default.aspx" target="_blank" rel="noopener">Season dates ↗</a>') + '</small></div>';
  }
  /* a quota-hunt NOTE (the area stays open except to the drawn hunters' tracts / days) looks like the season lines; a REAL closure
     to the public gets the red-orange line (HQ Oct 29: today only West Kentucky WMA 'Tract 1 is closed to public access') */
  const isNote = x => x.note === true || /note/i.test(x.kind || '') || (/hunt/i.test(x.kind || '') && /except drawn|quota hunt|drawn hunters/i.test(x.details || '') && !/closed to (all )?public access|closed to all access/i.test(x.details || ''));
  const isReal = x => x.closed === true || /closed to (all )?public access|closed to all access/i.test(x.details || '');

  async function get(ref, st) {
    const [c, s] = await Promise.all([cond(), srcs()]);
    const now = Date.now(), ky = st === 'KY' || (!st && /^KFF-|^W4K\//.test(ref || ''));
    const items = ((c && c.items) || []).filter(x => x.ref === ref && (!x.expires || Date.parse(x.expires) > now) && (ky || String(x.id).startsWith('uc-')));
    const cover = Object.values((s && s.sources) || {}).filter(x => x.st === st).map(x => ({ agency: x.agency, page: x.page, ok: x.ok }));
    return { items, cover, ky };
  }
  function nice(d) { const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d || ''); return m ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m[2] - 1] + ' ' + (+m[3]) : ''; }
  const NM = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'DC', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii',
    ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota',
    MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina',
    ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas',
    UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  async function html(ref, st, opts) {
    opts = opts || {};
    const r = await get(ref, st);
    if (!r.ky) return '';   /* Brandon Oct 29 scope rule (chat 11 check): closures are shown for Kentucky parks only */
    const hb = opts.noHunt ? '' : await hunt(ref).catch(() => '');
    const watch = r.ky ? 'Kentucky State Parks alerts and KPC member reports' : r.cover.length ? r.cover.map(x => x.agency).join(', ') : '';
    const covLine = r.ky || r.cover.length
      ? 'Checked: ' + esc(watch) + (r.ky ? '' : ' (every 6 hours)') + '. Other managers are not watched, so check the official page too.'
      : 'We do not watch closures in ' + esc(NM[st] || st || 'this state') + ' yet, so no notice here does NOT mean it is open. Check the official page before you go.';
    if (!r.items.length) {
      if (opts.quiet) return hb;
      return hb + '<div class="kcl none"><b class="kcl-h">CLOSURES &amp; NOTICES</b>' + (r.ky || r.cover.length ? 'No current notices for this park. ' : '') +
        '<p class="kcl-c">' + covLine + '</p></div>';
    }
    const items = r.items.slice().sort((a, b) => (isReal(b) - isReal(a)));
    return hb + '<div class="kcl"><b class="kcl-h">⚠ CLOSURES &amp; NOTICES (' + r.items.length + ')</b>' + items.slice(0, 6).map(x =>
      '<div class="kcl-i' + (isReal(x) ? ' real' : isNote(x) ? ' note' : '') + '"><b>' + (isReal(x) ? '⛔ CLOSED TO THE PUBLIC: ' : isNote(x) ? '🦌 ' + esc(/quota/i.test(x.details || '') ? 'Quota hunt' : (x.kind || 'Hunt note').replace(/closure/i, 'note')) + ':' : esc(x.kind || 'Notice') + ':') + '</b> ' + esc(x.details || '') +
      '<small>' + (x.seen ? 'Seen ' + esc(nice(x.seen)) : '') + (x.call && x.call !== 'KPC BOT' ? ' · reported by ' + esc(x.call) : '') +
      (x.link && !opts.print ? ' · <a href="' + esc(x.link) + '" target="_blank" rel="noopener">official notice ›</a>' : '') + '</small></div>').join('') +
      (r.items.length > 6 ? '<div class="kcl-i">+ ' + (r.items.length - 6) + ' more on the official page.</div>' : '') +
      '<p class="kcl-c">' + covLine + '</p></div>';
  }
  window.KPCClos = { get, html, hunt };
})();

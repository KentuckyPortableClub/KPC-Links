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
  const j = u => fetch(u, { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null);
  let C = null, S = null;
  const cond = () => C || (C = j('kpc-conditions.json'));
  const srcs = () => S || (S = j('data/alerts/us-parks.json'));
  const css = document.createElement('style');
  css.textContent = '.kcl{margin:12px 0 0;padding:10px 12px;border-radius:10px;border:1px solid #e3b4ad;background:#fdf1ef;color:#3a1f1a;font:14px/1.45 Arial,sans-serif}' +
    '.kcl b.kcl-h{display:block;font:900 11px Arial,sans-serif;letter-spacing:1.2px;color:#a5281b;margin-bottom:4px}.kcl-i{padding:4px 0;border-top:1px solid rgba(0,0,0,.08)}.kcl-i:first-of-type{border-top:0}' +
    '.kcl-i small{display:block;color:#6b5a55}.kcl a{color:#a5281b;font-weight:700}.kcl-c{margin:6px 0 0;font-size:12.5px;color:#5c5450}.kcl.none{background:#f4f1ea;border-color:#ddd3c0;color:#3b372d}.kcl.none b.kcl-h{color:#5c5450}' +
    'html[data-theme="dark"] .kcl{background:#2a1714;border-color:#6b2f27;color:#f3e3df}html[data-theme="dark"] .kcl.none{background:#1f2328;border-color:#30363d;color:#e6edf3}html[data-theme="dark"] .kcl-c,html[data-theme="dark"] .kcl-i small{color:#b9b2a5}html[data-theme="dark"] .kcl a{color:#ff9b8c}';
  document.head.appendChild(css);

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
    const watch = r.ky ? 'Kentucky State Parks alerts and KPC member reports' : r.cover.length ? r.cover.map(x => x.agency).join(', ') : '';
    const covLine = r.ky || r.cover.length
      ? 'Checked: ' + esc(watch) + (r.ky ? '' : ' (every 6 hours)') + '. Other managers are not watched, so check the official page too.'
      : 'We do not watch closures in ' + esc(NM[st] || st || 'this state') + ' yet, so no notice here does NOT mean it is open. Check the official page before you go.';
    if (!r.items.length) {
      if (opts.quiet) return '';
      return '<div class="kcl none"><b class="kcl-h">CLOSURES &amp; NOTICES</b>' + (r.ky || r.cover.length ? 'No current notices for this park. ' : '') +
        '<p class="kcl-c">' + covLine + '</p></div>';
    }
    return '<div class="kcl"><b class="kcl-h">⚠ CLOSURES &amp; NOTICES (' + r.items.length + ')</b>' + r.items.slice(0, 6).map(x =>
      '<div class="kcl-i"><b>' + esc(x.kind || 'Notice') + ':</b> ' + esc(x.details || '') +
      '<small>' + (x.seen ? 'Seen ' + esc(nice(x.seen)) : '') + (x.call && x.call !== 'KPC BOT' ? ' · reported by ' + esc(x.call) : '') +
      (x.link && !opts.print ? ' · <a href="' + esc(x.link) + '" target="_blank" rel="noopener">official notice ›</a>' : '') + '</small></div>').join('') +
      (r.items.length > 6 ? '<div class="kcl-i">+ ' + (r.items.length - 6) + ' more on the official page.</div>' : '') +
      '<p class="kcl-c">' + covLine + '</p></div>';
  }
  window.KPCClos = { get, html };
})();

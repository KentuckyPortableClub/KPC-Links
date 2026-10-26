/* KPC park facilities (Oct 25, HQ hand-off; chat 3): shelters, restrooms / bath houses and trailheads for Kentucky
   state parks + historic sites, from kpc-ky-facilities.json (built by .claude/build/facilities/build.py from the state
   parks GIS data chat 2 keeps). The other KY parks come later.
   KPCFac.html(ref, {la, lo, print}) -> Promise<string> ('' when we have nothing for that park).
   la/lo = where to measure from (the park's first parking point or its pin); nearest places are listed first. */
(function () {
  'use strict';
  if (window.KPCFac) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  /* data/ky-facilities.json (chat 2, 94 KY parks: yes / no summary, note, link) + kpc-ky-facilities.json (chat 3, the
     44 state parks' buildings + trailheads with GPS, for the directions lists) */
  let F = null, G = null;
  const get = u => fetch(u, { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null);
  const load = () => F || (F = get('kpc-ky-facilities.json'));
  const sum2 = () => G || (G = get('data/ky-facilities.json'));
  const mi = (a, b, c, d) => { const r = Math.PI / 180, x = Math.sin((c - a) * r / 2), y = Math.sin((d - b) * r / 2); return 2 * 3958.8 * Math.asin(Math.sqrt(x * x + Math.cos(a * r) * Math.cos(c * r) * y * y)); };
  const css = document.createElement('style');
  css.textContent = '.kfa{margin:12px 0 0;padding:10px 12px;border-radius:10px;border:1px solid #cfd9c9;background:#f1f6ee;color:#1f2d22;font:14px/1.45 Arial,sans-serif}' +
    '.kfa b.kfa-h{display:block;font:900 11px Arial,sans-serif;letter-spacing:1.2px;color:#1d5a3a;margin-bottom:4px}.kfa-n{font-weight:700}.kfa details{margin-top:6px}.kfa summary{cursor:pointer;font-weight:700;color:#1d5a3a}' +
    '.kfa a{display:block;padding:4px 0;color:#1d5a3a;text-decoration:none;border-top:1px solid rgba(0,0,0,.07);overflow-wrap:anywhere}.kfa small{display:block;margin-top:6px;color:#5f6a5f;font-size:12px}' +
    'html[data-theme="dark"] .kfa{background:#16201a;border-color:#2c4234;color:#e4efe6}html[data-theme="dark"] .kfa b.kfa-h,html[data-theme="dark"] .kfa summary,html[data-theme="dark"] .kfa a{color:#8fd3a6}html[data-theme="dark"] .kfa small{color:#a9b7ab}';
  document.head.appendChild(css);
  const dir = (la, lo) => 'https://www.google.com/maps/dir/?api=1&destination=' + la + ',' + lo;
  async function html(ref, o) {
    o = o || {};
    const [d, g] = await Promise.all([load(), sum2()]), p0 = d && d.parks && d.parks[ref], s = g && g.parks && g.parks[ref];
    if (!s && !(p0 && p0.sh.length + p0.rr.length + p0.th.length)) return '';
    const p = p0 || { sh: [], rr: [], th: [] };
    const yn = (k, lab) => s && s[k] ? lab + ': ' + (s[k] === 'yes' ? 'yes' : s[k] === 'no' ? 'no' : s[k]) : '';
    const line2 = s ? [s.shelters ? '' : yn('shelter', 'Shelter'), yn('tables', 'Picnic tables'), p.rr.length ? '' : yn('restrooms', 'Restrooms'), yn('water', 'Water'), yn('parking', 'Parking')].filter(Boolean).join(' · ') : '';
    const src = s && s.link ? (s.src === 'official park page' ? 'From the <a href="' + esc(s.link) + '" target="_blank" rel="noopener" style="display:inline;border:0;padding:0">official page</a>' : 'From the Kentucky State Parks map data') : 'From the Kentucky State Parks map data';
    const by = L => (isFinite(o.la) ? L.map(x => [x, mi(o.la, o.lo, x[0], x[1])]).sort((a, b) => a[1] - b[1]).map(x => x[0]) : L);
    const sh = by(p.sh), rr = by(p.rr), th = by(p.th);
    const thP = th.filter(t => t[4]).length, thR = th.filter(t => t[5]).length;
    const sum = [line2, sh.length ? sh.length + ' picnic shelter' + (sh.length > 1 ? 's' : '') : '', rr.length ? rr.length + ' restroom / bath house' + (rr.length > 1 ? 's' : '') : '',
      th.length ? th.length + ' trailhead' + (th.length > 1 ? 's' : '') + (thP ? ' (' + thP + ' with parking' + (thR ? ', ' + thR + ' with restrooms' : '') + ')' : '') : ''].filter(Boolean).join(' · ');
    if (o.print) {
      const li = (L, n, f) => L.slice(0, n).map(x => '<li>' + f(x) + ' — ' + x[0].toFixed(5) + ', ' + x[1].toFixed(5) + '</li>').join('');
      return '<ul class="ps-list"><li><b>' + esc(sum) + '</b></li>' + (s && s.note ? '<li>' + esc(s.note) + '</li>' : '') + li(sh, 3, x => 'Shelter: ' + esc(x[2])) + li(rr, 2, x => 'Restroom: ' + esc(x[2])) +
        li(th.filter(t => t[4]), 3, x => 'Trailhead: ' + esc(x[3] || x[2]) + (x[5] ? ' (restrooms)' : '')) + '<li style="font-size:12px">' + src.replace(/<[^>]+>/g, '') + (s && s.link && s.src === 'official park page' ? ' (' + esc(s.link) + ')' : '') + '. Confirm on site.</li></ul>';
    }
    const a = (L, f) => L.map(x => '<a href="' + dir(x[0], x[1]) + '" target="_blank" rel="noopener">' + f(x) + ' ›</a>').join('');
    const near = isFinite(o.la) ? ' (nearest first)' : '';
    return '<div class="kfa"><b class="kfa-h">🧺 SHELTERS, RESTROOMS &amp; TRAILHEADS</b><span class="kfa-n">' + esc(sum) + '</span>' + (s && s.note ? '<div>' + esc(s.note) + '</div>' : '') +
      (sh.length ? '<details><summary>Shelters' + near + '</summary>' + a(sh, x => esc(x[2])) + '</details>' : '') +
      (rr.length ? '<details><summary>Restrooms &amp; bath houses' + near + '</summary>' + a(rr, x => esc(x[2])) + '</details>' : '') +
      (th.length ? '<details><summary>Trailheads' + near + '</summary>' + a(th, x => esc(x[3] && x[3] !== x[2] ? x[2] + ' · ' + x[3] : x[2]) + (x[4] ? ' 🅿' : '') + (x[5] ? ' 🚻' : '')) + '</details>' : '') +
      '<small>' + (p.sh.length + p.rr.length + p.th.length ? 'Tap one for directions. ' : '') + src + ': confirm on site.</small></div>';
  }
  window.KPCFac = { html };
})();

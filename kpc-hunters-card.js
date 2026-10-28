/* WHEN IS POTA BUSIEST? card (was 'When are the hunters out?'; Brandon Oct 23: spots show busy times, not hunters) on Happening Now (Opus, Oct 23 2026). Reads kpc-hunters.json, which the KPC Hunters
   bot rebuilds every 15 minutes from its own counts of POTA spots on US parks (.github/scripts/kpc_hunters.py).
   Shows an hour-by-day grid in Central time (darker = more spots), the busiest windows and the busiest bands.
   Until 14 days are counted it says how far along it is. */
(function () {
  const box = document.getElementById('hunters'); if (!box) return;
  const D = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], DL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const hr = h => { h = +String(h).slice(0, 2); return h === 0 || h === 24 ? '12 AM' : h === 12 ? '12 PM' : h > 12 ? (h - 12) + ' PM' : h + ' AM'; };
  const out = box.querySelector('.hu-body');
  fetch('kpc-hunters.json?v=' + Date.now().toString(36).slice(0, 6), { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).then(j => {
    if (!j || !j.grid) { out.innerHTML = '<p class="hu-note">We started counting on Oct 23, 2026. Check back in about two weeks.</p>'; return; }
    const max = Math.max(1, ...j.grid.flat());
    let g = '<div class="hu-grid" role="img" aria-label="POTA spots on US parks by day and hour, Central time"><span></span>';
    for (let h = 0; h < 24; h += 1) g += '<span class="hu-h">' + (h % 3 ? '' : hr(h).replace(' ', '')) + '</span>';
    j.grid.forEach((row, d) => {
      g += '<span class="hu-d">' + D[d] + '</span>';
      row.forEach((v, h) => { const a = v / max; g += '<i title="' + DL[d] + ' ' + hr(h) + ': about ' + v + ' spots an hour" style="background:rgba(213,166,58,' + (0.06 + 0.94 * a).toFixed(2) + ')"></i>'; });
    });
    g += '</div>';
    const top = (j.top || []).map(w => '<li><b>' + DL[w.day - 1] + ' ' + hr(w.from) + '–' + hr(w.to) + '</b>' + (w.band ? ' · mostly ' + esc(w.band) : '') + ' · about ' + w.perHour + ' spots an hour</li>').join('');
    const odds = (j.odds || []).map(w => '<li><b>' + DL[w.day - 1] + ' ' + hr(w.from) + '–' + hr(w.to) + '</b> · about ' + w.perAct + ' spots for each activator on the air</li>').join('');
    const bands = (j.bands || []).slice(0, 4).map(b => esc(b[0]) + ' ' + b[1] + '%').join(' · ');
    out.innerHTML = (j.ready ? '' : '<p class="hu-note"><b>Still counting:</b> ' + j.days + ' of 14 days so far, so this is an early picture.</p>') +
      g + (top ? '<h3 class="hu-t">BUSIEST TIMES</h3><ul class="hu-top">' + top + '</ul>' : '') + (odds ? '<h3 class="hu-t">BEST ODDS FOR AN ACTIVATOR</h3><ul class="hu-top">' + odds + '</ul>' : '') +
      (bands ? '<p class="hu-note">Busiest bands: ' + bands + '</p>' : '') +
      '<p class="hu-note">Spots on US parks posted by someone other than the activator, last ' + Math.min(j.days, 56) + ' days, Central time. It shows when POTA is busy, not a head count of hunters. Updated ' + esc(new Date(j.updated).toLocaleString()) + '.</p>';
  }).catch(() => { out.innerHTML = '<p class="hu-note">Could not load the counts right now.</p>'; });
})();

/* Kentucky hunting seasons, worked out by date (Oct 17 2026, Brandon: bow for archery, gun for gun season, automatically; on the
   KY WMA cards; a small banner on the Activation Board and Parks). Dates follow KDFWR's usual pattern (check fw.ky.gov each year):
   deer archery 1st Sat Sep → 3rd Mon Jan; muzzleloader 3rd Sat Oct + Sun and 2nd Sat Dec (9 days); modern gun 2nd Sat Nov (16 days);
   spring turkey 2nd Sat Apr (23 days). Gun beats archery when both are open.
   On its own it: adds a small season chip to Kentucky WMA / forest / NRA park cards (Park Commander results, Park Notes, Campgrounds,
   Activation Kit) and fills <div id="kpc-season-bar"></div> with a banner. window.KPCSeason.now = {k, name, icon, end} or null. */
(function () {
  const nth = (y, m, wd, n) => { const d = new Date(y, m, 1); d.setDate(1 + ((wd - d.getDay() + 7) % 7) + (n - 1) * 7); return d; };
  const add = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
  const t = new Date(), day = new Date(t.getFullYear(), t.getMonth(), t.getDate()), S = [];
  for (const y of [t.getFullYear() - 1, t.getFullYear()]) {
    S.push(['archery', nth(y, 8, 6, 1), nth(y + 1, 0, 1, 3)]); S.push(['muzzle', nth(y, 9, 6, 3), add(nth(y, 9, 6, 3), 1)]);
    S.push(['gun', nth(y, 10, 6, 2), add(nth(y, 10, 6, 2), 15)]); S.push(['muzzle', nth(y, 11, 6, 2), add(nth(y, 11, 6, 2), 8)]);
    S.push(['turkey', nth(y + 1, 3, 6, 2), add(nth(y + 1, 3, 6, 2), 22)]);
  }
  const rank = { gun: 0, muzzle: 1, turkey: 2, archery: 3 };
  const open = S.filter(([, a, b]) => day >= a && day <= b).sort((a, b) => rank[a[0]] - rank[b[0]]);
  const RIFLE = '<svg viewBox="0 0 64 20" width="34" height="11" aria-hidden="true" style="vertical-align:middle"><path fill="currentColor" d="M1 9h30l3-3h9l1 2h14l5-1v4l-5 1H44l-2 2h-4l-1 5h-6l1-5h-3l-2 2H17l-3-2H1z"/></svg>';
  const N = { gun: 'Modern gun deer season', muzzle: 'Muzzleloader deer season', archery: 'Archery deer season', turkey: 'Spring turkey season' };
  const I = { gun: RIFLE, muzzle: RIFLE, archery: '🏹', turkey: '🦃' };
  const now = open.length ? { k: open[0][0], name: N[open[0][0]], icon: I[open[0][0]], end: open[0][2] } : null;
  window.KPCSeason = { now };
  if (!now) return;
  const fd = d => d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  const HUNT = /^(WMA|State Forest|National Forest|National Recreation Area|River \/ Wilderness)$/;
  const css = document.createElement('style');
  css.textContent = '.kss-chip{display:inline-flex;align-items:center;gap:6px;margin:4px 0;padding:3px 10px;border-radius:999px;background:#ff7a1a;color:#2a1205;font:900 11px Arial,sans-serif;letter-spacing:.6px;text-decoration:none;white-space:nowrap}'
    + '.kss-chip:hover{background:#ff944a}'
    + '.kss-bar{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:8px 14px;padding:9px 16px;background:#2a1205;border-bottom:2px solid #ff7a1a;color:#ffd2a8;font:13px Arial,sans-serif;text-align:center}'
    + '.kss-bar b{color:#fff;letter-spacing:.8px}.kss-bar a{color:#ffb070;font-weight:800}.kss-bar .ic{display:inline-flex;align-items:center;justify-content:center;min-width:42px;height:28px;border-radius:8px;background:#ff7a1a;color:#2a1205;font-size:18px}'
    + '@media print{.kss-chip,.kss-bar{display:none!important}}';
  document.head.appendChild(css);
  const chip = () => `<a class="kss-chip" href="https://fw.ky.gov" target="_blank" rel="noopener" data-keep-light title="${now.name} in Kentucky until about ${fd(now.end)}. Hunters may be here: wear blaze orange and stay near roads and parking. Dates follow KDFWR's usual pattern; check fw.ky.gov.">${now.icon} ${now.name.toUpperCase()} · WEAR ORANGE</a>`;
  const bar = document.getElementById('kpc-season-bar');
  if (bar) { bar.className = 'kss-bar'; bar.setAttribute('data-keep-light', ''); bar.innerHTML = `<span class="ic">${now.icon}</span><span><b>${now.name.toUpperCase()} IN KENTUCKY</b> until about ${fd(now.end)}. Hunters are in the WMAs and forests: wear blaze orange, stay near roads and parking, and check the area's rules. <a href="https://fw.ky.gov" target="_blank" rel="noopener">fw.ky.gov ›</a></span>`; }
  let T = null;
  if (!/^(finder|kpc-park-notes|kpc-campgrounds|kpc-kit)\.html$/.test(location.pathname.split('/').pop() || '')) return;   /* only these pages have park cards */
  fetch('kpc-ky-data.json').then(r => r.ok ? r.json() : null).then(d => { if (!d) return; T = {}; d.parks.forEach(p => { T[p.c] = p.t; }); scan(); }).catch(() => {});
  const isHunt = ref => T && HUNT.test(T[ref] || '');
  function put(el, where) { if (el.dataset.kss) return; el.dataset.kss = '1'; const s = document.createElement('div'); s.innerHTML = chip(); where.after ? where.after(s.firstChild) : el.appendChild(s.firstChild); }
  function scan() {
    if (!T) return;
    document.querySelectorAll('#items .entry').forEach(e => { const m = (e.querySelector('.tag') || {}).textContent || ''; const r = (m.match(/US-\d+/) || [])[0]; if (r && isHunt(r)) put(e, e.querySelector('h3')); });
    document.querySelectorAll('.pn-item[data-ref]').forEach(e => { if (isHunt(e.dataset.ref)) { const s = e.querySelector('summary .pn-nm'); if (s) put(e, s.lastChild || s); } });
    document.querySelectorAll('.cg-card[id^="park-"]').forEach(e => { if (isHunt(e.id.slice(5))) put(e, e.querySelector('h2')); });
    document.querySelectorAll('.kit-head').forEach(e => { const r = ((e.querySelector('.kit-ref') || {}).textContent || '').match(/US-\d+/); if (r && isHunt(r[0])) put(e, e.querySelector('h2')); });
  }
  let w = 0; new MutationObserver(() => { clearTimeout(w); w = setTimeout(scan, 300); }).observe(document.documentElement, { childList: true, subtree: true });
})();

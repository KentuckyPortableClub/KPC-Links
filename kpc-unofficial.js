/* KPC unofficial pages + maps, LAST RESORT (rule DOCS-U, Brandon Oct 31 2:53 PM).
   When a park has NO official agency page and / or NO official map, a page or map from a REAL NAMED organisation (friends group,
   tourism office, land trust, trail association, local club, town site) may be shown BELOW the official slot, never as official,
   labelled 'Unofficial page / map (from <organisation>): check with the agency before you go'. Directions / description / maps only.
   Data: KPC-Data data/unofficial.json {about, parks: {REF: {page: {url, org, checked}, map: {url, org, checked}}}}
   (filled by the documents bot, graded by chat 11; an entry is dropped when an official page / map is found).
   Use: put <div data-unoff="US-1234" data-has="page map"></div> under a card's official links; data-has lists the official
   ones the card already shows, so an unofficial one of that kind never appears next to it. The box fills by itself. */
(function () {
  'use strict';
  if (window.KPCUnoff) return;
  const BAN = /(^|\.)(google\.[a-z.]+|goo\.gl|alltrails\.com|tripadvisor\.[a-z.]+|yelp\.[a-z.]+|wikipedia\.org|wikimedia\.org|wikiloc\.com|blogspot\.[a-z.]+|wordpress\.com|medium\.com|tumblr\.com|reddit\.com|foursquare\.com|hipcamp\.com|campendium\.com|thedyrt\.com|gaiagps\.com|onxmaps\.com|mapcarta\.com|waze\.com)$/i;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let P = null;
  function load() {
    return P || (P = ((window.KPC && typeof KPC.dataUrl === 'function') ? KPC.dataUrl('data/unofficial.json', { cache: 'no-cache' }) : fetch('data/unofficial.json', { cache: 'no-cache' }))
      .then(r => r && r.ok ? r.json() : {}).then(j => (j && j.parks) || {}).catch(() => ({})));
  }
  function ok(x) {
    if (!x || !x.url || !String(x.org || '').trim()) return false;
    try { const u = new URL(x.url); return /^https?:$/.test(u.protocol) && !BAN.test(u.hostname.replace(/^www\./, '')); } catch (e) { return false; }
  }
  async function html(ref, has) {
    const all = await load(), u = all[String(ref || '').toUpperCase()]; if (!u) return '';
    has = String(has || '');
    const rows = [['page', '🌐', 'page'], ['map', '🗺', 'map']].filter(([k]) => !new RegExp('\\b' + k + '\\b').test(has) && ok(u[k]))
      .map(([k, ic, w]) => '<a href="' + esc(u[k].url) + '" target="_blank" rel="noopener nofollow" style="display:block;padding:8px 10px;margin:6px 0 0;border:1px dashed rgba(150,150,150,.7);border-radius:10px;color:inherit;text-decoration:none;font-size:13px;line-height:1.35">' +
        ic + ' <b>Unofficial ' + w + ' (from ' + esc(u[k].org) + ')</b>: check with the agency before you go ↗' + (u[k].checked ? '<br><span style="opacity:.75;font-size:12px">Last checked ' + esc(u[k].checked) + '. Not for rules, hours, fees, closures or 2-fers.</span>' : '<br><span style="opacity:.75;font-size:12px">Not for rules, hours, fees, closures or 2-fers.</span>') + '</a>');
    return rows.join('');
  }
  async function fill(el) {
    if (!el || el.dataset.unoffDone === el.dataset.unoff) return; el.dataset.unoffDone = el.dataset.unoff;
    el.innerHTML = await html(el.dataset.unoff, el.dataset.has);
  }
  const scan = () => document.querySelectorAll('[data-unoff]').forEach(fill);
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== 'loading') scan(); else document.addEventListener('DOMContentLoaded', scan);
  window.KPCUnoff = { load, html, fill, ok };
})();

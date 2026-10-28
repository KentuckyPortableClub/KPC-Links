/* Club Room 'What's new' box (HQ + Brandon Oct 28 5:10 AM, the WEEKLY RELEASE TRAIN): reads kpc-release-train.json and shows the
   newest members' batch on top, older ones folded. Empty until Brandon's first GO. Members-only (lives in the Club Room). */
(function () {
  'use strict';
  var el = document.getElementById('kpcRel'); if (!el) return;
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var KIND = { '2fer': '🧩 2-FERS', links: '🗺 OFFICIAL MAP LINKS', hours: '🕒 HOURS & FEES', camp: '🏕 CAMPGROUNDS', outline: '📐 NEW OUTLINES', other: '✨ NEW' };
  var INFO = 'ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go. <a href="kpc-about-info.html">About our information</a>';
  var TWO = '⚠️ Parks’ boundaries may overlap here, but we can’t confirm it. Check both official boundary maps and make your own call before you count it.';
  function nice(d) { var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d || ''); return m ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][+m[2] - 1] + ' ' + (+m[3]) + ', ' + m[1] : esc(d); }
  function batch(b) {
    var items = b.items || [];
    return '<div class="rel-b"><div class="rel-h"><b>' + esc(b.title || 'This week’s release') + '</b><span>' + nice(b.date) + '</span></div>' + (b.note ? '<p class="rel-n">' + esc(b.note) + '</p>' : '') +
      '<ul>' + items.map(function (i) { return '<li><span class="rel-k">' + (KIND[i.kind] || KIND.other) + '</span> ' + esc(i.text) + (i.link ? ' <a href="' + esc(i.link) + '">' + esc(i.where || 'OPEN') + ' ›</a>' : i.where ? ' <i>(' + esc(i.where) + ')</i>' : '') + '</li>'; }).join('') + '</ul></div>';
  }
  fetch('kpc-release-train.json', { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }).then(function (d) {
    var B = ((d && d.batches) || []).slice().sort(function (a, b) { return String(b.date).localeCompare(String(a.date)); });
    if (!B.length) { el.innerHTML = '<p class="rel-empty"><b>Nothing new yet.</b> Each week, everything that passed its checks ships to members together on <b>Sunday evening</b>: 2-fers, official map links, hours and fees, campground info and new park outlines. It will be listed here.</p>'; return; }
    var kinds = {}; B.forEach(function (b) { (b.items || []).forEach(function (i) { kinds[i.kind] = 1; }); });
    el.innerHTML = batch(B[0]) + (B.length > 1 ? '<details class="rel-old"><summary>EARLIER RELEASES (' + (B.length - 1) + ')</summary>' + B.slice(1).map(batch).join('') + '</details>' : '') +
      (kinds['2fer'] ? '<p class="rel-ntc">' + TWO + '</p>' : '') + (kinds['2fer'] || kinds.links || kinds.hours || kinds.camp || kinds.outline ? '<p class="rel-ntc">' + INFO + '</p>' : '');
  });
})();

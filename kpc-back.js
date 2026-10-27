/* KPC "back to the Lounge" bar (Oct 26, Brandon: 'when a Lounge tab opens another page … a clear way back').
   A page opened from a Lounge tab carries ?from=hunters or ?from=activators (or came straight from that Lounge):
   a gold '← HUNTERS LOUNGE' / '← ACTIVATORS LOUNGE' bar sits at the top of the page. Nothing shows otherwise,
   and nothing inside a Lounge tab (?embed=1). Load it with defer on any page a Lounge tab opens. */
(function () {
  'use strict';
  if (/[?&]embed=1/.test(location.search)) return;
  var T = { hunters: ['kpc-hunters.html', '← HUNTERS LOUNGE'], activators: ['kpc-activators-lounge.html', '← ACTIVATORS LOUNGE'] };
  var q = new URLSearchParams(location.search).get('from');
  if (!T[q]) { var r = document.referrer || ''; q = /kpc-hunters(-need)?\.html/.test(r) ? 'hunters' : /kpc-activators-lounge\.html/.test(r) ? 'activators' : ''; }
  if (!T[q]) return;
  function put() {
    if (document.getElementById('kpcBack')) return;
    var m = document.querySelector('main') || document.body, a = document.createElement('div');
    a.id = 'kpcBack';
    a.innerHTML = '<a href="' + T[q][0] + '">' + T[q][1] + '</a>';
    m.insertBefore(a, m.firstChild);
  }
  var css = document.createElement('style');
  css.textContent = '#kpcBack{position:sticky;top:var(--kpc-back-top,0);z-index:900;display:flex;justify-content:flex-start;padding:8px 14px;background:rgba(11,8,5,.92);border-bottom:1px solid rgba(240,201,107,.5);box-sizing:border-box;max-width:100%}' +
    '#kpcBack a{display:inline-flex;align-items:center;min-height:36px;padding:6px 16px;border-radius:999px;background:linear-gradient(#f6d58a,#d5a63a);color:#2a1a05!important;font:900 12px Arial,sans-serif;letter-spacing:1.2px;text-decoration:none;white-space:nowrap}';
  document.head.appendChild(css);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', put); else put();
  /* sit under the sticky site header */
  addEventListener('load', function () { var h = document.querySelector('header.site-nav, header'); if (h && getComputedStyle(h).position.match(/sticky|fixed/)) document.documentElement.style.setProperty('--kpc-back-top', h.offsetHeight + 'px'); });
})();

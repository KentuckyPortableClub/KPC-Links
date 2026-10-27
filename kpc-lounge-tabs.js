/* KPC Lounge tab strip (Oct 26, Brandon: 'tabs must stay put … ONE tab strip, the same order and the same spot (right under
   the hero) on every page it appears on, with the current tab lit'; 'nothing should cover anything').
   ONE strip per Lounge, built here, never floating (normal page flow, right under the page's hero picture):
     Hunters:    ← BACK · SPOTS & LOG · PARK CHECKER · ACTIVATION BOARD · RADIO CONDITIONS · HAPPENING NOW
     Activators: ← BACK · TOOLS · ACTIVATION BOARD · WEATHER · RADIO CONDITIONS · HAPPENING NOW
   Which Lounge: the page itself (kpc-hunters*.html / kpc-activators-lounge.html), else ?from=hunters|activators, else the
   page it came from. Pages shared by both Lounges (Activation Board, Radio Conditions) show the strip of the Lounge the
   visitor came from; opened from the menu they show none. Happening Now = #live on the Lounge page (its own panel).
   Phones: the strip scrolls sideways by itself (the page never does); the lit tab is scrolled into view. */
(function () {
  'use strict';
  if (/[?&]embed=1/.test(location.search) || document.getElementById('kpcLTabs')) return;
  var SETS = {
    hunters: { home: 'kpc-hunters.html', tabs: [['spots', '🎯 SPOTS & LOG', 'kpc-hunters.html#spots'], ['checker', '📋 PARK CHECKER', 'kpc-hunters-need.html'],
      ['board', '📝 ACTIVATION BOARD', 'kpc-activations.html?from=hunters'], ['radio', '☀️ RADIO CONDITIONS', 'kpc-space-weather.html?from=hunters'], ['live', '📡 HAPPENING NOW', 'kpc-hunters.html#live']] },
    activators: { home: 'kpc-activators-lounge.html', tabs: [['tools', '🧰 TOOLS', 'kpc-activators-lounge.html#tools'], ['board', '📝 ACTIVATION BOARD', 'kpc-activations.html?from=activators'],
      ['weather', '🌦 WEATHER', 'kpc-weather.html?from=activators'], ['radio', '☀️ RADIO CONDITIONS', 'kpc-space-weather.html?from=activators'], ['live', '📡 HAPPENING NOW', 'kpc-activators-lounge.html#live']] }
  };
  var page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  var set = /^kpc-hunters(-need)?\.html$/.test(page) ? 'hunters' : page === 'kpc-activators-lounge.html' ? 'activators' : '';
  if (!set) { var q = new URLSearchParams(location.search).get('from'); set = SETS[q] ? q : ''; }
  if (!set) { var r = document.referrer || ''; set = /kpc-hunters(-need)?\.html/.test(r) ? 'hunters' : /kpc-activators-lounge\.html/.test(r) ? 'activators' : ''; }
  if (!set) return;
  var S = SETS[set];
  function current() {
    if (page === 'kpc-hunters.html') return location.hash === '#live' ? 'live' : 'spots';
    if (page === 'kpc-activators-lounge.html') return location.hash === '#live' ? 'live' : 'tools';
    return { 'kpc-hunters-need.html': 'checker', 'kpc-activations.html': 'board', 'kpc-space-weather.html': 'radio', 'kpc-weather.html': 'weather' }[page] || '';
  }
  var css = document.createElement('style');
  css.textContent = '#kpcLTabs{position:relative!important;top:auto!important;z-index:1;display:flex;gap:8px;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;scrollbar-width:none;max-width:100%;box-sizing:border-box;' +
    'padding:10px 12px;margin:0;background:#0b0805;border-top:1px solid rgba(240,201,107,.35);border-bottom:1px solid rgba(240,201,107,.35);justify-content:safe center}' +
    '#kpcLTabs::-webkit-scrollbar{display:none}' +
    '#kpcLTabs a{flex:0 0 auto;display:inline-flex;align-items:center;min-height:38px;padding:7px 15px;border-radius:999px;border:1px solid rgba(240,201,107,.6);background:transparent;color:#f0c96b!important;' +
    'font:900 12px/1 Arial,sans-serif;letter-spacing:1.1px;text-decoration:none;white-space:nowrap;box-sizing:border-box}' +
    '#kpcLTabs a[aria-current=page]{background:linear-gradient(#f6d58a,#d5a63a);color:#2a1a05!important;border-color:#d5a63a}' +
    '#kpcLTabs a.kl-back{border-style:dashed}' +
    '@media(max-width:700px){#kpcLTabs{justify-content:flex-start}}';
  document.head.appendChild(css);
  function hero() {
    var m = document.querySelector('main') || document.body, c = [].slice.call(document.querySelectorAll('[class*="hero"]')).filter(function (e) {
      if (e.closest('header.site-nav, .site-nav, nav, footer, #kpcLTabs')) return false; var r = e.getBoundingClientRect(); return r.height > 80 && r.top + scrollY < 1100 && e.parentElement && !e.parentElement.closest('[class*="hero"]');
    });
    return c[0] || null;
  }
  function build() {
    var n = document.createElement('div'); n.id = 'kpcLTabs'; n.setAttribute('role', 'navigation'); n.setAttribute('aria-label', set === 'hunters' ? 'Hunters Lounge' : 'Activators Lounge');
    n.innerHTML = '<a href="' + (page === S.home ? 'index.html' : S.home) + '" class="kl-back" data-kl="back">← BACK</a>' + S.tabs.map(function (t) { return '<a href="' + t[2] + '" data-kl="' + t[0] + '">' + t[1] + '</a>'; }).join('');
    var h = hero(), m = document.querySelector('main') || document.body;
    if (h) h.parentNode.insertBefore(n, h.nextSibling); else m.insertBefore(n, m.firstChild);
    n.querySelector('[data-kl=back]').addEventListener('click', function (e) {   // the page you came from, else the Lounge
      if (history.length > 1 && document.referrer && new URL(document.referrer).origin === location.origin) { e.preventDefault(); history.back(); }
    });
    [].forEach.call(n.querySelectorAll('[data-kl]'), function (a) {   // tabs on this same page switch by #hash (no reload) and ALWAYS move the page
      var u = new URL(a.href, location.href); if (a.dataset.kl === 'back' || u.pathname !== location.pathname) return;
      a.addEventListener('click', function (e) {
        e.preventDefault();
        if (location.hash !== u.hash) { history.pushState(null, '', location.pathname + location.search + u.hash); dispatchEvent(new HashChangeEvent('hashchange')); }
        setTimeout(function () { jump(u.hash); }, 60);
      });
    });
    var lv = document.getElementById('hlLive') || document.getElementById('lgLive');   // the Happening Now panel sits right under the strip
    if (lv) n.parentNode.insertBefore(lv, n.nextSibling);
    lit();
  }
  /* Oct 26 (Brandon: 'the tool tab does nothing'): every tab visibly does something. TOOLS = smooth scroll to the first tool
     section ('Find a place to activate'), SPOTS & LOG = the main spots, HAPPENING NOW = the strip at the top with the panel under it.
     The page's sticky bars (site header, conditions bar, parks ticker) are measured so the target is not hidden under them. */
  var JUMP = { '#tools': function () { return document.getElementById('lgFind') || document.querySelector('#lgTools .lg-sec'); }, '#spots': function () { return document.getElementById('hlSpSec') || document.querySelector('.hl-split'); }, '#live': function () { return document.getElementById('kpcLTabs'); } };
  function stuckH() { var h = 0, hd = document.querySelector('header.site-nav'); if (hd && /sticky|fixed/.test(getComputedStyle(hd).position)) h = hd.getBoundingClientRect().height;
    var extra = 0; [].forEach.call(document.querySelectorAll('#hlTick, .kcx'), function (e) { var cs = getComputedStyle(e); if (/sticky|fixed/.test(cs.position) && e.offsetParent !== null && cs.display !== 'none') extra = Math.max(extra, e.getBoundingClientRect().height); }); return h + extra; }
  function jump(hash) { var f = JUMP[hash], el = f && f(); if (!el) return; var y = el.getBoundingClientRect().top + scrollY - stuckH() - 8; if (hash === '#live') y = el.getBoundingClientRect().top + scrollY - stuckH(); scrollTo({ top: Math.max(0, y), behavior: 'smooth' }); }
  function lit() {
    var n = document.getElementById('kpcLTabs'); if (!n) return; var c = current();
    [].forEach.call(n.querySelectorAll('[data-kl]'), function (a) { if (a.dataset.kl === c) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    var on = n.querySelector('[aria-current]'); if (on) n.scrollLeft = Math.max(0, on.offsetLeft - (n.clientWidth - on.offsetWidth) / 2);
  }
  addEventListener('hashchange', lit);
  /* build as soon as the hero is on the page (before the Lounge's own scripts lay out their windows); else when the page is ready */
  function start() { if (document.getElementById('kpcLTabs')) return; build(); try { dispatchEvent(new Event('resize')); } catch (e) {} }
  if (document.readyState !== 'loading' || hero()) start(); else document.addEventListener('DOMContentLoaded', start);
  window.KPCLTabs = { lit: lit, jump: jump };
  /* opened from another tab page with #tools / #spots: land on that spot once the page has laid itself out */
  if (/^#(tools|spots)$/.test(location.hash) && JUMP[location.hash]) addEventListener('load', function () { setTimeout(function () { jump(location.hash); }, 300); });
})();

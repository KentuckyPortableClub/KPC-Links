/* KPC dark mode (Oct 2026). Load in <head> on every page: <script src="kpc-theme.js?v=..."></script>
   - Follows the phone / computer setting (prefers-color-scheme) unless the visitor picks Dark or Light with the
     🌗 button this script adds to the top bar (saved in localStorage kpcTheme = auto | dark | light).
   - The site's pages use many hand-written light colours, so instead of a stylesheet per page this reads each
     element's real colours and swaps light backgrounds for dark ones and dark text for light text (same hue).
     Pictures, maps tiles, the QR code and anything inside [data-keep-light] are left alone.
   - Printing (and the PDF printer) always uses the normal light look. */
(function () {
  'use strict';
  var KEY = 'kpcTheme', root = document.documentElement;
  var mq = window.matchMedia ? matchMedia('(prefers-color-scheme: dark)') : null;
  function pref() { try { return localStorage.getItem(KEY) || 'auto'; } catch (e) { return 'auto'; } }
  /* page LOOKS (kpc-looks.js, Oct 17 2026): a picked look (Cabin Lodge, Night Sky, Campfire, Dark) on this page always uses the dark colours */
  try { var LK = localStorage.getItem('kpcLook:' + (location.pathname.split('/').pop() || 'index.html')); if (/^(lodge|night|camp|aurora|overlook|dark)$/.test(LK || '')) root.setAttribute('data-look', LK); } catch (e) {}
  function wantDark() { if (root.hasAttribute('data-look')) return true; var p = pref(); return p === 'dark' || (p === 'auto' && mq && mq.matches); }
  var noDark = /[?&](print|pdf)=/.test(location.search) || root.hasAttribute('data-no-dark');
  // paint the page dark straight away (no white flash), then fix colours once it has loaded
  var early = document.createElement('style'); early.id = 'kpc-theme-early';
  early.textContent = 'html[data-theme=dark]{background:#0e100e;color-scheme:dark}html[data-theme=dark] body{background:#0e100e}' +
    'html[data-theme=dark].kpc-th-wait body{opacity:0}' +
    '.kpc-theme-btn{flex:0 0 auto;width:38px;height:38px;border-radius:50%;border:1px solid rgba(213,166,58,.7);background:rgba(0,0,0,.35);color:#f0c96b;font-size:18px;line-height:1;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;padding:0;margin-left:6px}' +
    '.kpc-theme-btn:hover{background:#d5a63a;color:#111}@media(max-width:760px){.site-nav .nav-inner .kpc-theme-btn{order:2;margin-left:auto;margin-right:8px}.site-nav .nav-inner .menu-toggle{order:3}}' +
    '@media print{html[data-theme=dark],html[data-theme=dark] body{background:#fff!important}.kpc-theme-btn{display:none!important}}';
  (document.head || root).appendChild(early);
  if (!noDark && wantDark()) { root.setAttribute('data-theme', 'dark'); root.classList.add('kpc-th-wait'); setTimeout(function () { root.classList.remove('kpc-th-wait'); }, 1500); }

  /* ---------- colour helpers ---------- */
  function parse(c) { var m = /rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)/.exec(c || ''); return m ? [+m[1], +m[2], +m[3], m[4] == null ? 1 : +m[4]] : null; }
  function hsl(r, g, b) { r /= 255; g /= 255; b /= 255; var mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2, h = 0, s = 0, d = mx - mn;
    if (d) { s = l > .5 ? d / (2 - mx - mn) : d / (mx + mn); h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h /= 6; } return [h, s, l]; }
  function css(h, s, l, a) { return 'hsla(' + Math.round(h * 360) + ',' + Math.round(s * 100) + '%,' + Math.round(l * 100) + '%,' + (a == null ? 1 : a) + ')'; }
  var SKIP = /^(IMG|PICTURE|VIDEO|CANVAS|IFRAME|SVG|svg|SCRIPT|STYLE|NOSCRIPT|LINK|META|BR|HR|SOURCE|OPTION)$/;
  function skipEl(el) { return SKIP.test(el.tagName) || (el.classList && (el.classList.contains('leaflet-tile-pane') || el.classList.contains('leaflet-tile') || el.classList.contains('qrbox'))) || el.hasAttribute('data-keep-light') || !!(el.closest && el.closest('[data-keep-light]')); }

  var saved = new WeakMap(), touched = new Set(), effBg = new WeakMap();
  function setP(el, prop, val) {
    var o = saved.get(el); if (!o) { o = {}; saved.set(el, o); touched.add(el); }
    if (!(prop in o)) o[prop] = [el.style.getPropertyValue(prop), el.style.getPropertyPriority(prop)];
    el.style.setProperty(prop, val, 'important');
  }
  function revertEl(el) { var o = saved.get(el); if (!o) return; Object.keys(o).forEach(function (p) { if (o[p][0]) el.style.setProperty(p, o[p][0], o[p][1]); else el.style.removeProperty(p); }); saved.delete(el); touched.delete(el); }

  function fix(el, parentL) {
    var cs = getComputedStyle(el), myL = parentL;
    var bg = parse(cs.backgroundColor);
    if (bg && bg[3] > 0.35) {
      var h = hsl(bg[0], bg[1], bg[2]);
      if (h[2] > 0.72) { var nl = 0.075 + (1 - h[2]) * 0.55; setP(el, 'background-color', css(h[0], h[1] * 0.3, nl, bg[3])); myL = nl; }
      else if (h[2] > 0.6 && h[1] < 0.35) { setP(el, 'background-color', css(h[0], h[1] * 0.4, 0.22, bg[3])); myL = 0.22; }
      else myL = h[2];
    }
    var bi = cs.backgroundImage;
    if (bi && bi !== 'none' && bi.indexOf('gradient') >= 0 && bi.indexOf('url(') < 0) {
      var cols = (bi.match(/rgba?\([^)]+\)/g) || []).map(parse).filter(Boolean);
      if (cols.length) { var avg = cols.reduce(function (a, c) { return a + hsl(c[0], c[1], c[2])[2] * (c[3] > .3 ? 1 : 0); }, 0) / cols.length;
        if (avg > 0.75) { setP(el, 'background-image', 'none'); var c0 = hsl(cols[0][0], cols[0][1], cols[0][2]); setP(el, 'background-color', css(c0[0], c0[1] * .3, 0.1)); myL = 0.1; } }
    }
    if (myL < 0.45) {   // text sits on a dark background: make dark text light
      var fg = parse(cs.color);
      if (fg) { var f = hsl(fg[0], fg[1], fg[2]); if (f[2] < 0.5) setP(el, 'color', css(f[0], Math.min(1, f[1] * 0.75), Math.min(0.93, 0.93 - f[2] * 0.55), fg[3])); }
    }
    ['top', 'right', 'bottom', 'left'].forEach(function (s) {
      if (parseFloat(cs['border-' + s + '-width']) > 0) { var bc = parse(cs['border-' + s + '-color']); if (bc && bc[3] > .2) { var b = hsl(bc[0], bc[1], bc[2]); if (b[2] > 0.7) setP(el, 'border-' + s + '-color', css(b[0], b[1] * .5, 0.26, bc[3])); } }
    });
    effBg.set(el, myL);
    return myL;
  }
  function svgFix(el) {   // line drawings on white: soft invert so they sit on the dark page (colours keep their hue)
    if (el.tagName.toLowerCase() !== 'svg' || el.closest('.leaflet-container,[data-keep-light]')) return;
    var cs = getComputedStyle(el), bg = parse(cs.backgroundColor), light = bg && bg[3] > .35 && hsl(bg[0], bg[1], bg[2])[2] > .8;
    if (!light) { var r = el.querySelector(':scope > rect'); if (r) { var fl = parse(getComputedStyle(r).fill); var w = parseFloat(r.getAttribute('width') || '0'); light = fl && hsl(fl[0], fl[1], fl[2])[2] > .85 && (String(r.getAttribute('width')).indexOf('%') > 0 || w >= (el.viewBox && el.viewBox.baseVal ? el.viewBox.baseVal.width * .9 : 1e9)); } }
    if (light) { setP(el, 'filter', 'invert(.9) hue-rotate(180deg) saturate(1.2)'); setP(el, 'border-radius', '8px'); }
  }
  function walk(rootEl, startL) {
    var stack = [[rootEl, startL]];
    while (stack.length) {
      var it = stack.pop(), el = it[0];
      if (el.nodeType !== 1) continue;
      if (skipEl(el)) { if (el.tagName.toLowerCase() === 'svg') svgFix(el); continue; }
      var l = fix(el, it[1]);
      for (var c = el.lastElementChild; c; c = c.previousElementSibling) stack.push([c, l]);
    }
  }
  function parentL(el) { for (var p = el.parentElement; p; p = p.parentElement) { if (effBg.has(p)) return effBg.get(p); } return 0.07; }
  var on = false, mo = null, pending = new Set(), raf = 0;
  function flush() { raf = 0; var list = Array.from(pending); pending.clear();
    list = list.filter(function (n) { return n.isConnected && !list.some(function (o) { return o !== n && o.contains(n); }); });
    list.forEach(function (n) { if (n.querySelectorAll) { revertEl(n); n.querySelectorAll('*').forEach(revertEl); } walk(n, parentL(n)); }); }
  function queue(n) { if (n && n.nodeType === 1) { pending.add(n); if (!raf) raf = requestAnimationFrame(flush); } }
  var hovered = [];
  function hoverIn(e) {
    if (!on) return; var t = e.target, out = [];
    for (var el = t, i = 0; el && el !== document.body && i < 5; el = el.parentElement, i++) if (el.nodeType === 1 && !skipEl(el) && (saved.has(el) || el.matches('a,button,[role=button],.card,[class*=chip],[class*=btn]'))) out.push(el);
    hovered.forEach(function (el) { if (out.indexOf(el) < 0) { revertEl(el); fix(el, parentL(el)); } });
    out.forEach(function (el) { if (hovered.indexOf(el) < 0) { revertEl(el); fix(el, parentL(el)); } });
    hovered = out;
    clearTimeout(hoverIn.t); hoverIn.t = setTimeout(function () { hovered.forEach(function (el) { revertEl(el); fix(el, parentL(el)); }); }, 320);   // again after hover transitions finish
  }
  function start() {
    if (on || !document.body) return; on = true;
    walk(document.body, 0.07);
    root.classList.remove('kpc-th-wait');
    document.addEventListener('pointerover', hoverIn, true);
    mo = new MutationObserver(function (ms) { ms.forEach(function (m) {
      if (m.type === 'childList') m.addedNodes.forEach(queue);
      else if (m.type === 'attributes' && m.target.nodeType === 1 && !(m.attributeName === 'style' && saved.has(m.target))) queue(m.target);
    }); });
    mo.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'aria-pressed', 'aria-selected', 'aria-current', 'open', 'hidden', 'data-state'] });
  }
  function stop() { if (!on) return; on = false; if (mo) mo.disconnect(); mo = null; document.removeEventListener('pointerover', hoverIn, true); hovered = []; Array.from(touched).forEach(revertEl); }
  function apply() {
    var d = !noDark && wantDark();
    if (d) { root.setAttribute('data-theme', 'dark'); if (document.readyState !== 'loading') start(); }
    else { root.removeAttribute('data-theme'); root.classList.remove('kpc-th-wait'); stop(); }
    var b = document.querySelector('.kpc-theme-btn'); if (b) { var p = pref(); b.textContent = p === 'dark' ? '🌙' : p === 'light' ? '☀️' : '🌗';
      b.title = 'Colours: ' + (p === 'auto' ? 'automatic (follows your device)' : p) + '. Tap to change.'; b.setAttribute('aria-label', b.title); }
  }
  function addButton() {
    var host = document.querySelector('.site-nav .nav-inner') || document.querySelector('header .nav-inner');
    if (!host || host.querySelector('.kpc-theme-btn')) return;
    var b = document.createElement('button'); b.type = 'button'; b.className = 'kpc-theme-btn';
    b.addEventListener('click', function () { var p = pref(), n = p === 'auto' ? (wantDark() ? 'light' : 'dark') : p === 'dark' ? 'light' : 'auto';
      try { localStorage.setItem(KEY, n); } catch (e) {} stop(); apply(); });
    var nav = host.querySelector('.nav-links'); if (nav && nav.nextSibling) host.insertBefore(b, nav.nextSibling); else host.appendChild(b);
  }
  if (mq && mq.addEventListener) mq.addEventListener('change', function () { if (pref() === 'auto') { stop(); apply(); } });
  window.addEventListener('storage', function (e) { if (e.key === KEY) { stop(); apply(); } });
  window.addEventListener('beforeprint', function () { if (on) { stop(); root.removeAttribute('data-theme'); window.__kpcThemeWasDark = true; } });
  window.addEventListener('afterprint', function () { if (window.__kpcThemeWasDark) { window.__kpcThemeWasDark = false; apply(); } });
  function ready() { addButton(); apply(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready); else ready();
  window.KPCTheme = { refresh: function () { stop(); apply(); }, set: function (v) { try { localStorage.setItem(KEY, v); } catch (e) {} stop(); apply(); }, get: pref };
})();

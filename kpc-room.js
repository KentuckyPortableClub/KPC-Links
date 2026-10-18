/* KPC Beta Test Room (Brandon Oct 18 2026: 'build me beta test room with no way out with hunters lounge vip').
   Loaded in <head> of kpc-beta-room.html, kpc-beta-need.html and kpc-beta-cat.html (built by .claude/build/hunt/build.sh).
   - Hides the site menu, search, member button and footer: the room is all a tester sees.
   - Links to the VIP Lounge pages are turned into the room's own pages; every other link to this website is blocked
     with a short note. Links to other websites (POTA, QRZ, SOTA…) still open, always in a new tab.
   - window.KPCRoom.map(name) gives the room page for a Lounge page name (kpc-hunt.js uses it for its own jumps). */
(function () {
  var MAP = { 'kpc-hunt.html': 'kpc-beta-room.html', 'kpc-hunters.html': 'kpc-beta-room.html', 'kpc-hunt-need.html': 'kpc-beta-need.html', 'kpc-hunt-cat.html': 'kpc-beta-cat.html' };
  var ROOM = { 'kpc-beta-room.html': 1, 'kpc-beta-need.html': 1, 'kpc-beta-cat.html': 1 };
  var file = function (u) { return (u.pathname.split('/').pop() || 'index.html'); };
  var mapName = function (n) { var m = String(n || '').match(/^([^?#]*)(.*)$/); return (MAP[m[1]] || m[1]) + m[2]; };
  window.KPCRoom = { map: mapName };
  var de = document.documentElement; de.classList.add('kpc-room');
  var st = document.createElement('style');
  st.textContent = 'html.kpc-room header.site-nav .nav-links,html.kpc-room header.site-nav .menu-toggle,html.kpc-room header.site-nav .nav-toggle,html.kpc-room header.site-nav [class*="search"],' +
    'html.kpc-room header.site-nav .kg-btn,html.kpc-room header.site-nav [data-kg],html.kpc-room footer,html.kpc-room .site-footer,html.kpc-room .hl-ptabs a[href*="top50"],html.kpc-room .kpc-warn a{display:none!important}' +
    'html.kpc-room header.site-nav a.brand,html.kpc-room header.site-nav .brand a{pointer-events:none;cursor:default}' +
    '#kpcRoomBar{position:relative;z-index:5;text-align:center;padding:6px 10px;background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;font:900 12px Arial,sans-serif;letter-spacing:1.5px}' +
    '#kpcRoomNote{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:3000;max-width:calc(100% - 32px);padding:10px 16px;border-radius:12px;background:#140d06;border:1px solid rgba(240,201,107,.7);color:#f3e6c8;font:700 14px/1.4 Arial,sans-serif;box-shadow:0 6px 24px #000a}';
  (document.head || de).appendChild(st);
  var note = function (t) { var n = document.getElementById('kpcRoomNote'); if (!n) { n = document.createElement('div'); n.id = 'kpcRoomNote'; n.setAttribute('data-keep-light', ''); document.body.appendChild(n); }
    n.textContent = t; n.hidden = false; clearTimeout(note.t); note.t = setTimeout(function () { n.hidden = true; }, 3500); };
  /* fix links as they appear (Lounge pages → room pages; outside links → new tab) */
  var fix = function (root) { (root.querySelectorAll ? root : document).querySelectorAll('a[href]').forEach(function (a) {
    var h = a.getAttribute('href'); if (!h || /^(#|javascript:|mailto:|sms:|tel:)/i.test(h)) return;
    var u; try { u = new URL(h, location.href); } catch (e) { return; }
    if (u.origin === location.origin) { var f = file(u); if (MAP[f]) a.setAttribute('href', MAP[f] + u.search + u.hash); }
    else { a.target = '_blank'; a.rel = 'noopener'; } }); };
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]'); if (!a) return;
    var h = a.getAttribute('href'); if (!h || /^(#|javascript:|mailto:|sms:|tel:)/i.test(h)) return;
    var u; try { u = new URL(h, location.href); } catch (x) { return; }
    if (u.origin !== location.origin) { a.target = '_blank'; a.rel = 'noopener'; return; }
    var f = file(u); if (MAP[f]) { e.preventDefault(); location.href = MAP[f] + u.search + u.hash; return; }
    if (ROOM[f]) return;
    e.preventDefault(); e.stopPropagation(); note('🧪 That page is outside the beta test room.');
  }, true);
  var start = function () {
    var bar = document.createElement('div'); bar.id = 'kpcRoomBar'; bar.setAttribute('data-keep-light', ''); bar.textContent = '🧪 KPC BETA TEST ROOM · VIP HUNTERS LOUNGE';
    document.body.insertBefore(bar, document.body.firstChild);
    fix(document); new MutationObserver(function (ms) { ms.forEach(function (m) { m.addedNodes.forEach(function (n) { if (n.nodeType === 1) fix(n.matches && n.matches('a') ? n.parentNode || n : n); }); }); })
      .observe(document.body, { childList: true, subtree: true });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();

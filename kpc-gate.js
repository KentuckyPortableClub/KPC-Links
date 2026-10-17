/* KPC members gate (Brandon Oct 17 2026: 'I am not ready to roll all this out… hidden behind the member password… home page, campout,
   events, about, contact accessible to public').
   - PUBLIC below = the pages anyone can open. EVERY other page is members only: it shows the sign-in door until the member password
     is typed once on that device (localStorage kpcMember). A new page is members only by itself; to make a page public, add its file
     name to PUBLIC (one line).
   - On public pages, guests never see links to members-only pages (menu items, cards, buttons, search results are hidden); SWAP sends
     guests to the public version instead (Parks → Kentucky Parks, the map tools → Kentucky Park Control).
   - Only the SHA-256 of 'kpc-member:' + the lowercase password is here, never the password. Client-side only: it keeps the public
     out, it is not real security (the files are in a public GitHub repo).
   - The PDF printer (Playwright on GitHub Actions) passes through so the guide PDFs keep printing. */
(function () {
  var MH = '2925a56a5048f6d5dabbe552f8abb71e7c8b4dfc8b42b29cd76f9083c226a540', KEY = 'kpcMember';
  var PUBLIC = ['index.html', 'campout.html', 'events.html', 'news.html', 'photos.html', 'kpc-guestbook.html', 'join.html', 'about.html',
    'contact.html', 'contact-card.html', 'kpc-privacy.html', 'kentucky-parks.html', 'kpc-park-control.html', 'kpc-guide-pota.html',
    'kpc-guide-wwff.html', 'kpc-guide-sota.html', 'kpc-park-notes.html', 'kpc-park-notes-us.html', 'kpc-campgrounds.html',
    'kpc-community.html', 'kpc-spots.html', '404.html'];
  var SWAP = { 'parks.html': 'kentucky-parks.html', 'finder.html': 'kpc-park-control.html', 'kpc-planner.html': 'kpc-park-control.html',
    'kpc-planner-us.html': 'kpc-park-control.html', 'kpc-map-room.html': 'kpc-park-control.html', 'kpc-live.html': 'kpc-spots.html' };
  var LABEL = { 'kpc-map-room.html': 'Kentucky Park Control' }; /* menu wording for guests when the target is swapped */
  var de = document.documentElement, page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  if (!/\.html?$/.test(page)) page = 'index.html';
  var ok = false; try { ok = localStorage.getItem(KEY) === MH; } catch (e) {}
  if (navigator.webdriver) ok = true; /* the guide PDF printer */
  var isPub = PUBLIC.indexOf(page) >= 0;
  window.KPCGate = { member: function () { return ok; }, isPublic: function (f) { return PUBLIC.indexOf(String(f).toLowerCase()) >= 0; }, PUBLIC: PUBLIC };
  window.kpcLogout = function () { try { localStorage.removeItem(KEY); } catch (e) {} location.href = 'index.html'; };
  var css = 'html.kpc-door body>*:not(#kpcDoor){visibility:hidden!important}html.kpc-door{overflow:hidden}' +
    '#kpcDoor{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:20px;background:radial-gradient(circle at 50% 30%,rgba(213,166,58,.18),transparent 60%),#070707;font-family:Arial,Helvetica,sans-serif;visibility:visible!important;overflow:auto}' +
    '#kpcDoor .box{width:min(430px,100%);padding:30px 26px;background:rgba(20,13,6,.96);border:1px solid rgba(240,201,107,.6);border-radius:18px;box-shadow:0 0 40px rgba(240,201,107,.22);color:#f3e6c8;text-align:center}' +
    '#kpcDoor img{width:92px;height:92px;border-radius:50%;object-fit:contain;filter:drop-shadow(0 0 14px rgba(240,201,107,.45))}' +
    '#kpcDoor .k{margin-top:12px;color:#f0c96b;font-size:11px;font-weight:900;letter-spacing:4px}#kpcDoor h2{margin:8px 0 6px;font:700 30px/1.1 Georgia,serif;color:#fff}' +
    '#kpcDoor p{margin:0 0 16px;color:#e2d2ae;font-size:14.5px;line-height:1.45}#kpcDoor input{width:100%;box-sizing:border-box;min-height:50px;padding:10px 14px;border:1px solid rgba(240,201,107,.6);border-radius:10px;background:#0d0904;color:#fff;font:700 18px monospace;text-align:center;letter-spacing:2px}' +
    '#kpcDoor button{width:100%;margin-top:12px;min-height:50px;border:0;border-radius:999px;background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;font:900 15px Arial;letter-spacing:1px;cursor:pointer}' +
    '#kpcDoor .err{min-height:20px;margin-top:10px;color:#ff9b8a;font-size:13px;font-weight:700}#kpcDoor .links{display:flex;justify-content:space-between;gap:10px;margin-top:10px;flex-wrap:wrap}#kpcDoor a{color:#f0c96b;font-size:13.5px;font-weight:700}' +
    '#kpcDoor .x{position:absolute;top:14px;right:16px;width:auto;min-height:0;margin:0;padding:6px 12px;background:#2a2310;color:#f6d58a;border:1px solid rgba(240,201,107,.5)}' +
    '[data-kpc-hide]{display:none!important}' +
    '.kpc-mem-btn{display:inline-flex!important;align-items:center;gap:5px;padding:6px 12px!important;border:1px solid rgba(240,201,107,.65)!important;border-radius:999px!important;color:#f6d58a!important;font-weight:900!important;font-size:12.5px!important;letter-spacing:.6px;white-space:nowrap;text-decoration:none!important}' +
    '.kpc-mem-btn.on{background:rgba(240,201,107,.12)}@media(max-width:760px){.kpc-mem-btn{justify-content:center;margin:8px 0}}';
  var st = document.createElement('style'); st.textContent = css; (document.head || de).appendChild(st);
  async function sha(t) { var b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)); return Array.prototype.map.call(new Uint8Array(b), function (x) { return x.toString(16).padStart(2, '0'); }).join(''); }
  function door(closable) {
    if (document.getElementById('kpcDoor')) return; de.classList.add('kpc-door');
    var d = document.createElement('div'); d.id = 'kpcDoor'; d.setAttribute('data-keep-light', ''); d.setAttribute('role', 'dialog'); d.setAttribute('aria-label', 'Members sign in');
    d.innerHTML = '<form class="box">' + (closable ? '<button type="button" class="x" aria-label="Close">✕</button>' : '') + '<img src="KPC-logo.png" alt=""><div class="k">KENTUCKY PORTABLE CLUB</div><h2>Members Only</h2>' +
      '<p>' + (closable ? 'Club members: type the member password to open every page and tool on this device.' : 'This part of the KPC website is for club members. Type the member password to come in. You only need it once on this device.') + '</p>' +
      '<input type="password" autocomplete="current-password" placeholder="MEMBER PASSWORD" aria-label="Member password"><button type="submit">🔓 COME IN</button><div class="err" role="alert"></div>' +
      '<div class="links"><a href="join.html">Not a member yet? Join KPC ›</a><a href="index.html">← KPC home</a></div></form>';
    document.body.appendChild(d); var f = d.querySelector('form'), i = d.querySelector('input'); setTimeout(function () { i.focus(); }, 30);
    var x = d.querySelector('.x'); if (x) x.onclick = function () { d.remove(); de.classList.remove('kpc-door'); };
    f.onsubmit = function (e) { e.preventDefault(); sha('kpc-member:' + i.value.trim().toLowerCase()).then(function (h) {
      if (h === MH) { try { localStorage.setItem(KEY, MH); } catch (x2) {} location.reload(); }
      else { d.querySelector('.err').textContent = 'That password is not right. Try again.'; i.select(); } }); };
  }
  /* guests: hide links to members-only pages, send swapped ones to the public version */
  var CARD = '.card,.link-card,.feature-card,.kb-card,.tool-card,.rm-card,.nw-card,.cw-card,.kd-card,article,li';
  function fileOf(a) { var h = a.getAttribute('href'); if (!h || /^(#|mailto:|tel:|sms:|javascript:)/i.test(h)) return null;
    var u; try { u = new URL(h, location.href); } catch (e) { return null; } if (u.origin !== location.origin) return null;
    var f = (u.pathname.split('/').pop() || 'index.html').toLowerCase(); if (!f) f = 'index.html'; if (!/\.html?$/.test(f)) return null; return { f: f, u: u }; }
  function locked(a) { var r = fileOf(a); return !!r && PUBLIC.indexOf(r.f) < 0 && !SWAP[r.f]; }
  function fix(root) {
    var A = (root.querySelectorAll ? root.querySelectorAll('a[href]') : []); if (root.tagName === 'A') A = [root];
    for (var k = 0; k < A.length; k++) { var a = A[k], r = fileOf(a); if (!r) continue;
      if (SWAP[r.f]) { var ref = r.u.searchParams.get('ref') || r.u.searchParams.get('q') || (r.u.hash ? r.u.hash.slice(1) : ''); a.setAttribute('href', SWAP[r.f] + (SWAP[r.f] === 'kpc-park-control.html' && ref ? '?ref=' + encodeURIComponent(ref) : ''));
        if (LABEL[r.f] && a.closest('nav,.nav-dropdown')) { var ic = a.querySelector('.ni'); a.textContent = ''; if (ic) a.appendChild(ic); a.appendChild(document.createTextNode(LABEL[r.f])); } continue; }
      if (PUBLIC.indexOf(r.f) >= 0) continue;
      var c = a.matches(CARD) ? null : a.closest(CARD);
      if (c && !c.closest('nav,.nav-dropdown,header.site-nav')) { var all = c.querySelectorAll('a[href]'), any = false; for (var j = 0; j < all.length; j++) if (!locked(all[j]) && fileOf(all[j]) !== null) any = true; else if (fileOf(all[j]) === null && !/^#/.test(all[j].getAttribute('href') || '')) any = true;
        if (!any) { c.setAttribute('data-kpc-hide', ''); continue; } }
      a.setAttribute('data-kpc-hide', ''); }
    document.querySelectorAll('.nav-drop-section').forEach(function (s) { if (!s.querySelector('a[href]:not([data-kpc-hide])')) s.setAttribute('data-kpc-hide', ''); });
    document.querySelectorAll('[class*="grid"]').forEach(function (g) { if (g.children.length && !g.querySelector(':scope>*:not([data-kpc-hide])')) { var s = g.closest('section'); if (s && !s.classList.contains('hero') && !s.classList.contains('kb-hero')) { s.setAttribute('data-kpc-hide', ''); if (s.id) document.querySelectorAll('a[href="#' + s.id + '"]').forEach(function (j) { j.setAttribute('data-kpc-hide', ''); }); } } });
  }
  function memBtn() { var n = document.getElementById('kpc-main-nav') || document.querySelector('header.site-nav nav'); if (!n || n.querySelector('.kpc-mem-btn')) return;
    var b = document.createElement('a'); b.className = 'kpc-mem-btn' + (ok ? ' on' : ''); b.href = '#members';
    b.textContent = ok ? '✓ MEMBER' : '🔒 MEMBERS'; b.title = ok ? 'Signed in as a club member. Tap to sign out on this device.' : 'Club members: sign in';
    b.onclick = function (e) { e.preventDefault(); if (ok) { if (confirm('Sign out of the members area on this device?')) window.kpcLogout(); } else door(true); };
    var more = n.querySelector('.nav-more'); if (more) n.insertBefore(b, more); else n.appendChild(b); }
  function ready(fn) { if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn); else fn(); }
  if (!isPub && !ok) { de.classList.add('kpc-door'); ready(function () { door(false); }); return; }
  ready(function () {
    memBtn();
    if (ok) return;
    de.classList.add('kpc-guest'); fix(document);
    var q = [], t = 0; new MutationObserver(function (m) { m.forEach(function (x) { x.addedNodes.forEach(function (n) { if (n.nodeType === 1) q.push(n); }); }); if (!t) t = requestAnimationFrame(function () { t = 0; var Q = q; q = []; Q.forEach(function (n) { if (n.isConnected) fix(n); }); }); }).observe(document.body, { childList: true, subtree: true });
    if (location.hash === '#members') door(true);
  });
})();

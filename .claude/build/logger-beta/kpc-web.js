/* KPC Logger beta on the website (chat 3, Oct 26; Brandon: 'web logger lets make it more like the app it is beta').
   The page is the app's own screens (copied by .claude/build/logger-beta/sync.sh). This file adds the website bits only:
   a BETA tag + a way back to the website, the house info line, the members door's links (the page sits one folder down),
   and a note on what only the installed app can do. Nothing here changes how the logger works. */
(function () {
  'use strict';
  window.KPC_WEB = true;
  function $(s) { return document.querySelector(s); }
  var ttl = $('#ttl'); if (ttl && !$('.kw-beta')) ttl.insertAdjacentHTML('afterend', '<span class="kw-beta">BETA</span>');
  var hd = $('header.top'), lk = $('#look');
  if (hd && lk && !$('.kw-site')) lk.insertAdjacentHTML('beforebegin', '<a class="kw-site" href="../index.html" title="Back to the KPC website">← <span>KPC SITE</span></a>');
  var st = document.getElementById('scrStation') || $('section.scr[id*="Sta"]');
  var about = $('section.card[data-grp^="alerts help"]');
  if (about && !$('.kw-web')) about.insertAdjacentHTML('beforeend', '<p class="kw-web">This is the website copy of the KPC app\'s logger (beta). It runs in Chrome or Edge on a computer, or Chrome on Android, and talks to your radio over USB. Only the installed app can be a remote base station. Your log stays in this browser: save a KPC log file or ADIF now and then. The old logger is still here: <a href="../kpc-logger.html?old=1">old KPC Logger ›</a></p>');
  if (st && !$('.kw-info')) st.insertAdjacentHTML('beforeend', '<p class="kw-info">ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go. <a href="../kpc-about-info.html">About our information</a></p>');
  [].forEach.call(document.querySelectorAll('.hint'), function (p) { if (/share the log with each other on their own/.test(p.textContent)) p.textContent = 'Only needed for a new computer or phone, or a safety copy.'; });

  /* ---- RADIO PORT: easy pick + names (Oct 26, Brandon: 'same fixes on the web logger … port easy pick and rename').
     A web page only sees ports picked once in Chrome's box, so: Chrome's box lists only radio-type USB chips (SHOW EVERY PORT = all),
     a gold PICK THE RADIO'S PORT button in STATION → Radio control (lit when CONNECT found nothing), and ✏ NAME THIS PORT.
     Names are shared with the Hunters Lounge (localStorage kpcCatPorts, key = USB maker:product:interface#n) and shown in the
     USB PORT list (the app's portLabel reads port.kpcName). */
  var SER = navigator.serial, RCHIPS = [0x10C4, 0x0403, 0x067B, 0x1A86, 0x0483, 0x2E8A, 0x2341, 0x239A, 0x1FC9, 0x04D8, 0x0C26, 0x0B28], ALL = false;
  function PK() { try { return JSON.parse(localStorage.getItem('kpcCatPorts') || '{}') || {}; } catch (e) { return {}; } }
  function keysOf(ps) { var seen = {}; return ps.map(function (p) { var f = (p.getInfo && p.getInfo()) || {}, b = [f.usbVendorId, f.usbProductId, f.usbInterface].join(':'); seen[b] = (seen[b] || 0) + 1; return b + '#' + seen[b]; }); }
  if (SER && SER.getPorts && !SER.__kpc) {
    var gp = SER.getPorts.bind(SER), rp = SER.requestPort.bind(SER);
    SER.getPorts = function () { return gp().then(function (ps) { var A = PK(), ks = keysOf(ps); ps.forEach(function (p, i) { var e = A[ks[i]]; if (e && e.name) p.kpcName = e.name; else delete p.kpcName; p.__kpcKey = ks[i]; }); return ps; }); };
    SER.requestPort = function (o) {
      o = o || {}; if (ALL || o.filters) return rp(o);
      var f = RCHIPS.map(function (v) { return { usbVendorId: v }; }).concat([{ bluetoothServiceClassId: '00001101-0000-1000-8000-00805f9b34fb' }]);
      return rp(Object.assign({}, o, { filters: f })).catch(function (e) { if (e && e.name === 'TypeError') return rp(o); throw e; });
    };
    SER.__kpc = true;
  }
  var card = $('section.card[data-grp^="radio "]'), sel = document.getElementById('stPort'), stT = document.getElementById('stCatT');
  if (card && sel && SER && !document.getElementById('kwPort')) {
    var row = document.createElement('div'); row.id = 'kwPort'; row.className = 'row';
    row.innerHTML = '<button type="button" class="b" id="kwPick">🔌 PICK THE RADIO\'S PORT</button><button type="button" class="b" id="kwAll">SHOW EVERY PORT</button><button type="button" class="b" id="kwName">✏ NAME THIS PORT</button>' +
      '<div id="kwNameW" class="kw-name" hidden><input id="kwNameI" maxlength="40" placeholder="Name, like FT-710 or IC-705" autocomplete="off"><button type="button" class="b gold" id="kwNameS">SAVE</button></div>' +
      '<p class="hint kw-ph">A web page can only use a port you have picked once in Chrome\'s box (Yaesu radios show two: pick the <b>Enhanced</b> one). After that, CONNECT finds the port your radio answers on by itself. Name each port when you run more than one radio.</p>';
    (stT || sel.closest('.grid2')).insertAdjacentElement(stT ? 'beforebegin' : 'afterend', row);
    var fill = function () { return KPCCat.ports().then(function (ps) { var cur = sel.value; sel.innerHTML = ps.length ? ps.map(function (p) { return '<option value="' + p.i + '"' + (p.now ? ' selected' : '') + '>' + String(p.label).replace(/[<>&"]/g, '') + '</option>'; }).join('') : '<option value="">(no USB port seen)</option>'; if (!ps.some(function (p) { return p.now; }) && cur !== '' && sel.querySelector('option[value="' + cur + '"]')) sel.value = cur; }).catch(function () {}); };
    var lit = function (on) { var b = document.getElementById('kwPick'); if (b) b.classList.toggle('gold', !!on); };
    var pick = function (all) { ALL = !!all; KPCCat.pickNew().then(function (ok) { ALL = false; lit(!ok); fill(); }); };
    document.getElementById('kwPick').onclick = function () { pick(false); };
    document.getElementById('kwAll').onclick = function () { pick(true); };
    document.getElementById('kwName').onclick = function () {
      var w = document.getElementById('kwNameW'); w.hidden = !w.hidden; if (w.hidden) return;
      SER.getPorts().then(function (ps) { var p = ps[+sel.value || 0]; document.getElementById('kwNameI').value = (p && p.kpcName) || ''; document.getElementById('kwNameI').focus(); });
    };
    document.getElementById('kwNameS').onclick = function () {
      SER.getPorts().then(function (ps) { var i = +sel.value || 0, p = ps[i]; if (!p) { document.getElementById('kwNameW').hidden = true; return; }
        var A = PK(), k = p.__kpcKey, nm = document.getElementById('kwNameI').value.trim().slice(0, 40); A[k] = Object.assign({}, A[k] || {}, { name: nm }); if (!nm) delete A[k].name;
        try { localStorage.setItem('kpcCatPorts', JSON.stringify(A)); } catch (e) {}
        document.getElementById('kwNameW').hidden = true; return fill(); });
    };
    if (window.KPCCat && KPCCat.onStatus) KPCCat.onStatus(function (t, ok) { if (ok === true) lit(false); else if (/No port answered|No USB port found|No port picked|Could not open/i.test(String(t || ''))) lit(true); });
  }
  /* the members door is drawn by ../kpc-gate.js with links for the site's top folder */
  function fix(root) { [].forEach.call((root || document).querySelectorAll('#kpcDoor a[href], #kpcDoor img[src]'), function (a) { var at = a.tagName === 'IMG' ? 'src' : 'href', h = a.getAttribute(at); if (h && !/^(https?:|data:|#|\.\.\/|\/|mailto:)/.test(h)) a.setAttribute(at, '../' + h); }); }
  fix(); new MutationObserver(function () { fix(); }).observe(document.documentElement, { childList: true, subtree: true });
})();

/* VIP Hunters Lounge lock (Brandon Oct 17: 'add VIP before the name… put a password on it').
   Used on kpc-hunt.html, kpc-hunt-need.html, kpc-hunt-cat.html and kpc-top50.html. Load it in <head> so nothing shows first.
   Only a slow hash (PBKDF2 over the SHA-256 of 'kpc-vip:' + password, Nov 11) is here, never the password. One unlock opens all four pages on this device
   (localStorage kpcVipOK). Client-side only: it keeps casual visitors out, it is not real security.
   window.KPCVIP.ready = a promise that resolves once unlocked (the Lounge waits for it before loading spots).
   BETA mode (Brandon Oct 17: 'lock the public hunters lounge till I beta it'): <script src="kpc-vip.js" data-lock="beta"> on kpc-hunters.html
   uses its own password (SHA-256 of 'kpc-beta:' + password) and localStorage kpcBetaOK. A VIP unlock also opens the beta page. */
(function () {
  var LOCK = document.currentScript && document.currentScript.getAttribute('data-lock'), BETA = LOCK === 'beta', ROOM = LOCK === 'room';
  /* ROOM (Brandon Oct 18: 'beta test room with no way out with hunters lounge vip'): kpc-beta-room / -need / -cat pages, own password
     (SHA-256 of 'kpc-room:' + password, localStorage kpcRoomOK); a VIP or member unlock opens it too. */
  /* Nov 11 2026 (owner: soft lock, slower hash): each lock value is PBKDF2-SHA256 (200,000 rounds, its own salt) of the hex SHA-256 of
     prefix + password that this file used before, so the fast hashes are no longer here. It is still a soft lock: it keeps honest
     people out; private data must never be put in this public repo. */
  var VIPH = 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab', MEMH = 'ed00a12021b4460be189b4120e93d5f740408d2f769e108d332dcc4aa528ca61'; /* Oct 17: one member password for every lock; MEMH hardened to PBKDF2-SHA256 200k rounds Oct 27 (matches kpc-gate.js) */
  var HASH = ROOM ? '45fefe8e34282a0ca0864229046044d4e47988cb79b054a2cdadf4c4213574b3' : BETA ? 'd5a9320d7439f2c39d1edee093a44a78b395d6ac854a4f4f35e20cfd137c0ac6' : VIPH, KEY = ROOM ? 'kpcRoomOK' : BETA ? 'kpcBetaOK' : 'kpcVipOK', SALT = ROOM ? 'kpc-room:' : BETA ? 'kpc-beta:' : 'kpc-vip:';
  var PS = ROOM ? 'kpc-room-pbkdf2-salt-v1' : BETA ? 'kpc-beta-pbkdf2-salt-v1' : 'kpc-vip-pbkdf2-salt-v1', VPS = 'kpc-vip-pbkdf2-salt-v1';
  var enc = function (s) { return new TextEncoder().encode(s); }, hex = function (b) { return Array.prototype.map.call(new Uint8Array(b), function (x) { return x.toString(16).padStart(2, '0'); }).join(''); };
  var slow = function (h, salt) { return crypto.subtle.importKey('raw', enc(h), { name: 'PBKDF2' }, false, ['deriveBits']).then(function (k) { return crypto.subtle.deriveBits({ name: 'PBKDF2', salt: enc(salt), iterations: 200000, hash: 'SHA-256' }, k, 256); }).then(hex); };
  var get = function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } };
  var ok = false; try { ok = localStorage.getItem(KEY) === HASH || ((BETA || ROOM) && localStorage.getItem('kpcVipOK') === VIPH) || localStorage.getItem('kpcMember') === MEMH; } catch (e) {}
  var done; var ready = new Promise(function (r) { done = r; });
  window.KPCVIP = { ready: ready, ok: function () { return ok; } };
  if (ok) { done(); return; }
  var de = document.documentElement; de.classList.add('vip-lock');
  var st = document.createElement('style');
  st.textContent = 'html.vip-lock main,html.vip-lock .site-footer,html.vip-lock footer{display:none!important}' +
    '#vipLock{max-width:440px;margin:40px auto 60px;width:calc(100% - 32px);box-sizing:border-box;padding:26px 22px;border-radius:18px;background:rgba(20,13,6,.94);border:1px solid rgba(240,201,107,.6);box-shadow:0 0 34px rgba(240,201,107,.25);color:#f3e6c8;font:15px/1.5 Arial,sans-serif;text-align:center}' +
    '#vipLock .v{display:inline-block;font:900 12px Arial;letter-spacing:2px;padding:5px 12px;border-radius:999px;background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05}' +
    '#vipLock h1{font:900 26px Georgia,serif;margin:12px 0 6px;color:#fff}#vipLock p{margin:6px 0 14px;color:#e2d2ae}' +
    '#vipLock input{width:100%;box-sizing:border-box;padding:13px;border-radius:10px;border:1px solid rgba(240,201,107,.6);background:#0d0904;color:#fff;font:700 20px monospace;text-align:center;letter-spacing:4px}' +
    '#vipLock button{margin-top:12px;width:100%;padding:13px;border-radius:999px;border:0;background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;font:900 15px Arial;letter-spacing:1px;cursor:pointer}' +
    '#vipLock .bad{color:#ff9b8a;min-height:20px;margin-top:8px;font-weight:700}#vipLock a{color:#f0c96b}';
  (document.head || de).appendChild(st);
  var sha = function (t) { return crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)).then(function (b) { return Array.prototype.map.call(new Uint8Array(b), function (x) { return x.toString(16).padStart(2, '0'); }).join(''); }); };
  function show() {
    var box = document.createElement('div'); box.id = 'vipLock'; box.setAttribute('data-keep-light', '');
    box.innerHTML = ROOM ? '<span class="v">🧪 BETA TEST ROOM</span><h1>VIP Hunters Lounge</h1><p>Welcome, tester! Type the beta room password to come in. You only need it once on this device.</p>' +
      '<form><input type="password" autocomplete="off" placeholder="PASSWORD" aria-label="Password"><button type="submit">🔓 COME IN</button><div class="bad" aria-live="polite"></div></form>' : (BETA ? '<span class="v">🧪 BETA</span><h1>Hunters Lounge</h1><p>The Hunters Lounge is being tested and opens to everyone soon. Testers: type the beta password to come in. You only need it once on this device.</p>'
      : '<span class="v">⭐ VIP</span><h1>VIP Hunters Lounge</h1><p>This part of the Lounge is for KPC members. Type the VIP password to come in. You only need it once on this device.</p>') +
      '<form><input type="password" ' + (BETA ? '' : 'inputmode="numeric" ') + 'autocomplete="off" placeholder="PASSWORD" aria-label="Password"><button type="submit">🔓 COME IN</button><div class="bad" aria-live="polite"></div></form>' +
      (BETA ? '<p style="margin-top:16px;font-size:13px">Want live spots now? <a href="kpc-live.html">Happening Now</a> is open to everyone.</p>'
      : '<p style="margin-top:16px;font-size:13px">The free Hunters Lounge is being tested and opens to everyone soon.</p>');
    var hdr = document.querySelector('header.site-nav'); if (hdr && hdr.parentNode) hdr.parentNode.insertBefore(box, hdr.nextSibling); else document.body.insertBefore(box, document.body.firstChild);
    var f = box.querySelector('form'), inp = box.querySelector('input'), bad = box.querySelector('.bad');
    f.onsubmit = function (e) { e.preventDefault(); sha(SALT + inp.value.trim().toLowerCase()).then(function (h) { return slow(h, PS); }).then(function (h) {
      if (h === HASH) { try { localStorage.setItem(KEY, HASH); } catch (x) {} ok = true; box.remove(); de.classList.remove('vip-lock'); done(); try { dispatchEvent(new Event('resize')); } catch (x) {} }
      else { bad.textContent = 'That is not it. Try again.'; inp.select(); }
    }); };
    setTimeout(function () { inp.focus(); }, 50);
  }
  /* a device unlocked before Nov 11 remembers the old fast value: stretch it once here; if it matches, keep the new value instead */
  function migrate() {
    var L = [[KEY, HASH, PS]]; if (BETA || ROOM) L.push(['kpcVipOK', VIPH, VPS]);
    return L.reduce(function (p, x) { return p.then(function (hit) { var v = get(x[0]); if (hit || !/^[0-9a-f]{64}$/.test(v || '') || v === x[1]) return hit;
      return slow(v, x[2]).then(function (s) { if (s !== x[1]) return false; try { localStorage.setItem(x[0], x[1]); } catch (e) {} return true; }); }); }, Promise.resolve(false)).catch(function () { return false; });
  }
  migrate().then(function (hit) {
    if (hit) { ok = true; de.classList.remove('vip-lock'); done(); return; }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', show); else show();
  });
})();

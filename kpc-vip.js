/* VIP Hunters Lounge lock (Brandon Oct 17: 'add VIP before the name… put a password on it').
   Used on kpc-hunt.html, kpc-hunt-need.html, kpc-hunt-cat.html and kpc-top50.html. Load it in <head> so nothing shows first.
   Only the SHA-256 of 'kpc-vip:' + password is here, never the password. One unlock opens all four pages on this device
   (localStorage kpcVipOK). Client-side only: it keeps casual visitors out, it is not real security.
   window.KPCVIP.ready = a promise that resolves once unlocked (the Lounge waits for it before loading spots). */
(function () {
  var HASH = '1c98fe8c74bed6bc1d39200459508faa9126ea623c8d5062946caebe906a9f9f', KEY = 'kpcVipOK';
  var ok = false; try { ok = localStorage.getItem(KEY) === HASH; } catch (e) {}
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
    box.innerHTML = '<span class="v">⭐ VIP</span><h1>VIP Hunters Lounge</h1><p>This part of the Lounge is for KPC members. Type the VIP password to come in. You only need it once on this device.</p>' +
      '<form><input type="password" inputmode="numeric" autocomplete="off" placeholder="PASSWORD" aria-label="VIP password"><button type="submit">🔓 COME IN</button><div class="bad" aria-live="polite"></div></form>' +
      '<p style="margin-top:16px;font-size:13px">No password? The <a href="kpc-hunters.html">free Hunters Lounge</a> is open to everyone.</p>';
    var hdr = document.querySelector('header.site-nav'); if (hdr && hdr.parentNode) hdr.parentNode.insertBefore(box, hdr.nextSibling); else document.body.insertBefore(box, document.body.firstChild);
    var f = box.querySelector('form'), inp = box.querySelector('input'), bad = box.querySelector('.bad');
    f.onsubmit = function (e) { e.preventDefault(); sha('kpc-vip:' + inp.value.trim().toLowerCase()).then(function (h) {
      if (h === HASH) { try { localStorage.setItem(KEY, HASH); } catch (x) {} ok = true; box.remove(); de.classList.remove('vip-lock'); done(); try { dispatchEvent(new Event('resize')); } catch (x) {} }
      else { bad.textContent = 'That is not it. Try again.'; inp.select(); }
    }); };
    setTimeout(function () { inp.focus(); }, 50);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', show); else show();
})();

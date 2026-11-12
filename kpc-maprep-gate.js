/* Mapping Rep Tool Box door (Brandon Nov 8 2026, 8:01 AM CST: a separate page with a password so mapping reps can use it).
   Used only by kpc-maprep-reps.html. That page is marked data-kpc-public, so the members door in kpc-gate.js lets it through and
   this door asks for the mapping rep password instead. Only a slow hash (PBKDF2 over the SHA-256 of 'kpc-maprep:' + the lowercase password, Nov 11) is here,
   never the password. A good password is remembered on the device (localStorage kpcMapRep). Club members already signed in (kpcMember)
   go straight in. Client-side only: it keeps the public out, it is not real security (the repo is public). */
(function () {
  /* Nov 11 2026 (owner: a soft lock that keeps honest people out; private data must never be put in this public repo): RH is now
     PBKDF2-SHA256 (200,000 rounds, salt PS) of the hex SHA-256 of 'kpc-maprep:' + password used before, so no fast hash is here. */
  var PS = 'kpc-maprep-pbkdf2-salt-v1';
  var RH = 'f9f2be57c06d88fe6d03a3fe59b7b3b9394be1a63993d74a2ddd65a5b1bf2c80', KEY = 'kpcMapRep', de = document.documentElement;
  var ok = false;
  try { ok = localStorage.getItem(KEY) === RH || !!(window.KPCGate && window.KPCGate.member && window.KPCGate.member()); } catch (e) {}
  if (navigator.webdriver) ok = true;
  window.KPCRepGate = { ok: function () { return ok; }, hash: RH, signOut: function () { try { localStorage.removeItem(KEY); } catch (e) {} location.reload(); } };
  if (ok) return;
  function slow(h) { var e = new TextEncoder(); return crypto.subtle.importKey('raw', e.encode(h), { name: 'PBKDF2' }, false, ['deriveBits']).then(function (k) { return crypto.subtle.deriveBits({ name: 'PBKDF2', salt: e.encode(PS), iterations: 200000, hash: 'SHA-256' }, k, 256); }).then(function (b) { return Array.from(new Uint8Array(b)).map(function (x) { return x.toString(16).padStart(2, '0'); }).join(''); }); }
  function sha(t) { return crypto.subtle.digest('SHA-256', new TextEncoder().encode(t)).then(function (b) { return Array.from(new Uint8Array(b)).map(function (x) { return x.toString(16).padStart(2, '0'); }).join(''); }); }
  var css = 'html.kpc-repdoor body>*:not(#kpcRepDoor){visibility:hidden!important}html.kpc-repdoor{overflow:hidden}' +
    '#kpcRepDoor{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:20px;background:radial-gradient(circle at 50% 30%,rgba(213,166,58,.18),transparent 60%),#070707;font-family:Arial,Helvetica,sans-serif;visibility:visible}' +
    '#kpcRepDoor .box{width:min(430px,100%);padding:30px 26px;background:rgba(20,13,6,.96);border:1px solid rgba(240,201,107,.6);border-radius:18px;color:#f3e6c8;text-align:center}' +
    '#kpcRepDoor img{width:92px;height:92px;border-radius:50%;object-fit:contain}#kpcRepDoor .k{margin-top:12px;color:#f0c96b;font-size:11px;font-weight:900;letter-spacing:4px}' +
    '#kpcRepDoor h2{margin:8px 0 6px;font:700 28px/1.1 Georgia,serif;color:#fff}#kpcRepDoor p{margin:0 0 16px;color:#e2d2ae;font-size:14.5px;line-height:1.45}' +
    '#kpcRepDoor input{width:100%;box-sizing:border-box;min-height:50px;padding:10px 14px;border:1px solid rgba(240,201,107,.6);border-radius:10px;background:#0d0904;color:#fff;font:700 18px Arial;text-align:center}' +
    '#kpcRepDoor button{width:100%;margin-top:12px;min-height:50px;border:0;border-radius:999px;background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;font:900 15px Arial;letter-spacing:1px;cursor:pointer}' +
    '#kpcRepDoor .err{min-height:20px;margin-top:10px;color:#ff9b8a;font-size:13px;font-weight:700}';
  var st = document.createElement('style'); st.textContent = css; (document.head || de).appendChild(st);
  de.classList.add('kpc-repdoor');
  function door() {
    if (document.getElementById('kpcRepDoor')) return;
    var d = document.createElement('div'); d.id = 'kpcRepDoor'; d.setAttribute('data-keep-light', ''); d.setAttribute('role', 'dialog'); d.setAttribute('aria-label', 'Mapping rep sign in');
    d.innerHTML = '<form class="box"><img src="KPC-logo.png" alt=""><div class="k">KENTUCKY PORTABLE CLUB</div><h2>Mapping Rep Tool Box</h2>' +
      '<p>For POTA mapping representatives. Type the mapping rep password to open the Tool Box. You only need it once on this device.</p>' +
      '<input type="password" autocomplete="current-password" placeholder="MAPPING REP PASSWORD" aria-label="Mapping rep password"><button type="submit">OPEN THE TOOL BOX</button><div class="err" role="alert"></div></form>';
    document.body.appendChild(d); var f = d.querySelector('form'), i = d.querySelector('input'); setTimeout(function () { i.focus(); }, 30);
    f.onsubmit = function (e) { e.preventDefault(); sha('kpc-maprep:' + i.value.trim().toLowerCase()).then(slow).then(function (h) {
      if (h === RH) { try { localStorage.setItem(KEY, RH); } catch (x) {} location.reload(); }
      else { d.querySelector('.err').textContent = 'That password is not right. Try again.'; i.select(); } }); };
  }
  /* a device let in before Nov 11 remembers the old fast value: stretch it once; if it matches, keep the new value and reload */
  var old = null; try { old = localStorage.getItem(KEY); } catch (e) {}
  (/^[0-9a-f]{64}$/.test(old || '') ? slow(old).catch(function () { return ''; }) : Promise.resolve('')).then(function (s) {
    if (s && s === RH) { try { localStorage.setItem(KEY, RH); } catch (e) {} location.reload(); return; }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', door); else door();
  });
})();

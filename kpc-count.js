/* KPC visitor counter (GoatCounter: no cookies, no personal data; the counts are only visible to the club).
   OFF until CODE is set to the club's GoatCounter code (the "xxx" in xxx.goatcounter.com).
   Your own visits: open any page once with ?nocount=1 on that phone/computer and it stops counting you (?nocount=0 undoes it). */
(function () {
  var CODE = 'kentuckyportableclub';
  try {
    var q = new URLSearchParams(location.search);
    if (q.get('nocount') === '1') localStorage.setItem('kpcNoCount', '1');
    if (q.get('nocount') === '0') localStorage.removeItem('kpcNoCount');
    if (localStorage.getItem('kpcNoCount') === '1') return;
  } catch (e) {}
  if (!CODE || !/github\.io$/.test(location.hostname) || /[?&](print|pdf)=/.test(location.search)) return;
  /* Nov 11 2026 (owner): never on a page where a member types a password. Skipped: members-only pages (the members door), pages
     with the VIP / beta / room lock (kpc-vip.js), the map-rep door (kpc-maprep-gate.js), the old members door (kpc-members.js),
     and an address that opens the sign-in box (#members). Pages without kpc-gate.js are skipped too (this cannot tell). */
  var f = (location.pathname.split('/').pop() || 'index.html').toLowerCase(); if (!/\.html?$/.test(f)) f = 'index.html';
  var G = window.KPCGate, pub = !!G && (G.isPublic(f) || document.documentElement.hasAttribute('data-kpc-public'));
  /* ...and never while the members sign-in box is open (Nov 11: kpc-gate.js draws it as #kpcDoor) */
  if (!pub || location.hash === '#members' || document.getElementById('kpcDoor') || document.documentElement.classList.contains('kpc-door') || document.querySelector('script[src*="kpc-vip.js"],script[src*="kpc-maprep-gate.js"],script[src*="kpc-members.js"]')) return;
  var s = document.createElement('script');
  /* pinned version with an integrity check (GoatCounter's "Use SRI with count.js" help page, count.v4.js) */
  s.async = true; s.src = 'https://gc.zgo.at/count.v4.js'; s.crossOrigin = 'anonymous';
  s.integrity = 'sha384-nRw6qfbWyJha9LhsOtSb2YJDyZdKvvCFh0fJYlkquSFjUxp9FVNugbfy8q1jdxI+';
  s.setAttribute('data-goatcounter', 'https://' + CODE + '.goatcounter.com/count');
  document.head.appendChild(s);
})();

/* KPC visitor counter (GoatCounter: no cookies, no personal data; the counts are only visible to the club).
   OFF until CODE is set to the club's GoatCounter code (the "xxx" in xxx.goatcounter.com).
   Your own visits: open any page once with ?nocount=1 on that phone/computer and it stops counting you (?nocount=0 undoes it). */
(function () {
  var CODE = '';
  try {
    var q = new URLSearchParams(location.search);
    if (q.get('nocount') === '1') localStorage.setItem('kpcNoCount', '1');
    if (q.get('nocount') === '0') localStorage.removeItem('kpcNoCount');
    if (localStorage.getItem('kpcNoCount') === '1') return;
  } catch (e) {}
  if (!CODE || !/github\.io$/.test(location.hostname) || /[?&](print|pdf)=/.test(location.search)) return;
  var s = document.createElement('script');
  s.async = true; s.src = 'https://gc.zgo.at/count.js';
  s.setAttribute('data-goatcounter', 'https://' + CODE + '.goatcounter.com/count');
  document.head.appendChild(s);
})();

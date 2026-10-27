/* Park Notes 'ready to write' (Oct 26, Brandon via HQ: the Activators Lounge's 'Been there? Share a park note.' card opens
   kpc-park-notes.html#write (Kentucky) or kpc-park-notes-us.html#write (other states)). With #write the page puts the park
   search box on screen, focuses it and says what to do next: find the park, then SUBMIT A TIP (our form opens with the number). */
(function () {
  if (location.hash !== '#write') return;
  function go() {
    var q = document.getElementById('pnQ') || document.getElementById('pnuQ'); if (!q) return;
    if (!document.getElementById('pnWrite')) {
      var d = document.createElement('div'); d.id = 'pnWrite'; d.setAttribute('role', 'note');
      d.style.cssText = 'margin:0 0 12px;padding:12px 14px;border-radius:12px;border:2px solid #d5a63a;background:#fff8e6;color:#1c1c1c;font:15px/1.5 Arial,Helvetica,sans-serif';
      d.innerHTML = '<b>📝 Thanks for sharing!</b> Type the park’s name or number below, open it, then tap <b>SUBMIT A TIP</b>. Our short form opens with the park number filled in.' +
        (/park-notes-us/.test(location.pathname) ? ' Kentucky park? <a href="kpc-park-notes.html#write" style="color:#1d5a3a;font-weight:700">Kentucky Park Notes ›</a>' : ' Another state? <a href="kpc-park-notes-us.html#write" style="color:#1d5a3a;font-weight:700">Park Notes for every state ›</a>');
      var host = q.closest('.pn-bar, .pnu-find') || q; host.parentNode.insertBefore(d, host);
    }
    var hd = document.querySelector('header.site-nav'), off = hd ? hd.getBoundingClientRect().height + 12 : 12;
    scrollTo({ top: Math.max(0, document.getElementById('pnWrite').getBoundingClientRect().top + scrollY - off), behavior: 'smooth' });
    try { q.focus({ preventScroll: true }); } catch (e) { q.focus(); }
  }
  if (document.readyState === 'complete') setTimeout(go, 300); else addEventListener('load', function () { setTimeout(go, 300); });
})();

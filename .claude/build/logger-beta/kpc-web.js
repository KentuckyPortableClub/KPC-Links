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
  if (about && !$('.kw-web')) about.insertAdjacentHTML('beforeend', '<p class="kw-web">This is the website copy of the KPC app\'s logger (beta). It runs in Chrome or Edge on a computer, or Chrome on Android, and talks to your radio over USB. Only the installed app can be a remote base station. Your log stays in this browser: save a KPC log file or ADIF now and then. The old logger is still here: <a href="../kpc-logger.html">KPC Logger ›</a></p>');
  if (st && !$('.kw-info')) st.insertAdjacentHTML('beforeend', '<p class="kw-info">ℹ️ Maps and park info are a planning aid, not a guarantee. Always check the official agency map and rules before you go. <a href="../kpc-about-info.html">About our information</a></p>');
  [].forEach.call(document.querySelectorAll('.hint'), function (p) { if (/share the log with each other on their own/.test(p.textContent)) p.textContent = 'Only needed for a new computer or phone, or a safety copy.'; });
  /* the members door is drawn by ../kpc-gate.js with links for the site's top folder */
  function fix(root) { [].forEach.call((root || document).querySelectorAll('#kpcDoor a[href], #kpcDoor img[src]'), function (a) { var at = a.tagName === 'IMG' ? 'src' : 'href', h = a.getAttribute(at); if (h && !/^(https?:|data:|#|\.\.\/|\/|mailto:)/.test(h)) a.setAttribute(at, '../' + h); }); }
  fix(); new MutationObserver(function () { fix(); }).observe(document.documentElement, { childList: true, subtree: true });
})();

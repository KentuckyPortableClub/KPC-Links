/* KPC web guides: builds the link lists on kpc-guide-tools-links.html and kpc-guide-founders-favorites.html
   from kpc-guide-links.json. The page has <div id="g-links" data-page="tools|founders">.
   When finished it sets <html data-ready="1"> (the PDF printer waits for that). */
(function () {
  var box = document.getElementById('g-links');
  if (!box) return;
  var key = box.getAttribute('data-page');
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function safeUrl(u) { return /^https?:\/\//i.test(u || '') ? u : '#'; }
  fetch('kpc-guide-links.json?v=20261013a', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (data) {
      var pg = data.pages && data.pages[key];
      if (!pg) throw new Error('no page ' + key);
      var h = '<div class="g-links">';
      pg.sections.forEach(function (s) {
        h += '<section class="g-lsec g-card"><h2>' + esc(s.title) + '</h2><ul>';
        s.links.forEach(function (l) {
          h += '<li><b>' + esc(l.name) + '</b><a href="' + esc(safeUrl(l.url)) + '" target="_blank" rel="noopener">' +
            esc(l.label || l.url) + '</a>' + (l.why ? '<span class="why">' + esc(l.why) + '</span>' : '') + '</li>';
        });
        h += '</ul>' + (s.note ? '<p class="g-src" style="margin:10px 0 0">' + s.note + '</p>' : '') + '</section>';
      });
      h += '</div>';
      (pg.notes || []).forEach(function (n) {
        h += '<div class="g-call g-keep g-lnotes ' + esc(n.style || '') + '"><b class="t">' + esc(n.title) + '</b><p>' + n.html + '</p></div>';
      });
      box.innerHTML = h;
      document.documentElement.dataset.ready = '1';
    })
    .catch(function () {
      box.innerHTML = '<div class="g-call warn"><b class="t">COULD NOT LOAD THE LIST</b><p>Please refresh the page.</p></div>';
      document.documentElement.dataset.ready = 'error';
    });
})();

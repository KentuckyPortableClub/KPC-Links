/* KPC announcements + email-updates button.
   - <div id="kpc-announce" data-page="news|campout"></div> shows posts from kpc-announcements.json
     (written by .github/workflows/kpc-discord-relay.yml from the private Discord channel), with a date stamp.
   - <span data-kpc-sub></span> becomes the GET EMAIL UPDATES / UNSUBSCRIBE button from kpc-subscribe-form.json.
     It stays hidden while that file's url is empty. */
(function () {
  'use strict';
  var CSS = '.ka-wrap{margin:0 0 26px}.ka-item{background:#fff;border:1px solid rgba(23,23,23,.1);border-left:5px solid #d5a63a;border-radius:10px;padding:16px 18px;margin:0 0 14px;box-shadow:0 8px 22px rgba(0,0,0,.05);text-align:left}' +
    '.ka-date{font:800 12px/1.2 system-ui,sans-serif;letter-spacing:1.5px;color:#7a5b12;margin:0 0 8px;text-transform:uppercase}' +
    '.ka-text{white-space:pre-wrap;overflow-wrap:anywhere;color:#222;font-size:16px;line-height:1.5;margin:0}.ka-text a{color:#0b5cad;font-weight:700}' +
    '.ka-ph{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.ka-ph a{display:block;flex:1 1 140px;max-width:100%}.ka-ph img{display:block;width:100%;height:auto;max-height:340px;object-fit:cover;border-radius:8px}' +
    '.ka-by{margin-top:10px;font-size:13px;color:#666}.ka-more{display:inline-block;margin:4px 0 0;padding:10px 16px;border-radius:999px;border:2px solid #d5a63a;background:transparent;font:800 13px system-ui,sans-serif;letter-spacing:1px;cursor:pointer;color:inherit}' +
    '.ka-sub{display:inline-block;padding:12px 18px;border-radius:999px;background:#d5a63a;color:#10140f!important;font:900 13px system-ui,sans-serif;letter-spacing:1.2px;text-decoration:none;margin:6px 6px 0 0}' +
    '.ka-pin{border-left-color:#c0392b;background:#fffaf2}.ka-ed{color:#8a6d2a;font-weight:700}.ka-subnote{display:block;font-size:13px;margin-top:6px;opacity:.85}';
  var st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function linkify(t) {
    return esc(t).replace(/https?:\/\/[^\s<]+[^\s<.,;:!?)\]'"]/g, function (u) {
      var h = u.replace(/&amp;/g, '&');
      return '<a href="' + esc(h) + '" target="_blank" rel="noopener">' + u + '</a>';
    });
  }
  function fmt(iso) {
    var d = new Date(iso); if (isNaN(d)) return '';
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric', timeZone: 'America/New_York' });
  }
  function card(it) {
    var ph = (it.photos || []).map(function (p) { return '<a href="' + esc(p) + '" target="_blank" rel="noopener"><img src="' + esc(p) + '" alt="Announcement photo" loading="lazy"></a>'; }).join('');
    return '<article class="ka-item' + (it.pinned ? ' ka-pin' : '') + '" id="a-' + esc(it.id) + '"><p class="ka-date">' + (it.pinned ? '📌 PINNED · ' : '📅 ') + esc(fmt(it.date)) +
      (it.edited ? ' <span class="ka-ed">· UPDATED ' + esc(fmt(it.edited)) + '</span>' : '') + '</p><p class="ka-text">' + linkify(it.text) + '</p>' +
      (ph ? '<div class="ka-ph">' + ph + '</div>' : '') + '</article>';
  }

  // Every feed box: #kpc-announce (news / campout) and any [data-ka-feed] box (e.g. the Activation Reports section).
  var boxes = Array.prototype.slice.call(document.querySelectorAll('#kpc-announce,[data-ka-feed]'));
  if (boxes.length) {
    fetch('kpc-announcements.json?t=' + Math.floor(Date.now() / 120000)).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      var all = (j && j.items) || [];
      boxes.forEach(function (box) {
        var page = box.getAttribute('data-page') || 'news', SHOW = 5;
        var list = all.filter(function (it) { return (it.pages || [it.page]).indexOf(page) >= 0; })
          .sort(function (a, b) { return (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0) || String(b.date).localeCompare(String(a.date)); });
        if (!list.length) return;
        box.classList.add('ka-wrap');
        function draw(n) {
          box.innerHTML = list.slice(0, n).map(card).join('') + (list.length > n ? '<button type="button" class="ka-more">SHOW OLDER POSTS (' + (list.length - n) + ')</button>' : '');
          var b = box.querySelector('.ka-more'); if (b) b.onclick = function () { draw(n + 10); };
        }
        draw(SHOW);
        var sel = box.getAttribute('data-ka-reveal');
        var sh = document.querySelectorAll(sel || '[data-ka-show]'); for (var i = 0; i < sh.length; i++) sh[i].hidden = false;
      });
    }).catch(function () {});
  }

  var subs = document.querySelectorAll('[data-kpc-sub]');
  if (subs.length) {
    fetch('kpc-subscribe-form.json?t=' + Math.floor(Date.now() / 3600000)).then(function (r) { return r.ok ? r.json() : null; }).then(function (f) {
      if (!f || !/^https:\/\/(docs\.google\.com\/forms|forms\.gle)\//.test(f.url || '')) return;
      function u(choice) {
        if (!f.choiceEntry || !choice) return f.url;
        return f.url + (f.url.indexOf('?') < 0 ? '?' : '&') + 'usp=pp_url&' + encodeURIComponent(f.choiceEntry) + '=' + encodeURIComponent(choice);
      }
      for (var i = 0; i < subs.length; i++) {
        subs[i].innerHTML = '<a class="ka-sub" href="' + esc(u(f.subscribe)) + '" target="_blank" rel="noopener">📬 GET EMAIL UPDATES</a>' +
          '<a class="ka-sub" style="background:transparent;border:2px solid #d5a63a;color:inherit!important" href="' + esc(u(f.unsubscribe)) + '" target="_blank" rel="noopener">UNSUBSCRIBE</a>' +
          '<a class="ka-sub" style="background:transparent;border:2px solid #d5a63a;color:inherit!important" href="KPC-Email-Contact.vcf" download="Kentucky-Portable-Club.vcf">📇 SAVE KPC AS A CONTACT</a>' +
          '<span class="ka-subnote">Club news and campout updates by email. Same form for both; your email is only used for these updates.</span>' +
          '<span class="ka-subnote"><b>Keep our emails out of Spam:</b> tap SAVE KPC AS A CONTACT after you sign up. If an email still lands in Spam, open it and tap <b>Not spam</b>.</span>';
      }
      var c = document.getElementById('kaSubCard'); if (c) c.hidden = false;
    }).catch(function () {});
  }
})();

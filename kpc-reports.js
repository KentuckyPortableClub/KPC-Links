/* KPC Reports form helper (used by Park Notes, Campgrounds & Cabins, the POTA guide, Photos and Events).
   - KPCReports.ready: a promise that resolves once kpc-reports-form.json and kpc-conditions.json are loaded (never rejects).
   - KPCReports.formUrl(kind, ref): the Google Form link pre-set to that kind (conditions / problem / photo / event), or ''
     while kpc-reports-form.json has no url yet (so buttons stay hidden).
   - KPCReports.conds(refs) / banner(refs): current park-condition reports for those references (expired ones skipped).
   Banners use class no-print so they never show in the printed PDFs. */
(function (root) {
  var FORM = {}, COND = [];
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function today() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function nice(iso) { var m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || ''); return m ? MON[+m[2] - 1] + ' ' + (+m[3]) : ''; }
  function getJSON(u) { return fetch(u, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  if (typeof document !== 'undefined' && !document.getElementById('kpc-reports-css')) {
    var st = document.createElement('style'); st.id = 'kpc-reports-css';
    st.textContent = '.kpc-cond{margin:8px 0;padding:8px 11px;border:1px solid #c0392b;border-left:5px solid #c0392b;border-radius:6px;background:#fdecea;color:#5c1a12;font:13px/1.45 Arial,Helvetica,sans-serif;overflow-wrap:anywhere;text-align:left}' +
      '.kpc-cond b{color:#a5281b}.kpc-cond small{color:#7a4a43}.kpc-cond-n{display:inline-block;margin-left:6px;padding:2px 7px;border-radius:999px;background:#c0392b;color:#fff;font:900 10px Arial,sans-serif;letter-spacing:1px;white-space:nowrap;vertical-align:middle}' +
      '@media print{.kpc-cond,.kpc-cond-n,.kpc-rep-btn{display:none!important}}';
    (document.head || document.documentElement).appendChild(st);
  }
  var ready = Promise.all([getJSON('kpc-reports-form.json'), getJSON('kpc-conditions.json')]).then(function (a) {
    FORM = a[0] || {};
    var t = today();
    COND = ((a[1] && a[1].items) || []).filter(function (c) { return c && c.ref && (!c.expires || c.expires >= t); });
  });
  function formUrl(kind, ref) {
    if (!FORM.url || !/^https:\/\//.test(FORM.url)) return '';
    var p = [], k = (FORM.kinds || {})[kind];
    if (FORM.kindEntry && k) p.push(FORM.kindEntry + '=' + encodeURIComponent(k));
    if (ref && FORM.parkEntry && kind === 'conditions') p.push(FORM.parkEntry + '=' + encodeURIComponent(ref));
    return p.length ? FORM.url + (FORM.url.indexOf('?') >= 0 ? '&' : '?') + 'usp=pp_url&' + p.join('&') : FORM.url;
  }
  function conds(refs) {
    refs = [].concat(refs || []).filter(Boolean);
    return COND.filter(function (c) { return refs.indexOf(c.ref) >= 0; });
  }
  function banner(refs) {
    var main = [].concat(refs || [])[0];   // name the reference only when the report is for a linked one (a park's KFF or SOTA ref)
    return conds(refs).map(function (c) {
      return '<div class="kpc-cond no-print" role="note">⚠ <b>' + esc(c.kind || 'Report') + '</b>' + (c.ref !== main ? ' (' + esc(c.ref) + ')' : '') + ' — seen ' + esc(nice(c.seen)) +
        (c.call ? ' by ' + esc(c.call) : '') + (c.details ? ': ' + esc(c.details) : '') + ' <small>(shows until ' + esc(nice(c.expires)) + ')</small></div>';
    }).join('');
  }
  /* A reference plus the ones on the same ground (a POTA park's KFF / SOTA refs and back), from kpc-ky-data.json. */
  var REL = null;
  function related(D, ref) {
    if (!D || !D.parks) return [ref];
    if (!REL) {
      REL = {};
      var add = function (a, b) { (REL[a] = REL[a] || [a]); if (REL[a].indexOf(b) < 0) REL[a].push(b); };
      D.parks.forEach(function (p) {
        (p.kff || []).concat((p.sota || []).map(function (s) { return typeof s === 'string' ? s : (s.c || s[0]); })).forEach(function (r) { if (r) { add(p.c, r); add(r, p.c); } });
      });
      (D.kff || []).forEach(function (k) { if (k.p) { add(k.c, k.p); add(k.p, k.c); } });
    }
    return REL[ref] || [ref];
  }
  root.KPCReports = { ready: ready, formUrl: formUrl, conds: conds, banner: banner, related: related };
})(window);

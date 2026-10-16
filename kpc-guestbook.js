/* KPC Guestbook (kpc-guestbook.html). Data: kpc-guestbook.json (copied from the Google Form by
   .github/scripts/kpc_guestbook.py every 20 minutes). Form link: kpc-guestbook-form.json {url, nameEntry}. */
(function () {
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const proj = (lon, lat) => [(lon + 125) * 0.788 * 16, (50 - lat) * 16];
  const SKIP = new Set(['AK', 'HI', 'PR', 'DC']);
  let D = { entries: [] }, SHOW = 24;
  const HAM = { yes: '📻 Ham', study: '📚 Studying for a license', no: '👋 Visitor' };

  function sig(e) {
    const where = [e.town, e.state].filter(Boolean).join(', ');
    const d = e.date ? new Date(e.date + 'T12:00:00').toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) : '';
    return `<article class="kb-sig"><div class="kb-top"><h3>${esc(e.name)}</h3>${e.ham ? `<span class="kb-tag ${e.ham === 'yes' ? 'req' : 'plan'}">${HAM[e.ham] || ''}</span>` : ''}</div>
      <p class="kb-where">${where ? '📍 ' + esc(where) + ' · ' : ''}${esc(d)}</p>${e.msg ? `<p class="msg">${esc(e.msg)}</p>` : ''}</article>`;
  }
  function list() {
    const q = ($('gbQ').value || '').toLowerCase().trim();
    const all = (D.entries || []).filter(e => !q || [e.name, e.town, e.state, e.msg].join(' ').toLowerCase().includes(q));
    $('gbList').innerHTML = all.length ? '<div class="kb-grid">' + all.slice(0, SHOW).map(sig).join('') + '</div>'
      : `<div class="kb-empty">${(D.entries || []).length ? 'No signatures match that search.' : 'No signatures yet. Be the very first to sign!'}</div>`;
    $('gbMore').hidden = all.length <= SHOW;
  }
  function bars(obj, el) {
    const rows = Object.entries(obj || {}).sort((a, b) => b[1] - a[1]).slice(0, 8);
    if (!rows.length) { $(el).innerHTML = '<p class="kb-small">Nothing yet.</p>'; return; }
    const max = rows[0][1];
    $(el).innerHTML = rows.map(([k, v]) => `<div><span>${esc(k)}</span><i style="width:${Math.max(3, v / max * 100)}%"></i><b>${v}</b></div>`).join('');
  }
  async function map() {
    let st; try { st = (await (await fetch('kpc-us-states.json')).json()).filter(s => !SKIP.has(s.a)); } catch (e) { return; }
    const n = D.states || {}, max = Math.max(1, ...Object.values(n));
    const paths = st.map(s => {
      const d = s.p.map(poly => poly.map(ring => 'M' + ring.map(([lo, la]) => proj(lo, la).map(v => v.toFixed(1)).join(',')).join('L') + 'Z').join('')).join('');
      const c = n[s.n] || 0, cls = [c ? (c >= max / 2 && max > 1 ? 'on2' : 'on') : '', s.a === 'KY' ? 'home' : ''].join(' ').trim();
      return `<path d="${d}"${cls ? ` class="${cls}"` : ''}><title>${esc(s.n)}: ${c} signature${c === 1 ? '' : 's'}</title></path>`;
    }).join('');
    $('gbMap').innerHTML = `<svg viewBox="0 0 760 430" role="img" aria-label="Map of the states our guests came from">${paths}</svg>`;
    const other = Object.entries(n).filter(([k]) => !st.some(s => s.n === k)).map(([k, v]) => `${esc(k)} (${v})`);
    $('gbOther').textContent = other.length ? 'Also: ' + other.join(', ') : '';
  }
  async function init() {
    const [d, f] = await Promise.all([
      fetch('kpc-guestbook.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : {}).catch(() => ({})),
      fetch('kpc-guestbook-form.json').then(r => r.json()).catch(() => ({}))]);
    D = Object.assign({ entries: [] }, d);
    if (f && f.url) document.querySelectorAll('[data-gb-form]').forEach(a => { a.href = f.url; a.hidden = false; });
    const E = D.entries || [], places = Object.keys(D.states || {}).length, hams = E.filter(e => e.ham === 'yes').length;
    $('gbN').textContent = E.length; $('gbS').textContent = places; $('gbH').textContent = hams;
    $('gbQ').addEventListener('input', () => { SHOW = 24; list(); });
    $('gbMore').addEventListener('click', () => { SHOW += 24; list(); });
    list(); bars(D.found, 'gbFound'); bars(D.liked, 'gbLiked'); map();
  }
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init) : init();
})();

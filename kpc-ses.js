/* KPC Special Event Stations calendar (events.html / eventsHOLD.html, section #special-events).
   Data: kpc-special-events.json, refreshed every morning by .github/workflows/kpc-ses.yml from the ARRL
   Special Event Stations list, plus the big yearly events (13 Colonies, Museum Ships Weekend, ...). */
(function () {
  'use strict';
  const box = document.getElementById('sesBox'); if (!box) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const M = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'], D = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
  const NEAR = ['KY', 'IN', 'OH', 'WV', 'VA', 'TN', 'MO', 'IL'];
  const pd = s => { const [y, m, d] = String(s).split('-').map(Number); return new Date(y, m - 1, d); };
  const today = () => { const t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); };
  const DAY = 864e5;
  let S = [], Y = [], when = 'now', st = 'all', q = '', shown = 12;
  try { const v = JSON.parse(localStorage.getItem('kpcSesF') || '{}'); if (v.when) when = v.when; if (v.st) st = v.st; } catch (e) {}
  const save = () => { try { localStorage.setItem('kpcSesF', JSON.stringify({ when, st })); } catch (e) {} };
  const onNow = e => pd(e.start) <= today() && pd(e.end) >= today();
  function dateBox(e) {
    const s = pd(e.start), en = pd(e.end), same = s.getTime() === en.getTime();
    return `<div class="ses-date"><span>${M[s.getMonth()]}</span><b>${s.getDate()}${!same && en.getMonth() === s.getMonth() ? '–' + en.getDate() : ''}</b><small>${!same && en.getMonth() !== s.getMonth() ? 'TO ' + M[en.getMonth()] + ' ' + en.getDate() : D[s.getDay()]}</small></div>`;
  }
  function card(e) {
    const now = onNow(e), calls = (e.calls || []).filter(c => c && c !== e.call);
    const tags = [now ? '<span class="ses-tag now">● ON THE AIR NOW</span>' : '', e.st ? `<span class="ses-tag">${esc(e.st)}</span>` : '', e.qsl ? `<span class="ses-tag q">${esc(e.qsl.toUpperCase())}</span>` : ''].join('');
    const call = e.call || (e.calls || [])[0] || '';
    return `<article class="ses-ev${now ? ' now' : ''}">${dateBox(e)}<div class="ses-body"><div class="ses-tags">${tags}</div>` +
      `<h3>${call ? `<span class="ses-call">${esc(call)}</span> ` : ''}${esc(e.title)}</h3>` +
      `<p>${[e.where, e.by].filter(Boolean).map(esc).join(' · ')}${e.times ? ` · <span class="ses-utc">${esc(e.times)} UTC</span>` : ''}</p>` +
      (e.freqs ? `<p class="ses-f">📻 ${esc(e.freqs)}</p>` : '') +
      (calls.length ? `<p class="ses-more">Also: ${calls.map(esc).join(', ')}</p>` : '') +
      `</div><div class="ses-acts">${e.url ? `<a class="main" href="${esc(e.url)}" target="_blank" rel="noopener">DETAILS ↗</a>` : ''}` +
      (call ? `<a href="https://www.qrz.com/db/${encodeURIComponent(call.split('/')[0])}" target="_blank" rel="noopener">QRZ ↗</a><a href="kpc-live.html?spot=${encodeURIComponent(call.split('/')[0])}#spots-card">FIND ON THE AIR ›</a>` : '') + `</div></article>`;
  }
  function yearCard(e) {
    return `<a class="ses-y${onNow(e) ? ' now' : ''}" href="${esc(e.url)}" target="_blank" rel="noopener">${dateBox(e)}<span><b>${esc(e.title)}</b><small>${esc(e.about)}</small><em>${esc(e.calls)}</em></span></a>`;
  }
  function list() {
    const t = today().getTime(), ql = q.trim().toUpperCase();
    return S.filter(e => {
      const s = pd(e.start).getTime(), en = pd(e.end).getTime();
      if (en < t) return false;
      if (when === 'now' && s > t) return false;
      if (when === 'week' && s > t + 7 * DAY) return false;
      if (when === 'month' && s > t + 31 * DAY) return false;
      if (st === 'near' && !NEAR.includes(e.st)) return false;
      if (st !== 'all' && st !== 'near' && e.st !== st) return false;
      if (ql && !(e.title + ' ' + (e.calls || []).join(' ') + ' ' + e.call + ' ' + e.where + ' ' + e.by).toUpperCase().includes(ql)) return false;
      return true;
    });
  }
  function draw() {
    const L = list(), stl = [...new Set(S.map(e => e.st).filter(Boolean))].sort();
    box.querySelector('.ses-when').innerHTML = [['now', 'ON THE AIR NOW'], ['week', 'NEXT 7 DAYS'], ['month', 'NEXT 30 DAYS'], ['all', 'EVERYTHING LISTED']].map(([v, l]) => `<button type="button" class="ses-chip" data-w="${v}" aria-pressed="${when === v}">${l}</button>`).join('');
    const sel = box.querySelector('#sesSt');
    sel.innerHTML = `<option value="all">All states</option><option value="near">Kentucky + neighbors</option>` + stl.map(s => `<option value="${s}">${s}</option>`).join('');
    sel.value = [...sel.options].some(o => o.value === st) ? st : 'all';
    const el = box.querySelector('.ses-list');
    el.innerHTML = L.length ? L.slice(0, shown).map(card).join('') + (L.length > shown ? `<button type="button" class="ses-chip ses-showmore" data-more="1">SHOW ${Math.min(12, L.length - shown)} MORE (${L.length - shown} not shown)</button>` : '')
      : `<p class="ses-none">${when === 'now' ? 'No special event stations on the air today match these filters. Try NEXT 7 DAYS.' : 'Nothing matches these filters.'}</p>`;
    box.querySelector('.ses-count').textContent = `${L.length} station${L.length === 1 ? '' : 's'} · ${S.filter(onNow).length} on the air today`;
  }
  box.innerHTML = `<div class="ses-yearly"><h3 class="ses-h">⭐ Big yearly events</h3><div class="ses-ylist"></div></div>` +
    `<h3 class="ses-h">📡 Special event stations from the ARRL list</h3>` +
    `<div class="ses-tools"><div class="ses-when" role="group" aria-label="When"></div><label>STATE<select id="sesSt" aria-label="State"></select></label><label>SEARCH<input id="sesQ" type="search" placeholder="Call or name…" aria-label="Search special event stations"></label></div>` +
    `<div class="ses-count"></div><div class="ses-list" aria-live="polite"><p class="ses-none">Loading…</p></div>` +
    `<p class="ses-note">From the <a href="https://www.arrl.org/special-event-stations" target="_blank" rel="noopener">ARRL Special Event Stations list</a>, checked every morning. Dates are the club's own listing; times are UTC. Many offer a QSL card or certificate (details on their page). <span id="sesUpd"></span></p>`;
  box.querySelector('.ses-when').addEventListener('click', e => { const b = e.target.closest('[data-w]'); if (!b) return; when = b.dataset.w; shown = 12; save(); draw(); });
  box.querySelector('#sesSt').addEventListener('change', e => { st = e.target.value; shown = 12; save(); draw(); });
  box.querySelector('#sesQ').addEventListener('input', e => { q = e.target.value; shown = 12; draw(); });
  box.querySelector('.ses-list').addEventListener('click', e => { if (e.target.closest('[data-more]')) { shown += 12; draw(); } });
  fetch('kpc-special-events.json', { cache: 'no-cache' }).then(r => r.json()).then(d => {
    S = (d.stations || []).slice().sort((a, b) => a.start < b.start ? -1 : a.start > b.start ? 1 : 0);
    Y = (d.yearly || []).filter(e => pd(e.end) >= today());
    const seen = new Set();
    box.querySelector('.ses-ylist').innerHTML = Y.filter(e => !seen.has(e.title) && seen.add(e.title)).map(yearCard).join('');
    if (when === 'now' && !S.some(onNow)) when = 'week';
    if (d.updated) box.querySelector('#sesUpd').textContent = 'Last checked ' + new Date(d.updated).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + '.';
    draw();
  }).catch(() => { box.querySelector('.ses-list').innerHTML = '<p class="ses-none">The special event list could not be loaded right now. See the <a href="https://www.arrl.org/special-event-stations" target="_blank" rel="noopener">ARRL list</a>.</p>'; });
})();

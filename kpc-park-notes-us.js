/* KPC Park Notes: Other States (Brandon Oct 16 2026). Tips for POTA parks, SOTA summits and KFF references
   outside Kentucky, from the same KPC Park Tips Google Form. The GitHub job (kpc_park_notes.py) copies the
   approved / auto-approved rows into kpc-park-notes-us.json. Kentucky places go to kpc-park-notes.html. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let FORM = { url: 'https://docs.google.com/forms/d/e/1FAIpQLSc6jTku8aIPejOVridQ19ChA5ACYsFK56n7Nk9WpIgAiLGTMw/viewform', parkEntry: 'entry.1271271904' };
  let N = [], KY = new Set(), KYN = {}, st = '', shown = 12;
  const prog = r => /\//.test(r) ? 'SOTA' : /FF-/.test(r) ? 'WWFF' : 'POTA';
  const page = r => prog(r) === 'SOTA' ? ['https://sotl.as/summits/' + r, 'SOTLAS'] : prog(r) === 'WWFF' ? ['https://wwff.co/directory/?showRef=' + r, 'WWFF PAGE'] : ['https://pota.app/#/park/' + r, 'POTA PAGE'];
  const formUrl = r => FORM.url + (FORM.url.includes('?') ? '&' : '?') + 'usp=pp_url&' + FORM.parkEntry + '=' + encodeURIComponent(r);
  const pad = r => {
    r = String(r || '').toUpperCase().replace(/\s+/g, '');
    if (/^\d{1,5}$/.test(r)) r = 'US-' + r;
    const s = r.match(/^([A-Z0-9]{1,4})\/?([A-Z]{2})-?(\d{1,3})$/); if (s && /\//.test(r)) return s[1] + '/' + s[2] + '-' + s[3].padStart(3, '0');
    const k = r.match(/^([A-Z0-9]{1,4})-?(\d{1,5})$/); return k ? k[1] + '-' + k[2].padStart(4, '0') : r;
  };
  function tip(t, withPlace) {
    const gps = t.gps ? (/^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$/.test(t.gps)
      ? `<a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(t.gps.replace(/\s/g, ''))}" target="_blank" rel="noopener">📍 ${esc(t.gps)}</a>` : `📍 ${esc(t.gps)}`) : '';
    return `<div class="pnu-tip">${withPlace ? `<div class="w"><a href="?ref=${encodeURIComponent(t.ref)}#find" data-ref="${esc(t.ref)}">${esc(t.name || t.ref)}</a> · ${esc(t.ref)}${t.st ? ' · ' + esc(t.st) : ''}</div>` : ''}
 <div class="t">${esc(String(t.type || 'TIP').toUpperCase())}</div><p>${esc(t.text)}</p>
 <div class="m">${gps ? gps + ' · ' : ''}from <a href="https://www.qrz.com/db/${encodeURIComponent(t.call)}" target="_blank" rel="noopener">${esc(t.call)}</a>${t.date ? ' · ' + esc(t.date) : ''}</div>
 ${(t.photos || []).length ? `<div class="pnu-ph">${t.photos.map(p => `<a href="${esc(p)}" target="_blank" rel="noopener"><img src="${esc(p)}" alt="Photo from ${esc(t.call)} at ${esc(t.ref)}" loading="lazy"></a>`).join('')}</div>` : ''}</div>`;
  }
  async function nameOf(r) {
    const hit = N.find(t => t.ref === r && t.name); if (hit) return [hit.name, hit.st];
    try {
      if (prog(r) === 'WWFF') { const rows = await fetch('data/wwff/' + r.split('-')[0] + '.json').then(x => x.ok ? x.json() : []); const x = rows.find(y => y[0] === r); if (x) return [x[1], String(x[5] || '').replace(/^K-/, '')]; }
      else if (prog(r) === 'SOTA') { const [a, b] = r.split('/'); const j = await fetch('https://api2.sota.org.uk/api/summits/' + encodeURIComponent(a) + '/' + encodeURIComponent(b)).then(x => x.ok ? x.json() : null); if (j && j.name) return [j.name, '']; }
      else { const j = await fetch('https://api.pota.app/park/' + encodeURIComponent(r)).then(x => x.ok ? x.json() : null); if (j && j.name) return [j.name, String(j.locationDesc || '').replace(/^US-/, '').split(',')[0]]; }
    } catch (e) {}
    return ['', ''];
  }
  async function show(ref, name) {
    ref = pad(ref); const box = $('pnuOne');
    if (KY.has(ref)) {
      box.innerHTML = `<div class="pnu-card"><h3>${esc(name || KYN[ref] || ref)}</h3><div class="pnu-meta">${esc(ref)} · KENTUCKY</div><p class="pnu-none">This one is in Kentucky, so its tips live on our Kentucky page.</p><div class="pnu-acts"><a class="gold" href="kpc-park-notes.html#${encodeURIComponent(ref)}">OPEN KENTUCKY PARK NOTES ›</a></div></div>`;
      return;
    }
    box.innerHTML = '<div class="pnu-card"><p class="pnu-none">Looking it up…</p></div>';
    let st2 = ''; if (!name) [name, st2] = await nameOf(ref); else st2 = (N.find(t => t.ref === ref) || {}).st || '';
    if (!name && !N.some(t => t.ref === ref)) { box.innerHTML = `<div class="pnu-card"><p class="pnu-none">Couldn't find <b>${esc(ref)}</b>. Check the number, or try the name.</p></div>`; return; }
    if (st2 === 'KY') { KY.add(ref); return show(ref, name); }
    const tips = N.filter(t => t.ref === ref), pg = page(ref);
    const acts = [`<a class="gold" href="${esc(formUrl(ref))}" target="_blank" rel="noopener">📝 SUBMIT A TIP</a>`];
    if (prog(ref) === 'POTA') acts.push(`<a href="kpc-planner-us.html?q=${encodeURIComponent(ref)}">US TRIP PLANNER</a>`);
    acts.push(`<a href="kpc-park-info.html?ref=${encodeURIComponent(ref)}">OFFICIAL WEBSITE &amp; MAP</a>`, `<a href="${pg[0]}" target="_blank" rel="noopener">${pg[1]} ↗</a>`);
    box.innerHTML = `<div class="pnu-card"><h3>${esc(name || ref)}</h3><div class="pnu-meta">${esc(ref)} · ${prog(ref)}${st2 ? ' · ' + esc(st2) : ''} · ${tips.length} tip${tips.length === 1 ? '' : 's'}</div>
 ${tips.length ? tips.map(t => tip(t)).join('') : '<p class="pnu-none">No tips yet. Been there? Be the first.</p>'}
 <div class="pnu-acts">${acts.join('')}</div></div>`;
    try { history.replaceState(null, '', '?ref=' + encodeURIComponent(ref) + '#find'); } catch (e) {}
  }
  function list() {
    const L = st ? N.filter(t => t.st === st) : N;
    $('pnuList').innerHTML = L.length ? L.slice(0, shown).map(t => tip(t, true)).join('') + (L.length > shown ? '<div class="kb-actions"><button type="button" class="kb-btn line" id="pnuMore">SHOW MORE</button></div>' : '')
      : '<div class="kb-empty">No tips from other states yet. Find a park above and be the first.</div>';
    const m = $('pnuMore'); if (m) m.onclick = () => { shown += 12; list(); };
  }
  function states() {
    const c = {}; N.forEach(t => { if (t.st) c[t.st] = (c[t.st] || 0) + 1; });
    const ks = Object.keys(c).sort();
    $('pnuSts').innerHTML = ks.length ? `<button type="button" class="kb-chip" aria-pressed="${!st}" data-st="">ALL</button>` + ks.map(k => `<button type="button" class="kb-chip" aria-pressed="${st === k}" data-st="${k}">${k} (${c[k]})</button>`).join('') : '';
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('#pnuSts [data-st]'); if (b) { st = b.dataset.st; shown = 12; states(); list(); return; }
    const a = e.target.closest('#pnuList a[data-ref]'); if (a) { e.preventDefault(); show(a.dataset.ref); $('find').scrollIntoView({ behavior: 'smooth' }); }
  });
  const q = $('pnuQ');
  if (window.KPCTA) KPCTA.attach(q, (ref, it) => show(ref, it && it[1] && !/^Look up /.test(it[1]) ? it[1] : ''));
  q.addEventListener('keydown', e => { if (e.key === 'Enter' && /\d/.test(q.value)) { e.preventDefault(); q.blur(); document.querySelectorAll('.kta.on').forEach(x => x.classList.remove('on')); show(q.value); } });
  Promise.all([
    fetch('kpc-park-notes-us.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null),
    fetch('kpc-park-notes-form.json').then(r => r.ok ? r.json() : null).catch(() => null),
    fetch('kpc-ky-data.json').then(r => r.ok ? r.json() : null).catch(() => null)
  ]).then(([d, f, ky]) => {
    N = (d && d.notes) || []; if (f && f.url && f.parkEntry) FORM = f;
    if (ky) ['parks', 'summits', 'kff'].forEach(k => (ky[k] || []).forEach(p => { const c = String(p.c).toUpperCase(); KY.add(c); KYN[c] = p.n; }));
    if (d && d.updated) $('pnuUpd').textContent = 'Tips last checked ' + d.updated + '.';
    states(); list();
    const r = new URLSearchParams(location.search).get('ref'); if (r) show(r);
  });
})();

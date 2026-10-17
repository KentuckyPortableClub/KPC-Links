/* KPC Top 50 (members room, Brandon Oct 16 2026): the busiest POTA activators and hunters in each state, from
   data/leaders/US-XX.json (built weekly by kpc-state-leaders.yml from POTA's public activation lists and each park's
   top-10 hunter list). Rows: [call, activations, parks, qsos, first yyyymmdd, last yyyymmdd, acts this year, parks this year, qsos this year];
   hunters: [call, qsos, parks-where-top-10]. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming' };
  const ME = String(get('kpcMyCall', '') || '').toUpperCase();
  let S = Object.assign({ st: 'KY', per: 'all', l: 'acts' }, get('kpcTop50', {})), D = {};
  const n = v => (+v || 0).toLocaleString();
  const dt = d => d && /^\d{8}$/.test(d) ? `${d.slice(4, 6)}/${d.slice(6, 8)}/${d.slice(0, 4)}` : '–';
  const ago = d => { if (!d || !/^\d{8}$/.test(d)) return ''; const t = Date.UTC(+d.slice(0, 4), +d.slice(4, 6) - 1, +d.slice(6, 8)), days = Math.round((Date.now() - t) / 864e5); return days < 1 ? 'today' : days < 2 ? 'yesterday' : days < 60 ? days + ' days ago' : days < 730 ? Math.round(days / 30) + ' months ago' : Math.round(days / 365) + ' years ago'; };
  $('tSt').innerHTML = Object.keys(ST).map(a => `<option value="${a}"${a === S.st ? ' selected' : ''}>${ST[a]}</option>`).join('');
  function chips() {
    document.querySelectorAll('[data-per]').forEach(b => b.setAttribute('aria-pressed', b.dataset.per === S.per));
    document.querySelectorAll('[data-l]').forEach(b => { b.setAttribute('aria-pressed', b.dataset.l === S.l); b.hidden = S.per === 'year' && /^hunt/.test(b.dataset.l); });
  }
  async function load() {
    const a = S.st; put('kpcTop50', S); chips();
    if (!D[a]) { $('tList').innerHTML = '<div class="kb-empty">Loading…</div>'; D[a] = await fetch('data/leaders/US-' + a + '.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : null).catch(() => null) || { none: 1 }; }
    draw();
  }
  function draw() {
    const d = D[S.st], a = S.st;
    if (!d || d.none) { $('tList').innerHTML = `<div class="kb-empty">${esc(ST[a])}’s list is still being added up. It fills in within a week.</div>`; $('tTiles').innerHTML = $('tPod').innerHTML = $('tSrc').textContent = ''; return; }
    const yr = d.year || String(new Date().getFullYear());
    $('tYearBtn').textContent = 'THIS YEAR (' + yr + ')';
    const hunt = /^hunt/.test(S.l), year = S.per === 'year' && !hunt;
    const key = year ? 'y' + S.l : S.l;
    let L = d[key];
    if (!L) { $('tList').innerHTML = `<div class="kb-empty">${year ? 'This year’s list' : 'This list'} for ${esc(ST[a])} is being added up this week.</div>`; $('tPod').innerHTML = ''; tiles(d, year); src(d, hunt, year); return; }
    tiles(d, year);
    const q = $('tQ').value.trim().toUpperCase();
    const V = r => year ? { a: r[6], p: r[7], q: r[8] } : { a: r[1], p: r[2], q: r[3] };
    const medal = ['🥇', '🥈', '🥉'];
    $('tPod').innerHTML = L.slice(0, 3).map((r, i) => {
      const v = hunt ? null : V(r);
      const main = hunt ? (S.l === 'hunt' ? `${n(r[1])} QSOs` : `${n(r[2])} parks`) : S.l === 'acts' ? `${n(v.a)} activations` : S.l === 'uniq' ? `${n(v.p)} parks` : `${n(v.q)} QSOs`;
      const sub = hunt ? (S.l === 'hunt' ? `top 10 at ${n(r[2])} parks` : `${n(r[1])} QSOs`) : `${n(v.a)} act · ${n(v.p)} parks · ${n(v.q)} QSOs`;
      return `<div class="t5-p g${i + 1}"><div class="m">${medal[i]}</div><div class="c"><a href="https://www.qrz.com/db/${encodeURIComponent(r[0])}" target="_blank" rel="noopener">${esc(r[0])}</a></div><div class="v">${main}</div><div class="s">${sub}</div></div>`;
    }).join('');
    const head = hunt ? '<tr><th>#</th><th>HUNTER</th><th>QSOS</th><th>PARKS (TOP 10 AT)</th><th class="hs">% OF STATE’S PARKS</th></tr>'
      : `<tr><th>#</th><th>ACTIVATOR</th><th>ACTIVATIONS${year ? ' ' + yr : ''}</th><th>PARKS${year ? ' ' + yr : ''}</th><th class="hs">% OF STATE’S PARKS</th><th>QSOS${year ? ' ' + yr : ''}</th><th class="hs">QSOS / ACTIVATION</th><th class="hs">FIRST HERE</th><th>LAST OUT</th></tr>`;
    const rows = L.map((r, i) => {
      const cls = r[0] === ME ? 'me' : q && r[0].includes(q) ? 'hit' : '';
      const c = `<td class="r">${i < 3 ? medal[i] : i + 1}</td><td class="c"><a href="https://www.qrz.com/db/${encodeURIComponent(r[0])}" target="_blank" rel="noopener">${esc(r[0])}</a><small><a href="https://pota.app/#/profile/${encodeURIComponent(r[0])}" target="_blank" rel="noopener">POTA</a></small></td>`;
      if (hunt) { const pct = Math.round(r[2] / d.parks * 100); return `<tr class="${cls}">${c}<td class="n k">${n(r[1])}</td><td class="n">${n(r[2])}</td><td class="hs">${pct}%<span class="bar"><i style="width:${Math.min(100, pct)}%"></i></span></td></tr>`; }
      const v = V(r), pct = Math.round(v.p / d.parks * 100), avg = v.a ? Math.round(v.q / v.a) : 0;
      return `<tr class="${cls}">${c}<td class="n${S.l === 'acts' ? ' k' : ''}">${n(v.a)}</td><td class="n${S.l === 'uniq' ? ' k' : ''}">${n(v.p)}</td><td class="hs">${pct}%<span class="bar"><i style="width:${Math.min(100, pct)}%"></i></span></td><td class="n${S.l === 'qsos' ? ' k' : ''}">${n(v.q)}</td><td class="hs n">${avg}</td><td class="hs">${dt(r[4])}</td><td title="${dt(r[5])}">${r[5] ? ago(r[5]) : '–'}</td></tr>`;
    }).join('');
    $('tList').innerHTML = `<table><thead>${head}</thead><tbody>${rows}</tbody></table>`;
    const hit = document.querySelector('#tList tr.hit'); if (hit && q) hit.scrollIntoView({ block: 'center', behavior: 'smooth' });
    src(d, hunt, year);
  }
  function tiles(d, year) {
    const yr = d.year || '';
    $('tTiles').innerHTML = `<div><b>${n(d.parks)}</b><span>POTA PARKS IN ${esc(S.st)}</span></div><div><b>${n(d.activated)}</b><span>EVER ACTIVATED</span></div><div><b>${n(d.activators)}</b><span>ACTIVATORS ALL TIME</span></div>${d.yactivators != null ? `<div><b>${n(d.yactivators)}</b><span>ACTIVATORS IN ${yr}</span></div>` : ''}`;
  }
  function src(d, hunt, year) {
    $('tSrc').innerHTML = (hunt ? `HUNTERS: POTA only shares each park’s top 10 hunters, so KPC adds those lists up across ${esc(ST[S.st])}’s ${n(d.parks)} parks. QSOS = contacts counted where they’re in a park’s top 10; PARKS = how many parks they’re top 10 at. Close, but not an official count. All time.`
      : `ACTIVATORS: added up by KPC from POTA’s public activation list for every park in ${esc(ST[S.st])}. An activation counts with 10+ QSOs (POTA’s rule); calls like K4TEST/P count as K4TEST. ${year ? 'THIS YEAR = activations dated ' + esc(d.year) + '.' : 'ALL TIME = every activation POTA has on record.'} First here / last out = their first and newest activation in this state.`)
      + ` Updated ${esc(d.updated)}, every Wednesday.${ME ? ` Your call (${esc(ME)}) is highlighted when it’s on the list.` : ''}`;
  }
  $('tSt').onchange = () => { S.st = $('tSt').value; load(); };
  $('tQ').oninput = draw;
  document.addEventListener('click', e => {
    const p = e.target.closest('[data-per]'); if (p) { S.per = p.dataset.per; if (S.per === 'year' && /^hunt/.test(S.l)) S.l = 'acts'; load(); return; }
    const l = e.target.closest('[data-l]'); if (l) { S.l = l.dataset.l; load(); }
  });
  load();
})();

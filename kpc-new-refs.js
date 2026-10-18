/* KPC "New this week" box (Oct 17 2026, Brandon): new POTA parks, KFF references and SOTA summits found by the daily bot
   (kpc-new-refs.json, kept 7 days). Mount: <div id="kpcNewRefs" data-scope="ky|us"></div>.
   ky = Kentucky only (Park Notes); us = every other state (Park Notes: Other States). Shows from the start time in the file
   (Oct 21 2026, 5 PM Central); ?preview=1 shows it before that. */
(function () {
  const box = document.getElementById('kpcNewRefs');
  if (!box) return;
  const KY = box.dataset.scope !== 'us';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const PROG = { pota: ['🌲', 'POTA'], kff: ['🌳', 'KFF'], sota: ['⛰', 'SOTA'] };
  const css = `#kpcNewRefs{margin:18px 0}#kpcNewRefs .nr{background:#fffaf0;border:2px solid #d5a63a;border-radius:14px;padding:14px 16px;box-shadow:0 0 18px rgba(213,166,58,.25)}
#kpcNewRefs h3{margin:0 0 4px;font-size:1.15rem;letter-spacing:.04em}#kpcNewRefs .nr-sub{margin:0 0 10px;font-size:.88rem;opacity:.8}
#kpcNewRefs .nr-ch{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px}#kpcNewRefs .nr-ch button,#kpcNewRefs .nr-ch select{font:inherit;font-size:.8rem;font-weight:700;letter-spacing:.05em;border:1px solid #c9a24a;border-radius:999px;padding:5px 11px;background:#fff;color:#2a1a05;cursor:pointer}
#kpcNewRefs .nr-ch button[aria-pressed=true]{background:linear-gradient(#f6d58a,#d5a63a);border-color:#b8892a}
#kpcNewRefs ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}#kpcNewRefs li{background:#fff;border:1px solid #e4d3a6;border-radius:10px;padding:9px 11px}
#kpcNewRefs .nr-t{display:flex;flex-wrap:wrap;gap:6px;align-items:baseline}#kpcNewRefs .nr-ref{font-family:ui-monospace,Menlo,monospace;font-weight:800}
#kpcNewRefs .nr-tag{font-size:.7rem;font-weight:800;letter-spacing:.06em;border-radius:6px;padding:1px 6px;background:#2c6e49;color:#fff}#kpcNewRefs .nr-tag.kff{background:#1d7a7a}#kpcNewRefs .nr-tag.sota{background:#b4561e}
#kpcNewRefs .nr-m{font-size:.8rem;opacity:.75;margin-top:2px}#kpcNewRefs .nr-l{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
#kpcNewRefs .nr-l a{font-size:.74rem;font-weight:800;letter-spacing:.05em;text-decoration:none;border:1px solid #c9a24a;border-radius:999px;padding:3px 9px;color:#2a1a05;background:#fff6dc}
#kpcNewRefs .nr-more{margin-top:10px;font:inherit;font-weight:800;border:0;background:none;color:#8a5a00;cursor:pointer;text-decoration:underline}
#kpcNewRefs .nr-st{font:inherit;font-weight:900;font-size:.85rem;letter-spacing:.06em;border:0;border-radius:8px;padding:3px 9px;background:#2a1a05;color:#f6d58a;cursor:pointer}#kpcNewRefs .nr-refs{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}#kpcNewRefs .nr-refs a{font-size:.8rem;text-decoration:none;border:1px solid #e4d3a6;border-radius:8px;padding:3px 8px;color:#2a1a05;background:#fffaf0;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#kpcNewRefs .nr-back{font:inherit;font-weight:800;border:0;background:none;color:#8a5a00;cursor:pointer;margin:0 0 8px;padding:0}#kpcNewRefs .nr-none{margin:0;font-size:.9rem;opacity:.8}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const ago = d => { const n = Math.round((Date.parse(new Date().toISOString().slice(0, 10)) - Date.parse(d)) / 864e5); return n <= 0 ? 'found today' : n === 1 ? 'found yesterday' : `found ${n} days ago`; };
  function links(i) {
    const r = encodeURIComponent(i.ref), L = [];
    if (i.prog === 'pota') L.push([`https://pota.app/#/park/${r}`, 'POTA PAGE']);
    if (i.prog === 'kff') L.push([`https://wwff.co/directory/?showRef=${r}`, 'WWFF PAGE']);
    if (i.prog === 'sota') L.push([`https://sotl.as/summits/${i.ref}`, 'SOTLAS']);
    if (i.la != null && i.lo != null) L.push([`https://www.google.com/maps/search/?api=1&query=${i.la},${i.lo}`, 'MAP']);
    if (!KY) { L.push([`kpc-park-notes-us.html?ref=${r}`, '📝 ADD A TIP']); L.push([`kpc-planner-us.html?q=${r}`, 'TRIP PLANNER']); }
    return L.map(([h, t]) => `<a href="${h}"${/^https/.test(h) ? ' target="_blank" rel="noopener"' : ''}>${t}</a>`).join('');
  }
  let ALL = [], prog = '', state = '', shown = 12;
  function draw() {
    const list = ALL.filter(i => (!prog || i.prog === prog) && (!state || (i.st || []).includes(state)));
    const progs = [...new Set(ALL.map(i => i.prog))];
    const sts = KY ? [] : [...new Set(ALL.flatMap(i => i.st || []))].sort();
    let h = `<div class="nr"><h3>🆕 NEW THIS WEEK${KY ? ' IN KENTUCKY' : ' AROUND THE COUNTRY'}</h3><p class="nr-sub">New POTA parks, KFF references and SOTA summits ${KY ? 'in Kentucky' : 'outside Kentucky'}, found by our daily check. Each one stays here for 7 days.</p>`;
    if (progs.length > 1 || sts.length > 1) {
      h += '<div class="nr-ch">' + (progs.length > 1 ? `<button type="button" data-p="" aria-pressed="${!prog}">ALL</button>` + progs.map(p => `<button type="button" data-p="${p}" aria-pressed="${prog === p}">${PROG[p][0]} ${PROG[p][1]}</button>`).join('') : '')
        + (sts.length > 1 ? `<select aria-label="State"><option value="">ALL STATES</option>${sts.map(s => `<option${s === state ? ' selected' : ''}>${esc(s)}</option>`).join('')}</select>` : '') + '</div>';
    }
    if (!list.length) h += `<p class="nr-none">Nothing new this week${KY ? ' in Kentucky' : ''}. New ones show up here for 7 days.</p>`;
    else if (!KY && !state) {
      /* Oct 18 (Brandon): other states as a summary by state: 'GA · 7 new POTA parks: US-0096 …'; tap a state for the full cards */
      const by = {}; list.forEach(i => (i.st && i.st.length ? i.st : ['?']).forEach(st => (by[st] = by[st] || []).push(i)));
      const WORD = { pota: ['new POTA park', 'new POTA parks'], kff: ['new KFF reference', 'new KFF references'], sota: ['new SOTA summit', 'new SOTA summits'] };
      h += '<ul>' + Object.keys(by).sort((x, y) => by[y].length - by[x].length || x.localeCompare(y)).map(st => {
        const g = by[st], parts = ['pota', 'kff', 'sota'].map(p => { const n = g.filter(i => i.prog === p).length; return n ? `${n} ${WORD[p][n > 1 ? 1 : 0]}` : ''; }).filter(Boolean).join(' · ');
        return `<li><div class="nr-t"><button type="button" class="nr-st" data-st="${esc(st)}">${esc(st === '?' ? 'STATE NOT LISTED' : st)}</button><b>${esc(parts)}</b></div><div class="nr-refs">${g.map(i => `<a href="kpc-park-notes-us.html?ref=${encodeURIComponent(i.ref)}" title="${esc(i.name)}"><span class="nr-ref">${esc(i.ref)}</span> ${esc(i.name)}</a>`).join('')}</div></li>`;
      }).join('') + '</ul>';
    }
    else {
      if (!KY && state) h += `<button type="button" class="nr-back">← ALL STATES</button>`;
      h += '<ul>' + list.slice(0, shown).map(i => `<li><div class="nr-t"><span class="nr-tag ${i.prog}">${PROG[i.prog][0]} ${PROG[i.prog][1]}</span><span class="nr-ref">${esc(i.ref)}</span><b>${esc(i.name)}</b></div>`
        + `<div class="nr-m">${KY ? '' : esc((i.st || []).join(', ') || '') + ' · '}${i.prog === 'sota' && i.ft ? esc(i.ft.toLocaleString()) + ' ft · ' + esc(i.pts) + ' pts · ' : ''}${ago(i.found)}</div><div class="nr-l">${links(i)}</div></li>`).join('') + '</ul>';
      if (list.length > shown) h += `<button type="button" class="nr-more">SHOW ${Math.min(12, list.length - shown)} MORE (${list.length - shown} left)</button>`;
    }
    box.innerHTML = h + '</div>';
  }
  box.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    if (b.classList.contains('nr-more')) { shown += 12; draw(); return; }
    if (b.dataset.st) { state = b.dataset.st === '?' ? '' : b.dataset.st; shown = 12; draw(); box.scrollIntoView({ block: 'start' }); return; }
    if (b.classList.contains('nr-back')) { state = ''; draw(); return; }
    if ('p' in b.dataset) { prog = b.dataset.p; shown = 12; draw(); }
  });
  box.addEventListener('change', e => { if (e.target.tagName === 'SELECT') { state = e.target.value; shown = 12; draw(); } });
  fetch('kpc-new-refs.json?t=' + Date.now()).then(r => r.ok ? r.json() : null).then(d => {
    if (!d) return;
    const preview = /[?&]preview=1/.test(location.search);
    if (!preview && d.start && Date.now() < Date.parse(d.start)) return;
    ALL = (d.items || []).filter(i => KY ? (i.st || []).includes('KY') : !(i.st || []).includes('KY') || (i.st || []).length > 1);
    draw();
  }).catch(() => {});
})();

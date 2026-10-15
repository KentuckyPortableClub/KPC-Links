/* KPC Spot Me (kpc-spot-me.html): one form, pick where your spot goes.
   Nothing is sent until the visitor ticks a destination and presses SEND.
   POTA: posted straight from the browser to api.pota.app/spot/ (open to any website, no login; POTA checks the park).
   Everything else: we copy a ready-made spot to the clipboard and open that site (they need their own login,
   or don't accept spots from other websites). */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const store = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }, del(k) { try { localStorage.removeItem(k); } catch (e) {} } };
  const BANDS = [[1800, 2000, '160m'], [3500, 4000, '80m'], [5330, 5410, '60m'], [7000, 7300, '40m'], [10100, 10150, '30m'], [14000, 14350, '20m'], [18068, 18168, '17m'], [21000, 21450, '15m'], [24890, 24990, '12m'], [28000, 29700, '10m'], [50000, 54000, '6m'], [144000, 148000, '2m'], [222000, 225000, '1.25m'], [420000, 450000, '70cm']];

  /* p = programs it suits ('*' = any); how: 'post' (we send it) | 'copy' (copy + open) | 'info' (just open) */
  const G = [
    ['SPOTTING NETWORKS FOR YOUR PROGRAM', [
      { id: 'pota', name: 'POTA (pota.app)', p: ['POTA'], how: 'post', url: 'https://pota.app/#/', about: 'Posts your spot to the POTA spots page right from here. No login. POTA checks the park number.', tag: ['ONE TAP', 'one'] },
      { id: 'sotawatch', name: 'SOTAwatch', p: ['SOTA'], how: 'copy', url: 'https://sotawatch.sota.org.uk/en/', about: 'Summit spots. Sign in with your free SOTA account, then Post spot and paste.', tag: ['COPY + OPEN'] },
      { id: 'wwff', name: 'WWFF Spotline', p: ['WWFF'], how: 'copy', url: 'https://spots.wwff.co/', about: 'KFF / WWFF spots. Needs a Spotline login (WWFF approves new accounts by hand; use your call as the user name).', tag: ['COPY + OPEN'] },
      { id: 'gma', name: 'GMA (Global Mountain Activity)', p: ['GMA', 'SOTA'], how: 'copy', url: 'https://www.cqgma.org/', about: 'GMA spots and alerts. Sign in, then spot.', tag: ['COPY + OPEN'] },
      { id: 'pnp', name: 'ParksnPeaks', p: ['WWFF', 'SOTA', 'POTA'], how: 'copy', url: 'https://parksnpeaks.org/', about: 'Australian spotting site that also takes WWFF and SOTA spots. Needs a free account.', tag: ['COPY + OPEN'] }
    ]],
    ['GENERAL DX CLUSTER (ONE SHARED NETWORK)', [
      { id: 'dxsummit', name: 'DX Summit', p: ['*'], how: 'copy', url: 'https://www.dxsummit.fi/', about: 'Big web DX cluster. A spot here goes out to cluster nodes worldwide.', tag: ['COPY + OPEN'], warn: 1 },
      { id: 'holy', name: 'Holy Cluster', p: ['*'], how: 'copy', url: 'https://holycluster.iarc.org', about: 'Modern map-style DX cluster (IARC). Same worldwide cluster spots.', tag: ['COPY + OPEN'], warn: 1 },
      { id: 'dxheat', name: 'DXHeat', p: ['*'], how: 'copy', url: 'https://dxheat.com/dxc/', about: 'Web DX cluster with band filters. Same worldwide cluster spots.', tag: ['COPY + OPEN'], warn: 1 }
    ]],
    ['NO INTERNET? PHONE OR RADIO ONLY', [
      { id: 'apspot', name: 'APSPOT (APRS or text message)', p: ['POTA', 'SOTA', 'WWFF'], how: 'copy', url: 'https://apspot.radio', about: 'Send one APRS message to APSPOT (or a text to its gateway number, listed on its site) and it spots POTA, SOTA and WWFF for you. We copy the message in its format.', tag: ['COPY + OPEN'] },
      { id: 'sotamat', name: 'SOTAmat', p: ['SOTA', 'POTA'], how: 'info', url: 'https://sotamat.com', about: 'Spots you over the air using FT8 and other digital modes, for summits with no cell signal. Set it up at home first.', tag: ['SET UP FIRST'] }
    ]],
    ['THE CLUB & FRIENDS', [
      { id: 'discord', name: 'KPC Discord', p: ['*'], how: 'copy', url: 'https://discord.gg/yNNgFgnst', about: 'Paste your spot in the club Discord. (KPC members\' POTA spots already post there automatically.)', tag: ['COPY + OPEN'] },
      { id: 'fbgroup', name: 'KPC Facebook group', p: ['*'], how: 'copy', url: 'https://www.facebook.com/share/g/181cJ5cuoJ/', about: 'Post it in the club Facebook group so friends know to listen.', tag: ['COPY + OPEN'] }
    ]],
    ['PLAN AHEAD (SO HUNTERS KNOW YOU\'RE COMING)', [
      { id: 'potasch', name: 'POTA activation schedule', p: ['POTA'], how: 'info', url: 'https://pota.app/#/activations', about: 'Post when and where you\'ll be. On CW and FT8 POTA can then spot you automatically from the Reverse Beacon Network.', tag: ['OPEN'] },
      { id: 'sotaalert', name: 'SOTAwatch alert', p: ['SOTA'], how: 'info', url: 'https://sotawatch.sota.org.uk/en/', about: 'Post an alert for your planned summit and time.', tag: ['OPEN'] },
      { id: 'wwffag', name: 'WWFF agenda', p: ['WWFF'], how: 'info', url: 'https://spots.wwff.co/', about: 'Add your planned activation. With an agenda posted, Spotline can spot you automatically from the Reverse Beacon Network.', tag: ['OPEN'] }
    ]]
  ];
  const ALL = G.flatMap(g => g[1]);
  let pick = new Set(store.get('kpcSpotMePick', null) || []);
  const keep = store.get('kpcSpotMePick', null) !== null;
  const form = store.get('kpcSpotMeForm', {});

  const up = v => String(v || '').trim().toUpperCase().replace(/\s+/g, '');
  const callOk = c => /^([A-Z0-9]{1,4}\/)?[A-Z0-9]{1,3}\d{1,2}[A-Z]{1,4}(\/[A-Z0-9]{1,4})?$/.test(c);
  function khz() { let v = parseFloat(String($('smFreq').value).replace(',', '.')); if (!isFinite(v) || v <= 0) return null; if (v < 1000) v *= 1000; return Math.round(v * 10) / 10; }
  const band = k => { const b = BANDS.find(x => k >= x[0] && k <= x[1]); return b ? b[2] : ''; };
  const fk = k => (k % 1 ? k.toFixed(1) : String(k));
  const fm = k => (k / 1000).toFixed(3);
  function val() {
    const prog = $('smProg').value;
    return { call: up($('smCall').value), by: up($('smBy').value) || up($('smCall').value), k: khz(), mode: $('smMode').value, prog, ref: prog === 'NONE' ? '' : up($('smRef').value), cm: $('smCm').value.trim() };
  }
  function txt(v, kind) {
    const pg = v.prog === 'NONE' ? '' : v.prog + (v.ref ? ' ' + v.ref : '');
    if (kind === 'apspot') return `! ${v.prog === 'NONE' ? 'POTA' : v.prog} ${v.ref || '?'} ${v.k ? fm(v.k) : '?'} ${v.mode}${v.cm ? ' ' + v.cm : ''}`;
    if (kind === 'cluster') return `${v.k ? fk(v.k) : '?'} ${v.call} ${[v.mode, pg, v.cm].filter(Boolean).join(' ')}`.slice(0, 80);
    return `${v.call} on ${v.k ? fm(v.k) + ' MHz' : '?'} ${v.mode}${pg ? ' · ' + pg : ''}${refName(v.ref) ? ' (' + refName(v.ref) + ')' : ''}${v.cm ? ' · ' + v.cm : ''}`;
  }
  const kindOf = d => d.id === 'apspot' ? 'apspot' : ['dxsummit', 'holy', 'dxheat', 'sotawatch', 'wwff', 'gma', 'pnp'].includes(d.id) ? 'cluster' : 'plain';
  let REFS = {};
  const refName = r => REFS[r] || '';
  const fits = (d, prog) => d.p.includes('*') || d.p.includes(prog);

  function drawDests() {
    const prog = $('smProg').value;
    $('smDests').innerHTML = G.map(([h, list]) => `<div class="sm-g"><h3>${esc(h)}</h3><div class="sm-list">` + list.map(d => {
      const ok = fits(d, prog), on = ok && pick.has(d.id);
      return `<label class="sm-d${on ? ' on' : ''}${ok ? '' : ' off'}"><input type="checkbox" data-id="${d.id}"${on ? ' checked' : ''}${ok ? '' : ' disabled'}><div><b>${esc(d.name)}</b><span>${esc(d.about)}</span>` +
        `<em class="${d.tag[1] || ''}">${esc(d.tag[0])}</em>${d.warn ? '<em class="warn">SELF-SPOT FROWNED ON (EXCEPT SPECIAL EVENTS)</em>' : ''}${ok ? '' : `<em>NOT FOR ${esc(prog === 'NONE' ? 'NO PROGRAM' : prog)}</em>`}</div></label>`;
    }).join('') + `</div></div>`).join('');
    count();
  }
  function chosen() { const prog = $('smProg').value; return ALL.filter(d => pick.has(d.id) && fits(d, prog)); }
  function count() {
    const c = chosen();
    $('smN').textContent = c.length ? c.length + ' PICKED' + (c.some(d => d.how === 'post') ? ' · POTA POSTS DIRECTLY' : '') : 'NOTHING PICKED YET';
    $('smSend').disabled = !c.length;
  }
  function preview() {
    const v = val(), k = v.k;
    $('smBand').textContent = k ? (band(k) ? fm(k) + ' MHz · ' + band(k) : 'Not inside a ham band, check it') : '';
    $('smRefName').textContent = refName(v.ref);
    $('smRef').disabled = v.prog === 'NONE';
    $('smRef').placeholder = { POTA: 'US-1271', SOTA: 'W4K/EC-001', WWFF: 'KFF-0019', GMA: 'reference', NONE: 'none' }[v.prog];
    $('smPrev').textContent = v.call && k ? txt(v, 'plain') : 'Fill in your call and frequency';
    store.set('kpcSpotMeForm', { call: $('smCall').value, freq: $('smFreq').value, mode: v.mode, prog: v.prog, ref: $('smRef').value, by: $('smBy').value, cm: $('smCm').value });
  }
  function fillRefs() {
    const prog = $('smProg').value, L = [];
    Object.entries(REFS).forEach(([c, n]) => { if ((prog === 'POTA' && /^US-/.test(c)) || (prog === 'SOTA' && /^W4K\//.test(c)) || (prog === 'WWFF' && /^KFF-/.test(c))) L.push(`<option value="${esc(c)}">${esc(n)}</option>`); });
    $('smRefs').innerHTML = L.join('');
  }
  async function copy(t) { try { await navigator.clipboard.writeText(t); return true; } catch (e) { try { const a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select(); const ok = document.execCommand('copy'); a.remove(); return ok; } catch (x) { return false; } } }
  function row(cls, title, msg, btn, extra) { return `<div class="sm-r ${cls}"><div><b>${esc(title)}</b><p>${msg}</p>${extra || ''}</div>${btn || ''}</div>`; }

  async function send() {
    const v = val(), errs = [];
    ['smCall', 'smFreq', 'smRef'].forEach(id => $(id).classList.remove('bad'));
    if (!callOk(v.call)) { errs.push('your call sign'); $('smCall').classList.add('bad'); }
    if (!v.k || !band(v.k)) { errs.push('a frequency inside a ham band'); $('smFreq').classList.add('bad'); }
    const c = chosen();
    if (c.some(d => d.id === 'pota') && !/^[A-Z]{1,4}-\d{4,5}$/.test(v.ref)) { errs.push('a POTA park number like US-1271'); $('smRef').classList.add('bad'); }
    if (errs.length) { alert('Please check ' + errs.join(', ') + '.'); return; }
    if (c.some(d => d.how === 'post') && !confirm(`This posts a real, public spot on POTA:\n\n${txt(v, 'plain')}\n\nOnly send it when you're on the air. Send it?`)) return;
    const out = [];
    $('smOut').hidden = false; $('smRes').innerHTML = row('todo', 'Sending…', 'One moment.');
    for (const d of c) {
      if (d.how === 'post' && d.id === 'pota') {
        try {
          const r = await fetch('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ activator: v.call, spotter: v.by, frequency: fk(v.k), reference: v.ref, mode: v.mode, source: 'KPC Spot Me', comments: v.cm }) });
          const body = await r.text().catch(() => '');
          if (r.ok) out.push(row('ok', '✓ POTA: spotted', `${esc(v.call)} at ${esc(v.ref)} on ${fm(v.k)} ${esc(v.mode)}. It shows on pota.app within a minute.`, `<a href="https://pota.app/#/" target="_blank" rel="noopener">SEE IT ›</a>`));
          else out.push(row('err', '✗ POTA said no', esc(String(body).replace(/^"|"$/g, '') || ('Error ' + r.status)) + '. Nothing was posted; fix it and press SEND again.', `<a href="https://pota.app/#/" target="_blank" rel="noopener">OPEN POTA</a>`));
        } catch (e) { out.push(row('err', '✗ POTA could not be reached', 'Check your signal and try again, or spot from the POTA site.', `<a href="https://pota.app/#/" target="_blank" rel="noopener">OPEN POTA</a>`)); }
      } else if (d.how === 'copy') {
        const t = txt(v, kindOf(d));
        out.push(row('todo', d.name, 'Tap to copy your spot and open the site, then paste it in.', `<button type="button" data-open="${d.id}">COPY + OPEN ›</button>`, `<p class="sm-msg">${esc(t)}</p>`));
      } else {
        out.push(row('todo', d.name, esc(d.about), `<a href="${esc(d.url)}" target="_blank" rel="noopener">OPEN ›</a>`));
      }
    }
    $('smRes').innerHTML = out.join('');
    $('smOut').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function init() {
    if (form.call) $('smCall').value = form.call; if (form.freq) $('smFreq').value = form.freq; if (form.mode) $('smMode').value = form.mode;
    if (form.prog) $('smProg').value = form.prog; if (form.ref) $('smRef').value = form.ref; if (form.by) $('smBy').value = form.by; if (form.cm) $('smCm').value = form.cm;
    $('smKeep').checked = keep;
    drawDests(); preview();
    ['smCall', 'smFreq', 'smRef', 'smBy', 'smCm'].forEach(id => $(id).addEventListener('input', preview));
    ['smMode'].forEach(id => $(id).addEventListener('change', preview));
    $('smProg').addEventListener('change', () => { fillRefs(); drawDests(); preview(); });
    $('smDests').addEventListener('change', e => { const b = e.target.closest('input[data-id]'); if (!b) return; if (b.checked) pick.add(b.dataset.id); else pick.delete(b.dataset.id); if ($('smKeep').checked) store.set('kpcSpotMePick', [...pick]); drawDests(); });
    $('smKeep').addEventListener('change', e => { if (e.target.checked) store.set('kpcSpotMePick', [...pick]); else store.del('kpcSpotMePick'); });
    $('smSend').addEventListener('click', send);
    $('smCopy').addEventListener('click', async () => { const v = val(); const ok = await copy(txt(v, 'plain')); $('smCopy').textContent = ok ? 'COPIED ✓' : 'COULD NOT COPY'; setTimeout(() => $('smCopy').textContent = 'COPY SPOT TEXT', 1800); });
    $('smRes').addEventListener('click', async e => { const b = e.target.closest('[data-open]'); if (!b) return; const d = ALL.find(x => x.id === b.dataset.open); const v = val(); await copy(txt(v, kindOf(d))); b.textContent = 'COPIED ✓ OPENING…'; window.open(d.url, '_blank', 'noopener'); setTimeout(() => b.textContent = 'COPY + OPEN AGAIN ›', 2500); });
    fetch('kpc-ky-data.json').then(r => r.json()).then(d => { (d.parks || []).forEach(p => REFS[p.c] = p.n); (d.summits || []).forEach(p => REFS[p.c] = p.n); (d.kff || []).forEach(p => REFS[p.c] = p.n); fillRefs(); preview(); }).catch(() => {});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();

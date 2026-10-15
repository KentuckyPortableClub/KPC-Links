/* KPC Spot Me (kpc-spot-me.html): one form, pick where your spot goes.
   Nothing is sent until the visitor ticks a destination and presses SEND.
   POTA only: posted from the browser to api.pota.app/spot/ (needs a real park number; spam guard 1 per 5 min, 4 per hour).
   Everything else: we copy a ready-made spot to the clipboard and open that site (they need their own login,
   or don't accept spots from other websites). */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const store = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }, del(k) { try { localStorage.removeItem(k); } catch (e) {} } };
  const BANDS = [[1800, 2000, '160m'], [3500, 4000, '80m'], [5330, 5410, '60m'], [7000, 7300, '40m'], [10100, 10150, '30m'], [14000, 14350, '20m'], [18068, 18168, '17m'], [21000, 21450, '15m'], [24890, 24990, '12m'], [28000, 29700, '10m'], [50000, 54000, '6m'], [144000, 148000, '2m'], [222000, 225000, '1.25m'], [420000, 450000, '70cm']];

  /* need = which number box it uses ('pota' | 'wwff' | 'sota' | 'any' | none); how: 'post' (POTA only: we send it, real park number required, max 1 per 5 min / 4 per hour per browser) | 'copy' (copy in that site's format + open it; the visitor submits there) | 'info' (just open). */
  const G = [
    ['SPOTTING SITES', [
      { id: 'pota', name: 'POTA (pota.app)', need: 'pota', how: 'post', url: 'https://pota.app/#/', about: 'Sends the spot to the POTA spots page right from here. A real park number is required, and only one spot every 5 minutes (4 an hour), so nobody can flood POTA.', tag: ['SENDS FOR YOU', 'one'] },
      { id: 'sotawatch', name: 'SOTAwatch', need: 'sota', how: 'copy', url: 'https://sotawatch.sota.org.uk/en/', about: 'Summit spots. Sign in with your free SOTA account, tap Post spot, and paste.', tag: ['COPY + OPEN'] },
      { id: 'wwff', name: 'WWFF Spotline', need: 'wwff', how: 'copy', url: 'https://spots.wwff.co/', about: 'KFF / WWFF spots. You need a Spotline login (WWFF approves new accounts by hand; use your call as the user name).', tag: ['COPY + OPEN'] },
      { id: 'gma', name: 'GMA (Global Mountain Activity)', need: 'sota', how: 'copy', url: 'https://www.cqgma.org/', about: 'GMA spots and alerts (uses the SOTA summit number). Sign in, then paste the spot.', tag: ['COPY + OPEN'] }
    ]],
    ['WEAK CELL SIGNAL AT THE PARK? (TEXT MESSAGE)', [
      { id: 'apspot', name: 'APSPOT (text message or APRS)', need: 'any', how: 'copy', url: 'https://apspot.radio', about: 'For parks with only a bar or two: a text message gets through when the internet won\'t. Text one line to APSPOT and it spots POTA, SOTA and WWFF for you. GET IT READY AT HOME: fill in the park and frequency, tap TEXT IT (one message per program) and save it as a draft in your messages (don\'t send it yet). At the park, fix the frequency if it changed and hit send. Save APSPOT\'s number from apspot.radio in your contacts first.', tag: ['TEXT IT'] }
    ]],
    ['PLAN AHEAD (SO HUNTERS KNOW YOU\'RE COMING)', [
      { id: 'potasch', name: 'POTA activation schedule', need: 'pota', how: 'info', url: 'https://pota.app/#/activations', about: 'Post when and where you\'ll be. On CW and FT8, POTA can then spot you automatically when the Reverse Beacon Network hears you.', tag: ['OPEN'] },
      { id: 'sotaalert', name: 'SOTAwatch alert', need: 'sota', how: 'info', url: 'https://sotawatch.sota.org.uk/en/', about: 'Post an alert for your planned summit and time.', tag: ['OPEN'] },
      { id: 'wwffag', name: 'WWFF agenda', need: 'wwff', how: 'info', url: 'https://spots.wwff.co/', about: 'Add your planned activation. With an agenda posted, Spotline can spot you automatically when the Reverse Beacon Network hears you.', tag: ['OPEN'] }
    ]],
    ['SPOT OTHERS: DX CLUSTER (FOR A STATION YOU HEARD)', [
      { id: 'dxsummit', name: 'DX Summit', how: 'copy', url: 'https://www.dxsummit.fi/', about: 'Big web DX cluster. The spot is copied in cluster format (frequency, call, comment) and the site opens; paste it and press submit.', tag: ['COPY + OPEN'], warn: 1, others: 1 },
      { id: 'holy', name: 'Holy Cluster', how: 'copy', url: 'https://holycluster.iarc.org', about: 'Map-style DX cluster run by IARC. Same worldwide cluster as DX Summit.', tag: ['COPY + OPEN'], warn: 1, others: 1 },
      { id: 'dxheat', name: 'DXHeat', how: 'copy', url: 'https://dxheat.com/dxc/', about: 'Web DX cluster with band filters. Same worldwide cluster as DX Summit.', tag: ['COPY + OPEN'], warn: 1, others: 1 }
    ]]
  ];
  const ALL = G.flatMap(g => g[1]);
  let pick = new Set((store.get('kpcSpotMePick', null) || []).filter(id => !['discord', 'fbgroup', 'pnp', 'sotamat'].includes(id)));
  const keep = store.get('kpcSpotMePick', null) !== null;
  const form = store.get('kpcSpotMeForm', {});

  const up = v => String(v || '').trim().toUpperCase().replace(/\s+/g, '');
  const callOk = c => /^([A-Z0-9]{1,4}\/)?[A-Z0-9]{1,3}\d{1,2}[A-Z]{1,4}(\/[A-Z0-9]{1,4})?$/.test(c);
  function khz() { let v = parseFloat(String($('smFreq').value).replace(',', '.')); if (!isFinite(v) || v <= 0) return null; if (v < 1000) v *= 1000; return Math.round(v * 10) / 10; }
  const band = k => { const b = BANDS.find(x => k >= x[0] && k <= x[1]); return b ? b[2] : ''; };
  const fk = k => (k % 1 ? k.toFixed(1) : String(k));
  const fm = k => (k / 1000).toFixed(3);
  const PROG = { pota: ['POTA', 'smPota', 'POTA park number like US-1271'], wwff: ['WWFF', 'smWwff', 'WWFF number like KFF-1271'], sota: ['SOTA', 'smSota', 'SOTA summit like W4K/EC-001'] };
  function val() {
    return { call: up($('smCall').value), by: up($('smBy').value) || up($('smCall').value), k: khz(), mode: $('smMode').value, pota: up($('smPota').value), wwff: up($('smWwff').value), sota: up($('smSota').value), cm: $('smCm').value.trim() };
  }
  const refsOf = v => ['pota', 'wwff', 'sota'].filter(p => v[p]).map(p => [PROG[p][0], v[p]]);
  function txt(v, kind, d) {
    let R = refsOf(v);
    if (d && d.need && d.need !== 'any') R = R.filter(r => r[0] === PROG[d.need][0]);
    const pg = R.map(r => r[0] === 'POTA' ? 'POTA ' + r[1] : r[1]).join(' ');
    if (kind === 'apspot') return R.map(r => `! ${r[0]} ${r[1]} ${v.k ? fm(v.k) : '?'} ${v.mode}${v.cm ? ' ' + v.cm : ''}`);
    if (kind === 'cluster') return `${v.k ? fk(v.k) : '?'} ${v.call} ${[v.mode, pg, v.cm].filter(Boolean).join(' ')}`.slice(0, 80);
    const nm = refName(v.pota) || refName(v.wwff) || refName(v.sota);
    return `${v.call} on ${v.k ? fm(v.k) + ' MHz' : '?'} ${v.mode}${pg ? ' · ' + pg : ''}${nm ? ' (' + nm + ')' : ''}${v.cm ? ' · ' + v.cm : ''}`;
  }
  const kindOf = d => d.id === 'apspot' ? 'apspot' : ['sotawatch', 'wwff', 'gma', 'dxsummit', 'holy', 'dxheat'].includes(d.id) ? 'cluster' : 'plain';
  let REFS = {};
  const refName = r => REFS[r] || '';
  /* POTA spam guard (this browser): one spot per 5 minutes, at most 4 an hour. */
  const RL = { gap: 5 * 6e4, hour: 4 };
  function rlCheck() { const t = Date.now(), L = (store.get('kpcSpotMeSent', []) || []).filter(x => t - x < 36e5);
    if (L.length && t - L[L.length - 1] < RL.gap) return 'Please wait ' + Math.ceil((RL.gap - (t - L[L.length - 1])) / 6e4) + ' more minute(s): one POTA spot every 5 minutes.';
    if (L.length >= RL.hour) return 'That\'s 4 POTA spots this hour. Try again in ' + Math.ceil((36e5 - (t - L[0])) / 6e4) + ' minute(s).'; return ''; }
  function rlNote() { const L = (store.get('kpcSpotMeSent', []) || []).filter(x => Date.now() - x < 36e5); L.push(Date.now()); store.set('kpcSpotMeSent', L); }
  const hasRef = (d, v) => !d.need || (d.need === 'any' ? refsOf(v).length > 0 : !!v[d.need]);
  const needTxt = d => d.need === 'any' ? 'a park, WWFF or summit number' : PROG[d.need][2];

  function drawDests() {
    const v = val();
    $('smDests').innerHTML = G.map(([h, list]) => { const oth = list.some(d => d.others);
      return `<div class="sm-g${oth ? ' sm-others' : ''}"><h3>${esc(h)}</h3>${oth ? '<p class="sm-onote">The DX cluster is for spotting <b>other</b> stations you hear. Put <b>their</b> call in the first box and yours in SPOTTED BY. Spotting yourself there is frowned on, except for special event stations.</p>' : ''}<div class="sm-list">` + list.map(d => {
      const on = pick.has(d.id), ok = hasRef(d, v);
      return `<label class="sm-d${on ? ' on' : ''}"><input type="checkbox" data-id="${d.id}"${on ? ' checked' : ''}><div><b>${esc(d.name)}</b><span>${esc(d.about)}</span>` +
        `<em class="${d.tag[1] || ''}">${esc(d.tag[0])}</em>${d.warn ? '<em class="warn">NOT FOR SELF-SPOTTING (EXCEPT SPECIAL EVENTS)</em>' : ''}${ok ? '' : `<em class="need">NEEDS A ${esc(needTxt(d).toUpperCase())} (BOX ABOVE)</em>`}</div></label>`;
    }).join('') + `</div></div>`; }).join('');
    count();
  }
  function chosen() { return ALL.filter(d => pick.has(d.id)); }
  function count() {
    const c = chosen();
    $('smN').textContent = c.length ? c.length + ' PICKED' : 'NOTHING PICKED YET';
    $('smSend').disabled = !c.length;
  }
  let lastDraw = '';
  function preview() {
    const v = val(), k = v.k;
    $('smBand').textContent = k ? (band(k) ? fm(k) + ' MHz · ' + band(k) : 'That is not inside a ham band. Check the frequency.') : '';
    ['pota', 'wwff', 'sota'].forEach(p => { const e = $(PROG[p][1] + 'Name'); if (e) e.textContent = refName(v[p]); });
    $('smPrev').textContent = v.call && k ? txt(v, 'plain') : 'Fill in the call and frequency';
    const sig = refsOf(v).map(r => r[0]).join(); if (sig !== lastDraw) { lastDraw = sig; drawDests(); }
    store.set('kpcSpotMeForm', { call: $('smCall').value, freq: $('smFreq').value, mode: v.mode, pota: $('smPota').value, wwff: $('smWwff').value, sota: $('smSota').value, by: $('smBy').value, cm: $('smCm').value });
  }
  /* A Kentucky park number also fills in its WWFF (KFF) number and names (never fills) a summit inside it (kpc-ky-data.json). */
  let PARK = {};
  function autoFill() {
    const p = PARK[up($('smPota').value)]; if (!p) return;
    const fill = !$('smWwff').value && p.kff && p.kff.length; if (fill) $('smWwff').value = p.kff[0];
    preview();
    if (fill) { $('smWwffName').textContent = refName(p.kff[0]) + ' · filled in from the park'; }
    if (!$('smSota').value && p.sota && p.sota.length) $('smSotaName').textContent = 'Summit in this park: ' + p.sota.join(', ') + ' (only fill it in if you are on the summit)';
  }
  function fillRefs() {
    const L = { pota: [], wwff: [], sota: [] };
    Object.entries(REFS).forEach(([c, n]) => { const o = `<option value="${esc(c)}">${esc(n)}</option>`; if (/^US-/.test(c)) L.pota.push(o); else if (/^KFF-/.test(c)) L.wwff.push(o); else if (/^W4K\//.test(c)) L.sota.push(o); });
    $('smPotaList').innerHTML = L.pota.join(''); $('smWwffList').innerHTML = L.wwff.join(''); $('smSotaList').innerHTML = L.sota.join('');
  }
  async function copy(t) { try { await navigator.clipboard.writeText(t); return true; } catch (e) { try { const a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select(); const ok = document.execCommand('copy'); a.remove(); return ok; } catch (x) { return false; } } }
  function row(cls, title, msg, btn, extra) { return `<div class="sm-r ${cls}"><div><b>${esc(title)}</b><p>${msg}</p>${extra || ''}</div>${btn || ''}</div>`; }

  async function send() {
    const v = val(), errs = [];
    ['smCall', 'smFreq', 'smPota', 'smWwff', 'smSota'].forEach(id => $(id).classList.remove('bad'));
    if (!callOk(v.call)) { errs.push('the station call sign'); $('smCall').classList.add('bad'); }
    if (!v.k || !band(v.k)) { errs.push('a frequency inside a ham band'); $('smFreq').classList.add('bad'); }
    const c = chosen();
    c.forEach(d => { if (!hasRef(d, v)) { const t = 'a ' + needTxt(d) + ' for ' + d.name; if (!errs.includes(t)) errs.push(t); if (d.need !== 'any') $(PROG[d.need][1]).classList.add('bad'); } });
    if (v.pota && !/^[A-Z0-9]{1,4}-\d{4,5}$/.test(v.pota)) { errs.push('the POTA park number (like US-1271)'); $('smPota').classList.add('bad'); }
    if (v.wwff && !/^[A-Z0-9]{1,4}FF-\d{4}$/.test(v.wwff)) { errs.push('the WWFF number (like KFF-1271)'); $('smWwff').classList.add('bad'); }
    if (v.sota && !/^[A-Z0-9]{1,4}\/[A-Z0-9]{2}-\d{3}$/.test(v.sota)) { errs.push('the SOTA summit (like W4K/EC-001)'); $('smSota').classList.add('bad'); }
    if (errs.length) { alert('Please check: ' + errs.join('; ') + '.'); return; }
    if (c.some(d => d.how === 'post')) {
      const wait = rlCheck(); if (wait && !c.some(d => d.how !== 'post')) { alert(wait); return; }
      if (!wait && !confirm(`This posts a real, public spot on POTA:\n\n${txt(v, 'plain', ALL.find(d => d.id === 'pota'))}\n\nOnly send it when you're on the air. Send it?`)) return;
    }
    const fc = c.find(d => d.how === 'copy' && d.id !== 'apspot'); if (fc) copy(txt(v, kindOf(fc), fc));
    const out = [];
    $('smOut').hidden = false;
    for (const d of c) {
      if (d.how === 'post' && d.id === 'pota') {
        const wait = rlCheck();
        if (wait) { out.push(row('err', 'POTA: not sent', esc(wait), `<a href="https://pota.app/#/" target="_blank" rel="noopener">OPEN POTA</a>`)); continue; }
        try {
          const r = await fetch('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ activator: v.call, spotter: v.by, frequency: fk(v.k), reference: v.pota, mode: v.mode, source: 'KPC Spot Me', comments: v.cm }) });
          const body = await r.text().catch(() => '');
          if (r.ok) { rlNote(); out.push(row('ok', '✓ POTA: spot sent', `${esc(v.call)} at ${esc(v.pota)} on ${fm(v.k)} ${esc(v.mode)}. It shows on pota.app within a minute. The next POTA spot can go out in 5 minutes.`, `<a href="https://pota.app/#/" target="_blank" rel="noopener">SEE IT ›</a>`)); }
          else out.push(row('err', '✗ POTA turned it down', esc(String(body).replace(/^"|"$/g, '') || ('Error ' + r.status)) + '. Nothing was sent. Fix it and try again.', `<a href="https://pota.app/#/" target="_blank" rel="noopener">OPEN POTA</a>`));
        } catch (e) { out.push(row('err', '✗ POTA could not be reached', 'Check your signal and try again, or send the spot from the POTA site.', `<a href="https://pota.app/#/" target="_blank" rel="noopener">OPEN POTA</a>`)); }
      } else if (d.how === 'copy') {
        const t = txt(v, kindOf(d), d);
        if (d.id === 'apspot') t.forEach((m, n) => out.push(row('todo', d.name + (t.length > 1 ? ' · ' + m.split(' ')[1] : ''), n ? 'One more message for this program.' : 'Tap TEXT IT: your messages app opens with the spot already written (one message per program). Pick your saved APSPOT contact and send it now, or leave it as a draft and send it when you get to the park. The same words also work as an APRS message to APSPOT.', `<a href="sms:?&body=${encodeURIComponent(m)}">TEXT IT ›</a>`, `<p class="sm-msg">${esc(m)}</p>`)));
        else out.push(row('todo', d.name, (d.others && v.call === v.by ? '⚠ This is your own call. On the DX cluster, only spot yourself if you are a special event station. ' : '') + 'Tap the button: the spot is copied and the site opens. Paste it in and press submit.', `<button type="button" data-open="${d.id}">COPY + OPEN ›</button>`, `<p class="sm-msg">${esc(t)}</p>`));
      } else {
        out.push(row('todo', d.name, esc(d.about), `<a href="${esc(d.url)}" target="_blank" rel="noopener">OPEN ›</a>`));
      }
    }
    $('smRes').innerHTML = out.join('');
    $('smOut').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function init() {
    if (form.call) $('smCall').value = form.call; if (form.freq) $('smFreq').value = form.freq; if (form.mode) $('smMode').value = form.mode;
    if (form.pota || (form.prog === 'POTA' && form.ref)) $('smPota').value = form.pota || form.ref; if (form.wwff) $('smWwff').value = form.wwff; if (form.sota) $('smSota').value = form.sota;
    if (form.by) $('smBy').value = form.by; if (form.cm) $('smCm').value = form.cm;
    $('smKeep').checked = keep;
    drawDests(); preview();
    ['smCall', 'smFreq', 'smPota', 'smWwff', 'smSota', 'smBy', 'smCm'].forEach(id => $(id).addEventListener('input', preview));
    $('smPota').addEventListener('change', autoFill);
    $('smMode').addEventListener('change', preview);
    $('smDests').addEventListener('change', e => { const b = e.target.closest('input[data-id]'); if (!b) return; if (b.checked) pick.add(b.dataset.id); else pick.delete(b.dataset.id); if ($('smKeep').checked) store.set('kpcSpotMePick', [...pick]); drawDests(); });
    $('smKeep').addEventListener('change', e => { if (e.target.checked) store.set('kpcSpotMePick', [...pick]); else store.del('kpcSpotMePick'); });
    $('smSend').addEventListener('click', send);
    $('smCopy').addEventListener('click', async () => { const v = val(); const ok = await copy(txt(v, 'plain')); $('smCopy').textContent = ok ? 'COPIED ✓' : 'COULD NOT COPY'; setTimeout(() => $('smCopy').textContent = 'COPY THE SPOT', 1800); });
    $('smRes').addEventListener('click', async e => { const b = e.target.closest('[data-open]'); if (!b) return; const d = ALL.find(x => x.id === b.dataset.open); const v = val(); await copy(txt(v, kindOf(d), d)); b.textContent = 'COPIED ✓ OPENING…'; window.open(d.url, '_blank', 'noopener'); setTimeout(() => b.textContent = 'COPY + OPEN AGAIN ›', 2500); });
    fetch('kpc-ky-data.json').then(r => r.json()).then(d => { (d.parks || []).forEach(p => { REFS[p.c] = p.n; PARK[p.c] = p; }); (d.summits || []).forEach(p => REFS[p.c] = p.n); (d.kff || []).forEach(p => REFS[p.c] = p.n); fillRefs(); preview(); }).catch(() => {});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();

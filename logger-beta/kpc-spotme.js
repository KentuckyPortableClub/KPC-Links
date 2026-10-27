/* KPC app: SPOT ME + RE-SPOT (Opus, Oct 25; Brandon: 'go ahead with the spotting for the 3 programs and respotting pota stations').
   POTA: api.pota.app/spot/ takes a spot from any program, no sign-in (what pota.app's own page, HAMRS and PoLo use):
     POST JSON {activator, spotter, frequency (kHz), reference, mode, source, comments}.
   SOTA: SOTAwatch only takes spots from a signed-in SOTA account (no open door for apps): the button opens SOTAwatch's spot page.
   WWFF: Spotline gives programs an API key on request (OH3CUF, spots.wwff.co/info): until KPC has one the button opens Spotline.
   QRM CHECK (the website's rule, kpc-links kpc-qrm.js): before a spot goes out, look for another activator spotted in the last 20 min
   close by — SSB ±3 kHz, AM ±6, FM ±10, CW / RTTY ±1, PSK ±0.5; FT8 / FT4 / FT2 / JS8 never warn (everyone shares the same spot).
   A practice call (K4TEST) never spots. Opened from the CALL box (SPOTME / QRV / QSY / QRT), the 📣 chip on the LOG screen, or a spot's sheet. */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id), esc = AP && AP.esc;
  if (!AP) return;
  const QRMK = { SSB: 3, USB: 3, LSB: 3, AM: 6, FM: 10, CW: 1, RTTY: 1, PSK31: 0.5, PSK63: 0.5, PSK: 0.5 };
  const noQrm = m => /^(FT8|FT4|FT2|JS8|WSPR|FST4|Q65)$/.test(m);
  const sigOf = r => /^[A-Z0-9]*FF-/.test(r) ? 'WWFF' : /^[A-Z0-9]+\/[A-Z]{2}-\d{3}$/.test(r) ? 'SOTA' : 'POTA';
  const modeOut = m => { m = String(m || '').toUpperCase(); return /^(USB|LSB|SSB|PHONE)$/.test(m) ? 'SSB' : /^(PSK31|PSK63|PSK125)$/.test(m) ? 'PSK31' : m; };
  function where() {
    const L = G.KPCLog, d = L ? L.dock : { khz: 14074, mode: 'FT8' }, md = G.KPCModes && KPCModes.active(), dm = String(d.mode || '').toUpperCase();
    /* FT8 / the digital screens: their own dial (+ my TX audio for FT8 the way POTA lists it: the dial) */
    if (md && /^(FT8|FT4|CW|RTTY|PSK31|SSTV)$/.test(md.id) && document.body.dataset.screen === 'digi') return { khz: md.khz(), mode: md.id === 'PSK31' ? 'PSK31' : md.id };
    return { khz: +d.khz || 0, mode: dm };
  }
  function qrmNear(khz, mode, me) {
    if (noQrm(mode) || !G.KPCSpots) return [];
    const w = QRMK[mode] || 3, cut = Date.now() - 20 * 60000;
    return KPCSpots.all().filter(s => s.t >= cut && s.call !== me && s.refs && s.refs.length && Math.abs(s.khz - khz) <= w && !noQrm(String(s.mode || '').toUpperCase()));
  }
  async function postPota(o) {
    const body = JSON.stringify({ activator: o.activator, spotter: o.spotter, frequency: String(Math.round(o.khz * 10) / 10), reference: o.ref, mode: o.mode, source: 'KPC app', comments: o.comment || '' });
    const r = await AP.net.raw('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, ms: 12000 });
    if (!r || !r.ok) throw new Error((r && (r.err || ('POTA answered ' + r.status))) || 'no answer');
    return true;
  }
  function sheet(word, re) {
    const me = AP.myCall(), w = where();
    const refs = re ? (re.refs || []) : (G.KPCLog ? KPCLog.refList(AP.S.ref || '') : []);
    const act = re ? re.call : me, khz = re ? re.khz : w.khz, mode = modeOut(re ? re.mode : w.mode);
    const progs = [...new Set(refs.map(sigOf))];
    const bad = !me ? 'Put your call sign in STATION → My station first.' : !AP.stdCall(me) ? 'Spotting needs your real call sign (a practice call like K4TEST must never be spotted).' : !refs.length ? (re ? 'That spot has no park number.' : 'Put your park number in first (the 🌲 MY PARK chip on the LOG screen).') : !(khz > 100) ? 'No frequency yet: set the band / frequency on the LOG screen chip.' : '';
    const near = bad || re ? [] : qrmNear(khz, mode, me);
    const dflt = re ? 'TU' : word === 'QRT' ? 'QRT, thanks all' : word === 'QSY' ? 'QSY' : word === 'QRV' ? 'QRV' : '';
    AP.sheet(re ? '📣 Re-spot ' + esc(act) : '📣 Spot me', `
      ${bad ? `<p class="bad">${esc(bad)}</p>` : `<p><b>${esc(act)}</b> · ${esc((khz / 1000).toFixed(3))} MHz ${esc(mode)} · ${esc(refs.join(' + '))}</p>`}
      ${near.length ? `<p class="bad">⚠ Someone else is close: ${near.slice(0, 3).map(s => `<b>${esc(s.call)}</b> ${esc((s.khz / 1000).toFixed(3))} ${esc(s.mode || '')} (${esc(s.refs.join('+'))}, ${Math.round((Date.now() - s.t) / 60000)} min ago)`).join(' · ')}. Move a little before you spot, or spot anyway.</p>` : ''}
      <div class="grid2"><label class="e">FREQUENCY (kHz)<input id="smKhz" inputmode="decimal" value="${esc(String(khz || ''))}"></label><label class="e">MODE<input id="smMode" autocapitalize="characters" value="${esc(mode)}"></label></div>
      <label class="e wide">COMMENT<input id="smCom" maxlength="60" value="${esc(dflt)}" placeholder="optional: QRV, QRT, 2-fer…"></label>
      <div class="row">${progs.includes('POTA') || !progs.length ? `<button type="button" class="b gold" id="smPota"${bad ? ' disabled' : ''}>📣 SPOT ON POTA</button>` : ''}
        ${progs.includes('SOTA') ? '<button type="button" class="b" id="smSota">⛰ SOTAWATCH ›</button>' : ''}${progs.includes('WWFF') ? '<button type="button" class="b" id="smWwff">🌳 WWFF SPOTLINE ›</button>' : ''}</div>
      <p class="hint">POTA spots go straight in. SOTAwatch takes spots only from a signed-in SOTA account and WWFF only from programs with a Spotline key, so those two buttons open their spot page in the browser for now.${re ? ' A re-spot tells the hunters this station is still on the air there.' : ''}</p>`);
    const go = async () => {
      const k = parseFloat($('smKhz').value), m = modeOut($('smMode').value), com = $('smCom').value.trim();
      const pr = refs.filter(r => sigOf(r) === 'POTA'); if (!pr.length) { AP.toast('No POTA park number to spot.', 3000, 'bad'); return; }
      if (!AP.net.online()) { AP.toast('No signal right now: the spot did not go out.', 4000, 'bad'); return; }
      $('smPota').disabled = true; $('smPota').textContent = 'Sending…';
      try { for (const ref of pr) await postPota({ activator: act, spotter: me, khz: k, ref, mode: m, comment: com }); AP.shut(); AP.toast('📣 Spotted on POTA: ' + esc(act) + ' ' + (k / 1000).toFixed(3) + ' ' + esc(m) + ' ' + esc(pr.join(' + ')), 4000, 'log'); LAST = { t: Date.now(), khz: k };
        if (G.KPCSpots && KPCSpots.feed) KPCSpots.feed('own', [{ call: act, khz: k, mode: m, refs: pr, comment: com, spotter: me, t: Date.now() }]); }
      catch (e) { $('smPota').disabled = false; $('smPota').textContent = '📣 SPOT ON POTA'; AP.toast('The spot did not go: ' + esc(e.message || e), 5000, 'bad'); }
    };
    if ($('smPota')) $('smPota').onclick = go;
    if ($('smSota')) $('smSota').onclick = () => G.open('https://sotawatch.sota.org.uk/en/', '_blank');
    if ($('smWwff')) $('smWwff').onclick = () => G.open('https://spots.wwff.co/', '_blank');
  }
  let LAST = null;
  /* the 📣 chip on the LOG dock (activating only) */
  const chips = $('lgDock') && $('lgDock').querySelector('.chips');
  if (chips && !$('dkSpot')) { const p = $('dkP2p'); (p || chips.lastElementChild).insertAdjacentHTML('beforebegin', '<button type="button" class="chip" id="dkSpot" title="Spot me on POTA (QRM check first)">📣 SPOT ME</button>'); $('dkSpot').onclick = () => sheet(''); }
  const showChip = () => { const c = $('dkSpot'); if (c) c.hidden = AP.me().hunt; };
  AP.on('me', showChip); showChip();
  G.KPCSpotMe = { sheet: w => sheet(w), respot: s => sheet('', s), qrmNear, last: () => LAST, _post: postPota };
})(window);

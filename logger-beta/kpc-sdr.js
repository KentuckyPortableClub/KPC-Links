/* KPC app: 📻 THE BLACK SDR RADIO PAGE (Nov 18 2026; Brandon approved the mockup 'KPC Radio Screen — SDR-style mockup', Nov 17:
   'make the radio black and the buttons look like they are illuminated', 'nailed the waterfall … go back to black'; Nov 18: 'give me all
   the options more buttons', 'needs a power button', 'when button on or off does the light turn on and off?', XIT, WPM, clarifier, a
   SIMPLE / FULL switch). Builds on the RADIO tab (kpc-radio.js), the 🎛 MORE CONTROLS (kpc-rigx.js) and the 🌊 SCOPE (kpc-scope.js): the
   same working controls, a new front panel and a black, lit look.
   - FRONT PANEL: ⏻ POWER (green and lit = the radio is on and talking to the app; dark red = not), the radio's name + how it is linked,
     UTC, and SIMPLE | FULL. SIMPLE = frequency, bands, modes, the waterfall, meters, talk. FULL = every control the radio takes.
   - VFO A big, with a BAND PLAN STRIP under it (what YOUR licence class may use, a marker where you are); VFO B / SPLIT; A ⇄ B, A = B,
     SPLIT, CLAR (RIT) and XIT with − / + offset and CLEAR, keyer WPM − / +. Only what THIS radio takes over CAT shows (KPCCat.caps()).
   - M1–M6 MEMORIES (kept in the app, any radio): tap an empty one = store here; tap a full one = go there; ✎ STORE then a button = store
     over it. Band buttons get a coloured line: today's rule-of-thumb opening (green open / amber fair / grey closed, KPCProp).
   - LIGHTS: the whole page dims and the buttons go dark when the radio is not connected; lit buttons glow when ON.
   Settings: localStorage kpcAppSdr. */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id); if (!AP || !G.KPCCat) return;
  const K = G.KPCCat, esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const S = Object.assign({ view: 'full', mem: [null, null, null, null, null, null] }, LS('kpcAppSdr', {}));
  if (!Array.isArray(S.mem) || S.mem.length !== 6) S.mem = [null, null, null, null, null, null];
  const save = () => SV('kpcAppSdr', S);
  let STORE = false, LASTB = 0;
  const scr = $('scrRadio'); if (!scr) return;
  scr.classList.add('sdr');

  /* VFO B: the radio does not tell the app, so the app shows what IT set last (split from a spot, A = B) */
  if (K.splitTx && !K.splitTx._sdr) { const f0 = K.splitTx; K.splitTx = function (khz) { LASTB = +khz || 0; return f0.apply(this, arguments); }; K.splitTx._sdr = 1; }

  /* ---------------- the front panel ---------------- */
  scr.insertAdjacentHTML('afterbegin', `<div class="sdrhead" id="sdrHead">
      <button type="button" class="sdrpwr" id="sdrPwr" aria-label="Radio power" title="Radio power: lit green = on and connected">⏻</button>
      <div class="sdrid"><b id="sdrRig">—</b><i id="sdrLink">not connected</i></div>
      <div class="sdrclk"><i>UTC</i><b id="sdrUtc">--:--</b></div>
      <div class="sdrsw" role="group" aria-label="How much to show"><button type="button" data-sdrv="simple">SIMPLE</button><button type="button" data-sdrv="full">FULL</button></div>
    </div>`);
  const top = scr.querySelector('.rdtop'), vfo = scr.querySelector('.rdvfo');
  if (vfo && !$('sdrVfo2')) vfo.insertAdjacentHTML('afterend', `<div class="sdrvfo2" id="sdrVfo2">
      <div class="sdrplan" id="sdrPlan" aria-label="Band plan for your licence class"></div>
      <div class="sdrbrow"><span class="sdrlab">VFO B</span><b id="sdrB">—</b><i id="sdrSplit">SPLIT OFF</i></div>
      <div class="sdrkeys" id="sdrKeys">
        <button type="button" class="lit" data-sk="swap" title="Swap VFO A and B">A ⇄ B</button>
        <button type="button" class="lit" data-sk="ab" title="Copy A to B (same mode and filter)">A = B</button>
        <button type="button" class="lit" data-sk="split">SPLIT</button>
        <button type="button" class="lit" data-sk="rit" title="Clarifier / RIT: move what you hear, not what you send">CLAR</button>
        <button type="button" class="lit" data-sk="xit" title="XIT: move what you send, not what you hear">XIT</button>
        <span class="sdroff" id="sdrOffW"><button type="button" class="lit sm" data-sko="-1">−</button><b id="sdrOff">0 Hz</b><button type="button" class="lit sm" data-sko="1">+</button><button type="button" class="lit sm" data-sko="0">CLEAR</button></span>
        <span class="sdrwpm" id="sdrWpmW"><span class="sdrlab">WPM</span><button type="button" class="lit sm" data-skw="-1">−</button><b id="sdrWpm">22</b><button type="button" class="lit sm" data-skw="1">+</button></span>
      </div>
      <div class="sdrmem" id="sdrMem"></div>
    </div>`);

  const rx = () => (G.KPCRigX ? KPCRigX.X : {});
  const caps = () => { const C = K.caps ? K.caps() : { keys: [] }, ex = K.extras ? K.extras() : []; return k => C.keys.includes(k) && ex.includes(k); };
  const mhz = k => k > 0 ? (k / 1000).toFixed(3) : '—';
  function planHtml(khz) {
    const band = (G.KPCLog && KPCLog.band(khz)) || '';
    const segs = AP.bandPlan ? AP.bandPlan.segments(AP.S.cls || 'E') : [];
    const EDGE = { '160m': [1800, 2000], '80m': [3500, 4000], '60m': [5330, 5407], '40m': [7000, 7300], '30m': [10100, 10150], '20m': [14000, 14350], '17m': [18068, 18168], '15m': [21000, 21450], '12m': [24890, 24990], '10m': [28000, 29700], '6m': [50000, 54000], '2m': [144000, 148000] };
    const e = EDGE[band]; if (!e) return '<span class="sdrpoff">Out of the ham bands</span>';
    const [lo, hi] = e, W = hi - lo, pct = k => ((k - lo) / W * 100).toFixed(2);
    const in_ = segs.filter(s => s[1] > lo && s[0] < hi).map(s => [Math.max(lo, s[0]), Math.min(hi, s[1]), s[3]]).sort((a, b) => a[0] - b[0])
      .reduce((a, s) => { const p = a[a.length - 1]; if (p && p[2] === s[2] && s[0] <= p[1] + 0.01) p[1] = Math.max(p[1], s[1]); else a.push(s.slice()); return a; }, []);
    return in_.map(s => `<i class="sp k-${esc(s[2])}" style="left:${pct(s[0])}%;width:${((s[1] - s[0]) / W * 100).toFixed(2)}%"></i>`).join('')
      + (khz >= lo && khz <= hi ? `<b class="sdrmk" style="left:${pct(khz)}%"></b>` : '')
      + `<span class="sdre l">${(lo / 1000).toFixed(3)}</span><span class="sdre r">${(hi / 1000).toFixed(3)}</span>`;   /* edges inside the strip */
  }
  function memHtml() {
    return S.mem.map((m, i) => `<button type="button" class="lit mem${m ? ' full' : ''}" data-sm="${i}" title="${m ? 'Go to ' + mhz(m.khz) + ' ' + esc(m.mode || '') : 'Empty: tap to store here'}"><b>M${i + 1}</b><small>${m ? mhz(m.khz) + ' ' + esc(m.mode || '') : 'empty'}</small></button>`).join('')
      + `<button type="button" class="lit mem store${STORE ? ' on' : ''}" id="sdrStore" title="Then tap M1–M6 to store the frequency there">✎ STORE</button>`;
  }
  /* band buttons: today's opening as a coloured line (rule of thumb from flux / Kp / day or night, the CONDITIONS tab's table) */
  function bandLines() {
    const P = G.KPCProp, sun = LS('kpcAppSun', null); if (!P || !P.bands) return;
    const me = AP.gridLL && AP.gridLL(AP.myGrid()), day = me && P.elev ? P.elev(me.la, me.lo, Date.now()) > -0.833 : (h => h >= 7 && h < 19)(new Date().getHours());
    const g = P.bands(sun && sun.sfi, sun && sun.kp, day) || {};
    document.querySelectorAll('#rdBands [data-rband]').forEach(b => { const q = g[b.dataset.rband]; b.classList.remove('q0', 'q1', 'q2'); if (q != null) b.classList.add('q' + q); });
  }
  /* Nov 19 2026 (Brandon: 'make it look real … all the bells and whistles … full screen usage tablet and desk top … phone make it work
     best you can'; the approved mockup + the MODERN meters). THREE layouts, the same controls (every element keeps its id, only its
     place changes, so kpc-radio / kpc-rigx / kpc-scope / kpc-nr / kpc-voice keep working):
     · FIT (window ≥ 1100 x 600): LEFT = band, mode, memories, voice keyer, spots on this band; MIDDLE = the VFO panel, the meters, the
       scope filling the height left; RIGHT = receive / transmit / CW / more controls (scrolls on its own), HOLD TO TALK pinned at its foot.
     · PHONE (< 700 px): one column: VFO + meters (under the frequency) → scope → a thumb bar (TUNE + HOLD TO TALK) → bands, modes … the rest.
     · in between (small laptop, tablet upright): two columns as before (VFO + scope | the controls). */
  const wantFit = () => innerWidth >= 1100 && innerHeight >= 600 && document.body.dataset.screen === 'radio' && $('rdOn') && !$('rdOn').hidden;
  function panel(id, title, el, hint) {   /* a left-column panel around an existing element */
    let c = $(id); if (!c) { c = document.createElement('div'); c.className = 'card sdrcard'; c.id = id; c.innerHTML = `<h2>${title}</h2>` + (hint ? `<p class="hint sdrph">${hint}</p>` : ''); }
    if (el && el.parentNode !== c) c.insertBefore(el, c.querySelector('.sdrph')); return c;
  }
  function layout() {
    const on = $('rdOn'); if (!on) return;
    let L = $('sdrL'), R = $('sdrR'), A = $('sdrA');
    if (!L) { on.insertAdjacentHTML('afterbegin', '<div class="sdrcol" id="sdrA"></div><div class="sdrcol" id="sdrL"></div><div class="sdrcol" id="sdrR"></div>'); L = $('sdrL'); R = $('sdrR'); A = $('sdrA'); }
    if (!A) { L.insertAdjacentHTML('beforebegin', '<div class="sdrcol" id="sdrA"></div>'); A = $('sdrA'); }
    const t = on.querySelector('.rdtop'), sc = $('rdScope');
    if (t && t.parentNode !== L) L.prepend(t);
    if (sc && sc.parentNode !== L) L.appendChild(sc);
    [...on.children].forEach(c => { if (c !== L && c !== R && c !== A) R.appendChild(c); });
    const F = wantFit(), narrow = innerWidth < 700, met = on.querySelector('.rdmet'), grid = on.querySelector('.rdgrid'), vf = t && t.querySelector('.rdvfo');
    const bands = $('rdBands'), modes = $('rdModes'), spots = $('rdSpots'), steps = $('rdSteps'), mem = $('sdrMem'), vk = $('rdVk'), vmc = $('rdVmod'), v2 = $('sdrVfo2');
    if (F) {   /* LEFT column, then the MIDDLE: VFO, meters, scope (a short window: the meters go to the top of the RIGHT column so the scope keeps its room) */
      const want = [panel('sdrCBand', 'Band', bands, 'The coloured line under a band = today\'s opening.'), panel('sdrCMode', 'Mode', modes), panel('sdrCStep', 'Tuning step', steps),
        panel('sdrCMem', 'Memories', mem), (c => { if (vk && vk.parentNode !== c) c.appendChild(vk); return c; })(panel('sdrCVk', 'Voice keyer', vmc)), panel('sdrCSp', 'Spots on this band', spots)].filter(c => c.querySelector('[id^="rd"],[id^="sdr"]'));
      want.forEach((c, i) => { if (A.children[i] !== c) A.insertBefore(c, A.children[i] || null); });
      if (met) { if (innerHeight < 900) { if (R.firstElementChild !== met) R.prepend(met); } else if (t && met.previousElementSibling !== t) t.after(met); }
    } else {   /* everything back home */
      if (steps && t && steps.parentNode !== t) (v2 && v2.parentNode === t ? v2 : vf || t.firstElementChild).after(steps);
      if (steps && bands && bands.previousElementSibling !== steps) steps.after(bands);
      if (bands && modes && modes.previousElementSibling !== bands) bands.after(modes);
      if (modes && spots && spots.previousElementSibling !== modes) modes.after(spots);
      if (v2 && mem && mem.parentNode !== v2) v2.appendChild(mem);
      if (vk && $('sdrCVk') && vk.parentNode === $('sdrCVk')) { const lv = $('rdLv'); if (lv && lv.parentNode === R) R.insertBefore(vk, lv); else R.appendChild(vk); }
      if (vk && vmc && vmc.nextElementSibling !== vk) vk.before(vmc);   /* the voice chip sits just above the voice keyer */
      if (met && vf) { if (narrow && met.previousElementSibling !== vf) vf.after(met); else if (!narrow && grid && met.parentNode !== grid) grid.appendChild(met); }
    }
    /* the phone's thumb bar under the scope: the real TUNE and HOLD TO TALK buttons move there (the same buttons, the same safety).
       Never moved while talking or sending: moving a held button drops its pointer and would END the transmission early. */
    const tune = $('rdTune'), talk = $('rdTalk'), big = on.querySelector('.rdbig'), voice = $('rdVoice');
    if (talk && (talk.classList.contains('on') || (AP.txing && AP.txing()))) return;
    let pb = $('sdrThumb');
    if (narrow && sc && sc.parentNode === L) {
      if (!pb) { pb = document.createElement('div'); pb.className = 'sdrthumb'; pb.id = 'sdrThumb'; }
      if (pb.previousElementSibling !== sc) sc.after(pb);
      if (tune && tune.parentNode !== pb) pb.appendChild(tune);
      if (talk && talk.parentNode !== pb) pb.appendChild(talk);
      [...pb.children].forEach(c => { if (c !== tune && c !== talk) { if (voice && voice.parentNode === R) R.insertBefore(c, voice); else R.appendChild(c); } });   /* e.g. the noise-reduction card kpc-nr puts right before HOLD TO TALK */
    } else {   /* home: TUNE first in the big-button row, HOLD TO TALK just above the voice choices (FIT pins it to the foot with CSS) */
      if (tune && big && tune.parentNode !== big) big.prepend(tune);
      if (talk && voice && voice.parentNode === R && talk.nextElementSibling !== voice) R.insertBefore(talk, voice);
      else if (talk && talk.parentNode !== R && !(voice && voice.parentNode === R)) R.appendChild(talk);
      if (pb) pb.remove();
    }
  }
  function fit() {
    const on = $('rdOn'), ok = wantFit();
    scr.classList.toggle('fit', !!ok); if (!ok) return;
    const tb = document.querySelector('nav.tabs'), bot = tb && getComputedStyle(tb).position === 'fixed' ? tb.getBoundingClientRect().top : innerHeight;
    const h = Math.max(380, Math.floor(bot - (on.getBoundingClientRect().top + scrollY) - 34));   /* from the page top; room for the foot line */
    scr.style.setProperty('--fitH', h + 'px');
  }
  addEventListener('resize', () => { if (document.body.dataset.screen === 'radio') { layout(); fit(); } });
  /* the VFO readout line (what a radio's own screen shows under the frequency) */
  function exLine() {
    const e = $('sdrEx'); if (!e) return; const x = rx(), can = caps(), st = document.querySelector('#rdSteps .on'), wd = $('rdWidth');
    const off = +x.ritoff || 0, items = [];
    if (can('rit') || can('ritoff')) items.push(['CLAR', x.rit || off ? (off > 0 ? '+' : '') + off + ' Hz' : 'off']);
    if (can('xit')) items.push(['XIT', x.xit ? 'on' : 'off']);
    if (st) items.push(['STEP', st.textContent.trim()]);
    if (wd && wd.options.length && wd.selectedIndex >= 0 && wd.offsetParent) items.push(['FIL', wd.options[wd.selectedIndex].text]);
    if (can('split')) items.push(['SPLIT', x.split ? 'ON' : 'off']);
    const h = items.map(([k, v]) => `<span>${k} <em>${esc(String(v))}</em></span>`).join('');
    if (e.dataset.k !== h) { e.innerHTML = h; e.dataset.k = h; }
  }
  /* the knob: drag up / down (or the wheel, or the arrow keys) = tune; it only sends the SAME wheel step the frequency readout already takes */
  { const vf = scr.querySelector('.rdvfo'), kz = $('rdKhz');
    if (vf && kz && !$('sdrKnob')) {
      vf.insertAdjacentHTML('beforeend', '<div class="sdrknob" id="sdrKnob" role="slider" aria-label="Tuning knob: drag up or down, the mouse wheel or the arrow keys" tabindex="0"><i></i></div>');
      const kb = $('sdrKnob'); let y0 = null, acc = 0, ang = 0;
      const turn = d => { kz.dispatchEvent(new WheelEvent('wheel', { deltaY: d > 0 ? -1 : 1, bubbles: true, cancelable: true })); ang += d > 0 ? 15 : -15; kb.style.setProperty('--a', ang + 'deg'); };
      kb.addEventListener('pointerdown', e => { y0 = e.clientY; acc = 0; try { kb.setPointerCapture(e.pointerId); } catch (x) {} });
      kb.addEventListener('pointermove', e => { if (y0 == null) return; acc += y0 - e.clientY; y0 = e.clientY; while (Math.abs(acc) >= 12) { turn(acc); acc -= Math.sign(acc) * 12; } });
      kb.addEventListener('pointerup', () => { y0 = null; }); kb.addEventListener('pointercancel', () => { y0 = null; });
      kb.addEventListener('wheel', e => { e.preventDefault(); turn(-e.deltaY); }, { passive: false });
      kb.addEventListener('keydown', e => { const k = e.key; if (k === 'ArrowUp' || k === 'ArrowRight') { e.preventDefault(); turn(1); } else if (k === 'ArrowDown' || k === 'ArrowLeft') { e.preventDefault(); turn(-1); } });
    } }
  { const p = $('sdrPlan'); if (p && !$('sdrEx')) p.insertAdjacentHTML('beforebegin', '<div class="sdrex" id="sdrEx"></div>'); }
  /* the head: local time, RX / TX lights, FULL SCREEN; the foot: how many stations the scope names */
  { const ck = scr.querySelector('.sdrclk');
    if (ck && !$('sdrLoc')) ck.insertAdjacentHTML('afterend', '<div class="sdrclk sdrloc"><i>LOCAL</i><b id="sdrLoc">--:--</b></div><div class="sdrleds"><span><u id="sdrRx"></u><i>RX</i></span><span><u id="sdrTx"></u><i>TX</i></span></div><button type="button" class="sdrfs" id="sdrFs" title="Full screen (Esc to come back)">⛶ FULL</button>');
    if ($('sdrFs')) $('sdrFs').onclick = () => { if (document.fullscreenElement) document.exitFullscreen(); else if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen().catch(() => AP.toast('Full screen is not allowed here: use F11.', 3000)); };
    if (!$('sdrFoot')) scr.insertAdjacentHTML('beforeend', '<div class="sdrfoot" id="sdrFoot"></div>'); }
  function headLive() {
    const d = new Date(); if ($('sdrLoc')) $('sdrLoc').textContent = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    const on = K.connected(), tx = !!(AP.txing && AP.txing());
    if ($('sdrRx')) $('sdrRx').className = on && !tx ? 'on' : ''; if ($('sdrTx')) $('sdrTx').className = tx ? 'tx' : '';
    const n = G.KPCScope && KPCScope.tags ? KPCScope.tags() : 0, f = $('sdrFoot');
    if (f) { const t = on && !$('rdOn').hidden ? `<b>ON THE SCOPE</b> ${n} station${n === 1 ? '' : 's'} named from spots · tap a name tag = tune there + fill the log` : ''; if (f.dataset.k !== t) { f.innerHTML = t; f.dataset.k = t; } }
  }
  setInterval(() => { if (document.body.dataset.screen === 'radio') { headLive(); exLine(); } }, 500);
  function draw() {
    layout(); fit();
    const on = K.connected(), r = G.KPCRadio ? KPCRadio.rig() : { khz: 0, mode: '' }, x = rx(), can = caps(), cg = K.get ? K.get() : {};
    scr.classList.toggle('lit', on); scr.dataset.view = S.view;
    $('sdrPwr').classList.toggle('on', on); $('sdrPwr').title = on ? 'The radio is ON and connected: tap to turn it off' : 'Not connected: tap to connect or turn the radio on';
    const nm = (K.RADIO && cg.radio && K.RADIO[cg.radio] && K.RADIO[cg.radio].name) || (cg.radio || '').toUpperCase() || 'No radio picked';
    $('sdrRig').textContent = nm; $('sdrLink').textContent = on ? (K.link ? ({ serial: 'USB cable', rigctld: 'rigctld', flrig: 'flrig', fake: 'pretend radio' }[K.link()] || K.link()) + ' · CAT' : 'CAT') : 'not connected';
    $('sdrUtc').textContent = new Date().toISOString().slice(11, 16);
    document.querySelectorAll('[data-sdrv]').forEach(b => b.classList.toggle('on', b.dataset.sdrv === S.view));
    if (!$('sdrVfo2')) return;
    $('sdrPlan').innerHTML = planHtml(r.khz);
    const split = !!x.split; $('sdrSplit').textContent = split ? 'SPLIT ON · you transmit on B' : 'SPLIT OFF'; $('sdrSplit').classList.toggle('on', split);
    $('sdrB').textContent = split && LASTB ? mhz(LASTB) : split ? 'the radio\'s B' : '—';
    const keys = { swap: can('swap'), ab: can('ab'), split: can('split'), rit: can('rit') || can('ritoff'), xit: can('xit') };
    document.querySelectorAll('#sdrKeys [data-sk]').forEach(b => { const k = b.dataset.sk; b.hidden = !keys[k]; b.classList.toggle('on', !!x[k]); });
    $('sdrOffW').hidden = !can('ritoff'); $('sdrOff').textContent = ((+x.ritoff || 0) > 0 ? '+' : '') + (+x.ritoff || 0) + ' Hz';
    $('sdrWpmW').hidden = !can('keyspd'); $('sdrWpm').textContent = +x.keyspd || 22;
    const mh = memHtml(); if ($('sdrMem').dataset.k !== mh) { $('sdrMem').innerHTML = mh; $('sdrMem').dataset.k = mh; }
    bandLines();
  }
  async function send(k, v, label) {
    if (!G.KPCRigX) return false; const X = KPCRigX.X;
    if (['split', 'rit', 'xit', 'keyspd', 'ritoff', 'vox', 'comp', 'mon'].includes(k)) { X[k] = v; KPCRigX.save(); }
    const ok = await KPCRigX.go(k, v, label); if (KPCRigX.draw) KPCRigX.draw(); draw(); return ok;
  }
  scr.addEventListener('click', e => {
    const v = e.target.closest('[data-sdrv]'); if (v) { S.view = v.dataset.sdrv; save(); draw(); AP.toast(S.view === 'full' ? 'FULL: every control this radio takes.' : 'SIMPLE: frequency, bands, modes, the waterfall, meters, talk.', 2200); return; }
    const k = e.target.closest('[data-sk]'); if (k) { const n = k.dataset.sk, X = rx();
      if (n === 'swap' || n === 'ab') { send(n, 1, n === 'swap' ? 'A ⇄ B' : 'A = B'); if (n === 'ab') LASTB = (G.KPCRadio && KPCRadio.rig().khz) || LASTB; return; }
      if (n === 'rit' && !caps()('rit')) { send('ritoff', 0, 'CLAR clear'); return; }   /* the newest Yaesu: CLAR = the offset itself */
      send(n, X[n] ? 0 : 1); return; }
    const o = e.target.closest('[data-sko]'); if (o) { const X = rx(), st = +X.ritstep || 50, d = +o.dataset.sko; send('ritoff', d ? Math.max(-9990, Math.min(9990, (+X.ritoff || 0) + d * st)) : 0); return; }
    const w = e.target.closest('[data-skw]'); if (w) { const X = rx(); send('keyspd', Math.max(6, Math.min(48, (+X.keyspd || 22) + +w.dataset.skw))); return; }
    if (e.target.closest('#sdrStore')) { STORE = !STORE; draw(); if (STORE) AP.toast('✎ Now tap M1–M6 to store ' + mhz((G.KPCRadio && KPCRadio.rig().khz) || 0) + ' there.', 3000); return; }
    const m = e.target.closest('[data-sm]'); if (m) { const i = +m.dataset.sm, r = G.KPCRadio ? KPCRadio.rig() : {};
      if (STORE || !S.mem[i]) { if (!(r.khz > 0)) { AP.toast('No frequency yet: connect the radio first.', 2500, 'bad'); return; } S.mem[i] = { khz: r.khz, mode: r.mode || '' }; save(); STORE = false; draw(); AP.toast('M' + (i + 1) + ' = ' + mhz(r.khz) + ' ' + esc(r.mode || ''), 2000, 'log'); return; }
      if (G.KPCRadio) KPCRadio.tuneTo(S.mem[i].khz, S.mem[i].mode); return; }
    if (e.target.closest('#sdrPwr')) { power(); return; }
  });
  function power() {
    if (K.connected()) { const b = $('rdPwrOff'); if (b) b.click(); return; }
    AP.sheet('⏻ The radio', `<p>The app is not talking to the radio.</p>
      <div class="row"><button type="button" class="b gold" id="spConn">📻 CONNECT (the radio is on)</button><button type="button" class="b" id="spOn">⏻ TURN THE RADIO ON</button></div>
      <p class="hint">TURN ON works over the same USB cable on most Yaesu, Kenwood and Icom radios (some need their USB powered, or the radio's CAT power-on setting). Pick your radio in STATION → My radio first.</p>`);
    $('spConn').onclick = () => { AP.shut(); const b = $('rdConn'); if (b) b.click(); };
    $('spOn').hidden = !!(K.canOn && !K.canOn());   /* 0.9.9: the FTX-1 cannot be switched on over CAT */
    $('spOn').onclick = () => { AP.shut(); const b = $('rdPwrOn'); if (b) b.click(); };
  }
  { const o = $('rdOn'); if (o && G.MutationObserver) new MutationObserver(() => { const L = $('sdrL'); if ([...o.children].some(c => c.id !== 'sdrL' && c.id !== 'sdrR' && c.id !== 'sdrA') || ($('rdScope') && $('rdScope').parentNode !== L)) layout(); }).observe(o, { childList: true, subtree: true }); }
  AP.on('dial', () => { if (document.body.dataset.screen === 'radio') draw(); });
  AP.on('screen', s => { if (s === 'radio') { setTimeout(draw, 60); setTimeout(fit, 400); } else scr.classList.remove('fit'); });
  setInterval(() => { if (document.body.dataset.screen === 'radio') draw(); }, 2000);

  /* ---------------- the look (black, lit buttons) ---------------- */
  if (!$('kpcSdrCss')) document.head.insertAdjacentHTML('beforeend', `<style id="kpcSdrCss">
#scrRadio.sdr{--sdrbg:#040506;--sdrp:#0b0d10;--sdrp2:#111419;--sdrl:#1f242c;--lit:#ffb648;--litg:#4dff9a;background:var(--sdrbg);border-radius:18px;padding:10px;margin:-4px;color:#dfe6ee}
#scrRadio.sdr:not(.lit) .rdtop,#scrRadio.sdr:not(.lit) .rdscope,#scrRadio.sdr:not(.lit) .card{filter:saturate(.3) brightness(.6)}
.sdrhead{display:flex;align-items:center;gap:10px;padding:8px 10px;margin:0 0 10px;border-radius:14px;background:linear-gradient(180deg,#14181d,#0a0c0f);border:1px solid var(--sdrl);box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}
.sdrpwr{width:48px;height:48px;border-radius:50%;border:2px solid #5a1d1d;background:radial-gradient(circle at 50% 40%,#2a0d0d,#120606);color:#7a2a2a;font:900 22px var(--sans);flex:0 0 auto;cursor:pointer;transition:all .2s}
.sdrpwr.on{border-color:#2bd47a;color:#bfffd9;background:radial-gradient(circle at 50% 40%,#0f3a22,#06140c);box-shadow:0 0 14px rgba(77,255,154,.55),inset 0 0 10px rgba(77,255,154,.3);text-shadow:0 0 8px #4dff9a}
.sdrid{display:flex;flex-direction:column;min-width:0;flex:1}.sdrid b{font:800 15px var(--mono);color:#e9eef4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sdrid i{font:600 11px var(--sans);font-style:normal;color:#7d8794;letter-spacing:.06em;text-transform:uppercase}
.sdrclk{display:flex;flex-direction:column;align-items:center}.sdrclk i{font:700 9px var(--sans);font-style:normal;color:#7d8794;letter-spacing:.14em}.sdrclk b{font:800 15px var(--mono);color:#8fd3ff}
.sdrsw{display:flex;border:1px solid var(--sdrl);border-radius:10px;overflow:hidden}.sdrsw button{border:0;background:#0c0e11;color:#6f7884;font:800 11px var(--sans);letter-spacing:.1em;padding:9px 10px;cursor:pointer}.sdrsw button.on{background:#1b1406;color:var(--lit);text-shadow:0 0 8px rgba(255,182,72,.7)}
#scrRadio.sdr .rdtop{background:linear-gradient(180deg,#0e1115,#07080a);border:1px solid var(--sdrl);box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
#scrRadio.sdr .rdkhz{background:#020303;border-color:#2a2f37;color:#ffcf7a}
#scrRadio.sdr .rdkhz b{color:#ffd27e;text-shadow:0 0 14px rgba(255,170,60,.55),0 0 2px #ffb648}
#scrRadio.sdr .chip,.sdr .lit{background:#0d1014;border:1px solid #232933;color:#9aa6b4;box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
#scrRadio.sdr .chip.on,.sdr .lit.on{background:#1b1406;border-color:#7a5418;color:var(--lit);text-shadow:0 0 8px rgba(255,182,72,.8);box-shadow:0 0 10px rgba(255,170,60,.35),inset 0 0 8px rgba(255,170,60,.18)}
#scrRadio.sdr:not(.lit) .chip.on,.sdr:not(.lit) .lit.on{color:#8a6a3a;text-shadow:none;box-shadow:none}
#scrRadio.sdr .card{background:linear-gradient(180deg,#0d1014,#08090b);border-color:var(--sdrl)}
#scrRadio.sdr .card,#scrRadio.sdr .card::before,#scrRadio.sdr .card::after{background-image:none!important}
#scrRadio.sdr .card h2,#scrRadio.sdr .card summary{background:none!important;background-image:none!important;color:#c9a46a;font:800 12px var(--sans)!important;letter-spacing:.14em;text-transform:uppercase;border:0!important;box-shadow:none!important;padding:0!important;margin:0 0 10px!important;min-height:0!important;text-shadow:none!important}
#scrRadio.sdr .card h2 *,#scrRadio.sdr .card summary *{font-family:var(--sans)}
#scrRadio.sdr .b{background:#0d1014;border-color:#262c35;color:#c6ced8}#scrRadio.sdr .b.on{color:var(--lit);border-color:#7a5418;box-shadow:0 0 10px rgba(255,170,60,.35);text-shadow:0 0 8px rgba(255,182,72,.7)}
#rdBands .chip.q2{box-shadow:inset 0 -3px 0 #2bd47a}#rdBands .chip.q1{box-shadow:inset 0 -3px 0 #d5a63a}#rdBands .chip.q0{box-shadow:inset 0 -3px 0 #3a414b}
#rdBands .chip.on.q2{box-shadow:inset 0 -3px 0 #2bd47a,0 0 10px rgba(255,170,60,.35)}
.sdrvfo2{margin-top:10px}.sdrlab{font:800 10px var(--sans);letter-spacing:.14em;color:#7d8794}
.sdrplan{position:relative;height:18px;border-radius:4px;background:#07090b;border:1px solid #1d2229;overflow:hidden;margin:0 0 6px}
.sdrplan .sp{position:absolute;top:0;bottom:0}.sdrplan .k-cw,.sdrplan .k-cwo{background:rgba(109,180,245,.45)}.sdrplan .k-ph{background:rgba(232,184,74,.5)}.sdrplan .k-all{background:rgba(95,211,155,.42)}
.sdrmk{position:absolute;top:-2px;bottom:-2px;width:2px;margin-left:-1px;background:#ff4d5e;box-shadow:0 0 6px #ff4d5e}
.sdre{position:absolute;top:2px;font:700 10px/14px var(--mono);color:#cfd6de;text-shadow:0 0 3px #000,0 0 3px #000}.sdre.l{left:4px}.sdre.r{right:4px}.sdrpoff{display:block;text-align:center;font:11px var(--sans);color:#6f7884;line-height:18px}
.sdrbrow{display:flex;align-items:baseline;gap:10px;margin:6px 0}.sdrbrow b{font:800 18px var(--mono);color:#8fd3ff;text-shadow:0 0 8px rgba(143,211,255,.4)}.sdrbrow i{font:700 11px var(--sans);font-style:normal;color:#6f7884;letter-spacing:.08em}.sdrbrow i.on{color:#ff8a5e;text-shadow:0 0 6px rgba(255,120,80,.6)}
.sdrkeys,.sdrmem{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0 0}
.sdrkeys .lit,.sdrmem .lit{height:36px;padding:0 12px;border-radius:9px;font:800 12px var(--sans);letter-spacing:.06em;cursor:pointer}
.sdrkeys .lit.sm{height:32px;padding:0 10px}.sdroff,.sdrwpm{display:inline-flex;align-items:center;gap:5px;padding:0 6px;border:1px solid #1d2229;border-radius:10px}.sdroff b,.sdrwpm b{font:800 13px var(--mono);color:#ffd27e;min-width:52px;text-align:center}.sdrwpm b{min-width:26px}
.sdrmem .mem{display:flex;flex-direction:column;align-items:center;justify-content:center;height:44px;min-width:72px;padding:0 8px}.sdrmem .mem small{font:600 10px var(--mono);color:#6f7884}.sdrmem .mem.full small{color:#8fd3ff}.sdrmem .store.on{color:#ff8a5e}
#scrRadio.sdr[data-view="simple"] #rdMore,#scrRadio.sdr[data-view="simple"] #rdVoice,#scrRadio.sdr[data-view="simple"] #rdLv,#scrRadio.sdr[data-view="simple"] #rdNr,#scrRadio.sdr[data-view="simple"] #rdSteps,#scrRadio.sdr[data-view="simple"] #rdTalkH,#scrRadio.sdr[data-view="simple"] .sdrkeys,#scrRadio.sdr[data-view="simple"] .sdrbrow,#scrRadio.sdr[data-view="simple"] .rdctl,#scrRadio.sdr[data-view="simple"] #scChips{display:none!important}
#scrRadio.sdr .rdscope{background:#020304;border-color:var(--sdrl);padding:8px}#scrRadio.sdr .sccv{height:clamp(220px,38vh,420px)!important}
@media (min-width:1100px){#scrRadio.sdr #rdOn:not([hidden]){display:flex;gap:14px;align-items:flex-start}#scrRadio.sdr #sdrL{flex:1 1 auto;min-width:0}#scrRadio.sdr #sdrR{flex:0 0 420px;min-width:0}
  #scrRadio.sdr .rdgrid{grid-template-columns:1fr}#scrRadio.sdr .sccv{height:clamp(320px,52vh,600px)!important}}
/* Nov 19 2026 radio screen: FIT = three columns (left panels | VFO + meters + scope | controls, HOLD TO TALK pinned at the foot) */
#scrRadio.sdr.fit{max-width:none;margin:-4px 0}
#sdrA:empty{display:none}
#scrRadio.sdr.fit #rdOn:not([hidden]){display:flex;gap:12px;align-items:stretch;height:var(--fitH,760px)}
#scrRadio.sdr.fit #sdrA{flex:0 0 clamp(230px,15vw,300px);min-width:0;display:flex;flex-direction:column;gap:10px;overflow-y:auto;scrollbar-width:thin;height:100%}
#scrRadio.sdr.fit #sdrA .card{margin:0;padding:9px 11px}
#scrRadio.sdr.fit #sdrA .chips,#scrRadio.sdr.fit #sdrA .row{display:grid!important;grid-template-columns:repeat(auto-fill,minmax(58px,1fr));gap:5px;margin:0}
#scrRadio.sdr.fit #sdrA .chip{height:32px;padding:0 6px;justify-content:center;width:auto;margin:0}
#scrRadio.sdr.fit #sdrA .sdrmem{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin:0}
#scrRadio.sdr.fit #sdrA .sdrmem .mem{min-width:0;height:40px;padding:0 4px}#scrRadio.sdr.fit #sdrA .sdrmem .store{grid-column:1/-1;height:30px}
#scrRadio.sdr.fit #sdrA #rdSpots{max-height:none}#scrRadio.sdr.fit #sdrA #rdSpots *{max-width:100%}
#sdrCVk:has(#rdVk[hidden])::after{content:'No voice memories recorded yet.';display:block;font:12px var(--sans);color:#6f7884}
#sdrCSp:has(#rdSpots[hidden])::after{content:'No spots on this band right now.';display:block;font:12px var(--sans);color:#6f7884}
#scrRadio.sdr.fit #sdrA .sdrph{font-size:11px;margin:6px 0 0;color:#6f7884}#scrRadio.sdr.fit #sdrA #rdVk .kv{display:none}
#scrRadio.sdr.fit #sdrR > .rdmet{padding:8px 10px}
#scrRadio.sdr.fit #sdrR .grid2{grid-template-columns:minmax(0,1fr)}
#scrRadio.sdr.fit #sdrR .kmm{grid-template-columns:minmax(0,1fr)}#scrRadio.sdr.fit #sdrR .kmr{grid-template-columns:repeat(auto-fit,minmax(64px,1fr))}#scrRadio.sdr.fit #sdrR .kring{max-width:84px}
#scrRadio.sdr[data-view="simple"] #sdrCStep,#scrRadio.sdr[data-view="simple"] #sdrCVk{display:none!important}
#scrRadio.sdr.fit #sdrR label.e.slide{grid-template-columns:auto auto minmax(0,1fr)}#scrRadio.sdr.fit #sdrR input[type=range]{min-width:0;width:100%}
#scrRadio.sdr.fit #sdrA #rdVk{margin:0;padding:0;border:0;background:none;box-shadow:none}#scrRadio.sdr.fit #sdrA #rdVk > h2:first-child{display:none!important}
#scrRadio.sdr.fit #sdrL{flex:1 1 auto;display:flex;flex-direction:column;min-height:0;min-width:0;overflow-y:auto;scrollbar-width:thin}
#scrRadio.sdr.fit #sdrL .rdmet{margin:10px 0 0;padding:8px 10px}
#scrRadio.sdr.fit #sdrL .rdscope{flex:1 1 auto;display:flex;flex-direction:column;margin:10px 0 0;min-height:200px}
#scrRadio.sdr.fit #sdrL .sccv{flex:1 1 0;height:auto!important;min-height:140px;width:100%}
#scrRadio.sdr.fit #sdrL .rdscope h2{margin:0 0 4px}
#scrRadio.sdr.fit #sdrL #scChips{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;margin-top:6px}
#scrRadio.sdr.fit #sdrL #scSt{margin:4px 0 0;font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#scrRadio.sdr.fit #sdrL .rdtop .chip{height:32px;padding:0 9px}
#scrRadio.sdr.fit #sdrL .rdtop .chips,#scrRadio.sdr.fit #sdrL .rdtop .row{gap:5px;margin-top:6px}
#scrRadio.sdr.fit #sdrR{flex:0 0 clamp(320px,23vw,430px);min-width:0;height:100%;display:flex;flex-direction:column;overflow-y:auto;overflow-x:hidden;scrollbar-width:thin}
#scrRadio.sdr.fit #sdrR .rdgrid{display:contents}
#scrRadio.sdr.fit #sdrR > *,#scrRadio.sdr.fit #sdrR .rdgrid > *{margin-top:0;margin-bottom:10px;flex:0 0 auto}
#scrRadio.sdr.fit #sdrR > #rdTalk:not(.on){background:linear-gradient(rgba(243,154,85,.14),rgba(243,154,85,.14)),#0a0b0d}
#scrRadio.sdr.fit #sdrR > #rdTalk{order:99;position:sticky;bottom:0;z-index:3;margin:auto 0 0;box-shadow:0 -10px 14px #050608}#scrRadio.sdr.fit #sdrR > #rdMicLvl,#scrRadio.sdr.fit #sdrR > #rdVcLvl{order:98}
#scrRadio.sdr.fit #rdMet .kmg{display:grid;grid-template-columns:1fr 1fr;gap:4px}
#scrRadio.sdr.fit #rdMet .kmg canvas{width:100%;height:auto}
body:has(#scrRadio.sdr.fit) main{padding-bottom:0}
@media (max-width:699px){#scrRadio.sdr .rdtop .rdmet{margin:8px 0 0;padding:6px 8px}#scrRadio.sdr .rdtop .rdmet h2{display:none}#scrRadio.sdr .rdtop .rdmet [data-kmst]{display:none}#scrRadio.sdr .rdtop .rdmet .kmh{flex-wrap:wrap;gap:5px}
  #scrRadio.sdr .rdtop .chip{height:34px;padding:0 9px;font-size:12.5px}#scrRadio.sdr .rdtop .chips,#scrRadio.sdr .rdtop .row{gap:5px}
  #scrRadio.sdr .sdrmem .mem{min-width:0;flex:1 1 calc(25% - 6px);height:40px}}
#scrRadio.sdr.fit #sdrR .card{padding:9px 11px}
#scrRadio.sdr.fit #sdrR .card h2{margin:0 0 6px}
#scrRadio.sdr.fit #sdrR .b{min-height:34px;height:auto;padding-top:6px;padding-bottom:6px}
#scrRadio.sdr.fit #sdrR .chip{height:30px}
#scrRadio.sdr.fit #sdrR label.e{margin-top:2px}
#scrRadio.sdr.fit #sdrR input[type=range]{margin:2px 0 6px}
#scrRadio.sdr.fit #sdrR input[type=checkbox]{width:18px;height:18px;flex:0 0 18px;margin:2px 8px 0 0}
#scrRadio.sdr.fit #sdrR .ck{align-items:flex-start;text-align:left;justify-content:flex-start;gap:0}
#scrRadio.sdr.fit #sdrR .hint{font-size:11.5px;line-height:1.35;margin:4px 0}
#scrRadio.sdr.fit #sdrR .rdbig{display:grid;grid-template-columns:1fr 1fr;gap:6px}
#scrRadio.sdr.fit #sdrR .rdbig > *{width:auto;min-width:0;margin:0}
#scrRadio.sdr.fit #sdrR label.e.slide{display:grid;grid-template-columns:auto auto minmax(80px,1fr);align-items:center;column-gap:8px;margin:2px 0}
#scrRadio.sdr.fit #sdrR label.e.slide input[type=range]{margin:0}
#scrRadio.sdr.fit #sdrR .row,#scrRadio.sdr.fit #sdrR .chips,#scrRadio.sdr.fit #sdrR .kmh,#scrRadio.sdr.fit #rdVoice{flex-wrap:wrap}
/* the head extras, the VFO readout line, the knob, the foot, the phone thumb bar */
.sdrleds{display:flex;gap:10px;align-items:center}.sdrleds span{display:flex;align-items:center;gap:4px}.sdrleds i{font:800 10px var(--sans);font-style:normal;letter-spacing:.12em;color:#7d8794}
.sdrleds u{width:10px;height:10px;border-radius:50%;background:#1a1f26;border:1px solid #2a3039}.sdrleds u.on{background:#2bd47a;box-shadow:0 0 8px #2bd47a;border-color:#2bd47a}.sdrleds u.tx{background:#ff3b4e;box-shadow:0 0 10px #ff3b4e;border-color:#ff3b4e}
.sdrfs{height:30px;padding:0 10px;border-radius:8px;background:#0d1014;border:1px solid #262c35;color:#9aa6b4;font:800 11px var(--sans);letter-spacing:.08em;cursor:pointer}.sdrfs:hover{color:var(--lit,#ffb648)}
.sdrex{display:flex;flex-wrap:wrap;gap:4px 14px;margin:2px 0 8px;font:700 10.5px var(--sans);letter-spacing:.1em;color:#6f7884}.sdrex:empty{display:none}.sdrex em{font:700 12px var(--mono);font-style:normal;color:#8fd3ff;letter-spacing:0}
.sdrknob{--a:0deg;position:relative;flex:0 0 auto;width:64px;height:64px;border-radius:50%;margin-left:auto;cursor:ns-resize;touch-action:none;
  background:radial-gradient(circle at 50% 45%,#3a4049 0,#1d2127 55%,#0c0e11 100%);border:1px solid #2c323b;box-shadow:0 4px 10px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.08),0 0 0 4px #0b0d10,0 0 0 5px #222831}
.sdrknob::before{content:'';position:absolute;inset:8px;border-radius:50%;background:repeating-conic-gradient(from var(--a),#2a3038 0 4deg,#171a1f 4deg 8deg);opacity:.9}
.sdrknob i{position:absolute;left:50%;top:50%;width:10px;height:10px;margin:-5px;border-radius:50%;background:#ffb648;box-shadow:0 0 8px #ffb648;transform:rotate(var(--a)) translateY(-20px)}
.sdrknob:focus-visible{outline:2px solid #ffb648;outline-offset:4px}
.sdrfoot{font:600 11.5px var(--sans);color:#6f7884;margin:6px 2px 0;min-height:16px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sdrfoot b{color:#c9a46a;letter-spacing:.12em;font-size:10.5px;margin-right:6px}
.sdrthumb{display:grid;grid-template-columns:1fr 1.6fr;gap:8px;margin:10px 0}.sdrthumb > *{width:auto!important;min-width:0;margin:0!important}
.sdrthumb #rdTalk{min-height:56px}
@media (max-width:699px){.sdrknob{display:none}.sdrleds i{display:none}.sdrfs{display:none}.sdrloc{display:none}}
@media (min-width:700px) and (max-width:1099px){.sdrknob{width:54px;height:54px}}
</style>`);
  draw();
  G.KPCSdr = { draw, S, save, _lastB: () => LASTB };
})(window);

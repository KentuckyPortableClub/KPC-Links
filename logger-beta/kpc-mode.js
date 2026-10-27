/* KPC app: THE MODE FRAME (Fable, Oct 22). Every digital mode is one object with the same shape, so a new mode
   (CW, RTTY, PSK31, SSTV, WSPR, HELL, JS8, APRS…) plugs in here and gets the chip, the settings button, the sound,
   the remote link and the spot feed for free:
     KPCModes.add({
       id: 'APRS', label: 'APRS', panel: '#aprsPanel',   // the panel shown on the FT8/digital screen while this mode is active
       bands: ['2m','30m'], band(), setBand(b),           // its band list and the one it is on (the remote shows them)
       rx(c),                                             // sound in: {pcm: Float32Array 12 kHz, t, db} while the mode is active and sound runs
       run(on),                                           // sound started / stopped
       activate(), deactivate(),                          // became / stopped being the active mode
       settings(),                                        // opens its own settings sheet (the ⚙ chip)
       lines(),                                           // [{id,t,text,cls}] what it heard, for the remote tab and the lists
       ops: { cq: () => {}, halt: () => {} },             // what the remote may ask it to do: {op} messages land here
       buttons: [{op:'cq', label:'📣 CQ'}],               // what the remote tab shows for it
       enabled(), txing(), halt(why), state()             // is TX armed, is it sending now, stop everything, extra state for the remote
     });
   Sound: only the ACTIVE mode gets samples (one decoder at a time: phone battery, and the radio is on one band anyway).
   Rule (Brandon Oct 21): a mode whose buttons cannot work hides or dims them itself, with one line saying what to turn on. */
(function (G) {
  'use strict';
  const $ = id => document.getElementById(id);
  const AP = G.KPCApp, esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const M = [], byId = {};
  let ACT = null, RUN = false;
  const noop = () => {};
  const DEF = { bands: [], band: () => '', setBand: () => false, rx: noop, run: noop, activate: noop, deactivate: noop, settings: null, lines: () => [], ops: {}, buttons: [], enabled: () => false, txing: () => false, halt: noop, state: () => ({}), khz: () => 0, tune: null };

  function add(m) {
    m = Object.assign({}, DEF, m);
    if (!m.id || byId[m.id]) return byId[m.id];
    M.push(m); byId[m.id] = m; m.el = typeof m.panel === 'string' ? document.querySelector(m.panel) : m.panel;
    strip();
    const want = LS('kpcMode', 'FT8');
    if (!ACT && (m.id === want || M.length === 1)) use(m.id, true);
    return m;
  }
  function strip() {
    const el = $('modeChips'); if (!el) return;
    el.innerHTML = M.map(m => `<button type="button" class="chip mode${ACT === m ? ' on' : ''}" data-mode="${esc(m.id)}" title="${esc(m.title || m.label || m.id)}">${esc(m.label || m.id)}</button>`).join('');
    el.querySelectorAll('[data-mode]').forEach(b => { b.onclick = () => use(b.dataset.mode); });
    const set = $('dgSet'); if (set) { set.hidden = !(ACT && ACT.settings); $('dgSetM').textContent = ACT ? ACT.id : ''; }
  }
  function use(id, quiet) {
    const m = byId[id]; if (!m) return false;
    if (ACT === m) return true;
    const old = ACT;
    if (old) { try { old.deactivate(); } catch (e) { console.error(e); } if (old.el) old.el.hidden = true; }
    ACT = m; SV('kpcMode', id);
    if (m.el) m.el.hidden = false;
    try { m.activate(old ? old.id : ''); } catch (e) { console.error(e); }
    strip(); AP.fire('mode', m.id);
    if (!quiet && m.hello) AP.toast(m.hello, 3000);
    return true;
  }
  AP.on('rx', c => { if (ACT && RUN) ACT.rx(c); });
  AP.on('run', on => { RUN = on; M.forEach(m => { try { m.run(on, m === ACT); } catch (e) { console.error(e); } }); });
  const set = $('dgSet'); if (set) set.onclick = () => { if (ACT && ACT.settings) ACT.settings(); };
  /* the remote link asks by name */
  function op(name, a) {
    if (!ACT) return false;
    if (name === 'mode') return use(a && a.mode);
    if (name === 'band') return ACT.setBand(a && a.band);
    const f = ACT.ops[name]; if (!f) return false; f(a || {}); return true;
  }
  const state = () => ACT ? { mode: ACT.id, modes: M.map(m => m.id), bands: ACT.bands, band: ACT.band(), khz: ACT.khz(), enabled: !!ACT.enabled(), txing: !!ACT.txing(), buttons: ACT.buttons, extra: ACT.state() } : { mode: '', modes: [], bands: [], band: '', khz: 0, enabled: false, txing: false, buttons: [], extra: {} };
  G.KPCModes = { add, use, op, state, active: () => ACT, all: () => M.slice(), get: id => byId[id] || null, lines: () => ACT ? ACT.lines() : [] };
})(window);

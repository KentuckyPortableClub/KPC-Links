/* KPC Hunters Lounge: MORE RADIO CONTROLS for the website (Opus, Nov 7 2026; Brandon: 'what about more radio controls? … Does it have the easy
   radio settings?'). Sits under the Lounge's 📻 RADIO CONTROL card (#ctCat) and uses the same radio connection (kpc-cat.js, Web Serial):
   - 🎛 MORE CONTROLS: IF SHIFT, NR / NB level, AGC, ATT, PRE / IPO, CONTOUR, APF, MANUAL NOTCH, SPLIT, A ⇄ B, A = B, RIT / XIT, keyer speed,
     break-in. Only what THIS radio takes shows. The commands are the KPC app's (kpc-cat.js MORE, from the makers' CAT manuals), copied
     here as they are, with the same per-radio list (caps) — keep the two in step when one changes.
   - 📍 BAND MEMORY: band buttons go back to the last frequency + mode used on that band.
   - 🔧 TUNE (asks first: it transmits) and ⚠ SWR GUARD (when the Lounge keys the radio by CAT: warn / power to 25 % / stop + hold).
   - 📡 SCOPE: the Icom IC-7300 / 705 / 9700 / 7610 / 905's own scope over the USB cable; tap it to tune.
   - 🎧 HEAR THE RADIO HERE with the app's noise clean-up (kpc-nr.js), on by default.
   - 📖 SETUP GUIDE for the picked radio and 📝 WORKS ON MY RADIO.
   Settings in this browser only: kpcLoungeRx, kpcLoungeBM, kpcAppNr, kpcLoungeWorks. No outside services, no timers unless a feature is on. */
(function (G) {
  'use strict';
  const K = G.KPCCat; if (!K) return;   /* Nov 10: no longer only where #ctCat is: the logger's ⚙ radio pop-up (kpc-hunt-x.js) borrows the same box */
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  /* ================================================================ THE COMMANDS (copied from the KPC app's kpc-cat.js, Nov 6) */
  let S = K.get();
  const RADIO = K.RADIO || {}, LINK = () => 'serial';
  const pad = (n, w) => String(Math.round(n)).padStart(w, '0');
  const asc = t => new TextEncoder().encode(t);
  const icom = body => new Uint8Array([0xFE, 0xFE, parseInt(S.civ || '94', 16) & 255, 0xE0, ...body, 0xFD]);
  const pct255 = p => { const d = pad(Math.round(Math.max(0, Math.min(100, p)) * 2.55), 4); return [parseInt(d.slice(0, 2), 16), parseInt(d.slice(2), 16)]; };
  const EXTRA = {
    yaesu: { power: p => [asc('PC' + pad(Math.max(5, Math.min(100, p)), 3) + ';')], atu: () => [asc('AC002;')], mic: p => [asc('MG' + pad(Math.max(0, Math.min(100, p)), 3) + ';')] },
    kenwood: { power: p => [asc('PC' + pad(Math.max(5, Math.min(100, p)), 3) + ';')], atu: () => S.model === 'elecraft' ? null : [asc('AC111;')], mic: p => [asc('MG' + pad(Math.max(0, Math.min(100, p)), 3) + ';')] },
    icom: { power: p => [icom([0x14, 0x0A, ...pct255(p)])], atu: () => [icom([0x1C, 0x01, 0x02])], mic: p => [icom([0x14, 0x0B, ...pct255(p)])] },
    hamlib: {}
  };
  EXTRA.yaesu8 = EXTRA.yaesu;
  /* ---- MORE CONTROLS (Nov 6, Opus; Brandon: 'make sure you do all the options for more radios than I own … it needs to work for many radios').
     The same command sets Hamlib / flrig / fldigi use, taken from each maker's CAT reference manual (Hamlib's code was not copied):
       shift (IF SHIFT / PBT, Hz ±1200) · nrl / nbl (NR / NB level 0–100 %) · agc ('off' 'fast' 'mid' 'slow' 'auto') · att (dB) · pre (0 = off / IPO, 1, 2)
       contour · apf · mnotch (manual notch on / off) + mnotchf (Hz) · split · rit · xit · ritoff (RIT / clarifier offset Hz, absolute; 0 = clear)
       swap (VFO A ⇄ B) · ab (A = B) · keyspd (wpm) · bkin (0 off, 1 semi, 2 full).
     CAPS below says which radio takes which, so the RADIO screen only shows what that radio understands. A radio not yet tried on the air
     with KPC says 'not checked on a real radio yet' (TESTED lists the ones that have been: Brandon's 'works on my radio' reports go there). */
  const clamp = (v, a, b) => Math.max(a, Math.min(b, +v || 0));
  const bcd4 = v => { const d = pad(clamp(v, 0, 9999), 4); return [parseInt(d.slice(0, 2), 16), parseInt(d.slice(2), 16)]; };
  const l255 = p => Math.round(clamp(p, 0, 100) * 2.55);
  const bcd1 = v => parseInt(pad(clamp(v, 0, 99), 2), 16);
  const DX10 = { ftdx10: 1, ftdx101: 1, ft710: 1, ftx1: 1 };      /* Yaesu's newest CAT: IS with the extra 0, ATT 6/12/18 dB steps, CLAR instead of RT/XT */
  const ysh = hz => { hz = Math.round(clamp(hz, -1200, 1200) / 20) * 20; const s = (hz < 0 ? '-' : '+') + pad(Math.abs(hz), 4); return asc((DX10[S.radio] ? 'IS00' : 'IS0') + s + ';'); };
  const YAGC = { off: 0, fast: 1, mid: 2, slow: 3, auto: 4 };
  const yatt = db => DX10[S.radio] ? Math.max(0, [0, 6, 12, 18].indexOf(+db)) : (+db > 0 ? 1 : 0);
  const MORE = {
    yaesu: { shift: hz => [ysh(hz)], nrl: p => [asc('RL0' + pad(1 + Math.round(clamp(p, 0, 100) / 100 * 14), 2) + ';')], nbl: p => [asc('NL0' + pad(Math.round(clamp(p, 0, 100) / 10), 3) + ';')],
      agc: a => YAGC[a] == null ? null : [asc('GT0' + YAGC[a] + ';')], att: db => [asc('RA0' + yatt(db) + ';')], pre: n => [asc('PA0' + clamp(n, 0, 2) + ';')],
      contour: on => [asc('CO0000' + (on ? '01' : '00') + ';')], apf: on => [asc('CO0200' + (on ? '01' : '00') + ';')],
      mnotch: on => [asc('BP0000' + (on ? 1 : 0) + ';')], mnotchf: hz => [asc('BP01' + pad(clamp(Math.round(hz / 10), 1, 320), 3) + ';')],
      split: on => [asc(on ? 'ST1;' : 'ST0;')], rit: on => [asc(on ? 'RT1;' : 'RT0;')], xit: on => [asc(on ? 'XT1;' : 'XT0;')],
      ritoff: hz => { hz = Math.round(clamp(hz, -9990, 9990)); return hz ? [asc('RC;'), asc((hz > 0 ? 'RU' : 'RD') + pad(Math.abs(hz), 4) + ';')] : [asc('RC;')]; },
      swap: () => [asc('SV;')], ab: () => [asc('AB;')], keyspd: w => [asc('KS' + pad(clamp(w, 4, 60), 3) + ';')], bkin: n => [asc('BI' + (n ? 1 : 0) + ';')] },
    kenwood: { nrl: p => [asc('RL' + pad(1 + Math.round(clamp(p, 0, 100) / 100 * 9), 2) + ';')], nbl: p => [asc('NL' + pad(1 + Math.round(clamp(p, 0, 100) / 100 * 9), 3) + ';')],
      agc: a => S.model === 'elecraft' ? (a === 'fast' ? [asc('GT002;')] : a === 'slow' ? [asc('GT004;')] : null) : ({ off: 0, slow: 1, mid: 2, fast: 3 }[a] == null ? null : [asc('GT' + { off: 0, slow: 1, mid: 2, fast: 3 }[a] + ';')]),
      att: db => (S.radio === 'ts890' || S.radio === 'ts990') ? [asc('RA' + Math.max(0, [0, 6, 12, 18].indexOf(+db)) + ';')] : [asc('RA0' + (+db > 0 ? 1 : 0) + ';')], pre: n => [asc('PA' + (n ? 1 : 0) + ';')],
      apf: on => [asc('AP' + (on ? 1 : 0) + ';')],
      split: on => S.model === 'elecraft' ? [asc(on ? 'FT1;' : 'FT0;')] : on ? [asc('FR0;'), asc('FT1;')] : [asc('FR0;'), asc('FT0;')],
      rit: on => [asc(on ? 'RT1;' : 'RT0;')], xit: on => [asc(on ? 'XT1;' : 'XT0;')],
      ritoff: hz => { hz = Math.round(clamp(hz, -9990, 9990)); if (S.model === 'elecraft' || !hz) return [asc('RC;')]; return [asc('RC;'), asc((hz > 0 ? 'RU' : 'RD') + pad(Math.abs(hz), 5) + ';')]; },
      ab: () => [asc('VV;')], keyspd: w => [asc('KS' + pad(clamp(w, 4, 60), 3) + ';')] },
    icom: { shift: hz => { const l = Math.round(clamp(128 + clamp(hz, -1200, 1200) / 1200 * 127, 0, 255)); return [icom([0x14, 0x07, ...bcd4(l)]), icom([0x14, 0x08, ...bcd4(l)])]; },
      nrl: p => [icom([0x14, 0x06, ...bcd4(l255(p))])], nbl: p => [icom([0x14, 0x12, ...bcd4(l255(p))])],
      agc: a => a === 'off' ? [icom([0x1A, 0x04, 0x00])] : { fast: 1, mid: 2, slow: 3 }[a] ? [icom([0x16, 0x12, { fast: 1, mid: 2, slow: 3 }[a]])] : null,
      att: db => [icom([0x11, bcd1(db)])], pre: n => [icom([0x16, 0x02, clamp(n, 0, 2)])], apf: on => [icom([0x16, 0x32, on ? 1 : 0])],
      mnotch: on => [icom([0x16, 0x48, on ? 1 : 0])], mnotchf: hz => [icom([0x14, 0x0D, ...bcd4(Math.round(clamp((hz - 200) / 2800, 0, 1) * 255))])],
      split: on => [icom([0x0F, on ? 1 : 0])], rit: on => [icom([0x21, 0x01, on ? 1 : 0])], xit: on => [icom([0x21, 0x02, on ? 1 : 0])],
      ritoff: hz => { hz = Math.round(clamp(hz, -9999, 9999)); const a = Math.abs(hz), d = pad(a, 4); return [icom([0x21, 0x00, parseInt(d.slice(2), 16), parseInt(d.slice(0, 2), 16), hz < 0 ? 1 : 0])]; },
      swap: () => [icom([0x07, 0xB0])], ab: () => [icom([0x07, 0xA0])],
      keyspd: w => [icom([0x14, 0x0C, ...bcd4(Math.round((clamp(w, 6, 48) - 6) / 42 * 255))])], bkin: n => [icom([0x16, 0x47, clamp(n, 0, 2)])] },
    hamlib: { shift: hz => [asc('L IF ' + Math.round(clamp(hz, -1200, 1200)) + '\n')], nrl: p => [asc('L NR ' + (clamp(p, 0, 100) / 100).toFixed(2) + '\n')], nbl: p => [asc('L NB ' + (clamp(p, 0, 100) / 100).toFixed(2) + '\n')],
      agc: a => ({ off: 0, fast: 2, mid: 5, slow: 3, auto: 6 }[a] == null ? null : [asc('L AGC ' + { off: 0, fast: 2, mid: 5, slow: 3, auto: 6 }[a] + '\n')]),
      att: db => [asc('L ATT ' + Math.round(+db || 0) + '\n')], pre: n => [asc('L PREAMP ' + clamp(n, 0, 2) * 10 + '\n')], apf: on => [asc('U APF ' + (on ? 1 : 0) + '\n')],
      mnotch: on => [asc('U MN ' + (on ? 1 : 0) + '\n')], mnotchf: hz => [asc('L NOTCHF ' + Math.round(hz) + '\n')],
      split: on => [asc(on ? 'S 1 VFOB\n' : 'S 0 VFOA\n')], rit: on => [asc('U RIT ' + (on ? 1 : 0) + '\n')], xit: on => [asc('U XIT ' + (on ? 1 : 0) + '\n')], ritoff: hz => [asc('J ' + Math.round(hz) + '\n')],
      swap: () => [asc('G XCHG\n')], ab: () => [asc('G CPY\n')], keyspd: w => [asc('L KEYSPD ' + Math.round(clamp(w, 4, 60)) + '\n')], bkin: n => [asc('U FBKIN ' + (n === 2 ? 1 : 0) + '\n'), asc('U SBKIN ' + (n === 1 ? 1 : 0) + '\n')] }
  };
  MORE.yaesu8 = Object.assign({}, MORE.yaesu, { split: on => [asc(on ? 'FT3;' : 'FT2;')] });
  EXTRA.yaesu8 = Object.assign({}, EXTRA.yaesu);   /* its own copy now: the old ones split with FT3 / FT2 */
  Object.keys(MORE).forEach(p => { EXTRA[p] = Object.assign(EXTRA[p] || {}, MORE[p]); });
  /* which radio takes which (the radio list's id → what to leave out, and the choices its AGC / ATT / PRE knobs have) */
  const ALLK = ['shift', 'nrl', 'nbl', 'agc', 'att', 'pre', 'contour', 'apf', 'mnotch', 'mnotchf', 'split', 'rit', 'xit', 'ritoff', 'swap', 'ab', 'keyspd', 'bkin'];
  const ICOM_NEW = { ic7300: 1, ic705: 1, ic9700: 1, ic7610: 1, ic905: 1, ic7851: 1 };
  const ICOM_PRE2 = { ic7300: 1, ic7610: 1, ic7851: 1, ic7100: 1, ic756: 1, ic7600: 1, ic7700: 1, ic7800: 1, ic7410: 1 };
  const ICOM_ATT = { ic7610: [0, 6, 12, 18], ic7851: [0, 6, 12, 18], ic7800: [0, 6, 12, 18], ic7700: [0, 6, 12, 18], ic756: [0, 6, 12, 18], ic9700: [0, 10], ic905: [0, 10] };
  function caps(id) {
    id = id == null ? S.radio : id; const r = RADIO[id] || { proto: S.proto, model: S.model };
    const L = LINK(), pr = L === 'rigctld' ? 'hamlib' : L === 'flrig' ? 'flrig' : L === 'fake' ? 'fake' : r.proto;
    let out = [], agc = [], att = [], pre = [];
    if (pr === 'fake' || pr === 'hamlib') { out = ALLK.slice(); agc = ['off', 'fast', 'mid', 'slow', 'auto']; att = [0, 6, 12, 18]; pre = [0, 1, 2]; }
    else if (pr === 'yaesu' || pr === 'yaesu8') {
      out = ALLK.filter(k => !(DX10[id] && (k === 'rit' || k === 'xit')));
      agc = ['off', 'fast', 'mid', 'slow', 'auto']; att = DX10[id] ? [0, 6, 12, 18] : [0, 12]; pre = (id === 'ft891' || id === 'ft450') ? [0, 1] : [0, 1, 2];
    } else if (pr === 'icom') {
      if (r.model === 'xiegu') { out = ['split', 'swap', 'ab', 'att', 'pre']; att = [0, 20]; pre = [0, 1]; }
      else {
        const old = !ICOM_NEW[id] && id !== 'ic7100';
        const mn = ICOM_NEW[id] || /^ic(7100|7600|7700|7800|7410|756)$/.test(id);
        out = ALLK.filter(k => k !== 'contour' && !(old && ['rit', 'xit', 'ritoff', 'apf'].includes(k)) && !(id === 'ic718' && k === 'shift') && !(!mn && (k === 'mnotch' || k === 'mnotchf')));
        agc = ICOM_NEW[id] ? ['off', 'fast', 'mid', 'slow'] : ['fast', 'mid', 'slow']; att = ICOM_ATT[id] || [0, 20]; pre = ICOM_PRE2[id] ? [0, 1, 2] : [0, 1];
      }
    } else if (pr === 'kenwood') {
      if (r.model === 'elecraft') { out = ['agc', 'att', 'pre', 'apf', 'split', 'rit', 'xit', 'ritoff', 'keyspd']; agc = ['fast', 'slow']; att = [0, 10]; pre = [0, 1]; }
      else if (id === 'ts590') { out = ['nrl', 'nbl', 'att', 'pre', 'split', 'rit', 'xit', 'ritoff', 'ab', 'keyspd']; att = [0, 12]; pre = [0, 1]; }
      else if (id === 'ts890' || id === 'ts990') { out = ['agc', 'att', 'pre', 'split', 'rit', 'xit', 'ritoff', 'ab', 'keyspd']; agc = ['off', 'slow', 'mid', 'fast']; att = [0, 6, 12, 18]; pre = [0, 1]; }
      else if (/^ts(480|2000|570)$/.test(id)) { out = ['att', 'pre', 'split', 'rit', 'xit', 'ritoff', 'keyspd']; att = [0, 12]; pre = [0, 1]; }
      else if (id === 'flex') { out = ['split', 'rit', 'xit', 'ritoff', 'keyspd']; }
      else if (/^(qmx|qdx|qcx|trusdx|tx500|discovery)$/.test(id)) { out = ['split', 'keyspd']; }
    }
    return { keys: out, agc, att, pre, tested: TESTED[id] || null, id, proto: pr };
  }
  /* radios tried on the air with these controls (Brandon's 'works on my radio' reports go in here: id → { by, date, ok: [...], bad: [...] }) */
  const TESTED = {};
  function cmds(name, v) { S = K.get(); const E = EXTRA[S.proto] || {}; return E[name] ? E[name](v) : null; }
  async function send(name, v) {
    if (!K.connected()) { note('Connect the radio first (🔌 CONNECT MY RADIO).', false); return false; }
    const c = cmds(name, v); if (!c) { note('This radio does not take ' + (LBL[name] || name) + ' over CAT.', false); return false; }
    for (const b of c) if (!await K.raw(b)) { note('The radio did not take ' + (LBL[name] || name) + '.', false); return false; }
    return true;
  }
  const can = k => { S = K.get(); return caps(S.radio).keys.includes(k) && !!(EXTRA[S.proto] || {})[k]; };

  /* ================================================================ SETTINGS + LOOK */
  const X = Object.assign({ shift: 0, nrl: 50, nbl: 50, agc: '', att: 0, pre: 0, contour: 0, apf: 0, mnotch: 0, mnotchf: 1000, split: 0, rit: 0, xit: 0, ritoff: 0, ritstep: 50, keyspd: 22, bkin: 0,
    bandMem: true, tuneAsk: true, swrMax: 3, swrAct: 'warn', span: 25000, scope: false }, LS('kpcLoungeRx', {}));
  const save = () => SV('kpcLoungeRx', X);
  const BM = LS('kpcLoungeBM', {});
  const LBL = { shift: 'IF SHIFT', nrl: 'NR LEVEL', nbl: 'NB LEVEL', agc: 'AGC', att: 'ATT', pre: 'PRE', contour: 'CONTOUR', apf: 'APF', mnotch: 'MANUAL NOTCH', mnotchf: 'NOTCH', split: 'SPLIT', rit: 'RIT', xit: 'XIT', ritoff: 'RIT OFFSET', swap: 'A ⇄ B', ab: 'A = B', keyspd: 'KEYER SPEED', bkin: 'BREAK-IN', atu: 'TUNE', power: 'RF POWER' };
  const AGCL = { off: 'OFF', fast: 'FAST', mid: 'MID', slow: 'SLOW', auto: 'AUTO' };
  const css = document.createElement('style');
  css.textContent = `#lrBox{margin:14px 0 8px}#lrBox details{border:1px solid rgba(240,201,107,.45);border-radius:12px;background:rgba(20,12,6,.75);padding:0 12px;margin:0 0 10px}
#lrBox summary{cursor:pointer;list-style:none;padding:11px 0;font:900 12.5px Arial;letter-spacing:1.3px;color:#ffcf7a}#lrBox summary::-webkit-details-marker{display:none}#lrBox summary small{font:400 12.5px Arial;letter-spacing:0;color:#cdbb98;margin-left:6px}
#lrBox .lr-row{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:7px 0}#lrBox .lr-k{min-width:86px;font:900 11px Arial;letter-spacing:1px;color:#e9c77d}
#lrBox .lr-c{min-height:36px;padding:6px 12px;border:1px solid rgba(240,201,107,.5);border-radius:999px;background:#140d06;color:#f3e6c8;font:800 12.5px Arial;cursor:pointer}
#lrBox .lr-c.on{background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;border-color:#f6d58a}#lrBox .lr-c:disabled{opacity:.45;cursor:default}
#lrBox input[type=range]{flex:1 1 180px;accent-color:#d5a63a}#lrBox .lr-v{min-width:70px;font:700 12.5px monospace;color:#ffe2a8}
#lrBox .lr-h{font:900 11px Arial;letter-spacing:1.2px;color:#e9c77d;margin:12px 0 2px}#lrBox p.lr-n{margin:6px 0 10px;color:#cdbb98;font-size:13px;line-height:1.4}
#lrBox select{min-height:36px;background:#0d0904;color:#f3e6c8;border:1px solid rgba(240,201,107,.5);border-radius:8px;padding:4px 8px}#lrBox label.lr-t{display:flex;gap:8px;align-items:center;margin:6px 0;font-size:13.5px;color:#e9dcc6}
#lrBox canvas{display:block;width:100%;height:190px;border-radius:10px;border:1px solid rgba(240,201,107,.35);background:#050302;cursor:crosshair;touch-action:pan-y}
#lrBox ul.lr-g{margin:6px 0 10px 18px;padding:0;color:#e9dcc6;font-size:13.5px;line-height:1.45}#lrBox [hidden]{display:none!important}
#lrMsg{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:99999;max-width:min(560px,92vw);padding:12px 16px;border-radius:12px;background:#1d1208;border:1px solid #f0c96b;color:#fff;font:700 14px Arial;box-shadow:0 6px 24px rgba(0,0,0,.5)}#lrMsg.bad{border-color:#ff8a7a;background:#2a0e0a}
#lrSwr{margin:8px 0;padding:10px 12px;border-radius:10px;background:#3a0f0a;border:1px solid #ff8a7a;color:#fff;font:700 13.5px Arial}
#lrBox .nrbox .chip{min-height:34px;padding:5px 11px;border:1px solid rgba(240,201,107,.5);border-radius:999px;background:#140d06;color:#f3e6c8;font:800 12px Arial;margin:2px;cursor:pointer}#lrBox .nrbox .chip.on{background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05}
#lrBox .nrbox .nrh{font:900 11px Arial;letter-spacing:1px;color:#e9c77d;margin:8px 0}#lrBox .nrbox .nrh small{font-weight:400;letter-spacing:0;color:#cdbb98}#lrBox .nrbox .nrrow{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin:4px 0}#lrBox .nrbox .nrrow span{min-width:120px;font:900 11px Arial;color:#e9c77d}`;
  document.head.appendChild(css);
  let msgT = 0;
  function note(t, ok) { let m = $('lrMsg'); if (!m) { m = document.createElement('div'); m.id = 'lrMsg'; document.body.appendChild(m); } m.textContent = t; m.className = ok === false ? 'bad' : ''; m.hidden = false; clearTimeout(msgT); msgT = setTimeout(() => { m.hidden = true; }, ok === false ? 5000 : 2500); }

  /* ================================================================ THE CARD */
  const BANDS = [['160m', 1800, 2000, 1900, 'LSB'], ['80m', 3500, 4000, 3850, 'LSB'], ['60m', 5330, 5410, 5357, 'USB'], ['40m', 7000, 7300, 7200, 'LSB'], ['30m', 10100, 10150, 10110, 'CW'], ['20m', 14000, 14350, 14250, 'USB'], ['17m', 18068, 18168, 18130, 'USB'], ['15m', 21000, 21450, 21300, 'USB'], ['12m', 24890, 24990, 24950, 'USB'], ['10m', 28000, 29700, 28400, 'USB'], ['6m', 50000, 54000, 50125, 'USB'], ['2m', 144000, 148000, 146520, 'FM']];
  const bandOf = k => (BANDS.find(b => k >= b[1] && k <= b[2]) || [])[0] || '';
  const box = document.createElement('div'); box.id = 'lrBox';
  if ($('ctCat')) $('ctCat').appendChild(box);
  function html() {
    const C = caps(K.get().radio), on = K.connected(), r = RADIO[K.get().radio];
    const chip = (k, v, t, cur) => `<button type="button" class="lr-c${String(cur) === String(v) ? ' on' : ''}" data-xc="${k}:${v}">${t}</button>`;
    const tog = k => `<button type="button" class="lr-c${X[k] ? ' on' : ''}" data-xt="${k}">${LBL[k]} ${X[k] ? 'ON' : 'OFF'}</button>`;
    const sl = (k, min, max, step, f) => `<div class="lr-row"><span class="lr-k">${LBL[k]}</span><input type="range" data-xs="${k}" min="${min}" max="${max}" step="${step}" value="${X[k]}"><span class="lr-v" data-xv="${k}">${f(X[k])}</span>${k === 'shift' ? '<button type="button" class="lr-c" data-x0="shift">CENTER</button>' : ''}</div>`;
    const fS = v => (v > 0 ? '+' : '') + v + ' Hz', fP = v => v + ' %';
    const has = k => C.keys.includes(k);
    const yae = C.proto === 'yaesu' || C.proto === 'yaesu8';
    const tested = !r ? 'pick your radio above first' : C.tested ? '✓ checked on a real ' + r.label : r.label + ': not checked on a real radio yet';
    const more = !C.keys.length ? `<p class="lr-n">${r ? 'This radio takes none of these over CAT.' : 'Pick your radio in MY RADIO above, so the page knows which ones it takes.'}</p>` :
      (has('shift') ? sl('shift', -1200, 1200, 20, fS) : '') + (has('nrl') ? sl('nrl', 0, 100, 5, fP) : '') + (has('nbl') ? sl('nbl', 0, 100, 10, fP) : '') +
      (has('agc') ? `<div class="lr-row"><span class="lr-k">AGC</span>${C.agc.map(a => chip('agc', a, AGCL[a], X.agc)).join('')}</div>` : '') +
      (has('att') ? `<div class="lr-row"><span class="lr-k">ATT</span>${C.att.map(d => chip('att', d, d ? (C.att.length === 2 ? 'ON' : d + ' dB') : 'OFF', X.att)).join('')}</div>` : '') +
      (has('pre') ? `<div class="lr-row"><span class="lr-k">PRE</span>${C.pre.map(n => chip('pre', n, n === 0 ? (yae ? 'IPO' : 'OFF') : (C.pre.length === 2 ? 'ON' : (yae ? 'AMP ' : 'P.AMP ') + n), X.pre)).join('')}</div>` : '') +
      (['contour', 'apf', 'mnotch'].some(has) ? `<div class="lr-row">${['contour', 'apf', 'mnotch'].filter(has).map(tog).join('')}</div>` : '') +
      (has('mnotchf') ? `<div class="lr-row"><span class="lr-k">NOTCH AT</span><input type="range" data-xs="mnotchf" min="200" max="3000" step="10" value="${X.mnotchf}"><span class="lr-v" data-xv="mnotchf">${X.mnotchf} Hz</span></div>` : '') +
      (['split', 'swap', 'ab', 'rit', 'xit'].some(has) ? '<div class="lr-h">VFO</div><div class="lr-row">' + ['split', 'rit', 'xit'].filter(has).map(tog).join('') + ['swap', 'ab'].filter(has).map(k => `<button type="button" class="lr-c" data-xo="${k}">${LBL[k]}</button>`).join('') + '</div>' : '') +
      (has('ritoff') ? `<div class="lr-row"><span class="lr-k">OFFSET</span><span class="lr-v">${fS(X.ritoff)}</span><button type="button" class="lr-c" data-xr="-1">−</button><button type="button" class="lr-c" data-xr="1">+</button>${[10, 50, 100, 500].map(s => `<button type="button" class="lr-c${X.ritstep === s ? ' on' : ''}" data-xst="${s}">${s}</button>`).join('')}<button type="button" class="lr-c" data-xr="0">CLEAR</button></div>` : '') +
      (has('keyspd') ? '<div class="lr-h">CW</div>' + sl('keyspd', 6, 48, 1, v => v + ' wpm') : '') +
      (has('bkin') ? `<div class="lr-row"><span class="lr-k">BREAK-IN</span>${(C.proto === 'icom' ? [0, 1, 2] : [0, 1]).map(n => chip('bkin', n, ['OFF', 'SEMI', 'FULL'][n], X.bkin)).join('')}</div>` : '') +
      '<p class="lr-n">These go to the radio. The radio does not tell the page when you turn its own knobs, so they show what was sent last.</p>';
    const bm = BANDS.map(b => `<button type="button" class="lr-c" data-band="${b[0]}" title="${BM[b[0]] ? 'Back to ' + (BM[b[0]].khz / 1000).toFixed(3) + ' ' + BM[b[0]].mode : 'Go to ' + (b[3] / 1000).toFixed(3) + ' ' + b[4]}">${b[0]}${BM[b[0]] ? ' •' : ''}</button>`).join('');
    const scopeOk = C.proto === 'icom' && SCOPE_RIGS[K.get().radio];
    return `<details id="lrMore"${X.oMore ? ' open' : ''}><summary>🎛 MORE CONTROLS <small>${esc(tested)}${on ? '' : ' · radio not connected'}</small></summary>${more}</details>
      <details id="lrBand"${X.oBand ? ' open' : ''}><summary>📍 BANDS + TUNE + SWR <small>band memory, the radio's tuner, the SWR guard</small></summary>
        <div class="lr-row">${bm}</div><p class="lr-n">A band button goes back to the last frequency and mode you used on that band (• = remembered).</p>
        <label class="lr-t"><input type="checkbox" id="lrBm"${X.bandMem ? ' checked' : ''}> Band memory on</label>
        <div class="lr-row">${C.proto && (EXTRA[C.proto] || {}).atu && !(C.proto === 'kenwood' && K.get().model === 'elecraft') ? '<button type="button" class="lr-c" id="lrTune">🔧 TUNE THE ANTENNA</button>' : '<span class="lr-n">This radio has no tuner command over CAT.</span>'}<label class="lr-t"><input type="checkbox" id="lrAsk"${X.tuneAsk ? ' checked' : ''}> ask first (it transmits a carrier)</label></div>
        <div class="lr-row"><span class="lr-k">SWR GUARD</span><select id="lrSwr"><option value="2">2 : 1</option><option value="2.5">2.5 : 1</option><option value="3">3 : 1</option><option value="0">off</option></select><select id="lrSwrA"><option value="warn">warn me</option><option value="power">warn + power to 25 %</option><option value="stop">warn + stop transmitting</option></select></div>
        <p class="lr-n">The SWR guard watches the radio's SWR meter while this page keys the radio by CAT (voice keyer, FT8). With VOX the page does not know you are transmitting.</p><div id="lrSwrNote"></div></details>
      ${scopeOk ? `<details id="lrScope"${X.oScope ? ' open' : ''}><summary>📡 SCOPE <small>your Icom's own scope over the USB cable: tap it to tune</small></summary>
        <div class="lr-row"><button type="button" class="lr-c${X.scope ? ' on' : ''}" id="lrScOn">${X.scope ? 'SCOPE ON' : 'SCOPE OFF'}</button>${[5000, 10000, 25000, 50000, 100000].map(h => `<button type="button" class="lr-c${X.span === h ? ' on' : ''}" data-span="${h}">±${h / 1000} kHz</button>`).join('')}</div>
        <canvas id="lrScCv"></canvas><p class="lr-n" id="lrScSt">${on ? '' : 'Connect the radio first.'}</p></details>` : ''}
      <details id="lrHear"${X.oHear ? ' open' : ''}><summary>🎧 HEAR THE RADIO HERE <small>its USB sound through this computer, with noise clean-up</small></summary>
        <div class="lr-row"><span class="lr-k">FROM</span><select id="lrIn"><option value="">the radio's USB sound (pick)…</option></select><span class="lr-k">TO</span><select id="lrOut"><option value="">this computer's speakers</option></select></div>
        <div class="lr-row"><button type="button" class="lr-c" id="lrListen">${AU.ctx ? '⏹ STOP LISTENING' : '🎧 LISTEN'}</button><span class="lr-k">VOLUME</span><input type="range" id="lrVol" min="0" max="200" step="5" value="${X.vol == null ? 100 : X.vol}"></div>
        <div id="lrNrHost"></div><p class="lr-n">Pick the radio's own USB sound (USB Audio CODEC on Icom and Yaesu). Noise clean-up only changes what you hear; FT8 and the other decoders always get the untouched sound.</p></details>
      <details id="lrGuide"${X.oGuide ? ' open' : ''}><summary>📖 SETUP GUIDE + 📝 WORKS ON MY RADIO <small>what to set in the radio's own menus</small></summary>${guideHtml(K.get().radio)}
        <div class="lr-row"><button type="button" class="lr-c" id="lrWorks">📝 WORKS ON MY RADIO</button></div><div id="lrWorksBox"></div></details>`;
  }

  /* the radio-menu tips (kpc-app.js TIPS + kpc-help.js MODEL, Nov 6) */
  const TIPS = {
    yaesu: ['Yaesu (FT-710, FTDX10, FT-991A, FT-891, FTX-1)', ['CAT RATE = the baud rate picked here (38400), CAT RTS = ON is fine (the app holds RTS up)', 'DATA: MODE DATA → DATA MOD SOURCE = REAR and REAR SELECT = USB (FT8 power comes from this)', 'SSB voice from the app (keyer, hold to talk, the phone): MODE SSB → SSB MOD SOURCE = REAR (AUTO also works on most) — then PTT from the app carries the USB sound', 'CW typed from the app: the radio\'s own keyer over CAT works on the FT-710 / FTDX10 / 991A / 891; hand keying: USB KEYING (CW) = DTR + CW BK-IN = ON (the key is on the radio\'s SECOND USB port)', 'A tone through the sound card only transmits in DATA: the app flips the radio to DATA for the over when you pick that way']],
    icom: ['Icom (IC-7300, IC-705, IC-7100, IC-9700…)', ['CONNECTORS → CI-V: USB BAUD RATE = the one picked here, CI-V ADDRESS = the one shown here, CI-V USB ECHO BACK = OFF', 'DATA: MOD → DATA MOD = USB (FT8 power comes from this); the app uses USB-D', 'SSB voice from the app: CONNECTORS → MOD → DATA OFF MOD = USB (that is the SSB source) — or leave it MIC and turn on \'switch the radio to DATA while it sends\' under VOICE FROM THIS DEVICE', 'CW typed from the app: the radio\'s own keyer over CAT works; hand keying: CW by DTR on the USB port (CONNECTORS → USB SEND/KEYING → USB KEYING (CW) = DTR)', 'CI-V USB PORT = UNLINK FROM [REMOTE] so the USB port is a plain CAT port']],
    kenwood: ['Kenwood (TS-590, TS-890, TS-990, TS-480)', ['Menu: baud rate for the USB / COM port = the one picked here; TX ENABLE for the data (USB) audio input', 'DATA: pick DATA (DA1) with the USB audio as the source: menu \'USB audio input level\' up, \'audio input line select\' / \'DATA VOX\' off', 'SSB voice from the app: the SSB source must be the USB (ACC2) input while sending by CAT: menu \'TX audio source (SSB)\' / \'PC audio\' = USB — or use \'switch the radio to DATA while it sends\'', 'CW typed from the app: the radio\'s own keyer over CAT (KY) works; hand keying: DTR / RTS key line on the COM port where the radio allows it']],
    elecraft: ['Elecraft (KX2, KX3, K3, K4, KH1)', ['CONFIG: RS232 = the baud rate picked here; AUTOINF OFF', 'DATA: DATA A mode with LINE IN as the source (MIC/LINE = LINE); the KX2/KX3 take the sound card on the ACC / LINE jack', 'SSB voice from the app: MIC/LINE → LINE for the SSB source while sending from the app, or use \'switch the radio to DATA while it sends\'', 'CW typed from the app: the radio\'s own keyer over CAT (KY) works well; hand keying = a real key on the radio, or the DTR / RTS line through a Digirig']],
    xiegu: ['Xiegu (G90, X6100, X6200, G106)', ['CI-V on the USB-C / ACC: baud 19200 (G90 default), address 70', 'DATA + voice from the app both need the sound card on the ACC / LINE IN jack (a Digirig / Xiegu DE-19): the radio has no USB sound card of its own', 'CW typed from the app over CAT is not reliable on Xiegu: use the DTR / RTS key line (Digirig) or a tone', 'Hamlib / flrig also work for these (HOW THE APP REACHES IT)']],
    qrp: ['QRP Labs (QMX, QDX, QCX, (tr)uSDX)', ['QMX: USB SERIAL PORTS = 3 in its menu; CAT on the lowest port at 38400; the DTR line is NOT the key (the app keeps it down)', 'QDX / QMX are digital-only for the sound card (FT8 etc.); the QMX keys CW by its own keyer over CAT (KY, firmware 1_00_021+) or a paddle', 'No voice from these radios']],
    other: ['Other radios', ['The app sends standard Kenwood-style CAT (TS-590 commands); if the radio does not answer, try Hamlib rigctld or flrig under HOW THE APP REACHES IT', 'For DATA and voice from the app the radio must take its transmit sound from the sound card you picked (its USB / LINE / ACC input); set that in the radio\'s menu', 'CW: typed CW over CAT works on radios with a KY command; otherwise the DTR / RTS key line, or a tone through the sound card']]
  };
  const MODEL = {
    ic7300: ['MENU → SET → Connectors → CI-V: CI-V Baud Rate = 115200 (or Auto), CI-V Address = 94h, CI-V Transceive = ON, CI-V USB Port = Unlink from [REMOTE], CI-V USB Baud Rate = 115200, CI-V USB Echo Back = OFF', 'Connectors → MOD Input → DATA MOD = USB · USB MOD Level about 50 %', 'Connectors → ACC/USB Output Select = AF · USB AF Output Level about 50 %', 'For the RF scope under the band maps: Connectors → CI-V → CI-V USB Port must be Unlink from [REMOTE]', 'Windows driver: Icom\'s "USB driver" (Silicon Labs CP210x)'],
    ic705: ['MENU → SET → Connectors → CI-V: CI-V Address = A4h, CI-V USB Port = Unlink from [REMOTE], CI-V USB Echo Back = OFF', 'Connectors → MOD Input → DATA MOD = USB', 'USB AF / SQL Output → AF Output Level about 50 %', 'Bluetooth CAT is not used by the app: use the USB cable'],
    ic7100: ['MENU → SET → Connectors → CI-V: CI-V Baud Rate = 19200, CI-V Address = 88h, CI-V USB Echo Back = OFF', 'Connectors → DATA MOD = USB', 'Connectors → USB Audio SQL = OFF (OPEN), USB MOD Level about 50 %', 'The IC-7100 has no RF scope over CAT: the app shows the AUDIO picture'],
    ic9700: ['MENU → SET → Connectors → CI-V: CI-V Address = A2h, CI-V USB Port = Unlink from [REMOTE], CI-V USB Baud Rate = 115200, Echo Back = OFF', 'Connectors → MOD Input → DATA MOD = USB'],
    ic7610: ['MENU → SET → Connectors → CI-V: CI-V Address = 98h, CI-V USB (A) Port = Unlink from [REMOTE], USB (A) Baud = 115200, Echo Back = OFF', 'Connectors → MOD Input → DATA MOD = USB'],
    ft710: ['MENU → OPERATION SETTING → GENERAL: CAT-1 RATE = 38400, CAT-1 TIME OUT TIMER = 10 ms (or longer)', 'The radio makes two COM ports: the ENHANCED one is CAT, the STANDARD one is the PTT / keying line', 'MENU → OPERATION SETTING → MODE PSK/DATA (DATA): DATA MOD SOURCE = REAR, REAR SELECT = USB, USB MOD GAIN about 50', 'MODE SSB: SSB MOD SOURCE = REAR for voice from the app (or let the app switch to DATA while it sends)', 'The FT-710 scope over USB needs Yaesu\'s own driver: the app shows the AUDIO picture instead'],
    ftdx10: ['MENU → OPERATION SETTING → GENERAL: CAT RATE = 38400, CAT TIME OUT TIMER = 10 ms or longer', 'ENHANCED COM port = CAT, STANDARD = PTT / keying', 'MODE PSK/DATA: DATA MOD SOURCE = REAR, REAR SELECT = USB, USB MOD GAIN about 50', 'MODE SSB: SSB MOD SOURCE = REAR for voice from the app'],
    ftdx101: ['MENU → OPERATION SETTING → GENERAL: CAT RATE = 38400', 'ENHANCED COM port = CAT', 'MODE PSK/DATA: DATA MOD SOURCE = REAR, REAR SELECT = USB'],
    ftx1: ['MENU → CAT: CAT-1 RATE = 38400', 'ENHANCED COM port = CAT, STANDARD = PTT / keying', 'DATA mode: MOD SOURCE = REAR (USB), USB MOD GAIN about 50', 'Not checked on a real FTX-1 yet: please send a WORKS ON MY RADIO report'],
    ft891: ['MENU 05-06 CAT RATE = 38400, 05-08 CAT RTS = DISABLE (or let the app hold RTS)', 'The FT-891 has no USB sound card: use a Digirig, SCU-17 or similar on the DATA jack', 'DATA menu: DATA IN SELECT = REAR, DATA PTT SELECT = RTS (Digirig) or DAKY', 'With an SCU-17: CAT on the ENHANCED port, PTT on the STANDARD port'],
    ft991: ['MENU 031 CAT RATE = 38400, 032 CAT TOT = 10 ms or longer, 033 CAT RTS = DISABLE', 'MENU 070 DATA IN SELECT = REAR, 071 DATA PTT SELECT = RTS, 073 DATA OUT LEVEL about 50', 'ENHANCED COM port = CAT, STANDARD = PTT', 'Mode: DATA-U for FT8'],
    ts590: ['MENU: COM / USB port baud = 115200 (USB) — match the app', 'MENU: audio source for DATA = USB, USB audio input level about 5, DATA VOX = OFF', 'Use DATA (DA1) mode for FT8'],
    ts890: ['MENU → Advanced: USB (virtual COM) baud = 115200', 'Audio source for DATA mode = USB audio', 'Use DATA mode for FT8'],
    kx3: ['CONFIG: RS232 = 38400, AUTOINF = NOR', 'DATA A mode; MIC/LINE input = LINE IN from the sound card (KXUSB + a USB sound card, or a Digirig)'],
    k4: ['MENU: RS232 / USB baud = 38400 (the K4 USB port also works at higher rates)', 'DATA mode: TX audio from USB (LINE IN) — the K4 has its own USB audio'],
    g90: ['CI-V address 70h, baud 19200 (the G90 default)', 'Needs the Xiegu DE-19 (or a Digirig) for sound: the G90 has no USB sound card', 'PTT by CAT or by the DE-19\'s PTT line'],
    qmx: ['QMX menu: CAT = Kenwood TS-480 style (always on), any baud', 'USB sound card built in: pick "QMX" as the sound card', 'USB SERIAL PORTS = 3: CAT on the lowest-numbered port']
  };
  function draw() {
    if (!box.isConnected) return;   /* Nov 10: the box can be waiting, not on the page (VIP lounge until the ⚙ pop-up opens) */
    const op = ['lrMore', 'lrBand', 'lrScope', 'lrHear', 'lrGuide'].filter(id => $(id) && $(id).open);
    const f = document.activeElement && box.contains(document.activeElement) && document.activeElement.type === 'range';
    if (f) return;   /* never redraw under a finger on a slider */
    box.innerHTML = html();
    op.forEach(id => { if ($(id)) $(id).open = true; });
    $('lrSwr').value = String(X.swrMax); $('lrSwrA').value = X.swrAct;
    const nh = $('lrNrHost'); if (nh && G.KPCNR && KPCNR.html) nh.innerHTML = KPCNR.html('lrNr', true);
    fillDev(); swrNote(); scDraw();
  }
  box.addEventListener('toggle', e => { const k = { lrMore: 'oMore', lrBand: 'oBand', lrScope: 'oScope', lrHear: 'oHear', lrGuide: 'oGuide' }[e.target.id]; if (k) { X[k] = e.target.open; save(); } }, true);
  box.addEventListener('input', e => { const s = e.target.dataset && e.target.dataset.xs; if (s) { const v = +e.target.value, o = box.querySelector(`[data-xv="${s}"]`); if (o) o.textContent = s === 'shift' ? (v > 0 ? '+' : '') + v + ' Hz' : s === 'keyspd' ? v + ' wpm' : s === 'mnotchf' ? v + ' Hz' : v + ' %'; }
    if (e.target.id === 'lrVol') { X.vol = +e.target.value; save(); if (AU.gain) AU.gain.gain.value = X.vol / 100; } });
  box.addEventListener('change', e => {
    const t = e.target, s = t.dataset && t.dataset.xs;
    if (s) { X[s] = +t.value; save(); send(s, X[s]); return; }
    if (t.id === 'lrBm') { X.bandMem = t.checked; save(); } if (t.id === 'lrAsk') { X.tuneAsk = t.checked; save(); }
    if (t.id === 'lrSwr') { X.swrMax = +t.value; save(); } if (t.id === 'lrSwrA') { X.swrAct = t.value; save(); }
    if (t.id === 'lrIn' || t.id === 'lrOut') { X[t.id === 'lrIn' ? 'inDev' : 'outDev'] = t.value; save(); if (AU.ctx) { stopListen(); listen(); } }
  });
  box.addEventListener('click', async e => {
    const b = e.target.closest('button'); if (!b) return;
    if (b.dataset.x0) { X.shift = 0; save(); draw(); send('shift', 0); return; }
    if (b.dataset.xt) { const k = b.dataset.xt; X[k] = X[k] ? 0 : 1; save(); draw(); send(k, X[k]); return; }
    if (b.dataset.xo) { if (await send(b.dataset.xo, 1)) note(LBL[b.dataset.xo] + ' sent.'); return; }
    if (b.dataset.xc) { const [k, v] = b.dataset.xc.split(':'); X[k] = k === 'agc' ? v : +v; save(); draw(); send(k, X[k]); return; }
    if (b.dataset.xr) { const d = +b.dataset.xr; X.ritoff = d === 0 ? 0 : Math.max(-9990, Math.min(9990, X.ritoff + d * X.ritstep)); save(); draw(); send('ritoff', X.ritoff); return; }
    if (b.dataset.xst) { X.ritstep = +b.dataset.xst; save(); draw(); return; }
    if (b.dataset.band) { goBand(b.dataset.band); return; }
    if (b.dataset.span) { X.span = +b.dataset.span; save(); draw(); if (X.scope) scSpan(); return; }
    if (b.id === 'lrTune') { tuneAsk(); return; }
    if (b.id === 'lrScOn') { X.scope = !X.scope; save(); draw(); X.scope ? scStart() : scStop(); return; }
    if (b.id === 'lrListen') { AU.ctx ? stopListen() : listen(); return; }
    if (b.id === 'lrWorks') { works(); return; }
    if (b.id === 'lrResume') { HOLD = false; swrNote(); return; }
  });

  /* ================================================================ 📍 BAND MEMORY (remembers what the page tuned to, and what the dial says when the page reads it) */
  const remember = (khz, mode) => { khz = +khz; const b = bandOf(khz); if (!b || !X.bandMem) return; BM[b] = { khz, mode: mode || (BM[b] && BM[b].mode) || '', t: Date.now() }; SV('kpcLoungeBM', BM); };
  const tune0 = K.tune; K.tune = function (khz, mode) { const p = tune0.apply(K, arguments); Promise.resolve(p).then(ok => { if (ok) remember(khz, mode); }); return p; };
  const read0 = K.read; K.read = function () { const p = read0.apply(K, arguments); Promise.resolve(p).then(r => { if (r && r.khz) remember(r.khz, r.mode); }); return p; };
  async function goBand(b) {
    const B = BANDS.find(x => x[0] === b), m = X.bandMem && BM[b];
    if (!K.connected()) { note('Connect the radio first (🔌 CONNECT MY RADIO).', false); return; }
    const ok = await K.tune(m ? m.khz : B[3], m ? m.mode : B[4]);
    note(ok ? '📍 ' + b + ': ' + ((m ? m.khz : B[3]) / 1000).toFixed(3) + ' MHz ' + (m ? m.mode : B[4]) : 'The radio did not take the frequency.', ok);
    draw();
  }

  /* ================================================================ 🔧 TUNE (asks first) */
  const swrOf = v => v <= 0 ? 1 : v <= 30 ? 1 + v / 30 : v <= 60 ? 2 + (v - 30) / 30 : 3 + (v - 60) / 40 * 2;   /* the meter's 0–100 % → SWR (same as the app) */
  async function tuneAsk() {
    if (!K.connected()) { note('Connect the radio first (🔌 CONNECT MY RADIO).', false); return; }
    if (TX) { note('Transmitting now: tune after.', false); return; }
    if (X.tuneAsk && !confirm('🔧 Tune the antenna now?\n\nThe radio\'s own tuner runs: it TRANSMITS a carrier for a few seconds. Make sure the frequency is clear and the antenna is connected.')) return;
    if (!await send('atu', 1)) return;
    note('🔧 Tuning… watch the SWR.'); let best = null; const t0 = Date.now(); const was = K.get().on; if (!was) K.set({ on: true });
    while (Date.now() - t0 < 8000) { await sleep(700); const m = await K.meters(); if (m && m.swr != null && m.po > 3) best = best == null ? m.swr : Math.min(best, m.swr); }
    if (!was) K.set({ on: false });
    if (best != null) { const s = swrOf(best); note('🔧 Tuned: SWR about ' + s.toFixed(1) + ' : 1' + (s > 2 ? ' — still high: check the antenna or try again.' : '.'), s <= 2); } else note('🔧 Tune sent.');
  }

  /* ================================================================ ⚠ SWR GUARD (only while this page keys the radio by CAT) */
  let gBusy = false, TX = false, TXVIA = 'cat', HOLD = false, hi = 0, acted = false, gT = 0;
  const ptt0 = K.ptt;
  K.ptt = function (on, via) {
    if (on && HOLD) { note('⚠ Transmitting is on hold after a HIGH SWR. Check the antenna, then press "OK, TRANSMIT AGAIN" in the radio card.', false); return Promise.resolve(false); }
    const p = ptt0.apply(K, arguments);
    Promise.resolve(p).then(ok => { if (on && ok && (via || K.get().ptt || 'cat') !== 'vox') { TX = true; TXVIA = via || K.get().ptt || 'cat'; hi = 0; acted = false; if (!gT) gT = setInterval(() => { if (!gBusy) { gBusy = true; guard().finally(() => { gBusy = false; }); } }, 500); }   /* one meter read at a time: they must not pile up in front of the unkey */ if (!on) { TX = false; clearInterval(gT); gT = 0; } });
    return p;
  };
  async function guard() {
    if (!TX || acted || !(X.swrMax > 0)) return;
    const m = await K.meters(); if (!TX || !m || m.swr == null || !(m.po > 5)) return;
    const s = swrOf(m.swr); hi = s > X.swrMax ? hi + 1 : 0; if (hi < 2) return; acted = true;
    const what = X.swrAct === 'stop' ? ' Transmitting stopped and on hold.' : X.swrAct === 'power' ? ' Power turned down to 25 %.' : '';
    note('⚠ HIGH SWR: about ' + s.toFixed(1) + ' : 1.' + what + ' Check the antenna, or 🔧 TUNE.', false);
    if (X.swrAct === 'power') await send('power', 25);
    if (X.swrAct === 'stop') { HOLD = true; TX = false; clearInterval(gT); gT = 0; await ptt0.call(K, false, TXVIA); document.querySelectorAll('[data-vk-stop],#vkStop,.f8-halt,[data-halt]').forEach(b => { try { b.click(); } catch (e) {} }); }
    LAST = { s, t: new Date().toISOString().slice(11, 16) + ' UTC' }; swrNote();
  }
  let LAST = null;
  function swrNote() { const n = $('lrSwrNote'); if (!n) return; n.innerHTML = HOLD ? `<div id="lrSwr">⚠ HIGH SWR (${LAST ? LAST.s.toFixed(1) + ' : 1 at ' + LAST.t : ''}): transmitting is on hold. <button type="button" class="lr-c" id="lrResume">OK, TRANSMIT AGAIN</button></div>` : LAST ? `<p class="lr-n">Last warning: SWR about ${LAST.s.toFixed(1)} : 1 at ${LAST.t}.</p>` : ''; }

  /* ================================================================ 📡 THE ICOM SCOPE (CI-V 27 00, the same reader as the app's kpc-scope.js) */
  const SCOPE_RIGS = { ic7300: 1, ic705: 1, ic9700: 1, ic7610: 1, ic905: 1 };
  const bcd = x => (x >> 4) * 10 + (x & 15);
  const hzLE = a => { let s = ''; for (let j = a.length - 1; j >= 0; j--) s += bcd(a[j]).toString().padStart(2, '0'); return +s; };
  const bcdLE = (n, len) => { const s = String(Math.round(n)).padStart(len * 2, '0'); const o = []; for (let j = len - 1; j >= 0; j--) o.push(parseInt(s.substr(j * 2, 2), 16)); return o; };
  let CUR = null, pend = [], ROWS = [], scLast = 0, scOn = false;
  function civFrame(d) {
    if (!d || d.length < 3 || d[0] !== 0) return;
    const seq = bcd(d[1]), max = bcd(d[2]);
    if (seq === 1) { if (d.length < 15) return; const mode = d[3], f1 = hzLE(d.slice(4, 9)), f2 = hzLE(d.slice(9, 14)), c = mode === 0 || mode === 2;
      CUR = { max, lo: c ? f1 - f2 : f1, hi: c ? f1 + f2 : f2, oor: d[14] === 1, wave: [] }; if (d.length > 15) CUR.wave.push(...d.slice(15)); }
    else if (CUR && seq > 1) CUR.wave.push(...d.slice(3));
    if (CUR && seq === max) { if (!CUR.oor && CUR.wave.length >= 50 && CUR.hi > CUR.lo) { const v = new Float32Array(CUR.wave.length); for (let i = 0; i < v.length; i++) v[i] = Math.min(1, CUR.wave[i] / 160);
      ROWS.push({ lo: CUR.lo / 1000, hi: CUR.hi / 1000, v }); if (ROWS.length > 120) ROWS.shift(); scLast = Date.now(); paint(); } CUR = null; }
  }
  function tap(chunk) {
    const b = pend.length ? pend.concat(Array.from(chunk)) : Array.from(chunk); pend = [];
    const out = []; let i = 0;
    while (i < b.length) {
      if (b[i] === 0xFE && i === b.length - 1) { pend = [0xFE]; break; }
      if (b[i] === 0xFE && b[i + 1] === 0xFE) {
        const end = b.indexOf(0xFD, i + 2);
        if (end < 0) { if (b.length - i > 1500) { out.push(...b.slice(i)); i = b.length; } else pend = b.slice(i); break; }
        let s = i; while (s + 2 < end && b[s + 2] === 0xFE) s++;
        if (b[s + 4] === 0x27 && b[s + 5] === 0x00 && b[s + 3] !== 0xE0) civFrame(b.slice(s + 6, end)); else for (let k = i; k <= end; k++) out.push(b[k]);
        i = end + 1;
      } else { out.push(b[i]); i++; }
    }
    return out;
  }
  async function scStart() {
    S = K.get(); if (!K.connected() || S.proto !== 'icom' || !SCOPE_RIGS[S.radio]) { const st = $('lrScSt'); if (st) st.textContent = 'Connect the radio first.'; return false; }
    K.setTap(tap); scOn = true;
    const ok = await K.raw(icom([0x27, 0x10, 0x01])) && await K.raw(icom([0x27, 0x11, 0x01])); await scSpan();
    const st = $('lrScSt'); if (st) st.textContent = ok ? 'Waiting for the radio\'s scope… (CI-V USB Port must be "Unlink from [REMOTE]")' : 'The radio did not take the scope commands.';
    return ok;
  }
  async function scSpan() { await K.raw(icom([0x27, 0x14, 0x00, 0x00])); await K.raw(icom([0x27, 0x15, 0x00, ...bcdLE(X.span, 5)])); }
  async function scStop() { if (scOn && K.connected()) await K.raw(icom([0x27, 0x11, 0x00])); scOn = false; K.setTap(null); ROWS = []; paint(); }
  function scDraw() { const cv = $('lrScCv'); if (cv) paint(); }
  function paint() {
    const cv = $('lrScCv'); if (!cv || !cv.offsetParent) return;
    const W = cv.clientWidth, H = cv.clientHeight, dpr = Math.min(2, devicePixelRatio || 1); if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.fillStyle = '#050302'; c.fillRect(0, 0, W, H);
    const r = ROWS[ROWS.length - 1], SP = Math.round(H * 0.42);
    if (!r) { c.fillStyle = '#8f7f62'; c.font = '13px Arial'; c.fillText(scOn ? 'Waiting for the radio\'s scope…' : 'Press SCOPE OFF to turn it on.', 12, 24); return; }
    for (let y = 0; y < Math.min(ROWS.length, H - SP); y++) { const row = ROWS[ROWS.length - 1 - y], n = row.v.length;
      for (let x = 0; x < W; x += 2) { const v = row.v[Math.floor(x / W * n)]; c.fillStyle = `hsl(${40 - v * 40},90%,${8 + v * 55}%)`; c.fillRect(x, SP + y, 2, 1); } }
    c.strokeStyle = '#f6d58a'; c.lineWidth = 1.2; c.beginPath(); for (let x = 0; x < W; x++) { const v = r.v[Math.floor(x / W * r.v.length)], y = SP - 4 - v * (SP - 18); x ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke();
    c.fillStyle = '#cdbb98'; c.font = '11px monospace'; c.fillText((r.lo / 1000).toFixed(3), 4, 12); const t = (r.hi / 1000).toFixed(3); c.fillText(t, W - c.measureText(t).width - 4, 12);
    const st = $('lrScSt'); if (st) st.textContent = (r.lo / 1000).toFixed(3) + ' – ' + (r.hi / 1000).toFixed(3) + ' MHz · tap a signal to go there';
  }
  box.addEventListener('pointerup', e => { if (e.target.id !== 'lrScCv') return; const r = ROWS[ROWS.length - 1]; if (!r) return; const x = e.offsetX / e.target.clientWidth, khz = Math.round((r.lo + (r.hi - r.lo) * x) * 10) / 10;
    K.read().then(d => K.tune(khz, (d && d.mode) || 'USB')).then(ok => note(ok ? '📡 ' + (khz / 1000).toFixed(4) + ' MHz' : 'The radio did not take the frequency.', ok)); });

  /* ================================================================ 🎧 HEAR THE RADIO HERE (+ the app's noise clean-up) */
  const AU = { ctx: null, src: null, gain: null, stream: null, ch: null, el: null };
  if (G.KPCNR && !localStorage.getItem('kpcAppNr')) KPCNR.set({ nr: 'light' });   /* the handoff: clean-up ON by default */
  async function fillDev() {
    const i = $('lrIn'), o = $('lrOut'); if (!i || !navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
    try { const ds = await navigator.mediaDevices.enumerateDevices();
      const opt = (d, cur) => `<option value="${esc(d.deviceId)}"${d.deviceId === cur ? ' selected' : ''}>${esc(d.label || (d.kind === 'audioinput' ? 'Sound input ' : 'Speakers ') + d.deviceId.slice(0, 4))}</option>`;
      i.innerHTML = '<option value="">the radio\'s USB sound (pick)…</option>' + ds.filter(d => d.kind === 'audioinput').map(d => opt(d, X.inDev)).join('');
      const outs = ds.filter(d => d.kind === 'audiooutput'); const sinkOk = 'setSinkId' in HTMLMediaElement.prototype;
      o.innerHTML = '<option value="">this computer\'s speakers</option>' + (sinkOk ? outs.map(d => opt(d, X.outDev)).join('') : ''); o.disabled = !sinkOk; o.title = sinkOk ? '' : 'Picking the speakers works in Chrome and Edge';
    } catch (e) {}
  }
  async function listen() {
    try {
      AU.stream = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: X.inDev ? { exact: X.inDev } : undefined, echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
      AU.ctx = new AudioContext(); AU.src = AU.ctx.createMediaStreamSource(AU.stream); AU.gain = AU.ctx.createGain(); AU.gain.gain.value = (X.vol == null ? 100 : X.vol) / 100;
      if (G.KPCNR) { await KPCNR.prepare(AU.ctx); AU.ch = KPCNR.chain(AU.ctx); AU.src.connect(AU.ch.input); AU.ch.output.connect(AU.gain); } else AU.src.connect(AU.gain);
      if (X.outDev && 'setSinkId' in HTMLMediaElement.prototype) { const d = AU.ctx.createMediaStreamDestination(); AU.gain.connect(d); AU.el = new Audio(); AU.el.srcObject = d.stream; await AU.el.setSinkId(X.outDev).catch(() => {}); await AU.el.play(); }
      else AU.gain.connect(AU.ctx.destination);
      note('🎧 Listening' + (G.KPCNR && KPCNR.active() ? ' with noise clean-up.' : '.')); draw();
    } catch (e) { stopListen(); note('Could not open the sound: ' + (e.message || e) + '. Allow the microphone for this page and pick the radio\'s USB sound.', false); }
  }
  function stopListen() { try { AU.stream && AU.stream.getTracks().forEach(t => t.stop()); } catch (e) {} try { AU.el && AU.el.pause(); } catch (e) {} try { AU.ctx && AU.ctx.close(); } catch (e) {} Object.keys(AU).forEach(k => { AU[k] = null; }); draw(); }

  /* ================================================================ 📖 SETUP GUIDE (the app's kpc-help.js MODEL + kpc-app.js TIPS, Nov 6) */
  function guideHtml(id) {
    const R = RADIO[id]; if (!R) return '<p class="lr-n">Pick your radio in MY RADIO above for its setup guide.</p>';
    const fam = R.model === 'elecraft' ? 'elecraft' : R.model === 'xiegu' ? 'xiegu' : /^(qmx|qdx|qcx|trusdx)$/.test(id) ? 'qrp' : /^yaesu/.test(R.proto) ? 'yaesu' : R.proto === 'icom' ? 'icom' : R.proto === 'kenwood' && /^ts/.test(id) ? 'kenwood' : 'other';
    const F = TIPS[fam], C = caps(id);
    return `<p class="lr-n"><b>${esc(R.label)}</b> · CAT ${R.proto === 'icom' ? 'CI-V' : R.proto === 'kenwood' ? 'Kenwood-style' : 'Yaesu'} at <b>${R.baud}</b> baud${R.civ ? ' · CI-V address <b>' + esc(R.civ) + 'h</b>' : ''}</p>` +
      (MODEL[id] ? '<div class="lr-h">ON THIS RADIO</div><ul class="lr-g">' + MODEL[id].map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>' : '') +
      (F ? '<div class="lr-h">' + esc(F[0]).toUpperCase() + '</div><ul class="lr-g">' + F[1].map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>' : '') +
      `<p class="lr-n">🎛 The page can send it: ${C.keys.length ? C.keys.map(k => LBL[k] || k).join(', ') : 'frequency, mode and the basics only'}.</p>`;
  }

  /* ================================================================ 📝 WORKS ON MY RADIO */
  const WORKS = LS('kpcLoungeWorks', {});
  function works() {
    const id = K.get().radio, R = RADIO[id], w = $('lrWorksBox'); if (!w) return;
    if (!R) { note('Pick your radio first (MY RADIO).', false); return; }
    const list = [['freq', 'Tune to a spot (frequency + mode)'], ['read', 'TEST: READ MY DIAL'], ['ptt', 'Transmit (voice keyer / FT8)'], ['meters', 'Meters'], ['atu', '🔧 Tune'], ['scope', '📡 Scope'], ['band', '📍 Band buttons']].concat(caps(id).keys.map(k => [k, LBL[k] || k]));
    const prev = WORKS[id] || { ok: [], bad: [] }, val = {}; list.forEach(([k]) => { val[k] = prev.ok.includes(k) ? 1 : prev.bad.includes(k) ? -1 : 0; });
    w.innerHTML = '<p class="lr-n">Try each one on the radio, then tap ✓ or ✗. Leave the ones you did not try.</p>' + list.map(([k, l]) => `<div class="lr-row"><span class="lr-k" style="min-width:200px">${esc(l)}</span><button type="button" class="lr-c" data-wk="${k}" data-wv="1">✓ WORKS</button><button type="button" class="lr-c" data-wk="${k}" data-wv="-1">✗ NOT</button></div>`).join('') +
      `<label class="lr-t" style="display:block">NOTES (firmware, cable, what went wrong)<br><textarea id="lrWkN" rows="3" style="width:100%;background:#0d0904;color:#f3e6c8;border:1px solid rgba(240,201,107,.5);border-radius:8px">${esc(prev.note || '')}</textarea></label><div class="lr-row"><button type="button" class="lr-c on" id="lrWkGo">📤 COPY THE REPORT</button></div>`;
    const paintW = () => w.querySelectorAll('[data-wk]').forEach(b => b.classList.toggle('on', val[b.dataset.wk] === +b.dataset.wv));
    paintW(); w.querySelectorAll('[data-wk]').forEach(b => { b.onclick = ev => { ev.stopPropagation(); const k = b.dataset.wk, v = +b.dataset.wv; val[k] = val[k] === v ? 0 : v; paintW(); }; });
    $('lrWkGo').onclick = async ev => { ev.stopPropagation();
      const rep = { radio: id, label: R.label, ok: list.filter(([k]) => val[k] === 1).map(([k]) => k), bad: list.filter(([k]) => val[k] === -1).map(([k]) => k), note: $('lrWkN').value.trim(), date: new Date().toISOString().slice(0, 10) };
      WORKS[id] = rep; SV('kpcLoungeWorks', WORKS);
      const nm = l => (list.find(x => x[0] === l) || [l, l])[1];
      const txt = `KPC Hunters Lounge (website) — WORKS ON MY RADIO\nRadio: ${rep.label} (${id})\nBrowser: ${navigator.userAgent.replace(/^.*(Edg|Chrome)\/(\d+).*$/, '$1 $2')}\nDate: ${rep.date}\n\nWORKS: ${rep.ok.map(nm).join(', ') || '-'}\nDOES NOT WORK: ${rep.bad.map(nm).join(', ') || '-'}\nNotes: ${rep.note || '-'}\n`;
      let done = false; try { await navigator.clipboard.writeText(txt); done = true; } catch (e) {}
      if (!done) { const t = document.createElement('textarea'); t.value = txt; document.body.appendChild(t); t.select(); try { done = document.execCommand('copy'); } catch (e) {} t.remove(); }
      note(done ? '📝 Report copied: paste it to the club (email, Discord, GitHub).' : 'Could not copy: select the text and copy it.', done); };
  }

  /* ================================================================ START */
  draw();
  if (K.onStatus) K.onStatus(() => setTimeout(() => { draw(); if (X.scope && K.connected() && !scOn) scStart(); }, 300));
  const sel = $('ctRadio'); if (sel) sel.addEventListener('change', () => setTimeout(draw, 100));
  G.KPCLoungeRx = { box, home: () => $('ctCat'), X, caps, cmds, send, draw, goBand, tuneAsk, BM, tap, ROWS: () => ROWS, guard, hold: () => HOLD, swrOf };
})(window);

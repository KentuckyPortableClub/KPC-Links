/* KPC radio control (CAT) + QRZ logbook sender — shared by the members Hunters Lounge and its CAT & QRZ tab (Brandon Oct 17 2026).
   CAT uses the browser's Web Serial (Chrome / Edge on a computer, plugged in by USB). Settings live only in this browser
   (localStorage kpcCat). The QRZ logbook key lives only in this browser too (localStorage kpcQrz) and goes only to logbook.qrz.com.

   window.KPCCat: get(), set(o), supported(), connect(ask), connected(), tune(kHz, mode) -> Promise<bool>, read() -> {khz, mode}|null, ptt(on, via) -> Promise<bool>,
                  test(), onStatus(fn), follow(fn) (poll the radio every 2 s while 'follow' is on)
   window.KPCQrz: get(), set(o), on(), send(adifRecord) -> Promise<{ok, sure, msg}>                                                     */
(function () {
  const LS = k => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const DEF = { on: false, proto: 'kenwood', baud: 38400, civ: '94', data: 'usb', follow: false, model: '' };
  let S = Object.assign({}, DEF, LS('kpcCat') || {});
  let port = null, writer = null, reader = null, rbuf = [], busy = Promise.resolve(), subs = [], fol = null;
  const say = (t, ok) => subs.forEach(f => { try { f(t, ok); } catch (e) {} });
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  /* Bluetooth serial (SPP) radios show in the port list too on Chrome for Android (IC-705's Bluetooth data, BT CAT dongles) */
  const PICK = { allowedBluetoothServiceClassIds: ['00001101-0000-1000-8000-00805f9b34fb'] };

  /* ---- what each kind of radio wants ---- */
  const M = s => String(s || '').toUpperCase();
  function kind(mode, khz) { // CW / SSB(USB|LSB) / FM / AM / DATA
    const m = M(mode);
    if (/CW/.test(m)) return 'CW';
    if (/FT8|FT4|JS8|PSK|RTTY|DATA|DIG|OLIVIA|MFSK|VARA|SSTV|WSPR/.test(m)) return 'DATA';
    if (m === 'FM') return 'FM'; if (m === 'AM') return 'AM';
    if (m === 'LSB') return 'LSB'; if (m === 'USB') return 'USB';
    return khz && khz < 10000 ? 'LSB' : 'USB'; // SSB / PHONE: LSB below 10 MHz, USB above (60 m is USB)
  }
  const sb = (k, khz) => (k === 'USB' || k === 'LSB') ? (khz >= 5300 && khz <= 5410 ? 'USB' : k) : k;
  const pad = (n, w) => String(Math.round(n)).padStart(w, '0');
  const asc = t => new TextEncoder().encode(t);
  const bcdLE = (hz, bytes) => { const d = pad(hz, bytes * 2); const o = []; for (let i = bytes - 1; i >= 0; i--) o.push(parseInt(d.substr(i * 2, 2), 16)); return o; };
  const civ = () => parseInt(S.civ || '94', 16) & 255;
  const icom = body => new Uint8Array([0xFE, 0xFE, civ(), 0xE0, ...body, 0xFD]);

  const PROTOS = {
    kenwood: { // Kenwood, Elecraft K3/K4/KX2/KX3, QRP Labs QMX/QDX, (tr)uSDX, Lab599 TX-500, FlexRadio (SmartSDR CAT)
      tune(khz, k) { const md = { LSB: 1, USB: 2, CW: 3, FM: 4, AM: 5, DATA: S.data === 'data' ? (S.model === 'elecraft' ? 6 : 2) : 2 }[k] || 2;
        const out = [asc('FA' + pad(khz * 1000, 11) + ';'), asc('MD' + md + ';')]; if (k === 'DATA' && S.data === 'data' && S.model !== 'elecraft') out.push(asc('DA1;')); return out; },
      ask: () => asc('FA;IF;'),
      parse(t) { const f = /FA(\d{11});/.exec(t); const md = /IF[\d+\- ]{27}(\d)/.exec(t); if (!f) return null;
        return { khz: +f[1] / 1000, mode: md ? ({ 1: 'LSB', 2: 'USB', 3: 'CW', 4: 'FM', 5: 'AM', 6: 'DATA', 7: 'CW', 9: 'DATA' }[md[1]] || '') : '' }; }
    },
    yaesu: { // newer Yaesu CAT: FT-991A, FT-891, FT-710, FTDX10, FTDX101, FT-DX3000/5000
      tune(khz, k) { const md = { LSB: '1', USB: '2', CW: '3', FM: '4', AM: '5', DATA: S.data === 'data' ? 'C' : '2' }[k] || '2'; return [asc('FA' + pad(khz * 1000, 9) + ';'), asc('MD0' + md + ';')]; },
      ask: () => asc('FA;MD0;'),
      parse(t) { const f = /FA(\d{9});/.exec(t); const md = /MD0([0-9A-E]);/.exec(t); if (!f) return null;
        return { khz: +f[1] / 1000, mode: md ? ({ 1: 'LSB', 2: 'USB', 3: 'CW', 4: 'FM', 5: 'AM', 6: 'DATA', 7: 'CW', 8: 'DATA', 9: 'DATA', C: 'DATA', B: 'FM' }[md[1]] || '') : '' }; }
    },
    yaesu8: { // older 'new CAT' Yaesu with 8-digit frequency: FT-450D, FT-950, FT-2000, FTDX1200, FTDX3000, FTDX5000
      tune(khz, k) { const md = { LSB: '1', USB: '2', CW: '3', FM: '4', AM: '5', DATA: S.data === 'data' ? 'C' : '2' }[k] || '2'; return [asc('FA' + pad(khz * 1000, 8) + ';'), asc('MD0' + md + ';')]; },
      ask: () => asc('FA;MD0;'),
      parse(t) { const f = /FA(\d{8});/.exec(t); const md = /MD0([0-9A-E]);/.exec(t); if (!f) return null;
        return { khz: +f[1] / 1000, mode: md ? ({ 1: 'LSB', 2: 'USB', 3: 'CW', 4: 'FM', 5: 'AM', 6: 'DATA', 7: 'CW', 8: 'DATA', 9: 'DATA', C: 'DATA', B: 'FM' }[md[1]] || '') : '' }; }
    },
    yaesuold: { // FT-817 / FT-818 / FT-857 / FT-897 (5-byte binary commands)
      tune(khz, k) { const d = pad(khz * 100, 8); const f = [0, 2, 4, 6].map(i => parseInt(d.substr(i, 2), 16));
        const md = { LSB: 0, USB: 1, CW: 2, FM: 8, AM: 4, DATA: S.data === 'data' ? 0x0A : 1 }[k]; return [new Uint8Array([...f, 0x01]), new Uint8Array([md == null ? 1 : md, 0, 0, 0, 0x07])]; },
      ask: () => new Uint8Array([0, 0, 0, 0, 0x03]),
      parse(t, raw) { if (!raw || raw.length < 5) return null; const b = raw.slice(-5); const h = b.slice(0, 4).map(x => x.toString(16).padStart(2, '0')).join('');
        if (!/^\d{8}$/.test(h)) return null; return { khz: +h / 100, mode: ({ 0: 'LSB', 1: 'USB', 2: 'CW', 3: 'CW', 4: 'AM', 8: 'FM', 0x0A: 'DATA', 0x0C: 'DATA' }[b[4]] || '') }; }
    },
    icom: { // Icom CI-V: IC-705, IC-7300, IC-7610, IC-9700, IC-7100, IC-718; Xiegu G90 / X6100 / X5105 (CI-V)
      tune(khz, k) { const md = { LSB: 0, USB: 1, AM: 2, CW: 3, FM: 5, DATA: 1 }[k]; const o = [icom([0x05, ...bcdLE(khz * 1000, 5)]), icom([0x06, md == null ? 1 : md, 0x01])];
        if (S.model !== 'xiegu') o.push(icom([0x1A, 0x06, k === 'DATA' && S.data === 'data' ? 1 : 0, k === 'DATA' && S.data === 'data' ? 1 : 0])); return o; },
      ask: () => new Uint8Array([...icom([0x03]), ...icom([0x04])]),
      parse(t, raw) { if (!raw) return null; let khz = 0, mode = '';
        for (let i = 0; i < raw.length - 5; i++) { if (raw[i] === 0xFE && raw[i + 1] === 0xFE && raw[i + 2] === 0xE0) { const c = raw[i + 4];
          if ((c === 0x03 || c === 0x00) && raw[i + 10] === 0xFD) { let s = ''; for (let j = 4; j >= 0; j--) s += raw[i + 5 + j].toString(16).padStart(2, '0'); if (/^\d{10}$/.test(s)) khz = +s / 1000; }
          if ((c === 0x04 || c === 0x01) && raw[i + 7] === 0xFD) mode = { 0: 'LSB', 1: 'USB', 2: 'AM', 3: 'CW', 4: 'DATA', 5: 'FM', 7: 'CW', 8: 'DATA' }[raw[i + 5]] || ''; } }
        return khz ? { khz, mode } : null; }
    }
  };

  async function openPort(p) {
    port = p; await port.open({ baudRate: +S.baud || 38400, dataBits: 8, stopBits: S.proto === 'yaesuold' ? 2 : 1, parity: 'none', flowControl: 'none' });
    try { await port.setSignals({ dataTerminalReady: !!S.dtr, requestToSend: !!S.rts }); } catch (e) {}
    writer = port.writable.getWriter(); readLoop();
    say('Radio connected.', true); return true;
  }
  async function readLoop() {
    try { reader = port.readable.getReader(); for (;;) { const { value, done } = await reader.read(); if (done) break; if (value) { rbuf.push(...value); if (rbuf.length > 4096) rbuf = rbuf.slice(-2048); } } }
    catch (e) {} finally { try { reader.releaseLock(); } catch (e) {} }
  }
  async function connect(ask) {
    if (!('serial' in navigator)) { say('This browser can\'t talk to a radio. Use Chrome or Edge on a computer, or Chrome on an Android phone (newer versions, with a USB-C cable). iPhones can\'t do this yet.', false); return false; }
    if (port && writer) return true;
    try {
      const ps = await navigator.serial.getPorts(); // a radio this browser was allowed before (no question asked)
      if (ps.length) return await openPort(ps[Math.min(+S.portIx || 0, ps.length - 1)]);
      if (!ask) return false;
      return await openPort(await navigator.serial.requestPort(PICK));
    } catch (e) { port = null; writer = null; say('Could not open the radio: ' + (e.message || e) + '. Close other radio programs (WSJT-X, flrig, the radio\'s own app) and try again.', false); return false; }
  }
  async function disconnect() { try { if (reader) await reader.cancel(); } catch (e) {} try { if (writer) writer.releaseLock(); } catch (e) {} try { if (port) await port.close(); } catch (e) {} port = writer = reader = null; say('Radio disconnected.', false); }
  async function write(bytes) { await writer.write(bytes); await sleep(S.proto === 'yaesuold' ? 80 : 40); }
  function tune(khz, mode) {
    khz = +khz; if (!S.on || !khz) return Promise.resolve(false);
    busy = busy.then(async () => {
      if (!await connect(false)) { say('Radio not connected: open the CAT & QRZ tab and press CONNECT MY RADIO.', false); return false; }
      const P = PROTOS[S.proto] || PROTOS.kenwood, k = sb(kind(mode, khz), khz);
      try { for (const b of P.tune(khz, k)) await write(b); say(`📻 Radio set to ${(khz / 1000).toFixed(4).replace(/0+$/, '').replace(/\.$/, '')} MHz ${k}.`, true); return true; }
      catch (e) { say('Radio did not answer: ' + (e.message || e), false); await disconnect(); return false; }
    }).catch(() => false);
    return busy;
  }
  function read() {
    busy = busy.then(async () => {
      if (!port || !writer) return null; const P = PROTOS[S.proto] || PROTOS.kenwood;
      rbuf = []; try { await write(P.ask()); } catch (e) { return null; } await sleep(260);
      const raw = rbuf.slice(); const t = String.fromCharCode(...raw); return P.parse(t, raw);
    }).catch(() => null);
    return busy;
  }
  /* PTT for the FT8 tab in the KPC Logger (Brandon Oct 17). via: 'cat' (radio command), 'rts' / 'dtr' (serial line, e.g. Digirig), 'vox' (nothing sent) */
  const PTTC = { kenwood: on => [asc(on ? 'TX;' : 'RX;')], yaesu: on => [asc(on ? 'TX1;' : 'TX0;')], yaesu8: on => [asc(on ? 'TX1;' : 'TX0;')], yaesuold: on => [new Uint8Array([0, 0, 0, 0, on ? 0x08 : 0x88])], icom: on => [icom([0x1C, 0x00, on ? 1 : 0])] };
  function ptt(on, via) {
    via = via || S.ptt || 'cat'; if (via === 'vox') return Promise.resolve(true);
    busy = busy.then(async () => {
      if (!await connect(false)) { say('Radio not connected, so no PTT. Connect it, or use VOX.', false); return false; }
      try { if (via === 'rts' || via === 'dtr') { await port.setSignals(via === 'rts' ? { requestToSend: !!on } : { dataTerminalReady: !!on }); return true; }
        for (const b of (PTTC[S.proto] || PTTC.kenwood)(!!on)) await write(b); return true; }
      catch (e) { say('PTT did not work: ' + (e.message || e), false); return false; }
    }).catch(() => false);
    return busy;
  }
  /* ---- CW from the keyboard (Brandon Oct 17: 'cw keyboard to cw') ----
     The radio's own keyer sends the text: Kenwood / Elecraft / QRP Labs 'KY text;', Icom CI-V 0x17. Yaesu radios can't take free text
     over CAT, so for them (or anything else) the page keys the DTR or RTS line itself (Digirig etc.: DTR = key). */
  const CWOK = { kenwood: 1, icom: 1 };
  function cwCan() { return !!CWOK[S.proto]; }
  async function cwSpeed(wpm) { wpm = Math.max(6, Math.min(48, Math.round(wpm)));
    if (S.proto === 'kenwood') await write(asc('KS' + pad(wpm, 3) + ';'));
    if (S.proto === 'icom') { const lv = Math.round((wpm - 6) / 42 * 255), d = pad(lv, 4); await write(icom([0x14, 0x0C, parseInt(d.slice(0, 2), 16), parseInt(d.slice(2), 16)])); } }
  function cw(text, wpm) {
    text = String(text || '').toUpperCase().replace(/[^A-Z0-9 /?.,=+\-]/g, '');
    busy = busy.then(async () => {
      if (!await connect(false)) { say('Radio not connected.', false); return false; }
      if (!cwCan()) { say('This radio type can\'t take typed CW over CAT: use the DTR or RTS key line, or audio.', false); return false; }
      try { if (wpm) await cwSpeed(wpm);
        if (S.proto === 'kenwood') { for (let i = 0; i < text.length; i += 24) await write(asc('KY ' + text.slice(i, i + 24).padEnd(24, ' ') + ';')); }
        else { for (let i = 0; i < text.length; i += 30) await write(icom([0x17, ...asc(text.slice(i, i + 30))])); }
        return true; }
      catch (e) { say('CW did not send: ' + (e.message || e), false); return false; }
    }).catch(() => false);
    return busy;
  }
  async function cwStop() { try { if (!port || !writer) return; if (S.proto === 'kenwood') await write(asc('RX;'));
    if (S.proto === 'icom') await write(icom([0x17, 0xFF])); } catch (e) {} }
  /* key a serial line on and off (true = key down) */
  async function keyLine(down, line) { if (!port) return false; try { await port.setSignals(line === 'rts' ? { requestToSend: !!down } : { dataTerminalReady: !!down }); return true; } catch (e) { return false; } }

  /* every radio we know how to talk to (Brandon Oct 17: 'add all radios it can run cat on'); [id, label, proto, baud, CI-V, model] */
  const RADIOS = [
    ['Icom', [['ic705', 'IC-705', 'icom', 115200, 'A4'], ['ic7300', 'IC-7300', 'icom', 115200, '94'], ['ic7610', 'IC-7610', 'icom', 115200, '98'], ['ic9700', 'IC-9700', 'icom', 115200, 'A2'], ['ic905', 'IC-905', 'icom', 115200, 'AC'],
      ['ic7100', 'IC-7100', 'icom', 19200, '88'], ['ic7851', 'IC-7851', 'icom', 19200, '8E'], ['ic7800', 'IC-7800', 'icom', 19200, '6A'], ['ic7700', 'IC-7700', 'icom', 19200, '74'], ['ic7600', 'IC-7600', 'icom', 19200, '7A'],
      ['ic7410', 'IC-7410', 'icom', 19200, '80'], ['ic7200', 'IC-7200', 'icom', 19200, '76'], ['ic9100', 'IC-9100', 'icom', 19200, '7C'], ['ic7000', 'IC-7000', 'icom', 19200, '70'], ['ic746', 'IC-746 / 746PRO', 'icom', 19200, '66'],
      ['ic756', 'IC-756PRO III', 'icom', 19200, '6E'], ['ic718', 'IC-718', 'icom', 9600, '5E'], ['ic703', 'IC-703', 'icom', 9600, '68']]],
    ['Yaesu', [['ftx1', 'FTX-1', 'yaesu', 38400], ['ft710', 'FT-710', 'yaesu', 38400], ['ft891', 'FT-891', 'yaesu', 38400], ['ft991', 'FT-991 / 991A', 'yaesu', 38400], ['ftdx10', 'FTDX10', 'yaesu', 38400], ['ftdx101', 'FTDX101D / MP', 'yaesu', 38400],
      ['ftdx3000', 'FTDX3000', 'yaesu8', 38400], ['ftdx1200', 'FTDX1200', 'yaesu8', 38400], ['ftdx5000', 'FTDX5000', 'yaesu8', 38400], ['ft950', 'FT-950', 'yaesu8', 38400], ['ft2000', 'FT-2000', 'yaesu8', 38400], ['ft450', 'FT-450 / 450D', 'yaesu8', 38400],
      ['ft818', 'FT-818', 'yaesuold', 9600], ['ft817', 'FT-817', 'yaesuold', 9600], ['ft857', 'FT-857', 'yaesuold', 9600], ['ft897', 'FT-897', 'yaesuold', 9600]]],
    ['Kenwood', [['ts990', 'TS-990', 'kenwood', 115200], ['ts890', 'TS-890', 'kenwood', 115200], ['ts590', 'TS-590S / SG', 'kenwood', 115200], ['ts480', 'TS-480', 'kenwood', 57600], ['ts2000', 'TS-2000', 'kenwood', 57600], ['ts570', 'TS-570', 'kenwood', 57600]]],
    ['Elecraft', [['kx2', 'KX2', 'kenwood', 38400, '', 'elecraft'], ['kx3', 'KX3', 'kenwood', 38400, '', 'elecraft'], ['k4', 'K4', 'kenwood', 38400, '', 'elecraft'], ['k3', 'K3 / K3S', 'kenwood', 38400, '', 'elecraft'], ['k2', 'K2', 'kenwood', 4800, '', 'elecraft'], ['kh1', 'KH1', 'kenwood', 38400, '', 'elecraft']]],
    ['Xiegu (CI-V)', [['g90', 'G90', 'icom', 19200, '70', 'xiegu'], ['x6100', 'X6100', 'icom', 19200, '70', 'xiegu'], ['x6200', 'X6200', 'icom', 19200, '70', 'xiegu'], ['g106', 'G106', 'icom', 19200, '70', 'xiegu'], ['x5105', 'X5105', 'icom', 19200, '70', 'xiegu']]],
    ['QRP Labs & kits', [['qmx', 'QMX / QMX+', 'kenwood', 115200], ['qdx', 'QDX', 'kenwood', 115200], ['qcx', 'QCX / QCX mini (CAT)', 'kenwood', 38400], ['trusdx', '(tr)uSDX', 'kenwood', 115200]]],
    ['Others', [['tx500', 'Lab599 TX-500', 'kenwood', 9600], ['discovery', 'Lab599 Discovery TX-500MP', 'kenwood', 9600], ['flex', 'FlexRadio (SmartSDR CAT port)', 'kenwood', 9600]]]
  ];
  const RADIO = {}; RADIOS.forEach(([g, L]) => L.forEach(r => { RADIO[r[0]] = { id: r[0], label: g.split(' ')[0] + ' ' + r[1], proto: r[2], baud: r[3], civ: r[4] || '', model: r[5] || '' }; }));
  /* fill a <select> with every radio; pick(id) sets the right settings */
  function fillSelect(sel) { if (!sel) return; const cur = S.radio || '';
    sel.innerHTML = '<option value="">Pick your radio…</option>' + RADIOS.map(([g, L]) => `<optgroup label="${g}">` + L.map(r => `<option value="${r[0]}"${r[0] === cur ? ' selected' : ''}>${(g === 'QRP Labs & kits' || g === 'Others') ? '' : g.split(' ')[0] + ' '}${r[1]}</option>`).join('') + '</optgroup>').join('') + '<option value="other">Something else (pick the settings by hand)</option>'; }
  function pickRadio(id) { const r = RADIO[id]; if (!r) { S.radio = id; SV('kpcCat', S); return null; } S = Object.assign({}, S, { radio: id, proto: r.proto, baud: r.baud, civ: r.civ || S.civ || '94', model: r.model }); SV('kpcCat', S); return r; }

  function follow(fn) {
    if (fol) clearInterval(fol); fol = null; if (!fn) return; let last = '';
    fol = setInterval(async () => { if (!S.on || !S.follow || !port || document.hidden) return; const r = await read(); if (!r) return; const k = r.khz + '|' + r.mode; if (k !== last) { last = k; fn(r); } }, 2000);
  }
  /* change the port (Brandon Oct 17: 'a menu to change port if someone selects the wrong one') */
  const VEND = { 0x10C4: 'Silicon Labs CP210x (Icom, Yaesu, Xiegu, Elecraft cables)', 0x0403: 'FTDI (many CAT cables)', 0x067B: 'Prolific (older CAT cables)', 0x1A86: 'CH340 (QRP Labs, truSDX, cheap cables)', 0x0483: 'STMicro (QMX/QDX)', 0x2341: 'Arduino', 0x239A: 'Adafruit', 0x2E8A: 'Raspberry Pi Pico', 0x1FC9: 'NXP', 0x04D8: 'Microchip' };
  async function ports() {
    if (!('serial' in navigator)) return [];
    const ps = await navigator.serial.getPorts();
    return ps.map((p, i) => { const f = (p.getInfo && p.getInfo()) || {}, v = f.usbVendorId;
      return { i, now: p === port, label: (v != null ? (VEND[v] || 'USB maker ' + v.toString(16).toUpperCase().padStart(4, '0')) : 'Serial port') + (f.usbProductId != null ? ' · product ' + f.usbProductId.toString(16).toUpperCase().padStart(4, '0') : '') }; });
  }
  async function usePort(i) { await disconnect(); S.portIx = i; SV('kpcCat', S); return connect(false); }
  async function pickNew() {
    if (!('serial' in navigator)) return false;
    let p; try { p = await navigator.serial.requestPort(PICK); } catch (e) { say('No port picked.', false); return false; }
    await disconnect(); const ps = await navigator.serial.getPorts(); S.portIx = Math.max(0, ps.indexOf(p)); SV('kpcCat', S);
    try { return await openPort(p); } catch (e) { port = writer = null; say('Could not open that port: ' + (e.message || e) + '. Close other radio programs and try again.', false); return false; }
  }
  async function forget(i) {
    const ps = await navigator.serial.getPorts(), p = ps[i]; if (!p) return;
    if (p === port) await disconnect();
    try { if (p.forget) await p.forget(); } catch (e) {}
    S.portIx = 0; SV('kpcCat', S); say(p.forget ? 'Port forgotten. Press PICK A DIFFERENT PORT to choose the right one.' : 'This browser can\'t forget ports: pick the right one with PICK A DIFFERENT PORT.', null);
  }
  window.KPCCat = {
    get: () => Object.assign({}, S), set(o) { S = Object.assign({}, S, o || {}); SV('kpcCat', S); },
    supported: () => 'serial' in navigator, connect, disconnect, ports, usePort, pickNew, forget, connected: () => !!(port && writer), tune, read, follow, ptt,
    onStatus(fn) { subs.push(fn); }, kind, PROTOS: Object.keys(PROTOS), RADIOS, RADIO, fillSelect, pickRadio, cw, cwCan, cwStop, keyLine
  };

  /* ---- QRZ logbook (ACTION=INSERT with the logbook's own API key; needs a QRZ XML/logbook subscription) ---- */
  let Z = Object.assign({ on: false, key: '' }, LS('kpcQrz') || {});
  /* QRZ answers web pages but doesn't let them read the answer (no CORS, checked Oct 17). With the KPC QRZ relay
     (kpc-qrz-relay.json url = a Google Apps Script web app) the page gets QRZ's real answer; without it, it sends ONCE
     straight to QRZ (before Oct 17 it sent twice) and can only say 'sent'. */
  let RELAY = null;
  const relayUrl = () => RELAY || (RELAY = fetch('kpc-qrz-relay.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : {}).then(j => (j && /^https:\/\/script\.google(usercontent)?\.com\//.test(j.url || '') ? j.url : '')).catch(() => ''));
  const reasonOf = t => decodeURIComponent(((/REASON=([^&]*)/.exec(t) || [, ''])[1]).replace(/\+/g, ' ')).trim();
  async function viaRelay(action, rec) {
    const u = await relayUrl(); if (!u) return null;
    try { const r = await fetch(u, { method: 'POST', body: JSON.stringify({ key: Z.key, action, adif: rec || '' }) }); const j = await r.json(); return String(j.reply || ''); } catch (e) { return null; }
  }
  window.KPCQrz = {
    get: () => Object.assign({}, Z), set(o) { Z = Object.assign({}, Z, o || {}); SV('kpcQrz', Z); }, on: () => !!(Z.on && Z.key),
    relay: async () => !!(await relayUrl()),
    /* QRZ's OWN answer in a new tab (no relay needed): a normal form post opens logbook.qrz.com/api in a tab, and QRZ's
       plain-text reply (RESULT=OK / FAIL / AUTH + REASON) shows right there (Oct 17, Brandon: 'qrz still not working') */
    showAnswer(action, rec) {
      if (!Z.key) return false;
      const f = document.createElement('form'); f.method = 'POST'; f.action = 'https://logbook.qrz.com/api'; f.target = '_blank'; f.style.display = 'none';
      const add = (n, v) => { const i = document.createElement('input'); i.type = 'hidden'; i.name = n; i.value = v; f.appendChild(i); };
      add('KEY', Z.key); add('ACTION', action); if (action === 'INSERT') add('ADIF', rec || '');
      document.body.appendChild(f); f.submit(); setTimeout(() => f.remove(), 2000); return true;
    },
    async test() {   /* ACTION=STATUS: is the key good? (needs the relay to see the answer) */
      if (!Z.key) return { ok: false, msg: 'No QRZ logbook key saved.' };
      const t = await viaRelay('STATUS'); if (t == null) return { ok: null, msg: 'A web page can\'t see QRZ\'s answer without the KPC QRZ relay, so this test can\'t run yet. Log one contact and check your QRZ logbook.' };
      if (/RESULT=OK/.test(t)) { const n = (/COUNT=(\d+)/.exec(t) || [])[1], c = (/CALLSIGN=([^&]*)/.exec(t) || [])[1]; return { ok: true, msg: `Key works${c ? ' for ' + decodeURIComponent(c) : ''}${n ? ' · ' + n + ' contacts in that logbook' : ''}.` }; }
      return { ok: false, msg: 'QRZ said: ' + (reasonOf(t) || t.slice(0, 120)) + (/AUTH/.test(t) ? ' (check the key: QRZ.com → Logbook → Settings → API key; it needs a QRZ subscription that includes the logbook API)' : '') };
    },
    async send(rec) {
      if (!Z.key) return { ok: false, msg: 'No QRZ logbook key saved.' };
      const t = await viaRelay('INSERT', rec);
      if (t != null) { const ok = /RESULT=(OK|REPLACE)/.test(t), dup = /duplicate/i.test(t);
        return { ok: ok || dup, sure: true, msg: ok ? 'Saved in your QRZ logbook.' : dup ? 'Already in your QRZ logbook.' : 'QRZ said: ' + (reasonOf(t) || t.slice(0, 120)) }; }
      try { await fetch('https://logbook.qrz.com/api', { method: 'POST', body: new URLSearchParams({ KEY: Z.key, ACTION: 'INSERT', ADIF: rec }), mode: 'no-cors' });
        return { ok: true, sure: false, msg: 'Sent to QRZ. (A web page can\'t see QRZ\'s reply, so check your QRZ logbook once to be sure.)' }; }
      catch (e) { return { ok: false, msg: 'Could not reach QRZ (no signal?). Download your log for QRZ later.' }; }
    }
  };
})();

/* KPC radio control (CAT) + QRZ logbook sender — shared by the members Hunters Lounge and its CAT & QRZ tab (Brandon Oct 17 2026).
   CAT uses the browser's Web Serial (Chrome / Edge on a computer, plugged in by USB). Settings live only in this browser
   (localStorage kpcCat). The QRZ logbook key lives only in this browser too (localStorage kpcQrz) and goes only to logbook.qrz.com.

   window.KPCCat: get(), set(o), supported(), connect(ask), connected(), tune(kHz, mode) -> Promise<bool>, read() -> {khz, mode}|null,
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
    if (!('serial' in navigator)) { say('This browser can\'t talk to a radio. Use Chrome or Edge on a computer.', false); return false; }
    if (port && writer) return true;
    try {
      const ps = await navigator.serial.getPorts(); // a radio this browser was allowed before (no question asked)
      if (ps.length) return await openPort(ps[0]);
      if (!ask) return false;
      return await openPort(await navigator.serial.requestPort());
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
  function follow(fn) {
    if (fol) clearInterval(fol); fol = null; if (!fn) return; let last = '';
    fol = setInterval(async () => { if (!S.on || !S.follow || !port || document.hidden) return; const r = await read(); if (!r) return; const k = r.khz + '|' + r.mode; if (k !== last) { last = k; fn(r); } }, 2000);
  }
  window.KPCCat = {
    get: () => Object.assign({}, S), set(o) { S = Object.assign({}, S, o || {}); SV('kpcCat', S); },
    supported: () => 'serial' in navigator, connect, disconnect, connected: () => !!(port && writer), tune, read, follow,
    onStatus(fn) { subs.push(fn); }, kind, PROTOS: Object.keys(PROTOS)
  };

  /* ---- QRZ logbook (ACTION=INSERT with the logbook's own API key; needs a QRZ XML/logbook subscription) ---- */
  let Z = Object.assign({ on: false, key: '' }, LS('kpcQrz') || {});
  window.KPCQrz = {
    get: () => Object.assign({}, Z), set(o) { Z = Object.assign({}, Z, o || {}); SV('kpcQrz', Z); }, on: () => !!(Z.on && Z.key),
    async send(rec) {
      if (!Z.key) return { ok: false, msg: 'No QRZ logbook key saved.' };
      const body = new URLSearchParams({ KEY: Z.key, ACTION: 'INSERT', ADIF: rec });
      try { // QRZ answers like RESULT=OK&LOGID=… when the browser is allowed to read the answer
        const r = await fetch('https://logbook.qrz.com/api', { method: 'POST', body });
        const t = await r.text(); const ok = /RESULT=(OK|REPLACE)/.test(t);
        return { ok, sure: true, msg: ok ? 'Saved in your QRZ logbook.' : 'QRZ said: ' + decodeURIComponent((/REASON=([^&]*)/.exec(t) || [, t.slice(0, 120)])[1]).replace(/\+/g, ' ') };
      } catch (e) { // QRZ's server doesn't let web pages read its answer: send it anyway, we just can't see the reply
        try { await fetch('https://logbook.qrz.com/api', { method: 'POST', body, mode: 'no-cors' }); return { ok: true, sure: false, msg: 'Sent to QRZ (QRZ doesn\'t let a web page see its reply, so check your QRZ logbook once).' }; }
        catch (e2) { return { ok: false, msg: 'Could not reach QRZ (no signal?). Download your log for QRZ later.' }; }
      }
    }
  };
})();

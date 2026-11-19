/* KPC app: 📻 WEB RADIO = listen through a public KiwiSDR (Nov 10 2026; Brandon: 'kiwi sdr for sure').
   A KiwiSDR is somebody's receiver on the internet. We open one WebSocket to it (ws(s)://host:port/kiwi/<time>/SND), say what we want
   ('SET mod=usb low_cut=300 high_cut=2700 freq=14250.000'), and it sends back 12 kHz audio, IMA-ADPCM packed (Kiwi's own flavour: low nibble
   first, decoder state kept across frames) plus an S-meter value in every frame. We unpack it, resample to the sound card's rate and play it.
   LISTENING ONLY: nothing here can transmit.
   Frame:  'SND' flags(1) seq(4) smeter(2, big-endian: dBm = 0.1*v - 127) data…   flags 0x10 = ADPCM (state carried frame to frame), 0x02 = ADC overload, 0x08 = stereo, 0x80 = little-endian (camping only) — as in jks-prv/kiwiclient
           'MSG' key=value key=value …  (sample_rate, audio_rate, too_busy, badp, down …)
   Finding one: rx.linkfanel.net/kiwisdr_com.js (the list kiwisdr.com is built from) is read as TEXT, never run; kept 24 h in kpcKiwiList.
   Screens: STATION → 📻 WEB RADIO card, and a 📻 WEB RADIO button next to CONNECT THE RADIO on the RADIO screen; both open one sheet.
   FOLLOW SPOT TAPS: AP 'spot-tune' (kpc-spots.js) moves the Kiwi too.
   KPCKiwi.tap(fn): fn(Float32Array, 12000) for every decoded 12 kHz block. HOOK ONLY: the FT8 screen (kpc-digi.js) is NOT wired to it yet;
   to hunt FT8 with no radio, kpc-digi.js would take its 'rx' blocks from here instead of from the sound card.
   Settings: localStorage kpcKiwi (freq, mode, volume, follow; the password is never saved), kpcKiwiList, kpcKiwiRecent (last 5). */
(function (G) {
  'use strict';
  const AP = G.KPCApp; if (!AP) return;
  const $ = id => document.getElementById(id), esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const C = Object.assign({ khz: 14250, mode: 'usb', vol: 80, mute: false, follow: true }, LS('kpcKiwi', {}));
  const save = () => SV('kpcKiwi', C);
  const ST = { conn: 'off', url: '', name: '', err: '', dbm: null, rate: 12000, wide: false, pw: '' };
  const TAPS = [];
  const CUTS = { usb: [300, 2700], lsb: [-2700, -300], cw: [300, 800], am: [-4500, 4500] };   /* cw: Kiwi 'freq' is the carrier; 300..800 Hz above it is a 550 Hz-centred window */
  const MODES = ['usb', 'lsb', 'cw', 'am'];

  /* ---------------- IMA ADPCM (Kiwi's variant) ---------------- */
  const STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767];
  const IDX = [-1, -1, -1, -1, 2, 4, 6, 8];
  function Ima() { this.reset(); }
  Ima.prototype.reset = function () { this.p = 0; this.i = 0; };
  Ima.prototype.decode = function (u8, off) {
    const n = (u8.length - off) * 2, out = new Float32Array(n); let p = this.p, ix = this.i, k = 0;
    for (let j = off; j < u8.length; j++) for (let h = 0; h < 2; h++) {
      const c = h ? u8[j] >> 4 : u8[j] & 15, st = STEP[ix];
      let d = st >> 3; if (c & 4) d += st; if (c & 2) d += st >> 1; if (c & 1) d += st >> 2;
      p += c & 8 ? -d : d; if (p > 32767) p = 32767; else if (p < -32768) p = -32768;
      ix += IDX[c & 7]; if (ix < 0) ix = 0; else if (ix > 88) ix = 88;
      out[k++] = p / 32768;
    }
    this.p = p; this.i = ix; return out;
  };

  /* ---------------- the list ---------------- */
  /* kiwisdr_com.js text → [{url,name,loc,la,lo,users,max,lo_hz,hi_hz}] (offline ones left out). Never evaluated. */
  function parseList(text) {
    text = String(text || ''); const a = text.indexOf('['), b = text.lastIndexOf(']'); if (a < 0 || b < a) return [];
    const body = text.slice(a, b + 1); let arr = null;
    try { arr = JSON.parse(body.replace(/,\s*([\]}])/g, '$1')); } catch (e) { arr = null; }
    if (!Array.isArray(arr)) {
      arr = []; const re = /\{([^{}]*)\}/g; let m;
      while ((m = re.exec(body))) { const o = {}, kv = /["']?([A-Za-z_]\w*)["']?\s*:\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[-+\d.eE]+|true|false|null)/g; let x;
        while ((x = kv.exec(m[1]))) { let v = x[2]; if (/^["']/.test(v)) { try { v = v[0] === '"' ? JSON.parse(v) : v.slice(1, -1); } catch (e) { v = v.slice(1, -1); } } o[x[1]] = v; }
        arr.push(o); }
    }
    const out = [];
    arr.forEach(o => {
      if (!o || typeof o !== 'object' || !o.url) return;
      if (/^y/i.test(String(o.offline || '')) || /^(offline|down)/i.test(String(o.status || ''))) return;
      const g = /(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/.exec(String(o.gps || '')), bd = /(\d+)\s*-\s*(\d+)/.exec(String(o.bands || ''));
      out.push({ url: String(o.url).trim(), name: String(o.name || o.url).trim(), loc: String(o.loc || '').trim(), la: g ? +g[1] : null, lo: g ? +g[2] : null,
        users: +o.users || 0, max: +o.users_max || 0, lo_hz: bd ? +bd[1] : 0, hi_hz: bd ? +bd[2] : 30000000 });
    });
    return out;
  }
  const rad = Math.PI / 180;
  function kmBetween(a, b) { const h = Math.sin((b.la - a.la) * rad / 2) ** 2 + Math.cos(a.la * rad) * Math.cos(b.la * rad) * Math.sin((b.lo - a.lo) * rad / 2) ** 2; return 6371 * 2 * Math.asin(Math.sqrt(h)); }
  const myLL = () => { const g = AP.myGrid && AP.myGrid(); return g ? AP.gridLL(g) : null; };
  /* nearest first, free slots only (users < users_max), covering khz when it is given */
  function rank(list, me, khz) {
    const hz = khz ? khz * 1000 : 0;
    const r = (list || []).filter(k => k.max > 0 && k.users < k.max && (!hz || (hz >= k.lo_hz && hz <= k.hi_hz))).map(k => Object.assign({}, k, { km: me && k.la != null ? kmBetween(me, { la: k.la, lo: k.lo }) : null }));
    r.sort((a, b) => (a.km == null) - (b.km == null) || (a.km || 0) - (b.km || 0) || (a.users - b.users));
    return r;
  }
  let LIST = LS('kpcKiwiList', null), listBusy = false, listErr = '';
  async function loadList(force) {
    if (!force && LIST && LIST.list && Date.now() - LIST.t < 864e5) return LIST.list;
    if (listBusy) return LIST ? LIST.list : [];
    listBusy = true; listErr = ''; paintList();
    try {
      let text = '', last = '';
      for (const u of ['http://rx.linkfanel.net/kiwisdr_com.js', 'https://rx.linkfanel.net/kiwisdr_com.js']) {
        try {
          if (AP.net.canRaw && AP.net.canRaw()) { const r = await AP.net.raw(u, { ms: 20000 }); if (r.ok && r.text) { text = r.text; break; } last = r.err || 'HTTP ' + r.status; }
          else { const r = await AP.net.fetch(u, {}, 20000); if (r.ok) { text = await r.text(); break; } last = 'HTTP ' + r.status; }
        } catch (e) { last = String(e.message || e); }
      }
      const list = parseList(text);
      if (!list.length) throw new Error(last || 'the list came back empty');
      LIST = { t: Date.now(), list }; SV('kpcKiwiList', LIST);
    } catch (e) { listErr = 'Could not load the list of receivers (' + String(e.message || e).slice(0, 80) + ').' + (LIST ? ' Showing the saved one.' : ' Type an address instead.'); }
    listBusy = false; paintList(); return LIST ? LIST.list : [];
  }
  const recent = () => LS('kpcKiwiRecent', []).filter(r => r && r.url).slice(0, 5);
  function remember(url, name) { const r = recent().filter(x => x.url !== url); r.unshift({ url, name: name || url }); SV('kpcKiwiRecent', r.slice(0, 5)); }

  /* address → { ws:'ws://host:port', secure, host } */
  function addr(s) {
    s = String(s || '').trim(); if (!s) return null;
    s = s.replace(/^http(s?):\/\//i, (m, x) => 'ws' + x + '://');
    if (!/^wss?:\/\//i.test(s)) s = 'ws://' + s;
    let u; try { u = new URL(s.replace(/^ws/i, 'http')); } catch (e) { return null; }
    if (!u.hostname) return null;
    const secure = /^wss/i.test(s), port = u.port || (secure ? '' : '8073');
    return { ws: (secure ? 'wss://' : 'ws://') + u.hostname + (port ? ':' + port : ''), secure, host: u.host };
  }
  /* the website (https page) may not open ws:// ; the installed apps may */
  function blocked(a, proto, native) {
    a = typeof a === 'string' ? addr(a) : a;
    return !!(a && !a.secure && (proto === undefined ? location.protocol : proto) === 'https:' && !(native === undefined ? AP.native : native));
  }
  const BLOCKMSG = 'This receiver only works in the installed app (Android / Windows).';

  /* ---------------- sound out ---------------- */
  /* queue: ~300 ms of cushion; waits to fill first, drops the oldest if it gets past 700 ms (a worklet gets this function as text) */
  function mkQ(sr) {
    const a = [], want = Math.round(sr * 0.3), max = Math.round(sr * 0.7); let have = 0, pos = 0, play = false;
    return {
      push(f) { a.push(f); have += f.length; if (have > max) { while (have > want && a.length > 1) { have -= a[0].length - pos; a.shift(); pos = 0; } } },
      pull(o) {
        let k = 0; if (!play && have >= want) play = true;
        if (play) { while (k < o.length && a.length) { const f = a[0]; o[k++] = f[pos++]; have--; if (pos >= f.length) { a.shift(); pos = 0; } } if (!a.length) play = false; }
        while (k < o.length) o[k++] = 0;
      },
      have() { return have; }
    };
  }
  const WSRC = `const mk=${mkQ.toString()};class K extends AudioWorkletProcessor{constructor(){super();this.q=mk(sampleRate);this.port.onmessage=e=>{if(e.data&&e.data.f)this.q.push(e.data.f);};}process(i,o){this.q.pull(o[0][0]);return true;}}registerProcessor('kiwi-q',K);`;
  const OUT = { ctx: null, gain: null, node: null, q: null, last: 0, px: 0, py: 0, ph: 0, dc: 0, dcx: 0 };
  async function audioOn() {
    if (OUT.ctx) { try { await OUT.ctx.resume(); } catch (e) {} return OUT.ctx.sampleRate; }
    const AC = G.AudioContext || G.webkitAudioContext; if (!AC) return 48000;
    const ctx = new AC(), gain = ctx.createGain(); gain.connect(ctx.destination); OUT.ctx = ctx; OUT.gain = gain; setVol();
    const alive = () => OUT.ctx === ctx;   /* a DISCONNECT while the worklet loads closes this context */
    try {
      if (!ctx.audioWorklet) throw 0;
      const url = URL.createObjectURL(new Blob([WSRC], { type: 'text/javascript' })); await ctx.audioWorklet.addModule(url); URL.revokeObjectURL(url);
      if (!alive()) return ctx.sampleRate;
      const n = new AudioWorkletNode(ctx, 'kiwi-q', { numberOfInputs: 0, outputChannelCount: [1] }); n.connect(gain); OUT.node = n;
    } catch (e) {
      if (!alive()) return ctx.sampleRate;
      const q = mkQ(ctx.sampleRate), sp = ctx.createScriptProcessor(2048, 0, 1); sp.onaudioprocess = ev => q.pull(ev.outputBuffer.getChannelData(0)); sp.connect(gain); OUT.q = q; OUT.node = sp;
    }
    try { await ctx.resume(); } catch (e) {} return ctx.sampleRate;
  }
  function audioOff() { try { if (OUT.node) OUT.node.disconnect(); } catch (e) {} try { if (OUT.ctx) OUT.ctx.close(); } catch (e) {} OUT.ctx = OUT.node = OUT.gain = OUT.q = null; OUT.px = OUT.py = OUT.ph = OUT.dc = OUT.dcx = 0; }
  function setVol() { if (OUT.gain) OUT.gain.gain.value = C.mute ? 0 : Math.pow((+C.vol || 0) / 100, 2) * 1.5; }
  /* 12 kHz → context rate, linear interpolation, with a 20 Hz DC blocker (ADPCM has no leak, so a restarted decoder could leave an offset) */
  function play(f) {
    if (!OUT.ctx) return; const ratio = ST.rate / OUT.ctx.sampleRate, out = []; let ph = OUT.ph, px = OUT.px, dc = OUT.dc, dcx = OUT.dcx;
    const n = f.length, src = i => { const x = f[i]; const y = x - dcx + 0.9953 * dc; dcx = x; dc = y; return y; };
    /* DC-block the block first, then interpolate */
    const g = new Float32Array(n); for (let i = 0; i < n; i++) g[i] = src(i);
    OUT.dc = dc; OUT.dcx = dcx;
    while (ph < n) { const i = Math.floor(ph), fr = ph - i, a = i < 0 ? px : g[i], b = i + 1 < n ? g[i + 1] : null; if (b == null) break; out.push(a + (b - a) * fr); ph += ratio; }
    OUT.px = g[n - 1]; OUT.ph = ph - n;
    if (out.length) { const o = Float32Array.from(out); if (OUT.q) OUT.q.push(o); else if (OUT.node && OUT.node.port) OUT.node.port.postMessage({ f: o }, [o.buffer]); }
  }

  /* ---------------- the connection ---------------- */
  let ws = null, kaT = null, gotAny = false, ima = new Ima(), wantBare = false, cTO = null;
  function setErr(t) { ST.err = t; paint(); }
  function send(t) { try { if (ws && ws.readyState === 1) ws.send(t); } catch (e) {} }
  function sendTune() {
    const m = MODES.includes(C.mode) ? C.mode : 'usb', c = CUTS[m].slice(); if (ST.wide && m === 'usb') { c[0] = 100; c[1] = 3000; }
    send('SET mod=' + m + ' low_cut=' + c[0] + ' high_cut=' + c[1] + ' freq=' + (+C.khz).toFixed(3));
  }
  function connect(url, name, pw) {
    const a = addr(url); if (!a) { setErr('Type the receiver as host:port, for example myradio.example.org:8073.'); return false; }
    if (blocked(a)) { disconnect(true); ST.url = a.ws; ST.name = name || a.host; setErr(BLOCKMSG); return false; }
    disconnect(true); ST.url = a.ws; ST.name = name || a.host; ST.err = ''; ST.dbm = null; ST.conn = 'connecting'; if (pw !== undefined) ST.pw = pw; ST.wide = !!ST.wide;
    gotAny = false; ima = new Ima(); open(a, wantBare = false); paint(); return true;
  }
  function open(a, bare) {
    let w; const path = (bare ? '/kiwi/' : '/') + Date.now() + '/SND';   /* Nov 10 review: '/<time>/SND' first, like jks-prv/kiwiclient (the KiwiSDR author's own client); '/kiwi/…' as the second try */
    try { w = new WebSocket(a.ws + path); } catch (e) { fail('Could not open ' + a.host + ' (' + String(e.message || e).slice(0, 60) + ').'); return; }
    w.binaryType = 'arraybuffer'; ws = w;
    clearTimeout(cTO); cTO = setTimeout(() => { if (ws === w && !gotAny) { fail('No answer from ' + a.host + '. It may be busy, off, or the address is wrong.'); } }, 12000);
    w.onopen = async () => {
      if (ws !== w) return;
      const rate = Math.round(await audioOn()); if (ws !== w) return;
      send('SET auth t=kiwi p=' + (ST.pw || '')); send('SET ident_user=KPC-App');
      send('SET AR OK in=12000 out=' + rate); send('SET squelch=0 max=0'); send('SET compression=1');
      sendTune(); send('SET agc=1 hang=0 thresh=-100 slope=6 decay=1000 manGain=50'); send('SET keepalive');
      clearInterval(kaT); kaT = setInterval(() => send('SET keepalive'), 5000);
    };
    w.onmessage = e => { if (ws === w) frame(e.data); };
    w.onerror = () => {};
    w.onclose = () => {
      if (ws !== w) return; clearInterval(kaT); clearTimeout(cTO);
      if (!gotAny && !bare && ST.conn === 'connecting') { open(a, true); return; }   /* second try with /kiwi/ in the path */
      if (ST.conn !== 'off' && !ST.err) ST.err = gotAny ? 'The receiver closed the connection (many Kiwis do after a time limit, or when someone else needs the slot).' : 'Could not reach ' + a.host + '.';
      ws = null; ST.conn = 'off'; audioOff(); paint();
    };
  }
  function fail(t) { const w = ws; ws = null; try { if (w) w.close(); } catch (e) {} clearInterval(kaT); clearTimeout(cTO); ST.conn = 'off'; ST.err = t; audioOff(); paint(); }
  function disconnect(quiet) {
    const w = ws; ws = null; clearInterval(kaT); clearTimeout(cTO);
    if (w) { try { w.send('SET keepalive'); } catch (e) {} try { w.close(); } catch (e) {} }
    ST.conn = 'off'; if (!quiet) ST.err = ''; audioOff(); ST.dbm = null; paint();
  }
  const MSGS = { too_busy: 'That receiver is full (all its slots are taken right now). Pick another one.', badp: 'That receiver wants a password (or the one typed is wrong).', down: 'That receiver is down for maintenance. Pick another one.', inactivity_timeout: 'The receiver stopped the connection for being idle.', redirect: '' };
  function frame(d) {
    if (typeof d === 'string' || !d || d.byteLength < 3) return;
    const u = new Uint8Array(d), tag = String.fromCharCode(u[0], u[1], u[2]);
    if (tag === 'MSG') {
      gotAny = true; const txt = new TextDecoder().decode(u.subarray(3)).trim();
      txt.split(/\s+/).forEach(kv => {
        const i = kv.indexOf('='), k = i < 0 ? kv : kv.slice(0, i); let v = i < 0 ? '' : kv.slice(i + 1); try { v = decodeURIComponent(v); } catch (e) {}
        if (k === 'sample_rate' && +v > 1000 && +v < 50000) ST.rate = Math.round(+v);
        else if (k === 'too_busy' || k === 'down' || k === 'inactivity_timeout') { if (k === 'inactivity_timeout' || +v !== 0 || v === '') { fail(MSGS[k]); } }
        else if (k === 'badp') { if (+v === 1) fail(MSGS.badp); }
      });
      return;
    }
    if (tag === 'SND' && u.length > 10) {
      if (!gotAny) gotAny = true; if (ST.conn === 'connecting') { ST.conn = 'on'; clearTimeout(cTO); if (ST.name) remember(ST.url, ST.name); paint(); }
      const fl = u[3]; ST.dbm = ((u[8] << 8) | u[9]) * 0.1 - 127;
      let f;
      if (fl & 0x10) { f = ima.decode(u, 10); }   /* Nov 10 review: kiwiclient keeps the ADPCM state across every frame and has no 0x01 flag (0x02 = ADC overload) */
      else { const n = (u.length - 10) >> 1, dv = new DataView(d, 10, n * 2); f = new Float32Array(n); for (let i = 0; i < n; i++) f[i] = dv.getInt16(i * 2, !!(fl & 0x80)) / 32768; }
      for (let i = 0; i < TAPS.length; i++) { try { TAPS[i](f, ST.rate); } catch (e) { console.error(e); } }
      play(f); const now = Date.now(); if (now - lastP > 250) { lastP = now; paintMeter(); }
    }
  }
  let lastP = 0;

  /* ---------------- tuning ---------------- */
  function tune(khz, mode, o) {
    khz = +khz; if (!isFinite(khz) || khz < 10 || khz > 30000) { AP.toast('A Kiwi hears 10 kHz to 30 MHz.', 3000, 'bad'); return false; }
    C.khz = Math.round(khz * 1000) / 1000; if (mode) { mode = String(mode).toLowerCase(); if (MODES.includes(mode)) C.mode = mode; }
    ST.wide = !!(o && o.wide); save(); if (ST.conn !== 'off') sendTune(); paint(); return true;
  }
  /* a spot's mode word → a Kiwi mode */
  function modeFor(khz, m) {
    m = String(m || '').toUpperCase();
    if (/^CW/.test(m)) return { mode: 'cw' };
    if (/^(FT8|FT4|JS8|WSPR|DATA|RTTY|PSK|MFSK|OLIVIA|APRS|PKT|DIGI)/.test(m)) return { mode: 'usb', wide: true };
    if (m === 'AM') return { mode: 'am' };
    if (m === 'LSB') return { mode: 'lsb' };
    if (m === 'USB') return { mode: 'usb' };
    return { mode: khz < 10000 ? 'lsb' : 'usb' };   /* SSB / PHONE / nothing: the usual side for the band */
  }
  AP.on('spot-tune', s => {
    if (!C.follow || ST.conn === 'off' || !s || !isFinite(+s.khz)) return;
    const m = modeFor(+s.khz, s.mode); if (tune(+s.khz, m.mode, m)) AP.toast('📻 Web radio: ' + (+s.khz / 1000).toFixed(3) + ' MHz ' + m.mode.toUpperCase(), 2500, 'log');
  });

  /* ---------------- screens ---------------- */
  const fmt = () => (+C.khz / 1000).toFixed(3) + ' ' + C.mode.toUpperCase();
  function sText(dbm) {
    if (dbm == null) return ''; if (dbm >= -73) { const p = Math.round((dbm + 73) / 10) * 10; return p > 0 ? 'S9+' + p : 'S9'; }
    return 'S' + Math.max(0, Math.round(9 + (dbm + 73) / 6));
  }
  const stText = () => ST.conn === 'on' ? 'Listening on ' + ST.name + ' · ' + fmt() + (ST.dbm == null ? '' : ' · ' + sText(ST.dbm)) : ST.conn === 'connecting' ? 'Connecting to ' + ST.name + '…' : ST.err ? ST.err : 'Not connected.';
  function paintMeter() {
    document.querySelectorAll('.kw-sm i').forEach(i => { i.style.width = (ST.dbm == null || ST.conn !== 'on' ? 0 : Math.max(0, Math.min(100, (ST.dbm + 127) / 114 * 100))) + '%'; });
    document.querySelectorAll('.kw-st').forEach(e => { e.textContent = stText(); e.className = 'st kw-st' + (ST.conn === 'on' ? ' ok' : ST.err ? ' bad' : ''); });
  }
  function paint() {
    paintMeter(); const on = ST.conn !== 'off';
    const web = !!G.KPC_WEB || (location.protocol === 'https:' && !AP.native); document.querySelectorAll('.kw-web').forEach(e => { e.hidden = !web; });   /* Nov 10 review: the website copy */
    document.querySelectorAll('.kw-go').forEach(b => { b.textContent = on ? '⏹ DISCONNECT' : '▶ CONNECT'; b.classList.toggle('halt', on); });
    const f = $('kwKhz'); if (f && document.activeElement !== f) f.value = (+C.khz).toFixed(3);
    document.querySelectorAll('[data-kwm]').forEach(b => b.classList.toggle('on', b.dataset.kwm === C.mode));
    document.querySelectorAll('.kw-fol').forEach(b => { b.classList.toggle('on', !!C.follow); const x = b.querySelector('b'); if (x) x.textContent = C.follow ? 'ON' : 'OFF'; });
    document.querySelectorAll('.kw-mute').forEach(b => { b.textContent = C.mute ? '🔇 MUTED' : '🔊 MUTE'; b.classList.toggle('on', !!C.mute); });
    const h = $('kwHttps'); if (h) { const a = addr(($('kwAddr') || {}).value); h.hidden = !blocked(a); }
  }
  function paintList() {
    const el = $('kwList'); if (!el) return;
    const me = myLL(), list = LIST && LIST.list ? rank(LIST.list, me, C.khz).slice(0, 12) : [];
    el.innerHTML = (listBusy ? '<p class="hint">Loading the list of receivers…</p>' : '') + (listErr ? '<p class="hint bad">' + esc(listErr) + '</p>' : '')
      + (!me ? '<p class="hint">Set your grid (STATION → My station) to sort by distance.</p>' : '')
      + list.map((k, i) => `<button type="button" class="kw-row" data-kwi="${i}"><b>${esc(k.name)}</b><span>${esc(k.loc)}${k.km != null ? ' · ' + esc(AP.dist(k.km)) : ''} · ${k.users}/${k.max} users</span></button>`).join('')
      + (LIST && LIST.list && !list.length && !listBusy ? '<p class="hint">No receiver with a free slot covers that frequency.</p>' : '');
    el._rows = list;
  }
  const CSS = `.kw-row{display:block;width:100%;text-align:left;margin:4px 0;padding:8px 10px;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font:inherit;cursor:pointer}
.kw-row b{display:block;font-size:14px}.kw-row span{display:block;font-size:12px;color:var(--sub)}
.kw-sm{height:12px;border-radius:6px;background:var(--panel2);border:1px solid var(--line);overflow:hidden;margin:8px 0}.kw-sm i{display:block;height:100%;width:0;background:linear-gradient(90deg,#3fb950,#E8B84A,#f85149);transition:width .2s}
.kw-f{display:flex;gap:6px;align-items:center;margin:8px 0}.kw-f input{flex:1;min-width:0;font:700 20px var(--mono);text-align:center}.kw-f button{min-width:44px}
.kw-st.bad{border-left:4px solid var(--red,#f85149)}.kw-vol{width:100%}.kw-ch{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}`;
  const st0 = document.createElement('style'); st0.textContent = CSS; document.head.appendChild(st0);

  const LIMITS = `This is somebody else's receiver, so be kind: use one connection, and disconnect when you are done. Many Kiwis cut you off after about an hour, or when they get busy. It is <b>listening only</b>: you cannot transmit through it. The audio runs a second or so behind real time.`;
  function openSheet() {
    AP.sheet('📻 Web radio (KiwiSDR)', `<p class="hint" style="margin-top:0">${LIMITS}</p>
      <div class="st kw-st"></div>
      <div class="kw-sm" aria-label="Signal strength"><i></i></div>
      <div class="kw-f"><button type="button" class="b" data-kws="-1">−1</button><button type="button" class="b" data-kws="-0.1">−0.1</button><input id="kwKhz" inputmode="decimal" aria-label="Frequency in kHz"><button type="button" class="b" data-kws="0.1">+0.1</button><button type="button" class="b" data-kws="1">+1</button></div>
      <div class="kw-ch">${MODES.map(m => `<button type="button" class="chip" data-kwm="${m}">${m.toUpperCase()}</button>`).join('')}<span class="hint" style="align-self:center">kHz</span></div>
      <div class="row"><input class="kw-vol" id="kwVol" type="range" min="0" max="100" aria-label="Volume" style="flex:1"><button type="button" class="b kw-mute"></button></div>
      <button type="button" class="b upsw kw-fol"><b></b> <span>FOLLOW SPOT TAPS</span></button>
      <div class="row"><button type="button" class="b gold kw-go"></button></div>
      <h2 style="margin:14px 0 6px;font-size:12px;letter-spacing:.14em">RECEIVER</h2>
      <label class="e">ADDRESS (host:port)<input id="kwAddr" spellcheck="false" autocapitalize="off" placeholder="myradio.example.org:8073" value="${esc(ST.url ? ST.url.replace(/^wss?:\/\//, '') : '')}"></label>
      <label class="e">PASSWORD (only if it asks)<input id="kwPw" type="password" autocomplete="off" value="${esc(ST.pw)}"></label>
      <p class="hint bad" id="kwHttps" hidden>${BLOCKMSG}</p>
      <div class="kw-ch" id="kwRec">${recent().map((r, i) => `<button type="button" class="chip" data-kwr="${i}">${esc(r.name)}</button>`).join('')}</div>
      <div class="row"><button type="button" class="b" id="kwRef">↻ REFRESH LIST</button></div>
      <div id="kwList"></div>`, () => { const sb = $('sheetB'); if (sb) sb.onclick = null; });
    $('kwVol').value = C.vol; $('kwVol').oninput = () => { C.vol = +$('kwVol').value; C.mute = false; setVol(); save(); paint(); };
    const b = $('sheetB'), rec = recent(), go = (url, name) => { $('kwAddr').value = url.replace(/^\w+:\/\//, ''); connect(url, name, $('kwPw').value); };
    b.onclick = e => {
      const t = e.target.closest('button'); if (!t) return;
      if (t.dataset.kws) tune(+C.khz + +t.dataset.kws, C.mode);
      else if (t.dataset.kwm) tune(C.khz, t.dataset.kwm);
      else if (t.classList.contains('kw-mute')) { C.mute = !C.mute; setVol(); save(); paint(); }
      else if (t.classList.contains('kw-fol')) { C.follow = !C.follow; save(); paint(); }
      else if (t.classList.contains('kw-go')) { if (ST.conn !== 'off') disconnect(); else connect($('kwAddr').value, '', $('kwPw').value); }
      else if (t.dataset.kwr != null) { const r = rec[+t.dataset.kwr]; if (r) go(r.url, r.name); }
      else if (t.id === 'kwRef') loadList(true);
      else if (t.dataset.kwi != null) { const k = ($('kwList')._rows || [])[+t.dataset.kwi]; if (k) go(k.url, k.name); }
    };
    $('kwKhz').onchange = () => { const v = parseFloat($('kwKhz').value); if (isFinite(v)) tune(v, C.mode); else paint(); };
    $('kwKhz').onkeydown = e => { if (e.key === 'Enter') $('kwKhz').onchange(); };
    $('kwAddr').oninput = paint;
    paint(); paintList(); loadList(false).then(paintList);
  }
  /* STATION card */
  function draw() {
    const st = $('scrStation'); if (!st || $('stKiwi')) return;
    const anchor = $('stRot') || $('stCx') || st.lastElementChild; if (!anchor) return;
    anchor.insertAdjacentHTML('beforebegin', `<section class="card" id="stKiwi" data-grp="web radio kiwisdr kiwi sdr receiver listen internet websdr"><h2>📻 WEB RADIO (KiwiSDR)</h2>
      <p class="hint" style="margin-top:0">Listen through a public KiwiSDR receiver anywhere in the world: pick one near you, tune it, and hear the band with no radio of your own. ${LIMITS}</p>
      <p class="hint bad kw-web" hidden>On the website (a browser page) most receivers can't be reached and the list may not load: browsers block them. Use the installed KPC app (Android / Windows) for the web radio.</p>
      <div class="st kw-st"></div><div class="row"><button type="button" class="b gold" id="kwOpen">📻 OPEN WEB RADIO</button><button type="button" class="b kw-go"></button></div></section>`);
    $('kwOpen').onclick = openSheet;
    st.querySelector('#stKiwi .kw-go').onclick = () => { if (ST.conn !== 'off') disconnect(); else openSheet(); };
    paint();
  }
  /* RADIO screen button */
  function radioBtn() {
    const s = $('rdSet'); if (!s || $('rdWeb')) return;
    s.insertAdjacentHTML('afterend', '<button type="button" class="b" id="rdWeb">📻 WEB RADIO</button>'); $('rdWeb').onclick = openSheet;
  }
  AP.on('screen', n => { if (n === 'station') draw(); if (n === 'radio') radioBtn(); });
  draw(); radioBtn();

  G.KPCKiwi = {
    tune, connect: (u, n, p) => connect(u, n, p), disconnect: () => disconnect(),
    state: () => Object.assign({}, ST, { khz: C.khz, mode: C.mode, follow: C.follow, vol: C.vol, mute: C.mute, smeter: ST.dbm, sText: sText(ST.dbm), text: stText(), pw: undefined }),
    tap: fn => { if (typeof fn !== 'function') return () => {}; TAPS.push(fn); return () => { const i = TAPS.indexOf(fn); if (i >= 0) TAPS.splice(i, 1); }; },
    open: openSheet, parseList, rank, addr, blocked, modeFor, loadList, list: () => (LIST && LIST.list) || [], S: C
  };
})(window);

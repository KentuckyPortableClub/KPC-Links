/* KPC ambient sounds, made in the browser (no recordings, nothing to license) — Oct 17 2026, Brandon.
   KPCAmbient.button(host, kind, opts) adds a small on/off button. kinds: 'fire' (campfire crackle; crickets too after dark,
   7 PM - 6 AM on the visitor's clock) and 'creek' (running water and birds). Always OFF until tapped; the choice is remembered
   per kind (localStorage kpcAmb:<kind>) but browsers still need a tap on the page before any sound can start. */
(function () {
  let AC = null, master = null, cur = null;
  const get = k => { try { return localStorage.getItem(k) === '1'; } catch (e) { return false; } }, put = (k, v) => { try { localStorage.setItem(k, v ? '1' : '0'); } catch (e) {} };
  function ctx() { if (!AC) { AC = new (window.AudioContext || window.webkitAudioContext)(); master = AC.createGain(); master.gain.value = 0; master.connect(AC.destination); } if (AC.state === 'suspended') AC.resume(); return AC; }
  function noise(sec, brown) { const b = AC.createBuffer(1, AC.sampleRate * sec, AC.sampleRate), d = b.getChannelData(0); let l = 0; for (let i = 0; i < d.length; i++) { const w = Math.random() * 2 - 1; if (brown) { l = (l + .02 * w) / 1.02; d[i] = l * 3.5; } else d[i] = w; } return b; }
  function loopSrc(buf) { const s = AC.createBufferSource(); s.buffer = buf; s.loop = true; s.start(); return s; }
  const night = () => { const h = new Date().getHours(); return h >= 19 || h < 6; };
  function fire() {
    const nodes = [], timers = [];
    const rumble = loopSrc(noise(3, true)), lp = AC.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 500; const rg = AC.createGain(); rg.gain.value = .35;
    rumble.connect(lp); lp.connect(rg); rg.connect(master); nodes.push(rumble);
    const lfo = AC.createOscillator(), lg = AC.createGain(); lfo.frequency.value = .13; lg.gain.value = .12; lfo.connect(lg); lg.connect(rg.gain); lfo.start(); nodes.push(lfo);
    const wn = noise(1, false);
    const crackle = () => { const t = AC.currentTime, s = AC.createBufferSource(), bp = AC.createBiquadFilter(), g = AC.createGain(); s.buffer = wn; bp.type = 'bandpass'; bp.frequency.value = 1800 + Math.random() * 3200; bp.Q.value = 1.2;
      const big = Math.random() < .08, peak = big ? .55 : .08 + Math.random() * .18, len = big ? .05 : .006 + Math.random() * .02;
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(peak, t + .002); g.gain.exponentialRampToValueAtTime(.0005, t + len); s.connect(bp); bp.connect(g); g.connect(master); s.start(t, Math.random() * .8, len + .02);
      timers.push(setTimeout(crackle, 25 + Math.random() * (Math.random() < .3 ? 450 : 120))); };
    crackle();
    if (night()) {
      const cricket = (pitch, gap) => { const t = AC.currentTime, o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = pitch; g.gain.value = 0; o.connect(g); g.connect(master); o.start(t); o.stop(t + .3);
        for (let i = 0; i < 3; i++) { g.gain.setValueAtTime(0, t + i * .045); g.gain.linearRampToValueAtTime(.025, t + i * .045 + .006); g.gain.linearRampToValueAtTime(0, t + i * .045 + .022); }
        timers.push(setTimeout(() => cricket(pitch, gap), gap * (0.85 + Math.random() * .3))); };
      cricket(4300, 820); timers.push(setTimeout(() => cricket(4650, 1010), 400));
    }
    return () => { timers.forEach(clearTimeout); nodes.forEach(n => { try { n.stop(); } catch (e) {} }); };
  }
  function creek() {
    const nodes = [], timers = [], wn = noise(4, false);
    [[700, .5, .28], [1600, .9, .16], [3400, 1.4, .07]].forEach(([f, q, v], i) => { const s = loopSrc(wn), bp = AC.createBiquadFilter(), g = AC.createGain(); bp.type = 'bandpass'; bp.frequency.value = f; bp.Q.value = q; g.gain.value = v;
      const l = AC.createOscillator(), lg = AC.createGain(); l.frequency.value = .07 + i * .05; lg.gain.value = v * .45; l.connect(lg); lg.connect(g.gain); l.start(); s.connect(bp); bp.connect(g); g.connect(master); nodes.push(s, l); });
    const bubble = () => { const t = AC.currentTime, o = AC.createOscillator(), g = AC.createGain(), f = 380 + Math.random() * 700; o.type = 'sine'; o.frequency.setValueAtTime(f, t); o.frequency.exponentialRampToValueAtTime(f * 2.2, t + .05);
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.03 + Math.random() * .03, t + .005); g.gain.exponentialRampToValueAtTime(.0005, t + .06); o.connect(g); g.connect(master); o.start(t); o.stop(t + .08);
      timers.push(setTimeout(bubble, 60 + Math.random() * 380)); };
    bubble();
    const bird = () => { const t0 = AC.currentTime, n = 2 + Math.floor(Math.random() * 4), base = 2600 + Math.random() * 1600, kind = Math.random();
      for (let i = 0; i < n; i++) { const t = t0 + i * (.11 + Math.random() * .05), o = AC.createOscillator(), g = AC.createGain(); o.type = 'sine';
        const a = base * (kind < .5 ? 1 : 1.25), b = kind < .5 ? base * 1.45 : base * .8; o.frequency.setValueAtTime(a, t); o.frequency.exponentialRampToValueAtTime(b, t + .08);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.05, t + .012); g.gain.exponentialRampToValueAtTime(.0005, t + .09); o.connect(g); g.connect(master); o.start(t); o.stop(t + .1); }
      timers.push(setTimeout(bird, 2500 + Math.random() * 7000)); };
    timers.push(setTimeout(bird, 1500));
    return () => { timers.forEach(clearTimeout); nodes.forEach(n => { try { n.stop(); } catch (e) {} }); };
  }
  const KINDS = { fire: [fire, '🔥 CAMPFIRE SOUND', '🔥 CAMPFIRE: ON'], creek: [creek, '🌊 CREEK & BIRDS', '🌊 CREEK & BIRDS: ON'] };
  function start(kind) { ctx(); stop(true); cur = { kind, end: KINDS[kind][0]() }; master.gain.cancelScheduledValues(AC.currentTime); master.gain.setTargetAtTime(.5, AC.currentTime, .8); }
  function stop(quick) { if (!cur) return; const c = cur; cur = null; if (!AC) return; master.gain.setTargetAtTime(0, AC.currentTime, quick ? .05 : .5); setTimeout(c.end, quick ? 150 : 1800); }
  function button(host, kind, opts) {
    if (!host || !KINDS[kind]) return null; opts = opts || {};
    const b = document.createElement('button'); b.type = 'button'; b.className = opts.cls || 'kamb-btn';
    const KEY = 'kpcAmb:' + kind; let on = false;
    const lab = () => { b.textContent = on ? KINDS[kind][2] : KINDS[kind][1]; b.setAttribute('aria-pressed', on); b.title = on ? 'Tap to turn the sound off' : 'Soft background sound, made in your browser. Tap to turn it on.'; };
    b.onclick = () => { on = !on; put(KEY, on); if (on) start(kind); else stop(); lab(); };
    lab(); host.appendChild(b);
    if (get(KEY)) { const go = () => { document.removeEventListener('pointerdown', go, true); if (!on && get(KEY) && !(opts.when && !opts.when())) { on = true; start(kind); lab(); } }; document.addEventListener('pointerdown', go, true); }
    b.kOff = () => { if (on) { on = false; stop(); lab(); } };
    document.addEventListener('visibilitychange', () => { if (document.hidden && on && AC) master.gain.setTargetAtTime(0, AC.currentTime, .3); else if (!document.hidden && on && AC) master.gain.setTargetAtTime(.5, AC.currentTime, .8); });
    return b;
  }
  const css = document.createElement('style');
  css.textContent = '.kamb-btn{border:1px solid rgba(240,201,107,.6);background:rgba(0,0,0,.5);color:#f0c96b;border-radius:999px;padding:9px 15px;font:900 12px Arial;letter-spacing:1px;cursor:pointer;margin-top:12px}.kamb-btn[aria-pressed=true]{background:#d5a63a;color:#1a1205}';
  document.head.appendChild(css);
  window.KPCAmbient = { button, start, stop };
})();

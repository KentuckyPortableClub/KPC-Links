/* CW welcome (Oct 17 2026, Brandon: 'once someone opens the CW rooms can you send them something in CW?').
   Browsers block sound until the visitor taps, so: when the page opens, a signal lamp in the hero blinks the welcome in Morse
   (no sound, letters appear as it goes); the FIRST tap anywhere on the page plays it with sound, once per visit
   (sessionStorage kpcCwHello). On the Practice Room a first tap on START is skipped, because Zach's own welcome plays then.
   Greeting follows the visitor's clock: GM before noon, GA until 6 PM, GE after. Tap the lamp to hear it again. */
(function () {
  const h = new Date().getHours(), G = h < 12 ? 'GM' : h < 18 ? 'GA' : 'GE';
  const MSG = `${G} DE KPC WELCOME TO THE CW ROOM 73`;
  const M = { A: '.-', B: '-...', C: '-.-.', D: '-..', E: '.', F: '..-.', G: '--.', H: '....', I: '..', J: '.---', K: '-.-', L: '.-..', M: '--', N: '-.', O: '---', P: '.--.', Q: '--.-', R: '.-.', S: '...', T: '-', U: '..-', V: '...-', W: '.--', X: '-..-', Y: '-.--', Z: '--..', 0: '-----', 1: '.----', 2: '..---', 3: '...--', 4: '....-', 5: '.....', 6: '-....', 7: '--...', 8: '---..', 9: '----.' };
  const WPM = 18, EFF = 13, U = 1.2 / WPM, ta = (60 * WPM - 37.2 * EFF) / (WPM * EFF), CG = 3 * ta / 19, WG = 7 * ta / 19;
  /* [start, end, charIndex] marks */
  const marks = []; let t = 0;
  [...MSG].forEach((c, i) => { if (c === ' ') { t += WG - CG; return; } const code = M[c]; if (!code) return;
    [...code].forEach((s, j) => { const d = s === '.' ? U : 3 * U; marks.push([t, t + d, i]); t += d; if (j < code.length - 1) t += U; }); t += CG; });
  const TOTAL = t;
  const hero = document.querySelector('.hero .hero-inner') || document.querySelector('.hero'); if (!hero) return;
  const st = document.createElement('style');
  st.textContent = '.cwh{display:flex;align-items:center;gap:12px;margin-top:18px;max-width:680px;cursor:pointer;background:rgba(0,0,0,.45);border:1px solid rgba(213,166,58,.55);border-radius:999px;padding:8px 16px 8px 8px;position:relative;z-index:3}'
    + '.cwh-l{flex:0 0 auto;width:30px;height:30px;border-radius:50%;background:radial-gradient(circle at 40% 35%,#5a4a24,#2a2210);box-shadow:inset 0 0 0 2px #6b5524;transition:background .03s,box-shadow .03s}'
    + '.cwh-l.on{background:radial-gradient(circle at 40% 35%,#fff6c8,#ffcf4a 55%,#e08a00);box-shadow:0 0 18px 6px rgba(255,190,60,.75),inset 0 0 0 2px #ffe08a}'
    + '.cwh-t{font:700 15px ui-monospace,Menlo,Consolas,monospace;letter-spacing:2px;color:#f0c96b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
    + '.cwh-t i{font-style:normal;color:rgba(240,201,107,.25)}.cwh-s{font:11px Arial;color:#cfc6b0;white-space:nowrap}'
    + '@media(max-width:600px){.cwh{padding:6px 12px 6px 6px;gap:9px}.cwh-t{font-size:12.5px;letter-spacing:1px}.cwh-s{display:none}}';
  document.head.appendChild(st);
  const box = document.createElement('div'); box.className = 'cwh'; box.setAttribute('role', 'button'); box.tabIndex = 0;
  box.title = 'A welcome in Morse code. Tap to see it again.'; box.setAttribute('aria-label', 'Welcome in Morse code: ' + MSG + '. Tap to see it again.');
  box.innerHTML = '<span class="cwh-l" aria-hidden="true"></span><span class="cwh-t" aria-hidden="true"></span>';
  hero.appendChild(box);
  const lamp = box.querySelector('.cwh-l'), txt = box.querySelector('.cwh-t');
  const showText = n => { txt.innerHTML = MSG.slice(0, n).replace(/&/g, '&amp;') + '<i>' + MSG.slice(n).replace(/[A-Z0-9]/g, '·') + '</i>'; };
  showText(0);
  let run = 0;
  function blink(audio) {
    const my = ++run, reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let AC = null, g = null;
    if (audio) { try { AC = new (window.AudioContext || window.webkitAudioContext)(); const o = AC.createOscillator(); g = AC.createGain(); o.frequency.value = 620; g.gain.value = 0; o.connect(g); g.connect(AC.destination); o.start();
      const t0 = AC.currentTime + .08; marks.forEach(([a, b]) => { g.gain.setTargetAtTime(.22, t0 + a, .004); g.gain.setTargetAtTime(0, t0 + b, .004); }); o.stop(t0 + TOTAL + .3); } catch (e) { AC = null; } }
    if (reduce) { showText(MSG.length); return; }
    const start = performance.now() + (audio ? 80 : 0);
    (function step() {
      if (my !== run) return;
      const el = (performance.now() - start) / 1000; const m = marks.find(x => el >= x[0] && el < x[1]);
      lamp.classList.toggle('on', !!m);
      const done = marks.filter(x => x[1] <= el); showText(done.length ? done[done.length - 1][2] + 1 : 0);
      if (el < TOTAL + .1) requestAnimationFrame(step); else { lamp.classList.remove('on'); showText(MSG.length); if (AC) setTimeout(() => AC.close(), 600); }
    })();
  }
  setTimeout(() => blink(false), 900);   /* silent on open */
  /* Oct 17 (Brandon): the lamp only flashes now, no sound; tap it to see it again */
  const play = () => blink(false);
  box.addEventListener('click', play); box.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); play(); } });
})();

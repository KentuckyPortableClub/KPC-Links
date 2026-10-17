/* KPC screen effects (flames / fireworks / shooting stars), a toned-down copy of the Hunters Lounge ones for the KPC Logger
   (Brandon Oct 17: 'give the logger all them effects but slightly toned down'). window.KPCFx(kind, message). */
(function () {
  let fireT = 0, cv = null, mg = null;
  function CV() { if (!cv) { cv = document.createElement('canvas'); cv.className = 'kfx-cv'; cv.setAttribute('aria-hidden', 'true'); document.body.appendChild(cv); } return cv; }
  function MSG() { if (!mg) { mg = document.createElement('div'); mg.className = 'kfx-msg'; mg.setAttribute('aria-live', 'polite'); document.body.appendChild(mg); } return mg; }
  const st = document.createElement('style');
  st.textContent = '.kfx-cv{position:fixed;left:0;right:0;bottom:0;width:100%;height:45vh;pointer-events:none;z-index:2800;opacity:0;transition:opacity .4s}.kfx-cv.on{opacity:.62}'
    + '.kfx-msg{position:fixed;left:50%;bottom:30vh;transform:translate(-50%,30px);z-index:2900;pointer-events:none;font:900 clamp(18px,3vw,32px)/1.15 Georgia,serif;color:#fff;text-align:center;text-shadow:0 0 14px #ff7a00,0 2px 5px #000;opacity:0;width:min(90vw,800px)}'
    + '.kfx-msg.on{animation:kfxMsg 3.2s ease-out}@keyframes kfxMsg{0%{opacity:0;transform:translate(-50%,30px)}15%{opacity:1;transform:translate(-50%,0)}75%{opacity:1}100%{opacity:0;transform:translate(-50%,-20px)}}';
  document.head.appendChild(st);
  function flames(msg) {
    const cv = CV(), cx = cv.getContext('2d'), W = cv.width = innerWidth, H = cv.height = Math.round(innerHeight * .45); cv.style.height = '';
    const P = [], t0 = performance.now(), DUR = 3000;
    if (msg) { const m = MSG(); m.textContent = msg; m.classList.remove('on'); void m.offsetWidth; m.classList.add('on'); }
    cv.classList.add('on'); cancelAnimationFrame(fireT);
    const step = now => {
      const el = now - t0, live = el < DUR - 900;
      for (let i = 0; live && i < Math.max(8, W / 44); i++) P.push({ x: Math.random() * W, y: H + 10, vx: (Math.random() - .5) * .9, vy: -(2.2 + Math.random() * 4.2), r: 10 + Math.random() * 26, life: 0, max: 50 + Math.random() * 45 });
      cx.clearRect(0, 0, W, H); cx.globalCompositeOperation = 'lighter';
      for (let i = P.length - 1; i >= 0; i--) {
        const p = P[i]; p.life++; p.x += p.vx + Math.sin((p.life + i) / 6) * .6; p.y += p.vy; p.r *= .985;
        const k = p.life / p.max; if (k >= 1) { P.splice(i, 1); continue; }
        const g = cx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
        g.addColorStop(0, `rgba(255,${Math.round(230 - 150 * k)},${Math.round(120 - 110 * k)},${.75 * (1 - k)})`); g.addColorStop(.5, `rgba(255,${Math.round(110 - 80 * k)},0,${.45 * (1 - k)})`); g.addColorStop(1, 'rgba(120,10,0,0)');
        cx.fillStyle = g; cx.beginPath(); cx.arc(p.x, p.y, p.r, 0, 6.283); cx.fill();
      }
      if (el < DUR || P.length) fireT = requestAnimationFrame(step); else { cv.classList.remove('on'); cx.clearRect(0, 0, W, H); }
    };
    fireT = requestAnimationFrame(step);
  }
  /* 🌠 shooting stars: bright streaks with glowing tails race across the screen from the top */
  function shootingStars(msg) {
    const cv = CV(), cx = cv.getContext('2d'), W = cv.width = innerWidth, H = cv.height = Math.round(innerHeight * .7);
    cv.style.height = '70vh';
    if (msg) { const m = MSG(); m.textContent = msg.replace(/^🔥/, '🌠'); m.classList.remove('on'); void m.offsetWidth; m.classList.add('on'); }
    cv.classList.add('on'); cancelAnimationFrame(fireT);
    const S = [], SP2 = [], t0 = performance.now(), DUR = 3400; let made = 0;
    for (let i = 0; i < 70; i++) SP2.push({ x: Math.random() * W, y: Math.random() * H * .7, r: Math.random() * 1.3 + .3, p: Math.random() * 6.28 });
    const step = now => {
      const el = now - t0;
      if (el < DUR - 1200 && made < Math.round(el / 230) + 1) { made++; const a = (20 + Math.random() * 25) * Math.PI / 180, v = 14 + Math.random() * 12, left = Math.random() < .5;
        S.push({ x: left ? -40 + Math.random() * W * .5 : W * .5 + Math.random() * W * .5, y: -20 + Math.random() * H * .35, vx: (left ? 1 : -1) * Math.cos(a) * v, vy: Math.sin(a) * v, life: 0, max: 45 + Math.random() * 30, len: 14 + Math.random() * 10 }); }
      cx.clearRect(0, 0, W, H);
      const fade = Math.max(0, Math.min(1, el / 400, (DUR - el) / 600));
      SP2.forEach(st => { cx.globalAlpha = fade * (.35 + .35 * Math.sin(el / 300 + st.p)); cx.fillStyle = '#fff'; cx.beginPath(); cx.arc(st.x, st.y, st.r, 0, 6.283); cx.fill(); });
      cx.globalAlpha = 1;
      for (let i = S.length - 1; i >= 0; i--) {
        const s = S[i]; s.life++; s.x += s.vx; s.y += s.vy; const k = s.life / s.max;
        if (k >= 1) { S.splice(i, 1); continue; }
        const tx = s.x - s.vx * s.len, ty = s.y - s.vy * s.len, g = cx.createLinearGradient(s.x, s.y, tx, ty);
        g.addColorStop(0, `rgba(255,255,255,${1 - k})`); g.addColorStop(.25, `rgba(180,215,255,${.7 * (1 - k)})`); g.addColorStop(1, 'rgba(120,160,255,0)');
        cx.strokeStyle = g; cx.lineWidth = 3; cx.lineCap = 'round'; cx.beginPath(); cx.moveTo(s.x, s.y); cx.lineTo(tx, ty); cx.stroke();
        cx.fillStyle = `rgba(255,255,255,${1 - k})`; cx.shadowColor = '#bcd6ff'; cx.shadowBlur = 14; cx.beginPath(); cx.arc(s.x, s.y, 2.6, 0, 6.283); cx.fill(); cx.shadowBlur = 0;
      }
      if (el < DUR || S.length) fireT = requestAnimationFrame(step); else { cv.classList.remove('on'); cx.clearRect(0, 0, W, H); cv.style.height = ''; }
    };
    fireT = requestAnimationFrame(step);
  }
  /* 🎆 fireworks: rockets climb from the bottom and burst into colour */
  function fireworks(msg) {
    const cv = CV(), cx = cv.getContext('2d'), W = cv.width = innerWidth, H = cv.height = Math.round(innerHeight * .7);
    cv.style.height = '70vh';
    if (msg) { const m = MSG(); m.textContent = msg.replace(/^🔥/, '🎆'); m.classList.remove('on'); void m.offsetWidth; m.classList.add('on'); }
    cv.classList.add('on'); cancelAnimationFrame(fireT);
    const R = [], P = [], t0 = performance.now(), DUR = 3400, COL = ['#ffd76a', '#ff6b5a', '#3ddc84', '#8fb7ff', '#ff6fa8', '#ffffff', '#c08bff'];
    let launched = 0;
    const step = now => {
      const el = now - t0;
      if (el < DUR - 1400 && launched < Math.round(el / 260) + 1) { launched++; R.push({ x: W * (.12 + Math.random() * .76), y: H + 5, vy: -(H / 75 + Math.random() * H / 140), tY: H * (.18 + Math.random() * .3), c: COL[Math.floor(Math.random() * COL.length)] }); }
      cx.globalCompositeOperation = 'destination-out'; cx.fillStyle = 'rgba(0,0,0,.28)'; cx.fillRect(0, 0, W, H); cx.globalCompositeOperation = 'lighter';
      for (let i = R.length - 1; i >= 0; i--) {
        const r = R[i]; r.y += r.vy; r.vy *= .985;
        cx.fillStyle = r.c; cx.beginPath(); cx.arc(r.x, r.y, 2.4, 0, 6.283); cx.fill();
        if (r.y <= r.tY || r.vy > -1.5) { R.splice(i, 1); const k = 45 + Math.random() * 35; for (let j = 0; j < k; j++) { const a = Math.random() * 6.283, v = 1.5 + Math.random() * 5.5; P.push({ x: r.x, y: r.y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, life: 0, max: 50 + Math.random() * 35, c: Math.random() < .2 ? '#fff' : r.c }); } }
      }
      for (let i = P.length - 1; i >= 0; i--) {
        const p = P[i]; p.life++; p.x += p.vx; p.y += p.vy; p.vx *= .97; p.vy = p.vy * .97 + .06;
        const k = p.life / p.max; if (k >= 1) { P.splice(i, 1); continue; }
        cx.globalAlpha = 1 - k; cx.fillStyle = p.c; cx.beginPath(); cx.arc(p.x, p.y, 2.2 * (1 - k * .6), 0, 6.283); cx.fill(); cx.globalAlpha = 1;
      }
      if (el < DUR || P.length || R.length) fireT = requestAnimationFrame(step); else { cv.classList.remove('on'); cx.clearRect(0, 0, W, H); cv.style.height = ''; }
    };
    fireT = requestAnimationFrame(step);
  }
  window.KPCFx = function (kind, msg) {
    if (!kind || kind === 'off' || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (kind === 'fireworks') return fireworks(msg); if (kind === 'stars') return shootingStars(msg); return flames(msg);
  };
})();

/* CW Practice Room speed flames (Oct 17 2026, Brandon: 'make flames get larger… start out at 23 WPM and get larger the quicker
   they go… and have a button for off'). Flames rise from the bottom of the screen while code is playing or you are sending at
   23 WPM or faster; the faster, the taller and hotter (full size at 40 WPM). The speed comes from what is playing (window.__cwPlay,
   set in kpc-cw.js) or your own sending measured by the fist meter (window.__cwSend). 🔥 SPEED FLAMES button = on/off
   (localStorage kpcCwFlames). Off with reduced motion. */
(function () {
  const KEY = 'kpcCwFlames', START = 23, FULL = 40;
  let on = true; try { on = localStorage.getItem(KEY) !== '0'; } catch (e) {}
  const css = document.createElement('style');
  css.textContent = '.cwf-cv{position:fixed;left:0;right:0;bottom:0;width:100%;pointer-events:none;z-index:40;opacity:0;transition:opacity .6s}.cwf-cv.on{opacity:.7}'
    + '.cwf-badge{position:fixed;right:14px;bottom:14px;z-index:41;pointer-events:none;font:900 13px Arial;letter-spacing:1px;color:#fff;text-shadow:0 0 10px #ff6a00,0 2px 4px #000;opacity:0;transition:opacity .4s}.cwf-badge.on{opacity:1}'
    + '.cw-switch .cwf-btn{border:1px solid rgba(255,140,40,.6);background:rgba(255,120,20,.12);color:#ffb070;border-radius:999px;padding:8px 14px;font:900 12px Arial;letter-spacing:1px;cursor:pointer}'
    + '.cw-switch .cwf-btn[aria-pressed=false]{color:#aaa;border-color:rgba(255,255,255,.25);background:transparent}';
  document.head.appendChild(css);
  const cv = document.createElement('canvas'); cv.className = 'cwf-cv'; cv.setAttribute('aria-hidden', 'true'); document.body.appendChild(cv);
  const bd = document.createElement('div'); bd.className = 'cwf-badge'; document.body.appendChild(bd);
  const nav = document.querySelector('.cw-switch');
  const btn = document.createElement('button'); btn.type = 'button'; btn.className = 'cwf-btn';
  const lab = () => { btn.textContent = on ? '🔥 SPEED FLAMES: ON' : '🔥 SPEED FLAMES: OFF'; btn.setAttribute('aria-pressed', on); btn.title = 'Flames rise when the code runs at ' + START + ' WPM or faster (bigger the faster). Tap to turn ' + (on ? 'off' : 'on') + '.'; };
  lab(); if (nav) nav.appendChild(btn);
  btn.onclick = () => { on = !on; try { localStorage.setItem(KEY, on ? '1' : '0'); } catch (e) {} lab(); if (!on) { cv.classList.remove('on'); bd.classList.remove('on'); } };
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ctx = cv.getContext('2d'); let W = 0, H = 0, P = [], lvl = 0, want = 0, wpmNow = 0, raf = 0;
  const size = () => { W = cv.width = innerWidth; H = cv.height = Math.round(innerHeight * .5); cv.style.height = H + 'px'; };
  size(); addEventListener('resize', size);
  function speedNow() {
    const n = Date.now(), p = window.__cwPlay, s = window.__cwSend; let w = 0;
    if (p && n - p.t < (p.ms || 2000) + 1500) w = Math.max(w, p.wpm || 0);
    if (s && n - s.t < 4000) w = Math.max(w, s.wpm || 0);
    return w;
  }
  function frame() {
    raf = 0;
    wpmNow = speedNow();
    want = on && !reduce && wpmNow >= START ? Math.min(1, (wpmNow - START) / (FULL - START)) * .85 + .15 : 0;
    lvl += (want - lvl) * .06;
    const live = lvl > .01 || P.length;
    cv.classList.toggle('on', lvl > .02); bd.classList.toggle('on', want > 0);
    if (want > 0) bd.textContent = '🔥 ' + Math.round(wpmNow) + ' WPM';
    if (live) {
      const n = Math.round(4 + lvl * 26), top = H * (1 - (.28 + lvl * .72));
      for (let i = 0; i < n * lvl + (lvl > .02 ? 1 : 0); i++)
        P.push({ x: Math.random() * W, y: H + 10, vx: (Math.random() - .5) * 1.1, vy: -(1.6 + Math.random() * 2.4) * (0.6 + lvl * 1.2), r: (8 + Math.random() * 18) * (0.6 + lvl * .9), life: 0, max: 40 + Math.random() * 40, top });
      ctx.clearRect(0, 0, W, H); ctx.globalCompositeOperation = 'lighter';
      for (let i = P.length - 1; i >= 0; i--) {
        const q = P[i]; q.life++; q.x += q.vx + Math.sin((q.life + i) / 6) * .6; q.y += q.vy; q.r *= .985;
        const k = q.life / q.max; if (k >= 1 || q.y < q.top) { P.splice(i, 1); continue; }
        const g = ctx.createRadialGradient(q.x, q.y, 0, q.x, q.y, q.r);
        const hot = lvl > .7 ? 255 : 230;
        g.addColorStop(0, `rgba(255,${Math.round(hot - 150 * k)},${Math.round(120 - 110 * k)},${.7 * (1 - k)})`); g.addColorStop(.5, `rgba(255,${Math.round(110 - 80 * k)},0,${.42 * (1 - k)})`); g.addColorStop(1, 'rgba(120,10,0,0)');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(q.x, q.y, q.r, 0, 6.283); ctx.fill();
      }
      if (P.length > 900) P.splice(0, P.length - 900);
      raf = requestAnimationFrame(frame);
    } else { ctx.clearRect(0, 0, W, H); setTimeout(() => { if (!raf) raf = requestAnimationFrame(frame); }, 400); }
  }
  raf = requestAnimationFrame(frame);
})();

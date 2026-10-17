/* Kids Room looks + effects (Oct 17 2026, Brandon: 'falling balloons and flowers, like the Lounge but kids style').
   Mount: <div id="kzFx"></div> under the hero. LOOK: ☀️ SUNNY (as it was) / 🌈 RAINBOW / 🌙 BEDTIME, and an effect button that cycles
   🎈 BALLOONS / 🌸 FLOWERS / 🦋 BUTTERFLIES / ⭐ STARS / 🚫 NO EFFECTS. A few pictures drift gently behind the page all the time,
   and every time a star is earned a big burst floats up with a cheer. Saved in localStorage kpcKidsLook / kpcKidsFx (nothing else).
   Off with reduced motion. */
(function () {
  const mount = document.getElementById('kzFx'); if (!mount) return;
  const get = (k, d) => { try { return localStorage.getItem(k) || d; } catch (e) { return d; } }, put = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const FX = { balloons: ['🎈 BALLOONS', ['🎈', '🎈', '🎈', '🎈'], 'up'], flowers: ['🌸 FLOWERS', ['🌸', '🌼', '🌷', '🌻', '🌺'], 'down'],
    butterflies: ['🦋 BUTTERFLIES', ['🦋', '🦋', '🐞', '🌼'], 'up'], stars: ['⭐ STARS', ['⭐', '🌟', '✨', '💫'], 'down'], off: ['🚫 NO EFFECTS', [], ''] };
  const ORDER = ['balloons', 'flowers', 'butterflies', 'stars', 'off'], LOOKS = [['sunny', '☀️ SUNNY'], ['rainbow', '🌈 RAINBOW'], ['bedtime', '🌙 BEDTIME']];
  const BAL = ['#ff5d73', '#ffb703', '#3a86ff', '#8ac926', '#c77dff', '#ff7f11'];
  let fx = get('kpcKidsFx', 'balloons'), look = get('kpcKidsLook', 'sunny'); if (!FX[fx]) fx = 'balloons';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const st = document.createElement('style');
  st.textContent = `
.kzfx{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:7px;padding:12px;background:linear-gradient(90deg,#ff5d73,#ffb703,#8ac926,#3a86ff,#c77dff);position:relative;z-index:3}
.kzfx span{font:900 13px Arial;letter-spacing:1px;color:#fff;text-shadow:0 1px 3px rgba(0,0,0,.45)}
.kzfx button{border:3px solid #fff;background:rgba(255,255,255,.88);color:#3a2a6b;border-radius:999px;padding:8px 14px;font:900 13px Arial;cursor:pointer;box-shadow:0 3px 0 rgba(0,0,0,.15)}
.kzfx button.on{background:#3a2a6b;color:#fff}
.kzfx .fxb{background:#fff7d6}
.kz-drift{position:fixed;inset:0;pointer-events:none;z-index:1;overflow:hidden}
.kz-drift i{position:absolute;font-style:normal;will-change:transform;opacity:.85;filter:drop-shadow(0 3px 4px rgba(0,0,0,.15))}
.kz-drift i.up{bottom:-60px;animation:kzUp var(--t) linear infinite;animation-delay:var(--d)}
.kz-drift i.down{top:-60px;animation:kzDown var(--t) linear infinite;animation-delay:var(--d)}
@keyframes kzUp{0%{transform:translate(0,0) rotate(-6deg)}50%{transform:translate(28px,-55vh) rotate(6deg)}100%{transform:translate(-10px,-115vh) rotate(-4deg)}}
@keyframes kzDown{0%{transform:translate(0,0) rotate(0)}50%{transform:translate(-30px,55vh) rotate(120deg)}100%{transform:translate(20px,115vh) rotate(260deg)}}
.kz-bal{display:inline-block;width:1em;height:1.2em;border-radius:50% 50% 48% 48%;position:relative}
.kz-bal::after{content:'';position:absolute;left:50%;top:100%;width:1px;height:1.1em;background:rgba(80,60,40,.5)}
.kz-burst{position:fixed;inset:0;pointer-events:none;z-index:2600;overflow:hidden}
.kz-burst i{position:absolute;bottom:-70px;font-style:normal;animation:kzBurst var(--t) cubic-bezier(.2,.6,.3,1) forwards;animation-delay:var(--d)}
@keyframes kzBurst{0%{transform:translate(0,0) scale(.6);opacity:0}10%{opacity:1}100%{transform:translate(var(--x),-120vh) scale(1.15) rotate(var(--r));opacity:.9}}
.kz-cheer{position:fixed;left:50%;top:38%;transform:translate(-50%,-50%) scale(.6);z-index:2700;pointer-events:none;font:900 clamp(28px,6vw,54px)/1.1 Arial;color:#fff;text-align:center;
 -webkit-text-stroke:2px #3a2a6b;text-shadow:0 5px 0 #ff5d73,0 10px 22px rgba(0,0,0,.35);opacity:0}
.kz-cheer.on{animation:kzCheer 2.4s ease-out forwards}
@keyframes kzCheer{0%{opacity:0;transform:translate(-50%,-50%) scale(.5)}15%{opacity:1;transform:translate(-50%,-50%) scale(1.12)}25%{transform:translate(-50%,-50%) scale(1)}80%{opacity:1}100%{opacity:0;transform:translate(-50%,-70%) scale(1)}}
body.kzl-rainbow .kz{background:linear-gradient(180deg,#ffe3ec 0%,#fff3c4 25%,#e3f7d4 50%,#d6ecff 75%,#efe0ff 100%)!important}
body.kzl-bedtime .kz{background:radial-gradient(1.5px 1.5px at 12% 18%,#fff,transparent),radial-gradient(1px 1px at 33% 64%,#fff,transparent),radial-gradient(1.5px 1.5px at 71% 30%,#fff,transparent),radial-gradient(1px 1px at 88% 75%,#fff,transparent),radial-gradient(1px 1px at 52% 42%,#cfe3ff,transparent),linear-gradient(180deg,#1b1f4a,#2b2466)!important}
body.kzl-bedtime .kz-top{background:#fffdf3}
.kz{position:relative;z-index:2}
@media(max-width:600px){.kzfx{gap:5px;padding:9px}.kzfx button{padding:6px 10px;font-size:11.5px}.kzfx span{width:100%;text-align:center}}
@media print{.kzfx,.kz-drift,.kz-burst,.kz-cheer{display:none!important}}`;
  document.head.appendChild(st);
  mount.className = 'kzfx'; mount.setAttribute('data-keep-light', '');
  mount.innerHTML = '<span>PICK A LOOK:</span>' + LOOKS.map(([k, t]) => `<button type="button" data-kzl="${k}">${t}</button>`).join('') + '<button type="button" class="fxb" id="kzFxBtn"></button>';
  const drift = document.createElement('div'); drift.className = 'kz-drift'; drift.setAttribute('aria-hidden', 'true'); document.body.appendChild(drift);
  const pic = (e, i) => e === '🎈' ? `<b class="kz-bal" style="background:radial-gradient(circle at 35% 30%,#fff8 0 12%,transparent 13%),${BAL[i % BAL.length]}"></b>` : e;
  function drawDrift() {
    drift.innerHTML = ''; if (reduce || fx === 'off') return;
    const [, set, dir] = FX[fx], n = innerWidth < 600 ? 7 : 12;
    for (let i = 0; i < n; i++) {
      const e = document.createElement('i'); e.className = dir;
      e.style.left = (4 + Math.random() * 92) + '%'; e.style.fontSize = (22 + Math.random() * 18) + 'px';
      e.style.setProperty('--t', (16 + Math.random() * 14) + 's'); e.style.setProperty('--d', (-Math.random() * 28) + 's');
      e.innerHTML = pic(set[i % set.length], i); drift.appendChild(e);
    }
  }
  function burst(msg) {
    if (reduce || fx === 'off') return;
    const set = FX[fx][1], b = document.createElement('div'); b.className = 'kz-burst'; b.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < 34; i++) {
      const e = document.createElement('i'); e.style.left = (Math.random() * 100) + '%'; e.style.fontSize = (26 + Math.random() * 26) + 'px';
      e.style.setProperty('--t', (2.4 + Math.random() * 1.6) + 's'); e.style.setProperty('--d', (Math.random() * .8) + 's');
      e.style.setProperty('--x', ((Math.random() - .5) * 160) + 'px'); e.style.setProperty('--r', ((Math.random() - .5) * 90) + 'deg');
      e.innerHTML = pic(set[i % set.length], i); b.appendChild(e);
    }
    document.body.appendChild(b); setTimeout(() => b.remove(), 5000);
    let c = document.querySelector('.kz-cheer'); if (!c) { c = document.createElement('div'); c.className = 'kz-cheer'; c.setAttribute('aria-live', 'polite'); document.body.appendChild(c); }
    c.textContent = msg; c.classList.remove('on'); void c.offsetWidth; c.classList.add('on');
  }
  function paint() {
    document.body.classList.remove('kzl-sunny', 'kzl-rainbow', 'kzl-bedtime'); document.body.classList.add('kzl-' + look);
    mount.querySelectorAll('[data-kzl]').forEach(b => b.classList.toggle('on', b.dataset.kzl === look));
    document.getElementById('kzFxBtn').textContent = FX[fx][0];
  }
  mount.addEventListener('click', e => {
    const l = e.target.closest('[data-kzl]'); if (l) { look = l.dataset.kzl; put('kpcKidsLook', look); paint(); return; }
    if (e.target.closest('#kzFxBtn')) { fx = ORDER[(ORDER.indexOf(fx) + 1) % ORDER.length]; put('kpcKidsFx', fx); paint(); drawDrift(); if (fx !== 'off') burst(FX[fx][1][0] + ' Hooray!'); }
  });
  paint(); drawDrift(); addEventListener('resize', () => { clearTimeout(drawDrift.t); drawDrift.t = setTimeout(drawDrift, 400); });
  /* a star was earned: celebrate */
  const S = document.getElementById('kzStars');
  if (S) { let last = +S.textContent || 0; new MutationObserver(() => { const n = +S.textContent || 0; if (n > last) burst(['⭐ Great job!', '🎉 You did it!', '🌟 Super star!', '👏 Way to go!', '📻 73, star operator!'][Math.floor(Math.random() * 5)] + (n % 10 === 0 ? ` ${n} stars!` : '')); last = n; }).observe(S, { childList: true, characterData: true, subtree: true }); }
})();

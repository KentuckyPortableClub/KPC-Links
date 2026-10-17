/* KPC gentle motion (Oct 17 2026, Brandon picked): slow drift on hero pictures, cards easing in as you scroll (Tool Box, Map Room,
   program rooms), a slow glow on gold buttons, radio waves from the mast in the header logo, sparks rising from the campfire on
   the Community and Campgrounds heroes, and the creek & birds sound button on the WWFF Room. Everything is off for people whose
   device asks for reduced motion, and none of it runs while printing. */
(function () {
  const H = document.documentElement, P = location.pathname.split('/').pop() || 'index.html';
  if (/[?&](print|pdf)=/.test(location.search) || /^kpc-guide-/.test(P)) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const CARDS = /^(toolbox|kpc-map-room|kpc-pota-room|kpc-wwff-room|kpc-sota-room)\.html$/.test(P);
  const SPARKS = /^(kpc-community|kpc-campgrounds)\.html$/.test(P);
  const css = document.createElement('style');
  css.textContent = `
@media screen and (prefers-reduced-motion:no-preference){
 .kpm-drift{position:absolute;inset:0;z-index:0;pointer-events:none;background:inherit;animation:kpmDrift 46s ease-in-out infinite alternate;transform-origin:60% 45%;will-change:transform}
 .kpm-host{overflow:hidden!important;background-image:none!important}
 .kpm-host>*:not(.kpm-drift):not(.kpm-sparks){position:relative;z-index:1}
 .kpm-host>.kpc-who,.kpm-host>.gb-who{position:absolute!important;z-index:3}
 .kpm-host.kpm-b::before{animation:kpmDrift 46s ease-in-out infinite alternate;transform-origin:70% 45%}
 @keyframes kpmDrift{0%{transform:scale(1.02) translate(0,0)}100%{transform:scale(1.09) translate(-1.6%,-1%)}}
 html.kpm-ready .kpm-card{opacity:0;transform:translateY(22px);transition:opacity .7s ease,transform .7s ease}
 html.kpm-ready .kpm-card.kpm-in{opacity:1;transform:none}
 .kb-hero .kb-btn.gold,.hero .btn,.kb-actions .kb-btn.gold,.toolbox .btn{animation:kpmGlow 3.6s ease-in-out infinite}
 @keyframes kpmGlow{0%,100%{box-shadow:0 6px 16px rgba(0,0,0,.25)}50%{box-shadow:0 6px 16px rgba(0,0,0,.25),0 0 18px 2px rgba(240,190,80,.55)}}
 .kpm-waves{position:absolute;left:31%;top:6%;width:0;height:0;pointer-events:none;z-index:2}
 .kpm-waves i{position:absolute;left:-6px;top:-6px;width:12px;height:12px;border-radius:50%;border:2px solid rgba(240,201,107,.0);border-left-color:transparent;border-bottom-color:transparent;transform:rotate(-45deg) scale(.4);animation:kpmWave 4s ease-out infinite}
 .kpm-waves i:nth-child(2){animation-delay:.35s}.kpm-waves i:nth-child(3){animation-delay:.7s}
 @keyframes kpmWave{0%{transform:rotate(-45deg) scale(.4);border-top-color:rgba(255,215,120,.95);border-right-color:rgba(255,215,120,.95);opacity:1}55%{opacity:0;transform:rotate(-45deg) scale(2.6);border-top-color:rgba(255,215,120,.2);border-right-color:rgba(255,215,120,.2)}100%{opacity:0;transform:rotate(-45deg) scale(2.6)}}
 .kpm-sparks{position:absolute;inset:0;pointer-events:none;z-index:1;overflow:hidden}
 .kpm-sparks i{position:absolute;bottom:-8px;left:var(--x);width:4px;height:4px;border-radius:50%;background:#ffc15e;box-shadow:0 0 9px 3px rgba(255,140,40,.8);opacity:0;animation:kpmSpark var(--t) linear var(--d) infinite}
 @keyframes kpmSpark{0%{opacity:0;transform:translate(0,0)}10%{opacity:1}100%{opacity:0;transform:translate(var(--dx),-70vh)}}
}
@media print{.kpm-drift,.kpm-waves,.kpm-sparks{display:none!important}.kpm-card{opacity:1!important;transform:none!important}}`;
  document.head.appendChild(css);
  function heroes() {
    if (reduce) return;
    document.querySelectorAll('.kb-hero, section.hero, header.hero').forEach(h => {
      if (h.closest('#hl,#lg') || h.dataset.kpm) return; h.dataset.kpm = '1';
      const cs = getComputedStyle(h), bi = cs.backgroundImage;
      if (bi && bi.indexOf('url(') >= 0) {
        if (cs.position === 'static') h.style.position = 'relative';
        const d = document.createElement('div'); d.className = 'kpm-drift'; d.setAttribute('aria-hidden', 'true');
        d.style.backgroundImage = bi; d.style.backgroundSize = cs.backgroundSize; d.style.backgroundPosition = cs.backgroundPosition; d.style.backgroundRepeat = cs.backgroundRepeat; d.style.backgroundColor = cs.backgroundColor;
        h.insertBefore(d, h.firstChild); h.classList.add('kpm-host');
      } else {
        const b = getComputedStyle(h, '::before').backgroundImage;
        if (b && b.indexOf('url(') >= 0) h.classList.add('kpm-b');
      }
      if (SPARKS && !h.querySelector('.kpm-sparks')) {
        const s = document.createElement('div'); s.className = 'kpm-sparks'; s.setAttribute('aria-hidden', 'true');
        for (let i = 0; i < 16; i++) { const e = document.createElement('i'); e.style.setProperty('--x', (35 + Math.random() * 35) + '%'); e.style.setProperty('--t', (5 + Math.random() * 5) + 's'); e.style.setProperty('--d', (-Math.random() * 9) + 's'); e.style.setProperty('--dx', ((Math.random() - .5) * 120) + 'px'); s.appendChild(e); }
        h.appendChild(s);
      }
    });
  }
  function logo() {
    if (reduce) return;
    const b = document.querySelector('header .brand'); if (!b || b.querySelector('.kpm-waves')) return;
    const img = b.querySelector('img'); if (!img) return;
    const w = document.createElement('span'); w.className = 'kpm-waves'; w.setAttribute('aria-hidden', 'true'); w.innerHTML = '<i></i><i></i><i></i>';
    const wrap = document.createElement('span'); wrap.style.cssText = 'position:relative;display:inline-block;line-height:0';
    img.parentNode.insertBefore(wrap, img); wrap.appendChild(img); wrap.appendChild(w);
  }
  function cards() {
    if (!CARDS || reduce || !('IntersectionObserver' in window)) return;
    const L = [...document.querySelectorAll('.card, .kb-card, .rm-num, .rm-tool, .rm-step, .rm-card, .link-card')].filter(e => !e.closest('header,footer,.hero,.kb-hero'));
    if (!L.length) return;
    const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { en.target.classList.add('kpm-in'); io.unobserve(en.target); } }), { rootMargin: '0px 0px -8% 0px', threshold: .08 });
    L.forEach((e, i) => { const r = e.getBoundingClientRect(); if (r.top < innerHeight) return; e.classList.add('kpm-card'); e.style.transitionDelay = (i % 3) * 90 + 'ms'; io.observe(e); });
    H.classList.add('kpm-ready');
  }
  function sounds() {
    if (P !== 'kpc-wwff-room.html') return;
    const host = document.querySelector('.kb-hero .kb-actions') || document.querySelector('.kb-hero-in'); if (!host) return;
    const s = document.createElement('script'); s.src = 'kpc-ambient.js?v=20261017a'; s.onload = () => window.KPCAmbient && KPCAmbient.button(host, 'creek'); document.head.appendChild(s);
  }
  /* still pictures behind the page (Oct 17, Brandon: yes): the page's own picture, blurred, stays put while the sections scroll over it */
  const FIX = { 'kpc-pota-room.html': 'statepark', 'kpc-wwff-room.html': 'wildlife', 'kpc-sota-room.html': 'summit', 'kpc-map-room.html': 'map',
    'kpc-kids.html': 'kids', 'kpc-campgrounds.html': 'campsite', 'kpc-park-notes.html': 'journal', 'kpc-park-notes-us.html': 'journal' };
  function still() {
    const k = FIX[P]; if (!k) return;
    const st = document.createElement('style');
    st.textContent = `html.kpm-fix{background:#0b0b0b!important}html.kpm-fix body{background:transparent!important}
html.kpm-fix body::before{content:"";position:fixed;inset:0;z-index:-1;background:#0b0b0b url('bg-${k}.jpg') center/cover no-repeat}
@media(max-width:700px){html.kpm-fix body::before{background-image:url('bg-${k}-mobile.jpg')}}
html.kpm-fix main{background:transparent!important}@media print{html.kpm-fix body::before{display:none}}`;
    document.head.appendChild(st); H.classList.add('kpm-fix');
    const see = () => document.querySelectorAll('main > section, main > div, body > section').forEach(el => {
      if (el.closest('header,footer') || el.matches('.kb-hero,.hero,#kpc-cx,#kzFx,.kzfx')) return;
      const cs = getComputedStyle(el); if (/sticky|fixed/.test(cs.position)) return;
      const c = cs.backgroundColor, m = c.match(/rgba?\(([^)]+)\)/); if (!m) return;
      const v = m[1].split(/[ ,/]+/).map(Number); if (v.length > 3 && v[3] < .3) return;
      el.style.setProperty('background-color', `rgba(${v[0]},${v[1]},${v[2]},.9)`, 'important');
    });
    see(); setTimeout(see, 900); new MutationObserver(() => setTimeout(see, 700)).observe(H, { attributes: true, attributeFilter: ['data-theme'] });
  }
  const go = () => { [still, heroes, logo, cards, sounds].forEach(f => { try { f(); } catch (e) {} }); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  addEventListener('load', () => { try { heroes(); } catch (e) {} });
})();

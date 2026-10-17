/* KPC picture-wrapped boxes, site wide (Oct 17 2026, Brandon: 'what you did to Park Commander and the trip planners, website wide').
   The empty space inside each box shows a soft, blurred club picture under a veil made from the box's OWN colour, so light boxes stay
   light and dark boxes stay dark (in dark mode too, after kpc-theme.js recolours them); boxes get a soft gold glow.
   Skipped: the Hunters Lounge / KPC Logger apps, maps, boxes that already have a picture, small boxes, printing and the guide pages. */
(function () {
  const H = document.documentElement, P = location.pathname.split('/').pop() || 'index.html';
  if (/^kpc-guide-/.test(P) || /[?&](print|pdf)=/.test(location.search) || H.hasAttribute('data-no-wrap')) return;
  const SEL = '.card,.kb-card,.link-card,.feature-card,.panel,.kd-card,.cw-card,.nw-card,.fx-card,.kz-card,.mr-card,.lv-card,.enc-card,.trailcard,.learn-card,.sm-card,.kg2-card,.vb-card,.hm-card,.scale-card,.kr-card,.usp-card,.intro-panel,.tool-card,.hub-card';
  const SKIP = '#hl,#lg,.leaflet-container,header,footer,[data-no-wrap],.kd-wrap,.usp,.hero,.kb-hero';
  const PICS = ['lake-camp', 'river-camp', 'campsite', 'journal', 'solar', 'map', 'lodge', 'night'];
  const st = document.createElement('style');
  st.textContent = '@media screen{[data-kw]{background-size:cover!important;background-position:center!important;box-shadow:0 14px 34px rgba(0,0,0,.18),0 0 22px rgba(240,180,80,.10)}[data-kw]:hover{box-shadow:0 16px 38px rgba(0,0,0,.24),0 0 26px rgba(240,180,80,.2)}}@media print{[data-kw]{background-image:none!important}}';
  document.head.appendChild(st);
  const rgb = s => { const m = String(s || '').match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return p.length >= 3 ? [p[0], p[1], p[2], p.length > 3 ? p[3] : 1] : null; };
  let n = 0;
  function wrap(force) {
    const mob = matchMedia('(max-width:700px)').matches;
    document.querySelectorAll(SEL).forEach(el => {
      if (el.closest(SKIP)) return;
      if (el.dataset.kw && !force) return;
      const r = el.getBoundingClientRect(); if (r.width < 160 || r.height < 90) return;
      const cs = getComputedStyle(el), bi = el.dataset.kw ? '' : cs.backgroundImage;
      if (bi && bi !== 'none' && bi.indexOf('url(') >= 0) return;     /* it already has its own picture */
      const c = rgb(cs.backgroundColor); if (!c || c[3] < .5) return;   /* see-through boxes are left alone */
      if (!el.dataset.kw) el.dataset.kw = PICS[n++ % PICS.length];
      const pic = 'bg-' + el.dataset.kw + (mob ? '-mobile' : '') + '.jpg';
      const v = `rgba(${c[0]},${c[1]},${c[2]},`, lum = (c[0] * .299 + c[1] * .587 + c[2] * .114) / 255, a1 = lum > .55 ? .8 : .64, a2 = lum > .55 ? .88 : .78;
      el.style.setProperty('background-image', `linear-gradient(${v}${a1}),${v}${a2})),url('${pic}')`, 'important');
    });
  }
  const go = f => { try { wrap(f); } catch (e) {} };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => go()); else go();
  addEventListener('load', () => { go(); setTimeout(() => go(true), 900); });
  /* dark mode switches recolour the boxes: redo the veils to match */
  new MutationObserver(() => setTimeout(() => go(true), 700)).observe(H, { attributes: true, attributeFilter: ['data-theme'] });
  ['click', 'toggle'].forEach(ev => document.addEventListener(ev, () => setTimeout(() => go(), 400), true));   /* folded sections opened later */
  let t = 0; new MutationObserver(() => { clearTimeout(t); t = setTimeout(() => go(), 500); }).observe(document.body || H, { childList: true, subtree: true });
})();

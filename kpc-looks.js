/* KPC page LOOKS (Oct 17 2026, Brandon: looks, no effects, for the CW Practice Room, Happening Now and Voice Pileup Practice).
   Mount: <div id="kpc-looks"></div>. 🏕 CLASSIC = the page as it was; 🔥 CABIN LODGE / 🌌 NIGHT SKY / 🔥 CAMPFIRE = dark colours with a
   blurred club picture behind every section (fixed, so it reads as one backdrop); 🌑 DARK = plain dark. Saved per page in
   localStorage kpcLook:<page>; kpc-theme.js reads it before the page draws (no flash) and turns the dark colours on for it. */
(function () {
  const mount = document.getElementById('kpc-looks'); if (!mount) return;
  const H = document.documentElement, PAGE = location.pathname.split('/').pop() || 'index.html', KEY = 'kpcLook:' + PAGE;
  const L = [['classic', '🏕 CLASSIC'], ['lodge', '🪵 CABIN LODGE'], ['night', '🌌 NIGHT SKY'], ['camp', '🔥 CAMPFIRE'], ['dark', '🌑 DARK']];
  const PIC = { lodge: 'bg-lodge', night: 'bg-night', camp: 'bg-campsite' }, VEIL = { lodge: '20,12,6', night: '6,10,22', camp: '18,10,6', dark: '8,8,8' };
  const ACC = { lodge: '#e3a24a', night: '#7fd3e8', camp: '#ff9a3c', dark: '#ff8a3d' };
  const st = document.createElement('style');
  st.textContent = '.kpl{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:6px;padding:10px 12px;background:#0b0b0b;border-bottom:1px solid rgba(213,166,58,.35)}'
    + '.kpl span{font:900 11px Arial;letter-spacing:1.6px;color:#a59e8c;margin-right:2px}'
    + '.kpl button{border:1px solid rgba(255,255,255,.22);background:rgba(255,255,255,.04);color:#eee;border-radius:999px;padding:6px 12px;font:800 11.5px Arial;letter-spacing:.8px;cursor:pointer}'
    + '.kpl button.on{background:var(--kpl-acc,#d5a63a);border-color:var(--kpl-acc,#d5a63a);color:#160d04}'
    + 'html[data-look] body{background:#060606!important}'
    + 'html[data-look] [data-kpl-pic]{background-attachment:fixed!important;background-size:cover!important;background-position:center!important}'
    + '@media(max-width:700px){.kpl{padding:8px 10px}.kpl button{padding:5px 9px;font-size:10.5px}html[data-look] [data-kpl-pic]{background-attachment:scroll!important}}'
    + '@media print{[data-kpl-pic]{background-image:none!important}}';
  document.head.appendChild(st);
  mount.className = 'kpl'; mount.setAttribute('data-keep-light', ''); mount.setAttribute('role', 'group'); mount.setAttribute('aria-label', 'Page look');
  mount.innerHTML = '<span>LOOK:</span>' + L.map(([k, t]) => `<button type="button" data-kpl="${k}">${t}</button>`).join('');
  const cur = () => H.getAttribute('data-look') || 'classic';
  const SEL = 'main > section, main > div, body > section, body > div.section, section.section, main section';
  function paint() {
    const lk = cur(), mob = matchMedia('(max-width:700px)').matches;
    mount.style.setProperty('--kpl-acc', ACC[lk] || '#d5a63a');
    mount.querySelectorAll('[data-kpl]').forEach(b => b.classList.toggle('on', b.dataset.kpl === lk));
    document.querySelectorAll('[data-kpl-pic]').forEach(el => { el.style.removeProperty('background-image'); el.removeAttribute('data-kpl-pic'); });
    if (lk === 'classic') return;
    const pic = PIC[lk];
    document.querySelectorAll(SEL).forEach(el => {
      if (el.closest('header,footer,.hero,.lv-hero,#kpc-cx,#kpc-looks,.leaflet-container,[data-kw]') || el === mount) return;
      if (el.parentElement && el.parentElement.closest('[data-kpl-pic]')) return;     /* only the outer block */
      const r = el.getBoundingClientRect(); if (r.width < 300 || r.height < 120) return;
      const bi = getComputedStyle(el).backgroundImage; if (bi && bi.indexOf('url(') >= 0) return;
      el.setAttribute('data-kpl-pic', lk);
      const v = VEIL[lk];
      el.style.setProperty('background-image', pic ? `linear-gradient(rgba(${v},.6),rgba(${v},.76)),url('${pic}${mob ? '-mobile' : ''}.jpg')` : `linear-gradient(rgba(${v},.96),rgba(${v},.96))`, 'important');
    });
  }
  mount.addEventListener('click', e => {
    const b = e.target.closest('[data-kpl]'); if (!b) return; const k = b.dataset.kpl;
    try { localStorage.setItem(KEY, k); } catch (err) {}
    if (k === 'classic') H.removeAttribute('data-look'); else H.setAttribute('data-look', k);
    if (window.KPCTheme && KPCTheme.refresh) KPCTheme.refresh();
    setTimeout(paint, 60); setTimeout(paint, 900);
  });
  const go = () => { try { paint(); } catch (e) {} };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go); else go();
  addEventListener('load', () => setTimeout(go, 400));
})();

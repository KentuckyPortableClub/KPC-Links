/* KPC safety / "check for yourself" notes (Oct 17 2026, Brandon approved the list). One small note box per page, placed right
   under the hero (and its bars). Text is per page (W below). Skipped when printing. Close (✕) hides it for this visit. */
(function () {
  const P = location.pathname.split('/').pop() || 'index.html';
  const BOUND = '<b>A guide, not the final word.</b> Lines can be off and GPS can drift. <b>POTA, WWFF and SOTA decide what counts.</b>';
  const CALC = '<b>Starting numbers only.</b> Check SWR before you transmit, fuse every battery lead, and stay clear of power lines.';
  const W = {
    'kpc-in-park.html': ['⚠️', BOUND], 'kpc-kit.html': ['⚠️', BOUND], 'kpc-park-info.html': ['⚠️', BOUND],
    'kpc-spot-me.html': ['📣', '<b>These spots are real.</b> They show on pota.app for everyone, so only spot a station that\'s really on the air. No test spots.'],
    'kpc-weather.html': ['⛈', '<b>Forecasts can be wrong.</b> If you hear thunder, take the antenna down and get to a car or building.'],
    'kpc-antenna.html': ['🔧', CALC], 'kpc-battery.html': ['🔋', '<b>Starting numbers only.</b> Batteries give less than the label in the cold and as they age, so carry extra.'],
    'kpc-harmonics.html': ['🔧', CALC], 'kpc-radials.html': ['🔧', CALC], 'kpc-antenna-model.html': ['🔧', CALC], 'kpc-calc.html': ['🔧', CALC], 'kpc-loaded-verticals.html': ['🔧', CALC],
    'kpc-kids.html': ['👪', '<b>Grown-ups:</b> nothing about your child is saved or sent. <b>Kids:</b> ask a grown-up before using a real radio.'],
    'kpc-maprep.html': ['🧭', '<b>A research start only.</b> POTA (and SOTA and WWFF) make the final call.'],
    'kpc-suggest.html': ['🧭', '<b>A research start only.</b> POTA (and SOTA and WWFF) make the final call.'],
    'kpc-logger.html': ['💾', '<b>Your log lives only on this device.</b> Download a copy after each outing.'],
    'kpc-hunt.html': ['💾', '<b>Your log lives only on this device.</b> Download a copy after each outing.']
  };
  const w = W[P]; if (!w || /[?&](print|pdf)=/.test(location.search)) return;
  try { if (sessionStorage.getItem('kpcWarnX:' + P)) return; } catch (e) {}
  const css = document.createElement('style');
  css.textContent = '.kpw{display:flex;gap:12px;align-items:flex-start;max-width:1100px;margin:14px auto;padding:12px 16px;border-radius:12px;border:1px solid #e0a21a;border-left:6px solid #e0a21a;background:#fff8e6;color:#3d3220;font:14px/1.5 Arial,sans-serif;position:relative;z-index:3;box-shadow:0 8px 20px rgba(0,0,0,.12)}'
    + '.kpw .i{font-size:22px;line-height:1.2}.kpw .x{margin-left:auto;border:0;background:transparent;font-size:16px;cursor:pointer;color:#7a5c1a;padding:0 2px}'
    + '@media(max-width:1130px){.kpw{margin:12px}}@media print{.kpw{display:none!important}}'
    + 'html[data-theme=dark] .kpw{background:#2a2110!important;color:#f1e3c2!important}html[data-theme=dark] .kpw b{color:#ffd27a!important}';
  document.head.appendChild(css);
  const box = document.createElement('div'); box.className = 'kpw'; box.setAttribute('role', 'note'); box.setAttribute('data-keep-light', '');
  box.innerHTML = `<span class="i" aria-hidden="true">${w[0]}</span><div>${w[1]}</div><button type="button" class="x" aria-label="Hide this note">✕</button>`;
  box.querySelector('.x').onclick = () => { box.remove(); try { sessionStorage.setItem('kpcWarnX:' + P, '1'); } catch (e) {} };
  function place() {
    if (P === 'kpc-hunt.html') { const t = document.querySelector('#lgModal .hl-mbox h2'); if (t) { t.after(box); return true; } return false; }
    if (P === 'kpc-logger.html') { const t = document.getElementById('cFiles'); if (t) { t.insertBefore(box, t.children[1] || null); return true; } return false; }
    let h = document.querySelector('.tool-head, .kb-hero, section.hero, header.hero, .hm-hero, .lv-hero'); if (!h) return false;
    while (h.nextElementSibling && /^(kpc-cx|kpc-season-bar|kzFx|kpc-looks)$/.test(h.nextElementSibling.id || '') || (h.nextElementSibling && /cw-switch|toolnav/.test(h.nextElementSibling.className || ''))) h = h.nextElementSibling;
    h.after(box); return true;
  }
  if (!place()) addEventListener('DOMContentLoaded', place);
})();

/* KPC safety / "check for yourself" notes (Oct 17 2026, Brandon approved the list). One small note box per page, placed right
   under the hero (and its bars). Text is per page (W below). Skipped when printing. Close (✕) hides it for this visit. */
(function () {
  const P = location.pathname.split('/').pop() || 'index.html';
  const BOUND = '<b>A guide, not the final word.</b> Our boundary check uses official maps where we have them, but lines can be off, GPS can drift, and some land inside a park line is private. <b>POTA (and WWFF / SOTA) decide what counts</b>: check the official park map and the program\'s own rules before you rely on a spot.';
  const CALC = '<b>Starting numbers, not guarantees.</b> Cut wire a little long and trim, and check with an SWR meter or analyzer before you transmit. Put a fuse on every battery lead, and keep wires, masts and throw lines well away from power lines.';
  const W = {
    'kpc-in-park.html': ['⚠️', BOUND], 'kpc-kit.html': ['⚠️', BOUND], 'kpc-park-info.html': ['⚠️', BOUND],
    'kpc-spot-me.html': ['📣', '<b>Spots go to the real sites.</b> A POTA spot from here appears on pota.app for everyone in a few seconds, so only spot a station that is really on the air, on that frequency, from that park. Please don\'t send test spots.'],
    'kpc-weather.html': ['⛈', '<b>Forecasts can be wrong.</b> Use this to plan, then watch the sky. If you hear thunder or see lightning, take the antenna down and get to a car or building. A mast or wire in a storm is the tallest thing around: don\'t wait it out under a tree.'],
    'kpc-antenna.html': ['🔧', CALC], 'kpc-battery.html': ['🔋', CALC.replace('Cut wire a little long and trim, and check with an SWR meter or analyzer before you transmit.', 'Real batteries give less than the label in the cold and as they age, so carry extra.')],
    'kpc-harmonics.html': ['🔧', CALC], 'kpc-radials.html': ['🔧', CALC], 'kpc-antenna-model.html': ['🔧', CALC], 'kpc-calc.html': ['🔧', CALC], 'kpc-loaded-verticals.html': ['🔧', CALC],
    'kpc-kids.html': ['👪', '<b>For grown-ups:</b> nothing about your child is saved or sent anywhere. Stars and badges stay on this device only, and names typed for the certificate are never stored. <b>Kids:</b> ask a grown-up before you use a real radio, and only talk on the air with a licensed ham next to you.'],
    'kpc-maprep.html': ['🧭', '<b>A research start only.</b> This tool reads public records and maps to help you look into a place. POTA decides which places become parks, and its own rules and Mapping Representatives make the final call.'],
    'kpc-suggest.html': ['🧭', '<b>A research start only.</b> This tool reads public records and maps to help you look into a place. POTA (and SOTA / WWFF) decide which places are added, and their own rules and volunteers make the final call.'],
    'kpc-logger.html': ['💾', '<b>Your log lives only on this phone or computer.</b> Nothing is sent to KPC. Clearing your browser or losing the phone can lose it, so download a copy (Download &amp; files) after each outing.'],
    'kpc-hunt.html': ['💾', '<b>Your log lives only on this device.</b> Nothing is sent to KPC. Download a copy for QRZ now and then (MY LOG FILES), because clearing the browser or losing the phone can lose it.']
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

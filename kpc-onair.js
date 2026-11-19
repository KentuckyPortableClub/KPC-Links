/* KPC website: ● ON AIR + ■ STOP ALL (Nov 19 2026, Lounge round; the KPC app's 0.9.6 banner, for the website pages that can key a
   radio: the VIP FT8 tab (kpc-logger-ft8.js) and the Hunters Lounge radio card (kpc-hunt-x.js: hold to talk, CW, scan).
   Each of those registers what it can send:  KPCOnAir.add(id, { label, busy: () => bool, stop: why => {} }).
   While anything is busy (or KPCCat says the radio is keyed) a slim red line sits at the top of the page: ● ON AIR m:ss · what ·
   ■ STOP ALL (Esc). STOP ALL / Esc calls every stop and then unkeys the radio over CAT as a backstop. Loaded by the pages' own
   scripts (no page needs a new <script> tag). Nothing here keys a radio: it only stops. FABLE REVIEWS BEFORE LIVE. */
(function (G) {
  'use strict';
  if (G.KPCOnAir) return;
  const SRC = {}; let since = 0, el = null;
  const busyList = () => Object.keys(SRC).filter(k => { try { return !!SRC[k].busy(); } catch (e) { return false; } });
  const catKeyed = () => { try { return !!(G.KPCCat && KPCCat.txing && KPCCat.txing()); } catch (e) { return false; } };
  function make() {
    if (el || !document.body) return;
    el = document.createElement('div'); el.id = 'kpcOnAir'; el.hidden = true; el.setAttribute('role', 'status');
    el.innerHTML = '<b>● ON AIR</b> <span class="t">0:00</span> <span class="w"></span><button type="button">■ STOP ALL <small>(Esc)</small></button>';
    el.querySelector('button').onclick = () => stopAll('STOP ALL');
    document.body.appendChild(el);
    const st = document.createElement('style'); st.textContent = '#kpcOnAir{position:fixed;left:0;right:0;top:0;z-index:99999;display:flex;align-items:center;gap:10px;padding:4px 10px;background:#b3131f;color:#fff;font:700 13px system-ui,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.5)}#kpcOnAir[hidden]{display:none}#kpcOnAir .w{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:600}#kpcOnAir button{border:2px solid #fff;background:#fff;color:#b3131f;border-radius:8px;font:800 13px system-ui,sans-serif;padding:3px 10px;cursor:pointer}#kpcOnAir small{font-weight:600}';
    document.head.appendChild(st);
  }
  function tick() {
    make(); if (!el) return;
    const b = busyList(), on = b.length > 0 || catKeyed();
    if (on && !since) since = Date.now(); if (!on) since = 0;
    el.hidden = !on; if (!on) return;
    const s = Math.floor((Date.now() - since) / 1000);
    el.querySelector('.t').textContent = Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
    el.querySelector('.w').textContent = b.length ? b.map(k => SRC[k].label || k).join(' · ') : 'radio keyed';
  }
  async function stopAll(why) {
    for (const k of Object.keys(SRC)) { try { SRC[k].stop(why || 'STOP ALL'); } catch (e) {} }
    try { if (G.KPCCat && KPCCat.connected && KPCCat.connected() && KPCCat.ptt) await KPCCat.ptt(false, 'cat'); } catch (e) {}
    tick();
  }
  /* Esc stops everything while anything is on the air (capture: before a page's own Esc handlers) */
  addEventListener('keydown', e => { if (e.key === 'Escape' && (busyList().length || catKeyed())) { e.preventDefault(); stopAll('Esc'); } }, true);
  setInterval(tick, 250);
  G.KPCOnAir = { add: (id, o) => { SRC[id] = o; }, remove: id => { delete SRC[id]; }, stopAll, busy: () => busyList(), _tick: tick };
})(window);

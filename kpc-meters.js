/* KPC radio METERS popup for the website (Oct 26, Brandon: 'Radio meters (S meter, power, SWR) with options to change to analog or
   digital' … 'meters need to be a popup'). The needle dials + bars are the KPC app's (kpc-app www/kpc-meters.js, Opus 0.7.3), here as
   ONE floating window: open it with any [data-meters-open] button, drag it by its top bar, ✕ closes it. Readings come from
   KPCCat.meters() (kpc-cat.js) once a second while the window is open and the radio is connected.
   Settings (this browser only): localStorage kpcMetersWeb {style: analog|digital, show[], x, y}. window.KPCMeters.open()/close(). */
(function (G) {
  'use strict';
  if (G.KPCMeters) return;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const S = Object.assign({ style: 'analog', show: ['s', 'po', 'alc', 'swr'] }, LS('kpcMetersWeb', {}));
  const save = () => { try { localStorage.setItem('kpcMetersWeb', JSON.stringify(S)); } catch (e) {} };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const sTxt = v => v == null ? '—' : v <= 0 ? 'S' + Math.max(0, Math.min(9, Math.round(9 + v / 6))) : 'S9+' + Math.round(v);
  const swrOf = v => v <= 0 ? 1 : v <= 30 ? 1 + v / 30 : v <= 60 ? 2 + (v - 30) / 30 : 3 + (v - 60) / 40 * 2;
  const DEF = {
    s: { label: 'S', f: v => v <= 0 ? (v + 54) / 54 * 0.6 : 0.6 + v / 60 * 0.4, ticks: [[-48, '1'], [-36, '3'], [-24, '5'], [-12, '7'], [0, '9'], [20, '+20'], [40, '+40'], [60, '+60']], red: 0.6, txt: sTxt, help: 'signal strength: S1–S9, dB over S9' },
    po: { label: 'PWR OUT', f: v => v / 100, ticks: [[0, '0'], [25, '25'], [50, '50'], [75, '75'], [100, '100%']], red: 2, txt: v => v == null ? '—' : v + '%', help: 'power going out while you transmit' },
    alc: { label: 'ALC', f: v => v / 100, ticks: [[0, '0'], [50, ''], [100, 'MAX']], red: 0.62, txt: v => v == null ? '—' : v + '%', help: 'keep it low on FT8 and the data modes' },
    swr: { label: 'SWR', f: v => v / 100, ticks: [[0, '1'], [15, '1.5'], [30, '2'], [60, '3'], [100, '∞']], red: 0.3, txt: v => v == null ? '—' : '≈' + swrOf(v).toFixed(1), help: 'how well the antenna is matched' },
    comp: { label: 'COMP', f: v => v / 100, ticks: [[0, '0'], [50, ''], [100, 'MAX']], red: 0.75, txt: v => v == null ? '—' : v + '%', help: 'speech compressor' },
    idd: { label: 'IDD', f: v => v / 100, ticks: [[0, '0'], [50, ''], [100, 'MAX']], red: 0.85, txt: v => v == null ? '—' : v + '%', help: 'drain current' },
    vdd: { label: 'VDD', f: v => v / 100, ticks: [[0, '0'], [50, ''], [100, 'MAX']], red: 2, txt: v => v == null ? '—' : v + '%', help: 'supply voltage' }
  };
  const ORDER = ['s', 'po', 'alc', 'swr', 'comp', 'idd', 'vdd'];
  const css = document.createElement('style');
  css.textContent = `
#kpcMet{position:fixed;z-index:3000;width:min(440px,calc(100vw - 16px));max-height:calc(100vh - 16px);overflow:auto;box-sizing:border-box;border-radius:16px;border:1px solid #d5a63a;background:#101611;color:#efe9da;box-shadow:0 18px 50px rgba(0,0,0,.6);font:13px Arial,Helvetica,sans-serif}
#kpcMet[hidden]{display:none}
#kpcMet .km-top{display:flex;align-items:center;gap:6px;padding:8px 8px 8px 12px;border-bottom:1px solid rgba(213,166,58,.35);cursor:move;touch-action:none;user-select:none;background:linear-gradient(180deg,#1a231c,#121912);border-radius:16px 16px 0 0}
#kpcMet .km-top b{flex:1;font:900 12px Arial;letter-spacing:1.6px;color:#f0c96b;white-space:nowrap}
#kpcMet button{min-height:32px;padding:4px 10px;border-radius:999px;border:1px solid rgba(240,201,107,.6);background:transparent;color:#f0c96b;font:900 11px Arial;letter-spacing:.8px;cursor:pointer;white-space:nowrap}
#kpcMet button.on{background:linear-gradient(#f6d58a,#d5a63a);color:#2a1a05;border-color:#d5a63a}
#kpcMet .km-x{min-width:32px;padding:4px 0;font-size:14px}
#kpcMet .km-body{padding:10px}
#kpcMet .km-msg{margin:0 0 8px;color:#bdb6a5;font-size:12.5px}
#kpcMet .km-g{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
#kpcMet .km-g canvas{display:block;width:100%;height:auto;border-radius:10px;border:1px solid #2c362e}
#kpcMet .km-r{display:grid;grid-template-columns:64px 1fr 58px;gap:8px;align-items:center;margin:6px 0;font:700 11px Arial;color:#bdb6a5}
#kpcMet .km-r b{text-align:right;font:700 13px ui-monospace,Menlo,monospace;color:#efe9da}
#kpcMet .km-t{height:12px;border-radius:99px;background:#1f2a22;overflow:hidden}
#kpcMet .km-b{height:100%;width:0;border-radius:99px;background:#3ddc84;transition:width .25s}
#kpcMet .km-b.mid{background:#f0c96b}#kpcMet .km-b.bad{background:#e05c5c}#kpcMet .km-b.off{background:#444}
#kpcMet .km-set{margin:0 0 10px;padding:8px 10px;border:1px dashed rgba(240,201,107,.45);border-radius:10px}
#kpcMet .km-set label{display:flex;gap:8px;align-items:center;margin:5px 0;font-size:13px}
#kpcMet .km-set small{color:#9d968a}`;
  document.head.appendChild(css);
  let box = null, open = false, setOpen = false, LAST = null, cur = {}, pos = {}, peak = { v: -60, t: 0 }, sig = '', timer = null, busyM = false;
  const connected = () => !!(G.KPCCat && KPCCat.connected && KPCCat.connected());
  function shown() { return S.show.filter(k => DEF[k] && (k === 's' || !LAST || LAST[k] != null)); }
  function place() {
    const w = box.offsetWidth || 360, h = box.offsetHeight || 260, hdr = document.querySelector('header.site-nav'), top0 = hdr ? hdr.getBoundingClientRect().bottom + 8 : 8;
    let x = S.x == null ? innerWidth - w - 8 : S.x, y = S.y == null ? top0 : S.y;
    x = Math.max(8, Math.min(innerWidth - w - 8, x)); y = Math.max(8, Math.min(innerHeight - Math.min(h, 120), y));
    box.style.left = x + 'px'; box.style.top = y + 'px';
  }
  function build() {
    box = document.createElement('div'); box.id = 'kpcMet'; box.hidden = true; box.setAttribute('role', 'dialog'); box.setAttribute('aria-label', 'Radio meters');
    document.body.appendChild(box);
    box.addEventListener('click', e => {
      const t = e.target.closest('button'); if (!t) return;
      if (t.dataset.km === 'x') return close();
      if (t.dataset.km === 'style') { S.style = S.style === 'analog' ? 'digital' : 'analog'; save(); sig = ''; draw(); return; }
      if (t.dataset.km === 'set') { setOpen = !setOpen; sig = ''; draw(); return; }
    });
    box.addEventListener('change', e => { const c = e.target.closest('[data-kmk]'); if (!c) return; S.show = ORDER.filter(k => { const x = box.querySelector(`[data-kmk="${k}"]`); return x && x.checked; }); if (!S.show.length) S.show = ['s']; save(); sig = ''; draw(); });
    /* drag by the top bar */
    let drag = null;
    box.addEventListener('pointerdown', e => { if (!e.target.closest('.km-top') || e.target.closest('button')) return; const r = box.getBoundingClientRect(); drag = { dx: e.clientX - r.left, dy: e.clientY - r.top, id: e.pointerId }; try { box.setPointerCapture(e.pointerId); } catch (x) {} });
    box.addEventListener('pointermove', e => { if (!drag || e.pointerId !== drag.id) return; S.x = e.clientX - drag.dx; S.y = e.clientY - drag.dy; place(); });
    const end = e => { if (!drag || e.pointerId !== drag.id) return; drag = null; const r = box.getBoundingClientRect(); S.x = r.left; S.y = r.top; save(); };
    box.addEventListener('pointerup', end); box.addEventListener('pointercancel', end);
    addEventListener('resize', () => { if (open) place(); });
  }
  function draw() {
    if (!box) return; const keys = shown(), on = connected();
    const msg = !on ? 'Connect your radio first (RADIO CONTROL → CONNECT MY RADIO). The meters read it once a second.' : !LAST ? 'Reading the radio…' : (LAST.pwr != null ? 'Power set ' + LAST.pwr + '%' : '') ;
    const s2 = keys.join(',') + '|' + S.style + '|' + setOpen;
    if (s2 !== sig) {
      sig = s2;
      box.innerHTML = `<div class="km-top"><b>📟 METERS</b><button type="button" data-km="style">${S.style === 'analog' ? '◐ ANALOG' : '▮ DIGITAL'}</button><button type="button" data-km="set" class="${setOpen ? 'on' : ''}" aria-label="Which meters">⚙</button><button type="button" class="km-x" data-km="x" aria-label="Close the meters">✕</button></div>
        <div class="km-body">${setOpen ? `<div class="km-set"><small>Tap ◐ ANALOG / ▮ DIGITAL above to switch. Pick the meters to show (one your radio does not send stays hidden):</small>${ORDER.map(k => `<label><input type="checkbox" data-kmk="${k}"${S.show.includes(k) ? ' checked' : ''}> <span>${esc(DEF[k].label)} <small>(${esc(DEF[k].help)})</small></span></label>`).join('')}</div>` : ''}
        <p class="km-msg" data-kmmsg></p>
        ${S.style === 'analog' ? `<div class="km-g">${keys.map(k => `<canvas data-kc="${k}" width="200" height="118" aria-label="${esc(DEF[k].label)} meter"></canvas>`).join('')}</div>`
          : keys.map(k => `<div class="km-r"><span>${esc(DEF[k].label)}</span><div class="km-t"><div class="km-b off" data-kb="${k}"></div></div><b data-kt="${k}">—</b></div>`).join('')}</div>`;
      pos = {};
    }
    const me = box.querySelector('[data-kmmsg]'); if (me) { me.textContent = msg; me.hidden = !msg; }
    keys.forEach(k => { const v = LAST && on ? LAST[k] : null; cur[k] = v;
      if (S.style !== 'analog') { const b = box.querySelector(`[data-kb="${k}"]`), t = box.querySelector(`[data-kt="${k}"]`); if (!b) return; const f = v == null ? 0 : Math.max(0, Math.min(1, DEF[k].f(v)));
        b.style.width = (f * 100) + '%'; b.className = 'km-b ' + (v == null ? 'off' : f >= DEF[k].red ? 'bad' : f >= DEF[k].red * 0.8 ? 'mid' : ''); t.textContent = DEF[k].txt(v); } });
    if (S.style === 'analog') anim();
  }
  let raf = false;
  function anim() { if (raf) return; raf = true; requestAnimationFrame(step); }
  function step() {
    raf = false; if (!open) return; let more = false; const now = performance.now();
    box.querySelectorAll('canvas[data-kc]').forEach(cv => {
      const k = cv.dataset.kc, d = DEF[k], v = cur[k], tgt = v == null ? 0 : Math.max(0, Math.min(1, d.f(v)));
      const st = pos[k] || (pos[k] = { p: 0 }); st.p += (tgt - st.p) * 0.22; if (Math.abs(tgt - st.p) > 0.002) more = true;
      if (k === 's' && v != null) { if (v >= peak.v) { peak.v = v; peak.t = now; } else if (now - peak.t > 1500) { peak.v = Math.max(v, peak.v - 0.4); more = true; } }
      dial(cv, d, st.p, v, k === 's' && v != null ? Math.max(0, Math.min(1, d.f(peak.v))) : null);
    });
    if (more) anim();
  }
  function dial(cv, d, p, v, pk) {
    const g = cv.getContext('2d'), W = cv.width, H = cv.height, cx = W / 2, cy = H * 1.02, r = H * 0.9, a0 = -Math.PI / 2 - 0.82, a1 = -Math.PI / 2 + 0.82, at = f => a0 + (a1 - a0) * f;
    g.clearRect(0, 0, W, H);
    const face = g.createLinearGradient(0, 0, 0, H); face.addColorStop(0, '#1d2620'); face.addColorStop(1, '#0f1411');
    g.fillStyle = face; g.beginPath(); if (g.roundRect) g.roundRect(1, 1, W - 2, H - 2, 10); else g.rect(1, 1, W - 2, H - 2); g.fill();
    g.lineWidth = 3; g.strokeStyle = 'rgba(240,201,107,.75)'; g.beginPath(); g.arc(cx, cy, r, at(0), at(Math.min(1, d.red))); g.stroke();
    if (d.red < 1) { g.strokeStyle = '#e05c5c'; g.beginPath(); g.arc(cx, cy, r, at(d.red), at(1)); g.stroke(); }
    g.fillStyle = '#d9cfa8'; g.font = '600 10px ui-monospace,Menlo,monospace'; g.textAlign = 'center';
    d.ticks.forEach(([tv, tl]) => { const f = Math.max(0, Math.min(1, d.f(tv))), a = at(f); g.strokeStyle = g.fillStyle; g.lineWidth = 1.5; g.beginPath(); g.moveTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r); g.lineTo(cx + Math.cos(a) * (r - 7), cy + Math.sin(a) * (r - 7)); g.stroke(); if (tl) g.fillText(tl, cx + Math.cos(a) * (r - 17), cy + Math.sin(a) * (r - 17) + 3); });
    if (pk != null) { const a = at(pk); g.strokeStyle = 'rgba(243,154,85,.9)'; g.lineWidth = 2; g.beginPath(); g.moveTo(cx + Math.cos(a) * (r + 2), cy + Math.sin(a) * (r + 2)); g.lineTo(cx + Math.cos(a) * (r - 9), cy + Math.sin(a) * (r - 9)); g.stroke(); }
    const a = at(p); g.strokeStyle = v == null ? 'rgba(150,150,150,.5)' : '#ffe3a0'; g.lineWidth = 2.2; g.shadowColor = 'rgba(255,214,120,.6)'; g.shadowBlur = 6;
    g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a) * (r + 1), cy + Math.sin(a) * (r + 1)); g.stroke(); g.shadowBlur = 0;
    g.fillStyle = '#a8a18f'; g.font = '800 10px Arial,sans-serif'; g.textAlign = 'left'; g.fillText(d.label, 8, 14);
    g.textAlign = 'right'; g.fillStyle = '#efe9da'; g.font = '800 13px ui-monospace,Menlo,monospace'; g.fillText(d.txt(v), W - 8, 15);
  }
  async function poll() {
    if (!open || busyM || document.hidden) return;
    if (!connected()) { LAST = null; draw(); return; }
    busyM = true; try { const m = await KPCCat.meters(); if (m) LAST = m; } catch (e) {} busyM = false; draw();
  }
  function openM() { if (!box) build(); open = true; box.hidden = false; sig = ''; draw(); place(); poll(); if (!timer) timer = setInterval(poll, 1000); }
  function close() { open = false; if (box) box.hidden = true; if (timer) { clearInterval(timer); timer = null; } }
  document.addEventListener('click', e => { const b = e.target.closest('[data-meters-open]'); if (!b) return; e.preventDefault(); if (open) close(); else openM(); });
  addEventListener('keydown', e => { if (e.key === 'Escape' && open) close(); });
  G.KPCMeters = { open: openM, close, isOpen: () => open, S, DEF, sTxt, swrOf };
})(window);

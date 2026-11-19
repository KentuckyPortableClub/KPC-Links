/* KPC app: STATION TIDY-UP (Opus, Nov 10 2026; Brandon: 'tidy up polish make it very user friendly with the settings etc all where
   they need to be ... tabs').
   STATION was one long page of 12+ cards (about 7 phone screens). Now:
   - a row of group tabs at the top: 👤 ME · 📻 RADIO & SOUND · 📋 LOG · 🌲 PARKS & ALERTS · 🔗 REMOTE · ❓ HELP · ALL (remembered: kpcStGrp)
   - the cards sit in their group in a sensible order (cards other files add later, like the rotator or contesting, are placed too)
   - long 'how it works' paragraphs fold into ℹ️ HOW THIS WORKS (tap to read)
   - 🔍 Find a setting still searches EVERY card, whatever tab is lit
   - anything that jumps to a setting (RADIO SETTINGS, the setup wizard, 'put your call in STATION…') lights the right tab first.
   Nothing is taken away: every card, button and setting is where it was inside its card. */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id), st = $('scrStation'); if (!AP || !st) return;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  /* group, then the order inside it: [group, test on the card's data-grp / id / heading] */
  const GRP = [['me', '👤 ME'], ['radio', '📻 RADIO & SOUND'], ['log', '📋 LOG'], ['parks', '🌲 PARKS & ALERTS'], ['remote', '🔗 REMOTE'], ['more', '➕ MORE'], ['help', '❓ HELP'], ['all', 'ALL']];
  const RULES = [
    ['me', /^my station/], ['me', /^look/],
    ['radio', /^radio cat/], ['radio', /^sound/], ['radio', /kiwi|web radio/], ['radio', /^rotator|#stRot/],
    ['log', /^log files/], ['log', /^contest|#stCx/], ['log', /^backup new phone/],
    ['parks', /^parks offline/], ['parks', /^alerts notifications/],
    ['remote', /^remote link/],
    ['help', /^alerts help/]
  ];
  const keyOf = c => ((c.dataset.grp || '') + ' #' + (c.id || '') + ' ' + ((c.querySelector('h2') || {}).textContent || '')).toLowerCase().trim();
  function place(c) { const k = keyOf(c); for (let i = 0; i < RULES.length; i++) if (RULES[i][1].test(k)) return [RULES[i][0], i]; return ['more', 999]; }
  let CUR = LS('kpcStGrp', 'me'), busy = false;
  const css = document.createElement('style');
  css.textContent = `
  .tdy-bar{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:2px 0 10px;margin:0 0 4px;position:sticky;top:0;z-index:3;background:var(--bg,#0d1117)}
  .tdy-bar::-webkit-scrollbar{display:none}
  .tdy-bar button{flex:0 0 auto;border:1px solid var(--line,#333);background:var(--panel,#161b22);color:var(--ink,#eee);border-radius:999px;padding:8px 13px;font:800 12px var(--sans,Arial);letter-spacing:.06em;white-space:nowrap;cursor:pointer}
  .tdy-bar button.on{background:var(--gold,#e8b84a);border-color:var(--gold,#e8b84a);color:#1a1405}
  .tdy-bar button[hidden]{display:none}
  #scrStation>.card.tdy-off{display:none!important}
  body.tdy-q #scrStation>.card.tdy-off{display:block!important}
  body.tdy-q #scrStation>.card.tdy-off.hide{display:none!important}
  details.tdy-how{margin:8px 0 2px}
  details.tdy-how>summary{cursor:pointer;list-style:none;font:800 11px var(--sans,Arial);letter-spacing:.08em;color:var(--goldT,#e8b84a);padding:4px 0}
  details.tdy-how>summary::-webkit-details-marker{display:none}
  details.tdy-how>summary::after{content:' ▸'}details.tdy-how[open]>summary::after{content:' ▾'}
  details.tdy-how>.hint{margin-top:4px}
  .tdy-empty{opacity:.75;font-size:13px;padding:6px 2px}
  @media(min-width:900px){#scrStation>.tdy-bar{column-span:all}}`;
  document.head.appendChild(css);
  const bar = document.createElement('div'); bar.className = 'tdy-bar'; bar.setAttribute('role', 'tablist'); bar.setAttribute('aria-label', 'Settings groups');
  bar.innerHTML = GRP.map(g => `<button type="button" role="tab" data-tg="${g[0]}">${g[1]}</button>`).join('');
  const q = $('stQ'); (q ? q.after(bar) : st.prepend(bar));
  /* long how-to text folds away (static paragraphs only: a .hint with an id is a live status line, it stays open) */
  function fold(c) {
    c.querySelectorAll(':scope .hint').forEach(p => {
      if (p.id || p.closest('details') || p.dataset.tdy || p.textContent.trim().length < 200) return;
      p.dataset.tdy = '1'; const prev = p.previousElementSibling;
      if (prev && prev.matches('details.tdy-how')) { prev.appendChild(p); return; }   /* two paragraphs in a row = one fold */
      const d = document.createElement('details'); d.className = 'tdy-how';
      d.innerHTML = '<summary>ℹ️ HOW THIS WORKS</summary>'; p.before(d); d.appendChild(p);
    });
  }
  /* the ❓ HELP tab's card starts with the way into the help page and the setup wizard */
  function helpBtns(c) {
    if (c.dataset.tg !== 'help' || c.querySelector('.tdy-help') || !G.KPCHelp) return;
    const h = c.querySelector('h2'); if (!h) return;
    h.insertAdjacentHTML('afterend', '<div class="row tdy-help"><button type="button" class="b gold" data-th="open">❓ OPEN THE HELP PAGE</button><button type="button" class="b" data-th="wiz">🧙 RADIO SETUP WIZARD</button></div>');
    c.querySelector('[data-th="open"]').onclick = () => KPCHelp.open(); c.querySelector('[data-th="wiz"]').onclick = () => KPCHelp.wizard();
  }
  function arrange() {
    if (busy) return; busy = true;
    try {
      const cards = [...st.querySelectorAll(':scope > .card')];
      const L = cards.map((c, i) => { const p = place(c); c.dataset.tg = p[0]; fold(c); helpBtns(c); return { c, g: GRP.findIndex(x => x[0] === p[0]), o: p[1], i }; });
      L.sort((a, b) => a.g - b.g || a.o - b.o || a.i - b.i);
      let after = bar; L.forEach(x => { if (after.nextElementSibling !== x.c) after.after(x.c); after = x.c; });
      const lite = document.documentElement.dataset.lite;
      GRP.forEach(g => { const b = bar.querySelector(`[data-tg="${g[0]}"]`); if (g[0] === 'all') return;
        b.hidden = !cards.some(c => c.dataset.tg === g[0] && !(lite && c.dataset.lite === 'off')); });
      if (bar.querySelector(`[data-tg="${CUR}"]`).hidden) CUR = 'me';
      show(CUR, true);
    } finally { busy = false; }
  }
  function show(g, quiet) {
    CUR = g; if (!quiet) SV('kpcStGrp', g);
    bar.querySelectorAll('button').forEach(b => { const on = b.dataset.tg === g; b.classList.toggle('on', on); b.setAttribute('aria-selected', on ? 'true' : 'false'); });
    st.querySelectorAll(':scope > .card').forEach(c => c.classList.toggle('tdy-off', g !== 'all' && c.dataset.tg !== g));
  }
  bar.addEventListener('click', e => { const b = e.target.closest('[data-tg]'); if (!b) return; show(b.dataset.tg); b.scrollIntoView({ block: 'nearest', inline: 'center' }); st.scrollTop = 0; try { (document.scrollingElement || document.documentElement).scrollTop = 0; } catch (x) {} });
  /* 🔍 searching = every card (the app's own search hides the ones that don't match) */
  if (q) q.addEventListener('input', () => document.body.classList.toggle('tdy-q', !!q.value.trim()));
  /* jumps into STATION light the right tab first */
  function reveal(el) {
    const c = el && el.closest && el.closest('#scrStation > .card'); if (!c || !c.classList.contains('tdy-off') || document.body.classList.contains('tdy-q')) return;
    show(c.dataset.tg);
    const d = el.closest('details.tdy-how'); if (d) d.open = true;
  }
  const sIV = Element.prototype.scrollIntoView, foc = HTMLElement.prototype.focus;
  Element.prototype.scrollIntoView = function () { try { reveal(this); } catch (e) {} return sIV.apply(this, arguments); };
  HTMLElement.prototype.focus = function () { try { reveal(this); } catch (e) {} return foc.apply(this, arguments); };
  /* 'Put your call sign in STATION → My station first' style jumps: AP.go('station') right after such a toast opens that card's tab */
  const go0 = AP.go;
  if (typeof go0 === 'function') AP.go = function (name) {
    const r = go0.apply(this, arguments);
    if (name === 'station') { const t = $('toast'); const m = t && !t.hidden && /STATION\s*→\s*([A-Za-z &]+)/.exec(t.textContent || '');
      if (m) { const w = m[1].trim().toLowerCase(), A = { 'my radio': 'radio', 'connect radio': 'radio', 'how the radio': 'radio', 'radio control': 'radio', sound: 'radio', calibrate: 'help', backup: 'log', 'log files': 'log', contesting: 'log', parks: 'parks', remote: 'remote', 'my station': 'me' };
        const k = Object.keys(A).find(a => w.indexOf(a) === 0); if (k && CUR !== 'all') show(A[k]); } }
    return r;
  };
  arrange();
  /* cards added later by other files (contesting, rotator, web radio …) */
  let T = 0; new MutationObserver(() => { if (!busy && !T) T = setTimeout(() => { T = 0; arrange(); }, 150); }).observe(st, { childList: true });
  G.KPCTidy = { show, arrange, group: () => CUR };
})(window);

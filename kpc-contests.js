/* KPC contest calendar (events.html / eventsHOLD.html, section #contests).
   Data: kpc-contests.json, refreshed every morning by .github/workflows/kpc-ses.yml:
   - "week": every contest in the next ~8 days from the WA7BNM Contest Calendar RSS feed (its terms allow
     showing the feed on a club site when labeled "WA7BNM Contest Calendar" and linked, which we do);
   - "big": the big yearly contests from their usual dates, linked to the official rules. */
(function () {
  'use strict';
  const box = document.getElementById('ccBox'); if (!box) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const NEAR = /kentucky|tennessee|ohio|indiana|illinois|missouri|west virginia|virginia/i;
  const MODES = [['all', 'ALL MODES'], ['CW', 'CW'], ['PHONE', 'PHONE'], ['DIGITAL', 'DIGITAL']];
  const KINDS = [['QSOPARTY', 'STATE QSO PARTIES'], ['NEAR', 'KY + NEIGHBORS'], ['BIG', 'BIG WEEKENDS'], ['SHORT', 'SHORT (UNDER 4 HRS)'], ['VHF', 'VHF / UHF'], ['QRP', 'QRP'], ['FIELD', 'FIELD DAY TYPE']];
  const WHEN = [['now', 'ON NOW'], ['wknd', 'THIS WEEKEND'], ['week', 'NEXT 8 DAYS'], ['m1', 'NEXT MONTH'], ['m3', 'NEXT 3 MONTHS'], ['m6', 'NEXT 6 MONTHS'], ['all', 'NEXT 12 MONTHS']];
  const WDAYS = { m1: 31, m3: 92, m6: 183 };
  let F = { when: 'week', mode: 'all', kinds: [], hideShort: false, q: '' }, shown = 15, ALL = [], lastCorral = 0;
  try { Object.assign(F, JSON.parse(localStorage.getItem('kpcContestF') || '{}')); F.q = ''; } catch (e) {}
  const save = () => { try { localStorage.setItem('kpcContestF', JSON.stringify({ when: F.when, mode: F.mode, kinds: F.kinds, hideShort: F.hideShort })); } catch (e) {} };
  const T = s => Date.parse(s.replace(/Z$/, ':00Z'));
  function prep(c, src) {
    const segs = c.segs.map(([a, b]) => [T(a), T(b)]).filter(x => isFinite(x[0]) && isFinite(x[1]));
    const s = Math.min(...segs.map(x => x[0])), e = Math.max(...segs.map(x => x[1])), hrs = Math.max(...segs.map(x => (x[1] - x[0]) / 36e5));
    const kinds = (c.kinds || []).slice();
    if (hrs <= 4) kinds.push('SHORT');
    if (/QSO PARTY/i.test(c.name) && NEAR.test(c.name)) kinds.push('NEAR');
    if (src === 'big' && !kinds.includes('BIG')) kinds.push('BIG');
    return Object.assign({}, c, { s, e, segsT: segs, hrs, kinds, src });
  }
  function weekendRange() {
    const n = new Date(), d = n.getDay(), sat = new Date(n.getFullYear(), n.getMonth(), n.getDate() + ((6 - d + 7) % 7) - (d === 0 ? 1 : 0));
    const fri = new Date(sat.getFullYear(), sat.getMonth(), sat.getDate() - 1, 18), mon = new Date(sat.getFullYear(), sat.getMonth(), sat.getDate() + 2, 6);
    return [fri.getTime(), mon.getTime()];
  }
  function list() {
    const now = Date.now(), q = F.q.trim().toUpperCase(), [w0, w1] = weekendRange();
    return ALL.filter(c => {
      if (c.e < now) return false;
      if (F.when === 'now' && !c.segsT.some(x => x[0] <= now && x[1] >= now)) return false;
      if (F.when === 'wknd' && !(c.s < w1 && c.e > w0)) return false;
      if (F.when === 'week' && c.s > now + 8.2 * 864e5) return false;
      if (WDAYS[F.when] && c.s > now + WDAYS[F.when] * 864e5) return false;
      if (F.mode !== 'all' && c.modes.length && !c.modes.includes(F.mode)) return false;
      if (F.kinds.length && !F.kinds.some(k => c.kinds.includes(k))) return false;
      if (F.hideShort && c.kinds.includes('SHORT') && !F.kinds.includes('SHORT')) return false;
      if (q && !c.name.toUpperCase().includes(q)) return false;
      return true;
    }).sort((a, b) => a.s - b.s);
  }
  const fmtD = t => new Date(t).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
  const fmtT = t => new Date(t).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  function whenTxt(c) {
    const a = c.segsT[0][0], b = c.segsT[c.segsT.length - 1][1], same = new Date(a).toDateString() === new Date(b - 1).toDateString();
    let t = same ? `${fmtD(a)} · ${fmtT(a)}–${fmtT(b)}` : `${fmtD(a)} ${fmtT(a)} → ${fmtD(b)} ${fmtT(b)}`;
    if (c.segsT.length > 1) t += ` (${c.segsT.length} sessions)`;
    return t + ' your time';
  }
  function card(c) {
    const now = Date.now(), live = c.segsT.some(x => x[0] <= now && x[1] >= now), M = new Date(c.s);
    const tags = (live ? '<span class="cc-tag live">● ON NOW</span>' : '') + (c.modes.length ? c.modes.map(m => `<span class="cc-tag m">${m}</span>`).join('') : '<span class="cc-tag dim">MODE: SEE RULES</span>') +
      c.kinds.filter(k => k !== 'BIG' || c.src === 'big').map(k => `<span class="cc-tag k">${esc((KINDS.find(x => x[0] === k) || [0, k])[1])}</span>`).join('');
    return `<article class="cc-ev${live ? ' live' : ''}${c.src === 'big' ? ' big' : ''}"><div class="cc-date"><span>${M.toLocaleDateString([], { month: 'short' }).toUpperCase()}</span><b>${M.getDate()}</b><small>${M.toLocaleDateString([], { weekday: 'short' }).toUpperCase()}</small></div>` +
      `<div class="cc-body"><div class="cc-tags">${tags}</div><h3>${esc(c.name)}</h3><p>${esc(whenTxt(c))}${c.src === 'big' ? ' · <em>usual dates, check the rules</em>' : c.when ? ` · <span class="cc-utc">${esc(c.when)}</span>` : ''}</p>` +
      (c.bands || c.exch ? `<p class="cc-x">${c.bands ? '📻 ' + esc(c.bands) + (/[a-z]/i.test(c.bands) ? '' : ' MHz') : ''}${c.bands && c.exch ? ' · ' : ''}${c.exch ? 'Exchange: ' + esc(c.exch) : ''}</p>` : '') + `</div>` +
      `<div class="cc-acts"><a href="${esc(c.url)}" target="_blank" rel="noopener">${c.src === 'big' || c.src === 'corral' ? 'RULES ↗' : 'DETAILS (WA7BNM) ↗'}</a>${c.site && c.src === 'week' ? `<a class="cc-a2" href="${esc(c.site)}" target="_blank" rel="noopener">SPONSOR ↗</a>` : ''}</div></article>`;
  }
  const chips = (list, sel, attr) => list.map(([v, l]) => `<button type="button" class="cc-chip" data-${attr}="${v}" aria-pressed="${Array.isArray(sel) ? sel.includes(v) : sel === v}">${l}</button>`).join('');
  function draw() {
    box.querySelector('.cc-when').innerHTML = chips(WHEN, F.when, 'w');
    box.querySelector('.cc-mode').innerHTML = chips(MODES, F.mode, 'm');
    box.querySelector('.cc-kind').innerHTML = `<button type="button" class="cc-chip" data-k="" aria-pressed="${!F.kinds.length}">ALL TYPES</button>` + chips(KINDS, F.kinds, 'k');
    box.querySelector('#ccHide').checked = F.hideShort;
    const L = list(), el = box.querySelector('.cc-list');
    el.innerHTML = L.length ? L.slice(0, shown).map(card).join('') + (L.length > shown ? `<button type="button" class="cc-chip cc-moreb" data-more="1">SHOW ${Math.min(15, L.length - shown)} MORE (${L.length - shown} not shown)</button>` : '')
      : `<p class="cc-none">No contests match these filters${F.when === 'now' ? ' right now' : ''}. Try another time or ALL TYPES.</p>`;
    box.querySelector('.cc-count').textContent = `${L.length} contest${L.length === 1 ? '' : 's'}` + ((F.when === 'all' || WDAYS[F.when]) ? ' · every contest through ' + (lastCorral ? new Date(lastCorral).toLocaleDateString([], { month: 'long', day: 'numeric' }) : 'the next 8 days') + ', then only the big yearly ones' : '');
  }
  box.innerHTML = `<div class="cc-tools"><div class="cc-lab">WHEN</div><div class="cc-row cc-when"></div><div class="cc-lab">MODE</div><div class="cc-row cc-mode"></div><div class="cc-lab">TYPE</div><div class="cc-row cc-kind"></div>` +
    `<div class="cc-row2"><label class="cc-chk"><input type="checkbox" id="ccHide"> Hide short weekly contests (CWT, sprints, mini-tests)</label><label class="cc-s">SEARCH<input id="ccQ" type="search" placeholder="Contest name…" aria-label="Search contests"></label></div></div>` +
    `<div class="cc-count"></div><div class="cc-list" aria-live="polite"><p class="cc-none">Loading…</p></div>` +
    `<p class="cc-note">Next 8 days: every contest from the <a href="https://www.contestcalendar.com/" target="_blank" rel="noopener">WA7BNM Contest Calendar</a> (used with its RSS feed, as its terms allow; full rules and the 5-week and 12-month calendars are on the <a href="https://www.contestcalendar.com/weeklycont.php" target="_blank" rel="noopener">WA7BNM Contest Calendar</a>). The rest of this month (and next month once ARRL posts it): every contest from ARRL's <a href="https://www.arrl.org/contest-calendar" target="_blank" rel="noopener">Contest Corral</a> (QST), with bands and exchange. Further out: the big yearly contests on their usual weekends, linked to the official rules. Times are shown in your local time. Mode comes from the Contest Corral or the contest's name; "see rules" means neither says. <span id="ccUpd"></span></p>`;
  box.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    if (b.dataset.w) { F.when = b.dataset.w; } else if (b.dataset.m) { F.mode = b.dataset.m; } else if (b.dataset.k !== undefined) { const k = b.dataset.k; F.kinds = !k ? [] : F.kinds.includes(k) ? F.kinds.filter(x => x !== k) : F.kinds.concat(k); } else if (b.dataset.more) { shown += 15; draw(); return; } else return;
    shown = 15; save(); draw();
  });
  box.querySelector('#ccHide').addEventListener('change', e => { F.hideShort = e.target.checked; shown = 15; save(); draw(); });
  box.querySelector('#ccQ').addEventListener('input', e => { F.q = e.target.value; shown = 15; draw(); });
  fetch('kpc-contests.json', { cache: 'no-cache' }).then(r => r.json()).then(d => {
    const key = c => c.name.toLowerCase().replace(/\(.*?\)|,.*$/g, '').replace(/[^a-z0-9]/g, '').slice(0, 16);
    const day = c => new Date(c.s).toISOString().slice(0, 10);
    const wk = (d.week || []).map(c => prep(c, 'week'));
    const mo = (d.month || []).map(c => prep(c, 'corral'));
    // enrich the 8-day feed with mode/bands/exchange from the ARRL Contest Corral, then add the Corral's later contests
    const mk = new Map(mo.map(c => [key(c) + day(c), c]));
    wk.forEach(c => { const m = mk.get(key(c) + day(c)); if (m) { if (!c.modes.length) c.modes = m.modes; c.bands = m.bands; c.exch = m.exch; c.site = m.url; m._dup = 1; } });
    const wkEnd = wk.length ? Math.max(...wk.map(c => c.s)) : Date.now();
    const moAdd = mo.filter(c => !c._dup && c.s > wkEnd - 864e5 && !wk.some(w => key(w) === key(c) && Math.abs(w.s - c.s) < 2 * 864e5));
    const have = wk.concat(moAdd);
    const big = (d.big || []).map(c => prep(c, 'big')).filter(c => !have.some(h => Math.abs(h.s - c.s) < 3 * 864e5 && (key(h).slice(0, 8) === key(c).slice(0, 8) || h.name.toLowerCase().includes(c.name.toLowerCase().replace(/\s*\(.*\)/, '').slice(0, 12)))));
    ALL = wk.concat(moAdd, big);
    lastCorral = mo.length ? Math.max(...mo.map(c => c.s)) : 0;

    if (d.updated) box.querySelector('#ccUpd').textContent = 'Last checked ' + new Date(d.updated).toLocaleDateString([], { month: 'short', day: 'numeric' }) + '.';
    draw();
  }).catch(() => { box.querySelector('.cc-list').innerHTML = '<p class="cc-none">The contest list could not be loaded right now. See the <a href="https://www.contestcalendar.com/weeklycont.php" target="_blank" rel="noopener">WA7BNM Contest Calendar</a>.</p>'; });
})();

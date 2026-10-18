/* KPC Kentucky college scoreboard (kpc-community.html, under the hero)
   Live games, recent finals and the next games for Kentucky's Division I schools in football, men's and women's
   basketball and baseball. Read straight from ESPN's public team schedules in the browser (no key). Live games
   refresh every minute. Each game has a LISTEN button to that school's official radio / audio page. */
(function () {
  'use strict';
  const box = document.getElementById('kpcScores'); if (!box) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const SP = {
    cf: { name: 'Football', icon: '🏈', path: 'football/college-football', months: [8, 9, 10, 11, 12, 1], slug: 'football' },
    mb: { name: "Men's basketball", icon: '🏀', path: 'basketball/mens-college-basketball', months: [11, 12, 1, 2, 3, 4], slug: 'mens-basketball' },
    wb: { name: "Women's basketball", icon: '🏀', path: 'basketball/womens-college-basketball', months: [11, 12, 1, 2, 3, 4], slug: 'womens-basketball' },
    bb: { name: 'Baseball', icon: '⚾', path: 'baseball/college-baseball', months: [2, 3, 4, 5, 6], slug: 'baseball' }
  };
  // ESPN team ids per sport; listen = the school's official radio / audio page (UK: UK Sports Network; others: the
  // schedule page, where each game has its Listen / Watch links).
  const TEAMS = [
    { k: 'UK', n: 'Kentucky', radio: 'UK Sports Network', id: { cf: 96, mb: 96, wb: 96, bb: 82 }, listen: () => 'https://ukathletics.com/uk-sports-network/' },
    { k: 'UL', n: 'Louisville', radio: 'Louisville Cardinals', id: { cf: 97, mb: 97, wb: 97, bb: 83 }, site: 'https://gocards.com' },
    { k: 'WKU', n: 'Western Kentucky', radio: 'Hilltopper Sports Network', id: { cf: 98, mb: 98, wb: 98, bb: 84 }, site: 'https://wkusports.com' },
    { k: 'EKU', n: 'Eastern Kentucky', radio: 'EKU Colonels', id: { cf: 2198, mb: 2198, wb: 2198, bb: 348 }, site: 'https://ekusports.com' },
    { k: 'MUR', n: 'Murray State', radio: 'Murray State Racers', id: { cf: 93, mb: 93, wb: 93, bb: 394 }, site: 'https://goracers.com' },
    { k: 'MORE', n: 'Morehead State', radio: 'Morehead State Eagles', id: { cf: 2413, mb: 2413, wb: 2413, bb: 391 }, site: 'https://msueagles.com' },
    { k: 'NKU', n: 'Northern Kentucky', radio: 'Northern Kentucky Norse', id: { mb: 94, wb: 94, bb: 410 }, site: 'https://nkunorse.com' },
    { k: 'BELL', n: 'Bellarmine', radio: 'Bellarmine Knights', id: { mb: 91, wb: 91, bb: 1143 }, site: 'https://athletics.bellarmine.edu' }
  ];
  /* Oct 17 (Brandon: 'remove all the ones that dont work… link just to a local station that has a play now button'):
     one 📻 button per Kentucky team = the flagship station's own site with its play button (station sites from Wikipedia /
     the school pages, Oct 17). EKU has no station: its games stream on EKUSports.com ('Listen Live'). */
  const STATION = {
    UK: ['WLAP 630', 'https://wlap.iheart.com/'], UL: ['93.9 THE VILLE', 'https://www.939theville.com/'], WKU: ['WKLX 100.7', 'https://bighitsbg.com/'],
    EKU: ['EKU LISTEN LIVE', 'https://ekusports.com/'], MUR: ['FROGGY 103.7', 'https://player.amperwave.net/2845'], MORE: ['WIVY 96.3', 'https://wivyradio.com/'],
    NKU: ['ESPN 1530', 'https://espn1530.iheart.com/'], BELL: ['ESPN 680', 'https://v7player.wostreaming.net/8860']
  };
  const stBtn = t => { const x = STATION[t.k]; return x ? `<a href="${x[1]}" target="_blank" rel="noopener" title="${esc(t.n)}: the station's live stream (press play there)">📻 ${x[0]}</a>` : ''; };
  const listenUrl = (t, sp) => t.listen ? t.listen(sp) : t.site + '/sports/' + SP[sp].slug + '/schedule';
  const KYID = {}; TEAMS.forEach(t => Object.keys(t.id).forEach(sp => KYID[sp + ':' + t.id[sp]] = t));
  let games = {}, filt = 'all', timer = null;
  try { filt = localStorage.getItem('kpcScoreF') || 'all'; } catch (e) {}

  const now = () => Date.now(), DAY = 864e5;
  function inSeason(sp) { const m = new Date().getMonth() + 1, ms = SP[sp].months; return ms.includes(m) || ms.includes(m % 12 + 1); }   // also a month early (preseason / exhibitions)
  async function teamSched(sp, tid) {
    const r = await fetch('https://site.web.api.espn.com/apis/site/v2/sports/' + SP[sp].path + '/teams/' + tid + '/schedule');
    if (!r.ok) throw new Error('HTTP ' + r.status); return r.json();
  }
  function keep(ev, sp) {
    const c = ev.competitions && ev.competitions[0]; if (!c) return;
    const t = new Date(c.date || ev.date).getTime(), st = (c.status && c.status.type) || {};
    const live = st.state === 'in', done = st.state === 'post';
    if (!live && !(done && t > now() - 7 * DAY) && !(!done && t > now() - 6 * 36e5 && t < now() + 10 * DAY)) return;
    const side = c.competitors.map(x => ({ id: x.team && x.team.id, abbr: (x.team && x.team.abbreviation) || '', name: (x.team && (x.team.shortDisplayName || x.team.displayName)) || '',
      logo: x.team && x.team.logos && x.team.logos[0] && x.team.logos[0].href, score: x.score && (x.score.displayValue != null ? x.score.displayValue : x.score), home: x.homeAway === 'home', win: x.winner,
      rank: x.curatedRank && x.curatedRank.current < 26 ? x.curatedRank.current : null, ky: KYID[sp + ':' + (x.team && x.team.id)] }));
    side.sort((a, b) => (a.home === b.home) ? 0 : a.home ? 1 : -1);   // away first, home second
    const tv = (c.broadcasts || []).map(b => b.media && b.media.shortName).filter(Boolean).slice(0, 2).join(' / ');
    games[ev.id] = { id: ev.id, sp, t, live, done, st, side, tv, url: (ev.links || []).map(l => l.href).find(h => /gamecast|game\//.test(h || '')) || ('https://www.espn.com/college-football/game/_/gameId/' + ev.id) };
  }
  async function load(only) {
    const jobs = [];
    TEAMS.forEach(t => Object.keys(t.id).forEach(sp => {
      if (!inSeason(sp)) return;
      if (only && !only.has(sp + ':' + t.id[sp])) return;
      jobs.push(teamSched(sp, t.id[sp]).then(j => (j.events || []).forEach(ev => keep(ev, sp))).catch(() => {}));
    }));
    await Promise.all(jobs); await liveFix(); draw();
  }
  /* Oct 17 (Brandon: 'see no scores'): a team's schedule doesn't update during a game, so games that should be under way
     ask ESPN's game summary for the live score and clock */
  async function liveFix() {
    const due = Object.values(games).filter(g => !g.done && g.t < now() + 5 * 6e4 && g.t > now() - 8 * 36e5);
    await Promise.all(due.map(g => fetch('https://site.web.api.espn.com/apis/site/v2/sports/' + SP[g.sp].path + '/summary?event=' + g.id).then(r => r.ok ? r.json() : null).then(j => {
      const c = j && j.header && j.header.competitions && j.header.competitions[0]; if (!c) return;
      const st = (c.status && c.status.type) || {}; g.st = st; g.live = st.state === 'in'; g.done = st.state === 'post';
      (c.competitors || []).forEach(x => { const s = g.side.find(y => y.id === (x.team && x.team.id)); if (s) { s.score = x.score != null ? (x.score.displayValue != null ? x.score.displayValue : x.score) : s.score; s.win = x.winner; } });
    }).catch(() => {})));
  }
  function statusTxt(g) {
    if (g.live) return '<b class="ks-live">● LIVE</b> ' + esc(g.st.shortDetail || '');
    if (g.done) return esc(g.st.shortDetail || 'Final');
    const d = new Date(g.t), today = new Date().toDateString() === d.toDateString(), tmr = new Date(now() + DAY).toDateString() === d.toDateString();
    const day = today ? 'Today' : tmr ? 'Tomorrow' : d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
    return esc(day + (g.st.name === 'STATUS_SCHEDULED' && /TBD/i.test(g.st.shortDetail || '') ? ' · TBD' : ' · ' + d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })));
  }
  function card(g) {
    const ky = g.side.map(s => s.ky).filter(Boolean), home = g.side.find(s => s.home && s.ky) || g.side.find(s => s.ky);
    const L = home && home.ky ? listenUrl(home.ky, g.sp) : '';
    const other = g.side.find(s => s.ky && s !== home), L2 = other ? listenUrl(other.ky, g.sp) : '';
    const row = s => `<div class="ks-t${g.done && s.win ? ' w' : ''}${s.ky ? ' ky' : ''}">${s.logo ? `<img src="${esc(s.logo)}" alt="" loading="lazy" width="22" height="22">` : '<i></i>'}` +
      `<span>${s.rank ? '<small>' + s.rank + '</small> ' : ''}${esc(s.name)}</span><b>${g.live || g.done ? esc(s.score == null ? '' : s.score) : ''}</b></div>`;
    return `<div class="ks-g${g.live ? ' live' : ''}" data-sp="${g.sp}"><div class="ks-h"><span>${SP[g.sp].icon} ${esc(SP[g.sp].name)}</span><span>${statusTxt(g)}</span></div>` +
      g.side.map(row).join('') +
      (g.tv ? '<div class="ks-tv">📺 ' + esc(g.tv) + '</div>' : '') + `<div class="ks-f"><span class="ks-b">${home && home.ky ? stBtn(home.ky) : ''}${other ? stBtn(other.ky) : ''}` +
      `<a href="${esc(g.url)}" target="_blank" rel="noopener" title="Play-by-play on ESPN">ESPN ↗</a></span></div></div>`;
  }
  function draw() {
    const all = Object.values(games).filter(g => filt === 'all' || g.sp === filt || (filt === 'bk' && (g.sp === 'mb' || g.sp === 'wb')));
    const live = all.filter(g => g.live).sort((a, b) => a.t - b.t), fin = all.filter(g => g.done).sort((a, b) => b.t - a.t), up = all.filter(g => !g.live && !g.done).sort((a, b) => a.t - b.t);
    const list = live.concat(up, fin);
    const chips = [['all', 'ALL'], ['cf', '🏈 FOOTBALL'], ['bk', '🏀 BASKETBALL'], ['bb', '⚾ BASEBALL']].filter(c => c[0] === 'all' || Object.values(games).some(g => c[0] === 'bk' ? (g.sp === 'mb' || g.sp === 'wb') : g.sp === c[0]));
    box.querySelector('.ks-chips').innerHTML = chips.map(c => `<button type="button" data-f="${c[0]}" aria-pressed="${filt === c[0]}">${c[1]}</button>`).join('');
    const track = box.querySelector('.ks-track');
    track.innerHTML = list.length ? list.map(card).join('') : '<p class="ks-none">No Kentucky games in the last week or the next 10 days. Check back on game day.</p>';
    box.querySelector('.ks-sub').textContent = (live.length ? live.length + ' live now · ' : '') + up.length + ' coming up · ' + fin.length + ' recent finals · UK, UL, WKU, EKU, Murray State, Morehead State, NKU and Bellarmine';
    box.hidden = false;
    clearTimeout(timer);
    if (live.length || up.some(g => g.t < now() + 15 * 6e4)) timer = setTimeout(() => load(new Set(live.concat(up.filter(g => g.t < now() + 15 * 6e4)).flatMap(g => g.side.filter(s => s.ky).map(s => g.sp + ':' + s.ky.id[g.sp])))), 60000);
  }
  box.innerHTML = '<div class="ks-head"><div><b>🏟️ KENTUCKY COLLEGE SCOREBOARD</b><span class="ks-sub">Loading…</span></div><div class="ks-chips"></div></div>' +
    '<div class="ks-track" tabindex="0" aria-label="Scores and upcoming games, swipe sideways"></div><p class="ks-note">Scores and times from ESPN. 📻 opens the Kentucky school\'s radio station so you can press play (some games may be blocked online). Some games are TV or ESPN+ only.</p>';
  box.querySelector('.ks-chips').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; filt = b.dataset.f; try { localStorage.setItem('kpcScoreF', filt); } catch (x) {} draw(); });
  // gentle auto-scroll ("rolling"); stops while a finger or mouse is on it, and for people who asked for less motion
  const track = box.querySelector('.ks-track');
  let hold = false, dir = 1;
  ['pointerdown', 'pointerenter', 'focusin', 'touchstart'].forEach(ev => track.addEventListener(ev, () => hold = true, { passive: true }));
  ['pointerleave', 'focusout'].forEach(ev => track.addEventListener(ev, () => setTimeout(() => hold = false, 4000)));
  track.addEventListener('touchend', () => setTimeout(() => hold = false, 6000), { passive: true });
  if (!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) setInterval(() => {
    if (hold || document.visibilityState !== 'visible' || track.scrollWidth <= track.clientWidth + 4) return;
    if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 2) dir = -1; else if (track.scrollLeft <= 0) dir = 1;
    track.scrollLeft += dir;
  }, 30);
  load();
})();

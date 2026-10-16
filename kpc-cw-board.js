/* CW Challenge Leaderboard on kpc-cw.html. Data: kpc-cw-board.json (from the Google Form, copied by
   .github/scripts/kpc_cwboard.py every 20 minutes). Form: kpc-cw-board-form.json.
   KPCCWBoard.link(kind, week, pts, wpm, call) -> pre-filled form link (kind 'copy' or 'gauntlet'; for the Gauntlet,
   wpm carries the round reached). Load this BEFORE kpc-cw.js. */
window.KPCCWBoard = (function () {
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let F = null, D = null, show = 'copy';
  const ready = Promise.all([
    fetch('kpc-cw-board-form.json').then(r => r.json()).catch(() => ({})),
    fetch('kpc-cw-board.json', { cache: 'no-cache' }).then(r => r.ok ? r.json() : {}).catch(() => ({}))
  ]).then(([f, d]) => { F = f || {}; D = d || {}; draw(); });
  function wk(off) { const d = new Date(); d.setDate(d.getDate() - 7 * (off || 0)); const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())); const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day); const y = t.getUTCFullYear(); return y + '-W' + String(Math.ceil(((t - Date.UTC(y, 0, 1)) / 864e5 + 1) / 7)).padStart(2, '0'); }
  function link(kind, week, pts, wpm, call) {
    if (!F || !F.url) return '';
    const p = new URLSearchParams({ usp: 'pp_url' });
    const c = (call || '').toUpperCase().trim();
    if (c && c !== 'K4TEST') p.set(F.callEntry, c);
    p.set(F.kindEntry, F.kinds[kind === 'gauntlet' ? 'gauntlet' : 'copy']);
    p.set(F.weekEntry, week); p.set(F.pointsEntry, String(pts)); p.set(F.wpmEntry, String(wpm));
    return F.url + '?' + p.toString();
  }
  function table(rows, kind) {
    if (!rows || !rows.length) return '<p class="dim">No scores yet. Play the challenge, then tap SUBMIT MY SCORE.</p>';
    return '<table class="cwb-t"><thead><tr><th>#</th><th>CALL</th><th>POINTS</th><th>' + (kind === 'gauntlet' ? 'ROUND' : 'TOP WPM') + '</th></tr></thead><tbody>' +
      rows.slice(0, 15).map((r, i) => `<tr${i < 3 ? ' class="top"' : ''}><td>${['🥇', '🥈', '🥉'][i] || i + 1}</td><td><a href="https://www.qrz.com/db/${encodeURIComponent(r.call)}" target="_blank" rel="noopener">${esc(r.call)}</a></td><td><b>${r.pts}</b></td><td>${r.wpm}</td></tr>`).join('') + '</tbody></table>';
  }
  function draw() {
    const box = document.getElementById('wkBoard'); if (!box || !D) return;
    const W = D.weeks || {}, now = wk(0), last = wk(1);
    const cur = (W[now] || {})[show] || [], prev = (W[last] || {})[show] || [];
    const winner = prev[0];
    box.innerHTML = `<div class="cwb-head"><b>🏆 KPC LEADERBOARD</b><span class="cwb-tabs"><button type="button" class="cw-small" data-k="copy" aria-pressed="${show === 'copy'}">COPY CHALLENGE</button><button type="button" class="cw-small" data-k="gauntlet" aria-pressed="${show === 'gauntlet'}">GAUNTLET</button></span></div>` +
      `<p class="dim">This week (week ${now.slice(-2)}): scores sent in with SUBMIT MY SCORE. Updated about every 20 minutes.</p>` + table(cur, show) +
      (winner ? `<p class="dim" style="margin-top:8px">Last week's winner: <b>${esc(winner.call)}</b> with ${winner.pts} points.</p>` : '');
    box.querySelectorAll('[data-k]').forEach(b => b.onclick = () => { show = b.dataset.k; draw(); });
  }
  return { link, ready, draw, week: () => wk(0) };
})();

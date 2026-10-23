/* KPC QRM check (Opus, Oct 23 2026; Brandon: 'if someone was going to spot at 14.284 but someone was spotted 5 minutes
   ago at 14.286 give a warning … you may cause QRM, are you sure you want to spot here? Same for cw … ft8 and 4 is
   perfectly fine'). One rule for every place a station spots ITSELF (Spot Me page; the Logger has the same rule inline).
     KPCQrm.check(kHz, mode, myCall) -> Promise of '' (clear) or the warning text to put in a confirm()
   Room each side: SSB 3 kHz, AM 6, FM 10, CW / RTTY 1, PSK 0.5; FT8 / FT4 / FT2 / JS8 never warn (one shared sub-band by
   design). Spots up to 20 minutes old count. Reads POTA's spot list; if it can't, it says nothing. */
(function (G) {
  const ROOM = { SSB: 3, AM: 6, FM: 10, CW: 1, RTTY: 1, PSK31: 0.5, PSK: 0.5 };
  const base = c => { c = String(c || '').toUpperCase().trim(); const p = c.split('/').filter(Boolean); return p.length ? p.reduce((a, b) => (b.length > a.length ? b : a)) : ''; };
  const kh = f => { f = +f; return !isFinite(f) || f <= 0 ? null : f < 1000 ? f * 1000 : f; };
  const mhz = k => (k / 1000).toFixed(k % 1 ? 4 : 3).replace(/0+$/, '').replace(/\.$/, '');
  const ms = t => { const s = String(t || ''); const d = Date.parse(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + 'Z'); return isFinite(d) ? d : 0; };
  async function check(k, mode, me) {
    const m = String(mode || '').toUpperCase(), g = ROOM[/^(USB|LSB|PHONE)$/.test(m) ? 'SSB' : m];
    k = kh(k); if (!g || !k) return '';
    let L = [];
    try { const r = await fetch('https://api.pota.app/spot/activator', { cache: 'no-store' }); L = r.ok ? await r.json() : []; } catch (e) { return ''; }
    const now = Date.now(), mine = base(me);
    const near = (Array.isArray(L) ? L : []).map(x => Object.assign({}, x, { _k: kh(x.frequency), _t: ms(x.spotTime) }))
      .filter(x => x._k && base(x.activator) !== mine && Math.abs(x._k - k) <= g && now - x._t < 20 * 60000)
      .sort((a, b) => Math.abs(a._k - k) - Math.abs(b._k - k)).slice(0, 3);
    if (!near.length) return '';
    const ago = x => { const n = Math.max(0, Math.round((now - x._t) / 60000)); return n < 1 ? 'just now' : n === 1 ? '1 minute ago' : n + ' minutes ago'; };
    return '⚠ Possible QRM\n\n' + near.map(x => `${x.activator} was spotted on ${mhz(x._k)} ${ago(x)}` + (x.reference ? ` (${x.reference})` : '')).join('\n') +
      `.\n\nSpotting on ${mhz(k)} may put you on top of ${near.length > 1 ? 'them' : 'that station'}. Are you sure you want to spot here?`;
  }
  G.KPCQrm = { check, ROOM };
})(window);

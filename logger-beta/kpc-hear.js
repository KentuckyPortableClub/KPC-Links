/* KPC app: 👂 CAN I HEAR THEM? (Nov 18 2026; to-do 6; Brandon Nov 11). An alert only when a park you NEED is spotted AND this radio
   actually hears that station right now, so you are not chasing spots you cannot work. 'Need' = a park you have not worked today
   (or, switched to NEW PARKS ONLY: never worked). 'Hears' = proof from this radio, not from the internet:
     - your FT8 / FT4 decoder decoded that call in the last 3 minutes (with its report), or
     - your CW decoder copied that call in the last 3 minutes.
   One alert per station per band per 30 minutes; tap SPOTS to work it. Settings: alerts list (👂) + localStorage kpcAppHear. */
(function (G) {
  'use strict';
  const AP = G.KPCApp; if (!AP) return;
  const esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const S = Object.assign({ newOnly: false }, LS('kpcAppHear', {}));
  const save = () => { try { localStorage.setItem('kpcAppHear', JSON.stringify(S)); } catch (e) {} };
  const day = t => new Date(t).toISOString().slice(0, 10);
  function need(ref) {
    const L = G.KPCLog; if (!L) return true;
    if (S.newOnly) return !(L.hunted ? L.hunted(ref) : false);
    const today = day(Date.now());
    return ![...L.all().values()].some(q => !q.d && (q.refs || []).includes(ref) && day(q.t) === today);
  }
  const bandOf = k => (G.KPCLog && KPCLog.band(k)) || '';
  /* who this radio heard in the last 3 minutes: call → {db, how, band} */
  function heard() {
    const out = {}, cut = Date.now() - 180000;
    if (G.KPCDigi && KPCDigi.lines) {
      const dk = KPCDigi.dialKhz ? KPCDigi.dialKhz() : 0;
      KPCDigi.lines().forEach(x => { if (x.fr && x.t * 1000 >= cut && !/\.\.\./.test(x.fr)) out[x.fr] = { db: x.db, how: (KPCDigi.S && KPCDigi.S.mode) || 'FT8', band: bandOf(dk) }; });
    }
    if (G.KPCModes5 && KPCModes5.heardCalls) KPCModes5.heardCalls(cut).forEach(c => { if (!out[c.call]) out[c.call] = { db: null, how: 'CW', band: bandOf(c.khz || 0) }; });
    return out;
  }
  function check() {
    if (!G.KPCSpots || !AP.notify) return [];
    const H = heard(), hits = [];
    KPCSpots.all().forEach(s => {
      const h = H[s.call]; if (!h || !(s.refs || []).length) return;
      if (h.band && bandOf(s.khz) && h.band !== bandOf(s.khz)) return;
      const refs = s.refs.filter(need); if (!refs.length) return;
      hits.push({ s, h, refs });
      AP.notify('hear', `👂 ${s.call} (${refs.join(' + ')}) is spotted and YOUR radio hears it: ${(s.khz / 1000).toFixed(3)} ${s.mode || h.how}${h.db != null ? ', ' + (h.db > 0 ? '+' : '') + Math.round(h.db) + ' dB here' : ''}`, { key: s.call + '|' + bandOf(s.khz), every: 1800000, ref: refs[0] });
    });
    return hits;
  }
  AP.on('decoded', () => setTimeout(check, 200));
  setInterval(check, 30000);
  G.KPCHear = { S, save, check, heard, need };
})(window);

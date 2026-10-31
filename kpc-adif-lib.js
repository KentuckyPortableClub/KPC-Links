/* KPC ADIF library (Brandon Oct 31: 'checks the log and verifies the log is correct for qrz example N4KPC … a log checker
   for pota and qrz and then an adif editor'). Shared by the Club Room uploader (kpc-qrz-upload.js) and the ADIF Log
   Checker & Editor page (kpc-adif.html). Everything runs in the browser; nothing is sent anywhere.
   KPCAdif.parse(text) -> {header, recs:[{FIELD: value}]}   KPCAdif.write(header, recs) -> text   KPCAdif.record(r) -> one record
   KPCAdif.check(recs, {qrz:'N4KPC', pota:true}) -> [{i, field, level:'error'|'warn', msg, fix}]   KPCAdif.fix(recs, issue)
   Rule sheet: notes/logger-lounge-digi.md 'ADIF CHECKER RULES (Oct 31)'. */
(function () {
  'use strict';
  /* ADIF 3.1 bands (kHz) */
  const BANDS = [['2190m', 135.7, 137.8], ['630m', 472, 479], ['560m', 501, 504], ['160m', 1800, 2000], ['80m', 3500, 4000], ['60m', 5060, 5450], ['40m', 7000, 7300],
    ['30m', 10100, 10150], ['20m', 14000, 14350], ['17m', 18068, 18168], ['15m', 21000, 21450], ['12m', 24890, 24990], ['10m', 28000, 29700], ['8m', 40000, 45000],
    ['6m', 50000, 54000], ['5m', 54000.001, 69900], ['4m', 70000, 71000], ['2m', 144000, 148000], ['1.25m', 222000, 225000], ['70cm', 420000, 450000], ['33cm', 902000, 928000],
    ['23cm', 1240000, 1300000], ['13cm', 2300000, 2450000], ['9cm', 3300000, 3500000], ['6cm', 5650000, 5925000], ['3cm', 10000000, 10500000]];
  const MODES = 'AM ARDOP ATV CHIP CLO CONTESTI CW DIGITALVOICE DOMINO DSTAR DYNAMIC FAX FM FSK441 FT8 HELL ISCAT JT4 JT6M JT9 JT44 JT65 MFSK MSK144 MT63 OLIVIA OPERA PAC PAX PKT PSK PSK2K Q15 QRA64 ROS RTTY RTTYM SSB SSTV T10 THOR THRB TOR V4 VOI WINMOR WSPR'.split(' ');
  /* a submode typed as the mode -> the ADIF mode it belongs to */
  const SUB = { FT4: 'MFSK', JS8: 'MFSK', FST4: 'MFSK', FST4W: 'MFSK', Q65: 'MFSK', MFSK16: 'MFSK', FT2: 'MFSK', PSK31: 'PSK', PSK63: 'PSK', PSK125: 'PSK', BPSK31: 'PSK', QPSK31: 'PSK',
    USB: 'SSB', LSB: 'SSB', C4FM: 'DIGITALVOICE', DMR: 'DIGITALVOICE', FREEDV: 'DIGITALVOICE', M17: 'DIGITALVOICE', 'VARA HF': 'DYNAMIC', VARA: 'DYNAMIC', FMHELL: 'HELL', 'FELD HELL': 'HELL', OLIVIA8: 'OLIVIA' };
  const PARK = /^[A-Z0-9]{1,4}-\d{4,5}$/;
  const CALL = /^([A-Z0-9]{1,4}\/)?[A-Z0-9]{1,3}\d[A-Z0-9]{0,4}[A-Z](\/[A-Z0-9]{1,4})?$/;

  function parse(text) {
    text = String(text || '');
    const hm = /<eoh>/i.exec(text), header = hm ? text.slice(0, hm.index + hm[0].length) : '', body = hm ? text.slice(hm.index + hm[0].length) : text;
    const recs = []; let cur = {}, re = /<([a-z0-9_]+)(?::(\d+)(?::[a-z])?)?>/gi, m;
    while ((m = re.exec(body))) {
      const tag = m[1].toUpperCase();
      if (tag === 'EOR') { if (Object.keys(cur).length) recs.push(cur); cur = {}; continue; }
      if (m[2] == null) continue;
      cur[tag] = body.substr(re.lastIndex, +m[2]); re.lastIndex += +m[2];
    }
    if (Object.keys(cur).length) recs.push(cur);
    return { header, recs };
  }
  const len = v => String(v).length;   /* ADIF counts characters */
  function record(r) { return Object.keys(r).filter(k => r[k] !== '' && r[k] != null).map(k => '<' + k.toLowerCase() + ':' + len(r[k]) + '>' + r[k]).join(' ') + ' <eor>'; }
  function write(header, recs) {
    const h = header && /<eoh>/i.test(header) ? header : 'KPC ADIF Log Checker export <adif_ver:5>3.1.4 <programid:3>KPC <eoh>';
    return h + '\n\n' + recs.map(record).join('\n') + '\n';
  }
  function bandOf(mhz) { const k = +mhz * 1000; if (!isFinite(k) || !k) return ''; const b = BANDS.find(x => k >= x[1] && k <= x[2]); return b ? b[0] : ''; }
  function okDate(d) { if (!/^\d{8}$/.test(d || '')) return false; const y = +d.slice(0, 4), mo = +d.slice(4, 6), da = +d.slice(6); const t = new Date(Date.UTC(y, mo - 1, da)); return y >= 1930 && t.getUTCMonth() === mo - 1 && t.getUTCDate() === da && t.getTime() <= Date.now() + 864e5; }
  function okTime(t) { return /^([01]\d|2[0-3])[0-5]\d([0-5]\d)?$/.test(t || ''); }

  /* each issue: {i (record index), field, level, msg, fix: {kind, ...} or null} */
  function check(recs, o) {
    o = o || {}; const out = [], add = (i, field, level, msg, fix) => out.push({ i, field, level, msg, fix: fix || null });
    const station = String(o.qrz || '').toUpperCase();
    recs.forEach((r, i) => {
      const call = String(r.CALL || '').trim();
      if (!call) add(i, 'CALL', 'error', 'No call sign.');
      else if (call !== call.toUpperCase() || /\s/.test(call)) add(i, 'CALL', 'warn', 'Call sign "' + call + '" has lower case or spaces.', { kind: 'set', field: 'CALL', value: call.toUpperCase().replace(/\s+/g, '') });
      else if (!CALL.test(call)) add(i, 'CALL', 'warn', '"' + call + '" does not look like a call sign.');
      if (!r.QSO_DATE) add(i, 'QSO_DATE', 'error', 'No date (QSO_DATE).');
      else if (/^\d{4}-\d{2}-\d{2}$/.test(r.QSO_DATE)) add(i, 'QSO_DATE', 'error', 'Date "' + r.QSO_DATE + '" has dashes; ADIF wants YYYYMMDD.', { kind: 'set', field: 'QSO_DATE', value: r.QSO_DATE.replace(/-/g, '') });
      else if (!okDate(r.QSO_DATE)) add(i, 'QSO_DATE', 'error', 'Date "' + r.QSO_DATE + '" is not a real date (YYYYMMDD).');
      if (!r.TIME_ON) add(i, 'TIME_ON', 'error', 'No time (TIME_ON, UTC).');
      else if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(r.TIME_ON)) add(i, 'TIME_ON', 'error', 'Time "' + r.TIME_ON + '" has colons; ADIF wants HHMM.', { kind: 'set', field: 'TIME_ON', value: r.TIME_ON.split(':').map(x => x.padStart(2, '0')).join('') });
      else if (/^\d{3}$/.test(r.TIME_ON)) add(i, 'TIME_ON', 'error', 'Time "' + r.TIME_ON + '" is missing a leading zero.', { kind: 'set', field: 'TIME_ON', value: '0' + r.TIME_ON });
      else if (!okTime(r.TIME_ON)) add(i, 'TIME_ON', 'error', 'Time "' + r.TIME_ON + '" is not a real time (HHMM, UTC).');
      const fb = bandOf(r.FREQ), band = String(r.BAND || '').toLowerCase();
      if (!band && !r.FREQ) add(i, 'BAND', 'error', 'No band or frequency.');
      else if (!band && fb) add(i, 'BAND', 'warn', 'No band; the frequency says ' + fb + '.', { kind: 'set', field: 'BAND', value: fb });
      else if (band && !BANDS.some(b => b[0] === band)) add(i, 'BAND', 'error', 'Band "' + r.BAND + '" is not an ADIF band (like 20m, 40m, 2m).', fb ? { kind: 'set', field: 'BAND', value: fb } : null);
      else if (band && fb && fb !== band) add(i, 'BAND', 'error', 'Band ' + r.BAND + ' does not match the frequency ' + r.FREQ + ' MHz (' + fb + ').', { kind: 'set', field: 'BAND', value: fb });
      if (r.FREQ && !fb) add(i, 'FREQ', 'warn', 'Frequency "' + r.FREQ + '" is not inside a ham band (it must be in MHz, like 14.074).', +r.FREQ > 1000 && bandOf(+r.FREQ / 1000) ? { kind: 'set', field: 'FREQ', value: String(+r.FREQ / 1000) } : null);
      const mode = String(r.MODE || '').toUpperCase().trim();
      if (!mode) add(i, 'MODE', 'error', 'No mode.');
      else if (SUB[mode]) add(i, 'MODE', 'error', mode + ' must be sent as MODE ' + SUB[mode] + ' with SUBMODE ' + mode + ' (QRZ and POTA read it that way).', { kind: 'sub', mode: SUB[mode], sub: mode });
      else if (!MODES.includes(mode)) add(i, 'MODE', 'error', 'Mode "' + r.MODE + '" is not an ADIF mode.');
      else if (mode !== r.MODE) add(i, 'MODE', 'warn', 'Mode "' + r.MODE + '" should be capital letters.', { kind: 'set', field: 'MODE', value: mode });
      if (station) {
        const sc = String(r.STATION_CALLSIGN || '').toUpperCase().trim();
        if (!sc) add(i, 'STATION_CALLSIGN', 'warn', 'No STATION_CALLSIGN: QRZ will file it under ' + station + '.', { kind: 'set', field: 'STATION_CALLSIGN', value: station });
        else if (sc !== station) add(i, 'STATION_CALLSIGN', 'error', 'Station call is ' + sc + ', not ' + station + ': QRZ refuses it for the ' + station + ' logbook.', { kind: 'station', value: station, was: sc });
      }
      if (o.pota) {
        const sig = String(r.MY_SIG || '').toUpperCase(), info = String(r.MY_SIG_INFO || '').toUpperCase().trim();
        const parks = info.split(/[,\s]+/).filter(Boolean);
        if (!info && !r.MY_POTA_REF) add(i, 'MY_SIG_INFO', 'warn', 'No park (MY_SIG_INFO). POTA reads the park from the file name when you upload, so the file must be one park.');
        else if (info && parks.some(p => !PARK.test(p))) add(i, 'MY_SIG_INFO', 'error', 'Park "' + info + '" is not a park number like US-1234.', /^[A-Z]{1,2}\d{1,5}$/.test(info) ? null : null);
        if (info && sig && sig !== 'POTA' && sig !== 'WWFF' && sig !== 'SOTA') add(i, 'MY_SIG', 'warn', 'MY_SIG is "' + r.MY_SIG + '"; for a park it should be POTA.', { kind: 'set', field: 'MY_SIG', value: 'POTA' });
        if (info && !sig) add(i, 'MY_SIG', 'warn', 'MY_SIG is missing; set it to POTA.', { kind: 'set', field: 'MY_SIG', value: 'POTA' });
        if (!r.STATION_CALLSIGN && !r.OPERATOR) add(i, 'STATION_CALLSIGN', 'warn', 'No STATION_CALLSIGN or OPERATOR: POTA needs the activating call.');
        const hp = String(r.SIG_INFO || r.POTA_REF || '').toUpperCase().trim();
        if (hp && hp.split(/[,\s]+/).some(p => !PARK.test(p))) add(i, 'SIG_INFO', 'warn', 'Their park "' + hp + '" is not a park number like US-1234.');
      }
    });
    /* whole-file checks */
    const seen = {};
    recs.forEach((r, i) => { const k = [String(r.CALL || '').toUpperCase(), String(r.QSO_DATE || ''), String(r.BAND || bandOf(r.FREQ)).toLowerCase(), String(r.SUBMODE || r.MODE || '').toUpperCase(), String(r.MY_SIG_INFO || '').toUpperCase()].join('|');
      if (seen[k] != null) add(i, 'CALL', 'warn', 'Same call, day, band and mode as contact ' + (seen[k] + 1) + ' (a duplicate counts once).', { kind: 'delete' }); else seen[k] = i; });
    if (o.pota && recs.length) {
      const parks = [...new Set(recs.map(r => String(r.MY_SIG_INFO || '').toUpperCase().trim()).filter(Boolean))];
      const calls = [...new Set(recs.map(r => String(r.STATION_CALLSIGN || r.OPERATOR || '').toUpperCase().trim()).filter(Boolean))];
      if (parks.length > 1) add(-1, 'MY_SIG_INFO', 'warn', 'This file has ' + parks.length + ' parks (' + parks.slice(0, 4).join(', ') + '). POTA wants one park per upload: use SPLIT BY PARK.', { kind: 'split' });
      if (calls.length > 1) add(-1, 'STATION_CALLSIGN', 'warn', 'This file has ' + calls.length + ' station calls (' + calls.slice(0, 4).join(', ') + '). POTA wants one activating call per upload.');
      const days = {}; recs.forEach(r => { const d = String(r.QSO_DATE || ''); days[d] = (days[d] || 0) + 1; });
      Object.entries(days).forEach(([d, c]) => { if (d && c < 10) add(-1, 'QSO_DATE', 'warn', 'Only ' + c + ' contact' + (c > 1 ? 's' : '') + ' on ' + d + ' (UTC): POTA needs 10 in one UTC day for the activation to count (the contacts still count for the hunters).'); });
    }
    return out;
  }
  /* apply one issue's fix; returns true when something changed */
  function fix(recs, is) {
    const f = is && is.fix; if (!f) return false;
    if (f.kind === 'set') { recs[is.i][f.field] = f.value; return true; }
    if (f.kind === 'sub') { recs[is.i].MODE = f.mode; recs[is.i].SUBMODE = f.sub; return true; }
    if (f.kind === 'station') { const r = recs[is.i]; if (!r.OPERATOR && f.was) r.OPERATOR = f.was; r.STATION_CALLSIGN = f.value; return true; }
    if (f.kind === 'delete') { recs.splice(is.i, 1); return true; }
    return false;
  }
  /* apply every simple fix (never deletes, never splits); returns how many */
  function fixAll(recs, o) {
    let n = 0, guard = 0, list;
    do { list = check(recs, o).filter(x => x.i >= 0 && x.fix && x.fix.kind !== 'delete' && x.fix.kind !== 'split'); list.forEach(x => { if (fix(recs, x)) n++; }); } while (list.length && ++guard < 5);
    return n;
  }
  function byPark(recs) { const g = {}; recs.forEach(r => { const k = String(r.MY_SIG_INFO || '').toUpperCase().trim() || 'NO-PARK'; (g[k] = g[k] || []).push(r); }); return g; }
  window.KPCAdif = { parse, write, record, check, fix, fixAll, byPark, bandOf, BANDS: BANDS.map(b => b[0]), MODES, PARK };
})();

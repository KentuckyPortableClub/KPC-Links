/* KPC Club Room: N4KPC QRZ Log Uploader (Brandon Oct 31 2:10 PM: 'hide all that … label N4KPC QRZ Log Uploader … only thing
   that shows is place to upload a file … needs to work for anyone with access to that room').
   No key on this page at all: the N4KPC logbook key lives only in the KPC QRZ relay (Google Apps Script, Script Properties).
   The page reads the ADIF file in the browser and sends one contact a second to the relay with the Club Room's member token;
   the relay adds the key and hands back QRZ's answer. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('qrzUp')) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let recs = [], stop = false, busy = false, RELAY = null;
  const relay = () => RELAY || (RELAY = fetch('kpc-qrz-relay.json', { cache: 'no-store' }).then(r => r.ok ? r.json() : {})
    .then(j => (j && /^https:\/\/script\.google(usercontent)?\.com\//.test(j.url || '') ? j.url : '')).catch(() => ''));
  const member = () => { try { return localStorage.getItem('kpcMember') || ''; } catch (e) { return ''; } };
  const reasonOf = t => decodeURIComponent(((/REASON=([^&]*)/.exec(t) || [, ''])[1]).replace(/\+/g, ' ')).trim();
  function say(t, bad) { const m = $('quMsg'); m.textContent = t; m.className = 'qu-msg' + (bad ? ' bad' : ''); }

  /* ADIF: header ends at <eoh>; records end at <eor> (any case); each record keeps its own fields */
  function parse(text) {
    const body = /<eoh>/i.test(text) ? text.split(/<eoh>/i).slice(1).join('') : text;
    return body.split(/<eor>/i).map(r => r.trim()).filter(r => /<call:/i.test(r)).map(r => r + ' <eor>');
  }
  async function one(u, rec) {
    try {
      const r = await fetch(u, { method: 'POST', body: JSON.stringify({ club: 1, member: member(), adif: rec }) });
      const j = await r.json(), t = String(j.reply || '');
      if (/RESULT=(OK|REPLACE)/.test(t)) return 'ok';
      if (/duplicate/i.test(t)) return 'dup';
      return 'bad:' + (reasonOf(t) || 'QRZ did not take it');
    } catch (e) { return 'bad:could not reach the uploader'; }
  }
  async function send() {
    if (busy || !recs.length) return;
    const u = await relay();
    if (!u) { say('The N4KPC uploader is not switched on yet. Ask Brandon (KZ4CP).', true); return; }
    busy = true; stop = false; $('quSend').hidden = true; $('quStop').hidden = false; $('quFile').disabled = true;
    const c = { ok: 0, dup: 0, bad: 0 }, why = {};
    for (let i = 0; i < recs.length && !stop; i++) {
      const a = await one(u, recs[i]);
      if (a === 'ok') c.ok++; else if (a === 'dup') c.dup++; else { c.bad++; const w = a.slice(4); why[w] = (why[w] || 0) + 1; if (/not switched on|member password/.test(w)) stop = true; }
      $('quBar').style.width = Math.round((i + 1) / recs.length * 100) + '%';
      $('quProg').textContent = (i + 1) + ' of ' + recs.length;
      if (i < recs.length - 1 && !stop) await new Promise(res => setTimeout(res, 1000));   /* about one a second */
    }
    busy = false; $('quSend').hidden = false; $('quStop').hidden = true; $('quFile').disabled = false;
    const parts = [];
    if (c.ok) parts.push(c.ok + ' added'); if (c.dup) parts.push(c.dup + ' already there'); if (c.bad) parts.push(c.bad + ' not added');
    say((stop ? 'Stopped. ' : 'Done. ') + (parts.join(' · ') || 'Nothing sent.') + (Object.keys(why).length ? ' (' + Object.entries(why).map(([w, n]) => w + (n > 1 ? ' ×' + n : '')).join('; ') + ')' : ''), c.bad > 0);
  }
  $('quFile').addEventListener('change', () => {
    const f = $('quFile').files[0]; if (!f) return;
    const rd = new FileReader();
    rd.onload = () => { recs = parse(String(rd.result || '')); const n = recs.length; $('quBar').style.width = '0'; $('quProg').textContent = '';
      $('quGo').hidden = !n; say(n ? n + ' contact' + (n > 1 ? 's' : '') + ' found.' : 'No contacts found in that file. Pick an ADIF (.adi) log.', !n); };
    rd.readAsText(f);
  });
  $('quSend').addEventListener('click', send);
  $('quStop').addEventListener('click', () => { stop = true; });
  window.KPCQrzUp = { parse };
})();

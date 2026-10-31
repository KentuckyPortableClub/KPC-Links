/* KPC Club Room: "Upload your log to QRZ" (Brandon Oct 31 2:00 PM: 'upload ADIF to QRZ, a place to enter the key,
   make sure the key stays hidden'). The key lives ONLY in this browser (KPCQrz / localStorage kpcQrz, the same key the
   Logger uses): never in the page, a URL, the console or an error message; shown masked (last 4 only). The ADIF file is
   read in the browser; records go one at a time to QRZ through KPCQrz.send (the KPC relay when it is set up, else
   straight to QRZ, which then can only say 'sent'). */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const box = $('qrzUp'); if (!box) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const Q = () => window.KPCQrz;
  const mask = k => k ? '•••• ' + String(k).slice(-4) : '';
  let REM = true; try { REM = localStorage.getItem('kpcQrzRem') !== '0'; } catch (e) {}
  let recs = [], stop = false, busy = false;

  function keyLine() {
    const k = Q() && Q().get().key;
    $('quKeyNow').innerHTML = k ? 'Saved key: <b>' + esc(mask(k)) + '</b>' + (REM ? ' (on this device)' : ' (for this visit only)') : 'No key saved yet.';
    $('quForget').hidden = !k;
  }
  function saveKey() {
    const v = $('quKey').value.trim(); if (!v || !Q()) return;
    Q().set({ key: v }); $('quKey').value = ''; $('quKey').type = 'password'; $('quEye').textContent = '👁 SHOW';
    keyLine(); say('Key saved. It stays on this device.');
  }
  function say(t, bad) { const m = $('quMsg'); m.textContent = t; m.className = 'qu-msg' + (bad ? ' bad' : ''); }

  /* ADIF: header ends at <eoh>; records end at <eor>; each record keeps its own fields */
  function parse(text) {
    const body = /<eoh>/i.test(text) ? text.split(/<eoh>/i).slice(1).join('') : text;
    return body.split(/<eor>/i).map(r => r.trim()).filter(r => /<call:/i.test(r)).map(r => {
      const f = {}, re = /<([a-z0-9_]+):(\d+)(?::[a-z])?>/gi; let m;
      while ((m = re.exec(r))) { f[m[1].toUpperCase()] = r.substr(re.lastIndex, +m[2]); re.lastIndex += +m[2]; }
      return { raw: r + ' <eor>', f };
    });
  }
  function preview() {
    const n = recs.length;
    $('quCount').textContent = n ? n + ' contact' + (n > 1 ? 's' : '') + ' in this file.' : 'No contacts found in this file.';
    $('quPrev').innerHTML = n ? '<table><tr><th>CALL</th><th>DATE</th><th>BAND</th><th>MODE</th></tr>' + recs.slice(0, 5).map(r => {
      const d = r.f.QSO_DATE || ''; return '<tr><td>' + esc(r.f.CALL || '') + '</td><td>' + esc(d.length === 8 ? d.slice(0, 4) + '-' + d.slice(4, 6) + '-' + d.slice(6) : d) + '</td><td>' + esc(r.f.BAND || r.f.FREQ || '') + '</td><td>' + esc(r.f.SUBMODE || r.f.MODE || '') + '</td></tr>'; }).join('') + '</table>' + (n > 5 ? '<p class="qu-small">…and ' + (n - 5) + ' more.</p>' : '') : '';
    $('quSend').disabled = !n;
  }
  async function send() {
    if (busy || !recs.length) return;
    if (!Q() || !Q().get().key) { say('Save your QRZ logbook key first.', true); return; }
    busy = true; stop = false; $('quSend').hidden = true; $('quStop').hidden = false;
    const c = { ok: 0, dup: 0, bad: 0, sent: 0 }, why = {};
    for (let i = 0; i < recs.length && !stop; i++) {
      let r; try { r = await Q().send(recs[i].raw); } catch (e) { r = { ok: false, sure: true, msg: 'Could not reach QRZ.' }; }
      if (r.sure === false || (r.ok && !r.sure)) c.sent++;
      else if (r.ok && /already/i.test(r.msg || '')) c.dup++;
      else if (r.ok) c.ok++;
      else { c.bad++; const w = String(r.msg || 'failed').replace(/^QRZ said:\s*/i, '').replace(/[A-Za-z0-9]{20,}/g, '…'); why[w] = (why[w] || 0) + 1; }   /* never echo anything key-like */
      $('quBar').style.width = Math.round((i + 1) / recs.length * 100) + '%';
      $('quProg').textContent = (i + 1) + ' of ' + recs.length;
      if (i < recs.length - 1 && !stop) await new Promise(res => setTimeout(res, 1000));   /* about one a second */
    }
    busy = false; $('quSend').hidden = false; $('quStop').hidden = true;
    const parts = [];
    if (c.ok) parts.push(c.ok + ' saved'); if (c.dup) parts.push(c.dup + ' already in your logbook'); if (c.bad) parts.push(c.bad + ' failed');
    if (c.sent) parts.push(c.sent + ' sent (check your QRZ logbook: a web page can\'t see QRZ\'s answer without the KPC relay)');
    say((stop ? 'Stopped. ' : 'Done. ') + (parts.join(' · ') || 'Nothing sent.') + (Object.keys(why).length ? ' QRZ said: ' + Object.entries(why).map(([w, n]) => w + (n > 1 ? ' (' + n + ')' : '')).join('; ') : ''), c.bad > 0);
  }

  $('quEye').addEventListener('click', () => { const i = $('quKey'); i.type = i.type === 'password' ? 'text' : 'password'; $('quEye').textContent = i.type === 'password' ? '👁 SHOW' : '🙈 HIDE'; });
  $('quSave').addEventListener('click', saveKey);
  $('quKey').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); saveKey(); } });
  $('quRem').checked = REM;
  $('quRem').addEventListener('change', () => { REM = $('quRem').checked; try { localStorage.setItem('kpcQrzRem', REM ? '1' : '0'); } catch (e) {} keyLine(); });
  $('quForget').addEventListener('click', () => { if (Q()) Q().set({ key: '' }); keyLine(); say('Key removed from this device.'); });
  $('quTest').addEventListener('click', async () => { if (!Q() || !Q().get().key) { say('Save your QRZ logbook key first.', true); return; } say('Checking the key…'); const r = await Q().test(); say(r.msg, r.ok === false); });
  $('quFile').addEventListener('change', () => { const f = $('quFile').files[0]; if (!f) return; const rd = new FileReader(); rd.onload = () => { recs = parse(String(rd.result || '')); preview(); say(''); $('quBar').style.width = '0'; $('quProg').textContent = ''; }; rd.readAsText(f); });
  $('quSend').addEventListener('click', send);
  $('quStop').addEventListener('click', () => { stop = true; });
  /* 'Remember' off = the key is wiped when this page closes */
  window.addEventListener('pagehide', () => { if (!REM && Q()) Q().set({ key: '' }); });
  window.KPCQrzUp = { parse };
  keyLine();
})();

/* KPC QRZ relay (Brandon Oct 17: 'qrz did not push to qrz').
   QRZ's logbook server answers web pages but does not let them READ the answer (no CORS header, checked Oct 17),
   so the Hunters Lounge can't tell whether QRZ took a contact. This tiny Google Apps Script passes the contact to QRZ
   and hands QRZ's real answer back to the page.

   It only ever talks to logbook.qrz.com. Nothing is saved or logged: the QRZ key passes through and is forgotten.

   SET UP (once, in the kpcwebhost Google account, about 3 minutes):
     1. script.google.com → New project → name it "KPC QRZ relay" → paste this whole file over the sample code → Save.
     2. Deploy → New deployment → gear ⚙ → Web app.
          Description: KPC QRZ relay · Execute as: Me · Who has access: Anyone → Deploy → Authorize (allow).
     3. Copy the Web app URL (it ends in /exec) and send it to Claude (it is not a secret: it can only forward to QRZ).
        Claude puts it in kpc-qrz-relay.json on the site.
   CLUB MODE (N4KPC QRZ Log Uploader in the Club Room): also add the two Script Properties described above clubInsert().
   If you change this code later: Deploy → Manage deployments → ✏ edit → Version: New version → Deploy (the URL stays). */
/* Oct 31 (Brandon: 'N4KPC QRZ Log Uploader … needs to work for anyone with access to that room'): CLUB MODE.
   The N4KPC logbook key is stored ONLY here, in this script's Script Properties (never on the website):
     Project Settings (gear) → Script Properties → Add property:
       N4KPC_QRZ_KEY = the N4KPC QRZ logbook API key
       MEMBER_HASH   = ed00a12021b4460be189b4120e93d5f740408d2f769e108d332dcc4aa528ca61   (the Club Room lock's token)
   A Club Room page sends {club: 1, member: <the member token in that browser>, adif: one contact}; the key is added here.
   At most 1,500 contacts an hour go through (stops a runaway page or a stranger who copied the token). */
function clubInsert(d, out) {
  var P = PropertiesService.getScriptProperties(), key = P.getProperty('N4KPC_QRZ_KEY'), mh = P.getProperty('MEMBER_HASH');
  if (!key || !mh) return out({ ok: false, reply: 'RESULT=FAIL&REASON=the club uploader is not switched on yet' });
  if (String(d.member || '') !== mh) return out({ ok: false, reply: 'RESULT=FAIL&REASON=open the Club Room with the member password first' });
  var adif = String(d.adif || ''); if (!/<call:/i.test(adif) || adif.length > 6000) return out({ ok: false, reply: 'RESULT=FAIL&REASON=that is not one ADIF contact' });
  var C = CacheService.getScriptCache(), hr = 'n4kpc-' + new Date().toISOString().slice(0, 13), n = +(C.get(hr) || 0);
  if (n >= 1500) return out({ ok: false, reply: 'RESULT=FAIL&REASON=too many uploads this hour, try again later' });
  C.put(hr, String(n + 1), 3700);
  var r = UrlFetchApp.fetch('https://logbook.qrz.com/api', { method: 'post', payload: { KEY: key, ACTION: 'INSERT', ADIF: adif }, muteHttpExceptions: true, headers: { 'User-Agent': 'KPCClubUploader/1.0 (kentuckyportableclub.github.io)' } });
  return out({ ok: true, code: r.getResponseCode(), reply: String(r.getContentText()).replace(key, '…').slice(0, 2000) });
}
function doPost(e) {
  var out = function (o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); };
  try {
    var d = JSON.parse(e.postData.contents || '{}');
    if (d.club) return clubInsert(d, out);
    var action = String(d.action || 'INSERT').toUpperCase();
    if (['INSERT', 'STATUS'].indexOf(action) < 0) return out({ ok: false, reply: 'RESULT=FAIL&REASON=action not allowed' });
    if (!/^[A-Z0-9-]{8,40}$/i.test(String(d.key || ''))) return out({ ok: false, reply: 'RESULT=FAIL&REASON=that is not a QRZ logbook key' });
    var adif = String(d.adif || ''); if (adif.length > 6000) return out({ ok: false, reply: 'RESULT=FAIL&REASON=contact too long' });
    var p = { KEY: String(d.key), ACTION: action }; if (action === 'INSERT') p.ADIF = adif;
    var r = UrlFetchApp.fetch('https://logbook.qrz.com/api', { method: 'post', payload: p, muteHttpExceptions: true, headers: { 'User-Agent': 'KPCHuntersLounge/1.0 (kentuckyportableclub.github.io)' } });
    return out({ ok: true, code: r.getResponseCode(), reply: String(r.getContentText()).slice(0, 2000) });
  } catch (err) {
    return out({ ok: false, reply: 'RESULT=FAIL&REASON=' + String(err).slice(0, 200) });
  }
}
function doGet() { return ContentService.createTextOutput('KPC QRZ relay is running.'); }

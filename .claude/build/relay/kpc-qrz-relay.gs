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
   If you change this code later: Deploy → Manage deployments → ✏ edit → Version: New version → Deploy (the URL stays). */
function doPost(e) {
  var out = function (o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); };
  try {
    var d = JSON.parse(e.postData.contents || '{}');
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

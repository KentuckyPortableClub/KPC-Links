/* KPC mailer: runs in the campout Gmail (kypotacampout@gmail.com) as an Apps Script web app.
   The website's Discord relay (GitHub Actions) sends it the post; it emails Groups.io and the
   email-updates list from the campout Gmail. Used because App Passwords aren't offered on that account.
   Setup: Project Settings -> Script properties -> add MAIL_KEY = the same secret phrase saved in GitHub as RELAY_MAIL_KEY.
   Deploy -> New deployment -> Web app, Execute as: Me, Who has access: Anyone. The /exec link goes in GitHub as RELAY_MAIL_URL. */
function doPost(e) {
  var out = function (o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); };
  try {
    var d = JSON.parse(e.postData.contents);
    var key = PropertiesService.getScriptProperties().getProperty('MAIL_KEY');
    if (!key || d.key !== key) return out({ ok: false, error: 'wrong key' });
    var files = (d.images || []).map(function (im) { return Utilities.newBlob(Utilities.base64Decode(im.b64), 'image/jpeg', im.name); });
    var opts = { name: 'Kentucky Portable Club', attachments: files };
    if (d.bcc && d.bcc.length) opts.bcc = d.bcc.join(',');
    GmailApp.sendEmail(d.to || Session.getActiveUser().getEmail(), String(d.subject || 'KPC update').slice(0, 200), String(d.body || ''), opts);
    return out({ ok: true, left: MailApp.getRemainingDailyQuota() });
  } catch (err) {
    return out({ ok: false, error: String(err) });
  }
}
/* Run this once from the editor (▶ Run) to give the script permission to send mail. */
function testSend() {
  GmailApp.sendEmail(Session.getActiveUser().getEmail(), 'KPC mailer test', 'If you got this, the KPC mailer can send email.');
}

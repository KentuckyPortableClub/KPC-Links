/* KPC Mailer + Watcher. Runs in kpcwebhost@gmail.com as an Apps Script project.

   1) MAILER (doPost): the website's Discord relay (GitHub Actions) sends it a post; it emails Groups.io and the
      email-updates list from this Gmail.
   2) WATCHER (kpcWatch, runs every minute): looks at the private Discord channel. When a post is added, edited,
      deleted or pinned, or a scheduled post's time comes, it starts the relay on GitHub right away, so posts go out
      in about 1-2 minutes instead of waiting for GitHub's 15-minute timer.

   Script properties (Project Settings -> Script properties). Never paste these into a chat:
     MAIL_KEY          the same secret phrase saved in GitHub as RELAY_MAIL_KEY
     DISCORD_BOT_TOKEN the bot's token (same as the GitHub secret DISCORD_BOT_TOKEN)
     DISCORD_CHANNEL   the channel ID (same as the GitHub secret KPC_RELAY_CHANNEL)
     GH_TOKEN          a GitHub fine-grained token: only the KPC-Links repository, permission "Actions: Read and write"
   Setup: Deploy -> New deployment -> Web app, Execute as: Me, Who has access: Anyone (the /exec link = GitHub secret
   RELAY_MAIL_URL). Then pick startWatcher in the function list and press Run once (it makes the 1-minute timer).
   After pasting a NEW version of this code: Deploy -> Manage deployments -> pencil -> Version: New version -> Deploy. */

var REPO = 'KentuckyPortableClub/KPC-Links';
var WORKFLOW = 'kpc-discord-relay.yml';

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

/* Run this once to start the 1-minute watcher (running it again replaces the old timer). */
function startWatcher() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'kpcWatch') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('kpcWatch').timeBased().everyMinutes(1).create();
  kpcWatch(true);
}
function stopWatcher() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'kpcWatch') ScriptApp.deleteTrigger(t); });
}

function kpcWatch(verbose) {
  var P = PropertiesService.getScriptProperties();
  var bot = P.getProperty('DISCORD_BOT_TOKEN'), chan = P.getProperty('DISCORD_CHANNEL'), gh = P.getProperty('GH_TOKEN');
  if (!bot || !chan || !gh) { if (verbose === true) throw new Error('Add DISCORD_BOT_TOKEN, DISCORD_CHANNEL and GH_TOKEN in Script properties first.'); return; }
  var now = Date.now();

  // What the channel looks like now: ids + edit times, and the pinned posts.
  var r = UrlFetchApp.fetch('https://discord.com/api/v10/channels/' + chan + '/messages?limit=100',
    { headers: { Authorization: 'Bot ' + bot }, muteHttpExceptions: true });
  if (r.getResponseCode() !== 200) { if (verbose === true) throw new Error('Discord said ' + r.getResponseCode() + ': ' + r.getContentText().slice(0, 200)); return; }
  var sig = JSON.parse(r.getContentText()).filter(function (m) { return !(m.author && m.author.bot); })
    .map(function (m) { return m.id + ':' + (m.edited_timestamp || '') + ':' + ((m.attachments || []).length) + ':' + (m.pinned ? 1 : 0); }).join(',');
  sig = Utilities.base64Encode(Utilities.computeDigest(Utilities.DigestAlgorithm.MD5, sig));
  var changed = sig !== P.getProperty('SIG');

  // A scheduled post coming due? (the relay writes its next time into kpc-relay-state.json; checked every 5 minutes)
  var due = P.getProperty('DUE') || '';
  if (now - Number(P.getProperty('DUE_AT') || 0) > 5 * 60000) {
    try {
      var s = UrlFetchApp.fetch('https://raw.githubusercontent.com/' + REPO + '/main/kpc-relay-state.json?t=' + now, { muteHttpExceptions: true });
      if (s.getResponseCode() === 200) due = JSON.parse(s.getContentText()).due || '';
    } catch (e) {}
    P.setProperties({ DUE: due, DUE_AT: String(now) });
  }
  var dueNow = due && new Date(due).getTime() <= now && P.getProperty('DUE_FIRED') !== due;

  if (!changed && !dueNow) { if (verbose === true) Logger.log('Nothing new. Watcher is running.'); return; }
  if (now - Number(P.getProperty('LAST_RUN') || 0) < 50000) return;   // at most one start per minute

  var g = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + '/actions/workflows/' + WORKFLOW + '/dispatches', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + gh, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' },
    payload: JSON.stringify({ ref: 'main', inputs: { dry_run: 'false' } })
  });
  if (g.getResponseCode() === 204) {
    var set = { SIG: sig, LAST_RUN: String(now) };
    if (dueNow) { set.DUE_FIRED = due; set.DUE_AT = '0'; }
    P.setProperties(set);
    if (verbose === true) Logger.log('Started the relay on GitHub.');
  } else if (verbose === true) {
    throw new Error('GitHub said ' + g.getResponseCode() + ': ' + g.getContentText().slice(0, 300) + ' (check GH_TOKEN: KPC-Links only, Actions: Read and write)');
  }
}

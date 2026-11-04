/* KPC Mailer + Watcher. Runs in kpcwebhost@gmail.com as an Apps Script project.

   1) MAILER (doPost): the website's Discord relay (GitHub Actions) sends it a post; it emails Groups.io and the
      email-updates list from this Gmail.
   2) WATCHER (kpcWatch, runs every 5 minutes): starts the relay on GitHub, so posts go out within about 30 minutes (Nov 4 fix bundle; was about 10)
      instead of waiting for GitHub's own 15-minute timer (which often runs late). PR3 (Nov 2): it starts the relay only
      when the newest relay run is 8+ minutes old (28+ at night), about 115 starts a day instead of ~280. It does NOT read Discord itself:
      Discord blocks Google's servers (error 40333 "internal network error", found Oct 15), so GitHub does the reading.

   Script properties (Project Settings -> Script properties). Never paste these into a chat:
     MAIL_KEY          the same secret phrase saved in GitHub as RELAY_MAIL_KEY
     (DISCORD_BOT_TOKEN / DISCORD_CHANNEL are no longer used here; you can delete them.)
     GH_TOKEN          a GitHub fine-grained token: only the KPC-Links repository, permission "Actions: Read and write"
   Setup: Deploy -> New deployment -> Web app, Execute as: Me, Who has access: Anyone (the /exec link = GitHub secret
   RELAY_MAIL_URL). Then pick startWatcher in the function list and press Run once (it makes the 5-minute timer).
   After pasting a NEW version of this code: Deploy -> Manage deployments -> pencil -> Version: New version -> Deploy. */

var REPO = 'KentuckyPortableClub/KPC-Links';
var WORKFLOW = 'kpc-discord-relay.yml';
var MIN_GAP_MIN = 28;    // Nov 4 fix bundle (item 12): every ~30 min, was 8 (PR3: start the relay only when its newest run is at least this old, daytime). Takes effect only when this code is pasted into the Apps Script and deployed again
var QUIET_GAP_MIN = 28;  // PR3: the same at night, 11 PM-6 AM Central (no email goes out then anyway)

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

/* Run this once to start the 5-minute watcher (running it again replaces the old timer). */
function startWatcher() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'kpcWatch') ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('kpcWatch').timeBased().everyMinutes(5).create();
  kpcWatch(true);
}
function stopWatcher() {
  ScriptApp.getProjectTriggers().forEach(function (t) { if (t.getHandlerFunction() === 'kpcWatch') ScriptApp.deleteTrigger(t); });
}

function kpcWatch(verbose) {
  var gh = PropertiesService.getScriptProperties().getProperty('GH_TOKEN');
  if (!gh) { if (verbose === true) throw new Error('Add GH_TOKEN in Script properties first.'); return; }
  var H = { Authorization: 'Bearer ' + gh, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' };
  var base = 'https://api.github.com/repos/' + REPO + '/actions/workflows/' + WORKFLOW;
  // Skip if a relay run is already waiting or running (no pile-up).
  var r = UrlFetchApp.fetch(base + '/runs?per_page=1', { headers: H, muteHttpExceptions: true });
  if (r.getResponseCode() === 200) {
    var run = (JSON.parse(r.getContentText()).workflow_runs || [])[0];
    if (run && run.status !== 'completed') { if (verbose === true) Logger.log('A relay run is already going. Watcher is running.'); return; }
    // PR3 (Nov 2, fewer runs): this watcher cannot ask Discord whether anything is new (Discord blocks Google's servers), so it
    // starts the relay less often instead: only when the newest relay run is MIN_GAP_MIN old (QUIET_GAP_MIN at night, 11 PM-6 AM
    // Central). The relay itself then looks in a few seconds and ends at once when nothing is new. Was: every 5 minutes (~280/day).
    if (run && verbose !== true) {
      var ageMin = (Date.now() - new Date(run.created_at).getTime()) / 60000;
      var hour = Number(Utilities.formatDate(new Date(), 'America/Chicago', 'H'));
      var gap = (hour >= 23 || hour < 6) ? QUIET_GAP_MIN : MIN_GAP_MIN;
      if (ageMin < gap) return;
    }
  }
  var g = UrlFetchApp.fetch(base + '/dispatches', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true, headers: H,
    payload: JSON.stringify({ ref: 'main', inputs: { dry_run: 'false' } })
  });
  if (g.getResponseCode() === 204) { if (verbose === true) Logger.log('Started the relay on GitHub. It will now start every 5 minutes.'); }
  else if (verbose === true) {
    throw new Error('GitHub said ' + g.getResponseCode() + ': ' + g.getContentText().slice(0, 300) + ' (check GH_TOKEN: KPC-Links only, Actions: Read and write)');
  }
}

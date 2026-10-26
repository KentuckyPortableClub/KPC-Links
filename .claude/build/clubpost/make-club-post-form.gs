// KPC CLUB POST FORM. Paste into an EMPTY Code.gs, Save, pick makeClubPostForm, Run ONCE.
// The Execution log then shows the FORM, EDIT and SHEET links. Then do the three short steps at the bottom of
// this file (Brandon Oct 25: "a Google Form that feeds the SAME Discord relay").
//
// HOW IT WORKS
//  1. Someone fills in the form: kind, where it goes (checkboxes), the message, optional pictures/files,
//     optional date + time (blank = send now).
//  2. If the signed-in Google email is a FOUNDER (list below), the post goes out by itself.
//     Anyone else waits: a club officer opens the response sheet and picks YES in the Approved column.
//  3. "Going out" = the script posts the same kind of tagged message you would type in the private Discord
//     channel ("Post Nov 4 2026 8:00 AM + Facebook + Website: ...") through that channel's webhook. The relay
//     (kpc_discord_relay.py, every 15 min) then does everything it already does: website, Facebook, other
//     Discord server, Groups.io, subscribers, Events calendar, scheduling. Same email rules: email goes out
//     ONLY when Groups.io / Email subscribers is ticked. Nobody's name is ever shown.
//  4. The sheet keeps a Status column (Sent, Waiting for approval, Declined, Problem: ...). No emails from here.

var FOUNDERS = [
  'brandonwhite42166@gmail.com'
  // add the other founders' Google emails here, one per line in quotes, with a comma after each but the last
];

var PLACES = ['Website', 'Facebook', 'Discord', 'Groups.io', 'Email subscribers', 'Events calendar'];
var KINDS = ['Post (news, general)', 'Campout post', 'Event for the calendar'];
var MAX_TEXT = 1600;          // Discord allows 2000 letters in all; the tag takes some
var MAX_FILE = 8 * 1024 * 1024;
var TZNAME = 'America/Chicago';

function makeClubPostForm() {
  var form = FormApp.create('KPC Club Post');
  form.setDescription('Post to the Kentucky Portable Club website, Facebook, Discord and email. Founders\' posts go out by themselves. Everyone else\'s are checked by a club officer first. Only the message is shown, never your name.');
  form.setCollectEmail(true);
  form.setProgressBar(false);

  var kind = form.addMultipleChoiceItem();
  kind.setTitle('What kind of post is it?');
  kind.setChoiceValues(KINDS);
  kind.setRequired(true);

  var where = form.addCheckboxItem();
  where.setTitle('Where should it go?');
  where.setHelpText('Email only goes out when you tick Groups.io or Email subscribers. Website also shows it on the other Discord server.');
  where.setChoiceValues(PLACES);
  where.setRequired(true);

  var msg = form.addParagraphTextItem();
  msg.setTitle('Message');
  msg.setHelpText('Write it the way it should read. For an Event, put the event date, time and place in the message too (like "Sat Nov 14, 9 AM, Taylorsville Lake").');
  msg.setRequired(true);
  var v = FormApp.createParagraphTextValidation();
  v = v.requireTextLengthLessThanOrEqualTo(MAX_TEXT);
  v = v.setHelpText('Please keep it under ' + MAX_TEXT + ' letters.');
  msg.setValidation(v.build());

  var d = form.addDateItem();
  d.setTitle('Send on (date)');
  d.setHelpText('Leave the date and time blank to send right away. Times are Central.');
  var t = form.addTimeItem();
  t.setTitle('Send at (time)');
  t.setHelpText('Date but no time = 8:00 AM.');

  form.setConfirmationMessage('Thanks! Founders\' posts go out within about 15 minutes. Others wait for a club officer to approve them. 73!');

  var ss = SpreadsheetApp.create('KPC Club Post (responses)');
  ss.setSpreadsheetTimeZone(TZNAME);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
  Utilities.sleep(3000);
  var sh = formSheet_(ss);
  var col = sh.getLastColumn() + 1;
  sh.getRange(1, col).setValue('Approved');
  sh.getRange(1, col + 1).setValue('Status');
  sh.getRange(1, col, 1, 2).setFontWeight('bold');
  approvedDropdown(sh, col);

  var props = PropertiesService.getScriptProperties();
  props.setProperty('FORM_ID', form.getId());
  props.setProperty('SHEET_ID', ss.getId());
  ScriptApp.newTrigger('onClubPostSubmit').forSpreadsheet(ss).onFormSubmit().create();
  ScriptApp.newTrigger('onClubPostEdit').forSpreadsheet(ss).onEdit().create();

  Logger.log('FORM (share this): ' + form.getPublishedUrl());
  Logger.log('EDIT: ' + form.getEditUrl());
  Logger.log('SHEET: ' + ss.getUrl());
  Logger.log('NEXT: (1) open EDIT and add a "File upload" question named exactly:  Pictures or files  (Apps Script cannot add that one). (2) In the form, Settings > Responses > Collect email addresses must say Verified. (3) Project Settings > Script properties > add RELAY_WEBHOOK = the webhook link of the private relay channel.');
}

function formSheet_(ss) {
  var sheets = ss.getSheets();
  var sh = sheets[0];
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getFormUrl()) { sh = sheets[i]; }
  }
  return sh;
}

// YES / NO drop-down on the Approved column (rows 2 to 2000). House rule.
function approvedDropdown(sh, col) {
  var rule = SpreadsheetApp.newDataValidation();
  rule = rule.requireValueInList(['YES', 'NO'], true);
  rule = rule.setAllowInvalid(false);
  sh.getRange(2, col, 1999, 1).setDataValidation(rule.build());
}

// ---------------------------------------------------------------- the tag the relay reads
// Pure text work (no Google calls), so it can be tested anywhere.
// kind: one of KINDS. places: array from PLACES. when: '' or 'Nov 4 2026 8:00 AM'.
function buildTag(kind, places, when) {
  var parts = [];
  if (when) { parts.push('Post ' + when); }
  var words = [];
  var isEvent = (String(kind).indexOf('Event') === 0) || places.indexOf('Events calendar') >= 0;
  var chosen = [];
  var map = { 'Website': 'Website', 'Facebook': 'Facebook', 'Discord': 'Discord', 'Groups.io': 'Groups.io', 'Email subscribers': 'Subscribers' };
  for (var i = 0; i < PLACES.length; i++) {
    if (places.indexOf(PLACES[i]) >= 0 && map[PLACES[i]]) { chosen.push(map[PLACES[i]]); }
  }
  if (chosen.length === 5) { words.push('All'); } else { words = chosen; }
  if (String(kind).indexOf('Campout') === 0) { parts.push('Campout'); }
  if (isEvent) { parts.push('Event'); }
  if (words.length) { parts.push(words.join(' + ')); }
  if (!parts.length) { parts.push('Website'); }
  return parts.join(' + ');
}

// "Nov 4 2026" and "8:00 AM" from the sheet cells (Date objects) -> 'Nov 4 2026 8:00 AM', or '' when no date.
function whenText_(dateCell, timeCell, tz) {
  if (!(dateCell instanceof Date)) { return ''; }
  var s = Utilities.formatDate(dateCell, tz, 'MMM d yyyy');
  if (timeCell instanceof Date) { s += ' ' + Utilities.formatDate(timeCell, tz, 'h:mm a'); } else { s += ' 8:00 AM'; }
  return s;
}

// ---------------------------------------------------------------- triggers
function onClubPostSubmit(e) {
  var sh = e.range.getSheet();
  var row = e.range.getRow();
  var cols = headerMap_(sh);
  var email = String(sh.getRange(row, cols['Email Address'] || 2).getValue()).toLowerCase().trim();
  var ok = false;
  for (var i = 0; i < FOUNDERS.length; i++) {
    if (FOUNDERS[i].toLowerCase() === email && email) { ok = true; }
  }
  if (ok) {
    sh.getRange(row, cols['Approved']).setValue('YES');
    sendRow_(sh, row, cols);
  } else {
    setStatus_(sh, row, cols, 'Waiting for approval');
  }
}

function onClubPostEdit(e) {
  var sh = e.range.getSheet();
  var cols = headerMap_(sh);
  if (!cols['Approved'] || e.range.getColumn() !== cols['Approved'] || e.range.getRow() < 2) { return; }
  var row = e.range.getRow();
  var v = String(e.range.getValue()).toUpperCase().trim();
  var status = String(sh.getRange(row, cols['Status']).getValue());
  if (v === 'YES' && status.indexOf('Sent') !== 0) { sendRow_(sh, row, cols); }
  if (v === 'NO' && status.indexOf('Sent') !== 0) { setStatus_(sh, row, cols, 'Declined'); }
}

function headerMap_(sh) {
  var head = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  var m = {};
  for (var c = 0; c < head.length; c++) { m[String(head[c]).trim()] = c + 1; }
  return m;
}

function setStatus_(sh, row, cols, text) {
  sh.getRange(row, cols['Status']).setValue(text);
}

function sendRow_(sh, row, cols) {
  var tz = sh.getParent().getSpreadsheetTimeZone() || TZNAME;
  var hook = PropertiesService.getScriptProperties().getProperty('RELAY_WEBHOOK');
  if (!hook) { setStatus_(sh, row, cols, 'Problem: no RELAY_WEBHOOK script property yet'); return; }
  var get = function (name) { return cols[name] ? sh.getRange(row, cols[name]).getValue() : ''; };
  var places = String(get('Where should it go?')).split(/\s*,\s*/);
  var text = String(get('Message')).replace(/@(everyone|here)/g, '').replace(/^\s+|\s+$/g, '');
  var tag = buildTag(String(get('What kind of post is it?')), places, whenText_(get('Send on (date)'), get('Send at (time)'), tz));
  var content = tag + ': ' + text;
  if (content.length > 1990) { setStatus_(sh, row, cols, 'Problem: message too long'); return; }

  var payload = { payload_json: JSON.stringify({ username: 'KPC Club Post Form', content: content, allowed_mentions: { parse: [] } }) };
  var skipped = 0;
  var n = 0;
  var urls = String(get('Pictures or files')).match(/[-\w]{25,}/g) || [];
  for (var i = 0; i < urls.length && n < 10; i++) {
    try {
      var f = DriveApp.getFileById(urls[i]);
      if (f.getSize() > MAX_FILE) { skipped++; continue; }
      payload['files[' + n + ']'] = f.getBlob();
      n++;
    } catch (err) { skipped++; }
  }
  var r = UrlFetchApp.fetch(hook + (hook.indexOf('?') < 0 ? '?wait=true' : '&wait=true'), { method: 'post', payload: payload, muteHttpExceptions: true });
  var code = r.getResponseCode();
  if (code === 200 || code === 204) {
    setStatus_(sh, row, cols, 'Sent ' + Utilities.formatDate(new Date(), tz, 'MMM d h:mm a') + (skipped ? ' (' + skipped + ' file(s) skipped: too big or not readable)' : ''));
  } else {
    setStatus_(sh, row, cols, 'Problem: Discord said HTTP ' + code + ' (fix, then set Approved to NO and back to YES)');
  }
}

// Run by hand to check the tag text with no Google calls and nothing sent (see the Execution log).
function testTags() {
  Logger.log(buildTag(KINDS[0], ['Website', 'Facebook'], ''));
  Logger.log(buildTag(KINDS[0], ['Website', 'Facebook', 'Discord', 'Groups.io', 'Email subscribers'], 'Nov 4 2026 8:00 AM'));
  Logger.log(buildTag(KINDS[1], ['Website', 'Email subscribers'], ''));
  Logger.log(buildTag(KINDS[2], ['Events calendar', 'Website'], 'Nov 10 2026 6:30 PM'));
}

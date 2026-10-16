// KPC forms, part 2. Paste into an EMPTY Code.gs and Save. Then run each function ONCE:
//   addEmailChoice        adds "Which emails do you want?" to the Email Updates form
//   makeCwLeaderboardForm makes the CW Challenge Leaderboard form + answer sheet
// The Execution log shows the links to send to Claude.

var SUB_ID = '1FAIpQLScWT7T2nNJytN8hDIn2HEI_2GSRLt_txXjdJ_-jmi0Tk1QwrQ';
var CHOICE_TITLE = 'Which emails do you want?';
var CHOICES = ['Everything (all club updates)', 'Campout updates only', 'Weekly roundup only (one email on Sundays)'];
var CALL = '^[A-Za-z0-9]{1,3}[0-9][A-Za-z0-9]{0,4}(/[A-Za-z0-9]{1,4})?$';
var WEEK = '^20[0-9][0-9]-W[0-9][0-9]$';

function approvedDropdown(sh, col) {
  var rule = SpreadsheetApp.newDataValidation();
  rule = rule.requireValueInList(['YES', 'NO'], true);
  rule = rule.setAllowInvalid(false);
  sh.getRange(2, col, 1999, 1).setDataValidation(rule.build());
}

function findSubForm() {
  var files = DriveApp.getFilesByType(MimeType.GOOGLE_FORMS);
  while (files.hasNext()) {
    var f = files.next();
    try {
      var form = FormApp.openById(f.getId());
      if (form.getPublishedUrl().indexOf(SUB_ID) >= 0) { return form; }
    } catch (e) {}
  }
  return null;
}

function addEmailChoice() {
  var form = findSubForm();
  if (!form) {
    Logger.log('Could not find the Email Updates form in this Google account. Run this in the account that made that form.');
    return;
  }
  var items = form.getItems();
  var item = null;
  var after = -1;
  for (var i = 0; i < items.length; i++) {
    if (items[i].getTitle() === CHOICE_TITLE) { item = items[i].asMultipleChoiceItem(); }
    if (items[i].getType() === FormApp.ItemType.MULTIPLE_CHOICE && items[i].getTitle() !== CHOICE_TITLE) {
      var ch = items[i].asMultipleChoiceItem().getChoices();
      for (var c = 0; c < ch.length; c++) {
        if (ch[c].getValue() === 'Subscribe') { after = i; }
      }
    }
  }
  if (!item) {
    item = form.addMultipleChoiceItem();
    item.setTitle(CHOICE_TITLE);
    item.setHelpText('Leave it blank to get everything. Skip it if you are unsubscribing.');
    item.setChoiceValues(CHOICES);
    if (after >= 0) { form.moveItem(item.getIndex(), after + 1); }
    Logger.log('Added the question to: ' + form.getTitle());
  } else {
    Logger.log('The question was already there (nothing added twice).');
  }
  var r = form.createResponse();
  r.withItemResponse(item.createResponse(CHOICES[0]));
  Logger.log('PREFILL (for Claude): ' + r.toPrefilledUrl());
}

function numberRule(max, help) {
  var v = FormApp.createTextValidation();
  v = v.requireNumberBetween(0, max);
  v = v.setHelpText(help);
  return v.build();
}

function textRule(pattern, help) {
  var v = FormApp.createTextValidation();
  v = v.requireTextMatchesPattern(pattern);
  v = v.setHelpText(help);
  return v.build();
}

function makeCwLeaderboardForm() {
  var form = FormApp.create('KPC CW Challenge Leaderboard');
  form.setDescription('Send your score from the KPC CW Practice Room weekly challenge. The SUBMIT MY SCORE button on the CW page fills this in for you. Only your call sign and score are shown on the leaderboard.');
  form.setCollectEmail(false);
  form.setProgressBar(false);

  var call = form.addTextItem();
  call.setTitle('Call sign');
  call.setHelpText('Just the call sign, like K4TEST');
  call.setValidation(textRule(CALL, 'Just the call sign, like K4TEST'));
  call.setRequired(true);

  var kind = form.addMultipleChoiceItem();
  kind.setTitle('Which challenge?');
  kind.setChoiceValues(['Weekly copy challenge', 'Weekly Gauntlet']);
  kind.setRequired(true);

  var wk = form.addTextItem();
  wk.setTitle('Week');
  wk.setHelpText('Filled in for you, like 2026-W42');
  wk.setValidation(textRule(WEEK, 'Like 2026-W42'));
  wk.setRequired(true);

  var pts = form.addTextItem();
  pts.setTitle('Points');
  pts.setValidation(numberRule(100000, 'Numbers only'));
  pts.setRequired(true);

  var wpm = form.addTextItem();
  wpm.setTitle('Top WPM');
  wpm.setValidation(numberRule(80, 'Numbers only'));
  wpm.setRequired(true);

  form.setConfirmationMessage('Score sent! It shows on the leaderboard once it is checked. 73 and see you next week.');

  var ss = SpreadsheetApp.create('KPC CW Challenge Leaderboard (responses)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
  Utilities.sleep(3000);
  var sheets = ss.getSheets();
  var sh = sheets[0];
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getFormUrl()) { sh = sheets[i]; }
  }
  var col = sh.getLastColumn() + 1;
  sh.getRange(1, col).setValue('Approved');
  sh.getRange(1, col).setFontWeight('bold');
  approvedDropdown(sh, col);

  var r = form.createResponse();
  r.withItemResponse(call.createResponse('K4TEST'));
  r.withItemResponse(kind.createResponse('Weekly copy challenge'));
  r.withItemResponse(wk.createResponse('2026-W42'));
  r.withItemResponse(pts.createResponse('123'));
  r.withItemResponse(wpm.createResponse('45'));

  Logger.log('FORM (share this): ' + form.getPublishedUrl());
  Logger.log('EDIT: ' + form.getEditUrl());
  Logger.log('SHEET: ' + ss.getUrl());
  Logger.log('PREFILL (for Claude): ' + r.toPrefilledUrl());
}

/* KPC Activations form builder.
   Builds the Google Form "KPC Activations & Park Requests" plus its response
   spreadsheet (with an Approved column), then prints the links in the log.

   HOW TO USE (once):
   1. Go to script.google.com while signed in to the Google account that should own the form.
      (On a phone: open it in Chrome and pick "Desktop site" from the ⋮ menu.)
   2. New project. Delete what's there, paste ALL of this file, press 💾 Save.
   3. Pick makeActivationForm in the function list and press ▶ Run.
      Google asks for permission the first time: Review permissions → your account →
      Advanced → Go to project → Allow.
   4. Open View → Logs (or the Execution log). It shows:
        FORM (share this) ......... the link people fill in
        EDIT ...................... where you can change the questions
        SHEET ..................... the answers, with the Approved column
        PREFILL ................... a link Claude needs for the website buttons
   Running it again makes a SECOND form, so only run it once. */

var TZ = ['Eastern', 'Central', 'Mountain', 'Pacific', 'UTC'];
var BANDS = ['160m', '80m', '60m', '40m', '30m', '20m', '17m', '15m', '12m', '10m', '6m', '2m', '70cm'];
var MODES = ['SSB (voice)', 'CW', 'FT8', 'FT4', 'FM', 'Other digital'];
var PROGS = ['POTA', 'WWFF / KFF', 'SOTA', 'Other'];
var ONE = '([A-Za-z0-9]{1,4}-[0-9]{1,5}|[A-Za-z0-9]{1,4}/[A-Za-z0-9]{2}-[0-9]{3})';
var REFS = '^\\s*' + ONE + '(\\s*,\\s*' + ONE + ')*\\s*$';   // US-1271, KFF-1271, W4K/EC-001 (commas between)
function refCheck(help) { return FormApp.createTextValidation().requireTextMatchesPattern(REFS).setHelpText(help).build(); }
function shortNote() { return FormApp.createParagraphTextValidation().requireTextLengthLessThanOrEqualTo(300).setHelpText('300 letters or fewer').build(); }

function makeActivationForm() {
  var form = FormApp.create('KPC Activations & Park Requests');
  form.setDescription(
    'Kentucky Portable Club: tell everyone where you are activating (planned or on the air now), ' +
    'or ask for a park you need. Approved posts show on the KPC website. ' +
    'Your call sign is shown; nothing else about you is.');
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false);
  form.setProgressBar(false);

  // ---- first page ----
  var callRx = '^[A-Za-z0-9]{1,3}[0-9][A-Za-z0-9]{0,4}(/[A-Za-z0-9]{1,4})?$';
  form.addTextItem().setTitle('Call sign').setRequired(true)
    .setValidation(FormApp.createTextValidation().requireTextMatchesPattern(callRx)
      .setHelpText('Just the call sign, like K4TEST or K4TEST/P').build());
  var kind = form.addMultipleChoiceItem().setTitle('What are you posting?').setRequired(true);

  // ---- section A: activation ----
  var pageA = form.addPageBreakItem().setTitle('Your activation');
  form.addMultipleChoiceItem().setTitle('Planned or on the air now?').setRequired(true)
    .setChoiceValues(['Planned activation', 'On the air now']);
  form.addTextItem().setTitle('Park, summit or reference number(s)').setRequired(true)
    .setHelpText('Numbers only, like US-1271, KFF-1271 or W4K/EC-001. Two or more? Separate with commas.')
    .setValidation(refCheck('Use the number, like US-1271 or W4K/EC-001 (commas between two or more)'));
  form.addCheckboxItem().setTitle('Program').setChoiceValues(PROGS);
  form.addDateItem().setTitle('Date').setRequired(true);
  form.addTimeItem().setTitle('Start time').setRequired(true);
  form.addTimeItem().setTitle('End time (about)');
  form.addMultipleChoiceItem().setTitle('Time zone').setRequired(true).setChoiceValues(TZ);
  form.addCheckboxItem().setTitle('Bands').setRequired(true).setChoiceValues(BANDS);
  form.addCheckboxItem().setTitle('Modes').setRequired(true).setChoiceValues(MODES);
  form.addTextItem().setTitle('Frequencies').setHelpText('Optional, like 14.285, 7.032')
    .setValidation(FormApp.createTextValidation().requireTextMatchesPattern('^[0-9.,\\s]+$').setHelpText('Numbers only, like 14.285, 7.032').build());
  form.addCheckboxItem().setTitle('Extras').setChoiceValues(['Park-to-park welcome', 'QRP (low power)', 'First activation', 'Kids on the air', '2-fer (two parks at once)', 'Club outing']);
  form.addParagraphTextItem().setTitle('Notes').setHelpText('Optional. Posts with notes are checked by a club officer before they show.').setValidation(shortNote());

  // ---- section B: hunter request ----
  var pageB = form.addPageBreakItem().setTitle('Park request (hunters)')
    .setHelpText('Ask for a park you still need. An activator may pick it up.');
  pageB.setGoToPage(FormApp.PageNavigationType.SUBMIT); // section A ends here and submits
  form.addTextItem().setTitle('Park(s) you need').setRequired(true)
    .setHelpText('Numbers only, like US-1271 (look it up on pota.app). Two or more? Separate with commas.')
    .setValidation(refCheck('Use the park number, like US-1271 (commas between two or more)'));
  form.addCheckboxItem().setTitle('Program (request)').setChoiceValues(PROGS);
  form.addCheckboxItem().setTitle('Bands you can hear').setChoiceValues(BANDS);
  form.addCheckboxItem().setTitle('Modes you can work').setChoiceValues(MODES);
  form.addCheckboxItem().setTitle('When works best for you?').setChoiceValues(['Weekday mornings', 'Weekday afternoons', 'Weekday evenings', 'Weekends', 'Any time']);
  form.addParagraphTextItem().setTitle('Notes (request)').setHelpText('Optional. Requests with notes are checked by a club officer before they show.').setValidation(shortNote());

  kind.setChoices([
    kind.createChoice('My activation (planned or on the air now)', pageA),
    kind.createChoice('Hunter request: I need a park', pageB)
  ]);
  form.setConfirmationMessage('Thanks! Once a club officer checks it, it shows on the KPC website. 73!');

  // ---- response sheet + Approved column ----
  var ss = SpreadsheetApp.create('KPC Activations & Park Requests (responses)');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
  SpreadsheetApp.flush();
  Utilities.sleep(3000);
  var sh = ss.getSheets().filter(function (s) { return s.getFormUrl(); })[0] || ss.getSheets()[0];
  var col = Math.max(sh.getLastColumn(), 1) + 1;
  sh.getRange(1, col).setValue('Approved').setFontWeight('bold').setBackground('#fff2cc');
  sh.getRange(2, col, 999, 1).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(['YES', 'NO'], true).setAllowInvalid(true).build());
  ss.getSheets().forEach(function (s) { if (s.getSheetName() === 'Sheet1' && s.getLastRow() === 0 && ss.getSheets().length > 1) ss.deleteSheet(s); });

  // ---- a pre-filled example link (Claude reads the entry numbers from it for website buttons) ----
  var items = form.getItems(), r = form.createResponse();
  items.forEach(function (it) {
    if (it.getTitle() === 'Park, summit or reference number(s)') r.withItemResponse(it.asTextItem().createResponse('PARKREF'));
    if (it.getTitle() === 'Park(s) you need') r.withItemResponse(it.asTextItem().createResponse('NEEDREF'));
    if (it.getTitle() === 'What are you posting?') r.withItemResponse(it.asMultipleChoiceItem().createResponse('My activation (planned or on the air now)'));
  });
  var prefill = r.toPrefilledUrl();

  Logger.log('FORM (share this): ' + form.getPublishedUrl());
  Logger.log('EDIT: ' + form.getEditUrl());
  Logger.log('SHEET: ' + ss.getUrl());
  Logger.log('PREFILL (for Claude): ' + prefill);
}

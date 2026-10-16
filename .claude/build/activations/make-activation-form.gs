// KPC Activations form builder. Paste into an EMPTY Code.gs, Save, pick makeActivationForm, Run ONCE.
// The Execution log then shows the FORM, EDIT, SHEET and PREFILL links.

var TZ = ['Eastern', 'Central', 'Mountain', 'Pacific', 'UTC'];
var BANDS = ['160m', '80m', '60m', '40m', '30m', '20m', '17m', '15m', '12m', '10m', '6m', '2m', '70cm'];
var MODES = ['SSB (voice)', 'CW', 'FT8', 'FT4', 'FM', 'Other digital'];
var PROGS = ['POTA', 'WWFF / KFF', 'SOTA', 'Other'];
var EXTRAS = ['Park-to-park welcome', 'QRP (low power)', 'First activation', 'Kids on the air', '2-fer (two parks at once)', 'Club outing'];
var WHEN = ['Weekday mornings', 'Weekday afternoons', 'Weekday evenings', 'Weekends', 'Any time'];
var ONE = '([A-Za-z0-9]{1,4}-[0-9]{1,5}|[A-Za-z0-9]{1,4}/[A-Za-z0-9]{2}-[0-9]{3})';
var REFS = '^ *' + ONE + '( *, *' + ONE + ')* *$';
var CALL = '^[A-Za-z0-9]{1,3}[0-9][A-Za-z0-9]{0,4}(/[A-Za-z0-9]{1,4})?$';
var FREQ = '^[0-9., ]+$';

function rule(pattern, help) {
  var v = FormApp.createTextValidation();
  v = v.requireTextMatchesPattern(pattern);
  v = v.setHelpText(help);
  return v.build();
}

function shortNote() {
  var v = FormApp.createParagraphTextValidation();
  v = v.requireTextLengthLessThanOrEqualTo(300);
  v = v.setHelpText('300 letters or fewer');
  return v.build();
}

function addText(form, title, help, pattern, required) {
  var it = form.addTextItem();
  it.setTitle(title);
  if (help) { it.setHelpText(help); }
  if (pattern) { it.setValidation(rule(pattern, help)); }
  if (required) { it.setRequired(true); }
  return it;
}

function addChecks(form, title, list, required) {
  var it = form.addCheckboxItem();
  it.setTitle(title);
  it.setChoiceValues(list);
  if (required) { it.setRequired(true); }
  return it;
}

function addNotes(form, title, help) {
  var it = form.addParagraphTextItem();
  it.setTitle(title);
  it.setHelpText(help);
  it.setValidation(shortNote());
  return it;
}

function makeActivationForm() {
  var form = FormApp.create('KPC Activations & Park Requests');
  form.setDescription('Kentucky Portable Club: tell everyone where you are activating (planned or on the air now), or ask for a park you need. Approved posts show on the KPC website. Only your call sign is shown.');
  form.setCollectEmail(false);
  form.setProgressBar(false);

  addText(form, 'Call sign', 'Just the call sign, like K4TEST or K4TEST/P', CALL, true);
  var kind = form.addMultipleChoiceItem();
  kind.setTitle('What are you posting?');
  kind.setRequired(true);

  // Section A: an activation
  var pageA = form.addPageBreakItem();
  pageA.setTitle('Your activation');
  var now = form.addMultipleChoiceItem();
  now.setTitle('Planned or on the air now?');
  now.setChoiceValues(['Planned activation', 'On the air now']);
  now.setRequired(true);
  addText(form, 'Park, summit or reference number(s)', 'Numbers only, like US-1271, KFF-1271 or W4K/EC-001. Two or more? Put commas between.', REFS, true);
  addChecks(form, 'Program', PROGS, false);
  var d = form.addDateItem();
  d.setTitle('Date');
  d.setRequired(true);
  var t1 = form.addTimeItem();
  t1.setTitle('Start time');
  t1.setRequired(true);
  var t2 = form.addTimeItem();
  t2.setTitle('End time (about)');
  var tz = form.addMultipleChoiceItem();
  tz.setTitle('Time zone');
  tz.setChoiceValues(TZ);
  tz.setRequired(true);
  addChecks(form, 'Bands', BANDS, true);
  addChecks(form, 'Modes', MODES, true);
  addText(form, 'Frequencies', 'Optional. Numbers only, like 14.285, 7.032', FREQ, false);
  addChecks(form, 'Extras', EXTRAS, false);
  addNotes(form, 'Notes', 'Optional. Posts with notes are checked by a club officer before they show.');

  // Section B: a hunter's park request
  var pageB = form.addPageBreakItem();
  pageB.setTitle('Park request (hunters)');
  pageB.setHelpText('Ask for a park you still need. An activator may pick it up.');
  pageB.setGoToPage(FormApp.PageNavigationType.SUBMIT);
  addText(form, 'Park(s) you need', 'Numbers only, like US-1271 (look it up on pota.app). Two or more? Put commas between.', REFS, true);
  addChecks(form, 'Program (request)', PROGS, false);
  addChecks(form, 'Bands you can hear', BANDS, false);
  addChecks(form, 'Modes you can work', MODES, false);
  addChecks(form, 'When works best for you?', WHEN, false);
  addNotes(form, 'Notes (request)', 'Optional. Requests with notes are checked by a club officer before they show.');

  var c1 = kind.createChoice('My activation (planned or on the air now)', pageA);
  var c2 = kind.createChoice('Hunter request: I need a park', pageB);
  kind.setChoices([c1, c2]);
  form.setConfirmationMessage('Thanks! Once it is checked, it shows on the KPC website. 73!');

  // Answer sheet with an Approved column
  var ss = SpreadsheetApp.create('KPC Activations & Park Requests (responses)');
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

  // Example pre-filled link (Claude reads the entry numbers from it)
  var r = form.createResponse();
  var items = form.getItems();
  for (var j = 0; j < items.length; j++) {
    var title = items[j].getTitle();
    if (title === 'Park, summit or reference number(s)') { r.withItemResponse(items[j].asTextItem().createResponse('PARKREF')); }
    if (title === 'Park(s) you need') { r.withItemResponse(items[j].asTextItem().createResponse('NEEDREF')); }
  }

  Logger.log('FORM (share this): ' + form.getPublishedUrl());
  Logger.log('EDIT: ' + form.getEditUrl());
  Logger.log('SHEET: ' + ss.getUrl());
  Logger.log('PREFILL (for Claude): ' + r.toPrefilledUrl());
}

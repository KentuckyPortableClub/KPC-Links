// KPC Guestbook form builder. Paste into an EMPTY Code.gs, Save, pick makeGuestbookForm, Run ONCE.
// The Execution log then shows the FORM, EDIT, SHEET and PREFILL links.

var STATES = ['Kentucky', 'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming', 'Puerto Rico / US territory', 'Canada', 'Outside the US and Canada'];
var HAM = ['Licensed ham', 'Studying for my license', 'Not a ham (yet!)'];
var FOUND = ['Facebook', 'Discord', 'YouTube', 'Google or another search', 'POTA / SOTA / WWFF', 'QRZ', 'A friend or club', 'Heard us on the air', 'A KPC campout or event', 'Other'];
var LIKE = ['Parks & maps', 'Radio tools', 'CW practice', 'Kids Room', 'Campout', 'Weather & band conditions', 'Guides', 'Just looking around'];

function shortNote() {
  var v = FormApp.createParagraphTextValidation();
  v = v.requireTextLengthLessThanOrEqualTo(300);
  v = v.setHelpText('300 letters or fewer');
  return v.build();
}

function shortName() {
  var v = FormApp.createTextValidation();
  v = v.requireTextLengthLessThanOrEqualTo(30);
  v = v.setHelpText('30 letters or fewer');
  return v.build();
}

function approvedDropdown(sh, col) {
  var rule = SpreadsheetApp.newDataValidation();
  rule = rule.requireValueInList(['YES', 'NO'], true);
  rule = rule.setAllowInvalid(false);
  sh.getRange(2, col, 1999, 1).setDataValidation(rule.build());
}

function makeGuestbookForm() {
  var form = FormApp.create('KPC Guestbook');
  form.setDescription('Sign the Kentucky Portable Club guestbook! Tell us you stopped by. Your call sign or first name, where you are from and your message can show on the KPC website. Please do not put phone numbers, emails or links in your message.');
  form.setCollectEmail(false);
  form.setProgressBar(false);

  var n = form.addTextItem();
  n.setTitle('Call sign or first name');
  n.setHelpText('This shows on the website. Like K4TEST or Sam.');
  n.setValidation(shortName());
  n.setRequired(true);

  var st = form.addListItem();
  st.setTitle('Where are you from?');
  st.setChoiceValues(STATES);
  st.setRequired(true);

  var town = form.addTextItem();
  town.setTitle('Town (optional)');
  town.setValidation(shortName());

  var ham = form.addMultipleChoiceItem();
  ham.setTitle('Are you a ham?');
  ham.setChoiceValues(HAM);
  ham.setRequired(true);

  var f = form.addMultipleChoiceItem();
  f.setTitle('How did you find us?');
  f.setChoiceValues(FOUND);

  var l = form.addCheckboxItem();
  l.setTitle('What did you like?');
  l.setChoiceValues(LIKE);

  var m = form.addParagraphTextItem();
  m.setTitle('Your message (optional)');
  m.setHelpText('Say hi! Messages are checked before they show on the website.');
  m.setValidation(shortNote());

  form.setConfirmationMessage('Thanks for signing the KPC guestbook! 73 and come back soon.');

  var ss = SpreadsheetApp.create('KPC Guestbook (responses)');
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
  var items = form.getItems();
  for (var j = 0; j < items.length; j++) {
    if (items[j].getTitle() === 'Call sign or first name') { r.withItemResponse(items[j].asTextItem().createResponse('NAME')); }
  }

  Logger.log('FORM (share this): ' + form.getPublishedUrl());
  Logger.log('EDIT: ' + form.getEditUrl());
  Logger.log('SHEET: ' + ss.getUrl());
  Logger.log('PREFILL (for Claude): ' + r.toPrefilledUrl());
}

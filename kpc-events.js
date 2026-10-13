/* ===== KENTUCKY RADIO CALENDAR — edit this list to add or change events (used by the Events page, the home page "Next Up" strip and the weekly Discord post) =====
   start/end: 'YYYY-MM-DD' (all-day) • time: optional text • tba: true when the next date isn't announced yet (put the usual timing in 'when')
   Past events (end date before today) hide automatically. */
(function(root){
var EVENTS=[
 {name:'Kentucky Mountains ARC Hamfest',tags:['HAMFEST'],start:'2026-10-31',where:'VFW Post 7387, 1700 N. Main St., Hazard, KY',by:'Kentucky Mountains Amateur Radio Club (KMARC)',url:'https://www.arrl.org/hamfests/kentucky-mountains-amateur-radio-club-hamfest'},
 {name:'POTA Support Your Parks Weekend',tags:['POTA'],start:'2027-01-16',end:'2027-01-17',where:'Any Kentucky park — get out and activate!',by:'Parks on the Air',url:'https://pota.app/'},
 {name:'Orlando HamCation',tags:['HAMFEST'],start:'2027-02-12',end:'2027-02-14',time:'Fri.–Sat. 9 AM–5 PM, Sun. 9 AM–1 PM (Eastern)',where:'Central Florida Fairgrounds & Expo Park, 4603 W. Colonial Dr., Orlando, FL — one of the biggest hamfests in the Southeast',by:'Orlando Amateur Radio Club',url:'https://www.hamcation.com/'},
 {name:'Cave City Hamfest',tags:['HAMFEST'],start:'2027-03-06',where:'Cave City Convention Center, Cave City, KY',by:'Mammoth Cave Amateur Radio Club',url:'https://www.ky4x.org/hamfest',url2:'https://www.arrl.org/hamfests/cave-city-hamfest-17'},
 {name:'SOTA Kentucky Campout',tags:['SOTA'],tba:true,when:'Usually a weekend in April (2025: weekend of April 12, the 3rd annual)',where:'Kingdom Come State Park, Cumberland, KY. Primitive camping; activate Eastern Kentucky summits all weekend',by:'Kentucky SOTA activators (announced on the SOTA Reflector)',url:'https://reflector.sota.org.uk/t/2025-sota-kentucky-campout/36069'},
 {name:'Elizabethtown Hamfest',tags:['HAMFEST'],tba:true,when:'Usually early April (2026: Sat., April 4)',where:'Elizabethtown, KY',by:'Stubblefield Repeater Club',url:'https://stubblefieldrepeaterclub.org/'},
 {name:'POTA Support Your Parks Weekend',tags:['POTA'],start:'2027-04-17',end:'2027-04-18',where:'Any Kentucky park',by:'Parks on the Air',url:'https://pota.app/'},
 {name:'Dayton Hamvention',tags:['HAMFEST'],start:'2027-05-21',end:'2027-05-23',where:'Greene County Fairgrounds & Expo Center, Xenia, OH — the biggest hamfest in the country',by:'Dayton Amateur Radio Association',url:'https://hamvention.org/'},
 {name:'Happy Birthday, Kentucky! — Statehood Day POTA Weekend',tags:['KPC','POTA'],start:'2027-06-05',end:'2027-06-06',time:'The first weekend after Kentucky’s birthday (statehood: June 1, 1792 — Kentucky turns 235!)',where:'Any Kentucky park — go activate and celebrate the Commonwealth. Saturday is also the Kentucky QSO Party, so hunters will be looking for Kentucky!',by:'Kentucky Portable Club',url:'events.html#events-calendar',local:true},
 {name:'Kentucky QSO Party',tags:['CONTEST'],start:'2027-06-05',time:'Planned 9 AM–9 PM Eastern (13–01 UTC) — rules are a draft, times may change',where:'On the air — Kentucky stations send RS(T) + county',by:'Kentucky QSO Party committee',url:'https://kyqsoparty.org/rules/'},
 {name:'POTA Support Your Parks Weekend',tags:['POTA'],start:'2027-07-17',end:'2027-07-18',where:'Any Kentucky park',by:'Parks on the Air',url:'https://pota.app/'},
 {name:'Huntsville Hamfest',tags:['HAMFEST'],start:'2027-08-21',end:'2027-08-22',time:'Sat. 9 AM–4:30 PM, Sun. 9 AM–3 PM (Central)',where:'Von Braun Center South Hall, 700 Monroe St. SW, Huntsville, AL',by:'Huntsville Hamfest',url:'https://hamfest.org/'},
 {name:'KYPOTA — Kentucky State Parks on the Air',tags:['CONTEST','POTA'],tba:true,when:'Usually a Saturday in August (2026: Sat., Aug. 8, 1400–2200 UTC)',where:'Operate from Kentucky state parks & national sites',by:'Murray State University Amateur Radio Club (K4MSU)',url:'https://k4msu.com/kypota/'},
 {name:'Greater Louisville Hamfest',tags:['HAMFEST'],tba:true,when:'Usually mid-September (2026: Sat., Sept. 12)',where:'Paroquet Springs Conference Centre, Shepherdsville, KY',by:'Greater Louisville Hamfest',url:'https://louisvillehamfest.wixsite.com/louisvillehamfest'},
 {name:'Richmond Kentucky Hamfest',tags:['HAMFEST'],tba:true,when:'Usually September (2026: Sat., Sept. 19)',where:'Madison County Fairgrounds, Richmond, KY',by:'Central Kentucky Amateur Radio Society',url:'http://www.ckars.org'},
 {name:'Paintsville KY4ARC Hamfest',tags:['HAMFEST'],tba:true,when:'Usually late September (2025: Sat., Sept. 27)',where:'Paintsville Recreation Center, Paintsville, KY',by:'KY4ARC',url:'http://ky4arc.com'},
 {name:'POTA Support Your Parks Weekend',tags:['POTA'],start:'2027-10-16',end:'2027-10-17',where:'Any Kentucky park',by:'Parks on the Air',url:'https://pota.app/'}
];
var M=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
function pd(s){var a=s.split('-').map(Number);return new Date(a[0],a[1]-1,a[2])}
function norm(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim()}
function words(s){return norm(s).split(' ').filter(function(w){return w.length>=5&&!/hamfest|kentucky|amateur|radio|annual|weekend|club|association/.test(w)})}
function days(x,y){return Math.abs(pd(x)-pd(y))/864e5}
/* Merge the hand-made list with kpc-events-auto.json (written weekly by the KPC Events Finder workflow).
   Auto-found events never overwrite what's here; they only fill in a missing date or add a second link. */
function merge(base,auto){
 var ALL=base.map(function(e){return Object.assign({},e,{tags:e.tags.slice()})});
 if(!auto)return ALL;
 function twinOf(e){if(e.tags.indexOf('AUTO')<0)return ALL.find(function(b){return norm(b.name)===norm(e.name)&&!b.tba&&b.start===e.start});
  return ALL.find(function(b){return !b.auto&&b.tags.some(function(t){return e.tags.indexOf(t)>=0})&&(
   [e.url,e.url2].some(function(u){return u&&/\/\/[^/]+\/./.test(u)&&(b.url===u||b.url2===u)})||
   (norm(b.name)===norm(e.name)&&(b.tba||e.tba||b.start===e.start))||
   (words(e.name).some(function(w){return words(b.name).indexOf(w)>=0})&&(b.tba||e.tba||days(b.start,e.start)<=3)))})}
 [].concat(auto.recurring||[],auto.found||[]).forEach(function(e){
  if(!e||!e.name||!Array.isArray(e.tags)||(!e.start&&!e.tba))return;
  var isAuto=e.tags.indexOf('AUTO')>=0,t=twinOf(e);
  if(t){
   if(t.tba&&e.start){Object.assign(t,{tba:false,start:e.start,end:e.end,auto:isAuto});if(isAuto)t.tags=t.tags.concat('AUTO')}
   if(isAuto&&!t.url2){var u=[e.url,e.url2].find(function(x){return x&&x!==t.url});if(u){t.url2=u;t.url2label=/arrl\.org\/hamfests/.test(u)?'ARRL LISTING ↗':e.source==='SOTA'?'ANNOUNCEMENT ↗':'CLUB WEBSITE ↗'}}
   return}
  ALL.push(Object.assign({},e,{auto:isAuto}))});
 return ALL}
// TBA events sort by their usual month
function sortKey(e,today){if(e.tba){var mm=M.findIndex(function(m){return String(e.when||'').toUpperCase().indexOf(m)>=0});var y=today.getFullYear()+(mm>=0&&mm<today.getMonth()?1:0);return new Date(y,Math.max(0,mm),15)}return pd(e.start)}
function upcoming(all,today){today=today||new Date();today=new Date(today.getFullYear(),today.getMonth(),today.getDate());
 return all.filter(function(e){return e.tba||pd(e.end||e.start)>=today}).sort(function(a,b){return sortKey(a,today)-sortKey(b,today)})}
var api={EVENTS:EVENTS,merge:merge,upcoming:upcoming,pd:pd,sortKey:sortKey};
root.KPCEvents=api;
if(typeof module==='object'&&module.exports)module.exports=api;
})(typeof window!=='undefined'?window:globalThis);

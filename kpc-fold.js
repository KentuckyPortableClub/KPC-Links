/* KPC: on phones, long sections start folded behind a SHOW MORE button.
   Add the attribute data-fold to a <section>. Desktop is never changed.
   The section heading (and the intro line after it) stay visible; the rest folds. */
(function(){
var st=document.createElement('style');st.id='kpc-fold-css';
st.textContent='.kpc-fold-btn{display:none}@media(max-width:760px){.kpc-fold-btn{display:inline-flex;align-items:center;gap:6px;margin:16px 0 4px;padding:10px 18px;border:1px solid var(--gold,#d5a63a);border-radius:999px;background:transparent;color:inherit;font:900 12px Arial,Helvetica,sans-serif;letter-spacing:1.5px;cursor:pointer}.kpc-folded .kpc-fold-item{display:none!important}.kpc-folded{padding-bottom:36px!important}}';
document.head.appendChild(st);
function init(){
 var mq=matchMedia('(max-width:760px)'),secs=[].slice.call(document.querySelectorAll('section[data-fold]')),ok=[];
 secs.forEach(function(s){
  var inner=s.querySelector(':scope > .section-inner')||s.querySelector(':scope > .wrap')||s.firstElementChild;if(!inner)return;
  var kids=[].slice.call(inner.children),head=[],at=-1;
  for(var i=0;i<kids.length;i++){var k=kids[i];head.push(k);if(k.tagName==='H2'||(k.querySelector&&k.querySelector('h2'))){at=i;break}}
  if(at<0)return;
  if(kids[at+1]&&kids[at+1].tagName==='P'&&/lead/.test(kids[at+1].className)){head.push(kids[at+1]);at++}
  var tail=kids.slice(at+1);if(!tail.length)return;
  tail.forEach(function(k){k.classList.add('kpc-fold-item')});
  var b=document.createElement('button');b.type='button';b.className='kpc-fold-btn';
  var last=head[head.length-1];last.parentNode.insertBefore(b,last.nextSibling);
  s._set=function(open){s.classList.toggle('kpc-folded',!open);b.setAttribute('aria-expanded',String(open));b.textContent=open?'SHOW LESS ▴':'SHOW MORE ▾'};
  b.addEventListener('click',function(){var open=s.classList.contains('kpc-folded');s._set(open);if(!open)s.scrollIntoView({block:'start'})});
  ok.push(s)});
 function apply(){ok.forEach(function(s){s._set(!mq.matches)})}apply();
 if(mq.addEventListener)mq.addEventListener('change',apply);else mq.addListener(apply);
 function openTo(id){var t=id&&document.getElementById(id),s=t&&t.closest('section[data-fold]');if(s&&s._set&&s.classList.contains('kpc-folded')){s._set(true);requestAnimationFrame(function(){t.scrollIntoView()})}}
 window.addEventListener('hashchange',function(){openTo(location.hash.slice(1))});openTo(location.hash.slice(1));
 document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^="#"]');if(a&&a.getAttribute('href').length>1)openTo(a.getAttribute('href').slice(1))});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

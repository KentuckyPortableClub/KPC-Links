/* KPC Community: approved posts from the KPC Community Google Form (kpc-community.json, updated by a
   GitHub job every 2 hours). Tabs by type, newest first, search. */
(function(){
// Google Form share link (set once the form is published)
const FORM_URL='https://docs.google.com/forms/d/e/1FAIpQLSf5IRZkwNWFb7OaOXqWj-FMcCf6dy5kyns9aT_pB_Ri06tOJQ/viewform';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const T=[['all','ALL'],['setup','STATION SETUPS'],['antenna','ANTENNA BUILDS'],['tip','FIELD TIPS'],['review','GEAR REVIEWS'],['story','ACTIVATION STORIES'],['elmer','ELMERS (MENTORS)'],['spotlight','OPERATOR SPOTLIGHTS']];
const KL={setup:'STATION SETUP',antenna:'ANTENNA BUILD',tip:'FIELD TIP',review:'GEAR REVIEW',story:'ACTIVATION STORY',elmer:'ELMER (MENTOR)',spotlight:'OPERATOR SPOTLIGHT'};
const ROWS={setup:[['radio','Radio'],['antenna','Antenna'],['power','Power'],['mast','Mast / support'],['weight','Weight & packing'],['cost','About cost']],
 antenna:[['bands','Bands'],['dims','Dimensions'],['feed','Feed / matching'],['swr','SWR']],
 review:[['pros','Pros'],['cons','Cons'],['again','Buy again?']],
 story:[['refs','Parks / summits'],['adate','Date']],
 elmer:[['area','Area'],['reach','How to reach']],
 spotlight:[['county','Home county'],['since','Licensed since'],['fav','Favorite spot']]};
let I=[],tab=store.get('kpcCommTab','all');if(!T.some(t=>t[0]===tab))tab='all';
const fmt=d=>{const m=String(d||'').match(/^(\d{4})-(\d\d)-(\d\d)/);return m?new Date(+m[1],+m[2]-1,+m[3]).toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'}):''};
function title(i){const f=i.f;if(i.type==='elmer')return `${i.call}: Elmer in ${f.area||'Kentucky'}`;if(i.type==='spotlight')return `${f.name?f.name+', ':''}${i.call}`;return f.title||KL[i.type]}
function refsLinks(s){return esc(s).replace(/\b(US-\d{4,5}|K-\d{4,5}|KFF-\d{4}|W4K\/[A-Z]{2}-\d{3})\b/g,r=>`<a href="kpc-park-notes.html#${encodeURIComponent(r)}">${r}</a>`)}
function card(i){const f=i.f;
 const ph=(i.photos||[]).length?`<div class="ph">${i.photos.map(p=>`<a href="${esc(p)}" target="_blank" rel="noopener"><img src="${esc(p)}" alt="${esc(title(i))} photo" loading="lazy"></a>`).join('')}</div>`:'';
 const dl=(ROWS[i.type]||[]).filter(([k])=>f[k]).map(([k,l])=>`<div><dt>${l}</dt><dd>${k==='refs'?refsLinks(f[k]):esc(f[k])}</dd></div>`).join('');
 const stars=i.type==='review'&&f.rating?`<div class="cm-stars" aria-label="${esc(f.rating)} out of 5">${'★'.repeat(Math.max(0,Math.min(5,+f.rating||0)))}${'☆'.repeat(5-Math.max(0,Math.min(5,+f.rating||0)))}</div>`:'';
 const help=i.type==='elmer'&&f.help?`<div>${String(f.help).split(/\s*,\s*/).map(h=>`<span class="cm-chip">${esc(h)}</span>`).join('')}</div>`:'';
 return `<article class="cm-card">${ph}<div class="cm-in"><div class="cm-k">${KL[i.type]}</div><h3>${esc(title(i))}</h3>
 <p class="cm-by">from <a href="https://www.qrz.com/db/${encodeURIComponent(i.call)}" target="_blank" rel="noopener">${esc(i.call)}</a>${i.date?' · '+fmt(i.date):''}</p>
 ${stars}${help}${dl?`<dl class="cm-dl">${dl}</dl>`:''}${f.body?`<p class="cm-body">${esc(f.body)}</p>`:''}</div></article>`}
function draw(){
 $('cmTabs').innerHTML=T.map(([k,l])=>{const n=k==='all'?I.length:I.filter(i=>i.type===k).length;return `<button type="button" class="cm-tab" role="tab" data-t="${k}" aria-selected="${k===tab}">${l} · ${n}</button>`}).join('');
 const q=$('cmQ').value.trim().toLowerCase();
 const l=I.filter(i=>(tab==='all'||i.type===tab)&&(!q||(i.call+' '+Object.values(i.f).join(' ')).toLowerCase().includes(q)));
 $('cmCount').textContent=`${l.length} post${l.length===1?'':'s'} · newest first`;
 $('cmList').innerHTML=l.length?l.map(card).join(''):`<p class="cm-none">${I.length?'Nothing matches. Try another tab or search.':'No posts yet. Be the first: tap Share yours.'}</p>`;
}
async function init(){if(!$('cmList'))return;
 const s=$('cmShare');if(FORM_URL)s.href=FORM_URL;else{s.textContent='FORM COMING SOON';s.removeAttribute('target')}
 $('cmTabs').addEventListener('click',e=>{const b=e.target.closest('.cm-tab');if(!b)return;tab=b.dataset.t;store.set('kpcCommTab',tab);draw()});
 $('cmQ').addEventListener('input',draw);
 try{const j=await (await fetch('kpc-community.json',{cache:'no-cache'})).json();I=Array.isArray(j.items)?j.items:[]}catch(e){I=[]}
 const h=location.hash.slice(1);if(T.some(t=>t[0]===h))tab=h;
 draw()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

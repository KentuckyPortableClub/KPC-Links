/* KPC Park Notes: every Kentucky POTA park, SOTA summit and KFF reference, lowest to highest,
   with community tips that the club has approved. Tips come from the KPC Google Form; a GitHub job
   copies only approved rows (and their photos) into kpc-park-notes.json every couple of hours. */
(function(){
// Google Form: set from the form's pre-filled link (Get pre-filled link, Park number = US-0050)
const FORM={url:'',parkEntry:''};
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const store={get(k,d){try{const v=localStorage.getItem(k);return v==null?d:JSON.parse(v)}catch(e){return d}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const LINK={pota:r=>'https://pota.app/#/park/'+r,sota:r=>'https://sotl.as/summits/'+r,kff:r=>'https://wwff.co/directory/?showRef='+r};
const LAB={pota:'POTA',sota:'SOTLAS',kff:'WWFF'};
const num=r=>{const m=String(r).match(/(\d+)\s*$/);return m?+m[1]:0};
const sotaKey=r=>{const m=String(r).match(/^(.*?)-(\d+)$/);return m?[m[1],+m[2]]:[r,0]};
let D=null,N=[],tab=store.get('kpcNotesTab','pota');if(!['pota','sota','kff'].includes(tab))tab='pota';
function formUrl(ref){if(!FORM.url||!FORM.parkEntry)return '';return FORM.url+(FORM.url.includes('?')?'&':'?')+'usp=pp_url&'+FORM.parkEntry+'='+encodeURIComponent(ref)}
function rows(){
 if(!D)return[];
 if(tab==='pota')return D.parks.map(p=>({ref:p.c,n:p.n,co:p.co,ex:p.t})).sort((a,b)=>num(a.ref)-num(b.ref));
 if(tab==='sota')return D.summits.map(s=>({ref:s.c,n:s.n,co:s.co,ex:(s.ft?s.ft.toLocaleString()+' ft':'')+(s.pts?' • '+s.pts+' pts':'')})).sort((a,b)=>{const x=sotaKey(a.ref),y=sotaKey(b.ref);return x[0]<y[0]?-1:x[0]>y[0]?1:x[1]-y[1]});
 return D.kff.map(k=>({ref:k.c,n:k.n,co:k.co,ex:k.p?'Also POTA '+k.p:''})).sort((a,b)=>num(a.ref)-num(b.ref));
}
function tipsFor(ref){return N.filter(t=>t.ref===ref)}
function tipHtml(t){
 const gps=t.gps?(/^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$/.test(t.gps)?`<a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(t.gps.replace(/\s/g,''))}" target="_blank" rel="noopener">📍 ${esc(t.gps)}</a>`:`📍 ${esc(t.gps)}`):'';
 return `<div class="pn-tip"><div class="t">${esc(String(t.type||'TIP').toUpperCase())}</div><p>${esc(t.text)}</p>
 <div class="m">${gps?gps+' · ':''}from <a href="https://www.qrz.com/db/${encodeURIComponent(t.call)}" target="_blank" rel="noopener">${esc(t.call)}</a>${t.date?' · '+esc(t.date):''}</div>
 ${(t.photos||[]).length?`<div class="pn-ph">${t.photos.map(p=>`<a href="${esc(p)}" target="_blank" rel="noopener"><img src="${esc(p)}" alt="Photo from ${esc(t.call)} at ${esc(t.ref)}" loading="lazy"></a>`).join('')}</div>`:''}</div>`;
}
function draw(){
 document.querySelectorAll('.pn-tab').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.p===tab)));
 const q=$('pnQ').value.trim().toUpperCase(),only=$('pnHas').checked;
 const all=rows();const l=all.filter(r=>(!q||(r.ref+' '+r.n+' '+(r.co||'')).toUpperCase().includes(q))&&(!only||tipsFor(r.ref).length));
 const withTips=all.filter(r=>tipsFor(r.ref).length).length;
 $('pnCount').textContent=`${l.length} of ${all.length} ${tab==='pota'?'POTA parks':tab==='sota'?'SOTA summits':'KFF references'} · ${withTips} with tips · lowest number first`;
 $('pnList').innerHTML=l.length?l.map(r=>{const t=tipsFor(r.ref),f=formUrl(r.ref);
  return `<details class="pn-item" data-ref="${esc(r.ref)}"><summary><span class="pn-ref">${esc(r.ref)}</span><span class="pn-nm">${esc(r.n)}<span class="pn-co">${esc([r.co&&r.co+(/county|counties|see official|\//i.test(r.co)?'':' County'),r.ex].filter(Boolean).join(' • '))}</span></span><span class="pn-n${t.length?' has':''}">${t.length?t.length+' TIP'+(t.length>1?'S':''):'NO TIPS YET'}</span></summary>
  <div class="pn-body"><div class="pn-acts">${f?`<a class="go" href="${esc(f)}" target="_blank" rel="noopener">✎ SUBMIT A TIP</a>`:'<a class="go" aria-disabled="true">TIP FORM COMING SOON</a>'}<a href="${LINK[tab](r.ref)}" target="_blank" rel="noopener">${LAB[tab]} PAGE ↗</a>${tab==='pota'?`<a href="kpc-park-sheet.html?ref=${encodeURIComponent(r.ref)}">PARK SHEET</a>`:''}</div>
  ${t.length?t.map(tipHtml).join(''):'<p class="pn-none">No tips yet. Been here? Share what you know.</p>'}</div></details>`}).join(''):'<p class="pn-none">Nothing matches. Try another search.</p>';
}
async function init(){
 if(!$('pnList'))return;
 document.querySelectorAll('.pn-tab').forEach(b=>b.addEventListener('click',()=>{tab=b.dataset.p;store.set('kpcNotesTab',tab);draw()}));
 $('pnQ').addEventListener('input',draw);$('pnHas').addEventListener('change',draw);
 try{D=await (await fetch('kpc-ky-data.json',{cache:'no-cache'})).json()}catch(e){$('pnList').innerHTML='<p class="pn-none">Could not load the park list. Refresh to try again.</p>';return}
 try{const j=await (await fetch('kpc-park-notes.json',{cache:'no-cache'})).json();N=Array.isArray(j.notes)?j.notes:[]}catch(e){N=[]}
 try{const f=await (await fetch('kpc-park-notes-form.json',{cache:'no-cache'})).json();if(f&&f.url&&/^entry\.\d+$/.test(f.parkEntry||'')){FORM.url=f.url;FORM.parkEntry=f.parkEntry}}catch(e){}
 const h=decodeURIComponent(location.hash.slice(1)).toUpperCase();
 if(h){const p=/^US-/.test(h)?'pota':/^KFF-/.test(h)?'kff':/\//.test(h)?'sota':null;if(p)tab=p}
 draw();
 if(h){const el=[...document.querySelectorAll('.pn-item')].find(e=>e.dataset.ref===h);if(el){el.open=true;el.scrollIntoView({block:'center'})}}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

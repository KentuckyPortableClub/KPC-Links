'use strict';
const $=id=>document.getElementById(id), status=$('status');
let data=[],unmapped=[],center=null,markers=[],map=null,layer=null,requestController=null,lastMatches=[];
let potaWWFF=new Map(),sotaLocations=[];
let userLocationMarker=null;
let official2ferEvidence={};fetch('official-2fer-evidence.json').then(r=>r.ok?r.json():{}).then(x=>{official2ferEvidence=x;if(data.length)render()}).catch(()=>{});
let officialParkAccess={};fetch('official-park-access.json').then(r=>r.ok?r.json():{}).then(x=>{officialParkAccess=x;if(data.length)render()}).catch(()=>{});
let officialTrailMaps={};fetch('official-trail-maps.json').then(r=>{if(!r.ok)throw Error('map list');return r.json()}).then(x=>{officialTrailMaps=x; if(data.length)render()}).catch(()=>{});
function buildCrossReferences(){potaWWFF=new Map();sotaLocations=[];for(const d of data){if(d[0]==='WWFF'&&d[7]){const a=potaWWFF.get(d[7])||[];a.push(d[1]);potaWWFF.set(d[7],a)}if(d[0]==='SOTA')sotaLocations.push(d)}}
const savedKey='radio-finder-saved-v1';let saved={favorites:[],trip:[]};try{const v=JSON.parse(localStorage.getItem(savedKey));if(v&&Array.isArray(v.favorites)&&Array.isArray(v.trip))saved=v}catch(_){}
const key=d=>d[0]+':'+d[1];function persist(){try{localStorage.setItem(savedKey,JSON.stringify(saved))}catch(_){}drawSaved()}
function toggleSaved(kind,d){const k=key(d),a=saved[kind];const i=a.indexOf(k);if(i<0){a.push(k)}else{a.splice(i,1)}persist();render()}
function drawSaved(){for(const kind of ['favorites','trip']){const el=$(kind==='favorites'?'favorites':'tripstops');el.replaceChildren();const entries=saved[kind].map(k=>data.find(d=>key(d)===k)).filter(Boolean);$(kind==='favorites'?'favcount':'tripcount').textContent=entries.length;for(const d of entries){const r=node('div','saveditem');r.append(node('span','',d[0]+' '+d[1]+' · '+d[2]));const b=node('button','tiny','Remove');b.type='button';b.addEventListener('click',()=>toggleSaved(kind,d));r.append(b);el.append(r)}if(!entries.length)el.append(node('p','meta','No saved locations yet.'))}const route=$('triproute'),stops=saved.trip.map(k=>data.find(d=>key(d)===k)).filter(Boolean).slice(0,10);if(stops.length){const points=stops.map(d=>d[3]+','+d[4]);route.href='https://www.google.com/maps/dir/?api=1&destination='+encodeURIComponent(points.at(-1))+(points.length>1?'&waypoints='+encodeURIComponent(points.slice(0,-1).join('|')):'');route.hidden=false;route.textContent='Open '+stops.length+' trip stop'+(stops.length===1?'':'s')+' in Google Maps'}else route.hidden=true}
$('clearplan').addEventListener('click',()=>{saved.trip=[];persist();render()});
// Use one consistent map tile layer. Do not switch providers during zoom or pan.
// Failed tiles can be retried by reloading the page without disturbing map markers.
if(window.L){
  map=L.map('map',{zoomAnimation:true,markerZoomAnimation:true}).setView([39,-97],4);
  const tileNotice=document.createElement('p');
  tileNotice.setAttribute('role','status');
  tileNotice.setAttribute('aria-live','polite');
  tileNotice.style.cssText='font-size:13px;color:#f0c96b;margin:7px 0';
  document.getElementById('map').insertAdjacentElement('afterend',tileNotice);
  const baseTiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution:'&copy; OpenStreetMap contributors',
    maxZoom:19, tileSize:256, zoomOffset:0, updateWhenIdle:true, crossOrigin:true
  });
  let tileErrors=0;
  baseTiles.on('tileerror',()=>{
    tileErrors++;
    if(tileErrors>=3)tileNotice.textContent='Some map tiles did not load. Check your internet connection or content blocker, then refresh the page.';
  });
  baseTiles.on('load',()=>{tileErrors=0;tileNotice.textContent='';});
  const baseMaps={'Street':baseTiles,
   'Terrain':L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'&copy; OpenTopoMap (CC-BY-SA), &copy; OpenStreetMap contributors'}),
   'Satellite':L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Imagery &copy; Esri, Maxar, Earthstar Geographics'})};
  let wantBase='Street';try{wantBase=localStorage.getItem('kpcBaseMap')||'Street'}catch(_){}
  (baseMaps[wantBase]||baseTiles).addTo(map);
  L.control.layers(baseMaps,null,{position:'topright',collapsed:true}).addTo(map);
  map.on('baselayerchange',e=>{try{localStorage.setItem('kpcBaseMap',e.name)}catch(_){}});
  layer=L.layerGroup().addTo(map);
  window.addEventListener('load',()=>map.invalidateSize({animate:false}));
}else{status.textContent='Map library could not load; search results can still work.'}
const rad=n=>n*Math.PI/180;
function miles(a,b,c,d){const dl=rad(c-a),dn=rad(d-b),h=Math.sin(dl/2)**2+Math.cos(rad(a))*Math.cos(rad(c))*Math.sin(dn/2)**2;return 3958.7613*2*Math.asin(Math.min(1,Math.sqrt(h)))}
function node(tag,cls,txt){const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e}
function link(label,url){const a=node('a','',label);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a}

/* KPC additions: Kentucky guide data (county, park type), Maidenhead grid, shortcuts, remembered search */
let kyGuide=new Map();fetch('kpc-ky-data.json').then(r=>r.ok?r.json():null).then(j=>{if(!j)return;for(const p of j.parks||[])kyGuide.set(p.c,p);for(const p of j.summits||[])kyGuide.set(p.c,p);for(const p of j.kff||[])kyGuide.set(p.c,p);if(data.length)render()}).catch(()=>{});
function grid6(lat,lon){lat=Number(lat)+90;lon=Number(lon)+180;if(!(lat>=0&&lat<=180&&lon>=0&&lon<=360))return '';const A='ABCDEFGHIJKLMNOPQR',a='abcdefghijklmnopqrstuvwx';const f1=Math.floor(lon/20),f2=Math.floor(lat/10),s1=Math.floor((lon%20)/2),s2=Math.floor(lat%10),t1=Math.floor((lon%2)*12),t2=Math.floor((lat%1)*24);return A[f1]+A[f2]+s1+s2+a[t1]+a[t2]}
function kyLine(d){const g=grid6(d[3],d[4]),p=kyGuide.get(d[1]);let co='';if(p&&p.co&&!/official|see /i.test(p.co)){const l=String(p.co).replace(/\?/g,'').split('/').map(x=>x.trim()).filter(Boolean);co=l.length>3?'Multi-county ('+l.length+' counties)':l.length>1?l.join(' / ')+' counties':l[0]+' County'}return [g?'Grid '+g:'',co].filter(Boolean).join(' · ')}

/* KPC: better card links - directions to a real entrance, park-specific pages, camping, and a guide summary line */
const HOSTLBL=[[/parks\.ky\.gov/,'Kentucky State Parks page'],[/fw\.ky\.gov/,'KDFWR area page'],[/eec\.ky\.gov/,'Nature Preserves page'],[/nps\.gov/,'National Park Service page'],[/fs\.usda\.gov/,'Forest Service page'],[/fws\.gov/,'Fish & Wildlife Service page']];
const hostLabel=(u,def)=>{for(const [r,l] of HOSTLBL)if(r.test(u))return l;return def};
const genericCamp=u=>/parks\.ky\.gov\/(parks\/)?camping\/?$|reserve-a-campground\/?$|parks\.ky\.gov\/?$/i.test(u||'');
const TYPENAME={'WMA':'Wildlife Management Area','National / NPS':'National Park Service site'};
function kyExtras(d,kp,links,card){
 const dest=(la,lo)=>`https://www.google.com/maps/dir/?api=1&destination=${la},${lo}&travelmode=driving`;
 let aps=(d[0]==='POTA'&&kp&&Array.isArray(kp.ap))?kp.ap.filter(a=>Number.isFinite(Number(a[0]))&&Number.isFinite(Number(a[1]))):[];
 if(aps.length&&center)aps=aps.slice().sort((a,b)=>miles(center[0],center[1],a[0],a[1])-miles(center[0],center[1],b[0],b[1]));
 const cnt={},tot={};aps.forEach(a=>{const k=String(a[2]||'access point').trim();tot[k]=(tot[k]||0)+1});const nm=a=>{const k=String(a[2]||'access point').replace(/\s+/g,' ').trim().slice(0,32),kk=String(a[2]||'access point').trim();if(tot[kk]>1){cnt[kk]=(cnt[kk]||0)+1;return k+' #'+cnt[kk]}return k};
 if(aps.length){links.append(link('Directions: '+nm(aps[0]),dest(aps[0][0],aps[0][1])));if(Math.abs(aps[0][0]-d[3])>.002||Math.abs(aps[0][1]-d[4])>.002)links.append(link('Directions: park center',dest(d[3],d[4])))}
 else links.append(link('Directions',dest(d[3],d[4])));
 if(aps.length>1){const o=node('div','meta','Other entrances and parking: ');aps.slice(1,6).forEach((a,i)=>{if(i)o.append(document.createTextNode(' · '));o.append(link(nm(a),dest(a[0],a[1])))});card.append(o)}
 if(!kp||d[0]!=='POTA'||kp.t===undefined)return;
 const info=[TYPENAME[kp.t]||kp.t];if(kp.acc)info.push(kp.acc+' access point'+(kp.acc>1?'s':'')+' on record');
 if(kp.sota&&kp.sota.length)info.push('SOTA summit: '+kp.sota.slice(0,3).join(', ')+(kp.sota.length>3?' +'+(kp.sota.length-3):''));
 if(kp.kff&&kp.kff.length)info.push('KFF: '+kp.kff.slice(0,3).join(', '));
 if(kp.tf&&kp.tf.length)info.push('Linked trail refs: '+kp.tf.slice(0,3).join(', '));
 if(kp.camp)info.push('Camping available');
 card.append(node('div','meta','KPC guide: '+info.join(' · ')));
 const seen=new Set([d[5]]);
 if(kp.web&&!seen.has(kp.web)){seen.add(kp.web);links.append(link(hostLabel(kp.web,'Official park page'),kp.web))}
 if(kp.camp&&!seen.has(kp.camp)){seen.add(kp.camp);links.append(link(genericCamp(kp.camp)?'Camping & reservations (state page)':'Campground page',kp.camp));if(genericCamp(kp.camp))card.append(node('div','meta','The camping link opens the statewide Kentucky State Parks camping page. Pick this park there, or use the park page above.'))}
 if(kp.off&&!seen.has(kp.off)){seen.add(kp.off);links.append(link(/\.pdf(\?|$)/i.test(kp.off)?'Official map (PDF)':'Official map / info',kp.off))}
}
function dedupeLinks(box){const seen=new Set();[...box.querySelectorAll('a')].forEach(a=>{if(seen.has(a.href))a.remove();else seen.add(a.href)})}
const LASTKEY='kpcFinderLast';
function saveLast(){try{const q=$('place').value.trim();if(!center&&!q)return;localStorage.setItem(LASTKEY,JSON.stringify({lat:center?center[0]:null,lon:center?center[1]:null,q,radius:$('radius').value,sota:$('sota').checked,pota:$('pota').checked,wwff:$('wwff').checked,t:Date.now()}))}catch(_){}}
function restoreLast(){try{if(location.search)return false;const v=JSON.parse(localStorage.getItem(LASTKEY)||'null');if(!v)return false;if(['25','50','100','200','500'].includes(String(v.radius)))$('radius').value=String(v.radius);$('sota').checked=!!v.sota;$('pota').checked=!!v.pota;$('wwff').checked=!!v.wwff;$('place').value=v.q||'';
 if(Number.isFinite(v.lat)&&Number.isFinite(v.lon)){center=[v.lat,v.lon];render();status.textContent='Showing your last search'+(v.q?' ('+v.q+')':'')+'. Use GPS or search to change it.';return true}
 if(v.q){town();return true}}catch(_){}return false}
function render(){if(!data.length)return;const radius=Number($('radius').value),on={SOTA:$('sota').checked,POTA:$('pota').checked,WWFF:$('wwff').checked};const ref=$('place').value.trim().toUpperCase();const isRef=/^(?:W\d[A-Z]*\/|US-\d|KFF-\d)/.test(ref);let found=[];const exactRef=isRef&&data.some(d=>on[d[0]]&&d[1].toUpperCase()===ref);for(const d of data){if(!on[d[0]])continue;if(isRef){if(exactRef?d[1].toUpperCase()!==ref:!d[1].toUpperCase().includes(ref))continue;found.push([d,center?miles(center[0],center[1],d[3],d[4]):null]);}else if(center){let distance=miles(center[0],center[1],d[3],d[4]);if(distance<=radius)found.push([d,distance]);}}found.sort((a,b)=>isRef?a[0][1].localeCompare(b[0][1]):a[1]-b[1]);lastMatches=found;const shown=found.slice(0,150);$('count').textContent=(found.length+(isRef&&on.WWFF?unmapped.filter(x=>x[0].includes(ref)).length:0)).toLocaleString()+' found';const items=$('items');items.replaceChildren();if(isRef&&on.WWFF){for(const r of unmapped.filter(x=>x[0].includes(ref)).slice(0,50)){const card=node('article','entry');card.append(node('span','tag wwff','WWFF • '+r[0]),node('h3','',r[1]||r[0]),node('div','meta',[r[2],r[3],'Coordinates not supplied — reference lookup only'].filter(Boolean).join(' · ')));items.append(card)}}if(layer)layer.clearLayers();const bounds=[];for(const [d,dist] of shown){const card=node('article','entry');const tag=node('span','tag '+d[0].toLowerCase(),d[0]+' • '+d[1]);card.append(tag,node('h3','',d[2]));const details=[d[0]==='WWFF'&&d[7]?'Cross-referenced to '+d[7]+' (2025)':'',dist===null?'':dist.toFixed(1)+' mi straight-line',Number.isFinite(Number(d[6]))&&d[0]==='SOTA'&&d[6]!==null?'Elevation '+d[6]+' m':'',kyLine(d),Number(d[3]).toFixed(5)+', '+Number(d[4]).toFixed(5)].filter(Boolean).join(' · ');card.append(node('div','meta',details));const kp=kyGuide.get(d[1]);if(d[0]==='POTA'&&kp&&kp.t==='WMA'){const w=node('div','crossref wma','Public hunting land: check Kentucky Fish & Wildlife season dates and wear blaze orange during gun seasons. ');w.append(link('Hunting seasons','https://fw.ky.gov/Hunt/Pages/ky-hunting-fishing-seasons-planner.aspx'));card.append(w)}if(d[0]==='POTA'&&official2ferEvidence[d[1]]){const e=official2ferEvidence[d[1]];card.append(node('div','crossref','POTA reference review — not a verified POTA 2-fer. '+e.status+'. '+e.evidence+' '+e.caution));}
if(d[0]==='POTA'&&potaWWFF.has(d[1])){const refs=potaWWFF.get(d[1]);card.append(node('div','crossref','WWFF/KFF cross-reference (not a POTA 2-fer). Historical WWFF references (2025): '+refs.join(', ')+'. Verify current program references and eligible boundaries.'))}if(d[0]==='WWFF'&&d[7])card.append(node('div','crossref','WWFF/KFF and POTA cross-reference — not a POTA 2-fer. Historical match (2025); simultaneous activation eligibility not verified.'));const links=node('div','links');if(d[0]==='POTA'&&official2ferEvidence[d[1]]){const e=official2ferEvidence[d[1]];links.append(link(e.map_label,e.map))}links.append(link('Program details',d[5]));kyExtras(d,kp,links,card);links.append(link('Share location',`https://www.google.com/maps/search/?api=1&query=${d[3]},${d[4]}`));if(d[0]==='POTA'&&kp&&kp.t!==undefined){links.append(link('Weather',`kpc-weather.html?lat=${d[3]}&lon=${d[4]}&ref=${encodeURIComponent(d[1])}&name=${encodeURIComponent(d[2])}`),link('Park sheet',`kpc-park-sheet.html?ref=${encodeURIComponent(d[1])}`))}if(d[0]==='POTA'&&officialTrailMaps[d[1]]){const t=officialTrailMaps[d[1]];links.append(link('Official trail map / agency maps',t.url));card.append(node('div','meta',(t.type==='official directory (not park-specific)'?'Agency directory (not a park-specific trail map).':'Official agency resource; map coverage may vary.')+' Verify current routes and activation boundaries.'))}if(d[0]==='POTA'&&officialParkAccess[d[1]]){const access=officialParkAccess[d[1]];if(access.access_url)links.append(link('Official access / trailheads',access.access_url));if(access.camping_url)links.append(link('Official camping information',access.camping_url));if(access.trailheads){const stops=node('div','meta','Official trailhead parking: ');access.trailheads.forEach((t,i)=>{if(i)stops.append(document.createTextNode(' · '));stops.append(link(t.name,`https://www.google.com/maps/search/?api=1&query=${t.lat},${t.lon}`))});card.append(stops)}if(access.note)card.append(node('div','meta',access.note))}dedupeLinks(links);card.append(links);const actions=node('div','saveactions');for(const [kind,label] of [['favorites','Favorite'],['trip','Trip stop']]){const b=node('button','tiny', (saved[kind].includes(key(d))?'✓ ':'+ ')+label);b.type='button';b.setAttribute('aria-pressed',String(saved[kind].includes(key(d))));b.addEventListener('click',()=>toggleSaved(kind,d));actions.append(b)}card.append(actions);items.append(card);if(layer){const pinColor=d[0]==='SOTA'?'#168454':d[0]==='WWFF'?'#b04ae8':'#d5a63a';const pinIcon=L.divIcon({className:'kpc-map-pin',html:'<span style="display:block;width:16px;height:16px;border:2px solid white;border-radius:50%;background:'+pinColor+';box-shadow:0 1px 6px #000c"></span>',iconSize:[16,16],iconAnchor:[8,8]});const mark=L.marker([d[3],d[4]],{icon:pinIcon,title:d[0]+' '+d[1]+' — '+d[2]}).addTo(layer);const popup=node('div');popup.append(node('strong','',d[2]),node('div','',d[1]),link('Directions',`https://www.google.com/maps/dir/?api=1&destination=${d[3]},${d[4]}`));mark.bindPopup(popup);bounds.push([d[3],d[4]])}}if(!shown.length&&!items.children.length)items.append(node('p','empty',center||isRef?'No matching locations. Try a wider radius or another program.':'Use GPS or enter a town to begin.'));if(map){if(bounds.length)map.fitBounds(bounds,{padding:[30,30],maxZoom:11});else if(center)map.setView(center,9)}saveLast();status.textContent=found.length>150?`Showing the nearest 150 of ${found.length.toLocaleString()} matches on the map and list.`:`${found.length.toLocaleString()} matching locations.`}
async function town(){const value=$('place').value.trim();if(!value){status.textContent='Enter a town, state, ZIP, or reference number.';return}if(/^(?:W\d[A-Z]*\/|US-\d|KFF-\d)/i.test(value)){render();return}status.textContent='Looking up town…';$('town').disabled=true;try{if(requestController)requestController.abort();requestController=new AbortController();const res=await fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=us&q='+encodeURIComponent(value),{signal:requestController.signal});if(!res.ok)throw Error('Town lookup unavailable');const j=await res.json();if(!j.length){status.textContent='Town not found. Try including the state abbreviation.';return}center=[Number(j[0].lat),Number(j[0].lon)];render()}catch(e){if(e.name!=='AbortError')status.textContent='Town lookup failed. Please retry.'}finally{$('town').disabled=false}}
$('town').addEventListener('click',town);$('place').addEventListener('keydown',e=>{if(e.key==='Enter')town()});$('gps').addEventListener('click',()=>{if(!navigator.geolocation){status.textContent='GPS is unavailable in this browser.';return}status.textContent='Requesting GPS permission…';navigator.geolocation.getCurrentPosition(p=>{center=[p.coords.latitude,p.coords.longitude];$('place').value='';render();if(map&&window.L){if(userLocationMarker)map.removeLayer(userLocationMarker);userLocationMarker=L.marker(center,{icon:L.divIcon({className:'kpc-user-location',html:'<span></span>',iconSize:[20,20],iconAnchor:[10,10]}),title:'You are here',zIndexOffset:1000}).addTo(map).bindPopup('<strong>You are here</strong><div>Approximate GPS location</div>');userLocationMarker.openPopup();map.setView(center,11,{animate:false});map.invalidateSize();}status.textContent='GPS location found. Blue dot shows your reported location ('+Math.round(p.coords.accuracy)+' m accuracy).';},e=>{status.textContent='Could not get GPS location: '+e.message},{enableHighAccuracy:false,timeout:15000,maximumAge:60000})});['sota','pota','wwff','radius'].forEach(id=>$(id).addEventListener('change',render));
Promise.all([fetch('locations.json').then(r=>{if(!r.ok)throw Error('Missing locations.json');return r.json()}),fetch('wwff-unmapped.json').then(r=>r.ok?r.json():[])]).then(([j,u])=>{data=j;unmapped=u;buildCrossReferences();drawSaved();status.textContent=`Loaded ${data.length.toLocaleString()} mapped SOTA, POTA and WWFF locations. Use GPS or search for a town.`;restoreSearch();if(!center&&!$('place').value.trim())restoreLast()}).catch(()=>{status.textContent='Could not load finder data files. Upload them beside finder.html on an HTTPS website.'});


// Offline exports contain only user-visible program data; no GPS location is transmitted by this feature.
function exportCSV(records,filename){
 const rows=[['Program','Reference','Name','Latitude','Longitude','Details URL','Distance (miles)']];
 for(const [d,dist] of records)rows.push([d[0],d[1],d[2],d[3],d[4],d[5],dist==null?'':dist.toFixed(1)]);
 const content=rows.map(row=>row.map(v=>'"'+String(v??'').replace(/"/g,'""')+'"').join(',')).join('\r\n');
 const blob=new Blob(['\uFEFF',content],{type:'text/csv;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$('exportresults').addEventListener('click',()=>{if(!lastMatches.length){status.textContent='Search for locations before exporting.';return}exportCSV(lastMatches,'activation-search-results.csv')});
$('exporttrip').addEventListener('click',()=>{const matches=saved.trip.map(k=>data.find(d=>key(d)===k)).filter(Boolean).map(d=>[d,null]);if(!matches.length){status.textContent='Add a trip stop before exporting.';return}exportCSV(matches,'activation-trip.csv')});
$('sharesearch').addEventListener('click',async()=>{const url=new URL(location.href);if(center){url.searchParams.set('lat',center[0].toFixed(5));url.searchParams.set('lon',center[1].toFixed(5))}else{url.searchParams.delete('lat');url.searchParams.delete('lon')}url.searchParams.set('radius',$('radius').value);url.searchParams.set('sota',$('sota').checked?'1':'0');url.searchParams.set('pota',$('pota').checked?'1':'0');url.searchParams.set('wwff',$('wwff').checked?'1':'0');if($('place').value.trim())url.searchParams.set('q',$('place').value.trim());else url.searchParams.delete('q');try{if(navigator.share)await navigator.share({title:'Activation Finder',url:url.href});else if(navigator.clipboard){await navigator.clipboard.writeText(url.href);status.textContent='Search link copied.'}else{prompt('Copy this search link',url.href)}}catch(e){if(e.name!=='AbortError')status.textContent='Unable to share this search.'}});
function restoreSearch(){const q=new URLSearchParams(location.search);const radius=q.get('radius');if(['25','50','100','200','500'].includes(radius))$('radius').value=radius;if(q.has('sota'))$('sota').checked=q.get('sota')==='1';if(q.has('pota'))$('pota').checked=q.get('pota')==='1';if(q.has('wwff'))$('wwff').checked=q.get('wwff')==='1';const query=q.get('q');if(query)$('place').value=query;const lat=Number(q.get('lat')),lon=Number(q.get('lon'));if(q.has('lat')&&q.has('lon')&&Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180){center=[lat,lon];render()}else if(query){town()}}

// Trail guide town shortcuts; actual route GIS not included in this package.
document.querySelectorAll(".trailsearch").forEach(button=>button.addEventListener("click",()=>{ $("place").value=button.dataset.town;town();document.querySelector(".resultshead").scrollIntoView({behavior:"smooth",block:"start"});}));

/* KPC: out-of-state visitors can jump to Kentucky */
(function(){const b=document.getElementById('ky-jump');if(!b)return;b.addEventListener('click',()=>{center=[37.84,-85.7];$('place').value='';$('radius').value='200';render();if(map&&window.L)map.setView([37.8,-85.7],7,{animate:false});status.textContent='Showing locations within 200 miles of central Kentucky. Use GPS or search to change it.'})})();

/* KPC: POTA activity (times activated, last activated) - loaded only when a card's button is tapped */
(function(){
 const items=document.getElementById('items');if(!items)return;
 const CK='kpcPotaActivity_v1',TTL=6*3600e3;
 const cache=(()=>{try{return JSON.parse(localStorage.getItem(CK)||'{}')}catch(e){return{}}})();
 const keep=()=>{try{localStorage.setItem(CK,JSON.stringify(cache))}catch(e){}};
 const j=async u=>{const c=new AbortController(),t=setTimeout(()=>c.abort(),12000);try{const r=await fetch(u,{signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}};
 const fmt=s=>{s=String(s||'');const m=s.match(/^(\d{4})-?(\d{2})-?(\d{2})/);if(!m)return s;const d=new Date(Date.UTC(+m[1],+m[2]-1,+m[3],12));const days=Math.round((Date.now()-d)/864e5);const nice=d.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});return nice+(days>=0&&days<400?' ('+(days<1?'today':days===1?'yesterday':days+' days ago')+')':'')};
 async function load(ref){
  const c=cache[ref];if(c&&Date.now()-c.t<TTL)return c;
  const base='https://api.pota.app/park/';
  const [st,ac]=await Promise.all([j(base+'stats/'+ref),j(base+'activations/'+ref+'?count=1').catch(()=>null)]);
  const last=Array.isArray(ac)&&ac[0]?ac[0]:null;
  const r={t:Date.now(),acts:Number(st&&st.activations),attempts:Number(st&&st.attempts),qsos:Number(st&&st.contacts),last:last&&(last.qso_date||last.date||''),by:last&&(last.activeCallsign||last.callsign||'')};
  cache[ref]=r;keep();return r}
 function show(box,r){
  box.textContent='';
  if(!Number.isFinite(r.acts)){box.textContent='No activity data returned for this park.';return}
  const parts=[];
  if(r.acts===0&&!r.last)parts.push('Not activated yet - be the first!');
  else{parts.push('Activated '+r.acts.toLocaleString()+' time'+(r.acts===1?'':'s'));if(r.last)parts.push('last '+fmt(r.last)+(r.by?' by '+r.by:''));if(Number.isFinite(r.qsos)&&r.qsos>0)parts.push(r.qsos.toLocaleString()+' contacts logged')}
  box.textContent=parts.join(' · ')}
 const io='IntersectionObserver' in window?new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){io.unobserve(e.target);e.target.__go&&e.target.__go()}}),{rootMargin:'200px'}):null;
 let busy=0;const q=[];const pump=()=>{while(busy<3&&q.length){const f=q.shift();busy++;f().finally(()=>{busy--;pump()})}};
 function add(card){
  if(card.dataset.act)return;const tag=card.querySelector('.tag.pota');if(!tag)return;
  const m=tag.textContent.match(/US-\d+|[A-Z]{1,2}-\d{3,5}/);if(!m)return;card.dataset.act='1';
  const ref=m[0],wrap=document.createElement('div');wrap.className='meta kpc-act';wrap.style.cssText='margin-top:8px;padding:8px 10px;border-left:3px solid #d5a63a;background:rgba(213,166,58,.08)';
  const out=document.createElement('span');out.textContent='POTA activity: loading...';
  const b=document.createElement('button');b.type='button';b.className='secondary';b.textContent='Try again';b.style.cssText='display:none;margin-left:8px;padding:6px 10px;font-size:12px';
  const run=()=>new Promise(res=>{q.push(()=>load(ref).then(x=>{show(out,x);out.textContent='POTA activity: '+out.textContent}).catch(()=>{out.textContent='POTA activity could not load (offline or POTA not answering).';b.style.display='inline-block'}).finally(res));pump()});
  b.onclick=()=>{out.textContent='POTA activity: loading...';b.style.display='none';run()};wrap.append(out,b);card.append(wrap);card.__go=run;
  if(io)io.observe(card);else card.__go()}
 const scan=()=>items.querySelectorAll('article.entry').forEach(add);
 new MutationObserver(scan).observe(items,{childList:true});scan();
})();

/* KPC: park-name suggestions - type part of a park, summit or WWFF name and tap a match */
(function(){
 const inp=document.getElementById('place');if(!inp)return;
 const box=document.createElement('div');box.id='kpc-sugg';box.style.cssText='display:none;margin-top:8px;border:1px solid #80632e;border-radius:10px;background:#151515;overflow:hidden';
 const row=inp.closest('.inputrow')||inp.parentElement;row.insertAdjacentElement('afterend',box);
 const norm=s=>String(s||'').toLowerCase().replace(/[^a-z0-9 ]+/g,' ').replace(/\s+/g,' ').trim();
 let idx=null;const build=()=>{if(idx||!data.length)return;idx=data.map(d=>[norm(d[2]),d])};
 const show=()=>{const q=norm(inp.value);box.textContent='';
  if(q.length<3||/^(w\d[a-z]*\/|us-\d|kff-\d)/i.test(inp.value.trim())){box.style.display='none';return}
  build();if(!idx){box.style.display='none';return}
  const words=q.split(' ');const hits=[];
  for(const [n,d] of idx){if(words.every(w=>n.includes(w))){hits.push([n.startsWith(q)?0:n.includes(' '+q)?1:2,d])}}
  hits.sort((a,b)=>a[0]-b[0]||(a[1][0]==='POTA'?0:1)-(b[1][0]==='POTA'?0:1)||String(a[1][2]).localeCompare(String(b[1][2])));
  if(!hits.length){box.style.display='none';return}
  const h=document.createElement('div');h.textContent='Parks and summits matching "'+inp.value.trim()+'" - tap one to open it, or press SEARCH for a town';h.style.cssText='font-size:12px;color:#c9c5bc;padding:8px 12px;border-bottom:1px solid #493d2b';box.append(h);
  hits.slice(0,8).forEach(([,d])=>{const b=document.createElement('button');b.type='button';b.style.cssText='display:block;width:100%;text-align:left;background:none;color:#f5f0e4;border:0;border-bottom:1px solid #2a2418;border-radius:0;padding:11px 12px;font-weight:600;white-space:normal';
   b.textContent=d[2]+'  \u2022  '+d[0]+' '+d[1];b.onclick=()=>{inp.value=d[1];box.style.display='none';center=null;render();try{inp.blur()}catch(_){}};box.append(b)});
  if(hits.length>8){const m=document.createElement('div');m.textContent=(hits.length-8)+' more - keep typing to narrow it down';m.style.cssText='font-size:12px;color:#c9c5bc;padding:8px 12px';box.append(m)}
  box.style.display='block'};
 inp.addEventListener('input',show);inp.addEventListener('keydown',e=>{if(e.key==='Escape')box.style.display='none'});
})();

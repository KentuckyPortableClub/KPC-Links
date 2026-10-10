/* KPC official GIS overlays — trails (live) + official park boundaries (bundled files, live fallback).
   A mapped trail or boundary near a reference does not establish a POTA 2-fer. Always confirm on the agency's official map. */
'use strict';
(()=>{
 const KY='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/';
 const rec=KY+'Ky_Recreational_Trails_WGS84WM/MapServer/';
 const parks=KY+'Ky_State_Parks_Features_WGS84WM/MapServer/';
 /* ---------- TRAILS (loaded live for the current map view) ---------- */
 const sources={
  tears:{name:'Trail of Tears (NPS)',url:'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/TRTE_NHT/FeatureServer/0/query',info:'https://www.nps.gov/trte/planyourvisit/maps.htm',color:'#ef8a98',kind:'line'},
  lewis:{name:'Lewis & Clark (NPS)',url:'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/Lewis_and_Clark_National_Historic_Trail_Congressionally_Designated_Route/FeatureServer/0/query',info:'https://www.nps.gov/lecl/planyourvisit/maps.htm',color:'#5bd5ec',kind:'line'},
  pine:{name:'Pine Mountain State Scenic Trail',file:'ky-pine-mountain.geojson',url:rec+'1/query',info:'https://parks.ky.gov/parks/find-a-park/pine-mountain-state-scenic-trail-7826',color:'#ffc36b',kind:'line'},
  dawkins:{name:'Dawkins Line Rail Trail',file:'ky-dawkins.geojson',url:rec+'3/query',info:'https://parks.ky.gov/parks/find-a-park/dawkins-line-rail-trail-7831',color:'#c7a5ff',kind:'line',filter:/dawkins/i},
  sheltowee:{name:'Sheltowee Trace',file:'ky-sheltowee.geojson',url:rec+'11/query',info:'https://www.fs.usda.gov/dbnf',color:'#6cdb97',kind:'line',filter:/sheltowee/i},
  stateparks:{name:'Kentucky State Park Trails',url:parks+'9/query',info:'https://parks.ky.gov/',color:'#e2c76b',kind:'line'},
  trailheads:{name:'Kentucky State Park Trailheads',url:parks+'0/query',info:'https://parks.ky.gov/',color:'#f5b45d',kind:'point'},
  camping:{name:'Kentucky State Park Campgrounds',url:parks+'6/query',info:'https://parks.ky.gov/',color:'#a5de9b',kind:'point'},
  campsites:{name:'State Park Campsites',url:parks+'1/query',info:'https://parks.ky.gov/',color:'#7fd3c4',kind:'point',minZoom:13},
  lodges:{name:'State Park Lodges',url:parks+'2/query',info:'https://parks.ky.gov/',color:'#ff9f7a',kind:'point'},
  cottages:{name:'State Park Cottages',url:parks+'3/query',info:'https://parks.ky.gov/',color:'#f2a6c8',kind:'point',minZoom:11},
  infosites:{name:'Park Offices & Info',url:parks+'4/query',info:'https://parks.ky.gov/',color:'#f4f1e8',kind:'point'}
 };
 /* ---------- OFFICIAL BOUNDARIES (bundled .geojson first, live state server as fallback) ---------- */
 const live=(svc,id)=>`${KY}${svc}/MapServer/${id}/query?where=1%3D1&outFields=*&outSR=4326&geometryPrecision=5&f=geojson`;
 const bounds={
  bstate:{name:'State Parks',agency:'Kentucky State Parks',file:'ky-state-parks.geojson',live:live('Ky_State_Parks_Features_WGS84WM',8),color:'#2fa84f',info:'https://parks.ky.gov/parks/find-a-park'},
  bwma:{name:'WMAs & Public Hunting Areas',agency:'Kentucky Fish & Wildlife',file:'ky-hunting-areas.geojson',live:live('Ky_Public_Hunting_Areas_WGS84WM',1),color:'#f08a1c',info:'https://fw.ky.gov/hunt/pages/public-land-hunting.aspx'},
  bsnp:{name:'State Nature Preserves',agency:'Kentucky Office of Nature Preserves',file:'ky-nature-preserves.geojson',live:live('Ky_KNP_State_Nature_Preserves_WGS84WM',0),color:'#a25ee0',info:'https://eec.ky.gov/Nature-Preserves/Locations/Pages/default.aspx'},
  bsna:{name:'State Natural Areas',agency:'Kentucky Office of Nature Preserves',file:'ky-natural-areas.geojson',live:live('Ky_KNP_Natural_Areas_WGS84WM',0),color:'#e2559f',info:'https://eec.ky.gov/Nature-Preserves/Locations/Pages/default.aspx'},
  bdbnf:{name:'Daniel Boone National Forest',agency:'U.S. Forest Service',file:'ky-dbnf.geojson',live:live('Ky_DBNF_Boundary_Polygon_WGS84WM',0),color:'#2f7fd6',info:'https://www.fs.usda.gov/r08/danielboone',note:'This is the forest’s outer (proclamation) boundary — it includes private land, towns and other parks. Check land ownership on the Forest Service map before activating.'},
  bnps:{name:'National Park Service',agency:'National Park Service',file:'ky-nps.geojson',live:'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2/query?where=STATE%3D%27KY%27&outFields=UNIT_NAME&outSR=4326&f=geojson',color:'#9b6a3c',info:'https://www.nps.gov/state/ky/index.htm'},
  bwild:{name:'Wild River Corridors',agency:'Kentucky Office of Nature Preserves',file:'ky-wild-rivers.geojson',live:live('Ky_KNP_Wild_River_Corridors_WGS84WM',0),color:'#16b3c0',info:'https://eec.ky.gov/Nature-Preserves/conserving_natural_areas/wild-rivers/Pages/default.aspx'},
  bwilder:{name:'Wilderness Areas',agency:'U.S. Forest Service',file:'ky-wilderness.geojson',live:'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_Wilderness_01/MapServer/0/query?where=1%3D1&geometry=-84.9%2C36.5%2C-83.2%2C38.4&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&outSR=4326&geometryPrecision=5&f=geojson',color:'#c6e03a',info:'https://www.fs.usda.gov/r08/danielboone',note:'Federally designated wilderness inside Daniel Boone National Forest — no motorized equipment, and group size limits apply. Check Forest Service rules before setting up.'}
 };
 const $=id=>document.getElementById(id), overlays={}, routes={}, bLayers={}, bData={};
 const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const coarse=window.matchMedia&&matchMedia('(pointer:coarse)').matches;
 function flatten(g){if(g.paths)return g.paths;if(g.type==='LineString')return[g.coordinates];if(g.type==='MultiLineString')return g.coordinates;return []}
 function getName(f){const p=f.attributes||f.properties||{};const keys=['trl_Name','TRAIL_NAME','TRAILNAME','TRAIL','ROUTE_NAME','PARK_NAME','PARKNAME','PARK_NM','PARK','AREA_NAME','AREANAME','WMA_NAME','PROP_NAME','PROPERTY','PRES_NAME','PRESERVE','UNIT_NAME','UNITNAME','WILDERNESSNAME','WILDERNESS_NAME','FOREST','FORESTNAME','RIVER','RIVER_NAME','FACILITY','FACILITY_NAME','SITE_NAME','SITENAME','LABEL','NAME','SiteName','DESCRIPTION'];for(const key of keys){const found=Object.keys(p).find(k=>k.toLowerCase()===key.toLowerCase());if(found&&p[found]!=null&&String(p[found]).trim())return String(p[found]).trim()}return nameGuess(p)}
 /* ---------- shared geometry helpers ---------- */
 function ringsOf(g){if(!g)return[];if(g.type==='Polygon')return[g.coordinates];if(g.type==='MultiPolygon')return g.coordinates;if(g.rings)return[g.rings];return[]}
 function inRing(x,y,r){let ins=false;for(let i=0,j=r.length-1;i<r.length;j=i++){const xi=r[i][0],yi=r[i][1],xj=r[j][0],yj=r[j][1];if((yi>y)!==(yj>y)&&x<(xj-xi)*(y-yi)/(yj-yi+1e-15)+xi)ins=!ins}return ins}
 function inside(lat,lon,g){for(const poly of ringsOf(g)){if(!poly.length||!inRing(lon,lat,poly[0]))continue;if(poly.slice(1).some(h=>inRing(lon,lat,h)))continue;return true}return false}
 function segDistKm(lat,lon,pts){let best=Infinity;const sx=111.195*Math.cos(lat*Math.PI/180),sy=111.195;for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i],dx=(b[0]-a[0])*sx,dy=(b[1]-a[1])*sy,x=(lon-a[0])*sx,y=(lat-a[1])*sy,t=Math.max(0,Math.min(1,(x*dx+y*dy)/((dx*dx+dy*dy)||1)));best=Math.min(best,Math.hypot(x-t*dx,y-t*dy))}return best}
 function edgeKm(lat,lon,g){let best=Infinity;for(const poly of ringsOf(g))for(const r of poly)best=Math.min(best,segDistKm(lat,lon,r));return best}
 function bbox(g){let a=[180,90,-180,-90];for(const poly of ringsOf(g))for(const r of poly)for(const[x,y]of r){if(x<a[0])a[0]=x;if(y<a[1])a[1]=y;if(x>a[2])a[2]=x;if(y>a[3])a[3]=y}return a}
 const mi=km=>km*0.621371, fmtMi=km=>{const m=mi(km);return m<0.1?`${Math.round(m*5280)} ft`:`${m.toFixed(m<10?1:0)} mi`};
 /* ---------- KPC guide data (official map links, park names) ---------- */
 let guide=null;const guideReady=fetch('kpc-ky-data.json').then(r=>r.ok?r.json():null).then(j=>{if(j)guide=new Map(j.parks.map(p=>[p.c,p]))}).catch(()=>{});
 const potaPts=()=>(typeof data!=='undefined'&&Array.isArray(data))?data.filter(d=>d[0]==='POTA'&&Number.isFinite(d[3])&&Number.isFinite(d[4])):[];
 const norm=s=>String(s||'').toLowerCase().replace(/wildlife management area|state nature preserve|state natural area|state resort park|state historic site|state park|national forest|wma|snp|sna|the |[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();

 const ALIAS={"Clifty Wilderness": ["US-3801"], "Big South Fork National River and Recreation Area": ["US-0686"], "Bad Branch Wild River": ["US-10112"], "Big South Fork Wild River": ["US-10107"], "Cumberland River Wild River": ["US-10103"], "Green River Wild River": ["US-10105"], "Rock Creek Wild River": ["US-10111"], "Red River Wild River": ["US-10104"], "Rockcastle River Wild River": ["US-10106"], "Little South Fork Wild River": ["US-7962"], "Mammoth Cave National Park": ["US-0050"], "Abraham Lincoln Birthplace National Historical Park": ["US-0724"], "Camp Nelson National Monument": ["US-7950"], "Mill Springs Battlefield National Monument": ["US-7708"], "Cumberland Gap National Historical Park": ["US-0019"], "Fort Donelson National Battlefield": ["US-0703", "US-3790"], "Jefferson National Forest": ["US-4526"], "Pine Mountain State Scenic Trail": ["US-10102"], "Clay WMA": ["US-10124"], "Horsemill Branch WMA": ["US-11274"], "Little Sexton Creek WMA": ["US-12079"], "General Burnside Island State Park": ["US-1257"], "Green River State Natural Area (Rush Island Bottoms)": ["US-12752"], "Green River State Natural Area (Davis Bend)": ["US-12752"], "Dale Hollow Lake State Resort Park": ["US-1278"], "Big Rivers WMA and State Forest": ["US-3796"], "Marion County WMA and State Forest": ["US-3824"], "Miller Welch-Central Kentucky WMA": ["US-3825"], "Vernon-Douglas State Nature Preserve": ["US-7957"], "Dr. William H. Martin State Natural Area": ["US-7964"], "Otter Creek Outdoor Recreation Area": ["US-8144"], "Kentucky Ridge Forest WMA": ["US-10141"], "Tom Dorman State Nature Preserve": ["US-7958"]};
 /* POTA refs that belong to a boundary: reference point inside it, or a close name match */
 function matchPota(f){const g=f.geometry,b=f._bb||(f._bb=bbox(g)),nm=norm(getName(f)),out=new Map();
  for(const d of potaPts()){const[lat,lon]=[d[3],d[4]];
   const nmOk=(()=>{if(nm.length<=4)return false;const dn=norm(d[2]);if(!dn)return false;const sh=dn.length<nm.length?dn:nm,lg=dn.length<nm.length?nm:dn;return dn===nm||(sh.length>6&&lg.startsWith(sh)&&sh.length/lg.length>=.7)})();
   const inBox=lon>=b[0]-.02&&lon<=b[2]+.02&&lat>=b[1]-.02&&lat<=b[3]+.02&&inside(lat,lon,g);
   if(inBox)out.set(d[1],{d,why:nmOk?'name match, reference point inside':'reference point inside'});
   else if(nm.length>4&&lon>=b[0]-.5&&lon<=b[2]+.5&&lat>=b[1]-.5&&lat<=b[3]+.5){const dn=norm(d[2]);if(dn&&!out.has(d[1])){const sh=dn.length<nm.length?dn:nm,lg=dn.length<nm.length?nm:dn;if(dn===nm||(sh.length>6&&lg.startsWith(sh)&&sh.length/lg.length>=.7))out.set(d[1],{d,why:'name match'})}}}
  for(const r of (ALIAS[getName(f)]||[])){if(!out.has(r)){const d=potaPts().find(x=>x[1]===r);if(d)out.set(r,{d,why:'name match (KPC guide link)'})}}
  const v=[...out.values()],isN=x=>x.why.startsWith('name');return v.filter(isN).concat(v.filter(x=>!isN(x)))}
 function refLinks(m){const more=m.length>6?m.length-6:0;m=m.slice(0,6);return m.map(({d,why})=>{const gp=guide&&guide.get(d[1]);return `<div style="margin-top:6px"><a href="https://pota.app/#/park/${encodeURIComponent(d[1])}" target="_blank" rel="noopener">${safe(d[1])}</a> ${safe(d[2])} <span style="color:#68635a;font-size:12px">(${why})</span>${gp&&gp.off?`<br><a href="${safe(gp.off)}" target="_blank" rel="noopener">Official map ↗</a>`:''}${gp&&gp.web&&gp.web!==gp.off?` · <a href="${safe(gp.web)}" target="_blank" rel="noopener">Website ↗</a>`:''}</div>`}).join('')+(more?`<div style="margin-top:6px;font-size:12px">…and ${more} more POTA references inside this boundary.</div>`:'')}
 function boundaryPopup(f,s){const nm=getName(f)||s.name,m=matchPota(f);
  const P=f.properties||{};return `<strong>${safe(nm)}</strong><br><span style="font-size:13px">${safe(P.TYPE||s.name)} • ${safe(s.agency)}${P.ACCESS?' • access: '+safe(P.ACCESS):''}</span>${P.URL?`<br><a href="${safe(P.URL)}" target="_blank" rel="noopener">Official page ↗</a>`:''}${m.length?`<div style="margin-top:6px;font-weight:800">POTA reference${m.length>1?'s':''}:</div>${refLinks(m)}`:'<div style="margin-top:6px">No POTA reference matched to this boundary.</div>'}${s.note?`<div style="margin-top:8px;font-size:12px;font-weight:700">⚠ ${safe(s.note)}</div>`:''}<div style="margin-top:8px;font-size:12px">GIS boundaries can be out of date — confirm on the agency’s official map before activating. <a href="${s.info}" target="_blank" rel="noopener">Agency info ↗</a></div>`}
 async function getBoundary(k){if(bData[k])return bData[k];const s=bounds[k];let j=null,src='KPC copy';
  try{const r=await fetch(s.file,{cache:'force-cache'});if(r.ok)j=await r.json()}catch(_){}
  if(!j||!Array.isArray(j.features)){src='live from state GIS';const ctrl=new AbortController(),t=setTimeout(()=>ctrl.abort(),25000);try{const r=await fetch(s.live,{signal:ctrl.signal});if(!r.ok)throw Error('HTTP '+r.status);j=await r.json();if(j.error)throw Error(j.error.message||'GIS error')}finally{clearTimeout(t)}}
  j.features=(j.features||[]).filter(f=>f.geometry&&ringsOf(f.geometry).length);j._src=src;bData[k]=j;return j}
 function drawBoundary(k,j){const s=bounds[k];const has=f=>(f._pota!==undefined?f._pota:(f._pota=matchPota(f).length>0));const st=f=>has(f)?{color:s.color,weight:coarse?4.5:4,opacity:1,fillColor:s.color,fillOpacity:.3,dashArray:null,className:'kpc-bnd'}:{color:s.color,weight:coarse?3:2.5,opacity:1,fillColor:s.color,fillOpacity:.1,dashArray:'6 6',className:'kpc-bnd'};
 const lay=L.geoJSON(j,{style:st,
   onEachFeature:(f,l)=>{if(!coarse)l.bindTooltip(safe(getName(f)||s.name),{sticky:true,direction:'top',opacity:1,className:'kpc-gis-tooltip'});l.bindPopup(()=>boundaryPopup(f,s),{maxWidth:280});l.on('popupopen',()=>{try{l.closeTooltip()}catch(_){}});l.on('mouseover',function(){this.setStyle({fillOpacity:.34,weight:4.5})});l.on('mouseout',function(){this.setStyle(st(f))})}});return lay}
 async function toggleBoundary(k){const on=$('gis-'+k)?.checked;
  if(!on){if(bLayers[k]){map.removeLayer(bLayers[k]);delete bLayers[k]}bStatus();return}
  setB(`Loading ${bounds[k].name}…`);try{await guideReady;const j=await getBoundary(k);if(!$('gis-'+k).checked)return;if(bLayers[k])map.removeLayer(bLayers[k]);bLayers[k]=drawBoundary(k,j).addTo(map);bLayers[k].bringToBack();if(k!=='bdbnf'&&bLayers.bdbnf)bLayers.bdbnf.bringToBack();if(k!=='bwilder'&&bLayers.bwilder)bLayers.bwilder.bringToFront();bStatus()}
  catch(e){setB(`${bounds[k].name}: unavailable right now (${e.message||'network'}). Try again later.`);$('gis-'+k).checked=false}}

 /* ---------- map legend for active boundary layers ---------- */
 let legend=null;
 function drawLegend(){const on=Object.keys(bLayers);if(!on.length){if(legend){legend.remove();legend=null}return}
  if(!legend){legend=L.control({position:'bottomleft'});legend.onAdd=()=>{const d=L.DomUtil.create('div','kpc-blegend');L.DomEvent.disableClickPropagation(d);return d};legend.addTo(map)}
  legend.getContainer().innerHTML='<button type="button" class="kbl-t" aria-expanded="true">Boundaries legend</button><div class="kbl-b"><b>Official boundaries</b>'+on.map(k=>`<div><i style="background:${bounds[k].color}33;border:2px solid ${bounds[k].color}"></i>${safe(bounds[k].name)}</div>`).join('')+'<div class="k"><i style="border:2px solid #555"></i>Solid = has a POTA reference</div><div class="k"><i style="border:2px dashed #555"></i>Dashed = no POTA reference</div></div>';const c=legend.getContainer(),t=c.querySelector('.kbl-t');if(innerWidth<760&&!c.dataset.seen){c.classList.add('closed');t.setAttribute('aria-expanded','false')}c.dataset.seen=1;t.onclick=()=>{const cl=c.classList.toggle('closed');t.setAttribute('aria-expanded',String(!cl))}}
 const setB=t=>{const e=$('gis-bstatus');if(e)e.textContent=t};
 function bStatus(){drawLegend();const on=Object.keys(bLayers);setB(on.length?on.map(k=>`${bounds[k].name}: ${bData[k].features.length} (${bData[k]._src})`).join(' | ')+' · Tap a boundary for its POTA reference and official map.':'Choose a boundary layer to show official park boundaries.')}
 /* ---------- "Am I inside a park?" ---------- */
 let hereMark=null;
 async function insideCheck(){const out=$('gis-inside');out.innerHTML='Getting your location…';
  const pos=await new Promise(res=>{if(!navigator.geolocation)return res(null);navigator.geolocation.getCurrentPosition(p=>res(p),()=>res(null),{enableHighAccuracy:true,timeout:15000,maximumAge:30000})});
  if(!pos){out.innerHTML='Location unavailable — allow location access for this site and try again.';return}
  const lat=pos.coords.latitude,lon=pos.coords.longitude,acc=Math.round(pos.coords.accuracy||0);
  out.innerHTML='Checking official boundaries…';await guideReady;const hits=[],near=[],fails=[];
  for(const k of Object.keys(bounds)){let j;try{j=await getBoundary(k)}catch(e){fails.push(bounds[k].name);continue}
   for(const f of j.features){const b=f._bb||(f._bb=bbox(f.geometry));const roughKm=Math.max(0,(b[0]-lon)*89,(lon-b[2])*89,(b[1]-lat)*111,(lat-b[3])*111);if(roughKm>40)continue;
    if(inside(lat,lon,f.geometry)){hits.push({k,f,edge:edgeKm(lat,lon,f.geometry)})}else{const d=edgeKm(lat,lon,f.geometry);if(d<40)near.push({k,f,d})}}}
  if(hereMark)map.removeLayer(hereMark);hereMark=L.circleMarker([lat,lon],{radius:9,color:'#fff',weight:3,fillColor:'#1378ff',fillOpacity:1}).addTo(map);map.setView([lat,lon],Math.max(map.getZoom(),13));
  const accNote=acc?` GPS accuracy about ${fmtMi(acc/1000)}.`:'';
  hits.sort((a,b)=>{const ar=x=>(x.f._bb[2]-x.f._bb[0])*(x.f._bb[3]-x.f._bb[1]);return ar(a)-ar(b)}); /* smallest (most specific) boundary first */
  if(hits.length){out.innerHTML=hits.map(h=>{const s=bounds[h.k],all=matchPota(h.f),nm=all.filter(x=>x.why.startsWith('name')),km=(d)=>Math.hypot((d[3]-lat)*111,(d[4]-lon)*89),m=nm.concat(all.filter(x=>!x.why.startsWith('name')).sort((a,b)=>km(a.d)-km(b.d)).slice(0,nm.length?2:3)).map((x,i)=>i>=nm.length&&nm.length?{...x,why:'also inside this boundary'}:x);
    return `<div style="padding:10px 12px;margin:6px 0;background:#123b28;border-left:4px solid #3ecf6e;border-radius:6px"><b style="color:#7ff0a6">✓ INSIDE</b> ${safe(getName(h.f)||s.name)} <span style="opacity:.8">(${safe(s.name)})</span><br><span style="font-size:13px">About ${fmtMi(h.edge)} from the nearest boundary line.${h.edge<0.05?' <b>You are very close to the edge — move further in.</b>':''}${s.note?'<br><b>⚠ '+safe(s.note)+'</b>':''}</span>${m.length?refLinks(m).replace(/color:#68635a/g,'color:#cfcabf'):''}</div>`}).join('')+`<p style="font-size:12px;margin:6px 0 0">${accNote} Boundaries come from official state/federal GIS and may not match POTA’s or the agency’s current map exactly — confirm before you count it.</p>`;
   Object.keys(bounds).forEach(k=>{if(hits.some(h=>h.k===k)&&!bLayers[k]&&$('gis-'+k)){$('gis-'+k).checked=true;bLayers[k]=drawBoundary(k,bData[k]).addTo(map);bLayers[k].bringToBack()}});bStatus()}
  else{near.sort((a,b)=>a.d-b.d);const n=near[0];
   out.innerHTML=`<div style="padding:10px 12px;margin:6px 0;background:#3a1610;border-left:4px solid #e8734a;border-radius:6px"><b style="color:#ffb59a">✕ NOT INSIDE</b> any official boundary on these layers.${n?`<br>Nearest: <b>${safe(getName(n.f)||bounds[n.k].name)}</b> (${safe(bounds[n.k].name)}) — about ${fmtMi(n.d)} away.`:''}</div><p style="font-size:12px;margin:6px 0 0">${accNote} Some POTA parks (federal sites, historic sites, trails, Corps lakes) aren’t in these layers — check the park’s official map.${fails.length?' Could not load: '+safe(fails.join(', '))+'.':''}</p>`}}
 /* ---------- trail drawing ---------- */
 async function query(s,bb){const p=new URLSearchParams({where:'1=1',geometry:bb,geometryType:'esriGeometryEnvelope',inSR:'4326',spatialRel:'esriSpatialRelIntersects',outFields:'*',returnGeometry:'true',outSR:'4326',f:'json'});
  const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),16000);try{const res=await fetch(s.url+'?'+p.toString(),{signal:ctrl.signal});if(!res.ok)throw Error('HTTP '+res.status);const j=await res.json();if(j.error)throw Error(j.error.message||'GIS service error');return j}finally{clearTimeout(timer)}}
 const TREF={sheltowee:'US-11181',pine:'US-10102',dawkins:'US-1253'};
 /* real field names from the Kentucky State Parks GIS layers (MapServer 6 campgrounds, 0 trailheads, 9 trails) */
 const FIELDS={
  camping:{t:['facilityNa'],rows:[['Amp','Electric'],['WaterHookup','Water hookup'],['SewerHookup','Sewer hookup'],['Pets','Pets'],['Waterfront','Waterfront']],link:['link','Campground details / reservations']},
  trailheads:{t:['NAME','TRAIL_NAME'],rows:[['TRAIL_NAME','Trail'],['PARKING','Parking'],['RESTROOMS','Restrooms'],['SHELTER','Shelter'],['PICNIC','Picnic area'],['DESCRIPTN','About']],link:['PHOTOLINK','Photo']},
  campsites:{t:['PARK_NAME'],rows:[['CAMPSITE_NO','Site'],['SITE_TYPE','Type'],['ELECTRIC','Electric'],['WATER','Water'],['SEWER','Sewer'],['PAD_SURFACE','Pad'],['SITE_ACCESS','Access'],['ADA_ACCESS','ADA'],['WATERFRONT','Waterfront'],['COMMENT','Note']],link:['PHT_1_HYPE','Site photo']},
  lodges:{t:['LODGE_NAME','PARK_NAME'],rows:[['PARK_NAME','Park'],['RESTAURANT_NAME','Restaurant'],['NUM_ROOMS','Rooms']],link:['Web_link','Lodge website']},
  cottages:{t:['PARK_NAME'],rows:[['UNIT','Cottage'],['BL_NAME','Building'],['USE_DESCR','Type'],['COMMENT','Note']],link:['PHT_1_HYPE','Photo']},
  infosites:{t:['BL_NAME','PARK_NAME'],rows:[['PARK_NAME','Park'],['PHONE_NUMB','Phone'],['COMMENT','Note']],link:['','']},
  stateparks:{t:['PUBLIC_NAME','TRAIL_NAME'],rows:[['TRAIL_MILE','Length'],['RATING','Difficulty'],['SURFACE','Surface'],['_USES','Open to'],['DOGS','Dogs'],['BLAZE','Blaze'],['DESCRIPTN','About']],link:['HYPERLINK','Trail information']}};
 const yn=v=>{const t=String(v).trim();return /^y(es)?$/i.test(t)?'Yes':/^n(o)?$/i.test(t)?'No':t};
 function fieldVal(P,f){if(f==='_USES'){const u=[['HIKING','hiking'],['BIKING','biking'],['HORSE','horses'],['ATV','ATVs'],['MOTORCYCLE','motorcycles']].filter(([k])=>/^y/i.test(String(P[k]||''))).map(x=>x[1]);return u.join(', ')}
  let v=P[f];if(v==null)return '';v=String(v).trim();if(!v||/^(0|<null>|null|n\/a|unknown|none)$/i.test(v))return '';if(f==='TRAIL_MILE'){const n=Number(v);return n>0?(n<10?n.toFixed(1):Math.round(n))+' mi':''}return yn(v)}

 /* nearest Kentucky State Parks guide entry, so a campground/lodge popup can link to its own park page */
 let KYP=[];fetch('kpc-ky-data.json').then(r=>r.ok?r.json():null).then(j=>{if(j&&j.parks)KYP=j.parks.filter(p=>p.web&&/parks\.ky\.gov/.test(p.web))}).catch(()=>{});
 const llOf=sh=>{try{return sh.getLatLng?sh.getLatLng():(sh.getBounds?sh.getBounds().getCenter():null)}catch(_){return null}};
 function nearPark(ll){if(!ll||!KYP.length)return null;let best=null,bd=1e9;const r=Math.PI/180;for(const p of KYP){const dl=(p.la-ll.lat)*r,dn=(p.lo-ll.lng)*r,h=Math.sin(dl/2)**2+Math.cos(ll.lat*r)*Math.cos(p.la*r)*Math.sin(dn/2)**2,d=3958.8*2*Math.asin(Math.min(1,Math.sqrt(h)));if(d<bd){bd=d;best=p}}return bd<=6?best:null}
 function knownPopup(k,s,P,ll){const F=FIELDS[k];P=P||{};let title='';for(const f of F.t){const v=fieldVal(P,f);if(v){title=v;break}}
  let rows='',nr=0;for(const[f,lab] of F.rows){if(nr>=8)break;const v=fieldVal(P,f);if(!v||v===title||v.length>140)continue;const tel=lab==='Phone'&&/\d{3}.*\d{4}/.test(v)?`<a href="tel:${safe(v.replace(/[^\d+]/g,''))}">${safe(v)}</a>`:safe(v);rows+=`<span class="r"><i>${safe(lab)}:</i> ${tel}</span>`;nr++}
  const lk=F.link[0]?fieldVal(P,F.link[0]):'',url=/^https?:\/\//i.test(lk)?lk:'';
  const gen=/parks\.ky\.gov\/?$|parks\.ky\.gov\/(parks\/)?camping\/?$|reserve-a-campground\/?$/i.test(url);
  const pp=nearPark(ll),a=[];
  if(url)a.push(`<a href="${safe(url)}" target="_blank" rel="noopener noreferrer">${safe(gen?'Statewide camping & reservations':F.link[1])} ↗</a>`);
  if(pp&&pp.web&&pp.web!==url)a.push(`<a href="${safe(pp.web)}" target="_blank" rel="noopener noreferrer">${safe(pp.n)} page ↗</a>`);
  if(ll&&s.kind==='point')a.push(`<a href="https://www.google.com/maps/dir/?api=1&destination=${ll.lat.toFixed(6)},${ll.lng.toFixed(6)}&travelmode=driving" target="_blank" rel="noopener noreferrer">Directions ↗</a>`);
  if(!url&&!(pp&&pp.web))a.push(`<a href="${s.info}" target="_blank" rel="noopener noreferrer">Kentucky State Parks ↗</a>`);
  return `<div class="kpc-pop"><strong>${safe(title||s.name)}</strong>${rows}<span class="lk">${a.join('')}</span><span class="src">${safe(s.name)} (official state GIS)${s.kind==='line'?' · not a POTA 2-fer':''}. Verify before you go.</span></div>`}
 function popup(name,s,P,ll){const kk=Object.keys(sources).find(x=>sources[x]===s);if(kk&&FIELDS[kk])return knownPopup(kk,s,P,ll);if(s.file){const k=Object.keys(sources).find(x=>sources[x]===s),ref=TREF[k];P=P||{};return `<strong>${safe(name||s.name)}</strong>${P.PLACE?`<br><span style="font-size:13px">${safe(P.PLACE)}</span>`:''}<br>POTA: <a href="https://pota.app/#/park/${ref}" target="_blank" rel="noopener">${ref}</a> ${safe(s.name)}<br><a href="${safe(P.URL||s.info)}" target="_blank" rel="noopener">Official trail info ↗</a><div style="margin-top:6px;font-size:12px">Official state GIS line. Possible 2-fers along this trail are listed under the trail checkboxes — confirm both boundaries on the official maps.</div>`}
  return `<div class="kpc-pop"><strong>${safe(name||s.name)}</strong>${featureRows(P,name)}<span class="src">${safe(s.name)} (official state GIS)${s.kind==='line'?' · trail line only, not a POTA 2-fer':''}. Verify current access before you go.</span><a href="${s.info}" target="_blank" rel="noopener noreferrer">Official agency information ↗</a></div>`}
 function label(shape,name,s,P){const title=name||s.name;if(!coarse&&s.kind!=='point')shape.bindTooltip(safe(title),{sticky:true,direction:'top',opacity:1,className:'kpc-gis-tooltip'});shape.bindPopup(()=>popup(name,s,P,llOf(shape)),{maxWidth:260});shape.on('popupopen',()=>{try{shape.closeTooltip()}catch(_){}});return shape}
 function nameGuess(p){for(const k of Object.keys(p||{})){if(!/name|park|label|title|facility|site/i.test(k))continue;const v=p[k];if(typeof v==='string'&&v.trim().length>1&&v.trim().length<=80&&!/^[\d.\s-]+$/.test(v))return v.trim()}return ''}
 const SKIPK=/^(state|facilityid|trailhd_id|trail_id|ma_id|xy_\w+|att_\w+|datemodifd|datecreate|modifydate|createdate|objectid\w*|fid|shape\w*|globalid|gis\w*|created\w*|last_?edit\w*|editor|creator|x|y|lat\w*|lon\w*|st_\w+|\w*_id|id|\w*objectid\w*)$/i;
 function featureRows(P,used){P=P||{};let n=0,out='';for(const k of Object.keys(P)){if(n>=5)break;if(SKIPK.test(k))continue;let v=P[k];if(v==null)continue;v=String(v).trim();if(!v||v==='0'||/^<?null>?$/i.test(v)||v===used||v.length>110)continue;if(/^\d{11,}$/.test(v))continue;
   const lab=k.replace(/_/g,' ').replace(/([a-z])([A-Z])/g,'$1 $2').replace(/\b\w/g,c=>c.toUpperCase());
   out+=/^https?:\/\//i.test(v)?`<span class="r"><i>${safe(lab)}:</i> <a href="${safe(v)}" target="_blank" rel="noopener noreferrer">Open ↗</a></span>`:`<span class="r"><i>${safe(lab)}:</i> ${safe(v)}</span>`;n++}return out}
 function matching(f,s){return !s.filter||s.filter.test(getName(f))}
 function draw(j,s){const layer=L.layerGroup(),lines=[];let n=0;for(const f of j.features||[]){if(!matching(f,s))continue;const g=f.geometry||{},name=getName(f);
   if(s.kind==='line'){for(const pts of flatten(g)){if(pts.length<2)continue;const ll=pts.map(c=>[c[1],c[0]]);
     const vis=L.polyline(ll,{color:s.color,weight:coarse?6:5,opacity:.95,interactive:false});
     const hit=label(L.polyline(ll,{color:s.color,weight:coarse?24:16,opacity:0,interactive:true}),name,s,f.properties||f.attributes); /* wide invisible tap target */
     hit.on('mouseover',()=>vis.setStyle({weight:8}));hit.on('mouseout',()=>vis.setStyle({weight:coarse?6:5}));
     vis.addTo(layer);hit.addTo(layer);lines.push(pts);n++}}
   else if(s.kind==='point'){const pt=g.x!==undefined?[g.y,g.x]:g.type==='Point'?[g.coordinates[1],g.coordinates[0]]:null;if(pt){label(L.circleMarker(pt,{radius:coarse?9:7,color:'#111',weight:2,fillColor:s.color,fillOpacity:.95}),name,s,f.attributes||f.properties).addTo(layer);n++}}}
  return{layer,lines,n}}
 function candidates(){const host=$('gis-candidates');if(!host)return;host.replaceChildren();const keys=Object.keys(routes).filter(k=>sources[k].kind==='line'&&$('gis-'+k)?.checked);if(!keys.length){return}
  for(const k of keys){const tp=trailParks&&trailParks[{sheltowee:'sheltowee',pine:'pine-mountain',dawkins:'dawkins'}[k]];if(!tp)continue;
   const h=document.createElement('p');h.innerHTML=`<b>${safe(tp.name)} (${safe(tp.ref)}) passes through these official boundaries:</b>`;host.append(h);
   for(const r of tp.parks){if(r.boundary===tp.name)continue;const p=document.createElement('p');p.style.margin='3px 0 3px 10px';
    p.innerHTML=`${r.refs.length?r.refs.map(x=>`<a href="https://pota.app/#/park/${encodeURIComponent(x)}" target="_blank" rel="noopener">${safe(x)}</a>`).join(', ')+' — ':''}${safe(r.boundary)} <span style="opacity:.75">(${safe(r.layer)}, about ${r.miles} mi of trail inside)</span>${r.refs.length?' · <b>possible 2-fer</b>':' · no POTA reference'}`;host.append(p)}
   const n=document.createElement('p');n.style.fontSize='.8rem';n.textContent='Measured from official state GIS lines. A possible 2-fer means standing on the trail inside both boundaries — confirm both on the official maps before counting it.';host.append(n)}
  if(keys.every(k=>sources[k].file&&fileTrail[k]))return;
  const ds=potaPts();if(!ds.length){host.textContent='Activation reference database not ready.';return}
  const b=map.getBounds(),results=[];
  for(const d of ds){if(!b.contains([d[3],d[4]]))continue;for(const k of keys){let best=Infinity;for(const pts of routes[k]){if(pts.length<2)continue;best=Math.min(best,segDistKm(d[3],d[4],pts))}if(best<=2)results.push({d,k,best})}}
  results.sort((a,b)=>a.best-b.best);const header=document.createElement('p');header.textContent=`${results.length} POTA-to-trail proximity matches (within 2 km). None verified; a route crossing a park does not itself qualify as two POTA references.`;host.append(header);
  for(const r of results.slice(0,70)){const p=document.createElement('p'),a=document.createElement('a');a.href='https://pota.app/#/park/'+encodeURIComponent(r.d[1]);a.target='_blank';a.rel='noopener noreferrer';a.textContent=r.d[1]+' — '+r.d[2];p.append(a,document.createTextNode(` · ${r.best.toFixed(2)} km from ${sources[r.k].name} · Proximity only; not a POTA 2-fer. Verify boundaries, access and rules.`));host.append(p)}}
 let busy=false,again=false;
 const fileTrail={};let trailParks=null;
 async function bundled(k){const s=sources[k];if(fileTrail[k])return fileTrail[k];try{const r=await fetch(s.file,{cache:'force-cache'});if(!r.ok)throw 0;const j=await r.json();if(!Array.isArray(j.features))throw 0;
   if(!trailParks){try{const t=await fetch('ky-trail-parks.json');trailParks=t.ok?await t.json():{}}catch(_){trailParks={}}}
   const render=draw(j,s);fileTrail[k]=render;return render}catch(_){return null}}
 async function load(){if(typeof map==='undefined'||!map){$('gis-status').textContent='Map unavailable.';return}
  const active=Object.keys(sources).filter(k=>$('gis-'+k)?.checked);for(const k of Object.keys(overlays)){if(!active.includes(k)){map.removeLayer(overlays[k]);delete overlays[k];delete routes[k]}}
  if(!active.length){$('gis-status').textContent='Choose a trail layer — trails load automatically for the area on the map.';candidates();return}
  const reportsB=[];for(const k of active.filter(k=>sources[k].file)){const r=await bundled(k);if(r){if(!map.hasLayer(r.layer))r.layer.addTo(map);overlays[k]=r.layer;routes[k]=r.lines;reportsB.push(`${sources[k].name}: full trail`)}}
  const liveKeys=active.filter(k=>!(sources[k].file&&fileTrail[k]));
  if(!liveKeys.length){$('gis-status').textContent=reportsB.join(' | ')+' · Official state GIS lines — verify on the agency map.';candidates();return}
  if(map.getZoom()<8){$('gis-status').textContent=(reportsB.length?reportsB.join(' | ')+' · ':'')+'Zoom in a little more (level 8+) to load the other selected trails.';candidates();return}
  if(busy){again=true;return}busy=true;const b=map.getBounds(),bb=[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()].join(',');const reports=[];
  try{for(const k of liveKeys){const s=sources[k];if(s.minZoom&&map.getZoom()<s.minZoom){if(overlays[k]){map.removeLayer(overlays[k]);delete overlays[k]}reports.push(`${s.name}: zoom in closer (level ${s.minZoom}+)`);continue}$('gis-status').textContent='Loading '+s.name+'…';try{const j=await query(s,bb),render=draw(j,s);if(overlays[k])map.removeLayer(overlays[k]);render.layer.addTo(map);overlays[k]=render.layer;routes[k]=render.lines;reports.push(`${s.name}: ${render.n}${j.exceededTransferLimit?' (partial; zoom in)':''}`)}catch(e){reports.push(`${s.name}: unavailable (${e.message})`)}}}
  finally{busy=false}
  $('gis-status').textContent=reportsB.concat(reports).join(' | ')+' · Updates as you move the map. Government GIS may change; verify before travel.';candidates();if(again){again=false;load()}}
 let deb;const auto=()=>{clearTimeout(deb);deb=setTimeout(load,650)};
 if(typeof map!=='undefined'&&map){map.on('moveend',()=>{if(Object.keys(sources).some(k=>$('gis-'+k)?.checked))auto()})}
 Object.keys(sources).forEach(k=>$('gis-'+k)?.addEventListener('change',auto));
 Object.keys(bounds).forEach(k=>$('gis-'+k)?.addEventListener('change',()=>toggleBoundary(k)));
 $('gis-load')?.addEventListener('click',load);
 $('gis-inside-btn')?.addEventListener('click',insideCheck);
 /* layers pre-checked in the HTML: draw them once the map exists */
 setTimeout(()=>{Object.keys(bounds).forEach(k=>{if($('gis-'+k)?.checked)toggleBoundary(k)});if(Object.keys(sources).some(k=>$('gis-'+k)?.checked))load()},300);
 window.kpcGIS={bounds,getBoundary,inside,matchPota}; /* exposed for testing */
})();

/* KPC official GIS overlays. A mapped trail near a reference does not establish a POTA 2-fer. */
'use strict';
(()=>{
 const rec='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_Recreational_Trails_WGS84WM/MapServer/';
 const parks='https://kygisserver.ky.gov/arcgis/rest/services/WGS84WM_Services/Ky_State_Parks_Features_WGS84WM/MapServer/';
 const sources={
  tears:{name:'Trail of Tears (NPS)',url:'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/TRTE_NHT/FeatureServer/0/query',info:'https://www.nps.gov/trte/planyourvisit/maps.htm',color:'#ef8a98',kind:'line'},
  lewis:{name:'Lewis & Clark (NPS)',url:'https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/Lewis_and_Clark_National_Historic_Trail_Congressionally_Designated_Route/FeatureServer/0/query',info:'https://www.nps.gov/lecl/planyourvisit/maps.htm',color:'#5bd5ec',kind:'line'},
  pine:{name:'Pine Mountain Trail (Open)',url:rec+'1/query',info:'https://parks.ky.gov/parks/find-a-park/pine-mountain-state-scenic-trail-7826',color:'#ffc36b',kind:'line'},
  dawkins:{name:'Dawkins Line Rail Trail',url:rec+'3/query',info:'https://parks.ky.gov/parks/find-a-park/dawkins-line-rail-trail-7831',color:'#c7a5ff',kind:'line',filter:/dawkins/i},
  sheltowee:{name:'Sheltowee Trace (candidate segments)',url:rec+'11/query',info:'https://www.fs.usda.gov/dbnf',color:'#6cdb97',kind:'line',filter:/sheltowee/i},
  stateparks:{name:'Kentucky State Park Trails',url:parks+'9/query',info:'https://parks.ky.gov/',color:'#e2c76b',kind:'line'},
  trailheads:{name:'Kentucky State Park Trailheads',url:parks+'0/query',info:'https://parks.ky.gov/',color:'#f5b45d',kind:'point'},
  camping:{name:'Kentucky State Park Campgrounds',url:parks+'6/query',info:'https://parks.ky.gov/',color:'#a5de9b',kind:'point'},
  boundaries:{name:'Kentucky State Park Boundaries',url:parks+'8/query',info:'https://parks.ky.gov/',color:'#81b9e7',kind:'polygon'}
 };
 const $=id=>document.getElementById(id), overlays={}, routes={};
 const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function flatten(g){if(g.paths)return g.paths;if(g.type==='LineString')return[g.coordinates];if(g.type==='MultiLineString')return g.coordinates;return []}
 function getName(f){const p=f.attributes||f.properties||{};return p.trl_Name||p.TRL_NAME||p.NAME||p.Name||p.name||p.ParkName||p.PARK_NAME||p.PARK||p.FACILITY||p.SiteName||p.DESCRIPTION||''}
 function matching(f,s){return !s.filter||s.filter.test(getName(f))}
 function distance(lat,lon,pts){let best=Infinity;const sx=111.195*Math.cos(lat*Math.PI/180),sy=111.195;for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i],dx=(b[0]-a[0])*sx,dy=(b[1]-a[1])*sy,x=(lon-a[0])*sx,y=(lat-a[1])*sy,t=Math.max(0,Math.min(1,(x*dx+y*dy)/((dx*dx+dy*dy)||1)));best=Math.min(best,Math.hypot(x-t*dx,y-t*dy))}return best}
 function candidates(){const host=$('gis-candidates');host.replaceChildren();const keys=Object.keys(routes).filter(k=>sources[k].kind==='line'&&$('gis-'+k)?.checked);if(!keys.length){host.textContent='Select a route layer to check nearby POTA references.';return}
  if(typeof data==='undefined'||!Array.isArray(data)){host.textContent='Activation reference database not ready.';return}
  const bounds=map.getBounds(),results=[];
  for(const d of data){if(d[0]!=='POTA'||!Number.isFinite(d[3])||!Number.isFinite(d[4])||!bounds.contains([d[3],d[4]]))continue;
   for(const k of keys){let best=Infinity;for(const pts of routes[k]){if(pts.length<2)continue;best=Math.min(best,distance(d[3],d[4],pts))}if(best<=2)results.push({d,k,best})}
  }
  results.sort((a,b)=>a.best-b.best);const header=document.createElement('p');header.textContent=`${results.length} POTA-to-trail proximity matches (within 2 km). None verified; a route crossing a park does not itself qualify as two POTA references.`;host.append(header);
  for(const r of results.slice(0,70)){const p=document.createElement('p'),a=document.createElement('a');a.href='https://pota.app/#/park/'+encodeURIComponent(r.d[1]);a.target='_blank';a.rel='noopener noreferrer';a.textContent=r.d[1]+' — '+r.d[2];p.append(a,document.createTextNode(` · ${r.best.toFixed(2)} km from ${sources[r.k].name} · Proximity only; not a POTA 2-fer. Verify boundaries, access and rules.`));host.append(p)}
 }
 async function query(s,bbox){const p=new URLSearchParams({where:'1=1',geometry:bbox,geometryType:'esriGeometryEnvelope',inSR:'4326',spatialRel:'esriSpatialRelIntersects',outFields:'*',returnGeometry:'true',outSR:'4326',f:'json'});
  const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),16000);try{const res=await fetch(s.url+'?'+p.toString(),{signal:ctrl.signal});if(!res.ok)throw Error('HTTP '+res.status);const j=await res.json();if(j.error)throw Error(j.error.message||'GIS service error');return j}finally{clearTimeout(timer)}}
 function popup(name,s){return `<strong>${safe(name||s.name)}</strong><br>Official government GIS layer; check source date, current access and agency maps.<br><a href="${s.info}" target="_blank" rel="noopener noreferrer">Official agency information ↗</a><br><b>Trail proximity only — not a POTA 2-fer.</b>`}
 function draw(j,s){const layer=L.layerGroup(),lines=[];let n=0;for(const f of j.features||[]){if(!matching(f,s))continue;const g=f.geometry||{},name=getName(f);if(s.kind==='line'){for(const pts of flatten(g)){if(pts.length<2)continue;L.polyline(pts.map(c=>[c[1],c[0]]),{color:s.color,weight:4,opacity:.9}).bindPopup(popup(name,s)).addTo(layer);lines.push(pts);n++}}
   else if(s.kind==='point'){const pt=g.x!==undefined?[g.y,g.x]:g.type==='Point'?[g.coordinates[1],g.coordinates[0]]:null;if(pt){L.circleMarker(pt,{radius:5,color:s.color,weight:2,fillOpacity:.7}).bindPopup(popup(name,s)).addTo(layer);n++}}
   else if(s.kind==='polygon'){const rings=g.rings||((g.type==='Polygon')?g.coordinates:[]);for(const ring of rings){L.polygon(ring.map(c=>[c[1],c[0]]),{color:s.color,weight:2,fillOpacity:.06}).bindPopup(popup(name,s)).addTo(layer);n++}}
  }return{layer,lines,n}}
 async function load(){if(typeof map==='undefined'||!map){$('gis-status').textContent='Map unavailable.';return}if(map.getZoom()<8){$('gis-status').textContent='Zoom to level 8 or higher, then try again.';return}
  const active=Object.keys(sources).filter(k=>$('gis-'+k)?.checked);for(const k of Object.keys(overlays)){if(!active.includes(k)){map.removeLayer(overlays[k]);delete overlays[k];delete routes[k]}}
  if(!active.length){$('gis-status').textContent='Choose one or more GIS layers.';candidates();return}
  $('gis-load').disabled=true;const b=map.getBounds(),bb=[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()].join(',');const reports=[];
  try{for(const k of active){const s=sources[k];$('gis-status').textContent='Loading '+s.name+'…';try{const j=await query(s,bb),render=draw(j,s);if(overlays[k])map.removeLayer(overlays[k]);render.layer.addTo(map);overlays[k]=render.layer;routes[k]=render.lines;reports.push(`${s.name}: ${render.n}${j.exceededTransferLimit?' (partial; zoom in)':''}`)}catch(e){reports.push(`${s.name}: unavailable (${e.message})`)}}}finally{$('gis-load').disabled=false}
  $('gis-status').textContent=reports.join(' | ')+' · Government GIS may change; verify before travel.';candidates()
 }
 $('gis-load')?.addEventListener('click',load);
})();

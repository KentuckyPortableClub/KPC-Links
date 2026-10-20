/* Parks page: Lewis & Clark National Historic Trail (US-4572) map for Kentucky.
   Layers: NPS trail route (loaded live from the National Park Service), the signed auto tour route
   (ky-lecl-auto.geojson, NPS 2025 centerline), NPS visitor centers, and possible 2-fer spots (ky-lecl-map.json).
   Leaflet loads only when the map scrolls into view. */
(function(){
const box=document.getElementById('lcMap');if(!box)return;
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const NPS='https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/Lewis_and_Clark_National_Historic_Trail_Congressionally_Designated_Route/FeatureServer/0/query?where=1%3D1&geometry=-89.6%2C36.4%2C-81.9%2C39.2&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=Exped_Seg&outSR=4326&geometryPrecision=5&maxAllowableOffset=0.0005&f=geojson';
const gm=(a,b)=>`https://www.google.com/maps/search/?api=1&query=${a},${b}`;
const dir=(a,b)=>`https://www.google.com/maps/dir/?api=1&destination=${a},${b}&travelmode=driving`;
const pota=r=>'https://pota.app/#/park/'+r;
function css(h,i){if(document.querySelector(`link[href="${h}"]`))return;const l=document.createElement('link');l.rel='stylesheet';l.href=h;l.integrity=i;l.crossOrigin='';document.head.append(l)}
function js(s,i){return new Promise((ok,no)=>{if(window.L)return ok();const e=document.createElement('script');e.src=s;e.integrity=i;e.crossOrigin='';e.onload=ok;e.onerror=no;document.head.append(e)})}
let started=false;
async function start(){if(started)return;started=true;const st=document.getElementById('lcMapStat');
 try{css('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css','sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=');
  await js('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js','sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=')}
 catch(e){if(st)st.textContent='The map could not load. Use the links below.';return}
 const map=L.map(box,{scrollWheelZoom:false,tap:true}).setView([37.85,-86.3],7);
 L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
 const lay={route:L.layerGroup().addTo(map),auto:L.layerGroup().addTo(map),vc:L.layerGroup().addTo(map),spots:L.layerGroup().addTo(map)};
 let msg=[];
 // NPS trail route (the Ohio River)
 fetch(NPS).then(r=>r.json()).then(j=>{L.geoJSON(j,{style:{color:'#1f7fb0',weight:5,opacity:.85},onEachFeature:(f,l)=>l.bindPopup(`<b>Lewis &amp; Clark National Historic Trail</b><br>${esc(f.properties.Exped_Seg||'Expedition route')}<br>The trail here is the Ohio River.`)}).addTo(lay.route)}).catch(()=>{msg.push('NPS trail line did not load');show()});
 // auto tour route
 fetch('ky-lecl-auto.geojson',{cache:'force-cache'}).then(r=>r.json()).then(j=>{L.geoJSON(j,{style:{color:'#8a4b16',weight:3,opacity:.9,dashArray:'6 4'},onEachFeature:(f,l)=>l.bindPopup(`<b>Lewis &amp; Clark Auto Tour Route</b><br>${esc(f.properties.NAME)}<br>Signed with brown Lewis and Clark Trail / AUTO TOUR ROUTE signs.`)}).addTo(lay.auto)}).catch(()=>{msg.push('auto tour route did not load');show()});
 // visitor centers and spots
 fetch('ky-lecl-map.json',{cache:'no-cache'}).then(r=>r.json()).then(d=>{
  d.vc.forEach(v=>L.marker([v.la,v.lo],{icon:L.divIcon({className:'',html:'<span class="lcm-vc">★</span>',iconSize:[22,22],iconAnchor:[11,11]}),title:v.n}).bindPopup(`<b>${esc(v.n)}</b><br>NPS Lewis &amp; Clark visitor center${v.pota?`<br>POTA <a href="${pota(v.pota)}" target="_blank" rel="noopener">${v.pota}</a> + <a href="${pota('US-4572')}" target="_blank" rel="noopener">US-4572</a>`:'<br>Not a POTA park'}<br><a href="${esc(v.url)}" target="_blank" rel="noopener">NPS page ↗</a> · <a href="${dir(v.la,v.lo)}" target="_blank" rel="noopener">Directions ↗</a>`).addTo(lay.vc));
  const GUEST=window.KPCGate&&!window.KPCGate.member(); /* Oct 19: guests don't get 2-fer spots yet */
  (GUEST?[]:d.spots).forEach(s=>{const c=s.type==='3-fer'?'#d5a63a':'#1d5a3a';
   L.circleMarker([s.la,s.lo],{radius:7,color:'#fff',weight:2,fillColor:c,fillOpacity:1}).bindPopup(`<b>Possible ${esc(s.type)}</b> (do your own research)<br>${s.refs.map((r,i)=>`<a href="${pota(r)}" target="_blank" rel="noopener">${r}</a> ${esc(s.names[i])}`).join('<br>')}<br><i>${esc(s.what)}</i><br>GPS pins are guides only.<br><a href="${gm(s.la,s.lo)}" target="_blank" rel="noopener">Map ↗</a> · <a href="${dir(s.la,s.lo)}" target="_blank" rel="noopener">Directions ↗</a>`).addTo(lay.spots)})
 }).catch(()=>{msg.push('spots did not load');show()});
 function show(){if(st)st.textContent=msg.length?msg.join(' · ')+'. Use the links below.':''}
 L.control.layers(null,{'Trail route (Ohio River, NPS)':lay.route,'Auto tour route (signed roads)':lay.auto,'NPS visitor centers':lay.vc,...(window.KPCGate&&!window.KPCGate.member()?{}:{'Possible 2-fers & 3-fers':lay.spots})},{collapsed:true}).addTo(map);
 map.on('focus',()=>map.scrollWheelZoom.enable());map.on('blur',()=>map.scrollWheelZoom.disable());
 setTimeout(()=>map.invalidateSize(),200);if(st)st.textContent='';
}
if('IntersectionObserver' in window){const io=new IntersectionObserver(e=>{if(e.some(x=>x.isIntersecting)){io.disconnect();start()}},{rootMargin:'300px'});io.observe(box)}else start();
document.addEventListener('click',e=>{if(e.target.closest('details,.kpc-fold'))setTimeout(()=>{if(box.offsetParent)start()},50)});
})();

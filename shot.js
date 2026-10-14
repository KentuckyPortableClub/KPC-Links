const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1000,height:760},deviceScaleFactor:2});
await p.addInitScript(()=>{localStorage.setItem('kpcCmdLayers',JSON.stringify({'gis-bsnp':true,'gis-bwild':true}));localStorage.setItem('kpcThickLines','1')});
await p.goto('https://kentuckyportableclub.github.io/KPC-Links/finder.html?lat=37.0928&lon=-82.7705&radius=25',{waitUntil:'networkidle'});
await p.waitForTimeout(3000);
for(const id of ['gis-bsnp','gis-bwild'])await p.evaluate(id=>{const i=document.getElementById(id);if(i&&!i.checked){i.checked=true;i.dispatchEvent(new Event('change',{bubbles:true}))}},id);
await p.waitForTimeout(3000);
await p.evaluate(()=>{const m=window.kpcMap;m.fitBounds([[37.060,-82.815],[37.125,-82.725]]);});
await p.waitForTimeout(8000);
const el=await p.$('#map')||await p.$('.leaflet-container');await el.scrollIntoViewIfNeeded();await p.waitForTimeout(2000);
await el.screenshot({path:'bad-branch.png'});
// satellite version
await p.evaluate(()=>{const r=[...document.querySelectorAll('.leaflet-control-layers-base label')].find(l=>/sat|imag/i.test(l.textContent));if(r)r.querySelector('input').click()});
await p.waitForTimeout(8000);await el.screenshot({path:'bad-branch-sat.png'});
console.log(await p.evaluate(()=>[...document.querySelectorAll('.leaflet-control-layers-base label')].map(l=>l.textContent.trim())));
await b.close()})();

const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch();const p=await b.newPage();const reqs=[];
p.on('response',async r=>{const u=r.url();if(/nwr|station/i.test(u)&&!/\.(png|gif|jpg|css)$/.test(u)){let body='';try{body=(await r.text()).slice(0,400000)}catch(e){};reqs.push({u,status:r.status(),ct:r.headers()['content-type'],len:body.length,body})}});
for(const st of ['KY','TN','IN','OH','WV','VA','IL','MO']){await p.goto('https://www.weather.gov/nwr/stations?State='+st,{waitUntil:'networkidle',timeout:90000}).catch(e=>console.log(e.message));await p.waitForTimeout(4000);
 const rows=await p.$$eval('table tr',trs=>trs.map(tr=>[...tr.children].map(td=>td.innerText.trim())));fs.writeFileSync('nwr-'+st+'.json',JSON.stringify(rows));console.log(st,rows.length)}
fs.writeFileSync('nwr-reqs.json',JSON.stringify(reqs.map(r=>({u:r.u,status:r.status,ct:r.ct,len:r.len,head:r.body.slice(0,1500)})),null,1));await b.close()})();

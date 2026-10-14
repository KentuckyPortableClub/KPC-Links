const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('https://noaaweatherradio.org/',{waitUntil:'networkidle',timeout:90000});await p.waitForTimeout(3000);
fs.writeFileSync('nwro.html',await p.content());
const links=await p.$$eval('a,audio,source',as=>as.map(a=>[a.tagName,a.textContent.trim().slice(0,80),a.href||a.src||'']).filter(x=>x[2]));fs.writeFileSync('nwro-links.json',JSON.stringify(links,null,0));
for(const u of ['https://noaaweatherradio.org/howto.php']){try{await p.goto(u,{timeout:60000});fs.writeFileSync('nwro-howto.txt',await p.evaluate(()=>document.body.innerText))}catch(e){}}
// test that a KY stream answers without sign-in
const ky=links.filter(l=>/Frankfort|Owenton/i.test(l[1])||/frankfort|owenton/i.test(l[2]));const out=[];
for(const l of ky){try{const r=await p.request.get(l[2],{timeout:15000,maxRedirects:5,headers:{Range:'bytes=0-2000'}});out.push([l[2],r.status(),r.headers()['content-type']])}catch(e){out.push([l[2],String(e).slice(0,100)])}}
fs.writeFileSync('nwro-test.json',JSON.stringify(out,null,1));await b.close()})();

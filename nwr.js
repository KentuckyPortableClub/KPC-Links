const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:2,timezoneId:'America/Chicago'});const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('https://kentuckyportableclub.github.io/KPC-Links/kpc-community.html?v='+Date.now(),{waitUntil:'networkidle',timeout:90000});await p.waitForTimeout(5000);
await p.evaluate(()=>{const t=document.querySelector('.ks-track');if(t)t.scrollLeft=0});
const el=await p.$('.ks-wrap');if(el)await el.screenshot({path:'ks-live.png'});
require('fs').writeFileSync('ks-live.txt',JSON.stringify({errs,sub:await p.evaluate(()=>{const e=document.querySelector('.ks-sub');return e&&e.textContent}),cards:await p.evaluate(()=>[...document.querySelectorAll('.ks-g')].map(g=>g.innerText.replace(/\n/g,' | ')))},null,1));
const c=await p.$('#cgRv');await b.close()})();

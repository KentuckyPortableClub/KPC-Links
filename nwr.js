const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
const c=await b.newContext({viewport:{width:390,height:844},geolocation:{latitude:36.9685,longitude:-86.4808},permissions:['geolocation']});const p=await c.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('https://kentuckyportableclub.github.io/KPC-Links/kpc-weather.html?v='+Date.now(),{waitUntil:'networkidle',timeout:90000});await p.waitForTimeout(6000);
const v=await p.evaluate(()=>[...document.scripts].map(s=>s.src).filter(s=>s.includes('kpc-weather')).join());
await p.click('.wx-play');await p.waitForTimeout(9000);const m=await p.evaluate(()=>document.getElementById('wxPlNow').textContent);
const el=await p.$('#wxNwr');await el.screenshot({path:'wx-radio.png'});require('fs').writeFileSync('wx-radio.txt',JSON.stringify({v,m,errs}));await b.close()})();

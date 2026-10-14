const {webkit,chromium,devices}=require('playwright');(async()=>{
for(const [eng,name] of [[webkit,'ios'],[chromium,'and']]){const b=await eng.launch();
const c=await b.newContext({...(name==='ios'?devices['iPhone 13']:devices['Pixel 7']),geolocation:{latitude:36.9959,longitude:-85.9119},permissions:['geolocation']});const p=await c.newPage();
await p.goto('https://kentuckyportableclub.github.io/KPC-Links/kpc-weather.html?v='+Date.now(),{waitUntil:'networkidle',timeout:90000});await p.waitForTimeout(7000);
await p.evaluate(()=>document.querySelector('.kpc-header,header')&&(document.querySelectorAll('header')[0].style.position='static'));
const el=await p.$('#wxNwr');await el.screenshot({path:'wx-r-'+name+'.png'});await b.close()}})();

const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1000,height:760},deviceScaleFactor:2});
await p.goto('http://localhost:8000/lb.html');await p.waitForFunction(()=>document.title==='ready',null,{timeout:60000});await p.screenshot({path:'lucy.png'});await b.close()})();

const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:900,height:700}});
for(const i of [0,1,2,3]){await p.goto('http://localhost:8000/pins.html?i='+i);await p.waitForFunction(()=>document.title==='ready',null,{timeout:60000});await p.screenshot({path:'d'+i+'.png'})}await b.close()})();

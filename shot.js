const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:900,height:700}});
for(let i=0;i<4;i++){await p.goto('http://localhost:8000/shot.html?i='+i);await p.waitForFunction(()=>document.title==='ready',null,{timeout:60000});await p.screenshot({path:'d'+i+'.png'})}await b.close()})();

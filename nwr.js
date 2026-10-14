const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:900,height:640}});
for(const k of ['gr','wc','ww']){await p.goto('http://localhost:8000/b2.html?k='+k);await p.waitForFunction(()=>document.title==='ready',null,{timeout:60000});await p.screenshot({path:'b2-'+k+'.png'})}await b.close()})();

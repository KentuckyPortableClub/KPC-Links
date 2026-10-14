const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch();const log=[];
for(const i of [0,1,2,3]){const p=await b.newPage({viewport:{width:900,height:700}});p.on('pageerror',e=>log.push(i+' '+e.message));p.on('console',m=>log.push(i+' console '+m.text()));
try{await p.goto('http://localhost:8000/pins.html?i='+i);await p.waitForFunction(()=>document.title==='ready',null,{timeout:60000})}catch(e){log.push(i+' '+e.message)}
await p.screenshot({path:'d'+i+'.png'});await p.close()}fs.writeFileSync('shotlog.txt',log.join('\n'));await b.close()})();

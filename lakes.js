const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
for(const k of ['bullock','boltz','guist','linville','wilgreen','woodcreek','beaver','kingfisher','carpenter']){const p=await b.newPage({viewport:{width:900,height:640}});
try{await p.goto('http://localhost:8000/lakes.html?k='+k);await p.waitForFunction(()=>document.title==='ready',null,{timeout:60000})}catch(e){console.log(k,e.message)}
await p.screenshot({path:'lake-'+k+'.png'});await p.close()}await b.close()})();

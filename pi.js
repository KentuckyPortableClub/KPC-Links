const {chromium}=require('playwright');const fs=require('fs');(async()=>{const b=await chromium.launch();const log=[];
const B='https://kentuckyportableclub.github.io/KPC-Links/kpc-park-info.html?q=';
for(const [q,n,w] of [['US-2177','yargo',390],['Vogel','vogel',1280],['W4G/NG-001','brass',390],['KFF-1271','kff',390],['DE-0298','de',390]]){const p=await b.newPage({viewport:{width:w,height:1300}});p.on('pageerror',e=>log.push(n+' ERR '+e.message));
await p.goto(B+encodeURIComponent(q));await p.waitForTimeout(9000);
if(n==='vogel'){const x=await p.$('.pi-pick');if(x){await x.click();await p.waitForTimeout(9000)}}
log.push(n+': '+((await p.textContent('#piOut').catch(()=>''))||'').replace(/\s+/g,' ').slice(0,400)+' || list:'+((await p.textContent('#piList'))||'').slice(0,200));
log.push(n+' sw '+await p.evaluate(()=>document.documentElement.scrollWidth));
await p.screenshot({path:'pi-'+n+'.png',fullPage:true});await p.close()}
fs.writeFileSync('pi.txt',log.join('\n'));await b.close()})();

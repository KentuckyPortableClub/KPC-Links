const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage();const log=[];
p.on('console',m=>log.push(m.text()));p.on('requestfailed',r=>log.push('FAIL '+r.url()+' '+r.failure().errorText));
p.on('response',async r=>{if(r.url().includes('espn')){let t='';try{t=(await r.text()).slice(0,300)}catch(e){};log.push(r.status()+' '+r.url()+' '+JSON.stringify(r.headers()['access-control-allow-origin'])+' '+t.slice(0,200))}});
await p.goto('https://kentuckyportableclub.github.io/KPC-Links/kpc-community.html?v='+Date.now(),{waitUntil:'networkidle',timeout:90000});await p.waitForTimeout(5000);
const r=await p.evaluate(async()=>{const j=await (await fetch('https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/96/schedule')).json();return (j.events||[]).slice(-6).map(e=>[e.date,e.name,e.competitions[0].status.type.state])});
require('fs').writeFileSync('ks-live.txt',JSON.stringify({log:log.slice(0,30),r},null,1));await b.close()})();

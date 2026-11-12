/* Nov 10: the website copy of the app logger (logger-beta) says the NEW BUILD is the installed app's, and drops the false 'no internet' clock line.
   Not in kpc_full_suite.py (needs Chromium). Run: python3 -m http.server 8794 &  NODE_PATH=$(npm root -g) node tests/logger_beta_nov10_browser.js */
const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();let fails=0;const ok=(c,m)=>{console.log((c?'  ✓ ':'  ✗ ')+m);if(!c)fails++;};
for(const vp of [[1280,900],[390,844]]){const c=await b.newContext({viewport:{width:vp[0],height:vp[1]}});const P=await c.newPage();const E=[];
P.on('pageerror',e=>E.push(e.message));
await P.route(/version\.json/,r=>r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ver:'0.8.1',when:'2026-11-12',notes:'test',where:'https://example.org/'})}));
await P.route(/worldtimeapi|timeapi/,r=>r.abort());
await P.addInitScript(()=>{localStorage.setItem('kpcVipOK','dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab');localStorage.setItem('kpcUpdLast',JSON.stringify({ver:'0.8.1',when:'2026-11-12',notes:'test notes',where:'https://example.org/'}));});
await P.goto((process.env.BASE||'http://127.0.0.1:8794/')+'logger-beta/kpc-logger-beta.html');await P.waitForTimeout(4000);
const r=await P.evaluate(()=>({upd:(document.getElementById('stUpd')||{}).textContent||'',bar:(document.querySelector('.updbar')||{}).textContent||'',clk:(document.getElementById('stClk')||{}).textContent||'',ver:document.body.innerText.match(/0\.8\.\d/)?1:0}));
console.log(vp[0],JSON.stringify(r).slice(0,400));
ok(/installed KPC app \(Android \/ Windows\) has a newer build/.test(r.upd)&&/updates itself/.test(r.upd),'STATION update line says it is the installed app');
ok(/KPC app \(Android \/ Windows\): new build 0\.8\.1/.test(r.bar),'top bar says KPC app new build');
ok(!/no internet to check against/.test(r.clk),'no false "no internet" clock line: '+r.clk.slice(0,80));
const v=await P.evaluate(()=>{const e=[...document.querySelectorAll('*')].find(x=>x.children.length===0&&/0\.8\.0/.test(x.textContent));return !!e});
ok(!E.length,'no page errors '+E.slice(0,2).join('|'));

await c.close();}
await b.close();console.log(fails?fails+' FAILED':'ALL PASSED');process.exit(fails?1:0);})();

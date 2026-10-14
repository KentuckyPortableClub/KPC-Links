const {chromium}=require('playwright');const S=process.argv[2];
const CSS=`.kpc-utc{flex:0 0 auto;display:inline-flex;align-items:center;gap:5px;height:30px;padding:0 10px;border-radius:15px;border:1px solid rgba(213,166,58,.7);background:rgba(0,0,0,.35);color:#f0c96b;font:800 13px/1 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.5px;white-space:nowrap}
.kpc-utc small{font:700 10px/1 system-ui;color:#cfc6ae;letter-spacing:1px}
@media(max-width:760px){.site-nav .nav-inner .kpc-utc{order:2;margin-left:auto;margin-right:6px}.site-nav .nav-inner .kpc-theme-btn{margin-left:0!important}}
@media(min-width:761px){.site-nav .nav-inner .kpc-utc{margin-left:auto;margin-right:10px}.site-nav .nav-inner .kpc-utc+.kpc-theme-btn{margin-left:0!important}}
.brand-text small.n4w{display:block;margin-top:4px;line-height:0}.brand-text small.n4w img{width:auto;display:block;filter:drop-shadow(0 1px 2px rgba(0,0,0,.8))}`;
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
for(const [w,h] of [[390,140],[1280,90]]) for(const px of [18,22,26]){
  const p=await b.newPage({viewport:{width:w,height:900},deviceScaleFactor:2});
  await p.route('**/__img/*',r=>r.fulfill({path:'/tmp/'+r.request().url().split('/').pop()}));
  await p.goto('http://localhost:8765/index.html',{waitUntil:'networkidle'}).catch(()=>{});await p.waitForTimeout(700);
  await p.evaluate(([css,px])=>{const st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
    const inner=document.querySelector('.site-nav .nav-inner');const tb=inner.querySelector('.kpc-theme-btn');
    const c=document.createElement('span');c.className='kpc-utc';c.innerHTML='23:22 <small>UTC</small>';inner.insertBefore(c,tb);
    const sm=document.querySelector('.brand-text small');sm.className='n4w';sm.innerHTML='<img src="/__img/straight.png" alt="N4KPC" style="height:'+px+'px!important;width:auto!important;max-width:none!important;border-radius:0!important;box-shadow:none!important;border:0!important">';},[CSS,px]);
  await p.waitForTimeout(500);
  const hh=await p.evaluate(()=>document.querySelector('.site-nav').getBoundingClientRect().height);
  const sw=await p.evaluate(()=>document.documentElement.scrollWidth);
  await p.screenshot({path:`${S}/h-${w}-${px}.png`,clip:{x:0,y:0,width:w,height:Math.ceil(hh)}});console.log(w,px,hh,sw);await p.close();}
await b.close();})();

const {chromium}=require('playwright');
const S=process.argv[2];
const CSS=`.kpc-utc{flex:0 0 auto;display:inline-flex;align-items:center;gap:5px;height:30px;padding:0 10px;border-radius:15px;border:1px solid rgba(213,166,58,.7);background:rgba(0,0,0,.35);color:#f0c96b;font:800 13px/1 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.5px;margin-right:8px;white-space:nowrap}
.kpc-utc small{font:700 10px/1 system-ui;color:#cfc6ae;letter-spacing:1px}
@media(max-width:760px){.site-nav .nav-inner .kpc-utc{order:2;margin-left:auto;margin-right:6px}.site-nav .nav-inner .kpc-theme-btn{margin-left:0!important}}
.brand-text small img.n4{height:15px;width:auto;display:block;margin-top:3px;filter:drop-shadow(0 1px 1px #000)}
.hero-n4{display:block;flex:0 1 auto;min-width:0;width:min(560px,86vw);height:auto;margin:0 0 14px;filter:drop-shadow(0 6px 14px rgba(0,0,0,.6))}
@media(min-width:761px){.site-nav .nav-inner .kpc-utc{margin-left:auto;margin-right:10px}.site-nav .nav-inner .kpc-utc+.kpc-theme-btn{margin-left:0!important}}
.hero-brand{display:flex;align-items:center;gap:28px;margin-bottom:14px}.hero-brand .hero-n4{margin:0}
@media(min-width:901px){.hero .hero-brand .hero-logo{display:block!important;position:static!important;transform:none!important;width:230px;margin:0!important;flex:0 0 auto}.hero-brand .hero-n4{width:min(560px,44vw)}}
@media(max-width:900px){.hero-brand{display:block}}`;
async function go(b,w,h,n4,name){
  const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:2});
  await p.route('**/__img/*',r=>r.fulfill({path:'/tmp/'+r.request().url().split('/').pop()}));
  await p.goto('http://localhost:8765/index.html',{waitUntil:'networkidle'}).catch(()=>{});
  await p.waitForTimeout(800);
  await p.evaluate(([css,n4])=>{
    const st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
    const inner=document.querySelector('.site-nav .nav-inner');const tb=inner.querySelector('.kpc-theme-btn');
    const c=document.createElement('span');c.className='kpc-utc';const d=new Date();
    c.innerHTML=String(d.getUTCHours()).padStart(2,'0')+':'+String(d.getUTCMinutes()).padStart(2,'0')+' <small>UTC</small>';
    inner.insertBefore(c,tb||inner.querySelector('.menu-toggle'));
    if(n4){const hi=document.querySelector('.hero-inner');const row=document.createElement('div');row.className='hero-brand';
      const lg=hi.querySelector('.hero-logo');hi.insertBefore(row,lg);row.appendChild(lg);const im=document.createElement('img');im.className='hero-n4';im.src='/__img/arch-outline.png';row.appendChild(im);}
  },[CSS,n4]);
  await p.waitForTimeout(600);
  await p.screenshot({path:S+'/'+name+'.png'});
  const sw=await p.evaluate(()=>document.documentElement.scrollWidth);console.log(name,sw);
  await p.close();
}
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});

await go(b,1280,760,true,'B3-computer-n4kpc');await go(b,1920,1000,true,'B3-wide-n4kpc');await b.close();})();

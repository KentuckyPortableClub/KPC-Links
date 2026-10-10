/* KPC Band Conditions strip: real WSPR signal reports to/from Kentucky (last hour) + NOAA Kp/SFI.
   Mount: <div id="kpc-band-strip"></div>. Data: db1.wspr.live and services.swpc.noaa.gov (both allow browser requests). */
(function(){
const mount=document.getElementById('kpc-band-strip');if(!mount)return;
const KYSQ=['EM56','EM57','EM66','EM67','EM68','EM76','EM77','EM78','EM79','EM86','EM87','EM88','EM89'];
const KYIN="('"+KYSQ.join("','")+"')";
const BANDS=[[1,'160m'],[3,'80m'],[7,'40m'],[10,'30m'],[14,'20m'],[18,'17m'],[21,'15m'],[24,'12m'],[28,'10m'],[50,'6m']];
const BCODES=BANDS.map(b=>b[0]).join(',');
const COL={1:'#8e6bd6',3:'#5b8def',7:'#2dae6e',10:'#7bc043',14:'#f2c230',18:'#f08a1c',21:'#e5533d',24:'#d63b8a',28:'#b04ae8',50:'#e0e0e0'};
const CK='kpcStripCache_v1',MAXAGE=10*60*1000;
const css=document.createElement('style');css.textContent=`
.kbs{background:#0d2419;border-bottom:1px solid rgba(213,166,58,.45);color:#fff;font-family:Arial,Helvetica,sans-serif}
.kbs-in{width:min(1200px,100%);margin:auto;padding:12px 24px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.kbs-t{font-size:12px;font-weight:900;letter-spacing:3px;color:#f0c96b;white-space:nowrap}
.kbs-t small{display:block;margin-top:5px;font-size:11px;font-weight:400;letter-spacing:.2px;color:#cfdad2;white-space:normal;max-width:210px;line-height:1.35}
.kbs-bands{display:flex;gap:6px;flex:1;min-width:0;overflow-x:auto;scrollbar-width:none;padding:2px 0}.kbs-bands::-webkit-scrollbar{display:none}
.kbs-b{flex:0 0 auto;min-width:62px;text-align:center;border:1px solid rgba(255,255,255,.22);border-radius:8px;padding:5px 8px 6px;background:rgba(255,255,255,.04)}
.kbs-b b{display:block;font-size:13px;line-height:1.2}.kbs-b span{display:block;font-size:11px;color:#cfdad2}
.kbs-bar{height:4px;border-radius:2px;margin-top:4px;background:rgba(255,255,255,.12);overflow:hidden}.kbs-bar i{display:block;height:100%}
.kbs-b.hot{border-color:#f0c96b;box-shadow:0 0 0 1px #f0c96b inset}
.kbs-x{font-size:13px;color:#e9eee9}.kbs-x b{color:#fff}
.kbs-a{color:#f0c96b;font-weight:800;font-size:12px;letter-spacing:.6px;text-decoration:none;border:1px solid #80632e;border-radius:6px;padding:8px 11px;white-space:nowrap}
.kbs-a:hover{background:#3c321a}
@media(max-width:640px){.kbs-in{padding:10px 16px}.kbs-t{width:100%}.kbs-t small{max-width:none}.kbs-a{width:100%;text-align:center}}`;
document.head.appendChild(css);
mount.className='kbs';mount.setAttribute('aria-label','Current band conditions');
mount.innerHTML='<div class="kbs-in"><span class="kbs-t">BAND CONDITIONS NOW<small>Signal reports heard in the last hour, to or from Kentucky (WSPR). Bigger number = busier band.</small></span><div class="kbs-bands" id="kbs-bands"><span class="kbs-x">Checking real signal reports…</span></div><span class="kbs-x" id="kbs-x"></span><a class="kbs-a" href="'+(document.getElementById('band-activity')?'#band-activity':'kpc-space-weather.html#band-activity')+'">FULL BAND MAP →</a></div>';
const jget=async(u,ms)=>{const c=new AbortController(),t=setTimeout(()=>c.abort(),ms||15000);try{const r=await fetch(u,{signal:c.signal});if(!r.ok)throw Error('HTTP '+r.status);return await r.json()}finally{clearTimeout(t)}};
async function load(){
 let c=null;try{c=JSON.parse(localStorage.getItem(CK)||'null')}catch(e){}
 if(c&&Date.now()-c.t<MAXAGE)return c;
 const n={t:Date.now(),rows:null,kp:null,sfi:null};
 const sql=`SELECT band, count(*) AS c FROM wspr.rx WHERE time > now() - INTERVAL 60 MINUTE AND band IN (${BCODES}) AND (substring(tx_loc,1,4) IN ${KYIN} OR substring(rx_loc,1,4) IN ${KYIN}) GROUP BY band ORDER BY band FORMAT JSON`;
 await Promise.all([
  jget('https://db1.wspr.live/?query='+encodeURIComponent(sql)).then(j=>n.rows=j.data||[]).catch(()=>{}),
  jget('https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json').then(k=>n.kp=Number(k[k.length-1].Kp)).catch(()=>{}),
  jget('https://services.swpc.noaa.gov/products/summary/10cm-flux.json').then(f=>n.sfi=Number((Array.isArray(f)?f[0]:f).flux)).catch(()=>{})]);
 if(!n.rows&&c)return c;
 try{localStorage.setItem(CK,JSON.stringify(n))}catch(e){}return n}
function draw(d){
 const box=document.getElementById('kbs-bands'),x=document.getElementById('kbs-x');
 if(!d.rows){box.innerHTML='<span class="kbs-x">Live signal reports are not available right now.</span>';return}
 const m={};d.rows.forEach(r=>m[Number(r.band)]=Number(r.c));
 const max=Math.max(1,...Object.values(m));
 const sorted=BANDS.map(b=>[b,m[b[0]]||0]).sort((a,b)=>b[1]-a[1]);const hot=new Set(sorted.filter(s=>s[1]>0).slice(0,2).map(s=>s[0][0]));
 box.innerHTML=BANDS.map(([code,lab])=>{const c=m[code]||0;return `<div class="kbs-b${hot.has(code)?' hot':''}" title="${c} signal reports to or from Kentucky in the last hour"><b>${lab}</b><span>${c?c.toLocaleString():'quiet'}</span><div class="kbs-bar"><i style="width:${Math.max(c?6:0,Math.round(c/max*100))}%;background:${COL[code]}"></i></div></div>`}).join('');
 const bits=[];if(Number.isFinite(d.sfi))bits.push('Solar flux (SFI) <b>'+Math.round(d.sfi)+'</b>');if(Number.isFinite(d.kp))bits.push('Kp <b>'+d.kp.toFixed(d.kp%1?1:0)+'</b> (0-9, lower is calmer)');
 x.innerHTML=bits.join(' · ');try{window.dispatchEvent(new CustomEvent('kpc-bands',{detail:d}))}catch(e){}x.title='SFI = solar flux index, Kp = geomagnetic activity (NOAA). Higher SFI and lower Kp usually mean better HF conditions.'}
load().then(draw).catch(()=>draw({rows:null}));
})();

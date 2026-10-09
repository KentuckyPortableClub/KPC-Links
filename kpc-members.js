/* KPC members-only gate. NOTE: GitHub Pages is public — this keeps casual visitors out, it is not real security.
   To change the password: open any page with ?newpass=YourNewPassword, copy the code it shows, paste it below. */
(function(){
const HASH='af9a50b3b6a03acfaed05b33cd9d2cfec5bd0f3e257745b403928e6930ebcc3c'; // set by the build — see note above
const KEY='kpcMember';
async function sha(t){const b=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(t.trim()));return[...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('')}
const css=`#kpcGate{position:fixed;inset:0;z-index:5000;background:#070707;display:flex;align-items:center;justify-content:center;padding:24px;font-family:Arial,Helvetica,sans-serif}
#kpcGate .box{width:min(420px,100%);padding:34px;background:#111;border:1px solid #d5a63a;box-shadow:12px 12px 0 #d5a63a;color:#fff;text-align:center}
#kpcGate img{width:96px;height:96px;border-radius:50%;object-fit:contain}
#kpcGate .k{margin-top:14px;color:#f0c96b;font-size:12px;font-weight:900;letter-spacing:4px}
#kpcGate h2{margin:8px 0 6px;font:700 30px/1.1 Georgia,serif}#kpcGate p{margin:0 0 18px;color:#bcb8ae;font-size:14px}
#kpcGate input{width:100%;min-height:48px;padding:10px 14px;border:1px solid #444;border-radius:7px;background:#070707;color:#fff;font-size:16px}
#kpcGate button{width:100%;margin-top:12px;min-height:48px;border:0;border-radius:7px;background:#d5a63a;color:#0b0b0b;font-weight:900;letter-spacing:1px;cursor:pointer}
#kpcGate .err{min-height:20px;margin-top:10px;color:#ff8a7a;font-size:13px}#kpcGate a{color:#f0c96b;font-size:13px}
html.kpc-locked body>*:not(#kpcGate){visibility:hidden}`;
const q=new URLSearchParams(location.search);
if(q.get('newpass')){sha(q.get('newpass')).then(h=>{document.addEventListener('DOMContentLoaded',()=>{document.body.innerHTML=`<pre style="padding:30px;font:15px monospace;white-space:pre-wrap">Paste this into kpc-members.js as the HASH value:\n\n${h}</pre>`})});return}
let ok=false;try{ok=localStorage.getItem(KEY)===HASH}catch(e){}
if(ok)return;
document.documentElement.classList.add('kpc-locked');
const st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
document.addEventListener('DOMContentLoaded',()=>{
 const g=document.createElement('div');g.id='kpcGate';
 g.innerHTML=`<form class="box"><img src="KPC-logo.png" alt=""><div class="k">KENTUCKY PORTABLE CLUB</div><h2>Members Only</h2><p>Enter the KPC member password to continue.</p><input type="password" autocomplete="current-password" placeholder="Member password" aria-label="Member password"><button>ENTER</button><div class="err" role="alert"></div><a href="index.html">← Back to KPC home</a></form>`;
 document.body.appendChild(g);const f=g.querySelector('form'),i=g.querySelector('input');i.focus();
 f.onsubmit=async e=>{e.preventDefault();if(await sha(i.value)===HASH){try{localStorage.setItem(KEY,HASH)}catch(_){}g.remove();document.documentElement.classList.remove('kpc-locked');window.dispatchEvent(new Event('resize'))}else{g.querySelector('.err').textContent='That password isn’t right.';i.select()}}});
window.kpcLogout=()=>{try{localStorage.removeItem(KEY)}catch(e){}location.reload()};
})();

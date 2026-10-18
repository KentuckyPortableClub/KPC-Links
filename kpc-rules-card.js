/* KPC shared card: 📋 RULES TO KNOW BEFORE YOU ACTIVATE (POTA, KFF/WWFF, SOTA).
   Mount: <div id="kpc-rules"></div> then this script. Same wording as Park Control's card. */
(function(){
  function go(){
    var m=document.getElementById('kpc-rules'); if(!m||m.dataset.done) return; m.dataset.done='1';
    if(!document.getElementById('kpc-rules-css')){
      var s=document.createElement('style'); s.id='kpc-rules-css';
      s.textContent='#kpc-rules{max-width:1160px;margin:18px auto;padding:0 16px;box-sizing:border-box}'+
      '#kpc-rules .kr{background:#fffdf7;border:1px solid #c9b48a;border-left:5px solid #d5a63a;border-radius:10px;padding:12px 16px;color:#1c1a14;box-shadow:0 0 14px rgba(240,201,107,.25);font-family:Arial,Helvetica,sans-serif;text-align:left}'+
      '#kpc-rules summary{list-style:none;display:flex;justify-content:space-between;align-items:center;gap:8px;cursor:pointer}'+
      '#kpc-rules summary::-webkit-details-marker{display:none}'+
      '#kpc-rules .kr-k{font:800 13px Arial;letter-spacing:.06em;color:#5a3d06}'+
      '#kpc-rules .kr-t{font:800 11px Arial;letter-spacing:.06em;border:1px solid #c9a24a;border-radius:999px;padding:3px 10px;background:linear-gradient(#f6d58a,#d5a63a);color:#2a1a05;white-space:nowrap}'+
      '#kpc-rules .kr[open] .kr-t{font-size:0}#kpc-rules .kr[open] .kr-t::before{content:"CLOSE \\25B4";font-size:11px}'+
      '#kpc-rules .kr-r{margin-top:10px;font-size:.92rem;line-height:1.45}#kpc-rules .kr-r ul{margin:4px 0 0;padding-left:18px}#kpc-rules .kr-r li{margin:2px 0}'+
      '#kpc-rules .kr-n{margin:10px 0 0;font-size:.85rem;color:#5b5446}#kpc-rules a{color:#7a4f00;font-weight:700}'+
      'html[data-theme=dark] #kpc-rules .kr{background:#15130f;border-color:rgba(240,201,107,.6);color:#f1ead8}'+
      'html[data-theme=dark] #kpc-rules .kr-k{color:#f0c96b}html[data-theme=dark] #kpc-rules .kr-n{color:#c9c0aa}html[data-theme=dark] #kpc-rules a{color:#f0c96b}'+
      '@media print{#kpc-rules{display:none}}';
      document.head.appendChild(s);
    }
    var L=function(u,t){return '<a href="'+u+'" target="_blank" rel="noopener">'+t+'</a>';};
    m.setAttribute('data-keep-light','');
    m.innerHTML='<details class="kr"><summary><span class="kr-k">📋 RULES TO KNOW BEFORE YOU ACTIVATE</span><span class="kr-t">OPEN ▾</span></summary>'+
    '<div class="kr-r"><b>🌲 POTA</b><ul><li>You and all your gear must be inside the park\'s boundary and on public property.</li><li>2-fers, 3-fers and more are allowed, but only where every park\'s boundary overlaps, and you and all your gear must be inside that overlap.</li><li>Trail or river parks (with no land boundary of their own): be on public property within 100 ft (30.5 m) of the trail or river.</li><li>10 contacts in one UTC day = a valid activation.</li></ul></div>'+
    '<div class="kr-r"><b>🌳 KFF / WWFF</b><ul><li>You and all your gear (antenna, radio, battery) must be inside the reference area.</li><li>One reference at a time; you can start a second one only after the first is finished.</li><li>44 contacts count toward WWFF awards and can add up over several visits; KFF may accept fewer.</li><li>Operating from your vehicle is OK; send your log to the KFF log manager (activators don\'t upload it themselves).</li></ul></div>'+
    '<div class="kr-r"><b>⛰ SOTA</b><ul><li>Operate inside the activation zone: within 82 ft (25 m) below the summit\'s top.</li><li>No operating from or connected to a vehicle; the last part of the trip up must be on foot (or other non-motor way).</li><li>Portable power only. 1 contact logs the activation; 4 contacts earn the points.</li></ul></div>'+
    '<p class="kr-n">Our short summary, not the official rules. Read them: '+L('https://parksontheair.com/rules/','POTA')+' · '+L('https://wwff.co/wwff_cont/uploads/2025/09/WWFF-Global-Rules-V_5.10.pdf','WWFF')+' · '+L('https://wwff.us/','KFF')+' · '+L('https://www.sota.org.uk/','SOTA')+'.</p></details>';
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',go); else go();
})();

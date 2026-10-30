/* KPC Hunters Lounge: the ⭐ bookmark's real code (Brandon Oct 16 2026). The bookmark itself is a tiny loader:
     javascript:(function(){var s=document.createElement('script');s.src='…/kpc-pota-bm.js?t='+Date.now();document.head.appendChild(s)})()
   so phones can save it (Chrome on Android choked on the long one) and it never needs re-copying when this file changes.
   It runs ON pota.app while you are signed in, asks POTA for your hunted parks, award progress and per-park / per-activator
   counts with pota.app's own sign-in, and hands just those numbers to kpc-hunt.html through window.name. */
(function () {
  var me = document.currentScript && document.currentScript.src;
  var back = 'kpc-hunt.html'; try { var bq = me && new URL(me).searchParams.get('back'); if (bq && /^kpc-[a-z0-9-]+\.html$/.test(bq)) back = bq; } catch (e) {}   /* beta test room: come back to the room */
  var HERE = me ? new URL(back, me).href.split('?')[0] : 'https://kentuckyportableclub.github.io/KPC-Links/' + back;
  /* Oct 30 (Brandon: 'I use Google login to sign into pota'; Google blocks its sign-in inside apps): ?app=1 = the KPC APP's
     bookmark. Same reads, then a button that hands a small summary to the app (kpcapp://pota?z=…, deflate + base64url):
     parks hunted + activated, award numbers, states, awards earned. No sign-in ticket leaves pota.app. */
  var APP = false; try { APP = !!(me && new URL(me).searchParams.get('app')); } catch (e) {}
  function kpcPotaBM(HERE) {
    (async () => {
      try {
        if (!/pota\.app$/.test(location.hostname)) { alert('Open pota.app first (signed in), then tap this bookmark there.'); return; }
        let refs = null, t = '', hunted = null, activated = null;
        try {
          const el = document.querySelector('[data-v-app]') || document.getElementById('app');
          const pin = el && el.__vue_app__ && el.__vue_app__.config.globalProperties.$pinia;
          if (pin) for (const v of Object.values(pin.state.value)) {
            if (v && v.huntedParkRefs && v.huntedParkRefs.size && v.huntedActivatedLoaded) refs = [...v.huntedParkRefs];
            if (v && typeof v.token === 'string' && /^eyJ/.test(v.token)) t = v.token;
          }
        } catch (e) {}
        const jwt = x => { x = String(x || ''); try { x = decodeURIComponent(x); } catch (e) {} const m = x.match(/eyJ[\w-]+\.eyJ[\w-]+\.[\w-]+/); if (!m) return ''; try { const p = JSON.parse(atob(m[0].split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))); return p.token_use === 'id' || p['pota:callsign'] ? m[0] : ''; } catch (e) { return ''; } };
        if (!t) { for (const S of [localStorage, sessionStorage]) for (let i = 0; i < S.length && !t; i++) t = jwt(S.getItem(S.key(i))); if (!t) document.cookie.split(';').forEach(c => { if (!t) t = jwt(c.split('=').slice(1).join('=')); }); }
        if (!refs && !t) { alert('KPC could not find your pota.app sign-in on this page. Make sure you are signed in (your call shows top right), wait for the page to finish loading, then tap the bookmark again.'); return; }
        const H = { headers: { Authorization: t } };
        const G = u => fetch(u, H).then(r => r.ok ? r.json() : null).catch(() => null);
        if (t) { const j = await G('https://api.pota.app/user/stats/hunted_activated_list?type=both'); if (j && j.hunted) { hunted = j.hunted; refs = hunted.map(x => x.reference); activated = j.activated || null; } }
        if (!refs) { alert('POTA did not send your hunted parks. Sign out of pota.app and back in, then try again.'); return; }
        /* award progress, the same calls pota.app's Achievements pages make */
        const aw = { t: Date.now() };
        if (t) {
          const B = 'https://api.pota.app/user/award/progress/';
          const one = ['activator/parks', 'hunter/parks', 'activator/lateshift', 'hunter/lateshift', 'activator/earlyshift', 'hunter/earlyshift', 'activator/p2p', 'hunter/dxentity', 'activator/dxentity'];
          const list = ['hunter/op2op', 'activator/op2op', 'hunter/repeatoffender', 'activator/repeatoffender', 'hunter/n1ccmultiband', 'activator/n1ccmultiband', 'hunter/sixpack', 'activator/sixpack', 'activator/kilos'];
          const r1 = await Promise.all(one.map(k => G(B + k)));
          one.forEach((k, i) => { aw[k] = r1[i]; });
          const r2 = await Promise.all(list.map(k => G(B + k + '?page=1&size=30&sort=closest')));
          list.forEach((k, i) => { let v = r2[i]; const total = v && !Array.isArray(v) ? (v.total ?? v.count ?? null) : null; if (v && !Array.isArray(v)) v = v.data || v.items || v.results || []; aw[k] = { total: total ?? (Array.isArray(v) ? v.length : 0), top: (v || []).slice(0, 30) }; });
          /* how many times you've worked each park and each activator (the numbers pota.app's own spot chips use) + N1CC bands */
          const [pc, ac, n1] = await Promise.all([G('https://api.pota.app/user/stats/hunted_activated_list?type=park_counts'), G('https://api.pota.app/user/stats/hunted_activated_list?type=activator_counts'), G(B + 'hunter/n1ccmultiband')]);
          const flat = o => { const out = {}; if (Array.isArray(o)) o.forEach(x => { const k = x.reference || x.activator || x.callsign, v = x.count ?? x.contacts ?? x.qsos; if (k) out[String(k).toUpperCase()] = +v || 0; }); else if (o && typeof o === 'object') Object.keys(o).forEach(k => { const v = o[k]; out[k.toUpperCase()] = typeof v === 'object' && v ? +(v.count ?? v.contacts ?? 0) : +v || 0; }); return out; };
          aw.pc = flat(pc); aw.ac = flat(ac);
          aw.n1 = {}; (Array.isArray(n1) ? n1 : (n1 && n1.data) || []).forEach(x => { if (x.reference) aw.n1[x.reference] = String(x.bandlist || ''); });
          const e = await G('https://api.pota.app/user/award/earned');
          aw.earned = (e || []).map(x => [x.awardName, x.dateGranted, x.endorsements || '', x.operatorCallsign || x.operator || '', x.reference || '']);
          if (hunted) { const L = {}; hunted.forEach(x => String(x.locationDesc || x.location || x.locations || '').split(',').forEach(l => { l = l.trim(); if (l) L[l] = (L[l] || 0) + 1; })); aw.loc = L; }
          try { const p = JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))); aw.call = p['pota:callsign'] || ''; } catch (e) {}
        }
        if (APP) { await toApp(refs, activated, t ? aw : null); return; }
        const g = {};
        refs.forEach(x => { const m = String(x || '').match(/^([A-Z0-9]+)-(\d+)$/); if (m) (g[m[1]] = g[m[1]] || []).push(+m[2]); });
        /* the data rides along in window.name (no size limit like a web address has), the address just says to look */
        const json = JSON.stringify({ refs: Object.keys(g).map(p => p + '~' + g[p].join('.')).join('_'), n: refs.length, aw: t ? aw : null });
        window.name = 'KPCPOTA:' + json;
        /* iPhone Safari wipes window.name when the page changes sites, so the data ALSO rides in the address, squeezed
           (deflate + base64url, about a fifth of the size). Older browsers without CompressionStream use window.name only. */
        let z = '';
        try {
          if (window.CompressionStream) {
            const buf = await new Response(new Blob([json]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer();
            let bin = ''; const u = new Uint8Array(buf); for (let i = 0; i < u.length; i += 8192) bin += String.fromCharCode.apply(null, u.subarray(i, i + 8192));
            z = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
          }
        } catch (e) { z = ''; }
        location.href = HERE + '#kpcpota' + (z && z.length < 1500000 ? '&z=' + z : '');
      } catch (e) { alert('Could not get your parks: ' + e.message); }
    })();
  }
  /* the KPC app's hand-off: a big button on pota.app (a tap is needed: browsers only open an app from a tap) */
  async function toApp(refs, activated, aw) {
    const grp = L => { const g = {}; (L || []).forEach(x => { const m = String(x || '').toUpperCase().match(/^([A-Z0-9]+)-(\d+)$/); if (m) (g[m[1]] = g[m[1]] || []).push(+m[2]); }); return Object.keys(g).map(p => p + '~' + g[p].join('.')).join('_'); };
    const num = (o, ...k) => { if (o == null) return null; if (typeof o === 'number') return o; for (const x of k) if (o[x] != null && isFinite(+o[x])) return +o[x]; const v = Object.values(o).find(v => typeof v === 'number'); return v == null ? null : v; };
    const P = { v: 1, t: Date.now(), call: aw && aw.call || '', h: grp(refs), a: grp((activated || []).map(x => x.reference)), nh: (refs || []).length, na: (activated || []).length, n: {}, loc: aw && aw.loc || {}, ec: 0, e: [] };
    if (aw) {
      [['hunter/parks', 'numParks'], ['activator/parks', 'numParks'], ['activator/p2p', 'contacts'], ['hunter/dxentity', 'numEntities'], ['activator/dxentity', 'numEntities'], ['hunter/earlyshift', 'contacts'], ['hunter/lateshift', 'contacts'], ['activator/earlyshift', 'contacts'], ['activator/lateshift', 'contacts']]
        .forEach(([k, f]) => { const v = num(aw[k], f, 'parks'); if (v != null) P.n[k] = v; });
      const E = aw.earned || []; P.ec = E.length; P.e = E.slice().sort((a, b) => String(b[1]).localeCompare(String(a[1]))).slice(0, 8);
    }
    let z = '';
    try {
      const buf = await new Response(new Blob([JSON.stringify(P)]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer();
      let bin = ''; const u = new Uint8Array(buf); for (let i = 0; i < u.length; i += 8192) bin += String.fromCharCode.apply(null, u.subarray(i, i + 8192));
      z = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    } catch (e) { alert('This browser is too old to hand your parks to the KPC app. Update Chrome / Edge and try again.'); return; }
    const old = document.getElementById('kpcToApp'); if (old) old.remove();
    const d = document.createElement('div'); d.id = 'kpcToApp';
    d.style.cssText = 'position:fixed;inset:0;z-index:2147483647;background:rgba(10,12,10,.88);display:flex;align-items:center;justify-content:center;padding:16px;font:16px system-ui,sans-serif';
    d.innerHTML = '<div style="background:#141b17;color:#f3ead7;border:2px solid #e3a24a;border-radius:14px;padding:18px;max-width:420px;text-align:center">'
      + '<div style="font-size:20px;font-weight:700;margin-bottom:6px">Your POTA stats are ready</div>'
      + '<div style="margin-bottom:14px">' + P.nh.toLocaleString() + ' parks hunted · ' + P.na.toLocaleString() + ' activated' + (P.ec ? ' · ' + P.ec + ' awards' : '') + '</div>'
      + '<a id="kpcGo" href="kpcapp://pota?z=' + z + '" style="display:block;background:#e3a24a;color:#1a1206;font-weight:700;text-decoration:none;padding:14px;border-radius:10px;font-size:18px">OPEN IN KPC APP</a>'
      + '<div style="font-size:13px;opacity:.8;margin-top:10px">If your browser asks, choose KPC. Only these numbers go to the app; your sign-in stays on pota.app.</div>'
      + '<button id="kpcX" style="margin-top:10px;background:none;border:0;color:#f3ead7;text-decoration:underline;font-size:14px">close</button></div>';
    document.body.appendChild(d);
    document.getElementById('kpcX').onclick = () => d.remove();
  }
  kpcPotaBM(HERE);
})();

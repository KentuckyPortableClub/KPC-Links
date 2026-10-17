/* KPC place suggestions from anywhere in the US (KY Trip Planner + US Trip Planner type-ahead).
   KPCPlace.towns(q)   -> [{v:'Asheville, NC', k:'Town · NC', la, lo, st}]   Open-Meteo geocoding (free, no key, CORS ok;
                          also takes ZIP codes). "Asheville NC" / "Asheville, North Carolina" keep only that state.
   KPCPlace.parks(q)   -> [{v:'Great Smoky Mountains National Park', k:'POTA park · US-0003', ref}]  api.pota.app/lookup
   KPCPlace.park(ref)  -> {la, lo, n} coordinates of one POTA park (looked up when it's picked)
   KPCPlace.box(input, opts) -> a ready-made suggestion list under any input (US planner), opts:
        local(q) -> [{v,k,...}] instant items; remote: true to add towns; parks: true to add POTA parks; onPick(item)  */
(function () {
  'use strict';
  const ST = { Alabama: 'AL', Alaska: 'AK', Arizona: 'AZ', Arkansas: 'AR', California: 'CA', Colorado: 'CO', Connecticut: 'CT', Delaware: 'DE', 'District of Columbia': 'DC', Florida: 'FL', Georgia: 'GA', Hawaii: 'HI', Idaho: 'ID', Illinois: 'IL', Indiana: 'IN', Iowa: 'IA', Kansas: 'KS', Kentucky: 'KY', Louisiana: 'LA', Maine: 'ME', Maryland: 'MD', Massachusetts: 'MA', Michigan: 'MI', Minnesota: 'MN', Mississippi: 'MS', Missouri: 'MO', Montana: 'MT', Nebraska: 'NE', Nevada: 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', Ohio: 'OH', Oklahoma: 'OK', Oregon: 'OR', Pennsylvania: 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', Tennessee: 'TN', Texas: 'TX', Utah: 'UT', Vermont: 'VT', Virginia: 'VA', Washington: 'WA', 'West Virginia': 'WV', Wisconsin: 'WI', Wyoming: 'WY', 'Puerto Rico': 'PR' };
  const AB = new Set(Object.values(ST));
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const cache = {};
  async function jget(u, ms) { const c = new AbortController(), t = setTimeout(() => c.abort(), ms || 8000); try { const r = await fetch(u, { signal: c.signal }); return r.ok ? r.json() : null; } catch (e) { return null; } finally { clearTimeout(t); } }

  /* split a trailing state ("Asheville NC", "Asheville, North Carolina") off the name */
  function split(q) {
    let s = q.trim().replace(/\s+/g, ' '), st = '';
    const m = s.match(/^(.*?)[,\s]+([A-Za-z]{2})$/);
    if (m && AB.has(m[2].toUpperCase())) { s = m[1]; st = m[2].toUpperCase(); }
    else { for (const [n, a] of Object.entries(ST)) { const r = new RegExp('^(.*?)[,\\s]+' + n + '$', 'i'), k = s.match(r); if (k && k[1]) { s = k[1]; st = a; break; } } }
    return { name: s.replace(/,$/, '').trim(), st };
  }
  async function towns(q) {
    const { name, st } = split(q); if (name.length < 2) return [];
    const key = 't|' + name.toLowerCase() + '|' + st; if (cache[key]) return cache[key];
    const j = await jget('https://geocoding-api.open-meteo.com/v1/search?count=10&language=en&format=json&countryCode=US&name=' + encodeURIComponent(name));
    const out = ((j && j.results) || []).map(r => ({ v: r.name + ', ' + (ST[r.admin1] || r.admin1 || ''), k: 'Town · ' + (ST[r.admin1] || r.admin1 || 'US') + (r.admin2 ? ' · ' + r.admin2.replace(/ County$/, '') + ' Co.' : ''), la: r.latitude, lo: r.longitude, st: ST[r.admin1] || '', town: 1 }))
      .filter(r => !st || r.st === st);
    /* KPCPlace.world (US Trip Planner): add towns outside the US when the US has few matches and no state was typed */
    if (P.world && !st && out.length < 4) {
      const w = await jget('https://geocoding-api.open-meteo.com/v1/search?count=8&language=en&format=json&name=' + encodeURIComponent(name));
      ((w && w.results) || []).filter(r => r.country_code !== 'US').slice(0, 6 - out.length).forEach(r => out.push({ v: r.name + ', ' + (r.country || ''), k: 'Town · ' + [r.admin1, r.country].filter(Boolean).join(', '), la: r.latitude, lo: r.longitude, st: '', town: 1 }));
    }
    return (cache[key] = out);
  }
  async function parks(q) {
    if (q.trim().length < 3) return [];
    const key = 'p|' + q.toLowerCase(); if (cache[key]) return cache[key];
    const L = await jget('https://api.pota.app/lookup?search=' + encodeURIComponent(q.trim()) + '&size=60');
    const out = (L || []).filter(x => x.type === 'park' && (P.world || /^US-/.test(x.value))).slice(0, 12).map(x => ({ v: x.display.replace(/^\S+\s+/, ''), k: 'POTA park · ' + x.value, ref: x.value, park: 1 }));
    return (cache[key] = out);
  }
  async function park(ref) {
    const p = await jget('https://api.pota.app/park/' + encodeURIComponent(ref), 10000);
    if (!p || !isFinite(+p.latitude)) return null;
    return { la: +p.latitude, lo: +p.longitude, n: p.name + (p.parktypeDesc && !new RegExp(p.parktypeDesc, 'i').test(p.name) ? ' ' + p.parktypeDesc : ''), st: String(p.locationDesc || '').replace(/^US-/, '').split(',')[0] };
  }

  /* ready-made list for pages without one of their own */
  let cssDone = false;
  function addCss() {
    if (cssDone) return; cssDone = true;
    const s = document.createElement('style');
    s.textContent = '.kps{position:relative}.kps-box{position:absolute;left:0;right:0;top:calc(100% + 3px);z-index:1500;background:#fff;border:1px solid #cbbf9f;border-radius:8px;box-shadow:0 12px 26px rgba(0,0,0,.25);max-height:min(55vh,380px);overflow:auto;text-align:left}' +
      '.kps-box[hidden]{display:none}.kps-box button{display:block;width:100%;padding:9px 12px;border:0;border-bottom:1px solid #eee3cc;background:#fff;color:#171717;font:15px/1.25 Arial,sans-serif;text-align:left;cursor:pointer}' +
      '.kps-box button:hover,.kps-box button.sel{background:#f6efdc}.kps-box b{display:block;font-weight:700}.kps-box small{display:block;font:800 11px Arial,sans-serif;letter-spacing:.5px;color:#1d5a3a;margin-top:2px}' +
      '.kps-box .h{padding:6px 12px;font:900 10px Arial,sans-serif;letter-spacing:1.3px;color:#68635a;background:#f6f2ea}';
    document.head.appendChild(s);
  }
  function box(input, opts) {
    addCss();
    const host = input.parentNode; host.classList.add('kps');
    const b = document.createElement('div'); b.className = 'kps-box'; b.setAttribute('role', 'listbox'); b.hidden = true; host.appendChild(b);
    input.setAttribute('autocomplete', 'off');
    let items = [], sel = -1, seq = 0, t = null;
    const draw = (groups) => {
      items = []; let h = '';
      groups.forEach(([title, list]) => { if (!list.length) return; h += `<div class="h">${esc(title)}</div>`; list.forEach(x => { h += `<button type="button" data-i="${items.length}" role="option"><b>${esc(x.v)}</b><small>${esc(x.k)}</small></button>`; items.push(x); }); });
      b.innerHTML = h; b.hidden = !items.length; sel = -1;
    };
    const run = () => {
      const q = input.value.trim(), my = ++seq; if (q.length < 2) { b.hidden = true; return; }
      const local = opts.local ? opts.local(q) : [];
      draw([['PARKS, SUMMITS & REFERENCES', local]]);
      clearTimeout(t); t = setTimeout(async () => {
        const [tw, pk] = await Promise.all([opts.remote ? towns(q) : [], opts.parks ? parks(q) : []]);
        if (my !== seq) return;
        draw([['TOWNS & ZIP CODES', tw.slice(0, 6)], ['PARKS, SUMMITS & REFERENCES', local], ['POTA PARKS', pk.filter(x => !local.some(y => y.ref === x.ref)).slice(0, 6)]]);
      }, 280);
    };
    input.addEventListener('input', run);
    input.addEventListener('keydown', e => {
      if (b.hidden) return;
      const btns = b.querySelectorAll('button');
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + btns.length) % btns.length; btns.forEach((x, i) => x.classList.toggle('sel', i === sel)); }
      else if (e.key === 'Enter' && sel >= 0) { e.preventDefault(); pick(sel); }
      else if (e.key === 'Escape' || e.key === 'Enter') b.hidden = true;
    });
    const pick = i => { const x = items[i]; if (!x) return; b.hidden = true; seq++; input.value = x.v; opts.onPick && opts.onPick(x); };
    b.addEventListener('mousedown', e => e.preventDefault());
    b.addEventListener('click', e => { const x = e.target.closest('button'); if (x) pick(+x.dataset.i); });
    document.addEventListener('click', e => { if (!host.contains(e.target)) b.hidden = true; });
    return { close: () => { b.hidden = true; } };
  }
  const P = window.KPCPlace = Object.assign(window.KPCPlace || {}, { towns, parks, park, box, ST });
})();

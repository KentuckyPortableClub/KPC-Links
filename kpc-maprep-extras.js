/* Mapping Rep Tool Box extras (Nov 8 2026, Brandon 8:26 AM CST: "1 yes, 2 come up with a solution, 3 same as 2").
   1. KPCMapExtras.clipFC: a huge multi-part outline (e.g. an Army Corps lake WMA stored as one shape) is drawn only for the parts
      near the place in view; the whole shape stays one tap away (and comes back when the rep zooms out).
   2. "Club layers for this state": every KPC layer we hold for the picked state or province, with its source, from the existing
      indexes (answer key, state key layers, land-class layers, trail layers, campgrounds, Virginia birding). Point layers we keep as
      files can be turned on and off on the map. Nothing here queries an agency server.
   3. "Research on this place": read-only notes we already keep for a park (review recommendations, held joins, signed overrides,
      mapping checks, open questions), from the published JSON files.
   No answer key is read for rules or written. */
(function () {
  'use strict';
  const W = typeof window !== 'undefined' ? window : globalThis, D = typeof document !== 'undefined' ? document : null;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const jget = p => ((typeof window !== 'undefined' && window.KPCB && KPCB.jget) ? KPCB.jget(p) : fetch(p).then(r => { if (!r.ok) throw new Error(p); return r.json(); })).catch(() => null);
  const cache = {};
  const once = p => (cache[p] = cache[p] || jget(p));

  /* ---------- 1. clip huge multi-part shapes to the parts near the view ---------- */
  const BIG_PARTS = 25, BIG_POINTS = 20000, NEAR_KM = 40;
  function ringBox(ring) { let a = 180, b = 90, c = -180, d = -90; for (const p of ring) { if (p[0] < a) a = p[0]; if (p[0] > c) c = p[0]; if (p[1] < b) b = p[1]; if (p[1] > d) d = p[1]; } return [a, b, c, d]; }
  function countPts(g) { let n = 0; const walk = x => { if (typeof x[0] === 'number') n++; else x.forEach(walk); }; try { walk(g.coordinates); } catch (e) {} return n; }
  function nearBox(box, la, lo, km) { const dy = km / 111, dx = km / (111 * Math.max(0.2, Math.cos(la * Math.PI / 180))); return !(box[2] < lo - dx || box[0] > lo + dx || box[3] < la - dy || box[1] > la + dy); }
  function clipFC(fc, la, lo, km) {
    let clipped = false;
    const feats = (fc && fc.features || []).map(f => {
      const g = f && f.geometry; if (!g || g.type !== 'MultiPolygon') return f;
      if (g.coordinates.length <= BIG_PARTS && countPts(g) <= BIG_POINTS) return f;
      const keep = g.coordinates.filter(poly => poly && poly[0] && nearBox(ringBox(poly[0]), la, lo, km || NEAR_KM));
      if (!keep.length || keep.length === g.coordinates.length) return f;
      clipped = true;
      return Object.assign({}, f, { properties: Object.assign({}, f.properties, { _clipped: g.coordinates.length - keep.length }), geometry: { type: 'MultiPolygon', coordinates: keep } });
    });
    return { fc: { type: 'FeatureCollection', features: feats }, clipped: clipped };
  }

  /* ---------- 2. Club layers for this state ---------- */
  function placeRow(code) { const G = W.KPCMapLogic; return (G && G.placeByCode && G.placeByCode(code)) || ((G && G.placeRows) ? G.placeRows().find(r => r.code === code) : null); }
  function keyPath(code, region) { return region === 'CA' ? 'data/ca-key/CA-' + code + '.json' : region === 'world' ? 'data/world-key/' + code + '.json' : 'data/us-key/US-' + code + '.json'; }
  const host = u => { try { return new URL(u).hostname.replace(/^www\./, ''); } catch (e) { return String(u || '').slice(0, 40); } };
  async function clubLayers(code) {
    const row = placeRow(code) || { code: code, region: 'US', name: code }, R = row.region || 'US', area = (R === 'CA' ? 'CA-' : R === 'world' ? 'W-' : 'US-') + code;
    const [key, sg, lc, tl, cs, cf, cm] = await Promise.all([once(keyPath(code, R)), once('data/state-gis.json'), once('data/key-layers-landclass-approved.json'), once('data/trails-layers.json'),
      R === 'US' ? once('data/campstate/US-' + code + '.json') : null, R === 'US' ? once('data/campfed/US-' + code + '.json') : null, R === 'US' ? once('data/campstate-manual/US-' + code + '.json') : null]);
    const out = [];
    const P = (key && key.parks) || {}, n = Object.keys(P).length, o = Object.keys(P).filter(r => P[r] && (P[r].m || []).length && P[r].g !== 'pin').length;
    if (n) out.push({ id: 'key', title: 'Park outlines (our answer key)', detail: o + ' of ' + n + ' parks have an official outline', source: 'Official agency and PAD-US records, drawn on each result' });
    ((sg && sg.states && sg.states[code]) || []).forEach((L, i) => out.push({ id: 'sg' + i, title: (L.ds || L.kind || 'layer') + ' · ' + (L.ag || ''), detail: 'Used to build the answer key', source: host(L.url) }));
    ((lc && lc.approved) || []).filter(a => a && a.area === area).forEach((a, i) => out.push({ id: 'lc' + i, title: a.title || 'Land-class layer', detail: 'Land-class layer used to build the answer key', source: host(a.url) }));
    ((tl && tl.layers && tl.layers[code]) || []).forEach((u, i) => out.push({ id: 'tl' + i, title: 'Trail lines', detail: 'Used for trail parks', source: ((tl.credits || {})[u]) || host(u) }));
    const camps = [].concat(((cs && cs.camps) || []).map(c => [c[2], c[3], c[1]]), ((cf && cf.camps) || []).map(c => [c[2], c[3], c[1]]), ((cm && cm.camps) || []).map(c => Array.isArray(c) ? [c[2], c[3], c[1]] : [c.lat, c.lon, c.name]))
      .filter(c => isFinite(c[0]) && isFinite(c[1]));
    if (camps.length) out.push({ id: 'camps', title: 'Campgrounds', detail: camps.length + ' campgrounds (state and federal)', source: [cs && 'state agency layers', cf && 'Recreation.gov', cm && 'hand-checked list'].filter(Boolean).join(', '), pts: camps });
    if (code === 'VA' && R === 'US') out.push({ id: 'vabird', title: 'Virginia Bird & Wildlife Trail sites (US-9935)', detail: 'The trail is its official site points', source: 'Virginia DWR', file: 'data/va-birding-sites.json' });
    return { row: row, layers: out };
  }
  const shown = {};
  async function toggle(L, on) {
    const map = window.KPCMapCheck && KPCMapCheck.map && KPCMapCheck.map(); if (!map || !window.L) return;
    if (shown[L.id]) { map.removeLayer(shown[L.id]); delete shown[L.id]; }
    if (!on) return;
    let pts = L.pts;
    if (!pts && L.file) { const d = await once(L.file); pts = ((d && d.pts) || []).map(p => [p[1], p[0], p[3]]); }
    if (!pts || !pts.length) return;
    const g = window.L.layerGroup();
    pts.forEach(p => window.L.circleMarker([p[0], p[1]], { radius: 4, color: '#2d5440', weight: 1, fillColor: '#3ddc84', fillOpacity: .85 }).bindTooltip(esc(p[2] || '')).addTo(g));
    shown[L.id] = g.addTo(map);
  }
  let lastCode = '';
  async function drawClub(code) {
    const anchor = document.getElementById('mrLayers'); if (!anchor) return;
    let box = document.getElementById('mrClubLayers');
    if (!box) { box = document.createElement('details'); box.id = 'mrClubLayers'; box.className = 'mr-agd'; anchor.insertAdjacentElement('afterend', box); }
    if (code === lastCode && box.dataset.ready) return; lastCode = code;
    Object.keys(shown).forEach(k => toggle({ id: k }, false));
    if (!code) { box.hidden = true; return; }
    const r = await clubLayers(code); box.hidden = !r.layers.length; box.dataset.ready = '1';
    box.innerHTML = '<summary>CLUB LAYERS FOR ' + esc(String(r.row.name || code).toUpperCase()) + ' (' + r.layers.length + ')</summary>' +
      '<p class="mr-help">Everything the club keeps for this place, with its source. Layers kept as files can be turned on here; the others are already part of the park outlines on each result.</p>' +
      r.layers.map(L => '<div class="mr-ag" style="display:block;margin:4px 0">' + ((L.pts || L.file) ? '<label><input type="checkbox" data-club="' + esc(L.id) + '"> ' : '<span>') +
        '<b>' + esc(L.title) + '</b> · ' + esc(L.detail) + ' <small>Source: ' + esc(L.source) + '</small>' + ((L.pts || L.file) ? '</label>' : '</span>') + '</div>').join('');
    box.querySelectorAll('[data-club]').forEach(cb => cb.onchange = () => toggle(r.layers.find(x => x.id === cb.dataset.club), cb.checked));
  }
  if (D) D.addEventListener('change', e => { const t = e.target; if (t && (t.id === 'mrCheckSt' || t.id === 'mrDeskPlace')) drawClub(t.value); });

  /* ---------- 3. Research on this place ---------- */
  /* Nov 12 2026 (KPC-Links #151): data/us-key/overrides.json is a MANIFEST. Its own 'parks' hold the parks with a 'no' list; its
     'parts' name the files (same folder) that hold every other park. The manifest and each part are read the same way (this page's
     working copy, the day's ?v= like the site's other working reads) and put together. A missing or unreadable manifest or part, a
     part name with a slash, a ref in two files, or a part park with a 'no' list = { failed } (the card says the signed decisions
     could not be read), never an empty set. A file with no 'parts' (Canada) is used as it is. */
  const day = () => new Date().toISOString().slice(0, 10);
  async function overrides(R) {
    const base = 'data/' + R + '-key/', m = await once(base + 'overrides.json?v=' + day());
    if (!m || typeof m !== 'object') return { failed: 'overrides.json did not load' };
    if (!Array.isArray(m.parts) || !m.parts.length) return m;
    if (m.parts.some(n => typeof n !== 'string' || !n || /[\/]/.test(n))) return { failed: 'a part name is not a plain file name' };
    const docs = await Promise.all(m.parts.map(n => once(base + n + '?v=' + day())));
    const parks = Object.assign({}, m.parks || {}), from = {};
    Object.keys(parks).forEach(r => { from[r] = 'overrides.json'; });
    for (let i = 0; i < docs.length; i++) {
      const c = docs[i] && docs[i].parks;
      if (!c || typeof c !== 'object' || Array.isArray(c)) return { failed: m.parts[i] + ' did not load' };
      for (const r of Object.keys(c)) {
        if (from[r]) return { failed: r + ' is in both ' + from[r] + ' and ' + m.parts[i] };
        if (c[r] && Array.isArray(c[r].no) && c[r].no.some(x => x != null)) return { failed: r + ' in ' + m.parts[i] + ' has a no list' };
        from[r] = m.parts[i]; parks[r] = c[r];
      }
    }
    return Object.assign({}, m, { parks: parks });
  }
  async function research(ref) {
    const R = /^CA-/.test(ref) ? 'ca' : 'us';
    const [ps, hj, ov, pn] = await Promise.all([once('data/' + R + '-key/review/problem-solver.json'), once('data/' + R + '-key/review/held-joins.json'), overrides(R), once('data/review/precheck-notes.json')]);
    const items = [];
    if (ov && ov.failed) items.push(['Signed decision', 'could not be read right now (' + ov.failed + '); reload the page before relying on this card']);
    ((ps && ps.parks) || []).filter(p => p.park === ref).forEach(p => items.push(['Recommended next step', (p.verdict ? p.verdict + ': ' : '') + (p.recommend || '') + (p.reasons && p.reasons.length ? ' (' + p.reasons.slice(0, 2).join('; ') + ')' : '')]));
    const hp = hj && hj.parks; (Array.isArray(hp) ? hp.filter(x => x && (x.park === ref || x.ref === ref)) : (hp && hp[ref] ? [hp[ref]] : [])).forEach(h => items.push(['Outline on hold', h.why || h.reason || 'held for a person to check']));
    const o = ov && !ov.failed && ov.parks && ov.parks[ref];
    if (o) items.push(['Signed decision', [o.join ? 'outline: ' + o.join.join(', ') : '', o.no ? 'not: ' + o.no.join(', ') : '', o.decided_by ? 'by ' + o.decided_by : '', o.when || ''].filter(Boolean).join(' · ')]);
    ['mapping_checked', 'ask_brandon', 'trail_check'].forEach(k => { const v = pn && pn[k] && pn[k][ref]; if (v) items.push([k === 'ask_brandon' ? 'Open question' : k === 'trail_check' ? 'Trail line check' : 'Mapping check', v.result || v.ask || v.keep || JSON.stringify(v).slice(0, 200)]); });
    return items;
  }
  async function addResearch(root) {
    if (!root || root.dataset.rsBusy) return;
    const refs = [...new Set((root.textContent.match(/\b(?:US|CA)-\d{4,5}\b/g) || []))].slice(0, 4);
    const old = root.querySelector('.mr-research'); if (old && old.dataset.refs === refs.join(',')) return;
    if (old) old.remove(); if (!refs.length) return;
    root.dataset.rsBusy = '1';
    try {
      const rows = []; for (const r of refs) (await research(r)).forEach(x => rows.push([r].concat(x)));
      if (!rows.length) return;
      const s = document.createElement('div'); s.className = 'mr-sec mr-research'; s.dataset.refs = refs.join(',');
      s.innerHTML = '<h3>Research on this place</h3><p class="mr-help">Notes the club already keeps. Read only; the agency page and the PAD-US record still win.</p>' +
        rows.map(x => '<div class="mr-kv"><dt>' + esc(x[0]) + ' · ' + esc(x[1]) + '</dt><dd>' + esc(x[2]) + '</dd></div>').join('');
      root.appendChild(s);
    } finally { delete root.dataset.rsBusy; }
  }
  function watch() {
    ['mrSpot', 'mrDeskOut', 'mrOut'].forEach(id => { const el = document.getElementById(id); if (!el || el.dataset.rsWatch) return; el.dataset.rsWatch = '1';
      let t = null; new MutationObserver(() => { clearTimeout(t); t = setTimeout(() => addResearch(el), 400); }).observe(el, { childList: true, subtree: true }); });
  }
  if (D) { if (D.readyState === 'loading') D.addEventListener('DOMContentLoaded', watch); else watch(); }

  /* Nov 8 (Brandon 8:49 / 8:50 AM CST): the PAD-US record, in plain words, near the top of a place card, plus one short line per
     search result. Every code is shown with its meaning (the domains are copied from the PAD-US 4.0 service). */
  const PAD = {
    ver: 'USGS PAD-US 4.0 (released April 2024)', layer: 'Fee and Managers layer',
    type: { FED: 'Federal', TRIB: 'American Indian Lands', STAT: 'State', DIST: 'Regional Agency Special District', LOC: 'Local Government', NGO: 'Non-Governmental Organization', PVT: 'Private', JNT: 'Joint', UNK: 'Unknown', TERR: 'Territorial', DESG: 'Designation' },
    name: { TVA: 'Tennessee Valley Authority', BLM: 'Bureau of Land Management', BOEM: 'Bureau of Ocean Energy Management', USBR: 'Bureau of Reclamation', FWS: 'U.S. Fish and Wildlife Service', USFS: 'Forest Service', DOD: 'Department of Defense', USACE: 'Army Corps of Engineers', DOE: 'Department of Energy', NPS: 'National Park Service', NRCS: 'Natural Resources Conservation Service', ARS: 'Agricultural Research Service', BIA: 'Bureau of Indian Affairs', NOAA: 'National Oceanic and Atmospheric Administration', BPA: 'Bonneville Power Administration', OTHF: 'Other or Unknown Federal Land', TRIB: 'American Indian Lands', SPR: 'State Park and Recreation', SDC: 'State Department of Conservation', SLB: 'State Land Board', SFW: 'State Fish and Wildlife', SDNR: 'State Department of Natural Resources', SDOL: 'State Department of Land', OTHS: 'Other or Unknown State Land', REG: 'Regional Agency Land', RWD: 'Regional Water Districts', CITY: 'City Land', CNTY: 'County Land', UNKL: 'Other or Unknown Local Government', NGO: 'Non-Governmental Organization', PVT: 'Private', JNT: 'Joint', OTHR: 'Other', UNK: 'Unknown', VI: 'U.S. Virgin Islands Government', AS: 'American Samoa Government', GU: 'Guam Government', MP: 'Mariana Islands Government', PR: 'Puerto Rico Government', FM: 'Federated States of Micronesia Government' },
    des: { NP: 'National Park', NM: 'National Monument', NCA: 'Conservation Area', NF: 'National Forest', NG: 'National Grassland', PUB: 'National Public Lands', NT: 'National Scenic or Historic Trail', NWR: 'National Wildlife Refuge', WA: 'Wilderness Area', WSR: 'Wild and Scenic River', WSA: 'Wilderness Study Area', MPA: 'Marine Protected Area', NRA: 'National Recreation Area', NSBV: 'National Scenic, Botanical or Volcanic Area', NLS: 'National Lakeshore or Seashore', IRA: 'Inventoried Roadless Area', ACEC: 'Area of Critical Environmental Concern', RNA: 'Research Natural Area', REC: 'Recreation Management Area', RMA: 'Resource Management Area', WPA: 'Watershed Protection Area', REA: 'Research or Educational Area', HCA: 'Historic or Cultural Area', MIT: 'Mitigation Land or Bank', MIL: 'Military Land', ACC: 'Access Area', SDA: 'Special Designation Area', PROC: 'Approved or Proclamation Boundary', FOTH: 'Federal Other or Unknown', ND: 'Not Designated', TRIBL: 'Native American Land Area', SP: 'State Park', SW: 'State Wilderness', SCA: 'State Conservation Area', SREC: 'State Recreation Area', SHCA: 'State Historic or Cultural Area', SRMA: 'State Resource Management Area', SOTH: 'State Other or Unknown', LP: 'Local Park', LCA: 'Local Conservation Area', LREC: 'Local Recreation Area', LHCA: 'Local Historic or Cultural Area', LRMA: 'Local Resource Management Area', LOTH: 'Local Other or Unknown', PCON: 'Private Conservation', PPRK: 'Private Park', PREC: 'Private Recreation or Education', PHCA: 'Private Historic or Cultural', PAGR: 'Private Agricultural', PRAN: 'Private Ranch', PFOR: 'Private Forest Stewardship', POTH: 'Private Other or Unknown', CONE: 'Conservation Easement', RECE: 'Recreation or Education Easement', HCAE: 'Historic or Cultural Easement', AGRE: 'Agricultural Easement', RANE: 'Ranch Easement', FORE: 'Forest Stewardship Easement', OTHE: 'Other Easement', UNKE: 'Unknown Easement', UNK: 'Unknown', OCS: 'Outer Continental Shelf Area', FACY: 'Facility' },
    acc: { OA: 'Open Access', RA: 'Restricted Access', XA: 'Closed', UK: 'Unknown' },
    gap: { '1': 'managed for biodiversity; natural disturbance allowed', '2': 'managed for biodiversity; natural disturbance suppressed', '3': 'multiple use (may allow mining, logging or off-road vehicles)', '4': 'no known biodiversity protection mandate' },
    cat: { Fee: 'Fee (land owned outright)', Easement: 'Easement', Other: 'Other', Unknown: 'Unknown', Designation: 'Designation', Marine: 'Marine Area', Proclamation: 'Approved, Proclamation or Extent Boundary' }
  };
  const pEsc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const blank = v => v == null || String(v).trim() === '';
  const code = (tbl, v) => blank(v) ? 'blank' : (tbl[v] ? v + ' = ' + tbl[v] : String(v));
  const gov = t => t === 'FED' || t === 'STAT' || t === 'TERR';
  function padHint(a) {
    const acc = a.Pub_Access, h = [];
    if (acc === 'OA') h.push('Public access: Open, which counts toward the public-access rule.');
    else if (acc === 'RA') h.push('Public access: Restricted. Check with the agency what the limits are before counting it as open to the public.');
    else if (acc === 'XA') h.push('Public access: Closed, which does not meet the public-access rule.');
    else h.push('Public access: Unknown here. Ask the managing agency.');
    if (a.Own_Type === 'JNT') h.push('Joint ownership: check that a federal or state owner is one of them.');
    else if (!blank(a.Own_Type) && !gov(a.Own_Type)) h.push('Owner type is ' + (PAD.type[a.Own_Type] || a.Own_Type) + ', not federal or state.');
    if (/proclamation/i.test(a.Category || '')) h.push('This is a proclamation boundary, not land actually owned.');
    return h.join(' ');
  }
  function padSource(a) {
    return 'Where this comes from: ' + PAD.ver + ', ' + PAD.layer + (blank(a.OBJECTID) ? '' : ', record OBJECTID ' + a.OBJECTID)
      + '. PAD-US is the federal inventory of public lands and protected areas. It can be out of date, so confirm with the managing agency.';
  }
  function padCard(a, link) {
    if (!a) return '';
    const who = (nm, loc, ty) => [blank(loc) ? '' : loc, blank(nm) ? '' : '(' + code(PAD.name, nm) + ')'].filter(Boolean).join(' ') + ' · type ' + code(PAD.type, ty);
    const rows = [
      ['Name', a.Unit_Nm + (blank(a.Loc_Nm) || a.Loc_Nm === a.Unit_Nm ? '' : ' (local name ' + a.Loc_Nm + ')')],
      ['Owner', who(a.Own_Name, a.Loc_Own, a.Own_Type)],
      ['Manager', who(a.Mang_Name, a.Loc_Mang, a.Mang_Type)],
      ['Designation', code(PAD.des, a.Des_Tp) + (blank(a.Loc_Ds) ? '' : ' · local: ' + (PAD.des[a.Loc_Ds] ? code(PAD.des, a.Loc_Ds) : a.Loc_Ds))],
      ['Public access', code(PAD.acc, a.Pub_Access)],
      ['GAP status', blank(a.GAP_Sts) ? 'blank' : 'GAP ' + a.GAP_Sts + ' = ' + (PAD.gap[String(a.GAP_Sts)] || 'not listed')],
      ['GIS acres', blank(a.GIS_Acres) ? 'blank' : Number(a.GIS_Acres).toLocaleString('en-US') + ' acres'],
      ['Land category', code(PAD.cat, a.Category)],
      ['Date established', blank(a.Date_Est) ? 'blank' : a.Date_Est],
      ['State', blank(a.State_Nm) ? 'blank' : a.State_Nm],
      ['Source', [blank(a.GIS_Src) ? '' : a.GIS_Src, blank(a.Src_Date) ? '' : 'dated ' + a.Src_Date].filter(Boolean).join(', ') || 'blank'],
      ['Data provider', blank(a.Agg_Src) ? 'blank' : a.Agg_Src],
      ['Comments', blank(a.Comments) ? 'none' : a.Comments]
    ];
    if (a.Own_Type === 'JNT' || a.Mang_Type === 'JNT') rows.splice(3, 0, ['Joint ownership', 'Yes. Listed owners: ' + (blank(a.Loc_Own) ? 'not named' : a.Loc_Own)]);
    rows.push(['Record ID', 'OBJECTID ' + (blank(a.OBJECTID) ? 'blank' : a.OBJECTID) + (blank(a.Source_PAID) ? '' : ' · Source_PAID ' + a.Source_PAID)]);
    return '<div class="mr-padus" data-mr-padus="' + pEsc(a.OBJECTID) + '"><h4 style="margin:0 0 6px">PAD-US record</h4>'
      + '<p class="mr-padhint"><b>' + pEsc(padHint(a)) + '</b></p>'
      + '<table class="mr-recbox">' + rows.map(r => '<tr><th>' + pEsc(r[0]) + '</th><td>' + pEsc(r[1]) + '</td></tr>').join('') + '</table>'
      + (link ? '<p class="mr-help"><a href="' + pEsc(link) + '" target="_blank" rel="noopener">Open PAD-US record ' + pEsc(a.OBJECTID) + ' ↗</a></p>' : '')
      + '<p class="mr-help">' + pEsc(padSource(a)) + '</p></div>';
  }
  function padLine(a) {
    if (!a) return 'PAD-US: no matching record';
    const short = (nm, loc, ty) => (blank(loc) || /^(unknown|recorded|owner)$/i.test(loc) ? (PAD.name[nm] || nm || 'unknown') : loc) + (blank(ty) ? '' : ' (' + (PAD.type[ty] || ty) + ')');
    return 'PAD-US: Owner ' + short(a.Own_Name, a.Loc_Own, a.Own_Type) + ' · Manager ' + short(a.Mang_Name, a.Loc_Mang, '')
      + ' · Access ' + (({ OA: 'Open', RA: 'Restricted', XA: 'Closed', UK: 'Unknown' })[a.Pub_Access] || 'blank')
      + ' · ' + (blank(a.Loc_Ds) ? (PAD.des[a.Des_Tp] || a.Des_Tp || 'no designation') : (PAD.des[a.Loc_Ds] || a.Loc_Ds));
  }

  /* Nov 8 (Brandon 8:57 AM CST, "Cpcad"): the Canada counterpart of the PAD-US card. CPCAD = Canadian Protected and Conserved
     Areas Database (Environment and Climate Change Canada, Open Government Licence - Canada). Domains copied from the CPCAD service. */
  const CP = {
    ver: 'CPCAD, December 2025 edition (published by ECCC March 2026)', layer: 'CPCAD map service layer 0',
    pa: { 1: 'Protected area (PA)', 2: 'Other effective area-based conservation measure (OECM)', 3: 'Interim - protected area (PA)', 4: 'Interim - other effective area-based conservation measure (OECM)', 5: 'Not applicable' },
    iucn: { 1: 'Ia = strict nature reserve', 2: 'Ib = wilderness area', 3: 'II = national park (large natural area, recreation allowed)', 4: 'III = natural monument or feature', 5: 'IV = habitat or species management area', 6: 'V = protected landscape or seascape', 7: 'VI = protected area with sustainable use of natural resources', 8: 'Not reported', 9: 'Not applicable' },
    status: { 0: 'Delisted', 1: 'Designated', 2: 'Established', 3: 'Interim', 4: 'Inscribed', 5: 'Adopted' },
    biome: { M: 'Marine', T: 'Terrestrial / freshwater' },
    loc: { 1: 'Alberta', 2: 'British Columbia', 3: 'Manitoba', 4: 'New Brunswick', 5: 'Newfoundland and Labrador', 6: 'Northwest Territories', 7: 'Nova Scotia', 8: 'Nunavut', 9: 'Ontario', 10: 'Prince Edward Island', 11: 'Quebec', 12: 'Saskatchewan', 13: 'Yukon', 14: 'Coastal Arctic Marine', 15: 'Coastal Atlantic Marine', 16: 'Coastal Pacific Marine', 17: 'Offshore Arctic Marine', 18: 'Offshore Atlantic Marine', 19: 'Offshore Pacific Marine', 20: 'Arctic Marine Coastal/Offshore', 21: 'Offshore Arctic/Atlantic Marine' },
    own: { 1: 'Federal', 2: 'Provincial / territorial', 3: 'Municipal', 4: 'Indigenous', 5: 'Communal', 6: 'Individual landowners', 7: 'For-profit organizations', 8: 'Non-profit organizations', 9: 'Joint ownership', 10: 'Multiple ownership', 11: 'Contested', 12: 'Not reported' },
    gov: { 1: 'National government', 2: 'Sub-national (provincial / territorial) government', 3: 'Government-delegated management', 4: 'Transboundary governance', 5: 'Collaborative governance', 6: 'Joint governance', 7: 'Individual landowners', 8: 'Non-profit organizations', 9: 'For-profit organizations', 10: 'Indigenous peoples', 11: 'Local communities', 12: 'Not reported' },
    prov: { AB: 1, BC: 2, MB: 3, NB: 4, NL: 5, NT: 6, NS: 7, NU: 8, ON: 9, PE: 10, QC: 11, SK: 12, YT: 13 }
  };
  const cc = (tbl, v) => blank(v) ? 'blank' : (tbl[v] != null ? v + ' = ' + tbl[v] : String(v));
  function caHint(a) {
    const h = [];
    if (+a.OWNER_TYPE === 1 || +a.OWNER_TYPE === 2) h.push('Owner: ' + CP.own[a.OWNER_TYPE] + ', which counts toward the government-owned rule.');
    else if (+a.OWNER_TYPE === 9 || +a.OWNER_TYPE === 10) h.push('Owner: ' + CP.own[a.OWNER_TYPE] + '. Check that a federal or provincial owner is one of them.');
    else if (!blank(a.OWNER_TYPE)) h.push('Owner type is ' + (CP.own[a.OWNER_TYPE] || a.OWNER_TYPE) + ', not federal or provincial.');
    if (+a.STATUS === 0) h.push('Status: Delisted, so it is no longer a protected area.');
    else if (+a.STATUS === 3) h.push('Status: Interim, not yet final.');
    if (+a.PA_OECM_DF === 2 || +a.PA_OECM_DF === 4) h.push('This is a conserved area (OECM), not a protected area. Check it is a named public place.');
    h.push('CPCAD has no public-access field. Ask the managing agency whether the public can visit.');
    return h.join(' ');
  }
  function caSource(a) {
    return 'Where this comes from: ' + CP.ver + ', ' + CP.layer + (blank(a.ZONE_ID) ? '' : ', record ZONE_ID ' + a.ZONE_ID)
      + '. CPCAD is Canada\u2019s national inventory of protected and conserved areas, compiled by Environment and Climate Change Canada (Open Government Licence - Canada). It can be out of date, so confirm with the managing agency.';
  }
  const haAc = ha => blank(ha) ? 'blank' : Number(ha).toLocaleString('en-US', { maximumFractionDigits: 1 }) + ' ha (' + Math.round(Number(ha) * 2.47105).toLocaleString('en-US') + ' acres)';
  function caCard(a, link) {
    if (!a) return '';
    const yr = [blank(a.ESTYEAR) ? '' : 'established ' + a.ESTYEAR, blank(a.QUALYEAR) || a.QUALYEAR === a.ESTYEAR ? '' : 'counted as protected since ' + a.QUALYEAR].filter(Boolean).join(', ');
    const rows = [
      ['Name', a.NAME_E + (blank(a.NAME_IND) ? '' : ' (Indigenous name ' + a.NAME_IND + ')') + (blank(a.ZONEDESC_E) ? '' : ' · zone: ' + a.ZONEDESC_E)],
      ['Owner / authority', (blank(a.OWNER_E) ? 'not named' : a.OWNER_E) + ' · type ' + cc(CP.own, a.OWNER_TYPE)],
      ['Manager / governance', (blank(a.MGMT_E) ? 'not named' : a.MGMT_E) + ' · governance ' + cc(CP.gov, a.GOV_TYPE)],
      ['Type / designation', (blank(a.TYPE_E) ? 'blank' : a.TYPE_E) + (blank(a.MECH_E) ? '' : ' · under ' + a.MECH_E)],
      ['Protected or conserved', cc(CP.pa, a.PA_OECM_DF)],
      ['IUCN category', blank(a.IUCN_CAT) ? 'blank' : 'code ' + a.IUCN_CAT + ': ' + (CP.iucn[a.IUCN_CAT] || 'not listed')],
      ['Status and year', cc(CP.status, a.STATUS) + (yr ? ' · ' + yr : '')],
      ['Area', haAc(a.O_AREA_HA)],
      ['Biome / zone', cc(CP.biome, a.BIOME) + (blank(a.LOC) ? '' : ' · ' + cc(CP.loc, a.LOC))],
      ['Management plan', blank(a.MPLAN) ? 'blank' : (+a.MPLAN === 1 ? 'Yes' + (blank(a.MPLAN_REF) ? '' : ' · ' + a.MPLAN_REF) : 'No')],
      ['Record ID', 'ZONE_ID ' + (blank(a.ZONE_ID) ? 'blank' : a.ZONE_ID) + (blank(a.PARENT_ID) || a.PARENT_ID === a.ZONE_ID ? '' : ' · part of PARENT_ID ' + a.PARENT_ID) + (blank(a.JUR_ID) ? '' : ' · provider id ' + a.JUR_ID) + (blank(a.OBJECTID) ? '' : ' · OBJECTID ' + a.OBJECTID)]
    ];
    if (+a.OWNER_TYPE === 9 || +a.OWNER_TYPE === 10) rows.splice(2, 0, ['Joint ownership', 'Yes (' + CP.own[a.OWNER_TYPE] + '). Listed: ' + (blank(a.OWNER_E) ? 'not named' : a.OWNER_E)]);
    return '<div class="mr-padus mr-cpcad" data-mr-cpcad="' + pEsc(a.ZONE_ID) + '"><h4 style="margin:0 0 6px">CPCAD record (Canada)</h4>'
      + '<p class="mr-padhint"><b>' + pEsc(caHint(a)) + '</b></p>'
      + '<table class="mr-recbox">' + rows.map(r => '<tr><th>' + pEsc(r[0]) + '</th><td>' + pEsc(r[1]) + '</td></tr>').join('') + '</table>'
      + (link ? '<p class="mr-help"><a href="' + pEsc(link) + '" target="_blank" rel="noopener">Open CPCAD record ' + pEsc(a.ZONE_ID) + ' ↗</a></p>' : '')
      + '<p class="mr-help">' + pEsc(caSource(a)) + '</p></div>';
  }
  function caLine(a) {
    if (!a) return 'CPCAD: no matching record';
    return 'CPCAD: Owner ' + (blank(a.OWNER_E) ? 'not named' : a.OWNER_E) + (CP.own[a.OWNER_TYPE] ? ' (' + CP.own[a.OWNER_TYPE] + ')' : '')
      + ' · Manager ' + (blank(a.MGMT_E) ? 'not named' : a.MGMT_E) + ' · ' + (blank(a.TYPE_E) ? 'no type' : a.TYPE_E)
      + ' · ' + (CP.status[a.STATUS] || 'status blank') + (blank(a.ESTYEAR) ? '' : ' ' + a.ESTYEAR)
      + (blank(a.IUCN_CAT) || !CP.iucn[a.IUCN_CAT] ? '' : ' · IUCN ' + String(CP.iucn[a.IUCN_CAT]).split(' = ')[0]);
  }

  W.KPCMapExtras = { clipFC: clipFC, clubLayers: clubLayers, drawClub: drawClub, research: research, overrides: overrides, padCard: padCard, padLine: padLine, padHint: padHint, padSource: padSource, PAD: PAD, caCard: caCard, caLine: caLine, caHint: caHint, caSource: caSource, CP: CP, BIG_PARTS: BIG_PARTS, NEAR_KM: NEAR_KM };
  if (typeof module !== 'undefined' && module.exports) module.exports = W.KPCMapExtras;
})();

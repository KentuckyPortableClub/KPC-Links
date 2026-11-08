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
  async function research(ref) {
    const R = /^CA-/.test(ref) ? 'ca' : 'us';
    const [ps, hj, ov, pn] = await Promise.all([once('data/' + R + '-key/review/problem-solver.json'), once('data/' + R + '-key/review/held-joins.json'), once('data/' + R + '-key/overrides.json'), once('data/review/precheck-notes.json')]);
    const items = [];
    ((ps && ps.parks) || []).filter(p => p.park === ref).forEach(p => items.push(['Recommended next step', (p.verdict ? p.verdict + ': ' : '') + (p.recommend || '') + (p.reasons && p.reasons.length ? ' (' + p.reasons.slice(0, 2).join('; ') + ')' : '')]));
    const hp = hj && hj.parks; (Array.isArray(hp) ? hp.filter(x => x && (x.park === ref || x.ref === ref)) : (hp && hp[ref] ? [hp[ref]] : [])).forEach(h => items.push(['Outline on hold', h.why || h.reason || 'held for a person to check']));
    const o = ov && ov.parks && ov.parks[ref];
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

  W.KPCMapExtras = { clipFC: clipFC, clubLayers: clubLayers, drawClub: drawClub, research: research, padCard: padCard, padLine: padLine, padHint: padHint, padSource: padSource, PAD: PAD, BIG_PARTS: BIG_PARTS, NEAR_KM: NEAR_KM };
  if (typeof module !== 'undefined' && module.exports) module.exports = W.KPCMapExtras;
})();

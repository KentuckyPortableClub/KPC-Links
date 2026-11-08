/* Mapping Rep Tool Box: "Possible new parks" for Check all, and the official agency-link dropdown.
   Design: Nov 7 checkall-candidates (decisions rounds 1-3). Pure functions, no fetches: the page passes data in.
   Safe to run under Node (node kpc-maprep-candidates.js runs the selftest).

   - The candidate list is ON (Nov 7, Brandon 7:36 PM CST). ?candidates=0 or localStorage kpcMapCandidates=0 turns it off;
     with it off, Check all shows what it showed before, plus the agency dropdown.
   - The agency dropdown is ON. It is only links: the place's row in data/maprep/agencies.json, and for a US place
     the federal land agencies from FEDA in kpc-maprep.js (passed in, not copied here).
   - Rows come from the published US key's `nonum` list ([objectid, name, designation, manager, acres]) or, when it
     exists, the full side file data/us-key/new/US-XX-nonum.json. Canada and world keys have no `nonum`: dropdown only.
   - Research leads only. Never a park, never a boundary. This file does not read or write answer keys. */
(function (root, factory) {
  const logic = (typeof module !== 'undefined' && module.exports && typeof require !== 'undefined')
    ? require('./kpc-maprep-logic.js')
    : (root && root.KPCMapLogic);
  const api = factory(logic);
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.KPCMapCands = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (L) {
  'use strict';
  const G = () => L || (typeof globalThis !== 'undefined' && globalThis.KPCMapLogic) || null;

  /* Nov 7 (Brandon 7:36 PM CST): switched ON. Default on; ?candidates=0 or localStorage kpcMapCandidates=0 turns the list off
     (?candidates=1 / localStorage 1 still mean on). Was: hidden, default off. */
  function candidatesOn() {
    try {
      if (typeof location !== 'undefined' && location && /(?:\?|&)candidates=0(?:&|$)/.test(String(location.search || ''))) return false;
      if (typeof localStorage !== 'undefined' && localStorage && localStorage.getItem('kpcMapCandidates') === '0') return false;
    } catch (e) {}
    return true;
  }

  const FLOOR_DEFAULT = 5;                       /* acres; a default of the control, never a hard cutoff */
  const FLOOR_CHOICES = [0, 1, 5, 10, 40, 100];
  const PAGE = 50;                               /* "Show more" adds this many; there is no cap */

  /* Designation codes (PAD-US Des_Tp). */
  const EXCLUDE_DES = {
    MIT: 'mitigation land or bank: set aside to offset damage elsewhere, not a park'
  };
  /* Local codes are kept, flagged, and skip the "city of" exclusion. */
  const LOCAL_DES = { LP: 'Local Park', LREC: 'Local Recreation Area', LHCA: 'Local Historic or Cultural Area' };

  const FLAG = {
    local: 'check local rules',
    university: 'check, university land',
    unknown: 'manager unknown, check',
    corps: 'Corps land: check with the district'
  };
  /* A college or university is never excluded: kept and flagged (Brandon, Nov 7 round 3; keeps Moundville).
     Nov 7 round 4: one rule shared with the pile-solver park-type design (same source strings in Python, re.I for WORDS).
     WORDS (any case): University / Universities / Univ. / the "Univeristy" typo; College(s) unless a street or a town
     ("College Street", "College Park", "College Station", "Borough of State College"); Board of Regents; Jacksonville State.
     ABBR (all caps only, whole word): UAB, UA, UNA ... Left out on purpose: USA (the key uses it for the US government),
     AU ("AU SABLE"), A&M ("Texas A&M Forest Service" is the state forestry agency). "Universal", "Collegeville" never match. */
  const UNIV_WORDS_RE = /\buniv(?:ersit(?:y|ies)|eristy)?\b|(?<!of state )\bcolleges?\b(?!\s+(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|way|pl|place|ct|court|park|station|hill|hills|heights|grove|point|corner|township|borough|area)\b)|\bboard of regents\b|\bjacksonville state\b(?!\s+(?:park|forest)\b)/i;
  const UNIV_ABBR_RE = /\b(?:UAB|UAH|UA|UNA|UWA|AAMU|JSU|SUNY|CUNY|MSU|LSU|UGA|UK|WKU|EKU|NKU|USM)\b/;
  function isUniversity(s) { s = String(s || ''); return UNIV_WORDS_RE.test(s) || UNIV_ABBR_RE.test(s); }
  /* Corps of Engineers land is kept (many parks are Corps lakes). The flag needs the text itself to say Corps. */
  const CORPS_RE = /\bcorps\b|\busace\b|\barmy\b/i;
  const UNKNOWN_RE = /^\s*(?:unknown|unk)?\s*$/i;
  /* Manager exclusions that remain. Each: [id, test, one-line reason, skipped for local codes]. */
  const MANAGER_EXCLUDE = [
    ['city', /\b(?:city|town|village) of\b/i, 'city or town land: new parks need the two highest tiers of government', true],
    ['dot', [/\b(?:department|dept\.?) of transportation\b/i, /\b[A-Z]{0,3}DOT\b/], 'state highway department land, not a park manager', false],
    /* GUESS G11 (design doc): administrative state land, read from the name only. */
    ['cultural', /\bstate cultural affairs\b/i, 'state cultural-affairs office land, not a park manager (reading of the name)', false]
  ];

  /* Kind words, same families as KINDS in .github/scripts/kpc_us_key.py (read only; not shared code). */
  const KINDS = [
    ['wma', /wildlife management area|\bwma\b|\bswa\b|wildlife area|game lands?|game areas?|game management area|hunting area|fish and wildlife area|public hunting|fishery area|fishing access|habitat area|wildlife and environmental area|(?<!recreation )(?<!herd )(?<!conservation )management area/],
    ['wsr', /wild (?:and|&) scenic river|recreational river/],
    ['ca', /conservation area|conservation reserve|\baccess$/],
    ['snp', /nature preserve|natural area|\bsnp\b|\bsna\b|natural heritage|\bpreserve\b|natural state conservation|natural reserve|scientific and natural|natural environment area|\bnea\b|\bnrma\b/],
    ['hist', /historic(?:al)? (?:site|park|area)|\bshs\b/],
    ['sp', /state (?:resort )?park|historic(?:al)? park|\bsrp\b|recreation(?:al)? area|state beach|state seashore/],
    ['nf', /national forest|national grassland/], ['sf', /state forest/],
    ['nwr', /wildlife refuge|\bnwr\b/], ['nfh', /hatchery|\bnfh\b|\bfh\b/],
    ['nps', /national (?:park|monument|preserve|seashore|lakeshore|battlefield|military park|river|scenic river|parkway)/],
    ['wild', /wilderness(?! study)/], ['wsa', /wilderness study area|\bwsa\b/],
    ['hma', /herd (?:management )?area|\bhma\b/],
    ['rma', /recreation management area|\bs?rma\b|\berma\b|campground|recreation site|day use area/],
    ['air', /airport|airstrip|air ?field|landing strip/], ['trh', /trail ?head/]
  ];
  const DES_KIND = { SP: 'sp', SREC: 'sp', SHCA: 'hist', NWR: 'nwr', NF: 'nf', NG: 'nf', NP: 'nps', NM: 'nps', NRA: 'nps', NHS: 'hist', WA: 'wild' };
  function kindsOf(text, des) {
    const s = String(text || '').toLowerCase();
    const out = new Set();
    KINDS.forEach(([k, re]) => { if (re.test(s)) out.add(k); });
    const d = DES_KIND[String(des || '').toUpperCase()];
    if (d) out.add(d);
    return out;
  }
  /* Kinds disagree only when both names carry a kind and they share none
     ("Little River Wildlife Management Area" vs "Little River State Forest"). */
  function kindsAgree(a, b) {
    if (!a.size || !b.size) return true;
    for (const k of a) if (b.has(k)) return true;
    return false;
  }

  /* Rule 4: "Mobile" reads "USACE Mobile District" only when the manager or owner text itself says Corps.
     The key rows carry one manager field; nothing is inferred from the name or from another file. */
  function displayManager(manager, owner) {
    const m = String(manager || '').trim();
    if (/\bmobile\b/i.test(m) && CORPS_RE.test(m + ' ' + String(owner || ''))) return 'USACE Mobile District';
    return m;
  }

  /* One key row -> { drop: reason or '', flags: [...] }. */
  function judgeRow(row) {
    const des = String(row[2] || '').toUpperCase();
    const mgr = String(row[3] || '');
    const owner = String(row[5] || '');        /* not in today's rows; read if a future file adds it */
    if (EXCLUDE_DES[des]) return { drop: des, flags: [] };
    const local = !!LOCAL_DES[des];
    const flags = [];
    if (local) flags.push('local');
    if (isUniversity(mgr) || isUniversity(owner)) flags.push('university');
    else {
      for (const [id, re, , localOk] of MANAGER_EXCLUDE) {
        if (local && localOk) continue;
        if ([].concat(re).some(x => x.test(mgr))) return { drop: id, flags: [] };
      }
    }
    if (UNKNOWN_RE.test(mgr)) flags.push('unknown');
    if (CORPS_RE.test(mgr + ' ' + owner)) flags.push('corps');
    return { drop: '', flags: flags };
  }
  function reasonOf(id) {
    if (EXCLUDE_DES[id]) return id + ': ' + EXCLUDE_DES[id];
    const m = MANAGER_EXCLUDE.find(x => x[0] === id);
    return m ? m[2] : id;
  }

  /* Every name the key already holds: the park name, and every joined (m) or check (c) record name. */
  function keyNames(key) {
    const out = [];
    const parks = (key && key.parks) || {};
    Object.keys(parks).forEach(ref => {
      const p = parks[ref] || {};
      if (p.n) out.push({ ref: ref, name: p.n, kinds: kindsOf(p.n + ' ' + (p.t || '')) });
      (p.m || []).concat(p.c || []).forEach(r => { if (r && r[1]) out.push({ ref: ref, name: String(r[1]), kinds: kindsOf(r[1]) }); });
    });
    return out;
  }
  /* Index words: the name without generic words (normName). A score of 84 or more (core equal, every core word
     in the other name, or a whole-word prefix/suffix) needs one of these words in both names. */
  function wordsOf(s) {
    const g = G();
    const t = (g && g.normName ? g.normName(s) : String(s || '').toLowerCase());
    const w = t.split(' ').filter(x => x.length > 2);
    return w.length ? w : t.split(' ').filter(Boolean);
  }
  /* Best key name for a candidate. Only key names that share an index word are scored, so the page stays quick. */
  function bestMatches(name, kinds, names, index) {
    const g = G();
    const seen = new Set(), hits = [];
    wordsOf(name).forEach(w => (index.get(w) || []).forEach(i => seen.add(i)));
    seen.forEach(i => {
      const k = names[i];
      const s = g.nameScore(name, k.name);
      if (s >= 52) hits.push({ ref: k.ref, name: k.name, score: s, agree: kindsAgree(kinds, k.kinds) });
    });
    hits.sort((a, b) => b.score - a.score || String(a.ref).localeCompare(String(b.ref)));
    return hits;
  }
  function indexNames(names) {
    const idx = new Map();
    names.forEach((k, i) => wordsOf(k.name).forEach(w => { const l = idx.get(w) || []; if (l[l.length - 1] !== i) l.push(i); idx.set(w, l); }));
    return idx;
  }

  /* Rows to use: the full side file when it is there and for this state, else the key's own list. */
  function sourceRows(key, side) {
    const counts = (key && key.counts) || {};
    if (side && Array.isArray(side.nonum) && (!side.state || !key || !key.st || side.state === key.st || ('US-' + side.state) === key.st)) {
      const gone = new Set((side.joined_since_cut || []).map(String));
      return { from: 'side', rows: side.nonum.filter(r => !gone.has(String(r[0]))), total: side.nonum.length, inFile: side.nonum.length };
    }
    const rows = (key && key.nonum) || null;
    if (!rows) return { from: 'none', rows: [], total: 0, inFile: 0 };
    return { from: 'key', rows: rows, total: counts.nonum != null ? counts.nonum : rows.length, inFile: rows.length };
  }

  /* The whole list. opts: { floor }. Returns every candidate group (no cap), sorted by acres then name. */
  function fromNonum(key, side, opts) {
    opts = opts || {};
    const floor = opts.floor == null ? FLOOR_DEFAULT : Math.max(0, +opts.floor || 0);
    const src = sourceRows(key, side);
    const res = { available: src.from !== 'none', from: src.from, total: src.total, inFile: src.inFile, floor: floor,
      dropped: {}, droppedRows: 0, groups: 0, sameAsKey: [], hiddenSmall: 0, rows: [] };
    if (!res.available) return res;
    const g = G();
    const groups = new Map();
    src.rows.forEach(r => {
      const j = judgeRow(r);
      if (j.drop) { res.dropped[j.drop] = (res.dropped[j.drop] || 0) + 1; res.droppedRows++; return; }
      const name = String(r[1] || '');
      const kinds = kindsOf(name, r[2]);
      const base = (g && g.normName ? g.normName(name) : '') || name.toLowerCase().trim();
      const gk = base + '|' + [...kinds].sort().join(',');
      const cur = groups.get(gk) || { key: gk, name: name, ids: [], pieces: 0, acres: 0, des: [], managers: [], flags: [], kinds: kinds, top: -1 };
      cur.ids.push(r[0]); cur.pieces++; cur.acres += (+r[4] || 0);
      if ((+r[4] || 0) > cur.top) { cur.top = +r[4] || 0; cur.name = name; }
      const d = String(r[2] || ''); if (d && cur.des.indexOf(d) < 0) cur.des.push(d);
      const shown = displayManager(r[3], r[5]); if (shown && cur.managers.indexOf(shown) < 0) cur.managers.push(shown);
      j.flags.forEach(f => { if (cur.flags.indexOf(f) < 0) cur.flags.push(f); });
      groups.set(gk, cur);
    });
    res.groups = groups.size;
    const names = keyNames(key);
    const index = indexNames(names);
    groups.forEach(c => {
      const hits = bestMatches(c.name, c.kinds, names, index);
      const same = hits.find(h => h.score >= 84 && h.agree);
      if (same) { res.sameAsKey.push({ name: c.name, ref: same.ref, keyName: same.name, score: same.score }); return; }
      if (c.acres < floor) { res.hiddenSmall++; return; }
      const byRef = [];
      hits.forEach(h => { if (!byRef.some(x => x.ref === h.ref)) byRef.push(h); });
      c.similar = byRef.slice(0, 3).map(h => ({ ref: h.ref, name: h.name, score: h.score, otherKind: !h.agree }));
      c.flagText = c.flags.map(f => FLAG[f]);
      c.outline = 'outline not checked';
      delete c.top;
      res.rows.push(c);
    });
    res.rows.sort((a, b) => b.acres - a.acres || a.name.localeCompare(b.name));
    return res;
  }
  function flagCounts(rows) {
    const n = { local: 0, university: 0, unknown: 0, corps: 0 };
    (rows || []).forEach(r => r.flags.forEach(f => { n[f] = (n[f] || 0) + 1; }));
    return n;
  }
  /* "Show more" paging: the first n rows. Every row is reachable; there is no cap. */
  function pageOf(rows, shown) { return (rows || []).slice(0, Math.max(PAGE, shown || 0)); }

  /* Spatial dedup when an outline is available (PAD-US by OBJECTID on tap). Never invents geometry. */
  function pinCheck(geoms, pins, miles) {
    const g = G();
    const list = (geoms || []).filter(x => x && x.type);
    if (!list.length) return { checked: false, hit: null, text: 'outline not checked' };
    for (const geom of list) {
      if (g.tractsOn && g.tractsOn() && g.alreadyParks) {   /* Nov 7 (tract switch on): every pin, so a parent and a child both show */
        const all = g.alreadyParks(geom, pins || [], miles == null ? 0.25 : miles);
        if (all.length) return { checked: true, hit: all[0], all: all, text: 'a park pin is inside or within 0.25 mi: ' + all.map(p => p.ref + ' ' + (p.name || '')).join('; ') };
        continue;
      }
      const hit = g.alreadyPark(geom, pins || [], miles == null ? 0.25 : miles);
      if (hit) return { checked: true, hit: hit, text: 'a park pin is inside or within 0.25 mi: ' + hit.ref + ' ' + (hit.name || '') };
    }
    return { checked: true, hit: null, text: 'no park pin inside or within 0.25 mi' };
  }

  /* ---------- Agency dropdown (ON) ---------- */
  /* Full addresses for the FEDA hosts. NPS, USFS, FWS and USACE are written out in kpc-maprep-check.js (agencyLinks). */
  const FED_URL = {
    'nps.gov': ['https://www.nps.gov/', true],
    'fs.usda.gov': ['https://www.fs.usda.gov/', true],
    'fws.gov': ['https://www.fws.gov/', true],
    'usace.army.mil': ['https://www.usace.army.mil/', true],
    'blm.gov': ['https://www.blm.gov/', false],      /* UNVERIFIED: only the host is in the repo; Brandon checks (Nov 7) */
    'usbr.gov': ['https://www.usbr.gov/', false],    /* UNVERIFIED: only the host is in the repo; Brandon checks (Nov 7) */
    'tva.com': ['https://tva.com/', false]           /* not in Brandon's list; built from the FEDA host, unverified */
  };
  function federalLinks(feda) {
    return (feda || []).map(([name, host]) => {
      const u = FED_URL[host] || ['https://' + String(host || '').replace(/^\/\//, '') + '/', false];
      return { name: name, slot: 'home', label: name, url: u[0], verified: u[1] };
    });
  }
  /* The stored Alabama State Parks "finder" is one park's page (Gulf State Park), not a park finder.
     Hide exactly that link here; agencies.json is not edited. No other finder link is hidden. */
  const HIDE = [{ code: 'AL', name: 'Alabama State Parks', slot: 'finder', url: 'https://alapark.com/parks/gulf-state-park', note: 'finder: stored link is one park page, hidden' }];
  function hiddenLink(code, name, slot, url) {
    return HIDE.find(h => h.code === code && h.name === name && h.slot === slot && h.url === url) || null;
  }
  /* Groups for the place being viewed. region 'US' adds the federal group. */
  function agencyOptions(code, region, feda) {
    const g = G();
    const groups = [], hidden = [];
    const ok = u => u && !(g && g.isBanned && g.isBanned(u));
    const rows = (g && g.agencyMatches) ? g.agencyMatches(code || '', '') : [];
    const items = [];
    rows.forEach(a => [['home', 'home'], ['finder', 'finder'], ['gis', 'GIS']].forEach(([slot, word]) => {
      const s = a[slot] || {};
      if (!ok(s.url)) return;
      const h = hiddenLink(code, a.name, slot, s.url);
      if (h) { hidden.push({ name: a.name, slot: slot, url: s.url, note: h.note }); return; }
      items.push({ name: a.name, slot: slot, label: a.name + ' — ' + word, url: s.url, verified: !!s.verified });
    }));
    if (items.length) groups.push({ label: 'Agencies for this place', items: items });
    if (String(region || '').toUpperCase() === 'US') {
      const fed = federalLinks(feda).filter(x => ok(x.url));
      if (fed.length) groups.push({ label: 'Federal land agencies', items: fed });
    }
    return { groups: groups, hidden: hidden };
  }

  /* ---------- HTML (strings only; the page wires the events) ---------- */
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function dropdownHtml(code, region, feda, placeName) {
    const o = agencyOptions(code, region, feda);
    const n = o.groups.reduce((s, x) => s + x.items.length, 0);
    let html = '<div class="mr-sec" id="mrAgDrop"><h3>Official agency links' + (placeName ? ' · ' + esc(placeName) : '') + '</h3>';
    if (!n) return html + '<p class="mr-help">No agency directory row for this place.</p></div>';
    html += '<label class="mr-help" for="mrAgSel">Pick an agency page. It opens in a new tab.</label>' +
      '<div class="mr-agpick"><select id="mrAgSel" aria-label="Official agency links">' +
      o.groups.map(gr => '<optgroup label="' + esc(gr.label) + '">' + gr.items.map(it => '<option value="' + esc(it.url) + '">' + esc(it.label + (it.verified ? '' : ' (unverified)')) + '</option>').join('') + '</optgroup>').join('') +
      '</select> <a id="mrAgGo" class="mr-agopen" href="' + esc(o.groups[0].items[0].url) + '" target="_blank" rel="noopener">OPEN</a></div>';
    if (o.hidden.length) html += o.hidden.map(h => '<p class="mr-help">' + esc(h.name) + ' ' + esc(h.note) + '.</p>').join('');
    return html + '</div>';
  }
  const fmtAc = n => Math.round(+n || 0).toLocaleString('en-US');
  function rowHtml(c, i, code) {
    const g = G();
    const ag = (g && g.agencyMatches) ? g.agencyMatches(code || '', c.name + ' ' + c.managers.join(' ')) : [];
    const links = [];
    ag.forEach(a => [['home', 'home'], ['finder', 'finder'], ['gis', 'GIS']].forEach(([slot, word]) => {
      const s = a[slot] || {};
      if (!s.url || hiddenLink(code, a.name, slot, s.url) || (g.isBanned && g.isBanned(s.url))) return;
      links.push('<a href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(a.name + ' ' + word + (s.verified ? '' : ' (unverified)')) + '</a>');
    }));
    const flags = c.flagText.length ? ' · <b>' + c.flagText.map(esc).join('; ') + '</b>' : '';
    const sim = (c.similar || []).length ? '<p class="mr-help">Similar name in the key: ' + c.similar.map(s => esc(s.ref + ' ' + s.name) + (s.otherKind ? ' (other kind of place)' : '')).join('; ') + '</p>' : '';
    const padIds = c.ids.filter(id => /^\d+$/.test(String(id)));
    return '<details class="mr-cand" data-i="' + i + '"><summary><b>' + esc(c.name) + '</b> · ' + fmtAc(c.acres) + ' ac' +
      (c.pieces > 1 ? ' · ' + c.pieces + ' pieces' : '') + ' · ' + esc(c.managers.join(' / ') || 'no manager text') +
      (c.des.length ? ' · code ' + esc(c.des.join(', ')) : '') + flags + '</summary>' +
      '<p class="mr-help">Record ids: ' + esc(c.ids.join(', ')) + '. ' + (padIds.length ? '' : 'State-table ids have no PAD-US outline to check.') + '</p>' + sim +
      (links.length ? '<p class="mr-help">Agency: ' + links.join(' · ') + (ag[0] && !ag[0].matched ? ' (no role matched, every agency for this place)' : '') + '</p>' : '') +
      '<p class="mr-help" data-outline="' + i + '">' + esc(c.outline) + (padIds.length ? ' <button type="button" class="mr-ag" data-pinchk="' + i + '">CHECK OUTLINE VS PARK PINS</button>' : '') + '</p>' +
      (padIds.length ? '<p class="mr-help"><button type="button" class="mr-ag" data-rstest="' + esc(padIds.join(',')) + '" data-rsname="' + esc(c.name) + '">RUN THE FULL NEW-PARK CHECKS</button> Answer key outlines, same-name parks and pins, the full PAD-US record and a summary to copy.</p>' : '') + '</details>';
  }
  function listHtml(res, shown, code) {
    if (!res || !res.available) return '<div class="mr-sec" id="mrCands"><h3>Possible new parks</h3><p class="mr-help">Possible new parks are not available for this place yet.</p></div>';
    const page = pageOf(res.rows, shown);
    const fc = flagCounts(res.rows);
    const why = Object.keys(res.dropped).map(k => res.dropped[k] + ' ' + reasonOf(k)).join('; ');
    const cut = res.from === 'key' && res.inFile < res.total ? ' The key file holds ' + res.inFile + ' of ' + res.total + ' rows; the rest are the smallest.' : '';
    return '<div class="mr-sec" id="mrCands"><h3>Possible new parks · ' + res.rows.length + '</h3>' +
      '<p class="mr-help"><b>Research leads, not parks.</b> Check the agency page and the PAD-US record before you submit anything.</p>' +
      '<p class="mr-help"><label for="mrCandFloor">Hide places under </label><select id="mrCandFloor" aria-label="Acre floor">' +
      FLOOR_CHOICES.map(v => '<option value="' + v + '"' + (v === res.floor ? ' selected' : '') + '>' + v + ' acres</option>').join('') +
      (FLOOR_CHOICES.indexOf(res.floor) < 0 ? '<option value="' + res.floor + '" selected>' + res.floor + ' acres</option>' : '') +
      '</select> · ' + res.hiddenSmall + ' hidden under ' + res.floor + ' acres.</p>' +
      '<p class="mr-help">' + res.sameAsKey.length + ' left out as the same place as a key park. ' + (why ? 'Left out: ' + esc(why) + '.' : '') + esc(cut) + '</p>' +
      '<p class="mr-help">Flags: ' + fc.local + ' check local rules · ' + fc.university + ' university land · ' + fc.unknown + ' manager unknown · ' + fc.corps + ' Corps land.</p>' +
      '<div id="mrCandRows">' + page.map((c, i) => rowHtml(c, i, code)).join('') + '</div>' +
      (page.length < res.rows.length ? '<button type="button" class="mr-ag" id="mrCandMore">SHOW MORE (' + page.length + ' of ' + res.rows.length + ')</button>' : '') +
      '</div>';
  }

  function selftest() {
    const fails = [];
    const ok = (c, m) => { if (!c) fails.push(m); };
    ok(candidatesOn() === true, 'candidates are on by default (Nov 7 7:36 PM CST)');
    ok(judgeRow([1, 'X', 'MIT', 'State', 10]).drop === 'MIT', 'MIT is left out');
    ok(judgeRow([1, 'X', 'LP', 'Huntsville, City of', 10]).flags.indexOf('local') >= 0, 'LP kept and flagged');
    ok(judgeRow([1, 'X', 'SCA', 'Huntsville, City of', 10]).drop === 'city', 'city land without a local code is left out');
    ok(judgeRow([1, 'X', 'LHCA', 'University of Alabama', 10]).flags.join() === 'local,university', 'university flagged, not left out');
    ok(judgeRow([1, 'X', 'LP', 'UAB', 10]).flags.join() === 'local,university' && !isUniversity('Universal') && !isUniversity('Collegeville') && !isUniversity('College Street Park'), 'UAB is university land; Universal / Collegeville / College Street are not');
    ok(displayManager('Mobile') === 'Mobile' && displayManager('Mobile District, Corps of Engineers') === 'USACE Mobile District', 'Mobile shown raw unless Corps is in the text');
    ok(!kindsAgree(kindsOf('Little River Wildlife Management Area'), kindsOf('Little River State Forest')), 'WMA vs state forest is another kind');
    ok(hiddenLink('AL', 'Alabama State Parks', 'finder', 'https://alapark.com/parks/gulf-state-park') && !hiddenLink('AL', 'Alabama Wildlife & Freshwater Fisheries (DCNR)', 'finder', 'https://outdooralabama.com/public-lands'), 'only the one Alabama finder link is hidden');
    if (fails.length) { console.log(fails.join('\n')); console.log('SOME FAILED'); return 1; }
    console.log('PASS maprep candidates selftest');
    return 0;
  }

  return {
    candidatesOn: candidatesOn, FLOOR_DEFAULT: FLOOR_DEFAULT, FLOOR_CHOICES: FLOOR_CHOICES, PAGE: PAGE,
    EXCLUDE_DES: EXCLUDE_DES, LOCAL_DES: LOCAL_DES, MANAGER_EXCLUDE: MANAGER_EXCLUDE, FLAG: FLAG, FED_URL: FED_URL, HIDE: HIDE,
    kindsOf: kindsOf, kindsAgree: kindsAgree, displayManager: displayManager, judgeRow: judgeRow,
    isUniversity: isUniversity, UNIV_WORDS_RE: UNIV_WORDS_RE, UNIV_ABBR_RE: UNIV_ABBR_RE, reasonOf: reasonOf,
    keyNames: keyNames, sourceRows: sourceRows, fromNonum: fromNonum, flagCounts: flagCounts, pageOf: pageOf, pinCheck: pinCheck,
    federalLinks: federalLinks, hiddenLink: hiddenLink, agencyOptions: agencyOptions,
    dropdownHtml: dropdownHtml, listHtml: listHtml, selftest: selftest
  };
});

if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
  process.exit(module.exports.selftest());
}

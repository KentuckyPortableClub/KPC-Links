/* KPC "Getting in" links for parks in GB, IE, AU and NZ (round 3, Nov 7 2026). OFF by default.
   For the US/Trip Planner popup of a park outside the US and Canada: the managing agency's own pages (home, park finder, fees,
   parking, entry points, hours, and this park's own page when the agency uses a known address pattern).
   LINKS ONLY. Nothing here states a fee, an hour or a gate time, and every address is marked "unverified" until a plain read
   (data/maprep/agencies.json: verified:false). Entrances and parking POINTS for these countries do not exist in the data yet.
   Switch: data/getting-in-switch.json {"on": true}, or ?getin=1 on the page, or localStorage kpcGetIn=1. Off = block() returns ''.
   No network except two same-site JSON files (the switch and data/maprep/agencies.json). Runs under Node: node kpc-getting-in.js */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.KPCGetIn = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const COUNTRIES = ['GB', 'IE', 'AU', 'NZ'];
  /* parkinfo sub-region codes -> agencies.json place. GUESS for Scotland: the council-area codes are ISO 3166-2:GB; the list is
     the ones I am sure of. Any other code gets the country row only. */
  const SCOT = new Set('ABD ABE ANS AGB CLK DGY DND EAY EDH ELN ELS ERW EDU FAL FIF GLG HLD IVC MLN MRY NAY NLK ORK PKN RFW SCB SLK STG SAY WDU WLN ZET SCT'.split(' '));
  const AU_STATES = new Set(['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'ACT', 'NT']);

  function placeCodes(pre, sub) {
    pre = String(pre || '').toUpperCase(); sub = String(sub || '').toUpperCase();
    if (!COUNTRIES.includes(pre)) return [];
    const out = [];
    if (pre === 'GB') { if (sub === 'ENG') out.push('GB-ENG'); else if (SCOT.has(sub)) out.push('GB-SCT'); else if (sub === 'WLS') out.push('GB-WLS'); else if (sub === 'NIR') out.push('GB-NIR'); }
    if (pre === 'AU' && AU_STATES.has(sub)) out.push('AU-' + sub);
    out.push(pre);
    return out;
  }

  function wantRoles(type, name) {
    const t = (String(type || '') + ' ' + String(name || '')).toLowerCase();
    const r = [];
    if (/forest|woodland|wood\b/.test(t)) r.push('forestry');
    if (/national park|regional park|state park|conservation park|country park|heritage|historic/.test(t)) r.push('parks', 'heritage');
    if (/reserve|nnr|nature|wildlife|wetland|marine|sanctuary|conservation/.test(t)) r.push('wildlife');
    r.push('parks', 'lands');
    return Array.from(new Set(r));
  }

  /* slug for a per-park page: rule text is "full ..." (whole name) or "name without the park type ..." */
  function slugOf(name, rule) {
    let s = String(name || '').toLowerCase();
    if (/without the park type/.test(rule || '')) s = s.replace(/\b(national park|state park|conservation park|regional park|nature reserve|national reserve|state forest|forest park)\b/g, ' ');
    s = s.normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/&/g, ' and ').replace(/['’]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return s;
  }

  const LABELS = { fees: 'Fees and passes', parking: 'Parking', entrances: 'Entry points', hours: 'Opening hours' };
  const safe = u => /^https:\/\/[^\s"'<>]+$/.test(String(u || ''));

  /* model: up to 3 agencies, region first, best role match first; each with its links (all unverified unless the file says so) */
  function build(AG, pre, sub, park) {
    const places = (AG && AG.places) || {};
    const codes = placeCodes(pre, sub), roles = wantRoles(park && park.type, park && park.name);
    const cand = [];
    codes.forEach((c, ci) => ((places[c] && places[c].agencies) || []).forEach(a => {
      const hit = Math.min(...(a.roles || [a.role]).map(r => { const i = roles.indexOf(r); return i < 0 ? 99 : i; }));
      cand.push({ a, c, key: [hit, ci] });
    }));
    cand.sort((x, y) => x.key[0] - y.key[0] || x.key[1] - y.key[1]);
    const out = [];
    cand.forEach(({ a, c }) => {
      if (out.length >= 3 || out.some(o => o.name === a.name)) return;
      const links = [];
      const add = (label, o, guess) => { if (o && safe(o.url)) links.push({ label, url: o.url, unverified: !o.verified, guess: !!guess, scope: o.scope || '' }); };
      add('Agency site', a.home); add('Find a park', a.finder);
      const ac = a.access || {};
      ['entrances', 'parking', 'fees', 'hours'].forEach(k => add(LABELS[k], ac[k]));
      if (ac.park_page && ac.park_page.template && park && park.name) {
        const sl = slugOf(park.name, ac.park_page.slug);
        if (sl) add('This park’s page', { url: ac.park_page.template.replace('{slug}', sl), verified: false, scope: 'built from the park name: may not exist' }, true);
      }
      if (links.length) out.push({ name: String(a.name).replace(/\s*\(.*$/, ''), place: c, links });
    });
    return out;
  }

  function html(model, esc) {
    esc = esc || (s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])));
    if (!model.length) return '';
    return '<div class="meta" style="margin-top:8px"><b>&#127359; GETTING IN: THE AGENCY’S OWN PAGES</b></div>' +
      model.map(m => '<div class="meta">&bull; <b>' + esc(m.name) + '</b>: ' + m.links.map(l =>
        '<a href="' + esc(l.url) + '" target="_blank" rel="noopener"' + (l.scope ? ' title="' + esc(l.scope) + '"' : '') + '>' + esc(l.label) + (l.guess ? ' (guess)' : '') + ' ↗</a>').join(' &middot; ') + '</div>').join('') +
      '<div class="meta" style="opacity:.8">These links are from the agency’s own site but we have not checked them yet, and we do not know today’s fees, hours or gate times. Check the page before you go.</div>';
  }

  let SW = null, AGP = null;
  function switchOn(sw) {
    try { if (/[?&]getin=1(?:&|$)/.test(location.search)) return true; } catch (e) {}
    try { if (localStorage.getItem('kpcGetIn') === '1') return true; } catch (e) {}
    return !!(sw && sw.on === true);
  }

  /* the popup hook: s = the clicked spot {c: ref, n: name}; PINFO = the planner's parkinfo cache; returns html or '' */
  async function block(s, pre, PINFO, dfetch, esc) {
    try {
      if (!COUNTRIES.includes(pre)) return '';
      if (SW === null) SW = fetch('data/getting-in-switch.json').then(r => r.ok ? r.json() : null).catch(() => null);
      if (!switchOn(await SW)) return '';
      if (AGP === null) AGP = (dfetch || fetch)('data/maprep/agencies.json').then(r => r.ok ? r.json() : null).catch(() => null);
      const AG = await AGP; if (!AG) return '';
      const d = PINFO && PINFO[pre] ? await PINFO[pre] : null, p = d && d.parks && d.parks[s.c];
      if (!p) return '';
      return html(build(AG, pre, p[10], { name: p[0] || s.n, type: p[2] }), esc);
    } catch (e) { return ''; }
  }

  function selftest() {
    let bad = 0;
    const ck = (c, m) => { if (!c) { bad++; console.error('FAIL ' + m); } else console.log('PASS ' + m); };
    ck(placeCodes('AU', 'NSW').join() === 'AU-NSW,AU' && placeCodes('GB', 'ENG').join() === 'GB-ENG,GB' && placeCodes('GB', 'HLD')[0] === 'GB-SCT' && placeCodes('NZ', 'AUK').join() === 'NZ' && placeCodes('US', 'KY').length === 0, 'place codes');
    ck(slugOf('Royal National Park', 'full name') === 'royal-national-park' && slugOf('Conondale National Park', 'name without the park type') === 'conondale', 'slugs');
    ck(slugOf('Mt. O’Brien & Sons', 'full') === 'mt-obrien-and-sons', 'slug punctuation');
    const AG = { places: { 'AU-NSW': { agencies: [{ name: 'NSW National Parks and Wildlife Service (x)', role: 'parks', roles: ['parks'], home: { url: 'https://www.nationalparks.nsw.gov.au/', verified: false }, finder: { url: '', verified: false }, access: { fees: { url: 'https://www.nationalparks.nsw.gov.au/passes-and-fees/fee-collecting-parks', verified: false }, park_page: { template: 'https://www.nationalparks.nsw.gov.au/visit-a-park/parks/{slug}/visitor-info', slug: 'full name', verified: false } } }] }, AU: { agencies: [] } } };
    const m = build(AG, 'AU', 'NSW', { name: 'Royal National Park', type: 'National Park' });
    ck(m.length === 1 && m[0].name === 'NSW National Parks and Wildlife Service' && m[0].links.length === 3 && m[0].links.every(l => l.unverified), 'build: one agency, three links, all unverified');
    ck(m[0].links[2].guess && /royal-national-park\/visitor-info$/.test(m[0].links[2].url), 'build: park page is built from the name and marked guess');
    ck(build(AG, 'US', 'KY', {}).length === 0 && build(null, 'AU', 'NSW', {}).length === 0, 'build: nothing for US or no data');
    ck(!/<script|javascript:/i.test(html(build({ places: { AU: { agencies: [{ name: '<script>', home: { url: 'javascript:alert(1)' }, finder: { url: 'https://x.example/"onmouseover="a' } }] } } }, 'AU', 'ZZ', {}))), 'html: unsafe addresses are dropped');
    ck(html(m).indexOf('we have not checked them') > 0 && html([]) === '', 'html: carries the not-checked line; empty model = empty string');
    return bad ? 1 : 0;
  }

  return { COUNTRIES, placeCodes, wantRoles, slugOf, build, html, switchOn, block, selftest };
});

if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
  process.exit(module.exports.selftest());
}

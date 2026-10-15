/* KPC Suggest a Park or Summit (hidden page kpc-suggest.html)
   PARK tab = the Map Rep Tool Box engine (kpc-maprep.js, public mode) + emails to the state's POTA Mapping
   Representative(s) and the KFF (WWFF USA) coordinator. SUMMIT tab = a summit check + email to the state's
   SOTA Association Manager. Every email carries the caller's call sign and everything the search found. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const B = window.KPCB;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const CHECKED = 'October 15, 2026';
  /* POTA US Mapping Representatives (docs.pota.app/docs/volunteers/countries/united-states-of-america.html) */
  const POTA_URL = 'https://docs.pota.app/docs/volunteers/countries/united-states-of-america.html';
  const POTA_RULES = 'https://docs.pota.app/docs/volunteer_reference/park_additions_edits.html';
  const REPS = { AK: [['WL7CG', 'Alan Sorum']], AL: [['KB3A', 'Chris Robson']], AR: [['W5LST', 'Eddie Daniel']], AZ: [['N7KB', 'Ken Blasor']], CA: [['WM6T', 'Tracy Lenocker']], CO: [['WJ0NF', 'John Fuller']], CT: [['NK1V', 'Steven Veci']], DC: [['K3MTO', 'Christopher Dean']], DE: [['W4BKR', 'Sean Pyne']], FL: [['KN4MQR', 'Justin Sligh']], GA: [['AC4SH', 'Claude Ray']], HI: [['WM6T', 'Tracy Lenocker']], IA: [['N0HR', 'Pat Rundall']], ID: [['W7IMC', 'Scott Burgess']], IL: [['KB9KC', 'Ken Curry']], IN: [['WQ9F', 'Kevin Duffy']], KS: [['KC0VYS', 'Steve Everley']], KY: [['N4BDW', 'Brent Wells']], LA: [['KD5PCK', 'Scott Hernandez']], MA: [['KN8PPY', 'Pete Knapp']], MD: [['KN8PPY', 'Pete Knapp']], ME: [['KB2FMH', 'James Gallo']], MI: [['WT8J', 'Julie Martin']], MN: [['K0WLO', 'Wayne Oliver']], MO: [['AB0O', 'John Ford']], MT: [['K0HAA', 'Nolan Taylor']], MS: [['N4MTE', 'Tom Suggs']], NC: [['KN4XP', 'Mike Prevatte']], ND: [['N3CDF', 'Wayne Fussell']], NE: [['NI0P', 'Brian Schmidt']], NH: [['W1ND', 'Glen Sansoucie']], NJ: [['KA2YRA', 'Steve Rosman']], NM: [['N3CDF', 'Wayne Fussell']], NV: [['K3VG', 'Neal Kernes']], NY: [['K5KHK', 'Karl Heinz Kremer']], OH: [['KZ3L', 'Kevin Culp']], OK: [['WD5JR', 'Josiah Russell']], OR: [['W7RTA', 'Charlie Bottita']], PA: [['K0BAK', 'Peter Kobak']], RI: [['KC1QDZ', 'Jim Garman']], SC: [['KK4JS', 'John Satterfield']], SD: [['K8ERS', 'Eric Stoddert']], TN: [['N4MTE', 'Tom Suggs']], TX: [['W3NY', 'Molly Sauder']], UT: [['KN7D', 'Val Hanney']], VA: [['W4BKR', 'Sean Pyne']], VT: [['N2YQT', 'Ryan Tourge']], WA: [['W7RTA', 'Charlie Bottita']], WI: [['K9ZIE', 'Ryan McKenzie']], WV: [['KN8PPY', 'Pete Knapp']], WY: [['KN7D', 'Val Hanney']] };
  /* KFF = WWFF's US program (wwff.co/awards/national-programs/, wwff.us/references/) */
  const KFF = { call: 'N9MM', role: 'KFF coordinator', email: 'n9mm.norm@gmail.com', refs: 'https://wwff.us/references/', rules: 'https://wwff.co/wwff_cont/uploads/2025/09/WWFF-Global-Rules-V_5.10.pdf', prog: 'https://wwff.co/awards/national-programs/' };
  /* SOTA associations by state (api2.sota.org.uk/api/associations) */
  const SOTA = { MN: 'K0M', HI: 'KH6', PR: 'KP4', CO: 'W0C', ND: 'W0D', SD: 'W0D', IA: 'W0I', MO: 'W0M', NE: 'W0N', CT: 'W1', ME: 'W1', MA: 'W1', NH: 'W1', RI: 'W1', VT: 'W1', NJ: 'W2', NY: 'W2', DE: 'W3', MD: 'W3', PA: 'W3', AL: 'W4A', NC: 'W4C', SC: 'W4C', GA: 'W4G', KY: 'W4K', TN: 'W4T', VA: 'W4V', AR: 'W5A', MS: 'W5M', NM: 'W5N', OK: 'W5O', TX: 'W5T', CA: 'W6', AZ: 'W7A', ID: 'W7I', MT: 'W7M', NV: 'W7N', OR: 'W7O', UT: 'W7U', WA: 'W7W', WY: 'W7Y', MI: 'W8M', OH: 'W8O', WV: 'W8V', IL: 'W9', IN: 'W9', WI: 'W9' };
  const AM = { K0M: ['K0YAK', ''], KH6: ['KH7AL', ''], KP4: ['KP3V', ''], W0C: ['K0MOS', ''], W0D: ['ND0C', ''], W0I: ['K9IR', ''], W0M: ['N0EVH', ''], W0N: ['K0NO', ''], W1: ['N2YTF', ''], W2: ['K1YMI', ''], W3: ['N2GBR', ''], W4A: ['KN4OK', ''], W4C: ['KI4SVM', ''], W4G: ['WG4I', ''], W4K: ['N4DCW', 'Michael Whitman'], W4T: ['NR3E', ''], W4V: ['AG4VA', ''], W5A: ['KD5ZZK', ''], W5M: ['KD5KC', ''], W5N: ['KT5X', ''], W5O: ['W5ODS', ''], W5T: ['KD5KC', ''], W6: ['N1CLC', ''], W7A: ['WA7JTM', ''], W7I: ['N0DNF', ''], W7M: ['AE7AP', ''], W7N: ['WB0USI', ''], W7O: ['K7ATN', ''], W7U: ['K7ODX', ''], W7W: ['WW7D', ''], W7Y: ['K7GUD', ''], W8M: ['N8HN', ''], W8O: ['W7AMF', ''], W8V: ['N8JEP', ''], W9: ['K9IR', ''] };
  const SOTA_RULES = 'https://www.sota-dl.de/media/SOTA-General-Rules-v1.20.pdf';
  const qrz = c => 'https://www.qrz.com/db/' + encodeURIComponent(c);
  const gq = s => 'https://www.google.com/search?q=' + encodeURIComponent(s);
  const ST = { AL: 'Alabama', AK: 'Alaska', AZ: 'Arizona', AR: 'Arkansas', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', DC: 'District of Columbia', FL: 'Florida', GA: 'Georgia', HI: 'Hawaii', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', IA: 'Iowa', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', ME: 'Maine', MD: 'Maryland', MA: 'Massachusetts', MI: 'Michigan', MN: 'Minnesota', MS: 'Mississippi', MO: 'Missouri', MT: 'Montana', NE: 'Nebraska', NV: 'Nevada', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NY: 'New York', NC: 'North Carolina', ND: 'North Dakota', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VT: 'Vermont', VA: 'Virginia', WA: 'Washington', WV: 'West Virginia', WI: 'Wisconsin', WY: 'Wyoming', PR: 'Puerto Rico' };

  /* ---------- call sign (required for every email) ---------- */
  const CALLRE = /^(?=.*\d)[A-Z0-9]{3,7}(\/[A-Z0-9]{1,4})?$/;
  const callOK = () => CALLRE.test(call());
  const call = () => ($('sgCall').value || '').trim().toUpperCase();
  try { $('sgCall').value = localStorage.getItem('kpcSgCall') || ''; } catch (e) {}
  const refreshAll = () => { document.querySelectorAll('[data-mail]').forEach(el => el._build && el._build()); $('sgCallMsg').textContent = callOK() ? '' : 'Type your call sign first: every email is signed with it.'; };
  $('sgCall').addEventListener('input', () => { const v = call(); $('sgCall').value = v; try { localStorage.setItem('kpcSgCall', v); } catch (e) {} refreshAll(); });
  $('sgCallMsg').textContent = callOK() ? '' : 'Type your call sign first: every email is signed with it.';

  /* ---------- tabs ---------- */
  function tab(t) {
    document.querySelectorAll('[data-sgtab]').forEach(b => b.setAttribute('aria-pressed', b.dataset.sgtab === t ? 'true' : 'false'));
    $('sgPark').hidden = t !== 'park'; $('sgSummit').hidden = t !== 'summit';
    if (t === 'summit' && smap) setTimeout(() => smap.invalidateSize(), 50);
    try { history.replaceState(null, '', location.pathname + location.search + '#' + t); } catch (e) {}
  }
  document.querySelectorAll('[data-sgtab]').forEach(b => b.onclick = () => { tab(b.dataset.sgtab); if (b.dataset.sgtab === 'summit') initMap(); });

  /* ---------- one email card: To + subject + editable body + COPY / OPEN IN EMAIL / QRZ ---------- */
  function mailCard(o) {
    // o: {id, title, to:[{call,name,email,role}], subject(), body(), note, ok}
    const el = document.createElement('div'); el.className = 'sg-mail'; el.dataset.mail = o.id;
    const toLine = o.to.map(t => `<div class="sg-to"><b>${esc(t.call)}</b>${t.name ? ' · ' + esc(t.name) : ''}${t.role ? ' <small>' + esc(t.role) + '</small>' : ''}<br>${t.email ? `<code>${esc(t.email)}</code>` : '<small>Email address: on their QRZ page (free QRZ sign-in may be needed)</small>'} <a href="${qrz(t.call)}" target="_blank" rel="noopener">QRZ PAGE ↗</a></div>`).join('');
    el.innerHTML = `<h4>${esc(o.title)}</h4>${o.note ? `<p class="mr-help">${o.note}</p>` : ''}<div class="sg-tos"><span>SEND TO</span>${toLine}</div>
<label class="sg-l">SUBJECT<input class="sg-subj"></label><label class="sg-l">EMAIL (YOU CAN EDIT IT)<textarea class="sg-body" rows="14"></textarea></label>
<div class="mr-btns"><a class="gold" href="#" data-act="copy">📋 COPY THE EMAIL</a><a href="#" data-act="mail">✉ OPEN IN MY EMAIL APP</a><a href="#" data-act="reset">↺ REBUILD FROM THE SEARCH</a></div><p class="mr-help sg-why"></p>`;
    const S = el.querySelector('.sg-subj'), T = el.querySelector('.sg-body'); let edited = false;
    T.addEventListener('input', () => { edited = true; }); S.addEventListener('input', () => { edited = true; });
    el._build = (force) => { if (edited && !force) return; S.value = o.subject(); T.value = o.body(); if (force) edited = false; };
    el._build(true);
    el.addEventListener('click', e => {
      const a = e.target.closest('[data-act]'); if (!a) return; e.preventDefault();
      const why = el.querySelector('.sg-why');
      if (a.dataset.act === 'reset') { el._build(true); why.textContent = 'Rebuilt with the latest search results.'; return; }
      if (!callOK()) { why.innerHTML = '<b class="mr-no">Type your call sign at the top first.</b>'; $('sgCall').focus(); $('sgCall').scrollIntoView({ block: 'center', behavior: 'smooth' }); return; }
      if (!edited) el._build(true);
      if (a.dataset.act === 'copy') { (navigator.clipboard ? navigator.clipboard.writeText(T.value) : Promise.reject()).then(() => { a.textContent = '✓ COPIED'; why.textContent = 'The email text is copied. Paste it into a new email; copy the subject line from the box above.'; }).catch(() => { T.select(); document.execCommand('copy'); a.textContent = '✓ COPIED'; }); return; }
      const to = o.to.map(t => t.email).filter(Boolean).join(',');
      const href = `mailto:${encodeURIComponent(to).replace(/%2C/g, ',')}?subject=${encodeURIComponent(S.value)}&body=${encodeURIComponent(T.value)}`;
      why.innerHTML = (to ? '' : '<b>Add their email address</b> (from the QRZ page) in the To line. ') + (href.length > 1900 ? 'Some email apps cut long emails short: if the email looks cut off, use COPY THE EMAIL and paste it.' : '');
      location.href = href;
    });
    return el;
  }

  /* ---------- PARK: called by kpc-maprep.js after a park is checked ---------- */
  let last = null;
  const top = t => t === 'FED' || t === 'STAT';
  function park(info) {
    last = info; const out = $('mrOut'); if (!out) return;
    const g = info.g, st = g.st, reps = REPS[st] || [];
    const note = () => (($('mrNote') || {}).value || '').trim().replace(/@@COUNTY@@/g, '(still looking it up)').replace(/@@LINKS@@/g, '(still looking them up)');
    const sec = document.createElement('section'); sec.className = 'sg-sec'; sec.id = 'sgMail';
    const potaDone = info.already && info.already.length;
    const nature = !/(historic|monument|memorial|museum|battlefield|cemetery|fort\b|house|home\b|building|railroad|trail)/i.test(g.name + ' ' + info.des.join(' ')) || /national monument/i.test(info.des.join(' ')) && /natural|geolog|canyon|cave|forest/i.test(g.name);
    const fedSt = info.own.every(top) && info.mng.every(top);
    const open = info.acc.includes('OA');
    const isWMA = /wildlife management|\bWMA\b|wildlife area|game (land|area)|hunting area/i.test(g.name + ' ' + info.des.join(' '));
    const big = (g.acres || 0) > 500;
    const kffChecks = [[nature, 'Nature related (not a building, monument, battleship, statue, old railroad...)'], [fedSt, 'Managed by a federal or state agency (no city parks or private centers)'], [open, 'Open to visitors'], [!isWMA || big, isWMA ? `Wildlife Management Area over 500 acres (this one: about ${Math.round(g.acres).toLocaleString()} acres)` : 'Not a small Wildlife Management Area (only major WMAs over 500 acres)']];
    const kffOK = kffChecks.every(c => c[0]);
    sec.innerHTML = `<h3>✉ EMAIL TO ASK FOR IT TO BE ADDED</h3><p class="mr-help">Each email below already holds your call sign and everything this search found (owner, manager, access, size, GPS pin, grid, county, parking, official links and the rule check). Read it over, add anything you know, then copy it or open it in your email app. Be polite: the people who add parks are volunteers.</p>
<div class="sg-prog"><div class="sg-ph"><b>POTA</b> · Parks on the Air · ${esc(st)} Mapping Representative${reps.length > 1 ? 's' : ''}</div><div id="sgPota"></div></div>
<div class="sg-prog"><div class="sg-ph"><b>WWFF / KFF</b> · World Wide Flora &amp; Fauna, USA program</div><div class="sg-kff">${kffChecks.map(c => `<div class="mr-r ${c[0] ? 'yes' : 'no'}"><i>${c[0] ? 'YES' : 'NO'}</i><div><b>${esc(c[1])}</b></div></div>`).join('')}<p class="mr-help">KFF rules: <a href="${KFF.refs}" target="_blank" rel="noopener">wwff.us/references</a> (US) and the <a href="${KFF.rules}" target="_blank" rel="noopener">WWFF Global Rules</a> (§15: proposals go to the national coordinator). <span id="sgKffHave">Checking if it is already a KFF reference…</span></p></div><div id="sgKff"></div></div>
<div class="sg-prog"><div class="sg-ph"><b>SOTA</b> · Summits on the Air · the peaks in this park</div><p class="mr-help">SOTA is for mountain tops, not parks. This looks at every mapped peak inside the park's boundary and shows which ones are already SOTA summits. Tap one to check it and write the email.</p><div class="mr-btns"><a class="gold" href="#" id="sgPeaksGo">⛰ FIND THE SUMMITS IN THIS PARK</a></div><div id="sgPeaks"></div></div>`;
    out.appendChild(sec);
    $('sgPeaksGo').onclick = e => { e.preventDefault(); peaksIn(info); };
    const intro = (who) => `Hello ${who},\n\n`;
    const sign = () => `\n\nThank you for all you do for the program.\n\n73,\n${call() || '(YOUR CALL SIGN)'}\n\n(Research gathered with the Kentucky Portable Club park helper. The official sources are the agency's own page and map.)`;
    const pv = $('sgPota');
    if (!reps.length) pv.innerHTML = `<p class="mr-help">No Mapping Representative is listed for ${esc(st)} on <a href="${POTA_URL}" target="_blank" rel="noopener">POTA's list</a>. Check that page for the current contact.</p>`;
    else if (potaDone) pv.innerHTML = `<p class="mr-help"><b class="mr-ok">It already looks like a POTA park</b> (${info.already.map(p => esc(p.ref + ' ' + p.name)).join(', ')}), so there's nothing to ask for. If something about it is wrong (name, pin, website), you can still email the Mapping Representative.</p>`;
    if (reps.length) pv.appendChild(mailCard({
      id: 'pota', title: potaDone ? 'Email (only if something needs fixing)' : 'Email the POTA Mapping Representative',
      note: `The ${esc(st)} Mapping Representative${reps.length > 1 ? 's are' : ' is'} listed on <a href="${POTA_URL}" target="_blank" rel="noopener">POTA's Mapping Representatives page</a> (checked ${CHECKED}); POTA says to email them from their QRZ page. Result of the rule check: <b>${esc(info.verdict)}</b>. Rules: <a href="${POTA_RULES}" target="_blank" rel="noopener">Park Additions and Edits</a>.`,
      to: reps.map(r => ({ call: r[0], name: r[1], role: 'POTA Mapping Representative, ' + st })),
      subject: () => `POTA park suggestion: ${g.name} (${st})${call() ? ' from ' + call() : ''}`,
      body: () => intro(reps.map(r => r[1].split(' ')[0] + ' ' + r[0]).join(' and ')) + `I'd like to suggest ${g.name} in ${ST[st] || st} as a new POTA park, if it fits the rules. Below is what I found about it.\n\n` + note() + `\n\n(Rules checked: POTA Park Additions and Edits, ${POTA_RULES})` + sign()
    }));
    let kffHave = '';
    const kv = $('sgKff');
    kv.appendChild(mailCard({
      id: 'kff', title: 'Email the KFF (WWFF USA) coordinator',
      note: `KFF coordinator ${KFF.call}, from WWFF's <a href="${KFF.prog}" target="_blank" rel="noopener">national programs page</a> (checked ${CHECKED}). wwff.us also has an email link under "Adding New References" on <a href="${KFF.refs}" target="_blank" rel="noopener">its references page</a>.${kffOK ? '' : ' <b class="mr-no">One or more KFF checks above say NO, so it may not qualify.</b>'}`,
      to: [{ call: KFF.call, role: KFF.role, email: KFF.email }],
      subject: () => `KFF new reference suggestion: ${g.name} (${st})${call() ? ' from ' + call() : ''}`,
      body: () => intro(KFF.call) + `I'd like to suggest ${g.name} in ${ST[st] || st} as a new KFF (WWFF) reference. Below is what I found about it.\n\nKFF checks (wwff.us/references):\n` + kffChecks.map(c => `- ${c[1]}: ${c[0] ? 'YES' : 'NO'}`).join('\n') + '\n' + (kffHave || '') + '\n' + note() + sign()
    }));
    B.wwffNear(info.la, info.lo, 8).then(L => {
      const m = L.filter(x => (B.sameName(x.name, g.name) && B.sameKind(x.name, g.name)) || (x.d < 1 && B.sameKind(x.name, g.name)));
      kffHave = m.length ? `Already in WWFF nearby: ${m.slice(0, 3).map(x => x.ref + ' ' + x.name + ' (' + x.d.toFixed(1) + ' km)').join('; ')}\n` : 'No WWFF reference with this name nearby (checked the WWFF directory).\n';
      const H = $('sgKffHave'); if (H) H.innerHTML = m.length ? `<b class="mr-w">Already in WWFF?</b> ${m.slice(0, 3).map(x => esc(x.ref + ' ' + x.name)).join(', ')} is close by: check it isn't the same place before emailing.` : '<b class="mr-ok">Not in the WWFF directory</b> by that name.';
      refreshAll();
    }).catch(() => { const H = $('sgKffHave'); if (H) H.textContent = ''; });
    /* the summary keeps filling in (county, links, parking): rebuild the emails while nobody has edited them */
    let n = 0; const iv = setInterval(() => { if (last !== info || ++n > 40) return clearInterval(iv); refreshAll(); }, 1500);
    const j = document.createElement('a'); j.href = '#sgMail'; j.className = 'sg-jump'; j.textContent = '✉ EMAIL TO ADD IT ↓';
    const head = out.querySelector('.mr-v'); if (head) head.after(j);
  }
  window.KPCSuggest = { park };

  /* every mapped peak inside a park (OpenStreetMap natural=peak) + the SOTA summits inside it */
  const OVER = ['https://overpass-api.de/api/interpreter', 'https://overpass.private.coffee/api/interpreter'];
  async function over(q) { for (const u of OVER) { try { return await B.jget(u, { method: 'POST', body: 'data=' + encodeURIComponent(q), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }, 45000); } catch (e) {} } throw new Error('overpass'); }
  async function peaksIn(info) {
    const box = $('sgPeaks'); box.innerHTML = '<div class="mr-msg busy"><span class="mr-spin">🧭</span><span>Looking for the peaks inside the boundary…</span></div>';
    const bb = info.feats.reduce((a, f) => { const b = B.bbox(f.geometry); return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; }, [180, 90, -180, -90]);
    const inP = (a, b) => info.feats.some(f => B.inside(a, b, f.geometry));
    const rad = Math.max(B.km(bb[1], bb[0], bb[3], bb[2]) / 2 + 1, 3);
    let osm = [], sota = [];
    try { const j = await over(`[out:json][timeout:40];(node[natural~"^(peak|hill)$"](${bb[1]},${bb[0]},${bb[3]},${bb[2]}););out 400;`); osm = (j.elements || []).filter(e => inP(e.lat, e.lon)); } catch (e) { osm = null; }
    try { sota = (await B.sotaNear((bb[1] + bb[3]) / 2, (bb[0] + bb[2]) / 2, rad)).filter(s => inP(s.la, s.lo)); } catch (e) {}
    const rows = (osm || []).map(e => { const t = e.tags || {}, s = sota.find(x => B.km(x.la, x.lo, e.lat, e.lon) < 0.35); return { la: e.lat, lo: e.lon, name: t.name || '(no name)', ele: +t.ele || null, prom: +t.prominence || null, tags: t, sota: s }; });
    sota.filter(s => !rows.some(r => r.sota === s)).forEach(s => rows.push({ la: s.la, lo: s.lo, name: s.name, ele: s.m, prom: null, tags: {}, sota: s }));
    rows.sort((a, b) => (b.ele || 0) - (a.ele || 0));
    if (!rows.length) { box.innerHTML = `<p class="mr-help">${osm === null ? 'Could not reach OpenStreetMap right now. Try again in a minute.' : 'No mapped peaks inside this boundary. You can still tap a hilltop on the map in the SUMMIT tab.'}</p>`; return; }
    const S = rows.filter(r => r.sota).length;
    box.innerHTML = `<p class="mr-help"><b>${rows.length} peak${rows.length > 1 ? 's' : ''} inside the boundary</b> (OpenStreetMap)${S ? `, ${S} already SOTA summit${S > 1 ? 's' : ''}` : ', none on the SOTA list yet'}. Highest first.</p>` + rows.slice(0, 40).map((r, i) => `<button type="button" class="mr-pick" data-pk="${i}"><b>${esc(r.name)}</b><span>${r.ele ? ft(r.ele).toLocaleString() + ' ft' : 'height ?'}${r.prom ? ' · prominence ' + ft(r.prom).toLocaleString() + ' ft' : ''}<br><small>${r.sota ? '✓ SOTA ' + esc(r.sota.ref) + ' (' + r.sota.pts + ' pts)' : 'not on the SOTA list · CHECK IT ›'}</small></span></button>`).join('') + (rows.length > 40 ? `<p class="mr-help">Showing the 40 highest of ${rows.length}.</p>` : '');
    box.onclick = e => { const b = e.target.closest('[data-pk]'); if (!b) return; const r = rows[+b.dataset.pk]; tab('summit'); initMap(); if (stSel) stSel.value = info.g.st; $('sgSName').value = r.name === '(no name)' ? '' : r.name; check(r.la, r.lo, r.name === '(no name)' ? '' : r.name, { extratags: r.tags }); window.scrollTo({ top: $('sgSummit').offsetTop - 70, behavior: 'smooth' }); };
  }
  /* prominence from OpenStreetMap (prominence tag) or Wikidata (P2660) for the mapped peak at the spot */
  async function promLookup(la, lo, name) {
    try {
      const j = await over(`[out:json][timeout:25];node(around:250,${la},${lo})[natural~"^(peak|hill)$"];out tags center;`);
      const e = (j.elements || []).sort((a, b) => B.km(la, lo, a.lat, a.lon) - B.km(la, lo, b.lat, b.lon))[0]; if (!e) return null;
      const t = e.tags || {}, out = { name: t.name || '', ele: +t.ele || null, d: B.km(la, lo, e.lat, e.lon), la: e.lat, lo: e.lon };
      if (+t.prominence) return Object.assign(out, { m: +t.prominence, src: 'OpenStreetMap' });
      if (t.wikidata) { const w = await B.jget(`https://www.wikidata.org/w/api.php?action=wbgetentities&ids=${encodeURIComponent(t.wikidata)}&props=claims&format=json&origin=*`, null, 15000); const c = (((w.entities || {})[t.wikidata] || {}).claims || {}).P2660; const v = c && c[0] && c[0].mainsnak.datavalue && c[0].mainsnak.datavalue.value; if (v && +v.amount) { const u = /11573|Q11573/.test(v.unit) ? 1 : /3710/.test(v.unit) ? 0.3048 : 1; return Object.assign(out, { m: +v.amount * u, src: 'Wikidata' }); } }
      return out;
    } catch (e) { return null; }
  }

  /* ---------- SUMMIT tab ---------- */
  let smap = null, spin = null, sres = null;
  const stSel = $('sgSt');
  stSel.innerHTML = '<option value="">State…</option>' + Object.keys(ST).sort().map(k => `<option value="${k}">${k} · ${ST[k]}</option>`).join('');
  try { stSel.value = localStorage.getItem('kpcMrState') || ''; } catch (e) {}
  function initMap() {
    if (smap || !window.L) return;
    smap = L.map('sgMap').setView([37.5, -85.3], 7);
    if (window.KPCLayers) KPCLayers(smap, 'Topo'); else L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap' }).addTo(smap);
    if (window.KPCLocate) KPCLocate(smap); if (window.KPCFull) KPCFull(smap);
    smap.on('click', e => check(e.latlng.lat, e.latlng.lng, '', null));
  }
  const msg = h => { $('sgSOut').innerHTML = `<div class="mr-msg${/…$/.test(h) ? ' busy' : ''}">${/…$/.test(h) ? '<span class="mr-spin">🧭</span>' : ''}<span>${h}</span></div>`; };
  $('sgSForm').addEventListener('submit', async e => {
    e.preventDefault(); initMap();
    const name = $('sgSName').value.trim(), st = stSel.value, town = $('sgSTown').value.trim();
    if (!st) { msg('<b>Pick the state first.</b>'); return; }
    if (name.length < 3) { msg('Type the summit name, or tap the map / USE MY GPS.'); return; }
    msg('Looking for the summit…'); $('sgSList').innerHTML = '';
    let hits = [];
    try {
      const j = await B.jget('https://nominatim.openstreetmap.org/search?' + new URLSearchParams({ q: `${name}${town ? ', ' + town : ''}, ${ST[st]}`, format: 'jsonv2', addressdetails: 1, extratags: 1, limit: 15, countrycodes: 'us' }), null, 20000);
      hits = (j || []).filter(h => (h.address && (h.address.state === ST[st] || h.address['ISO3166-2-lvl4'] === 'US-' + st)));
      hits.sort((a, b) => (/peak|hill|ridge|mountain|volcano|saddle/.test(b.type) ? 1 : 0) - (/peak|hill|ridge|mountain|volcano|saddle/.test(a.type) ? 1 : 0));
    } catch (x) {}
    if (!hits.length) { msg(`Couldn't find a place called <b>${esc(name)}</b> in ${esc(ST[st])} on OpenStreetMap. Tap its top on the map instead (switch the map to Topo or Terrain to see the peaks), or use your GPS when you're on it.`); return; }
    $('sgSOut').innerHTML = '';
    $('sgSList').innerHTML = `<p class="mr-help">${hits.length} match${hits.length > 1 ? 'es' : ''}. Pick one:</p>` + hits.slice(0, 12).map((h, i) => `<button type="button" class="mr-pick" data-h="${i}"><b>${esc(h.name || h.display_name.split(',')[0])}</b><span>${esc(h.type)}${h.extratags && h.extratags.ele ? ' · ' + Math.round(h.extratags.ele * 3.28084).toLocaleString() + ' ft' : ''}<br><small>${esc(h.display_name.split(',').slice(1, 3).join(','))}</small></span></button>`).join('');
    $('sgSList').onclick = ev => { const b = ev.target.closest('[data-h]'); if (!b) return; const h = hits[+b.dataset.h]; $('sgSList').innerHTML = ''; check(+h.lat, +h.lon, h.name || h.display_name.split(',')[0], h); };
  });
  $('sgGps').onclick = () => { initMap(); if (!navigator.geolocation) return msg('This phone or browser has no GPS access.'); msg('Getting your GPS…'); navigator.geolocation.getCurrentPosition(p => check(p.coords.latitude, p.coords.longitude, $('sgSName').value.trim(), null), () => msg('Could not get your location. Allow location for this site, or tap the map.'), { enableHighAccuracy: true, timeout: 20000 }); };

  const ft = m => Math.round(m * 3.28084);
  async function check(la, lo, name, nom) {
    initMap(); msg('Checking the summit: height, nearby SOTA summits, who owns the land, county…');
    if (spin) spin.remove(); spin = L.marker([la, lo]).addTo(smap); smap.setView([la, lo], Math.max(smap.getZoom(), 14));
    const st0 = stSel.value;
    const [el, sNear, land, cty, pota, wwff] = await Promise.all([
      B.elevation(la, lo).catch(() => null),
      B.sotaNear(la, lo, 6).catch(() => []),
      B.padusArea(la, lo, 0.002).catch(() => []),
      B.jget(`https://geo.fcc.gov/api/census/area?lat=${la}&lon=${lo}&censusYear=2020&format=json`, null, 15000).then(j => (j.results || [])[0] || null).catch(() => null),
      B.potaNear(la, lo, 0.05).catch(() => []),
      B.wwffNear(la, lo, 3).catch(() => []),
    ]);
    const PL = await promLookup(la, lo, name).catch(() => null);
    if (!name && PL && PL.name && PL.d < 0.2) name = PL.name;
    const st = (cty && cty.state_code) || st0, assoc = SOTA[st], am = assoc ? AM[assoc] : null;
    const osmEle = (nom && nom.extratags && +nom.extratags.ele) || (PL && PL.d < 0.2 && PL.ele) || null;
    const hereM = el ? el.m : (osmEle || null);
    const same = sNear.find(s => s.d < 0.4 || (name && B.sameName(s.name, name) && s.d < 2));
    const lands = (land || []).filter(f => f.geometry && B.inside(la, lo, f.geometry)).map(f => f.properties || {});
    const pub = lands.filter(p => p.Pub_Access === 'OA');
    const nameT = name || 'Unnamed summit';
    const grid = (() => { const A = 'ABCDEFGHIJKLMNOPQR', a = 'abcdefghijklmnopqrstuvwx'; let x = lo + 180, y = la + 90; return A[Math.floor(x / 20)] + A[Math.floor(y / 10)] + Math.floor((x % 20) / 2) + Math.floor(y % 10) + a[Math.floor((x % 2) * 12)] + a[Math.floor((y % 1) * 24)]; })();
    sres = { la, lo, name: nameT, st, assoc, am, hereM, osmEle, sNear, same, lands, pub, cty, pota, wwff, grid };
    const P = la.toFixed(5) + ', ' + lo.toFixed(5);
    const links = [['Google Maps', `https://www.google.com/maps/search/?api=1&query=${la.toFixed(6)},${lo.toFixed(6)}`], ['Topo map (CalTopo)', `https://caltopo.com/map.html#ll=${la.toFixed(5)},${lo.toFixed(5)}&z=15&b=t`], ['OpenStreetMap', `https://www.openstreetmap.org/?mlat=${la.toFixed(5)}&mlon=${lo.toFixed(5)}#map=15/${la.toFixed(5)}/${lo.toFixed(5)}`], ['Peakbagger search (prominence)', name ? `https://www.peakbagger.com/search.aspx?ss=${encodeURIComponent(name)}` : gq(`peakbagger ${la.toFixed(3)} ${lo.toFixed(3)}`)], ['ListsOfJohn / prominence (Google)', gq(`"${name}" ${ST[st] || st} prominence`)]].concat(sNear.slice(0, 3).map(s => [`Nearest SOTA summit ${s.ref}`, `https://sotl.as/summits/${s.ref}`]));
    sres.links = links;
    $('sgSOut').innerHTML = `<section class="mr-res"><div class="mr-head"><div class="mr-k">${esc(st)}${assoc ? ' · SOTA association ' + esc(assoc) : ''}</div><h2>${esc(nameT)}</h2><p>${P} · grid ${grid}${hereM ? ' · ' + ft(hereM).toLocaleString() + ' ft (' + Math.round(hereM) + ' m)' : ''}</p></div>
${same ? `<div class="mr-v yes"><b>ALREADY A SOTA SUMMIT: ${esc(same.ref)}</b><span>${esc(same.name)} · ${same.ft.toLocaleString()} ft · ${same.pts} points · ${(same.d * 0.621).toFixed(2)} mi from the spot. Nothing to ask for.</span></div>` : !assoc ? `<div class="mr-v no"><b>NO SOTA ASSOCIATION FOR ${esc(st)}</b><span>SOTA has no association covering this state yet.</span></div>` : `<div class="mr-v maybe"><b>NOT ON THE SOTA LIST: CHECK THE PROMINENCE</b><span>SOTA needs at least 150 m (492 ft) of prominence. Enter it below if you know it.</span></div>`}
<div class="mr-rules">
<div class="mr-r ${same ? 'no' : 'yes'}"><i>${same ? 'NO' : 'YES'}</i><div><b>Not already a SOTA summit</b><p>${sNear.length ? 'SOTA summits near the spot: ' + sNear.slice(0, 4).map(s => `<a href="https://sotl.as/summits/${esc(s.ref)}" target="_blank" rel="noopener">${esc(s.ref)}</a> ${esc(s.name)} (${s.ft.toLocaleString()} ft, ${(s.d * 0.621).toFixed(1)} mi)`).join('; ') + '.' : 'No SOTA summit within 6 km (about 4 miles).'}</p></div></div>
<div class="mr-r check" id="sgProm"><i>CHECK</i><div><b>Prominence at least 150 m (492 ft)</b><p>Prominence = how far you must go down from the top before climbing anything higher. SOTA's General Rules (§3.5) set 150 m as the worldwide minimum, and peaks must be distinct. Find it on Peakbagger or ListsOfJohn, then type it here:</p><div class="sg-prom"><input id="sgPromV" inputmode="decimal" placeholder="e.g. 620"><select id="sgPromU"><option value="ft">feet</option><option value="m">meters</option></select></div><div class="mr-rl"><a href="${links[3][1]}" target="_blank" rel="noopener">PEAKBAGGER SEARCH ↗</a><a href="${links[4][1]}" target="_blank" rel="noopener">PROMINENCE (GOOGLE) ↗</a></div></div></div>
<div class="mr-r ${pub.length ? 'yes' : 'check'}"><i>${pub.length ? 'YES' : 'CHECK'}</i><div><b>Legal access to the top</b><p>${lands.length ? 'Land at the spot (USGS PAD-US): ' + lands.slice(0, 3).map(p => esc((p.Unit_Nm || p.Loc_Nm || '?') + ' · ' + (p.Loc_Own || p.Own_Name || '') + ' · ' + ({ OA: 'open to the public', RA: 'restricted', XA: 'closed', UK: 'access unknown' })[p.Pub_Access] || '')).join('; ') + '.' : 'No public land at the spot in the national database: it is probably private land.'} SOTA (§3.7): you must use legitimate access and have permission or open access; private land without permission is not allowed.</p></div></div>
<div class="mr-r info"><i>INFO</i><div><b>Height</b><p>${hereM ? `Ground at the spot: ${ft(hereM).toLocaleString()} ft (${Math.round(hereM)} m, ${el ? el.src : 'OpenStreetMap'})${osmEle && el ? `; OpenStreetMap lists the peak at ${ft(osmEle).toLocaleString()} ft` : ''}. Put the pin right on the top for the best number.` : 'Could not look up the height.'} The activation zone is the area within 25 m (82 ft) below the top.</p></div></div>
</div>
<div class="mr-sec mr-facts"><h3>FACTS</h3><div class="mr-fact"><span>GPS (TOP)</span><b>${P}</b></div><div class="mr-fact"><span>GRID</span><b>${grid}</b></div><div class="mr-fact"><span>COUNTY</span><b>${cty ? esc(cty.county_name + ', ' + cty.state_code) : 'not found'}</b></div>${pota.length ? `<div class="mr-fact"><span>POTA PARKS HERE</span><b>${pota.filter(p => B.km(la, lo, p.la, p.lo) < 8).slice(0, 4).map(p => esc(p.ref + ' ' + p.name)).join('; ') || 'none close by'}</b></div>` : ''}${wwff.length ? `<div class="mr-fact"><span>WWFF NEARBY</span><b>${wwff.slice(0, 3).map(x => esc(x.ref + ' ' + x.name)).join('; ')}</b></div>` : ''}<div class="mr-links">${links.map(l => `<a href="${esc(l[1])}" target="_blank" rel="noopener"><b>${esc(l[0])}</b><span>${esc(l[1])}</span></a>`).join('')}</div></div>
<div class="mr-sec" id="sgSMail"><h3>✉ EMAIL THE SOTA ASSOCIATION MANAGER</h3></div></section>`;
    const box = $('sgSMail');
    const promTxt = () => { const v = parseFloat($('sgPromV').value); if (!isFinite(v)) return null; const m = $('sgPromU').value === 'm' ? v : v / 3.28084; return { m, ft: Math.round(m * 3.28084) }; };
    const promRule = () => { const p = promTxt(), r = $('sgProm'); if (!r) return; r.className = 'mr-r ' + (!p ? 'check' : p.m >= 150 ? 'yes' : 'no'); r.querySelector('i').textContent = !p ? 'CHECK' : p.m >= 150 ? 'YES' : 'NO'; const V = $('sgSOut').querySelector('.mr-v'); if (V && !same && assoc) { V.className = 'mr-v ' + (!p ? 'maybe' : p.m >= 150 ? 'yes' : 'no'); V.querySelector('b').textContent = !p ? 'NOT ON THE SOTA LIST: CHECK THE PROMINENCE' : p.m >= 150 ? 'PROMINENCE OK: WORTH SUGGESTING' : 'TOO LITTLE PROMINENCE FOR SOTA'; V.querySelector('span').textContent = !p ? 'SOTA needs at least 150 m (492 ft) of prominence. Enter it below if you know it.' : p.m >= 150 ? 'Check the land access, then email the Association Manager below.' : 'SOTA needs at least 150 m (492 ft); this peak has ' + p.ft + ' ft.'; } refreshAll(); };
    $('sgPromV').addEventListener('input', promRule); $('sgPromU').addEventListener('change', promRule);
    if (PL && PL.m && PL.d < 0.3) { $('sgPromV').value = Math.round(PL.m); $('sgPromU').value = 'm'; const n = document.createElement('p'); n.className = 'mr-help'; n.innerHTML = `<b>Filled in from ${esc(PL.src)}</b> (${Math.round(PL.m)} m = ${ft(PL.m)} ft) for the mapped peak${PL.name ? ' ' + esc(PL.name) : ''}. Volunteer data: double-check it on Peakbagger or ListsOfJohn.`; $('sgProm').querySelector('.sg-prom').after(n); promRule(); }
    else { const n = document.createElement('p'); n.className = 'mr-help'; n.textContent = 'No prominence is listed for this spot in OpenStreetMap or Wikidata, so look it up with the buttons below.'; $('sgProm').querySelector('.sg-prom').after(n); }
    if (!assoc) { box.innerHTML += `<p class="mr-help">SOTA has no association for ${esc(ST[st] || st)}, so there is no one to email about a summit there yet.</p>`; return; }
    box.innerHTML += `<p class="mr-help">SOTA association <b>${esc(assoc)}</b>${am && am[1] ? ' · manager ' + esc(am[1]) : ''}. SOTA's General Rules (§3.6.1): adding a summit is handled by the Association Manager first. ${same ? '<b class="mr-ok">This one is already on the list.</b>' : ''} Rules: <a href="${SOTA_RULES}" target="_blank" rel="noopener">SOTA General Rules</a>.</p>`;
    box.appendChild(mailCard({
      id: 'sota', title: 'Email the SOTA Association Manager',
      note: `Association Manager from the SOTA database (checked ${CHECKED}; it updates live below if it changed).`,
      to: [{ call: am ? am[0] : '?', name: am ? am[1] : '', role: 'SOTA Association Manager, ' + assoc }],
      subject: () => `SOTA summit suggestion for ${assoc}: ${nameT}${call() ? ' from ' + call() : ''}`,
      body: () => {
        const p = promTxt();
        return `Hello ${am ? am[0] : ''},\n\nI'd like to suggest a summit for the ${assoc} SOTA list, if it qualifies. Here is what I found:\n\nSummit: ${nameT}\nState: ${ST[st] || st}${cty ? '\nCounty: ' + cty.county_name : ''}\nGPS (top): ${P}\nGrid square: ${grid}\nHeight: ${hereM ? ft(hereM) + ' ft (' + Math.round(hereM) + ' m) from ' + (el ? el.src : 'OpenStreetMap') : 'unknown'}${osmEle ? '\nOpenStreetMap peak height: ' + ft(osmEle) + ' ft (' + Math.round(osmEle) + ' m)' : ''}\nProminence: ${p ? p.ft + ' ft (' + Math.round(p.m) + ' m)' + (p.m >= 150 ? ' - meets the 150 m minimum' : ' - below the 150 m minimum') : 'not known yet (please check)'}\n\nNearest SOTA summits:\n${sNear.length ? sNear.slice(0, 4).map(s => `- ${s.ref} ${s.name}, ${s.ft} ft, ${(s.d * 0.621).toFixed(1)} mi away`).join('\n') : '- none within about 4 miles'}${same ? '\n(It may already be listed as ' + same.ref + '.)' : ''}\n\nLand at the top (USGS PAD-US): ${lands.length ? lands.slice(0, 3).map(x => (x.Unit_Nm || x.Loc_Nm || '?') + ', ' + (x.Loc_Own || '') + ', ' + (({ OA: 'open to the public', RA: 'restricted access', XA: 'closed', UK: 'access unknown' })[x.Pub_Access] || '')).join('; ') : 'no public land found (may be private)'}${pota.length ? '\nPOTA parks close by: ' + pota.filter(q => B.km(la, lo, q.la, q.lo) < 8).slice(0, 4).map(q => q.ref + ' ' + q.name).join('; ') : ''}${wwff.length ? '\nWWFF nearby: ' + wwff.slice(0, 3).map(x => x.ref + ' ' + x.name).join('; ') : ''}\n\nLinks:\n${links.map(l => `- ${l[0]}: ${l[1]}`).join('\n')}\n\nThank you for managing the association.\n\n73,\n${call() || '(YOUR CALL SIGN)'}\n\n(Research gathered with the Kentucky Portable Club summit helper. Heights and land data are from public map services; please check them against your sources.)`;
      }
    }));
    /* live check of the current Association Manager */
    B.jget(`https://api2.sota.org.uk/api/associations/${assoc}`, null, 15000).then(j => { if (j && j.associationManagerCallsign && sres && sres.assoc === assoc) { AM[assoc] = [j.associationManagerCallsign, j.manager || '']; const t = box.querySelector('.sg-to'); if (t) t.innerHTML = `<b>${esc(j.associationManagerCallsign)}</b>${j.manager ? ' · ' + esc(j.manager) : ''} <small>SOTA Association Manager, ${esc(assoc)} (live from SOTA)</small><br><small>Email address: on their QRZ page (free QRZ sign-in may be needed)</small> <a href="${qrz(j.associationManagerCallsign)}" target="_blank" rel="noopener">QRZ PAGE ↗</a>`; if (am) { am[0] = j.associationManagerCallsign; am[1] = j.manager || am[1]; } refreshAll(); } }).catch(() => {});
  }

  const h = (location.hash || '').slice(1); tab(h === 'summit' ? 'summit' : 'park');
  /* the page is locked until the password is entered (kpc-maprep.js unhides #mrApp): draw the summit map then */
  const app = $('mrApp'), wake = () => { if (app && !app.hidden && !$('sgSummit').hidden) { initMap(); if (smap) smap.invalidateSize(); } };
  if (app) new MutationObserver(wake).observe(app, { attributes: true, attributeFilter: ['hidden'] }); wake();
})();

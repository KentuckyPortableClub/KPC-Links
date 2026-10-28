/* Kentucky boundary ANSWER KEY (Oct 18 2026, Brandon OK'd the plan: 'park ↔ tract master list, built weekly, review list').
   Runs the site's own matching code (kpc-bounds.js, the same rules Park Control / In-Park / Kit use) over every Kentucky outline file and writes
   data/ky-answer-key.json:
     parks:   { ref: { n, t, tracts: [[layer, outline name, acres, how, pieces]] } }   how = name | alias | file | pin (pin = only "the park's pin is inside")
     nonum:   [[layer, name, acres, [POTA pins inside], [KFF inside], [SOTA on it]]]  government land with no POTA / KFF number of its own
     kffonly: [[layer, name, acres, [KFF refs]]]                                        outlines that are a KFF reference with no POTA number
     missing: [ref, ...]                                                                 POTA parks with no outline at all
   Usage: node .github/scripts/kpc_ky_key.js   (from the repo root; writes the file and prints a short summary + 'changes' as JSON on the last line) */
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = process.cwd();
const fakeFetch = async u => {
  const f = path.join(ROOT, String(u).split('?')[0]);
  if (!fs.existsSync(f)) return { ok: false, status: 404, json: async () => ({}) };
  const t = fs.readFileSync(f, 'utf8');
  return { ok: true, status: 200, json: async () => JSON.parse(t) };
};
const win = {};
const ctx = vm.createContext({ window: win, fetch: fakeFetch, AbortController, setTimeout, clearTimeout, console, document: undefined, navigator: {}, location: { href: '' } });
vm.runInContext(fs.readFileSync(path.join(ROOT, 'kpc-bounds.js'), 'utf8'), ctx);
const B = win.KPCB;

function acres(g) { // spherical-ish shoelace, holes subtracted
  let a = 0;
  for (const poly of B.ringsOf(g)) poly.forEach((r, i) => {
    let s = 0; const la0 = r.reduce((x, p) => x + p[1], 0) / r.length, kx = 111.32 * Math.cos(la0 * Math.PI / 180), ky = 110.57;
    for (let j = 0, k = r.length - 1; j < r.length; k = j++) s += (r[k][0] * kx) * (r[j][1] * ky) - (r[j][0] * kx) * (r[k][1] * ky);
    a += (i ? -1 : 1) * Math.abs(s / 2);
  });
  return Math.round(a * 247.105);
}

(async () => {
  const F = await B.ky(), D = B.kyData();
  const P = D.parks || [], parks = {}, nonum = [], kffonly = [];
  for (const x of P) parks[x.c] = { n: x.n, t: x.t || '', tracts: [] };
  const owned = {};   // Oct 27: Forest Service-owned parcels (thousands) = ONE tract per park: the land the agency owns
  for (const f of F) {
    if (f._L.own) { const r = (f.properties || {}).ref, o = owned[r] = owned[r] || [f._L.k, f._nm, 0, 'agency-owned land (ownership map)', 0]; o[2] += acres(f.geometry); o[4] += B.ringsOf(f.geometry).length; continue; }
    if (f._L.proc) { // the DBNF proclamation line: only one big outline, belongs to the forest
      (f._names || new Set()).forEach(r => parks[r] && parks[r].tracts.push([f._L.k, f._nm, acres(f.geometry), 'proclamation line']));
      continue;
    }
    const I = B.landInfo(f), A = acres(f.geometry), p = f.properties || {};
    if (I.own.length) I.own.forEach(o => {
      const how = p.ref === o.ref ? 'file' : B.sameName(o.name, f._nm) ? 'name' : 'alias';
      parks[o.ref] && parks[o.ref].tracts.push([f._L.k, f._nm, A, how, B.ringsOf(f.geometry).length]);
    });
    else if (I.kff.length) kffonly.push([f._L.k, f._nm, A, I.kff.map(k => k.ref)]);
    else {
      nonum.push([f._L.k, f._nm, A, I.pins.map(r => r.ref), I.kffIn.map(k => k.ref), I.sota.map(s => s.ref)]);
      // parks that only have "pin inside" outlines (kyFor falls back to that): mark them so the review list shows them
    }
  }
  for (const r in owned) if (parks[r]) parks[r].tracts.push(owned[r]);
  for (const x of P) if (!parks[x.c].tracts.length) {
    const g = await B.kyFor(x.c);
    g.forEach(f => parks[x.c].tracts.push([f._L.k, f._nm, acres(f.geometry), 'pin', B.ringsOf(f.geometry).length]));
  }
  // Oct 28 (HQ, Brandon): a park handed to a county / city keeps its POTA number and NEVER loses its outline. Tag who runs it;
  // when the state layer drops it and no other file holds it, keep the last official copy (from the previous key) and say so.
  let TR = {}; try { TR = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/park-transfers.json'), 'utf8')).parks || {}; } catch (e) {}
  let prev = null; try { prev = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/ky-answer-key.json'), 'utf8')); } catch (e) {}
  const kept = [];
  for (const r in TR) if (parks[r]) {
    parks[r].run_by = TR[r].by + (TR[r].since ? ' since ' + TR[r].since : '');
    if (TR[r].outline_note) parks[r].outline_note = TR[r].outline_note;   // Oct 28: e.g. Levi Jackson's PAD-US outline is ~174 ac short
    if (!parks[r].tracts.length && prev && prev.parks[r] && prev.parks[r].tracts.length) {
      parks[r].tracts = prev.parks[r].tracts.map(t => [t[0], t[1], t[2], 'kept: last official copy (transferred to ' + TR[r].by + ')', t[4] || 1]);
      kept.push(r);
    }
  }
  // Oct 28 (HQ + chat 8's Truth Checker read, measured): pieces that are the SAME land as another tract of the park, counted twice
  // in its acreage (raster check: Bissell Bluff 99.9% and Newman's Bluff 99.8% inside KDFWR's Livingston WMA polygon; KDFWR's Big South
  // Fork hunting polygon 99.3% inside the NPS unit). The park keeps its land; only the double count goes.
  const SAME_LAND = { 'US-3823': ['bsnp'], 'US-0686': ['bwma'] };
  for (const r in SAME_LAND) if (parks[r] && parks[r].tracts.some(t => !SAME_LAND[r].includes(t[0]))) {
    const gone = parks[r].tracts.filter(t => SAME_LAND[r].includes(t[0]));
    if (gone.length) { parks[r].tracts = parks[r].tracts.filter(t => !SAME_LAND[r].includes(t[0])); parks[r].same_land_dropped = gone.map(t => t[1] + ' (' + t[2] + ' ac, inside the main outline)'); }
  }
  // Oct 28 (HQ): Mammoth Cave = the land the Park Service OWNS (PAD-US fee 50,624 ac), not the authorized boundary (71,228 ac with
  // private inholdings); Land Between the Lakes = Forest Service-owned land (Basic Ownership, 'Land Between the Lakes NRA').
  const OWNED_ONLY = { 'US-0050': 'Park Service-owned land only (PAD-US fee records)', 'US-3792': 'Forest Service-owned land only (Basic Ownership)' };
  for (const r in OWNED_ONLY) if (parks[r]) parks[r].owned_only = OWNED_ONLY[r];
  const missing = P.filter(x => !parks[x.c].tracts.length).map(x => x.c);
  nonum.sort((a, b) => a[1].localeCompare(b[1])); kffonly.sort((a, b) => a[1].localeCompare(b[1]));
  for (const r in parks) parks[r].tracts.sort((a, b) => b[2] - a[2]);
  const out = { updated: new Date().toISOString().slice(0, 10), note: 'Built by .github/scripts/kpc_ky_key.js from the Kentucky outline files with the same rules the map tools use.', parks, nonum, kffonly, missing };
  const file = path.join(ROOT, 'data/ky-answer-key.json');
  let old = null; try { old = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) {}
  // what changed since last time (for the weekly issue comment)
  const ch = [];
  if (old) {
    for (const r in parks) {
      const a = (old.parks[r] || { tracts: [] }).tracts.map(t => t[0] + '|' + t[1]).sort().join(';'), b = parks[r].tracts.map(t => t[0] + '|' + t[1]).sort().join(';');
      if (!old.parks[r]) ch.push(`NEW PARK ${r} ${parks[r].n}: ${parks[r].tracts.length} outline piece(s)`);
      else if (a !== b) ch.push(`${r} ${parks[r].n}: outlines ${old.parks[r].tracts.length} → ${parks[r].tracts.length}`);
      if (TR[r] && (a !== b || kept.includes(r))) ch.push(`TRANSFERRED ${r} ${parks[r].n} (run by ${parks[r].run_by}): ${kept.includes(r) ? 'dropped off the state layer, last official copy KEPT' : 'outline source changed'}: check the new owner's map`);
    }
    const on = new Set(old.nonum.map(x => x[0] + '|' + x[1])), nn = new Set(nonum.map(x => x[0] + '|' + x[1]));
    nonum.filter(x => !on.has(x[0] + '|' + x[1])).forEach(x => ch.push(`NOW NO NUMBER: ${x[1]}`));
    old.nonum.filter(x => !nn.has(x[0] + '|' + x[1])).forEach(x => ch.push(`NO LONGER 'NO NUMBER': ${x[1]}`));
  }
  const same = old && JSON.stringify(Object.assign({}, old, { updated: '' })) === JSON.stringify(Object.assign({}, out, { updated: '' }));
  if (!same) fs.writeFileSync(file, JSON.stringify(out, null, 0).replace(/\],"/g, '],\n"').replace(/\},"/g, '},\n"') + '\n');
  const multi = Object.values(parks).filter(p => p.tracts.reduce((a, t) => a + (t[4] || 1), 0) > 1).length, weak = Object.entries(parks).filter(([, p]) => p.tracts.length && p.tracts.every(t => t[3] === 'pin')).map(([r]) => r);
  console.log(`${P.length} parks · ${P.length - missing.length} with outlines (${multi} in 2+ pieces) · ${weak.length} only by pin · ${missing.length} none · ${nonum.length} no-number outlines · ${kffonly.length} KFF-only`);
  console.log(JSON.stringify({ changes: ch, weak, missing, same: !!same }));
})();

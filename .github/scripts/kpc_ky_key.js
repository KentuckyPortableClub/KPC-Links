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
  for (const f of F) {
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
  for (const x of P) if (!parks[x.c].tracts.length) {
    const g = await B.kyFor(x.c);
    g.forEach(f => parks[x.c].tracts.push([f._L.k, f._nm, acres(f.geometry), 'pin', B.ringsOf(f.geometry).length]));
  }
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

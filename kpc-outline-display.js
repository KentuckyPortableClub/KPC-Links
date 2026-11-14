/* kpc-outline-display.js (KPC owner, 2026-11-13): the public map's NEW outline source, the DISPLAY COPY made from the outline
   store by tools/kpc_display_copy.py. OFF BY DEFAULT. No page includes this file yet; while that is so it changes nothing.
   When a page includes it (see docs/map-from-store.md, step 2), the official-outline layer asks kpcDisplayOutlines.load(area)
   first and keeps today's file for every park the display copy does not hold.

   Who sees the new outlines (wanted(area)):
     - nobody, by default;
     - one visitor who asks: ?outlines=store in the address (?outlines=old turns it off again; remembered in this browser), or
       the club-room toggle that sets localStorage kpcOutlineStore = '1';
     - everybody, for the areas the owner lists in LIVE_AREAS below (the go-live list; [] = none). Rollback = take the area out.
   Never used for "am I in the park" or 2-fers: drawing only.

   Files: data/display/<AREA>/INDEX.json (asked for fresh, like RELEASED.json), then its parts
   data/display/<AREA>/<AREA>.geojson.gz (+ .p2 ...) and fine/<REF>.geojson.gz, each with ?v=<its sha12> so the browser keeps an
   unchanged file and a changed one shows at once. Anything wrong (no index, a PRIVATE PREVIEW stamp, a part missing or of
   another build, bad gzip) = null: the caller draws today's outline, exactly as before. Never half an area, never blank. */
(function (w) {
  'use strict';
  var root = w || (typeof globalThis !== 'undefined' ? globalThis : {});
  if (root.kpcDisplayOutlines) return;
  var FORMAT = 'kpc-display-1', ROOT = 'data/display/', KEY = 'kpcOutlineStore';
  var LIVE_AREAS = [];   /* the owner's go-live list, e.g. ['US-NH'] once New Hampshire is proven. [] = nobody unless they ask */
  var idxCache = {}, areaCache = {}, fineCache = {};

  function ls(k, v) { try { if (v === undefined) return root.localStorage ? root.localStorage.getItem(k) : null; if (root.localStorage) { if (v === null) root.localStorage.removeItem(k); else root.localStorage.setItem(k, v); } } catch (e) {} return null; }
  function asked() {   /* ?outlines=store | old, remembered; else the stored toggle */
    var q = '';
    try { q = new URLSearchParams((root.location && root.location.search) || '').get('outlines') || ''; } catch (e) {}
    if (q === 'store') ls(KEY, '1'); else if (q === 'old') ls(KEY, null);
    return q === 'store' ? true : q === 'old' ? false : ls(KEY) === '1';
  }
  function wanted(area) {
    var a = String(area || '').toUpperCase();
    if (!/^(US|CA)-[A-Z]{2,3}$|^W-[A-Z]{2}$/.test(a)) return false;
    var q = '';
    try { q = new URLSearchParams((root.location && root.location.search) || '').get('outlines') || ''; } catch (e) {}
    if (q === 'old') { asked(); return false; }
    return asked() || LIVE_AREAS.indexOf(a) >= 0;
  }
  function gunzipJson(res) {
    return res.arrayBuffer().then(function (ab) {
      var u8 = new Uint8Array(ab);
      if (u8.length >= 2 && u8[0] === 0x1f && u8[1] === 0x8b) {
        if (typeof DecompressionStream !== 'function') throw new Error('gzip');
        return new Response(new Blob([ab]).stream().pipeThrough(new DecompressionStream('gzip'))).text().then(JSON.parse);
      }
      return JSON.parse(new TextDecoder().decode(ab));
    });
  }
  function get(url, mode) { return root.fetch(url, { cache: mode }).then(function (r) { if (!r || !r.ok) throw new Error('http'); return gunzipJson(r); }); }
  function goodIndex(x, area) {
    return !!(x && x.format === FORMAT && x.area === area && !x.stamp && Array.isArray(x.parts) && x.parts.length > 0 &&
      x.parts.every(function (p) { return Array.isArray(p) && typeof p[0] === 'string' && /^[0-9a-f]{12}$/.test(p[1]) && !/\.\.|^\//.test(p[0]); }));
  }
  function index(area) {   /* one fresh read per page; a failed read is tried again after a minute */
    var c = idxCache[area];
    if (c && !(c.at && Date.now() - c.at > 60000)) return c.p;
    c = idxCache[area] = { at: 0 };
    return (c.p = get(ROOT + area + '/INDEX.json', 'no-cache').then(function (x) { if (!goodIndex(x, area)) throw new Error('index'); return x; })
      .catch(function () { c.at = Date.now(); return null; }));
  }
  /* pure: the new features first, then today's feature for every park the display copy does not draw (fallback list, a park
     new since the store build, ...). Pin-only rows of today's file stay out, as today. */
  function merge(newFeats, oldFeats) {
    var have = {}, out = [];
    (newFeats || []).forEach(function (f) { var r = f && f.properties && f.properties.ref; if (r && !have[r]) { have[r] = 1; out.push(f); } });
    (oldFeats || []).forEach(function (f) { var p = (f && f.properties) || {}; if (p.ref && !have[p.ref] && p.g !== 'pin') { have[p.ref] = 1; out.push(f); } });
    return out;
  }
  function pack(feats, area, credits) { var by = {}; feats.forEach(function (f) { by[f.properties.ref] = f; }); return { features: feats, by: by, area: area, credits: credits || {}, source: 'store' }; }
  /* load(area, oldPack): oldPack = today's {features} (or a promise of it). -> a pack like kpcKeyOutlines.load gives, or null. */
  function load(area, oldPack) {
    area = String(area || '').toUpperCase();
    if (!wanted(area)) return Promise.resolve(null);
    if (!areaCache[area]) {
      areaCache[area] = index(area).then(function (x) {
        if (!x) return null;
        return Promise.all(x.parts.map(function (p) { return get(ROOT + area + '/' + p[0] + '?v=' + p[1], 'force-cache'); })).then(function (docs) {
          var n = x.parts.length, feats = [];
          for (var i = 0; i < docs.length; i++) {
            var k = (docs[i] && docs[i].kpc) || {};
            if (k.format !== FORMAT || k.area !== area || k.stamp || !Array.isArray(k.part) || k.part[0] !== i + 1 || k.part[1] !== n) return null;
            if (!Array.isArray(docs[i].features) || docs[i].features.length !== x.parts[i][2]) return null;
            feats = feats.concat(docs[i].features);
          }
          return { feats: feats, credits: x.credits || {}, fine: x.fine || {} };
        });
      }).catch(function () { return null; });
    }
    return Promise.all([areaCache[area], Promise.resolve(oldPack).catch(function () { return null; })]).then(function (r) {
      var d = r[0], old = r[1];
      if (!d) return null;
      return pack(merge(d.feats, old && old.features), area, d.credits);
    });
  }
  function mpp(zoom, lat) { return 156543.034 * Math.cos((lat || 0) * Math.PI / 180) / Math.pow(2, zoom || 0); }
  /* the finer copy is worth loading when the park's display detail is coarser than one screen pixel */
  function needFine(f, zoom, lat) { var p = (f && f.properties) || {}; return !!(p.fine && p.detail_m > mpp(zoom, lat)); }
  function fine(area, ref) {
    area = String(area || '').toUpperCase(); ref = String(ref || '').toUpperCase();
    var k = area + '|' + ref;
    if (!fineCache[k]) {
      fineCache[k] = index(area).then(function (x) {
        var e = x && x.fine && x.fine[ref];
        if (!e || !/^[0-9a-f]{12}$/.test(e[1]) || !/^fine\/[A-Z0-9-]+\.geojson\.gz$/.test(e[0])) return null;
        return get(ROOT + area + '/' + e[0] + '?v=' + e[1], 'force-cache').then(function (d) {
          var f = d && d.features && d.features[0], k2 = (d && d.kpc) || {};
          return f && k2.format === FORMAT && !k2.stamp && f.properties && f.properties.ref === ref ? f : null;
        });
      }).catch(function () { return null; });
    }
    return fineCache[k];
  }
  /* popup line: "Outline: <agency credit>" for a drawn park (credits come from the store index, per layer) */
  function creditLine(pk, f) {
    var p = (f && f.properties) || {};
    if (!pk || pk.source !== 'store' || !Array.isArray(p.cr) || !p.cr.length) return '';
    var seen = {}, names = p.cr.map(function (c) { return (pk.credits || {})[c] || c; }).filter(function (t) { return seen[t] ? false : (seen[t] = 1); });
    return 'Outline: ' + names.join('; ') + '. Check the official map before you set up.';
  }
  var api = { load: load, fine: fine, needFine: needFine, wanted: wanted, merge: merge, creditLine: creditLine, mpp: mpp,
              FORMAT: FORMAT, LIVE_AREAS: LIVE_AREAS.slice() };
  root.kpcDisplayOutlines = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : null);

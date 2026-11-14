/* kpc-outline-display.js (KPC owner, 2026-11-13; levels, pieces and parks across state lines 2026-11-14): the public map's NEW
   outline source, the DISPLAY COPY made from the outline store by tools/kpc_display_copy.py. OFF BY DEFAULT. No page includes
   this file yet; while that is so it changes nothing. When a page includes it (docs/map-from-store.md, step 3), the official-
   outline layer asks kpcDisplayOutlines.load(area) first and keeps today's file for every park the display copy does not hold.

   Who sees the new outlines (wanted(area)):
     - nobody, by default;
     - one visitor who asks: ?outlines=store in the address (?outlines=old turns it off again; remembered in this browser), or
       the club-room toggle that sets localStorage kpcOutlineStore = '1';
     - everybody, for the areas the owner lists in LIVE_AREAS below (the go-live list; [] = none). Rollback = take the area out.
   Never used for "am I in the park" or 2-fers: drawing only.

   Three levels (level(pack, f, zoom, lat) picks one; the rule: never more than about one screen pixel off):
     overview  data/display/<AREA>/<AREA>.geojson.gz (+ .p2 ...), every park, at most 3,000 points: used while its detail_m is
               no more than one pixel;
     middle    mid/<REF>.geojson.gz, one file, at most 30,000 points: used up to zoom 13 (and later while it is within a pixel);
     fine      fine/<REF>/<ix>_<iy>.geojson.gz pieces (T x T degree tiles, each under 128 KB): from zoom 14, only the pieces
               the screen touches (at most MAX_PIECES per look), within 5 m of the store.
   Each file is asked for with ?v=<its sha12> and kept by the browser; INDEX.json is asked for fresh (like RELEASED.json).
   A park across areas (properties.areas) is drawn new only when every one of its areas is wanted AND their indexes come from
   the same build (gen); otherwise today's outline, in every area. Anything wrong (no index, a PRIVATE PREVIEW stamp, a part
   missing or of another build, bad gzip) = null: the caller draws today's outline, exactly as before. Never half an area. */
(function (w) {
  'use strict';
  var root = w || (typeof globalThis !== 'undefined' ? globalThis : {});
  if (root.kpcDisplayOutlines) return;
  var FORMAT = 'kpc-display-2', ROOT = 'data/display/', KEY = 'kpcOutlineStore', FINE_MIN_Z = 14, MID_MAX_Z = 13, MAX_PIECES = 48;
  var LIVE_AREAS = [];   /* the owner's go-live list, e.g. ['US-NH', 'US-ME'] once proven. [] = nobody unless they ask */
  var AREA_RX = /^(US|CA)-[A-Z]{2,3}$|^W-[A-Z]{2}$/;
  var idxCache = {}, areaCache = {}, fileCache = {};

  function ls(k, v) { try { if (v === undefined) return root.localStorage ? root.localStorage.getItem(k) : null; if (root.localStorage) { if (v === null) root.localStorage.removeItem(k); else root.localStorage.setItem(k, v); } } catch (e) {} return null; }
  function param() { try { return new URLSearchParams((root.location && root.location.search) || '').get('outlines') || ''; } catch (e) { return ''; } }
  function asked() {   /* ?outlines=store | old, remembered; else the stored toggle */
    var q = param();
    if (q === 'store') ls(KEY, '1'); else if (q === 'old') ls(KEY, null);
    return q === 'store' ? true : q === 'old' ? false : ls(KEY) === '1';
  }
  function wanted(area) {
    var a = String(area || '').toUpperCase();
    if (!AREA_RX.test(a)) return false;
    if (param() === 'old') { asked(); return false; }
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
  function cached(url) { if (!fileCache[url]) fileCache[url] = get(url, 'force-cache').catch(function (e) { delete fileCache[url]; throw e; }); return fileCache[url]; }
  var SHA = /^[0-9a-f]{12}$/, NAME = /^[A-Z0-9-]+(\.p\d+)?\.geojson\.gz$/;
  function goodIndex(x, area) {
    return !!(x && x.format === FORMAT && x.area === area && !x.stamp && SHA.test(x.gen || '') && Array.isArray(x.parts) && x.parts.length > 0 &&
      x.parts.every(function (p) { return Array.isArray(p) && NAME.test(p[0]) && SHA.test(p[1]); }));
  }
  function index(area) {   /* one fresh read per page; a failed read is tried again after a minute */
    var c = idxCache[area];
    if (c && !(c.at && Date.now() - c.at > 60000)) return c.p;
    c = idxCache[area] = { at: 0 };
    return (c.p = get(ROOT + area + '/INDEX.json', 'no-cache').then(function (x) { if (!goodIndex(x, area)) throw new Error('index'); return x; })
      .catch(function () { c.at = Date.now(); return null; }));
  }
  /* pure: the new features (all of a park's: 'line' and 'hit' too) first, then today's feature for every park the display copy
     does not draw. Pin rows of today's file stay out, as today. */
  function merge(newFeats, oldFeats) {
    var have = {}, out = [];
    (newFeats || []).forEach(function (f) { var r = f && f.properties && f.properties.ref; if (r) { have[r] = 1; out.push(f); } });
    (oldFeats || []).forEach(function (f) { var p = (f && f.properties) || {}; if (p.ref && !have[p.ref] && p.g !== 'pin') { have[p.ref] = 1; out.push(f); } });
    return out;
  }
  /* a park across areas: every one of its areas wanted and from the same build, else none of it is new */
  function partnersOk(feats, area, gen) {
    var need = {};
    feats.forEach(function (f) { (f.properties.areas || []).forEach(function (a) { if (a !== area) need[a] = 1; }); });
    var list = Object.keys(need);
    return Promise.all(list.map(function (a) { return wanted(a) ? index(a).then(function (x) { return !!(x && x.gen === gen); }) : Promise.resolve(false); }))
      .then(function (ok) { var m = {}; list.forEach(function (a, i) { m[a] = ok[i]; }); return m; });
  }
  function pack(feats, area, x) {
    var by = {};
    feats.forEach(function (f) { var r = f.properties.ref; if (!by[r] || f.properties.role !== 'hit') by[r] = f; });
    return { features: feats, by: by, area: area, credits: x.credits || {}, index: x, source: 'store' };
  }
  /* load(area, oldPack): oldPack = today's {features} (or a promise of it). -> a pack like kpcKeyOutlines.load gives, or null. */
  function load(area, oldPack) {
    area = String(area || '').toUpperCase();
    if (!wanted(area)) return Promise.resolve(null);
    if (!areaCache[area]) {
      areaCache[area] = index(area).then(function (x) {
        if (!x) return null;
        return Promise.all(x.parts.map(function (p) { return cached(ROOT + area + '/' + p[0] + '?v=' + p[1]); })).then(function (docs) {
          var n = x.parts.length, feats = [];
          for (var i = 0; i < docs.length; i++) {
            var k = (docs[i] && docs[i].kpc) || {};
            if (k.format !== FORMAT || k.area !== area || k.gen !== x.gen || k.stamp || !Array.isArray(k.part) || k.part[0] !== i + 1 || k.part[1] !== n) return null;
            if (!Array.isArray(docs[i].features) || docs[i].features.length !== x.parts[i][2]) return null;
            feats = feats.concat(docs[i].features);
          }
          return partnersOk(feats, area, x.gen).then(function (ok) {
            feats = feats.filter(function (f) { return (f.properties.areas || []).every(function (a) { return a === area || ok[a]; }); });
            return { feats: feats, x: x };
          });
        });
      }).catch(function () { return null; });
    }
    return Promise.all([areaCache[area], Promise.resolve(oldPack).catch(function () { return null; })]).then(function (r) {
      var d = r[0], old = r[1];
      if (!d) return null;
      return pack(merge(d.feats, old && old.features), area, d.x);
    });
  }
  function mpp(zoom, lat) { return 156543.034 * Math.cos((lat || 0) * Math.PI / 180) / Math.pow(2, zoom || 0); }
  /* which level to draw a park at: 'overview' | 'mid' | 'fine' (never more than about a pixel off where a finer level exists) */
  function level(pk, f, zoom, lat) {
    var p = (f && f.properties) || {}, m = mpp(zoom, lat), x = (pk && pk.index) || {};
    if (!(p.detail_m > m)) return 'overview';
    var md = p.mid && x.mid && x.mid[p.ref];
    if (zoom < FINE_MIN_Z || !p.fine) return md ? 'mid' : 'overview';
    if (md && !(md[2] > m)) return 'mid';
    return 'fine';
  }
  function mid(area, ref) {
    area = String(area || '').toUpperCase(); ref = String(ref || '').toUpperCase();
    return index(area).then(function (x) {
      var e = x && x.mid && x.mid[ref];
      if (!e || !SHA.test(e[1]) || e[0] !== 'mid/' + ref + '.geojson.gz') return null;
      return cached(ROOT + area + '/' + e[0] + '?v=' + e[1]).then(function (d) {
        var f = d && d.features && d.features[0], k = (d && d.kpc) || {};
        return f && k.format === FORMAT && k.gen === x.gen && !k.stamp && f.properties && f.properties.ref === ref ? f : null;
      });
    }).catch(function () { return null; });
  }
  /* the fine pieces of one park that the box [west, south, east, north] touches (at most MAX_PIECES). -> [feature, ...] */
  function fine(area, ref, box) {
    area = String(area || '').toUpperCase(); ref = String(ref || '').toUpperCase();
    return index(area).then(function (x) {
      var e = x && x.fine && x.fine[ref];
      if (!e || !(e.t > 0) || !e.tiles || !Array.isArray(box)) return [];
      var T = e.t, keys = [];
      for (var ix = Math.floor(box[0] / T); ix <= Math.floor(box[2] / T); ix++)
        for (var iy = Math.floor(box[1] / T); iy <= Math.floor(box[3] / T); iy++) {
          var k = ix + '_' + iy;
          if (e.tiles[k] && SHA.test(e.tiles[k][0])) keys.push(k);
          if (keys.length > MAX_PIECES) return [];      /* too many for one look: stay on the middle level */
        }
      return Promise.all(keys.map(function (k) {
        return cached(ROOT + area + '/fine/' + ref + '/' + k + '.geojson.gz?v=' + e.tiles[k][0]).then(function (d) {
          var kk = (d && d.kpc) || {};
          return kk.format === FORMAT && kk.gen === x.gen && !kk.stamp && kk.fine === ref && d.features && d.features[0] ? d.features[0] : null;
        }, function () { return null; });
      })).then(function (fs) { return fs.filter(Boolean); });
    }).catch(function () { return []; });
  }
  /* popup line: "Outline: <agency credit>" for a drawn park (credits come from the store index, per layer) */
  function creditLine(pk, f) {
    var p = (f && f.properties) || {};
    if (!pk || pk.source !== 'store' || !Array.isArray(p.cr) || !p.cr.length) return '';
    var seen = {}, names = p.cr.map(function (c) { return (pk.credits || {})[c] || c; }).filter(function (t) { return seen[t] ? false : (seen[t] = 1); });
    return 'Outline: ' + names.join('; ') + '. Check the official map before you set up.';
  }
  var api = { load: load, mid: mid, fine: fine, level: level, wanted: wanted, merge: merge, creditLine: creditLine, mpp: mpp,
              FORMAT: FORMAT, FINE_MIN_Z: FINE_MIN_Z, MID_MAX_Z: MID_MAX_Z, MAX_PIECES: MAX_PIECES, LIVE_AREAS: LIVE_AREAS.slice() };
  root.kpcDisplayOutlines = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : null);

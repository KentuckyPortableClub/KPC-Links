/* Shared Kentucky answer-key lookup (Park Commander + KY trip planner).
   The saved data/ky-answer-key.json already joins some official outlines whose names
   differ from the POTA name (how = alias, file, or name). Load it once, lazily.
   Look up by layer + outline name. */
(function (w) {
  'use strict';
  let keyIdx = null, keyTried = false, keyReadyP = null;
  function outlineName(f) {
    const p = (f && f.properties) || {};
    const n = p.NAME || p.Name || p.name || p.UNIT_NAME || p.UNITNAME || '';
    return String(n).trim();
  }
  function layerOf(f) { return (f && (f._lk || (f._L && f._L.k))) || ''; }
  function buildKeyIdx(j) {
    const m = new Map();
    for (const ref of Object.keys((j && j.parks) || {})) {
      const p = j.parks[ref];
      for (const t of p.tracts || []) {
        if (!t || !t[0] || !t[1]) continue;
        const k = t[0] + '\t' + t[1];
        if (!m.has(k)) m.set(k, []);
        if (!m.get(k).some(x => x.ref === ref)) m.get(k).push({ ref, n: p.n || '', how: t[3] || '' });
      }
    }
    return m;
  }
  function useAnswerKey(j) { keyIdx = buildKeyIdx(j); keyTried = true; keyReadyP = Promise.resolve(keyIdx); return keyIdx; }
  function loadKey(onReady) {
    if (keyTried) return keyReadyP;
    keyTried = true;
    keyReadyP = fetch('data/ky-answer-key.json?v=20261110aj', { cache: 'force-cache' })
      .then(r => r.ok ? r.json() : null)
      .then(j => { keyIdx = buildKeyIdx(j); if (typeof onReady === 'function') onReady(keyIdx); return keyIdx; })
      .catch(() => { keyIdx = new Map(); if (typeof onReady === 'function') onReady(keyIdx); return keyIdx; });
    return keyReadyP;
  }
  function keyOf(layer, name) { return (keyIdx && layer && name) ? (keyIdx.get(layer + '\t' + name) || []) : []; }
  function keyJoin(f, nameFn) { loadKey(); return keyOf(layerOf(f), (nameFn || outlineName)(f)); }
  function ready() { return keyIdx !== null; }
  w.kpcAnswerKey = { buildKeyIdx, useAnswerKey, loadKey, keyOf, keyJoin, ready, outlineName, layerOf };
})(typeof window !== 'undefined' ? window : globalThis);

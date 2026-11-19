/* KPC app: SECRETS AT REST (Nov 18 full review SEC-2 / X5 / L17). Passwords, API keys and sign-in tickets are kept SEALED when the
   device can do it: the Windows app = Electron safeStorage (Windows' own DPAPI, tied to this Windows user). A sealed value is
   'kpcsec1:<base64>' in localStorage; anything else is read as it is (older settings, Android, a browser), and is sealed the next
   time it is saved. Android: plain localStorage inside the app's private storage for now (a Keystore plugin is on the list).
   KPCSec.sealObj(obj, ['qrz.key', …]) → a copy with those fields sealed · openObj(obj, paths) → a copy with them opened. */
(function (G) {
  'use strict';
  const P = 'kpcsec1:', B = () => G.kpcSecure;
  const ok = () => { try { return !!(B() && B().ok()); } catch (e) { return false; } };
  function seal(v) { if (v == null || v === '' || typeof v !== 'string' || v.startsWith(P) || !ok()) return v; try { const s = B().seal(v); return s ? P + s : v; } catch (e) { return v; } }
  function open(v) { if (typeof v !== 'string' || !v.startsWith(P)) return v; try { const s = B() && B().open(v.slice(P.length)); return typeof s === 'string' ? s : ''; } catch (e) { return ''; } }
  const getP = (o, p) => p.split('.').reduce((a, k) => a == null ? a : a[k], o);
  const setP = (o, p, v) => { const k = p.split('.'), last = k.pop(); let a = o; for (const x of k) { if (a[x] == null || typeof a[x] !== 'object') return; a = a[x]; } if (last in a) a[last] = v; };
  const copy = o => o == null ? o : JSON.parse(JSON.stringify(o));
  function sealObj(o, paths) { const c = copy(o); if (!c || typeof c !== 'object') return c; paths.forEach(p => setP(c, p, seal(getP(c, p)))); return c; }
  function openObj(o, paths) { const c = copy(o); if (!c || typeof c !== 'object') return c; paths.forEach(p => setP(c, p, open(getP(c, p)))); return c; }
  G.KPCSec = { ok, seal, open, sealObj, openObj, PREFIX: P };
})(window);

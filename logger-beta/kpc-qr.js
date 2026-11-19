/* KPC app: a small QR code maker (Nov 19 2026, to-do 15: 'the PC shows a QR code that the iPhone scans to open the phone page at
   the PC's address'). Written from the QR code standard (ISO/IEC 18004): byte mode, error correction level M, versions 1-10 (up to
   213 letters, plenty for 'http://192.168.1.23:8731/phone/'), all 8 masks tried and the best kept. Our own code, nothing copied.
   KPCQR.svg(text, {px, margin}) → an SVG string (black on white: phone cameras read that best); KPCQR.matrix(text) → rows of 0/1. */
(function (G) {
  'use strict';
  /* ---- GF(256) for the Reed-Solomon check bytes ---- */
  const EXP = new Array(512), LOG = new Array(256);
  { let x = 1; for (let i = 0; i < 255; i++) { EXP[i] = x; LOG[x] = i; x <<= 1; if (x & 0x100) x ^= 0x11d; } for (let i = 255; i < 512; i++) EXP[i] = EXP[i - 255]; }
  const mul = (a, b) => (a && b ? EXP[LOG[a] + LOG[b]] : 0);
  function rsGen(n) { let g = [1]; for (let i = 0; i < n; i++) { const ng = new Array(g.length + 1).fill(0); for (let j = 0; j < g.length; j++) { ng[j] ^= g[j]; ng[j + 1] ^= mul(g[j], EXP[i]); } g = ng; } return g; }
  function rsRem(data, n) { const g = rsGen(n), r = data.concat(new Array(n).fill(0)); for (let i = 0; i < data.length; i++) { const c = r[i]; if (c) for (let j = 0; j < g.length; j++) r[i + j] ^= mul(g[j], c); } return r.slice(data.length); }
  /* ---- level M: [EC bytes per block, [[blocks, data bytes per block], …]] for versions 1-10 ---- */
  const M = [null, [10, [[1, 16]]], [16, [[1, 28]]], [26, [[1, 44]]], [18, [[2, 32]]], [24, [[2, 43]]], [16, [[4, 27]]], [18, [[4, 31]]], [22, [[2, 38], [2, 39]]], [22, [[3, 36], [2, 37]]], [26, [[4, 43], [1, 44]]]];
  const ALIGN = [null, [], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34], [6, 22, 38], [6, 24, 42], [6, 26, 46], [6, 28, 50]];
  const dataCap = v => M[v][1].reduce((a, [n, d]) => a + n * d, 0);
  function bits(text, v) {
    const b = [...new TextEncoder().encode(text)], out = [];
    const put = (val, n) => { for (let i = n - 1; i >= 0; i--) out.push((val >> i) & 1); };
    put(4, 4); put(b.length, v < 10 ? 8 : 16); b.forEach(x => put(x, 8));
    const cap = dataCap(v) * 8; for (let i = 0; i < 4 && out.length < cap; i++) out.push(0);
    while (out.length % 8) out.push(0);
    const bytes = []; for (let i = 0; i < out.length; i += 8) bytes.push(parseInt(out.slice(i, i + 8).join(''), 2));
    for (let p = 0; bytes.length < dataCap(v); p++) bytes.push(p % 2 ? 0x11 : 0xec);
    return bytes;
  }
  function codewords(text, v) {
    const data = bits(text, v), [ec, groups] = M[v], blocks = []; let k = 0;
    groups.forEach(([n, d]) => { for (let i = 0; i < n; i++) { const blk = data.slice(k, k + d); k += d; blocks.push({ d: blk, e: rsRem(blk, ec) }); } });
    const out = [], maxD = Math.max(...blocks.map(x => x.d.length));
    for (let i = 0; i < maxD; i++) blocks.forEach(x => { if (i < x.d.length) out.push(x.d[i]); });
    for (let i = 0; i < ec; i++) blocks.forEach(x => out.push(x.e[i]));
    return out;
  }
  /* ---- the picture ---- */
  function build(text, v, mask) {
    const N = v * 4 + 17, m = [], fn = [];
    for (let i = 0; i < N; i++) { m.push(new Array(N).fill(0)); fn.push(new Array(N).fill(false)); }
    const set = (r, c, val) => { m[r][c] = val ? 1 : 0; fn[r][c] = true; };
    const finder = (r, c) => { for (let i = -1; i <= 7; i++) for (let j = -1; j <= 7; j++) { const rr = r + i, cc = c + j; if (rr < 0 || cc < 0 || rr >= N || cc >= N) continue;
      const on = i >= 0 && i <= 6 && j >= 0 && j <= 6 && (i === 0 || i === 6 || j === 0 || j === 6 || (i >= 2 && i <= 4 && j >= 2 && j <= 4)); set(rr, cc, on); } };
    finder(0, 0); finder(0, N - 7); finder(N - 7, 0);
    for (let i = 8; i < N - 8; i++) { set(6, i, i % 2 === 0); set(i, 6, i % 2 === 0); }
    const A = ALIGN[v]; for (const r of A) for (const c of A) { if ((r === 6 && c === 6) || (r === 6 && c === A[A.length - 1]) || (r === A[A.length - 1] && c === 6)) continue;
      for (let i = -2; i <= 2; i++) for (let j = -2; j <= 2; j++) set(r + i, c + j, Math.max(Math.abs(i), Math.abs(j)) !== 1); }
    /* format info (level M = 00) with its BCH bits, both copies; the dark module */
    let f = (0 << 3) | mask, rem = f << 10; for (let i = 14; i >= 10; i--) if ((rem >> i) & 1) rem ^= 0x537 << (i - 10);
    const fmt = ((f << 10) | rem) ^ 0x5412, fb = i => (fmt >> i) & 1;
    for (let i = 0; i <= 5; i++) set(i, 8, fb(i)); set(7, 8, fb(6)); set(8, 8, fb(7)); set(8, 7, fb(8)); for (let i = 9; i < 15; i++) set(8, 14 - i, fb(i));   /* (row, column) */
    for (let i = 0; i < 8; i++) set(8, N - 1 - i, fb(i)); for (let i = 8; i < 15; i++) set(N - 15 + i, 8, fb(i));
    set(N - 8, 8, 1);
    if (v >= 7) { let r2 = v << 12; for (let i = 17; i >= 12; i--) if ((r2 >> i) & 1) r2 ^= 0x1f25 << (i - 12); const vi = (v << 12) | r2;
      for (let i = 0; i < 18; i++) { const b = (vi >> i) & 1, a = Math.floor(i / 3), c = i % 3 + N - 11; set(a, c, b); set(c, a, b); } }
    /* the data, two columns at a time from the bottom right, up and down in turn */
    const cw = codewords(text, v), bitsAll = []; cw.forEach(x => { for (let i = 7; i >= 0; i--) bitsAll.push((x >> i) & 1); });
    let k = 0, up = true;
    for (let col = N - 1; col > 0; col -= 2) { if (col === 6) col = 5;
      for (let n = 0; n < N; n++) { const r = up ? N - 1 - n : n;
        for (let j = 0; j < 2; j++) { const c = col - j; if (fn[r][c]) continue; let b = k < bitsAll.length ? bitsAll[k] : 0; k++;
          const mk = [(r + c) % 2 === 0, r % 2 === 0, c % 3 === 0, (r + c) % 3 === 0, (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0, (r * c) % 2 + (r * c) % 3 === 0, ((r * c) % 2 + (r * c) % 3) % 2 === 0, ((r + c) % 2 + (r * c) % 3) % 2 === 0][mask];
          m[r][c] = b ^ (mk ? 1 : 0); } }
      up = !up; }
    return m;
  }
  /* the standard's penalty score: runs, 2x2 blocks, finder look-alikes, dark balance */
  function score(m) {
    const N = m.length; let s = 0;
    for (let pass = 0; pass < 2; pass++) for (let i = 0; i < N; i++) { let run = 1; for (let j = 1; j <= N; j++) { const a = pass ? m[j - 1] && m[j - 1][i] : m[i][j - 1], b = j < N ? (pass ? m[j][i] : m[i][j]) : -1;
      if (b === a) run++; else { if (run >= 5) s += run - 2; run = 1; } } }
    for (let i = 0; i < N - 1; i++) for (let j = 0; j < N - 1; j++) { const c = m[i][j]; if (c === m[i][j + 1] && c === m[i + 1][j] && c === m[i + 1][j + 1]) s += 3; }
    const P1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], P2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1];
    for (let i = 0; i < N; i++) for (let j = 0; j + 11 <= N; j++) for (const P of [P1, P2]) { if (P.every((x, k) => m[i][j + k] === x)) s += 40; if (P.every((x, k) => m[j + k][i] === x)) s += 40; }
    let dark = 0; m.forEach(r => r.forEach(x => { dark += x; })); s += Math.floor(Math.abs(dark * 100 / (N * N) - 50) / 5) * 10;
    return s;
  }
  function matrix(text) {
    const len = new TextEncoder().encode(String(text)).length; let v = 1;
    while (v <= 10 && dataCap(v) * 8 < 4 + (v < 10 ? 8 : 16) + len * 8) v++;
    if (v > 10) throw new Error('too long for a QR code here');
    let best = null, bs = Infinity; for (let mk = 0; mk < 8; mk++) { const m = build(String(text), v, mk), sc = score(m); if (sc < bs) { bs = sc; best = m; } }
    return best;
  }
  function svg(text, o) {
    o = o || {}; const m = matrix(text), N = m.length, q = o.margin == null ? 4 : o.margin, px = o.px || 6, W = (N + 2 * q) * px; let d = '';
    m.forEach((r, i) => r.forEach((x, j) => { if (x) d += `M${(j + q) * px} ${(i + q) * px}h${px}v${px}h-${px}z`; }));
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${W}" viewBox="0 0 ${W} ${W}" shape-rendering="crispEdges" role="img" aria-label="QR code: ${String(text).replace(/[<>&"]/g, '')}"><rect width="${W}" height="${W}" fill="#fff"/><path d="${d}" fill="#000"/></svg>`;
  }
  G.KPCQR = { matrix, svg };
})(window);

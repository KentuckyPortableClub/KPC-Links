#!/usr/bin/env python3
"""Split big overlap shapes out of a 2-fer area file (chat 3, Oct 29; for chat 2's save step).

WHY: Alaska's results file came out 135 MB (GitHub refuses > 100 MB) because each spot stores its
patch 'shape' + the park edges 'lines' + the trail 'zone' inline. Those three are ~95% of the file.

WHAT IT DOES (lossless, nothing is made coarser: R-G6 3 m detail stays):
  data/fers/US-AK.json(.gz)  ->  same file, but a spot whose shape+lines+zone weigh more than
                                 --max-inline bytes keeps only box / center / acres / status ... and
                                 gets  "heavy": "shapes/US-AK/<id hash>"   (+ "heavy_n": byte count, "shape_sig": a short fingerprint of the shape
                                 so the Finder can still hide a duplicate stretch without loading it)
  data/fers/shapes/US-AK/<hash>.json.gz = {"id": <spot id>, "shape": ..., "lines": ..., "zone": ...}
The Overlap Finder (kpc-overlap-finder.js, hydrate()) reads that file only when the row is opened.
Readers that use only center / box / status / refs (checker, far-hold, far-check, layered) are untouched.
A spot with no heavy parts, or small ones, stays exactly as it was (no heavy field).

USE:   python3 split_fers_shapes.py data/fers/US-AK.json [--out-dir data/fers] [--max-inline 20000] [--gz]
       python3 split_fers_shapes.py data/fers/US-AK.json --check      # re-joins and proves it is identical
Writes the slimmed file next to the input (same name; .json.gz when --gz or the input was .gz).
"""
import argparse, gzip, hashlib, json, os, sys
HEAVY = ('shape', 'lines', 'zone')

def load(p):
    op = gzip.open if p.endswith('.gz') else open
    with op(p, 'rt', encoding='utf-8') as f: return json.load(f)

def dump(obj, p, gz):
    s = json.dumps(obj, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    if gz:
        with open(p, 'wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', compresslevel=9, mtime=0) as g: g.write(s)
    else:
        with open(p, 'wb') as f: f.write(s)
    return len(s)

def hid(sid): return hashlib.sha1(sid.encode('utf-8')).hexdigest()[:14]

def region_name(p):
    b = os.path.basename(p)
    for e in ('.json.gz', '.json'):
        if b.endswith(e): return b[:-len(e)]
    return b

def split(p, out_dir, max_inline, gz):
    d = load(p); reg = region_name(p); sh_dir = os.path.join(out_dir, 'shapes', reg)
    n_split = 0; moved = 0
    for s in d.get('spots', []):
        parts = {k: s[k] for k in HEAVY if k in s and s[k]}
        w = len(json.dumps(parts, separators=(',', ':')))
        if not parts or w <= max_inline or 'heavy' in s: continue
        os.makedirs(sh_dir, exist_ok=True)
        name = hid(s['id']); dump(dict(id=s['id'], **parts), os.path.join(sh_dir, name + '.json.gz'), True)
        for k in parts: del s[k]
        s['heavy'] = 'shapes/%s/%s' % (reg, name); s['heavy_n'] = w; n_split += 1; moved += w
        s['shape_sig'] = hashlib.sha1(json.dumps(parts.get('shape'), separators=(',', ':')).encode('utf-8')).hexdigest()[:12]   # lets the Finder spot a duplicate stretch without loading it
        if 'box' not in s or 'center' not in s: print('WARNING spot %s has no box/center' % s['id'], file=sys.stderr)
    out = os.path.join(out_dir, reg + ('.json.gz' if gz else '.json'))
    size = dump(d, out, gz)
    print('%s: %d spots split, %.1f MB moved apart, slim file %.1f MB%s' % (reg, n_split, moved / 1e6, size / 1e6, ' (raw JSON; gz smaller)' if gz else ''))
    return out

def rejoin(p, base):
    d = load(p)
    for s in d.get('spots', []):
        if 'heavy' in s:
            h = load(os.path.join(base, s['heavy'] + '.json.gz')); assert h['id'] == s['id']
            for k in HEAVY:
                if k in h: s[k] = h[k]
            del s['heavy']; s.pop('heavy_n', None); s.pop('shape_sig', None)
    return d

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--out-dir', default=None)
    ap.add_argument('--max-inline', type=int, default=20000); ap.add_argument('--gz', action='store_true')
    ap.add_argument('--check', action='store_true', help='split a copy and prove the re-joined file equals the original')
    a = ap.parse_args(); out_dir = a.out_dir or os.path.dirname(os.path.abspath(a.file))
    if a.check:
        import tempfile
        t = tempfile.mkdtemp(); o = split(a.file, t, a.max_inline, a.gz)
        same = rejoin(o, t) == load(a.file); print('LOSSLESS' if same else 'DIFFERENT'); sys.exit(0 if same else 1)
    split(a.file, out_dir, a.max_inline, a.gz or a.file.endswith('.gz'))

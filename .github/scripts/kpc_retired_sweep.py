#!/usr/bin/env python3
"""Take RETIRED Kentucky POTA parks off everything the site lists (Opus, Oct 23 2026).

Brandon Oct 23: 'someone said there was a retired park still showing ... remove from anything that lists it and make sure
it dont happen again'. On Oct 22 three parks were taken out of kpc-ky-data.json, but they were still in the map download
files (KML/GPX), the KPC-drawn and PAD-US outline layers, the Top 25 list and its PDF; Martin's Fork (US-7969, retired
Oct 18) was still in both Resource guide PDFs and the WWFF guide. Each list had its own copy.

The list of retired parks is data/ky-retired.json (kpc_refcheck.py adds to it when POTA's active list drops a park).
  python3 .github/scripts/kpc_retired_sweep.py          look only: print every file that still mentions one
  python3 .github/scripts/kpc_retired_sweep.py --fix    take them out, rebuild the map files + Top 25, then look again
Leftovers it cannot fix by itself are printed as ::warning lines and returned in leftovers() for the ref-check issue.

LEAVE ALONE (on purpose): bot memory (data/new-refs/seen.json, data/ky-lands-seen.json: removing a park there makes the
bot announce it again), data/kpc-post-holds.json, data/ky-answer-key.json (kpc-ky-key.yml rebuilds it every Monday), data/leaders/ (who activated what: real history), notes and PDFs
(the PDFs are reprinted from the guide pages by kpc-guide-pdf.yml every Monday).
To bring a park back: take it out of data/ky-retired.json first, then follow .claude/build/mapfiles/retired-parks.md."""
import glob
import json
import os
import re
import subprocess
import sys

RET = 'data/ky-retired.json'
SKIP = re.compile(r'^(\.git|\.claude|\.github|cache|node_modules|data/new-refs|data/ky-lands-seen|data/kpc-post-holds|data/leaders|data/us-key|data/ca-key|data/world-key|data/world-bounds|data/canada-bounds|data/ky-retired|data/retired-refs|data/ky-answer-key|data/bot-health)(\.json)?(/|$)|\.pdf$')
REF = re.compile(r'^[A-Z0-9]{1,4}-\d{4,5}$')
LOOK = ('.html', '.js', '.json', '.geojson', '.kml', '.gpx', '.csv', '.txt')


def notice(t, m): print(f'::notice title={t}::{m}', flush=True)


def retired():
    try:
        return {r['c']: r for r in json.load(open(RET, encoding='utf-8'))['parks']}
    except FileNotFoundError:
        return {}


def add_retired(rows, when):
    """rows = [(ref, name)]; called by kpc_refcheck.py. Returns the refs that were new to the list."""
    try:
        d = json.load(open(RET, encoding='utf-8'))
    except FileNotFoundError:
        d = {'note': 'Kentucky POTA parks POTA has retired. kpc_retired_sweep.py keeps them off every site list.', 'parks': []}
    have = {r['c'] for r in d['parks']}
    new = [(c, n) for c, n in rows if c not in have]
    for c, n in new:
        d['parks'].append({'c': c, 'n': n, 'when': when})
    if new:
        json.dump(d, open(RET, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        open(RET, 'a').write('\n')
    return [c for c, _ in new]


def drop_retired(refs):
    """a park POTA brought back: off the retired list (kpc_refcheck.py)"""
    try:
        d = json.load(open(RET, encoding='utf-8'))
    except FileNotFoundError:
        return
    d['parks'] = [r for r in d['parks'] if r['c'] not in set(refs)]
    json.dump(d, open(RET, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(RET, 'a').write('\n')


def _layout(orig):
    """keep a file's own JSON layout (one line, or indented by 1 or 2)"""
    s = orig.lstrip()
    if '\n' not in s[:400]:
        return None
    return 2 if s.startswith('{\n  ') or s.startswith('[\n  ') else 1


def _save(path, obj, orig):
    ind = _layout(orig)
    txt = json.dumps(obj, ensure_ascii=False, indent=ind, separators=(',', ':') if ind is None else None)
    open(path, 'w', encoding='utf-8').write(txt + ('\n' if orig.endswith('\n') else ''))


def _strip(x, G):
    """take retired refs out of lists of refs and ' • ' text lists inside any JSON value; returns the cleaned value"""
    if isinstance(x, dict):
        if any(isinstance(x.get(k), str) and any(g in x[k] for g in G) for k in ('label', 'url')):
            return None               # a link button to the retired park's page
        out = {}
        for k, v in x.items():
            if k in G:
                continue              # a lookup keyed by the park number (app pack outlines, guide parks)
            if k in ('ref', 'p', 'c') and isinstance(v, str) and v in G:
                if k == 'p':
                    continue          # a KFF/SOTA row that pointed at the retired park: drop the link only
                return None           # the row IS the retired park: drop the whole row
            v2 = _strip(v, G)
            if v2 is None and k == 'properties':
                return None           # a map outline of the retired park: drop the whole feature
            if v2 is None and v is not None and isinstance(v, (dict, list)):
                continue
            out[k] = v2
        if 'xref' in out and isinstance(out['xref'], str) and any(g in out['xref'] for g in G):
            out['xref'] = ' • '.join(p for p in out['xref'].split(' • ') if not any(g in p for g in G))
        if isinstance(out.get('pota'), list) and not out['pota'] and 'potaName' in out:
            out['potaName'] = ''
        return out
    if isinstance(x, list):
        if x and all(isinstance(v, str) and REF.match(v) for v in x):
            return [v for v in x if v not in G]      # a list of park numbers
        if 2 <= len(x) <= 3 and isinstance(x[0], str) and x[0] in G:
            return None                              # a pair like ['US-xxxx', name] (2-fer lists in ky-overlaps)
        if len(x) >= 2 and isinstance(x[0], str) and x[0] == 'POTA' and x[1] in G:
            return None                              # a row like ['POTA', 'US-xxxx', name, la, lo, url]
        out = []
        for v in x:
            if isinstance(v, str) and v in G:
                out.append('')                       # a column in a row (wwff-unmapped): keep the column, blank it
                continue
            v2 = _strip(v, G)
            if v2 is None and isinstance(v, (dict, list)):
                continue
            out.append(v2)
        return out
    return x


def fix(G):
    changed = []
    files = ['kpc-ky-data.json', 'locations-ky.json', 'locations.json', 'kpc-guide-pota-data.json', 'kpc-guide-wwff-data.json',
             'kpc-guide-sota-data.json', 'wwff-unmapped.json'] + sorted(glob.glob('ky-*.geojson')) + sorted(glob.glob('app/packs/US-KY*.json'))
    for f in files:
        if not os.path.exists(f):
            continue
        orig = open(f, encoding='utf-8').read()
        if not any(g in orig for g in G):
            continue
        d = json.loads(orig)
        if f == 'kpc-guide-pota-data.json' and isinstance(d.get('parks'), dict):
            for g in G:
                d['parks'].pop(g, None)
        d2 = _strip(d, G)
        if f == 'locations-ky.json' and isinstance(d2, dict) and 'rows' in d2:
            d2['total'] = len(d2['rows'])
        _save(f, d2, orig)
        changed.append(f)
    # the map download files and the Top 25 are built from kpc-ky-data.json: rebuild them
    if os.path.exists('.claude/build/mapfiles/refresh.py') and any(g in open(p, encoding='utf-8').read() for p in ('KPC_Kentucky_POTA_Parks.kml', 'KPC_Kentucky_POTA_Parks.gpx') if os.path.exists(p) for g in G):
        subprocess.run([sys.executable, '.claude/build/mapfiles/refresh.py'], check=False)
        changed.append('KPC map files (KML/GPX)')
    if os.path.exists('kpc-top25.json') and any(g in open('kpc-top25.json', encoding='utf-8').read() for g in G):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import kpc_top25 as T
        orig = open('kpc-top25.json', encoding='utf-8').read()
        old = json.loads(orig)
        tt = {r['c']: r.get('t') for r in old.get('qsos', []) + old.get('acts', []) if 't' in r}
        stats = {c: (a, q, tt.get(c)) for c, a, q in old.get('all', [])}
        new = T.build(stats, old.get('updated', ''), [p for p in json.load(open('kpc-ky-data.json', encoding='utf-8'))['parks'] if p['c'] not in G])
        for k in old:
            new.setdefault(k, old[k])
        new['source'] = old.get('source', new['source'])
        _save('kpc-top25.json', new, orig)
        changed.append('kpc-top25.json')
    return changed


def leftovers(G):
    """every site file that still mentions a retired park number"""
    pat = re.compile(r'\b(' + '|'.join(re.escape(g) for g in sorted(G)) + r')\b')
    out = []
    for root, dirs, files in os.walk('.'):
        rel = os.path.relpath(root, '.')
        rel = '' if rel == '.' else rel.replace(os.sep, '/')
        dirs[:] = [d for d in dirs if not SKIP.match((rel + '/' + d).lstrip('/'))]
        for fn in files:
            p = (rel + '/' + fn).lstrip('/')
            if SKIP.match(p) or not p.endswith(LOOK):
                continue
            try:
                hits = sorted(set(pat.findall(open(p, encoding='utf-8', errors='ignore').read())))
            except OSError:
                continue
            if hits:
                out.append((p, hits))
    return out


def mismatches():
    """Oct 23 (Brandon: 'make sure our parks note etc matches'): every list that should carry EVERY Kentucky park must
    carry exactly the parks in kpc-ky-data.json, under the same name. Returns [(file, what is wrong)]."""
    M = {p['c']: p['n'] for p in json.load(open('kpc-ky-data.json', encoding='utf-8'))['parks']}
    nm = lambda x: re.sub(r'\W', '', str(x or '').lower())
    pat = re.compile(r'\bUS-\d{4,5}\b')
    out = []
    def refs_of(f):
        return set(pat.findall(open(f, encoding='utf-8', errors='ignore').read())) if os.path.exists(f) else None
    for f in ('KPC_Kentucky_POTA_Parks.kml', 'KPC_Kentucky_POTA_Parks.gpx', 'locations.json', 'kpc-guide-pota-data.json', 'kpc-top25.json', 'app/packs/US-KY.json'):
        r = refs_of(f)
        if r is None:
            continue
        miss = sorted(set(M) - r)
        if miss:
            out.append((f, 'missing ' + ', '.join(miss[:12])))
    try:
        g = json.load(open('kpc-guide-pota-data.json', encoding='utf-8'))['parks']
        extra = sorted(set(g) - set(M))
        if extra:
            out.append(('kpc-guide-pota-data.json', 'parks not on the site list: ' + ', '.join(extra[:12])))
        bad = [c for c in M if c in g and nm(g[c].get('pdfName')) != nm(M[c])]
        if bad:
            out.append(('kpc-guide-pota-data.json', 'name differs: ' + '; '.join('%s "%s" (site "%s")' % (c, g[c].get('pdfName'), M[c]) for c in bad[:8])))
    except (OSError, ValueError, KeyError):
        pass
    for f in ('locations.json', 'locations-ky.json'):
        try:
            d = json.load(open(f, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        rows = d['rows'] if isinstance(d, dict) else d
        bad = [r for r in rows if len(r) > 2 and r[1] in M and nm(r[2]) != nm(M[r[1]])]
        if bad:
            out.append((f, 'name differs: ' + '; '.join('%s "%s" (site "%s")' % (r[1], r[2], M[r[1]]) for r in bad[:8])))
    return out


def main():
    R = retired()
    G = set(R)
    if not G:
        notice('Retired parks', 'none listed in ' + RET); return 0
    if '--fix' in sys.argv:
        ch = fix(G)
        notice('Retired parks', ('taken out of: ' + ', '.join(ch)) if ch else 'nothing to take out')
    left = leftovers(G)
    for p, hits in left:
        print(f'::warning title=Retired park still listed::{p}: {", ".join(hits)}', flush=True)
    if not left:
        notice('Retired parks', 'none of %d retired parks is listed anywhere on the site' % len(G))
    for f, why in mismatches():
        print(f'::warning title=Park list does not match::{f}: {why}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

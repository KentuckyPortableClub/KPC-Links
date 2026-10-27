#!/usr/bin/env python3
"""NEAR-MISS LIST (chat 2, Oct 26 2026; HQ, Brandon: 'do we need a bot for name mismatch?' -> no new bot, a list in the
nightly check). For every US + Canada park with NO outline in the answer keys, list the official areas from layers we
already read (the saved copies the keys join from) that CONTAIN POTA's pin (or sit within 1 km of it) AND either share a
main name word with the park or are the right kind of place (WMA, state forest, NRA...). Both names, the layer, the
distance. -> data/outline-leads/near-miss.json + a section in the boundary-check issue (no email).

Chat 8 reviews it; an approved lead goes into data/us-key/overrides.json (US: {"join": [<id>], "why": "reviewed: near miss"})
or data/ca-key/overrides.json and the key then joins it as a reviewed match. Adds nothing itself. Never fails."""
import gzip, json, math, os, pathlib, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import kpc_match as KM  # noqa: E402
from kpc_save import save_json  # noqa: E402

HERE = pathlib.Path(os.path.dirname(__file__))
OUT = pathlib.Path('data/outline-leads/near-miss.json')
CUS = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/us')
CCA = pathlib.Path(os.environ.get('CA_CACHE') or 'cache/ca')
NEAR_KM = 1.0
STOP = set('lake lakes creek river rivers mountain mountains canyon canyons springs spring valley island islands point hill hills ridge rock rocks '
           'forest park parks area areas county wildlife north south east west upper lower big little new old fort mount saint the and of '
           'national state public land lands recreation management unit natural trail wilderness reservoir pond bay beach marsh swamp '
           'historic historical site sites conservation regional provincial reserve preserve nature ecological memorial des les aire parc'.split())


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)


def lib(path, stop):
    """the key's own name rules (norm, kinds, SITE), without running the key"""
    src = (HERE / path).read_text(encoding='utf-8')
    ns = {'__name__': 'nearmiss_' + path.split('.')[0], '__file__': str(HERE / path)}
    exec(compile(src[:src.index(stop)], path, 'exec'), ns)
    return ns


def main_words(norm, s): return {w for w in norm(s).split() if len(w) > 2 and w not in STOP and not w.isdigit()}


def leads_for(la, lo, name, kp, site, recs, norm, kinds, rec_name, rec_kinds, label):
    pw = main_words(norm, name)
    out = []
    pad = NEAR_KM / 80
    for a in recs:
        b = a.get('_bb')
        if not b or not (b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad): continue
        nm = rec_name(a)
        if not nm or KM.is_admin(nm): continue
        d = KM.km_to(la, lo, a['_g'])
        if d is None or d > NEAR_KM: continue
        shared = sorted(pw & main_words(norm, nm))
        same_kind = bool(kp & rec_kinds(a, kinds))
        if not shared and (site or not same_kind): continue
        out.append({'name': nm, 'id': str(a.get('OBJECTID', a.get('oid'))), 'layer': label(a), 'km': round(d, 2),
                    'why': ('shares ' + ', '.join(shared)) if shared else 'same kind of place (' + ', '.join(sorted(kp & rec_kinds(a, kinds))) + ')',
                    'acres': a.get('_acres', 0)})
    out.sort(key=lambda x: (not x['why'].startswith('shares'), x['km'], x['acres'] or 9e12))
    return out[:4]


def us(res):
    K = lib('kpc_us_key.py', '\nfor st in STATES:')
    K['CACHE'] = CUS
    n = 0
    for f in sorted(pathlib.Path('data/us-key').glob('US-??.json')):
        st = f.stem[3:]
        parks = {r: p for r, p in json.load(open(f))['parks'].items() if not p.get('m')}
        if not parks: continue
        got = K['load_cache'](st)
        if not got: res['skipped'].append(f'US-{st}: no saved copy'); continue
        recs = got[0]
        for a in recs:
            try: a['_acres'] = float(a.get('GIS_Acres') or 0)
            except (TypeError, ValueError): a['_acres'] = 0
        try: P = json.load(open(f'data/parkinfo/US-{st}.json'))['parks']
        except Exception: P = {}  # noqa: BLE001
        pins = K['pins']()
        for ref, p in parks.items():
            v = P.get(ref) or []
            la, lo = (v[5], v[6]) if len(v) > 6 and v[5] is not None else pins.get(ref, (None, None))
            if la is None: continue
            name = p.get('n') or (v[0] if v else '')
            kp = K['kinds'](name) | K['kinds'](p.get('t'))
            site = bool(K['SITE'].search(name))
            ls = leads_for(la, lo, name, kp, site, recs, K['norm'], K['kinds'],
                           lambda a: a.get('Unit_Nm') or a.get('Loc_Nm') or '',
                           lambda a, kinds: a.get('_k') or set(),
                           lambda a: a.get('Loc_Mang') or a.get('Mang_Name') or 'PAD-US')
            if ls:
                res['parks'][ref] = {'n': name, 'st': st, 'acts': v[7] if len(v) > 7 and isinstance(v[7], int) else 0, 'site': site, 'leads': ls}; n += 1
        res['counts'][st] = sum(1 for x in res['parks'].values() if x['st'] == st)
    return n


def ca(res):
    f = CCA / 'CA-ALL.json.gz'
    if not f.exists(): res['skipped'].append('Canada: no saved copy'); return 0
    C = lib('kpc_ca_key.py', '\nrecs = cload()')
    with gzip.open(f, 'rt', encoding='utf-8') as fh: blob = json.load(fh)
    recs = []
    for o in blob.get('recs') or []:
        g = {'rings': o.get('_r') or []}
        try: ac = float(o.get('ha') or 0) * 2.47105
        except (TypeError, ValueError): ac = 0
        recs.append({**{k: v for k, v in o.items() if k not in ('_r', '_k')}, '_g': g, '_bb': C['bbox'](g), '_k': set(o.get('_k') or []), '_acres': ac})
    P = json.load(open('data/parkinfo/CA.json'))['parks']
    n = 0
    for kf in sorted(pathlib.Path('data/ca-key').glob('CA-??.json')):
        pv = kf.stem
        for ref, p in json.load(open(kf))['parks'].items():
            if p.get('m'): continue
            v = P.get(ref) or []
            if len(v) < 7 or v[5] is None: continue
            name = p.get('n') or v[0]
            kp = C['kinds'](name) | C['kinds'](p.get('t'))
            ls = leads_for(v[5], v[6], name, kp, False, recs, C['norm'], C['kinds'],
                           lambda a: a.get('n') or a.get('nf') or '',
                           lambda a, kinds: a.get('_k') or set(),
                           lambda a: a.get('src') or a.get('mg') or 'CPCAD')
            if ls:
                res['parks'][ref] = {'n': name, 'st': pv, 'acts': v[7] if len(v) > 7 and isinstance(v[7], int) else 0, 'site': False, 'leads': ls}; n += 1
        res['counts'][pv] = sum(1 for x in res['parks'].values() if x['st'] == pv)
    return n


def main():
    res = {'about': 'NEAR MISSES (kpc_near_miss.py, nightly): parks with NO outline, and official areas from layers we already read that '
                    'contain the POTA pin (or lie within 1 km) and share a main name word or are the same kind of place. NOT joined. '
                    "Chat 8 reviews; an approved one goes into data/us-key/overrides.json (or data/ca-key) as {'join': [id], 'why': 'reviewed: near miss'}.",
           'made': time.strftime('%Y-%m-%d'), 'counts': {}, 'skipped': [], 'parks': {}}
    a = b = 0
    try: a = us(res)
    except Exception as e: res['skipped'].append(f'US stopped: {e}')  # noqa: BLE001
    try: b = ca(res)
    except Exception as e: res['skipped'].append(f'Canada stopped: {e}')  # noqa: BLE001
    words = sum(1 for x in res['parks'].values() if any(l['why'].startswith('shares') for l in x['leads']))
    res['totals'] = {'parks': len(res['parks']), 'us': a, 'canada': b, 'name_word': words}
    save_json(OUT, res, indent=1)
    notice('Near misses', f"{len(res['parks'])} parks with no outline have a near miss ({a} US, {b} Canada; {words} share a name word)"
           + (' · ' + ' | '.join(res['skipped'][:6]) if res['skipped'] else ''))


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        notice('Near misses', f'stopped: {e}')
    sys.exit(0)

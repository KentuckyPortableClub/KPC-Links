#!/usr/bin/env python3
"""ONE-OFF CANDIDATE FINDER (chat 9, HQ Oct 27 11:09 PM). TEMPORARY: delete with kpc-candidates.yml after the run.
For every US + Canada park still unmatched in the answer keys (skipping historic sites, city / county / regional parks,
scenic byways / parkways, trail LINES and BLM single sites, which are pin-only), list the official polygons from the
layers the keys already read (the saved copies on the boundary-cache release, so no map server is asked) that contain
the park's pin or sit within 2 km. Per candidate: name-word score (share of the park's main name words found in the
polygon's name), kind, area, distance from the pin (0 = inside), and whether it is already joined to another park.
STRONG = pin inside + same kind + every main name word agrees. Read only: joins nothing.
-> data/review/candidates-us-ca.json (+ a summary block at the top). Chat 8 reviews; it feeds Brandon's name-match rulings.
Never fails."""
import gzip, json, os, pathlib, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
import kpc_match as KM  # noqa: E402
import kpc_near_miss as NM  # noqa: E402  (its loaders: lib(), main_words(), STOP)

OUT = pathlib.Path('data/review/candidates-us-ca.json')
NEAR_KM = 2.0
KEEP = 6
SKIP_TYPE = re.compile(r'histor(ic|ical) (site|district|monument|area|preservation)|state historic|heritage site|national memorial'
                       r'|regional park|county|city|municipal|metro park|parkway|byway|scenic (highway|drive|road)'
                       r'|(national|state|scenic|recreation|geologic|historic) trail|blm (backcountry airstrip|interpretive site|historic)', re.I)


def notice(m): print('::notice title=Candidate finder::' + str(m).replace('\n', ' ')[:900], flush=True)


def joined_index(paths):
    """record id -> the park(s) already joined to it"""
    idx = {}
    for f in paths:
        try: P = json.load(open(f))['parks']
        except Exception: continue  # noqa: BLE001
        for ref, p in P.items():
            for m in p.get('m') or []:
                if m: idx.setdefault(str(m[0]), []).append(ref)
    return idx


def cands(la, lo, name, kp, recs, norm, rec_name, rec_kinds, label, jidx, ref):
    pw = NM.main_words(norm, name)
    pad = NEAR_KM / 80
    out = []
    for a in recs:
        b = a.get('_bb')
        if not b or not (b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad): continue
        nm = rec_name(a)
        if not nm or KM.is_admin(nm): continue
        d = KM.km_to(la, lo, a['_g'])
        if d is None or d > NEAR_KM: continue
        rk = rec_kinds(a)
        shared = pw & NM.main_words(norm, nm)
        score = round(len(shared) / len(pw), 2) if pw else 0.0
        rid = str(a.get('OBJECTID', a.get('oid')))
        other = [r for r in jidx.get(rid, []) if r != ref]
        out.append({'name': nm, 'id': rid, 'layer': label(a), 'km': round(d, 2), 'score': score, 'words': sorted(shared),
                    'kind': sorted(rk), 'same_kind': bool(kp & rk), 'acres': round(a.get('_acres') or 0),
                    'joined_to': other[:5], 'strong': d == 0 and bool(kp & rk) and score == 1.0 and not other})
    out.sort(key=lambda x: (not x['strong'], -x['score'], x['km'], x['acres'] or 9e12))
    return out[:KEEP]


def us(res, jidx):
    K = NM.lib('kpc_us_key.py', '\nfor st in STATES:')
    K['CACHE'] = NM.CUS
    pins = K['pins']()
    # the key's SITE test also calls every 'BLM Recreation Management Area' a site; here only the real site words count, so the
    # true BLM areas (Leslie Gulch, Klamath Hills…) still get their candidates
    SITE1 = re.compile(K['SITE'].pattern.replace(r'^blm |\bblm\b.*recreation management area|', ''), re.I)
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
        for ref, p in parks.items():
            t, name = p.get('t') or '', p.get('n') or ''
            if SKIP_TYPE.search(t) or (re.search(r'^BLM', t) and SITE1.search(name)): res['pin_only'] += 1; continue
            v = P.get(ref) or []
            la, lo = (v[5], v[6]) if len(v) > 6 and v[5] is not None else pins.get(ref, (None, None))
            if la is None: res['no_pin'] += 1; continue
            kp = K['kinds'](name) | K['kinds'](t)
            c = cands(la, lo, name, kp, recs, K['norm'], lambda a: a.get('Unit_Nm') or a.get('Loc_Nm') or '',
                      lambda a: a.get('_k') or set(), lambda a: a.get('Loc_Mang') or a.get('Mang_Name') or 'PAD-US', jidx, ref)
            res['parks'][ref] = {'n': name, 't': t, 'st': st, 'kinds': sorted(kp), 'cands': c}


def ca(res, jidx):
    f = NM.CCA / 'CA-ALL.json.gz'
    if not f.exists(): res['skipped'].append('Canada: no saved copy'); return
    C = NM.lib('kpc_ca_key.py', '\nrecs = cload()')
    with gzip.open(f, 'rt', encoding='utf-8') as fh: blob = json.load(fh)
    recs = []
    for o in blob.get('recs') or []:
        g = {'rings': o.get('_r') or []}
        try: ac = float(o.get('ha') or 0) * 2.47105
        except (TypeError, ValueError): ac = 0
        recs.append({**{k: v for k, v in o.items() if k not in ('_r', '_k')}, '_g': g, '_bb': C['bbox'](g), '_k': set(o.get('_k') or []), '_acres': ac})
    P = json.load(open('data/parkinfo/CA.json'))['parks']
    for kf in sorted(pathlib.Path('data/ca-key').glob('CA-??.json')):
        pv = kf.stem
        for ref, p in json.load(open(kf))['parks'].items():
            if p.get('m'): continue
            t, v = p.get('t') or '', P.get(ref) or []
            name = p.get('n') or (v[0] if v else '')
            if SKIP_TYPE.search(t): res['pin_only'] += 1; continue
            if len(v) < 7 or v[5] is None: res['no_pin'] += 1; continue
            kp = C['kinds'](name) | C['kinds'](t)
            c = cands(v[5], v[6], name, kp, recs, C['norm'], lambda a: a.get('n') or a.get('nf') or '',
                      lambda a: a.get('_k') or set(), lambda a: a.get('src') or a.get('mg') or 'CPCAD', jidx, ref)
            res['parks'][ref] = {'n': name, 't': t, 'st': pv, 'kinds': sorted(kp), 'cands': c}


def main():
    res = {'about': 'ONE-OFF CANDIDATE FINDER (chat 9, HQ Oct 27): unmatched US + Canada parks and the official polygons from layers the keys '
                    'already read that hold the pin or lie within 2 km. READ ONLY: nothing is joined. score = share of the park\'s main name '
                    'words in the polygon name; km 0 = pin inside; joined_to = parks already joined to that polygon; STRONG = pin inside + '
                    'same kind + all main words + not joined elsewhere. Chat 8 reviews; it feeds Brandon\'s name-match rulings.',
           'made': time.strftime('%Y-%m-%d'), 'skipped': [], 'pin_only': 0, 'no_pin': 0, 'parks': {}}
    jidx = joined_index(sorted(pathlib.Path('data/us-key').glob('US-??.json')) + sorted(pathlib.Path('data/ca-key').glob('CA-??.json')))
    for fn in (us, ca):
        try: fn(res, jidx)
        except Exception as e: res['skipped'].append(f'{fn.__name__} stopped: {e}')  # noqa: BLE001
    P = res['parks'].values()
    strong = [x for x in P if sum(c['strong'] for c in x['cands']) == 1]
    res['summary'] = {
        'parks_checked': len(res['parks']), 'skipped_pin_only': res['pin_only'], 'no_pin': res['no_pin'],
        'with_any_candidate': sum(1 for x in P if x['cands']),
        'ONE_strong_candidate': len(strong),
        'two_or_more_strong': sum(1 for x in P if sum(c['strong'] for c in x['cands']) > 1),
        'pin_inside_same_kind_but_words_differ': sum(1 for x in P if not any(c['strong'] for c in x['cands']) and any(c['km'] == 0 and c['same_kind'] for c in x['cands'])),
        'best_candidate_already_joined_elsewhere': sum(1 for x in P if x['cands'] and x['cands'][0]['joined_to']),
        'no_candidate': sum(1 for x in P if not x['cands']),
        'one_strong_by_area': {}}
    for x in strong: res['summary']['one_strong_by_area'][x['st']] = res['summary']['one_strong_by_area'].get(x['st'], 0) + 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False) + '\n')
    notice(json.dumps(res['summary'])[:800] + (' · ' + ' | '.join(res['skipped'][:6]) if res['skipped'] else ''))


if __name__ == '__main__':
    try: main()
    except Exception as e: notice(f'stopped: {e}')  # noqa: BLE001
    sys.exit(0)

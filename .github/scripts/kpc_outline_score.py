#!/usr/bin/env python3
"""SECOND WITNESS: how sure are we of each park's outline? (HQ boundary plan 2b, Brandon Oct 26 6:13 AM: 'our pins are from
POTA? could it just be POTA wrong'). POTA's pins are often off (the HQ, the wrong park, lat/lon swapped), so a pin outside
our outline is not proof the outline is wrong. Each joined US park gets a confidence score from evidence that does NOT
come from POTA's pin:

  name   the outline's own name against the park's name (core words, the kind words left out)        0-2
  agency the outline's manager fits the kind of park (NPS for a National Park, FWS for a refuge, the
         state for a state park / WMA, USFS for a forest) - from the saved PAD-US records              0-1
  agree  a SECOND map says the same: for a park joined to a state layer, a PAD-US record of the same
         name near the pin with a similar size (half to double); for a PAD-US join, two PAD-US
         records agreeing, or a state-layer piece joined as well                                       0-2
  pin    POTA's pin inside (2), just outside (1), well outside (0)                                     0-2

HIGH = 5 or more; MEDIUM = 3-4; LOW = 0-2. 'POTA PIN OFF' = the pin is outside but name + a second witness say the
outline is right: we KEEP the outline and list the park so the pin can be reported to POTA. Only LOW parks go to the
good-bot worklists. Reads data/us-key + the saved PAD-US copy (cache/us). Writes data/boundary-score.json. Changes no key.
Never fails."""
import gzip, json, math, os, pathlib, re, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from kpc_save import save_json

CACHE = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/us')
KIND = re.compile(r'\b(national|state|park|parks|forest|wildlife|management|area|areas|refuge|recreation|recreational|historic|historical|'
                  r'site|sites|preserve|reserve|natural|nature|monument|memorial|wilderness|scenic|river|trail|lake|wma|nwr|sp|sra|'
                  r'conservation|county|of|the|and|at|on|in|unit|tract|land|lands|game|fish|hunting|public|access|forest)\b')


def low(x): return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', str(x or '').lower().replace('&', ' and ')).split())
def core(x): return ' '.join(KIND.sub(' ', low(x)).split())


def _abbr(park, outline):
    """Ohio ODNR's short names ('CaesarCrkSP', 'WstBrnchSP' = Caesar Creek / West Branch State Park): the outline's letters,
    kind letters dropped from the end, appear in order in the park's name and start the same way."""
    o = re.sub(r'(sp|wa|sf|snp|dnp|sna|wma|nwr|sra|shs)$', '', re.sub(r'[^a-z]', '', low(outline)))
    p = re.sub(r'[^a-z]', '', low(park))
    if len(o) < 5 or not p or o[0] != p[0]: return False
    it = iter(p)
    return all(ch in it for ch in o)


def name_score(park, outline):
    a, b = core(park), core(outline)
    if a and b and a != b and not (a in b or b in a) and _abbr(park, outline): return 1
    if not a or not b: return 1 if low(park) == low(outline) else 0
    if a == b or a in b or b in a: return 2
    wa, wb = set(a.split()), set(b.split())
    return 1 if wa & wb and len(max(wa & wb, key=len)) > 3 else 0


def agency_fits(typ, mang, own):
    t, m = low(typ), str(mang or '').upper()
    if not m: return None
    if 'national park' in t or 'historic' in t and 'national' in t or 'national monument' in t or 'national recreation' in t or 'national seashore' in t or 'national lakeshore' in t or 'parkway' in t or 'national battlefield' in t or 'national military' in t or 'national preserve' in t:
        return m in ('NPS',)
    if 'wildlife refuge' in t or 'fish hatchery' in t and 'national' in t: return m in ('FWS',)
    if 'national forest' in t or 'national grassland' in t: return m in ('USFS',)
    if 'blm' in t or 'bureau of land' in t: return m in ('BLM',)
    if 'army corps' in t or 'corps of engineers' in t: return m in ('USACE',)
    if t.startswith('state') or 'state park' in t or 'wildlife management' in t or 'state forest' in t or 'state trail' in t:
        return str(own or '').upper() in ('STAT', 'SDNR', 'SPR', 'SFW', 'SLB', 'SDOL') or m.startswith('S')
    return None


LAY = json.load(open('data/us-key/layers.json')) if os.path.exists('data/us-key/layers.json') else {}


def label_agency(rid):
    """(manager, owner type) from the layer a state-layer / federal-layer id comes from."""
    m = re.match(r'([a-z]+)', str(rid)); pre = m.group(1) if m else ''
    if pre == 'fws': return 'FWS', 'FED'
    lab = (LAY.get(pre) or ['', '', ''])[2]
    if re.search(r'National Park Service|\bNPS\b', lab): return 'NPS', 'FED'
    if re.search(r'Fish and Wildlife Service|\bFWS\b|USFWS', lab): return 'FWS', 'FED'
    if re.search(r'Forest Service|USFS', lab): return 'USFS', 'FED'
    if re.search(r'\bBLM\b|Bureau of Land', lab): return 'BLM', 'FED'
    if re.search(r'Corps of Engineers|USACE', lab): return 'USACE', 'FED'
    return ('STATE', 'STAT') if lab else ('', '')


def pad_index():
    """PAD-US records from the saved copies: by id, and by name core for the second-witness look-up."""
    by_id, by_name = {}, {}
    for f in CACHE.glob('US-*.json.gz'):
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as fh: recs = json.load(fh).get('recs') or []
        except Exception: continue  # noqa: BLE001
        for r in recs:
            rs = r.get('_r') or []
            xs = [p[0] for g in rs for p in g]; ys = [p[1] for g in rs for p in g]
            r['_bb'] = [min(xs), min(ys), max(xs), max(ys)] if xs else None
            r.pop('_r', None)
            by_id[r.get('OBJECTID')] = r
            for nm in (r.get('Unit_Nm'), r.get('Loc_Nm')):
                c = core(nm)
                if c: by_name.setdefault(c, []).append(r)
    return by_id, by_name


def near(la, lo, bb, pad):
    return bb and bb[0] - pad <= lo <= bb[2] + pad and bb[1] - pad <= la <= bb[3] + pad


def main():
    by_id, by_name = pad_index()
    have_pad = bool(by_id)
    out, states, pin_off, lowl, weak = {}, {}, [], [], []
    for f in sorted(pathlib.Path('data/us-key').glob('US-*.json')):
        st = f.stem
        try: key = json.load(open(f))['parks']
        except Exception: continue  # noqa: BLE001
        try: info = json.load(open(f'data/parkinfo/{st}.json'))['parks']
        except Exception: info = {}  # noqa: BLE001
        S = states.setdefault(st, {'outlines': 0, 'high': 0, 'medium': 0, 'low': 0, 'pota_pin_off': 0, 'no_outline': 0})
        for ref, p in key.items():
            m = p.get('m') or []
            v = info.get(ref) or []
            acts = v[7] if len(v) > 7 and isinstance(v[7], (int, float)) else 0
            if not m: S['no_outline'] += 1; continue
            S['outlines'] += 1
            name, typ = p.get('n') or (v[0] if v else ''), p.get('t') or (v[2] if len(v) > 2 else '')
            la, lo = (v[5], v[6]) if len(v) > 6 else (None, None)
            why = []
            ns = max(name_score(name, x[1]) for x in m)
            # Oct 27 (boundary review #5): a SOFT join (shared words, or 'same name, different kind + pin inside') is never full
            # name evidence; a person's join ('reviewed') always is
            soft = not any(str(x[3]).startswith(('name', 'reviewed')) for x in m if len(x) > 3)
            if soft: ns = min(ns, 1)
            why.append(f'name {ns}/2' + (' (soft join)' if soft else ''))
            worst = min(name_score(name, x[1]) for x in m)
            if worst == 0 and len(m) > 1 and not any(str(x[3]).startswith('reviewed') for x in m if len(x) > 3):
                weak.append([ref, name, st, next(x[1] for x in m if name_score(name, x[1]) == 0), acts])   # one piece whose name says another place
            pads = [by_id.get(x[0]) for x in m if isinstance(x[0], int) and by_id.get(x[0])]
            fits = [agency_fits(typ, r.get('Mang_Name'), r.get('Mang_Type')) for r in pads]
            fits += [agency_fits(typ, *label_agency(x[0])) for x in m if isinstance(x[0], str)]
            ag = 1 if any(x is True for x in fits) else 0
            why.append(f'agency {ag}/1')
            agree = 0
            strs = [x for x in m if isinstance(x[0], str)]
            if strs and la is not None:
                # joined to a state layer: does PAD-US have the same place, near, of a similar size?
                our = sum(x[2] or 0 for x in strs)
                for x in strs:
                    for r in by_name.get(core(x[1]), []):
                        if not near(la, lo, r.get('_bb'), .3): continue
                        a = r.get('GIS_Acres') or 0
                        agree = max(agree, 2 if our and a and .5 <= a / our <= 2 else 1)
                if pads: agree = max(agree, 1)           # a PAD-US piece joined as well
            elif len(pads) > 1 and len({core(r.get('Unit_Nm')) for r in pads}) == 1:
                agree = 1                                 # two PAD-US records (fee + designation) of the same place
            if pads and strs: agree = max(agree, 2)
            why.append(f'second map {agree}/2' + ('' if have_pad else ' (no saved PAD-US copy in this run)'))
            far = p.get('far')
            pin = 0 if far in ('well outside', 'no shape to check against') else 1 if far == 'edge' else 2
            why.append({2: 'POTA pin inside', 1: 'POTA pin just outside', 0: 'POTA pin well outside'}[pin])
            score = ns + ag + agree + pin
            level = 'high' if score >= 5 else 'medium' if score >= 3 else 'low'
            flag = ''
            if pin == 0 and far == 'well outside' and ns == 2 and (agree >= 1 or ag == 1):   # 'edge' = within ~1 mile = map precision, not a POTA mistake
                flag = 'POTA PIN OFF'; S['pota_pin_off'] += 1
                if pin == 0 and level == 'low': level = 'medium'
                pin_off.append([ref, name, st, far, m[0][1], acts])
            S[level] += 1
            out[ref] = [score, level, flag, '; '.join(why)]
            if level == 'low': lowl.append([ref, name, st, m[0][1], acts, '; '.join(why)])
    tot = {k: sum(s[k] for s in states.values()) for k in ('outlines', 'high', 'medium', 'low', 'pota_pin_off', 'no_outline')}
    lowl.sort(key=lambda x: -x[4]); pin_off.sort(key=lambda x: -x[5])
    save_json(pathlib.Path('data/boundary-score.json'), {
        'about': 'Second-witness confidence per joined US park (kpc_outline_score.py): name, agency, a second map, POTA pin. '
                 'HIGH >= 5, MEDIUM 3-4, LOW 0-2. POTA PIN OFF = pin outside but name + a second witness agree: the outline is kept.',
        'totals': tot, 'states': states, 'pota_pin_off': pin_off, 'low_busiest_first': lowl[:400],
        'weak_piece': sorted(weak, key=lambda x: -x[4])[:400], 'parks': out}, indent=None)
    print('::notice title=Second witness::' + json.dumps(tot) + f' · {len(weak)} parks with a joined piece whose name says another place', flush=True)
    return tot


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Second witness::stopped: {e}', flush=True)
    sys.exit(0)

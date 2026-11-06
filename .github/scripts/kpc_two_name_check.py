#!/usr/bin/env python3
"""Two-name park check (Nov 6, big key / 2-fer patch; Brandon [pt437u]). Offline, REPORT ONLY, reads the built keys.

A POTA park named for two places ('Black Rock Range East/West', 'Carson Lake and Pasture WMA', 'Empire & Carson River Mills')
is often TWO official areas. When the key joined records that name only ONE half, the other half is probably missing.
For every park whose name splits on '/', ' & ' or ' and ' into two halves that each have a word of their own (not a kind word
like lake/river/state/park/wild/scenic), the check looks at the joined record names (m[1]):
  one half named, the other not -> 'half outlined' (listed; the parks' joins are NOT changed)
Nov 6 follow-up (Brandon [pt449u]): the KY GIS Workbench's same-place name matcher (kpc_name_match.py, FIND NEW nameMatch) sharpens
it: a joined record with the SAME name as the whole park after the stop words ('K'zuzalt / Twin Two Conservancy') clears the park, and a half also
counts as named when a joined record is the same place as that half (whole-word prefix / suffix, 2+ words). Each row carries the
'also in' layers of its joined land (kpc_also_in.py). KPC_TWO_NAME_MATCH=words = the Nov 6 word test only.
Writes data/status/key-check/two-name-<key>.json; one notice. Env KEY=us|ca|world (or WORKFLOW_NAME), TREND_DIR.
"""
import difflib, glob, json, os, pathlib, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kpc_key_trend import KEYS, key_of, note, _j, DIR  # noqa: E402
import kpc_name_match as NM  # noqa: E402
from kpc_also_in import also_in  # noqa: E402

KIND = set('''lake lakes river rivers creek creeks state park parks national wild scenic recreation recreational area areas management
wildlife forest forests refuge trail trails historic historical site sites monument memorial preserve reserve natural conservation
fish game wma sp nf nwr blm herd preservation the of at on in de du la le des et and county regional provincial ecological
reservoir pond ponds island islands bay beach dam canyon mountain mountains hill hills range valley marsh swamp spring springs
north south east west upper lower big little old new great unit units tract tracts public use access point fishing hunting
complex landscape catchment natura dams reservoirs habitat protected protection conservancy nature
flora fauna fish wildlife birds bird sanctuary nature reserves wetland wetlands ffr
wilderness heritage corridor district system city municipal community water waters falls gorge ridge point rock rocks
sac spa sci sps zps ramsar sssi nnr lnr iba rspb'''.split())


def fold(s): return ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c)).replace('ł', 'l').replace('ə', 'e')


def words(s): return [w for w in re.findall(r"[a-z0-9]+", fold(s).lower().replace("'", '').replace('’', '')) if len(w) > 1]


def own(s): return {w for w in words(s) if w not in KIND and not w.isdigit()}


def halves(name):
    n = re.sub(r'(\d)\s*/\s*(\d)', r'\1-\2', str(name or ''))   # 'STA 3/4', '5/6' are one number
    n = re.sub(r'\([^)]*\b(count(y|ies)|section|only|portion|parish|district)\b[^)]*\)', ' ', n, flags=re.I).strip()   # Nov 6 follow-up: '(Delaware and Otsego County)' is a note, not a second place
    for sep in (r'\s*/\s*', r'\s+&\s+', r'\s+and\s+'):
        parts = re.split(sep, n, maxsplit=1, flags=re.I)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip(): return parts
    return None


def check(name, recs, matcher=None):
    h = halves(name)
    if not h or not recs: return None
    wb = (matcher or os.environ.get('KPC_TWO_NAME_MATCH') or 'workbench').strip().lower() != 'words'
    if wb and any(NM.norm_name(name) == NM.norm_name(x) and len(NM.norm_name(x)) >= 4 for x in recs): return None   # one record IS the whole two-name place (exact; a prefix would clear 'Carson Lake and Pasture' on 'Carson Lake')
    a, b = own(h[0]), own(h[1]) - own(h[0])
    a -= own(h[1])
    if not a or not b: return None
    got = set()
    for x in recs: got |= set(words(x))
    def hit(ws): return any(w in got or (len(w) >= 5 and any(difflib.SequenceMatcher(None, w, g).ratio() >= 0.8 for g in got)) for w in ws)
    ha, hb = hit(a), hit(b)
    if wb:
        ha = ha or bool(NM.best_match(h[0], recs)); hb = hb or bool(NM.best_match(h[1], recs))
    if ha != hb: return {'named': h[0] if ha else h[1], 'missing': h[1] if ha else h[0], 'missing_words': sorted(b if ha else a)}
    return None


def main():
    key = key_of()
    if not key: note('notice', 'two-name check: no key given'); return
    d, g = KEYS[key]
    rows, n = [], 0
    for f in sorted(glob.glob(os.path.join(d, g))):
        for r, p in ((_j(f) or {}).get('parks') or {}).items():
            if not isinstance(p, dict): continue
            nm = p.get('n') or ''
            if halves(nm): n += 1
            c = check(nm, [x[1] for x in (p.get('m') or []) if len(x) > 1])
            if c: rows.append(dict({'area': pathlib.Path(f).stem, 'park': r, 'name': nm, 'joined': sorted({x[1] for x in p['m'] if len(x) > 1})[:5]}, **c,
                                   also_in=also_in(key, p)))
    out = DIR / f'two-name-{key}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'key': key, 'about': __doc__.split('\n\n')[0], 'two_name_parks': n, 'half_outlined': len(rows), 'parks': rows},
                              indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    note('notice', f'{key}: {n} parks have two names; {len(rows)} have only one half outlined (listed in {out}; joins unchanged)')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('--test', '--selftest'):
        assert check('Annuello Flora and Fauna Reserve', ['Annuello F.F.R.']) is None
        assert check("K'zuzalt / Twin Two Conservancy Protected Area", ["K'ZUZÁLT/TWIN TWO CONSERVANCY"]) is None
        assert check('Donnelley/DePue State Park', ['Lake DePue State Fish and Wildlife Area'])['missing_words'] == ['donnelley']
        assert check('Carson Lake and Pasture Wildlife Management Area', ['Carson Lake WMA'])['missing_words'] == ['pasture']
        assert check('Hal and Fern Cooper Wildlife Management Area', ['Hal and Fern Cooper Wildlife Management Area']) is None
        assert check('Stormwater Treatment Area 5/6 State Conservation Area', ['x']) is None
        assert check('White Clay Creek National Wild and Scenic River', ['White Clay Creek Wild and Scenic River']) is None
        assert check("K'zuzalt / Twin Two Conservancy", ['Kzuzalt Twin Two Conservancy']) is None
        assert check('Dale Hollow Lake / Wolf River WMA', ['Dale Hollow Lake State Resort Park'])['missing_words'] == ['wolf']
        assert check('Blue Ridge / Smith Mountain Lake State Park', ['Smith Mountain Lake State Park', 'Blue Ridge Overlook']) is None
        assert halves('South Hill (Delaware and Otsego County) State Forest') is None
        print('two-name self-test OK'); sys.exit(0)
    try: main()
    except Exception as e:  # noqa: BLE001
        note('warning', f'two-name check stopped: {type(e).__name__}: {str(e)[:200]} (report only)')

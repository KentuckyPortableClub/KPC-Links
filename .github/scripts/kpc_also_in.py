#!/usr/bin/env python3
"""'Also in' notes: which official layers a park's joined land comes from (Nov 6 2026 follow-up key / 2-fer patch, Brandon [pt449u];
borrowed from the KY GIS Workbench FIND NEW, which keeps one copy of land found in two layers and notes 'also in <layer>').
Offline, REPORT ONLY: reads the built keys, never changes a join (kept out of the rules hash, kpc_key_freeze.NOT_RULES).

Where a joined record (m[]) comes from:
  US     record id: a number = PAD-US; a letter prefix ('sgtnc158', 'tnd12', 'fwsr3') = that layer in data/us-key/layers.json
         ([url, name field, label]); the label is the note.
  Canada m[3] 'how · <layer label>'; no label = CPCAD (the federal database).
  world  m[2] is the source label itself.
also_in(key, park) -> sorted labels (one per layer). Parks whose joined land is in 2+ layers are written to
data/status/key-check/also-in-<key>.json (counts by layer pair), and the other report scripts add the list to their rows.
Env KEY=us|ca|world (or WORKFLOW_NAME), TREND_DIR.
"""
import collections, glob, json, os, pathlib, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kpc_key_trend import KEYS, key_of, note, _j, DIR  # noqa: E402

_LAYERS = None


def us_layers():
    global _LAYERS
    if _LAYERS is None:
        d = _j(os.path.join(KEYS['us'][0], 'layers.json')) or {}
        _LAYERS = {k: (v[2] if isinstance(v, list) and len(v) > 2 and v[2] else k) for k, v in d.items()}
    return _LAYERS


def source_of(key, x):
    if not isinstance(x, list) or not x: return None
    if key == 'world': return str(x[2]) if len(x) > 2 and isinstance(x[2], str) and x[2] else 'world source'
    if key == 'ca':
        h = str(x[3]) if len(x) > 3 else ''
        return h.split(' · ', 1)[1].strip() if ' · ' in h else 'CPCAD (federal)'
    i = str(x[0])
    if re.fullmatch(r'\d+', i): return 'PAD-US'
    m = re.match(r'[a-z]+', i)
    if not m: return 'other'
    return us_layers().get(m.group(0)) or m.group(0)   # 'sgtnc' / 'tnd' are the stored prefixes


def also_in(key, park):
    return sorted({s for s in (source_of(key, x) for x in (park.get('m') or [])) if s})


def main():
    key = key_of()
    if not key: note('notice', 'also-in: no key given'); return
    d, g = KEYS[key]
    pairs, rows, joined, labels = collections.Counter(), {}, 0, {}
    for f in sorted(glob.glob(os.path.join(d, g))):
        for r, p in ((_j(f) or {}).get('parks') or {}).items():
            if not isinstance(p, dict) or not p.get('m'): continue
            joined += 1
            a = also_in(key, p)
            if len(a) > 1:
                rows[r] = [labels.setdefault(x, len(labels)) for x in a]   # compact: indexes into 'layers' (keeps the file small)
                pairs[' + '.join(a[:3]) + (' + ...' if len(a) > 3 else '')] += 1
    out = DIR / f'also-in-{key}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'key': key, 'about': __doc__.split('\n\n')[0], 'joined_parks': joined, 'in_two_or_more_layers': len(rows),
                               'top_layer_sets': pairs.most_common(25), 'layers': list(labels), 'parks': rows},
                              separators=(',', ':'), ensure_ascii=False) + '\n', encoding='utf-8')
    note('notice', f'{key}: {len(rows)} of {joined} joined parks have land in 2+ official layers (listed in {out}; joins unchanged)')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in ('--test', '--selftest'):
        _LAYERS = {'sgtnc': 'TN WMAs (TWRA)', 'tnd': 'TN state forests'}
        p = {'m': [[255725, 'X WMA', 'name'], ['sgtnc158', 'X WMA', 'reviewed'], ['tnd4', 'X SF', 'name']]}
        assert also_in('us', p) == ['PAD-US', 'TN WMAs (TWRA)', 'TN state forests'], also_in('us', p)
        assert also_in('ca', {'m': [[1, 'A', 1, 'name'], ['NS~1', 'A', 1, 'name · Nova Scotia parks']]}) == ['CPCAD (federal)', 'Nova Scotia parks']
        assert also_in('world', {'m': [[1, 'A', 'EEA Natura 2000', 'name']]}) == ['EEA Natura 2000']
        assert also_in('us', {}) == []
        print('also-in self-test OK'); sys.exit(0)
    try: main()
    except Exception as e:  # noqa: BLE001
        note('warning', f'also-in stopped: {type(e).__name__}: {str(e)[:200]} (report only)')

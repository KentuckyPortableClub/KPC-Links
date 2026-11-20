#!/usr/bin/env python3
"""Read-only check for the job 4 national-layer level rule (KPC owner, 20 Nov 2026).

A name-only join from PAD-US, or from one of the 13 federal layer prefixes, counts when
the record's manager level matches the park's. Levels that disagree go to check, unless
kpc_key_rules.size_pick finds a copy (within 10%, floor 5 acres) of land the park already
holds. A person's saved yes (a reviewed join) still stands. The check never changes a
key, a cache file, or the builder, and it never prints a park name or number.

  python3 .github/scripts/kpc_national_level_check.py [--keys DIR] [--cache DIR]
  python3 .github/scripts/kpc_national_level_check.py [--keys DIR] [--cache DIR] --answers PATH

--answers is a CSV, a folder, or a zip. With it, the script prints only two counts:
wrong records caught, and right records taken away.
"""
from __future__ import annotations

import argparse, csv, gzip, io, json, os, pathlib, re, sys, zipfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import kpc_key_rules as KR  # noqa: E402

# PAD-US (a numeric id) plus these 13 federal prefixes: the sheet's national-layer cut.
FEDERAL_PREFIXES = frozenset({
    'wld', 'hma', 'hab', 'rma', 'rst', 'wsrc', 'fwsr', 'fsod', 'nca', 'wsa', 'wbl', 'fws', 'trl',
})
_PRE = re.compile(r'^[a-z]+', re.I)
_STATE = re.compile(r'\bstate\b', re.I)
_FED = re.compile(r'\bnational\b|\bnwr\b|\bblm\b|\bfederal\b', re.I)


def prefix_of(rid):
    s = str(rid)
    if s.isdigit():
        return ''
    m = _PRE.match(s)
    return m.group(0).lower() if m else ''


def is_national(rid):
    """A PAD-US id (digits) or one of the 13 federal layer prefixes."""
    s = str(rid)
    if s.isdigit():
        return True
    return prefix_of(s) in FEDERAL_PREFIXES


def name_alone(why):
    """A name or words join, not reviewed, alias, trail-line or unit-code."""
    w = str(why or '')
    return (
        w == 'name' or w.startswith('name ') or w.startswith('name ·') or w.startswith('name(')
        or w == 'words' or w.startswith('words ')
    )


def park_level(name):
    """STAT if the name has a state word (that word wins when both are present), else FED, else None."""
    s = str(name or '')
    if _STATE.search(s):
        return 'STAT'
    if _FED.search(s):
        return 'FED'
    return None


def rec_level(rid, attrs):
    """Mang_Type FED or STAT from the saved copy; a federal-prefix record with no copy is FED."""
    a = attrs.get(str(rid)) or {}
    mt = str(a.get('Mang_Type') or '').upper()
    if mt in ('FED', 'STAT'):
        return mt
    if prefix_of(rid) in FEDERAL_PREFIXES:
        return 'FED'
    return mt or None


def is_copy(acres, others):
    """True when size_pick would keep this record as a copy of land the park already holds."""
    held = {'_': [x for x in others if x is not None]}
    return KR.size_pick(acres, held) is not None


def load_attrs(cache):
    """{OBJECTID string: record attrs} from a GEO_CACHE tree (US-XX.json.gz)."""
    attrs = {}
    if not cache:
        return attrs
    root = pathlib.Path(cache)
    if not root.exists():
        return attrs
    files = sorted(root.glob('US-??.json.gz')) + sorted(root.glob('US-??.json'))
    for f in files:
        try:
            raw = gzip.open(f).read() if f.suffixes[-2:] == ['.json', '.gz'] or f.name.endswith('.json.gz') else f.read_bytes()
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError, gzip.BadGzipFile):
            continue
        recs = data.get('recs') if isinstance(data, dict) else data
        if not isinstance(recs, list):
            continue
        for a in recs:
            if isinstance(a, dict) and a.get('OBJECTID') is not None:
                attrs[str(a['OBJECTID'])] = a
    return attrs


def load_keys(keys):
    """[(state, ref, park dict)] from data/us-key/US-XX.json. Parks from every state file, in file order."""
    out = []
    root = pathlib.Path(keys)
    for f in sorted(root.glob('US-??.json')):
        try:
            data = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        st = f.stem
        parks = data.get('parks') if isinstance(data, dict) else None
        if not isinstance(parks, dict):
            continue
        for ref, p in parks.items():
            if isinstance(p, dict):
                out.append((st, str(ref), p))
    return out


def joined_rows(p):
    """[(rid, acres, why), ...] from park['m']."""
    rows = []
    for row in p.get('m') or []:
        if not isinstance(row, (list, tuple)) or len(row) < 4:
            continue
        rows.append((row[0], row[2], row[3]))
    return rows


def iter_national_name_joins(keys, attrs):
    """Each name-alone national-layer join: dict with ref, state, rid, acres, park_level, rec_level, to_check."""
    for st, ref, p in load_keys(keys):
        pl = park_level(p.get('n'))
        rows = joined_rows(p)
        for rid, acres, why in rows:
            if not is_national(rid) or not name_alone(why):
                continue
            rl = rec_level(rid, attrs)
            item = {
                'state': st, 'ref': ref, 'rid': str(rid), 'acres': acres,
                'park_level': pl, 'rec_level': rl, 'to_check': False,
            }
            if pl in ('FED', 'STAT') and rl in ('FED', 'STAT') and rl != pl:
                others = [ac for r, ac, w in rows if str(r) != str(rid)]
                item['to_check'] = not is_copy(acres, others)
            yield item


def scan_keys(keys, attrs):
    """Counts on saved keys. Never includes names."""
    n_nat = n_name = n_flag = n_check = 0
    nat_p, name_p, flag_p, check_p = set(), set(), set(), set()
    # Walk parks once so national / name-alone totals include parks with no level word.
    for st, ref, p in load_keys(keys):
        rows = joined_rows(p)
        pl = park_level(p.get('n'))
        hit = hitn = False
        for rid, acres, why in rows:
            if not is_national(rid):
                continue
            hit = True
            n_nat += 1
            if not name_alone(why):
                continue
            hitn = True
            n_name += 1
            rl = rec_level(rid, attrs)
            if pl in ('FED', 'STAT') and rl in ('FED', 'STAT') and rl != pl:
                n_flag += 1
                flag_p.add(ref)
                others = [ac for r, ac, w in rows if str(r) != str(rid)]
                if not is_copy(acres, others):
                    n_check += 1
                    check_p.add(ref)
        if hit:
            nat_p.add(ref)
        if hitn:
            name_p.add(ref)
    return {
        'national_records': n_nat, 'national_parks': len(nat_p),
        'name_records': n_name, 'name_parks': len(name_p),
        'flag_records': n_flag, 'flag_parks': len(flag_p),
        'copy_records': n_flag - n_check,
        'check_records': n_check, 'check_parks': len(check_p),
    }


def _col(row, *names):
    lower = {str(k).strip().lower(): v for k, v in row.items()}
    for n in names:
        if n in lower and str(lower[n] or '').strip():
            return str(lower[n]).strip()
    return ''


def _verdict(v):
    v = str(v or '').strip().upper()
    if v in ('NO', 'N'):
        return 'NO'
    if v in ('YES', 'Y', 'BIGGER'):
        return 'YES' if v != 'BIGGER' else 'BIGGER'
    return ''


def _load_key_maps(paths):
    """From packet *.key.json files: {(ref, letter): [record ids]} for joined candidates only."""
    out = {}
    for p in paths:
        try:
            data = json.loads(pathlib.Path(p).read_text())
        except (OSError, json.JSONDecodeError):
            continue
        # packet key: {ref: {cands: {letter: {joined, ids}}}} or a list of parks
        parks = data if isinstance(data, dict) and not any(k in data for k in ('cands', 'parks')) else None
        if parks and all(isinstance(v, dict) and 'cands' in v for v in list(parks.values())[:1] or [{}]):
            items = parks.items()
        elif isinstance(data, dict) and 'cands' in data:
            items = [(data.get('ref') or data.get('park') or '', data)]
        elif isinstance(data, list):
            items = [((x.get('ref') or x.get('park') or ''), x) for x in data if isinstance(x, dict)]
        else:
            continue
        for ref, body in items:
            if not ref or not isinstance(body, dict):
                continue
            cands = body.get('cands') or {}
            for L, c in cands.items():
                if not isinstance(c, dict) or not c.get('joined'):
                    continue
                ids = [str(i) for i in (c.get('ids') or [])]
                if not ids and c.get('id') is not None:
                    ids = [str(c['id'])]
                if ids:
                    out[(str(ref), str(L).strip().upper())] = ids
    return out


def _iter_files(path):
    """Yield (kind, path-or-text) for csv/json found in a file, folder or zip. Text for zip members."""
    p = pathlib.Path(path)
    if p.is_dir():
        for f in sorted(p.rglob('*')):
            if f.is_file() and f.suffix.lower() in ('.csv', '.json'):
                yield f.suffix.lower(), f, None
        return
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as z:
            for name in z.namelist():
                low = name.lower()
                if low.endswith('.csv') or low.endswith('.json'):
                    yield pathlib.Path(low).suffix, None, z.read(name)
        return
    if p.is_file():
        yield p.suffix.lower(), p, None


def load_answers(path):
    """[(ref, record_id, verdict)] from a CSV, folder or zip. Letters are mapped via packet key files when present."""
    csv_rows = []
    key_paths = []
    key_blobs = []
    for kind, f, blob in _iter_files(path):
        if kind == '.json':
            if f is not None:
                key_paths.append(f)
            else:
                key_blobs.append(blob)
        elif kind == '.csv' or (f is not None and kind == ''):
            if f is not None:
                csv_rows.append(f.read_text(encoding='utf-8', errors='replace'))
            else:
                csv_rows.append(blob.decode('utf-8', errors='replace'))
        elif f is not None and f.suffix.lower() not in ('.csv', '.json'):
            # a bare answers file with no suffix: try csv
            csv_rows.append(f.read_text(encoding='utf-8', errors='replace'))
    # packet maps from files and from zip members written to a temp-less json load
    maps = _load_key_maps(key_paths)
    for blob in key_blobs:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        # reuse _load_key_maps by walking the same shapes in-memory
        if isinstance(data, dict) and data and all(isinstance(v, dict) and 'cands' in v for v in list(data.values())[:1] or [{}]):
            for ref, body in data.items():
                for L, c in (body.get('cands') or {}).items():
                    if isinstance(c, dict) and c.get('joined'):
                        ids = [str(i) for i in (c.get('ids') or [])] or ([str(c['id'])] if c.get('id') is not None else [])
                        if ids:
                            maps[(str(ref), str(L).strip().upper())] = ids
    out = []
    for text in csv_rows:
        rdr = csv.DictReader(io.StringIO(text))
        if not rdr.fieldnames:
            continue
        for row in rdr:
            ref = _col(row, 'ref', 'park', 'park_id')
            verd = _verdict(_col(row, 'verdict', 'answer', 'grade'))
            if not ref or not verd:
                continue
            rec = _col(row, 'record', 'record_id', 'id', 'objectid', 'rid')
            cand = _col(row, 'candidate', 'letter').upper()
            ids = []
            if rec:
                ids = [rec]
            elif cand:
                ids = list(maps.get((ref, cand)) or ([cand] if cand.isdigit() or prefix_of(cand) else []))
            for rid in ids:
                out.append((ref, str(rid), verd))
    return out


def sample_counts(answers, check_set, national_joined):
    """wrong records caught, right records taken away. Counts only.

    wrong = joined national-layer record graded NO.
    right = joined national-layer record graded YES or BIGGER.
    'Caught' / 'taken away' means the level rule would send it to check.
    A reviewed join is not in check_set, so a saved yes is not taken away.
    """
    wrong = right = caught = taken = 0
    seen = set()
    for ref, rid, verd in answers:
        key = (ref, str(rid))
        if key in seen:
            continue
        if key not in national_joined:
            continue
        seen.add(key)
        if verd == 'NO':
            wrong += 1
            if key in check_set:
                caught += 1
        elif verd in ('YES', 'BIGGER'):
            right += 1
            if key in check_set:
                taken += 1
    return {'wrong': wrong, 'caught': caught, 'right': right, 'taken': taken}


def print_key_counts(c):
    print(f"joined national-layer records {c['national_records']} on {c['national_parks']} parks")
    print(f"joined by name alone {c['name_records']}")
    print(f"level test flags {c['flag_records']} records on {c['flag_parks']} parks")
    print(f"size_pick keeps {c['copy_records']} as copies")
    print(f"would go to check {c['check_records']} records on {c['check_parks']} parks")


def print_sample_counts(s):
    print(f"sample: wrong records caught {s['caught']} of {s['wrong']}")
    print(f"sample: right records taken away {s['taken']} of {s['right']}")


def default_keys():
    env = os.environ.get('KPC_US_KEYS') or os.environ.get('KEYS')
    if env:
        return env
    cand = ROOT / 'data' / 'us-key'
    return str(cand if cand.is_dir() else pathlib.Path('data/us-key'))


def default_cache():
    return os.environ.get('GEO_CACHE') or os.environ.get('CACHE') or 'cache/us'


def main(argv=None):
    ap = argparse.ArgumentParser(description='Read-only national-layer level check (job 4). Prints counts only.')
    ap.add_argument('--keys', default=default_keys(), help='folder of US-XX.json key files (default data/us-key)')
    ap.add_argument('--cache', default=default_cache(), help='GEO_CACHE folder of US-XX.json.gz record copies')
    ap.add_argument('--answers', default='', help='sample answers: a CSV, a folder, or a zip. Prints only counts.')
    args = ap.parse_args(argv)
    attrs = load_attrs(args.cache)
    if args.answers:
        check_set = set()
        national_joined = set()
        for st, ref, p in load_keys(args.keys):
            rows = joined_rows(p)
            pl = park_level(p.get('n'))
            for rid, acres, why in rows:
                if not is_national(rid):
                    continue
                national_joined.add((ref, str(rid)))
                if not name_alone(why):
                    continue
                rl = rec_level(rid, attrs)
                if pl in ('FED', 'STAT') and rl in ('FED', 'STAT') and rl != pl:
                    others = [ac for r, ac, w in rows if str(r) != str(rid)]
                    if not is_copy(acres, others):
                        check_set.add((ref, str(rid)))
        ans = load_answers(args.answers)
        print_sample_counts(sample_counts(ans, check_set, national_joined))
        return 0
    print_key_counts(scan_keys(args.keys, attrs))
    return 0


if __name__ == '__main__':
    sys.exit(main())

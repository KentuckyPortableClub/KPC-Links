#!/usr/bin/env python3
"""kpc_ca_store_keep.py: the Canada key in store mode keeps its hard-look joins (KPC owner, 2026-11-15; keys in store mode).

A Canada HARD LOOK (data/ca-key/hardlook-joins.json, chat 11's YES rows) is a LIVE read of one named record of one layer; the
record is not in the saved copy (CA-ALL.json.gz). A store-mode run (repo variable KPC_KEY_SOURCE=store) reads no live map, so the
build step moves hardlook-joins.json aside for the build ('aside', then 'back' right after it: kpc_ca_key.py then makes no hard-look
read and opens no connection), and this script, run on the new province files before the join check:

  keep  every park whose key on --ref (main) is joined through a hard-look record ('Hard look~N:...') and that this build left
        without a join gets its entry from --ref back as it is (the existing join is kept: never worse). The province's counts,
        its index.json row, its review page and its tract records are brought in line. A park this build joined some other way
        keeps the new join.
  todo  a hard-look park that is still a pin after 'keep' (a new park, or one main has no hard-look join for) stays a pin and
        gets one row in data/ca-key/review/held-parks-todo.csv (todo_kind 'store_hard_look'): the keeper's to-do. Run after the
        join check, which rewrites that file.

  python3 .github/scripts/kpc_ca_store_keep.py aside | back      (to / from $RUNNER_TEMP/kpc-ca-hardlook-aside.json)
  python3 .github/scripts/kpc_ca_store_keep.py keep [--ref HEAD] [--key-dir data/ca-key] [--kept-out FILE]
  python3 .github/scripts/kpc_ca_store_keep.py todo [--hardlook data/ca-key/hardlook-joins.json] [--key-dir data/ca-key]
  python3 .github/scripts/kpc_ca_store_keep.py --selftest
Offline. Not a rule file: it decides no join, it only keeps main's (kpc_key_freeze.NOT_RULES). Standard library only.
"""
import argparse, csv, datetime, json, os, pathlib, re, subprocess, sys

HL = 'Hard look~'
HL_FILE = 'data/ca-key/hardlook-joins.json'
TODO_FIELDS = ['ref', 'name', 'kind', 'area', 'reason', 'pin_km', 'outline_ids', 'todo_kind', 'source', 'run_id', 'date', 'rules_version']   # = kpc_join_check.TODO_FIELDS


def hl_joined(p):
    """True when a park entry is joined through a hard-look record."""
    return isinstance(p, dict) and p.get('g') != 'pin' and any(isinstance(x, list) and x and str(x[0]).startswith(HL) for x in p.get('m') or [])


def counts(parks, detail):
    """The province counts, as kpc_ca_key.py writes them (display numbers only; no join is decided here)."""
    v = list(parks.values())
    return {'parks': len(v), 'matched': sum(1 for p in v if p['m']), 'check': sum(1 for p in v if not p['m'] and p['c']),
            'none': sum(1 for p in v if not p['m'] and not p['c'] and not p.get('a')), 'site': sum(1 for p in v if p.get('a')),
            'pin_outside': sum(1 for p in v if p.get('far')), 'pin_well_outside': sum(1 for p in v if p.get('far') == 'well outside'),
            'pin_no_shape': sum(1 for p in v if p.get('far') == 'no shape to check against'),
            'pin_swap': sum(1 for p in v if p.get('swap')), 'detail': detail}


def git_json(repo, ref, rel):
    r = subprocess.run(['git', 'show', f'{ref}:{rel}'], cwd=repo, capture_output=True)
    if r.returncode != 0: return None
    try: return json.loads(r.stdout)
    except ValueError: return None


def save(path, doc, indent=None):
    """Written as the key writes it (kpc_save's bytes, stamps left out), only when the content changed. No data/status line: this
    script changes no park data of its own (main's entries go back)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kpc_save as KS
    text = KS.canon({k: v for k, v in doc.items() if k not in KS.STAMPS} if isinstance(doc, dict) else doc, indent)
    path = pathlib.Path(path)
    if not path.exists() or path.read_text(encoding='utf-8') != text: path.write_text(text, encoding='utf-8')


def fix_review(path, kept, parks, cnt):
    """The review page: the header numbers, the kept parks out of the 'not joined' lists, one short section naming them."""
    if not path.exists(): return
    t = path.read_text(encoding='utf-8')
    t = re.sub(r'\*\*\d+ of \d+\*\* joined', f"**{cnt['matched']} of {cnt['parks']}** joined", t, count=1)
    t = re.sub(r'\*\*\d+\*\* to check, \*\*\d+\*\* nothing found', f"**{cnt['check']}** to check, **{cnt['none']}** nothing found", t, count=1)
    ks = set(kept)
    t = '\n'.join(ln for ln in t.split('\n') if not any(ln.startswith(f'- {r} ') or ln.startswith(f'- **{r}** ') for r in ks))
    t = t.rstrip('\n') + '\n\n## Kept from main (store mode: the hard look is a live read, not made in a store-mode run)\n\n' + \
        ''.join(f"- {r} {parks[r].get('n') or ''} ({parks[r].get('t') or ''}) → {'; '.join(str(x[1]) for x in parks[r].get('m') or [])}\n" for r in kept)
    path.write_text(t, encoding='utf-8')


def fix_tracts(path, before, kept):
    """The tract side file: the kept parks' tract records (and their parks-inside-parks rows) from main."""
    if not path.exists() or not before: return
    d = json.loads(path.read_text(encoding='utf-8'))
    ks = set(kept)
    for r in kept:
        if r in (before.get('parks') or {}): d.setdefault('parks', {})[r] = before['parks'][r]
    for k, a, b in (('nested', 'child', 'parent'), ('same_area', 'park', 'other')):
        have = {json.dumps(x, sort_keys=True) for x in d.get(k) or []}
        add = [x for x in before.get(k) or [] if isinstance(x, dict) and (x.get(a) in ks or x.get(b) in ks) and json.dumps(x, sort_keys=True) not in have]
        if add: d[k] = (d.get(k) or []) + add
    save(path, d)


def keep(key_dir, ref, repo='.', kept_out=None):
    kd = pathlib.Path(key_dir); repo = pathlib.Path(repo).resolve()
    idx_path = kd / 'index.json'; idx = json.loads(idx_path.read_text(encoding='utf-8')) if idx_path.exists() else {}
    all_kept = []
    for f in sorted(kd.glob('CA-??.json')):
        rel = os.path.relpath(f.resolve(), repo)
        before = git_json(repo, ref, rel)
        if not before: continue
        doc = json.loads(f.read_text(encoding='utf-8')); parks = doc.get('parks') or {}
        kept = sorted(r for r, p in (before.get('parks') or {}).items() if hl_joined(p) and r in parks and not (parks[r] or {}).get('m'))
        if not kept: continue
        for r in kept: parks[r] = before['parks'][r]
        pv = doc.get('prov') or f.stem[3:]
        side = [os.path.relpath((kd / 'review' / f'{f.stem}.md').resolve(), repo), os.path.relpath((kd / 'tracts' / f.name).resolve(), repo)]
        if parks == (before.get('parks') or {}):
            # every park is back to main's entry: the province file, its review page, its tracts and its index row are main's, byte for byte
            subprocess.run(['git', 'checkout', '-q', ref, '--', rel, *side], cwd=repo, capture_output=True)
            ri = git_json(repo, ref, os.path.relpath(idx_path.resolve(), repo)) or {}
            row = (ri.get('provinces') or {}).get(pv, before.get('counts'))
        else:
            doc['counts'] = row = counts(parks, (doc.get('counts') or {}).get('detail'))
            save(f, doc)
            fix_review(kd / 'review' / f'{f.stem}.md', kept, parks, doc['counts'])
            fix_tracts(kd / 'tracts' / f.name, git_json(repo, ref, side[1]), kept)
        if isinstance(idx.get('provinces'), dict) and pv in idx['provinces'] and row is not None: idx['provinces'][pv] = row
        print(f'::notice title=Canada key {pv} store mode::{len(kept)} hard-look join(s) kept from {ref} (a hard look is a live read; '
              f"not made in store mode): {' '.join(kept[:20])}{' ...' if len(kept) > 20 else ''}")
        all_kept += kept
    if all_kept and idx: save(idx_path, idx)   # as kpc_ca_key.py writes it (the stamp step formats it after)
    if kept_out: pathlib.Path(kept_out).write_text(''.join(r + '\n' for r in all_kept))
    print(f'Canada key store mode: {len(all_kept)} hard-look join(s) kept from {ref}')
    return all_kept


def todo(key_dir, hardlook, env=None):
    env = os.environ if env is None else env
    kd = pathlib.Path(key_dir)
    refs = list(dict.fromkeys(str(r.get('ref')) for r in (json.load(open(hardlook, encoding='utf-8')).get('rows') or []) if r.get('ref')))
    where = {}
    for f in sorted(kd.glob('CA-??.json')):
        for r, p in (json.loads(f.read_text(encoding='utf-8')).get('parks') or {}).items(): where[r] = (f.stem, p)
    rows, day = [], datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    for r in refs:
        if r not in where: continue
        area, p = where[r]
        if p.get('m') and p.get('g') != 'pin': continue
        rows.append({'ref': r, 'name': p.get('n') or '', 'kind': 'ca', 'area': area, 'pin_km': '', 'outline_ids': '', 'todo_kind': 'store_hard_look',
                     'reason': 'store mode: its join needs a hard look (a live read of the named record), which a store-mode run does not make; left as a pin',
                     'source': 'kpc_ca_store_keep', 'run_id': str(env.get('GITHUB_RUN_ID') or ''), 'date': day, 'rules_version': ''})
    path = kd / 'review' / 'held-parks-todo.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    have = list(csv.DictReader(open(path, encoding='utf-8'))) if path.exists() else []
    have = [x for x in have if x.get('todo_kind') != 'store_hard_look']
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=TODO_FIELDS, extrasaction='ignore'); w.writeheader(); w.writerows(have + rows)
    print(f'Canada key store mode: {len(rows)} hard-look park(s) left as pins, listed in {path} (todo_kind store_hard_look)')
    return rows


def aside_path(): return pathlib.Path(os.environ.get('RUNNER_TEMP') or '/tmp') / 'kpc-ca-hardlook-aside.json'


def aside(back=False):
    """Move the hard-look file out of the key's way for a store-mode build (or back). No file = nothing to do."""
    src, dst = (aside_path(), pathlib.Path(HL_FILE)) if back else (pathlib.Path(HL_FILE), aside_path())
    if not src.exists(): return False
    dst.parent.mkdir(parents=True, exist_ok=True); os.replace(src, dst)
    print('Canada key: the hard-look file is back' if back else
          "Canada key: store mode, no hard look is read (a live read; main's hard-look joins are kept by the next step)")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('keep', 'todo', 'aside', 'back')); ap.add_argument('--hardlook', default=HL_FILE); ap.add_argument('--ref', default='HEAD')
    ap.add_argument('--key-dir', default='data/ca-key'); ap.add_argument('--repo', default='.'); ap.add_argument('--kept-out')
    a = ap.parse_args(argv)
    if a.cmd in ('aside', 'back'): aside(a.cmd == 'back'); return 0
    if a.cmd == 'keep': keep(a.key_dir, a.ref, a.repo, a.kept_out); return 0
    if not a.hardlook or not os.path.exists(a.hardlook): print(f'Canada key store mode: no hard-look file ({a.hardlook}): no to-do rows'); return 0
    todo(a.key_dir, a.hardlook); return 0


def selftest():
    import tempfile
    ok = True

    def check(msg, cond):
        nonlocal ok
        ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
    E = lambda m, g='official': {'n': 'P', 't': 'Park', 'g': g, 'm': m, 'c': []}
    HLJ = E([['Hard look~3:7', 'Old Fort', 120, 'reviewed (chat 11 YES, Canada hard look)']])
    NJ = E([['1234', 'New Park', 50, 'name']])
    PIN = E([], 'pin')
    main_doc = {'prov': 'XX', 'counts': {'detail': 0.02}, 'parks': {'A': HLJ, 'B': HLJ, 'C': NJ, 'D': PIN}}
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); g = lambda *x: subprocess.run(['git', *x], cwd=t, capture_output=True, check=True)
        g('init', '-q'); g('config', 'user.email', 't@example.invalid'); g('config', 'user.name', 't')
        kd = t / 'data/ca-key'; (kd / 'review').mkdir(parents=True); (kd / 'tracts').mkdir()
        (kd / 'CA-XX.json').write_text(json.dumps(main_doc))
        (kd / 'tracts/CA-XX.json').write_text(json.dumps({'parks': {'A': [{'rid': 'Hard look~3:7'}]}, 'nested': [{'child': 'A', 'parent': 'C'}], 'same_area': []}))
        (kd / 'index.json').write_text(json.dumps({'provinces': {'XX': {}}}))
        g('add', '-A'); g('commit', '-qm', 'main')
        # the store build: A lost its hard-look join, B was joined another way, C kept, E is a new hard-look park (pin)
        (kd / 'CA-XX.json').write_text(json.dumps({'prov': 'XX', 'counts': {'detail': 0.02}, 'parks': {'A': PIN, 'B': NJ, 'C': NJ, 'D': PIN, 'E': PIN}}))
        (kd / 'tracts/CA-XX.json').write_text(json.dumps({'parks': {}, 'nested': [], 'same_area': []}))
        (kd / 'review/CA-XX.md').write_text('# x\n\n**2 of 5** joined (same name + same kind). **0** to check, **3** nothing found in CPCAD\n\n## Nothing found in CPCAD\n\n- A P (Park)\n- D P (Park)\n')
        kept = keep(kd, 'HEAD', t)
        d = json.loads((kd / 'CA-XX.json').read_text())
        check(f'only A (lost its hard-look join) is kept from main: {kept}', kept == ['A'] and d['parks']['A'] == HLJ)
        check('B joined another way keeps the new join', d['parks']['B'] == NJ)
        check(f"counts brought in line (matched {d['counts']['matched']}, none {d['counts']['none']})", d['counts']['matched'] == 3 and d['counts']['none'] == 2)
        check('index.json row = the counts', json.loads((kd / 'index.json').read_text())['provinces']['XX'] == d['counts'])
        md = (kd / 'review/CA-XX.md').read_text()
        check('review page: numbers fixed, A out of "nothing found", one kept section', '**3 of 5** joined' in md and '\n- A P (Park)\n' not in md and 'Kept from main' in md)
        tr = json.loads((kd / 'tracts/CA-XX.json').read_text())
        check('tracts: A\'s records and its nested row back from main', tr['parks'].get('A') and tr['nested'] == [{'child': 'A', 'parent': 'C'}])
        (kd / 'CA-YY.json').write_text(json.dumps({'prov': 'YY', 'counts': {'detail': 0.02, 'matched': 9}, 'parks': {'A': HLJ}}))
        (kd / 'review/CA-YY.md').write_text('main page\n'); (kd / 'tracts/CA-YY.json').write_text('{"parks":{}}')
        g('add', '-A'); g('commit', '-qm', 'yy')
        (kd / 'CA-YY.json').write_text(json.dumps({'prov': 'YY', 'counts': {'detail': 0.02}, 'parks': {'A': PIN}}))
        (kd / 'review/CA-YY.md').write_text('store page\n')
        keep(kd, 'HEAD', t)
        check('a province whose parks are all back to main is main\'s file, review page and tracts, byte for byte',
              (kd / 'review/CA-YY.md').read_text() == 'main page\n' and json.loads((kd / 'CA-YY.json').read_text())['counts']['matched'] == 9
              and not subprocess.run(['git', 'status', '--porcelain', 'data/ca-key/CA-YY.json', 'data/ca-key/review/CA-YY.md'], cwd=t, capture_output=True, text=True).stdout)
        hl = t / 'hl.json'; hl.write_text(json.dumps({'rows': [{'ref': 'A'}, {'ref': 'E'}, {'ref': 'Z'}]}))
        (kd / 'review/held-parks-todo.csv').write_text(','.join(TODO_FIELDS) + '\nQ,q,ca,CA-XX,held: far,,,join_held,kpc_join_check,,,\n')
        rows = todo(kd, hl, {})
        got = list(csv.DictReader(open(kd / 'review/held-parks-todo.csv')))
        check(f"to-do: only E (a pin hard-look park) is listed, the join check's row stays: {[x['ref'] for x in got]}",
              [x['ref'] for x in rows] == ['E'] and [(x['ref'], x['todo_kind']) for x in got] == [('Q', 'join_held'), ('E', 'store_hard_look')])
        todo(kd, hl, {})
        check('to-do run twice = one row per park', [x['ref'] for x in csv.DictReader(open(kd / 'review/held-parks-todo.csv'))] == ['Q', 'E'])
        cwd = os.getcwd(); os.chdir(t); os.environ['RUNNER_TEMP'] = str(t)
        try:
            (kd / 'hardlook-joins.json').write_text('{"rows": []}')
            check('aside: the hard-look file leaves data/ca-key, back: it returns', aside() and not (kd / 'hardlook-joins.json').exists() and aside(True) and (kd / 'hardlook-joins.json').exists())
            (kd / 'hardlook-joins.json').unlink(); check('aside with no file = nothing to do', aside() is False)
        finally: os.chdir(cwd)
        g('add', '-A'); g('commit', '-qm', 'b')
        check('keep again changes nothing (no lost hard-look join left)', keep(kd, 'HEAD', t) == [])
    print('SELFTEST PASS' if ok else 'SELFTEST FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    if sys.argv[1:2] == ['--selftest']: sys.exit(selftest())
    sys.exit(main())

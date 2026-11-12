#!/usr/bin/env python3
"""kpc_area_join.py (KPC owner, 2026-11-12): each area stands alone in a key join. Helpers shared by the world, US and Canada key joins.
Not a rule file (kpc_key_freeze.NOT_RULES): it never decides a join, it only decides which area's bytes are saved and which are kept
from main. Standard library only. Scheme: out/nov12/AB/SHARED-SCHEME.md (units, "kept from main", reason codes).

Why: Nov 11 commit a6c493c (a partial world join) rewrote the SHARED review files from only the countries of that run and wiped every
other country's rows (66 held joins -> 0, 35 join-check rows -> 1). The join check (kpc_join_check.py) writes held-joins.json / .csv,
held-joins-ledger.csv and join-check.json / .csv WHOLE from the key files git shows changed this run, on every run (also a complete
green one: an area whose file did not change loses its rows). Here every shared review file is merged PER AREA after the join check:
the rows of an area whose key file this run did not change come back from main byte for byte; a file that cannot be split per area is
put back from main whole (not written this run) and the run says so.

  python3 .github/scripts/kpc_area_join.py keep-rows --review data/us-key/review --key-dir data/us-key [--unchanged] [--areas "US-TN"]
      --unchanged: keep main's rows of EVERY area whose key file git shows unchanged (the default in the key workflows from Nov 12)
      --areas: keep main's rows of these areas too (the world's expected holds)
  python3 .github/scripts/kpc_area_join.py summary --record /tmp/world-join.json --index data/world-key/index.json [--ref HEAD]
      the ONE run summary table: area | built? | verdict | saved or kept from main | hash stamped | why
  python3 .github/scripts/kpc_area_join.py assert-kept --record /tmp/world-join.json --key-dir data/world-key [--ref HEAD]
      exit 1 when an area that is not saved this run differs from main (its key / review page / tracts file or its index row)
  python3 .github/scripts/kpc_area_join.py --selftest"""
import argparse, csv, io, json, os, pathlib, re, subprocess, sys

AREA_RE = re.compile(r'^(?:[A-Z]{2}|(?:US|CA)-[A-Z]{2})$')
REVIEW_FILES = ('held-joins.json', 'join-check.json', 'held-joins.csv', 'join-check.csv', 'held-joins-ledger.csv')
# Reason codes of the run summary table (the 'why' column starts with one of these; SHARED-SCHEME.md section 7)
REASONS = ('built', 'reused', 'held-expected', 'held-gate', 'failed', 'not-built', 'drop-guard', 'not-planned', 'join-refused', 'cancelled')
KEY_FILE = {'world': re.compile(r'^([A-Z]{2})\.json$'), 'us': re.compile(r'^(US-[A-Z]{2})\.json$'), 'ca': re.compile(r'^(CA-[A-Z]{2})\.json$')}


def kind_of(key_dir):
    n = pathlib.Path(key_dir).name
    return {'world-key': 'world', 'us-key': 'us', 'ca-key': 'ca'}.get(n, 'world')


def csv_records(text):
    """([(raw text of the record, {column: value})], (header raw text, header)); the raw text keeps its own bytes."""
    lines = io.StringIO(text, newline='').readlines()
    it = iter(lines); pos = [0]
    def feed():
        for ln in it:
            pos[0] += 1; yield ln
    rd = csv.reader(feed()); out = []
    try: head = next(rd)
    except StopIteration: return None, []
    head_raw = ''.join(lines[:pos[0]]); last = pos[0]
    for row in rd:
        out.append((''.join(lines[last:pos[0]]), dict(zip(head, row)))); last = pos[0]
    return (head_raw, head), out


def park_areas(*texts):
    """{park ref: area} from the held-joins rows (json or csv text, main's and this run's): the ledger rows name only the park."""
    m = {}
    for t in texts:
        if not t: continue
        try:
            d = json.loads(t)
            rows = d.get('parks') if isinstance(d, dict) else None
        except ValueError:
            rows = [r for _, r in (csv_records(t)[1] or [])]
        for r in rows or []:
            if isinstance(r, dict) and r.get('park') and AREA_RE.match(str(r.get('area') or '')): m.setdefault(str(r['park']), str(r['area']))
    return m


def row_area(row, name, parks=None):
    """The area of one review row, or None (the file then cannot be split per area)."""
    if name != 'held-joins-ledger.csv':
        a = str(row.get('area') or '')
        return a if AREA_RE.match(a) else None
    p = str(row.get('park') or '')
    if parks and p in parks: return parks[p]
    cc = p.split('-')[0]
    return cc if re.fullmatch(r'[A-Z]{2}', cc) and cc not in ('US', 'CA') else None   # a world park ref starts with its country


def merge_rows(name, main_text, cur_text, keep, parks=None):
    """New text of one review file: this run's rows of every area NOT in keep + main's rows of the areas in keep (byte for byte), in
    area order (each area's rows in their own order). None = the rows cannot be split per area safely (put main's file back whole)."""
    keep = set(keep)
    if name.endswith('.json'):
        lk = 'parks' if name == 'held-joins.json' else 'rows'
        try: m, c = (json.loads(main_text) if main_text else {lk: []}), (json.loads(cur_text) if cur_text else None)
        except ValueError: return None
        if c is None: c = dict(m)
        if not (isinstance(m, dict) and isinstance(c, dict) and isinstance(m.get(lk), list) and isinstance(c.get(lk), list)): return None
        rows = []
        for src, take in ((c[lk], lambda x: x not in keep), (m[lk], lambda x: x in keep)):
            for r in src:
                a = row_area(r, name, parks) if isinstance(r, dict) else None
                if a is None: return None
                if take(a): rows.append((a, r))
        rows.sort(key=lambda t: t[0])   # stable
        c[lk] = [r for _, r in rows]
        if name == 'held-joins.json': c['count'] = len(c[lk])
        else: c['suspect'] = len(c[lk])   # 'held' stays this run's count (held-joins.json 'count' is the merged one)
        c['kept_from_main'] = sorted(keep)
        return json.dumps(c, indent=1, ensure_ascii=False)   # the join check's own format (json.dump, indent 1, no newline at the end)
    mh, mr = csv_records(main_text or '')
    ch, cr = csv_records(cur_text or '') if cur_text else (mh, [])
    if mh is None and ch is None: return cur_text
    if mh is not None and ch is not None and mh[1] != ch[1]: return None   # another header: the columns cannot be lined up
    rows = []
    for src, take in ((cr, lambda x: x not in keep), (mr, lambda x: x in keep)):
        for raw, r in src:
            a = row_area(r, name, parks)
            if a is None: return None
            if take(a): rows.append((a, raw))
    rows.sort(key=lambda t: t[0])
    return (ch or mh)[0] + ''.join(raw for _, raw in rows)


def git(top, *a):
    return subprocess.run(['git', *a], cwd=top, capture_output=True)


def git_show(ref, rel, top):
    r = git(top, 'show', f'{ref}:{rel}')
    return r.stdout.decode('utf-8') if r.returncode == 0 else None


def toplevel(p):
    p = pathlib.Path(p)
    return subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=p if p.is_dir() else p.parent, capture_output=True, text=True).stdout.strip()


def changed_areas(key_dir, ref='HEAD'):
    """The areas whose key file differs from `ref` (or is new) in the working tree: the files the join check read this run."""
    key_dir = pathlib.Path(key_dir); top = toplevel(key_dir); rx = KEY_FILE[kind_of(key_dir)]
    rel = os.path.relpath(key_dir.resolve(), top).replace(os.sep, '/')
    r = git(top, 'status', '--porcelain', '--untracked-files=all', '--', rel)
    if r.returncode != 0: return None
    out = set()
    for ln in r.stdout.decode('utf-8', 'replace').splitlines():
        p = ln[3:].strip().strip('"')
        if '/' in p and p.rsplit('/', 1)[0] == rel:
            m = rx.match(p.rsplit('/', 1)[1])
            if m: out.add(m.group(1))
    return out


def all_review_areas(review, ref, top):
    out = set()
    for name in REVIEW_FILES:
        f = pathlib.Path(review) / name
        rel = os.path.relpath(f.resolve(), top).replace(os.sep, '/')
        txts = [git_show(ref, rel, top), f.read_bytes().decode('utf-8') if f.is_file() else None]
        parks = park_areas(*txts)
        for t in txts:
            if not t: continue
            try:
                d = json.loads(t); rows = (d.get('parks') or d.get('rows') or []) if isinstance(d, dict) else []
            except ValueError: rows = [r for _, r in (csv_records(t)[1] or [])]
            for r in rows:
                a = row_area(r, name, parks) if isinstance(r, dict) else None
                if a: out.add(a)
    return out


def keep_rows(review, keep=(), ref='HEAD', unchanged_of=None):
    """Write the merged review files; returns [(file, what happened)]. unchanged_of = the key folder: every area whose key file is
    unchanged against ref keeps main's rows too."""
    review = pathlib.Path(review); keep = set(keep)
    top = toplevel(review if review.is_dir() else review.parent)
    if unchanged_of is not None:
        ch = changed_areas(unchanged_of, ref)
        if ch is None:   # git cannot tell what changed: every file back from main whole (fail closed)
            ch, keep = set(), None
        else:
            keep |= all_review_areas(review, ref, top) - ch
    done = []
    texts = {}
    for name in REVIEW_FILES:
        f = review / name
        rel = os.path.relpath(f.resolve(), top).replace(os.sep, '/')
        texts[name] = (git_show(ref, rel, top), f.read_bytes().decode('utf-8') if f.is_file() else None)
    parks = park_areas(*texts['held-joins.json'], *texts['held-joins.csv'])   # the ledger names only the park
    for name in REVIEW_FILES:
        f = review / name
        main_text, cur_text = texts[name]
        if main_text is None and cur_text is None: continue
        if keep is not None and not keep: continue   # nothing to keep: this run's file as the join check wrote it
        new = None if keep is None else merge_rows(name, main_text, cur_text, keep, parks)
        if new is None:
            if main_text is None: f.unlink(missing_ok=True)
            else: f.write_bytes(main_text.encode('utf-8'))
            done.append((name, "NOT written this run: its rows cannot be split per area; main's copy kept whole")); continue
        if new != cur_text:
            f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(new.encode('utf-8'))
        done.append((name, f"rows of {len(keep)} area(s) not rebuilt this run kept from main" + (f" ({' '.join(sorted(keep)[:12])}{' ...' if len(keep) > 12 else ''})")))
    return done


# ---------------------------------------------------------------- the record of a join, the summary table, the kept check
def load(p, default=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return default  # noqa: BLE001


def row_hash(row):
    return (row or {}).get('rules') if isinstance(row, dict) else None


def summary_rows(record, index, main_index):
    """[(area, built?, verdict, saved or kept, hash stamped, why)] from the join's record and the index after the stamp."""
    rows_key = record.get('rows_key') or 'countries'
    now = (index or {}).get(rows_key) or {}; old = (main_index or {}).get(rows_key) or {}
    keywide_old = (main_index or {}).get('rules') or 'none'
    out = []
    for a, r in sorted((record.get('areas') or {}).items()):
        saved = r.get('action') == 'saved'
        if saved:
            h = row_hash(now.get(a)) or (index or {}).get('rules') or 'none'
            hs = f'{h} (new)' if h != row_hash(old.get(a)) else f'{h}'
        else:
            h = row_hash(old.get(a))
            hs = f'{h} (kept)' if h else f'kept: none recorded (key-wide on main {keywide_old})'
        out.append((a, r.get('built') or '-', r.get('verdict') or '-', 'saved' if saved else 'kept from main', hs, f"{r.get('code')}: {r.get('why') or ''}".strip()))
    return out


def write_summary(title, rows, problems=(), dest=None):
    t = f'**{title}**' + (f" - {'; '.join(problems[:20])}" if problems else '') + \
        '\n\n| area | built? | verdict | saved or kept from main | hash stamped | why |\n|---|---|---|---|---|---|\n'
    t += ''.join('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |\n' for r in rows)
    dest = dest or os.environ.get('GITHUB_STEP_SUMMARY')
    if dest: open(dest, 'a', encoding='utf-8').write(t + '\n')
    return t


def assert_kept(record, key_dir, ref='HEAD'):
    """[problems]: an area NOT saved this run must be main's bytes (key file, review page, tracts file) and main's index row."""
    key_dir = pathlib.Path(key_dir); top = toplevel(key_dir)
    rel = os.path.relpath(key_dir.resolve(), top).replace(os.sep, '/')
    rows_key = record.get('rows_key') or 'countries'
    idx_now = (load(key_dir / 'index.json', {}) or {}).get(rows_key) or {}
    m = git_show(ref, f'{rel}/index.json', top)
    idx_main = ((json.loads(m) if m else {}) or {}).get(rows_key) or {}
    bad = []
    for a, r in sorted((record.get('areas') or {}).items()):
        if r.get('action') == 'saved': continue
        for sub in (f'{a}.json', f'review/{a}.md', f'tracts/{a}.json'):
            f = key_dir / sub
            mb = git(top, 'show', f'{ref}:{rel}/{sub}')
            have = f.read_bytes() if f.is_file() else None
            want = mb.stdout if mb.returncode == 0 else None
            if have != want: bad.append(f'{a}: {rel}/{sub} is not main\'s bytes')
        if idx_now.get(a) != idx_main.get(a): bad.append(f'{a}: its index row is not main\'s')
    return bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['--selftest']: return selftest()
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['keep-rows', 'summary', 'assert-kept', 'record-whole'])
    ap.add_argument('--rows-key', default='provinces'); ap.add_argument('--kept', default='0'); ap.add_argument('--why', default=''); ap.add_argument('--out')
    ap.add_argument('--review'); ap.add_argument('--key-dir'); ap.add_argument('--areas', default=''); ap.add_argument('--unchanged', action='store_true')
    ap.add_argument('--ref', default='HEAD'); ap.add_argument('--record'); ap.add_argument('--index'); ap.add_argument('--title', default='Key join')
    a = ap.parse_args(argv)
    if a.cmd == 'keep-rows':
        for name, what in keep_rows(a.review, a.areas.split(), a.ref, a.key_dir if a.unchanged else None):
            print(f"::{'warning' if what.startswith('NOT') else 'notice'} title=Review files::{name}: {what}", flush=True)
        return 0
    if a.cmd == 'record-whole':   # Canada: one job, so every province is saved or every province is kept
        idx = load(a.index, {}) or {}
        top = toplevel(a.index); rel = os.path.relpath(pathlib.Path(a.index).resolve(), top).replace(os.sep, '/')
        m = git_show(a.ref, rel, top); old = (json.loads(m) if m else {}) or {}
        areas = sorted(set((idx.get(a.rows_key) or {})) | set((old.get(a.rows_key) or {})))
        kept = a.kept == '1'
        code, _, why = (a.why or 'failed: the build stopped').partition(': ')
        rec = {'rows_key': a.rows_key, 'areas': {x: ({'built': 'no', 'verdict': 'held' if code == 'held-gate' else '-', 'code': code, 'why': why, 'action': 'kept'} if kept else
                                                    {'built': 'yes', 'verdict': 'green', 'code': 'built', 'why': 'built and saved (whole-Canada job)', 'action': 'saved'}) for x in areas}, 'problems': []}
        rec['red'] = sorted(rec['areas']) if kept else []
        pathlib.Path(a.out).write_text(json.dumps(rec, indent=1, sort_keys=True) + '\n', encoding='utf-8')
        return 0
    rec = load(a.record, None)
    if a.cmd == 'summary':
        if not isinstance(rec, dict):
            write_summary(a.title, [], ['no join record: the join did not finish, NOTHING was saved this run'])
            print('::warning title=Run summary::no join record (the join did not finish): nothing was saved', flush=True); return 0
        top = toplevel(a.index); rel = os.path.relpath(pathlib.Path(a.index).resolve(), top).replace(os.sep, '/')
        m = git_show(a.ref, rel, top)
        rows = summary_rows(rec, load(a.index, {}), json.loads(m) if m else {})
        red = [r[0] for r in rows if r[3] != 'saved' and not r[5].startswith(('held-expected', 'reused'))]
        write_summary(a.title, rows, ([f"RED: {' '.join(red)} kept from main (not saved this run)"] if red else []) + list(rec.get('problems') or []))
        return 0
    bad = assert_kept(rec or {}, a.key_dir, a.ref)
    for b in bad: print(f'::error title=Kept from main::{b}', flush=True)
    if bad: print('::error title=Kept from main::an area that is not saved this run is not byte-identical to main: NOTHING is saved (fail closed)', flush=True)
    return 1 if bad else 0


def selftest():
    import tempfile
    n = [0, 0]
    def check(name, cond):
        n[0] += 1; n[1] += 0 if cond else 1
        print(('PASS ' if cond else 'FAIL ') + name)
    hj = lambda rows: json.dumps({'key': 'us', 'count': len(rows), 'parks': rows}, indent=1, ensure_ascii=False)
    r = lambda p, a: {'park': p, 'area': a}
    m = hj([r('US-1', 'US-AL'), r('US-2', 'US-TN')]); c = hj([r('US-9', 'US-AL')])
    got = json.loads(merge_rows('held-joins.json', m, c, {'US-TN'}))
    check('json: this run\'s AL row + main\'s TN row, count merged', [x['park'] for x in got['parks']] == ['US-9', 'US-2'] and got['count'] == 2)
    check('json: a row with no area cannot be split (None)', merge_rows('held-joins.json', hj([{'park': 'x'}]), c, {'US-TN'}) is None)
    mc = 'park,area\nUS-1,US-AL\nUS-2,US-TN\n'; cc = 'park,area\nUS-9,US-AL\n'
    check('csv: rows merged per area, raw bytes kept', merge_rows('held-joins.csv', mc, cc, {'US-TN'}) == 'park,area\nUS-9,US-AL\nUS-2,US-TN\n')
    check('csv: another header = None', merge_rows('held-joins.csv', mc, 'other\n1\n', {'US-TN'}) is None)
    led = 'park,kind\nUS-2,pile-enter\n'
    check('ledger: a US park is mapped to its state through held-joins', merge_rows('held-joins-ledger.csv', led, 'park,kind\n', {'US-TN'}, park_areas(m)) == led)
    check('ledger: an unmapped US park = None (US is not a state)', merge_rows('held-joins-ledger.csv', led, 'park,kind\n', {'US-TN'}, {}) is None)
    check('ledger: a world park maps by its prefix', row_area({'park': 'FR-14979'}, 'held-joins-ledger.csv') == 'FR')
    with tempfile.TemporaryDirectory() as td:
        t = pathlib.Path(td); k = t / 'data/us-key'; (k / 'review').mkdir(parents=True)
        for st in ('US-AL', 'US-TN'): (k / f'{st}.json').write_text('{"parks":{}}')
        (k / 'review/held-joins.json').write_text(m); (k / 'review/held-joins.csv').write_text(mc)
        subprocess.run(['git', 'init', '-q'], cwd=t); subprocess.run(['git', 'add', '-A'], cwd=t)
        subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'm'], cwd=t)
        (k / 'US-AL.json').write_text('{"parks":{"x":1}}'); (k / 'review/held-joins.json').write_text(c); (k / 'review/held-joins.csv').write_text(cc)
        check('changed_areas: only AL', changed_areas(k) == {'US-AL'})
        keep_rows(k / 'review', (), 'HEAD', k)
        got = json.loads((k / 'review/held-joins.json').read_text())
        check('keep-rows --unchanged: TN (unchanged) keeps main\'s row, AL takes this run\'s', [x['park'] for x in got['parks']] == ['US-9', 'US-2'])
        check('keep-rows --unchanged: csv too', (k / 'review/held-joins.csv').read_text() == 'park,area\nUS-9,US-AL\nUS-2,US-TN\n')
    print(f"SELFTEST {'PASS' if not n[1] else 'FAIL'}: {n[0]} cases")
    return 0 if not n[1] else 1


if __name__ == '__main__':
    sys.exit(main())

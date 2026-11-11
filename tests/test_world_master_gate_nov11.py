#!/usr/bin/env python3
"""Nov 11 (KPC owner, 2026-11-11): the world key master gate after run 43082247085 (all 4 build jobs red on the gate, 15 saved copies moved
aside, the join still saved AU CZ GB MP NZ to main, job 2's part lost to an upload-artifact API error).
  1) the join takes only the countries a part's verdict clears (kpc_world_key_join.py --gate): green saves, a moved-aside copy's country
     is held (main keeps its file and index row), no verdict / unknown gate / changed files = the whole part held, a missing part is not joined;
  2) a copy trimmed to parks is checked against its OWN manifest, exactly; a trimmed copy with a bad or missing manifest is refused;
     a full copy keeps its full baseline; a trimmed copy never records or replaces a baseline;
  3) owner-approved baselines are read only from a signed *.approved.json, per copy sha256; the proposed file is never read;
  6) the workflow: verdict in the part, upload / download tried 3 times, the join gate, no post-key check when nothing was saved.
Offline: temp folders only. Run: python3 -B tests/test_world_master_gate_nov11.py"""
import contextlib, datetime, gzip, hashlib, io, json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M  # noqa: E402
import kpc_master_cli as CLI  # noqa: E402
import kpc_world_key_join as J  # noqa: E402
ok = True


def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)


def quiet(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): r = fn(*a)
    return r, buf.getvalue()


def write_copy(p, recs, manifest=None):
    blob = {'cc': p.name[2:4], 'recs': recs}
    if manifest is not None: blob['manifest'] = manifest
    with gzip.GzipFile(p, 'wb', mtime=0) as f: f.write(json.dumps(blob, separators=(',', ':')).encode('utf-8'))   # same bytes every time (the sha256 tests)
    return blob


def recs(n, src='L1', start=0): return [{'id': start + i, 'n': f'park {start + i}', 'src': src, '_r': [[[1.0, 2.0]]]} for i in range(n)]


# ------------------------------------------------------------------ 1) the join: only the countries the verdict clears
def setup(t):
    o = t / 'world-key'; (o / 'review').mkdir(parents=True)
    (o / 'index.json').write_text(json.dumps({'countries': {c: {'p': 'old'} for c in ('AU', 'DE', 'GB', 'FR')}, 'build': 'b1'}))
    for c in ('AU', 'DE', 'GB', 'FR'): (o / f'{c}.json').write_text(json.dumps({'old': c}))
    (o / 'outline-test.json').write_text(json.dumps({'AU': {'outlines': 0}, 'DE': {'outlines': 0}}, indent=1))
    (t / 'world-bounds').mkdir()
    return o


def mkpart(t, i, countries, rc='0', short='', verdict=True):
    d = t / 'parts' / f'world-key-part-{i}'; (d / 'world-key' / 'review').mkdir(parents=True); (d / 'world-bounds').mkdir()
    (d / 'countries.txt').write_text(' '.join(countries) + '\n'); (d / 'failed.txt').write_text(''); (d / 'done.txt').write_text(''.join(c + '\n' for c in countries))
    (d / 'world-key' / 'index.json').write_text(json.dumps({'countries': {c: {'p': f'new{i}'} for c in countries}}))
    (d / 'world-key' / 'outline-test.json').write_text(json.dumps({c: {'outlines': 9} for c in countries}, indent=1))
    for c in countries:
        (d / 'world-key' / f'{c}.json').write_text(json.dumps({'new': i, 'c': c}))
        (d / 'world-key' / 'review' / f'{c}.md').write_text(f'review {c}')
        (d / 'world-bounds' / c).mkdir(); (d / 'world-bounds' / c / 'x.txt').write_text('new')
    if verdict:
        (t / f'rc{i}').write_text(rc + '\n') if rc is not None else None
        (t / f'short{i}').write_text(short)
        quiet(J.main, ['verdict', '--part', str(d), '--countries', ' '.join(countries), '--rc-file', str(t / f'rc{i}'), '--short-file', str(t / f'short{i}')])
    return d


def join(t, parts, gate=True):
    here = os.getcwd(); os.chdir(t); out = t / 'gh-out'; out.write_text(''); os.environ['GITHUB_OUTPUT'] = str(out)
    try:
        rc, log = quiet(J.main, [str(p) for p in parts] + (['--gate', '--held-out', str(t / 'held.txt')] if gate else []) +
                        ['--out', str(t / 'world-key'), '--bounds', str(t / 'world-bounds'), '--failed-out', str(t / 'failed.txt')])
    finally:
        import kpc_save
        kpc_save.flush_status(); os.chdir(here); os.environ.pop('GITHUB_OUTPUT', None)
    return rc, log, out.read_text()


def idx(t): return json.load(open(t / 'world-key' / 'index.json'))['countries']


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); o = setup(t)
    p0 = mkpart(t, 0, ['DE', 'GB'], rc='0'); p1 = mkpart(t, 1, ['AU', 'FR'], rc='7', short='W-AU\n')
    rc, log, gh = join(t, [p0, p1])
    check('gate green: DE and GB are saved (key files and index rows)', rc == 0 and json.load(open(o / 'DE.json'))['new'] == 0 and idx(t)['GB'] == {'p': 'new0'})
    check('gate red: AU (its copy moved aside) is NOT saved, main keeps its previous file and index row', json.load(open(o / 'AU.json')) == {'old': 'AU'} and idx(t)['AU'] == {'p': 'old'}
          and not (o / 'review' / 'AU.md').exists() and not (t / 'world-bounds' / 'AU').exists())
    check('gate red: FR of the same part (its copy passed) is saved', json.load(open(o / 'FR.json'))['new'] == 1 and idx(t)['FR'] == {'p': 'new1'})
    check('a held country is named failed (the stamp then says complete=false) and listed held', 'AU' in (t / 'failed.txt').read_text().split()
          and (t / 'held.txt').read_text().split()[0] == 'AU' and 'title=Master gate AU::held' in log)
    ot = json.load(open(o / 'outline-test.json'))
    check('shared files: a held country\'s key is not taken from its part, the others are', ot['AU'] == {'outlines': 0} and ot['FR'] == {'outlines': 9} and ot['DE'] == {'outlines': 9})
    check('built = the countries saved (3)', 'built=3' in gh)

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); o = setup(t)
    p0 = mkpart(t, 0, ['DE', 'GB'], verdict=False); p1 = mkpart(t, 1, ['AU', 'FR'], rc='7', short='W-AU W-FR\n')
    rc, log, gh = join(t, [p0, p1])
    check('missing verdict file = the whole part held (nothing of it saved, not even its shared file keys)', rc == 0 and json.load(open(o / 'DE.json')) == {'old': 'DE'}
          and json.load(open(o / 'GB.json')) == {'old': 'GB'} and json.load(open(o / 'outline-test.json')) == {'AU': {'outlines': 0}, 'DE': {'outlines': 0}})
    check('every country held = nothing saved: built=0 (stamp, save and world-bounds steps skip)', 'built=0' in gh and sorted(x.split()[0] for x in (t / 'held.txt').read_text().splitlines()) == ['AU', 'DE', 'FR', 'GB'])
    check('the index is not rewritten when nothing is saved', json.load(open(o / 'index.json'))['build'] == 'b1')

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); o = setup(t)
    p0 = mkpart(t, 0, ['DE', 'GB'], rc=None)   # the gate step left no exit code
    p1 = mkpart(t, 1, ['AU', 'FR'], rc='1', short='1\n')   # the gate stopped with an error
    v0 = json.load(open(p0 / 'master-gate.json')); v1 = json.load(open(p1 / 'master-gate.json'))
    check('no gate exit code = gate unknown, every country held', v0['gate'] == 'unknown' and v0['held'] == ['DE', 'GB'])
    check('the gate stopped (exit 1) = gate error, every country held', v1['gate'] == 'error' and v1['held'] == ['AU', 'FR'])
    rc, log, gh = join(t, [p0, p1])
    check('unknown / error gates: nothing saved', all(json.load(open(o / f'{c}.json')) == {'old': c} for c in ('AU', 'DE', 'FR', 'GB')) and 'built=0' in gh)

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); o = setup(t)
    p0 = mkpart(t, 0, ['DE', 'GB'], rc='0')
    (p0 / 'world-key' / 'DE.json').write_text('{"changed after the verdict": 1}')
    p1 = mkpart(t, 1, ['AU', 'FR'], rc='0'); (p1 / 'world-key' / 'review' / 'FR.md').unlink()   # a part cut short
    rc, log, gh = join(t, [p0, p1])
    check('a file changed after the verdict = the part held', json.load(open(o / 'DE.json')) == {'old': 'DE'} and 'not the files its verdict lists' in log)
    check('a part missing a file its verdict lists (cut short) = the part held', json.load(open(o / 'FR.json')) == {'old': 'FR'} and 'built=0' in gh)

with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); o = setup(t)
    p0 = mkpart(t, 0, ['DE', 'GB'], rc='0')   # the part of the job with AU FR never arrived (upload failed)
    rc, log, gh = join(t, [p0])
    check('a failed shard (no part): its countries are not joined and not saved', json.load(open(o / 'AU.json')) == {'old': 'AU'} and json.load(open(o / 'FR.json')) == {'old': 'FR'}
          and json.load(open(o / 'DE.json'))['new'] == 0 and idx(t)['AU'] == {'p': 'old'})
    import kpc_key_freeze as KF
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_freeze.py'), 'missing', '--planned-groups',
                        json.dumps([{'i': 0, 'countries': 'DE GB'}, {'i': 1, 'countries': 'AU FR'}]), '--built-file', str(p0 / 'done.txt')], capture_output=True, text=True, cwd=t)
    check('... and the join names them failed (kpc_key_freeze.py missing)', sorted(r.stdout.split()) == ['AU', 'FR'])

v = J.make_verdict(tempfile.gettempdir() + '/no-such-part-dir', 'AU FR', '7', 'W-DE\n')
check('a short copy of a country the job does not own = every country held', v['gate'] == 'error' and v['held'] == ['AU', 'FR'])
v = J.make_verdict(tempfile.gettempdir() + '/no-such-part-dir', 'AU FR', '0', 'W-AU\n')
check('exit 0 with a short list = every country held', v['gate'] == 'error' and v['held'] == ['AU', 'FR'])
v = J.make_verdict(tempfile.gettempdir() + '/no-such-part-dir', 'AU FR', '0', '')
check('exit 0 and no short copy = green, nothing held', v['gate'] == 'green' and v['held'] == [])

# ------------------------------------------------------------------ 2) + 3) the gate: manifests and approved baselines
def gate(t, *extra):
    r, log = quiet(CLI.main, ['gate', '--cache', str(t / 'cache'), '--root', str(t / 'outlines'), '--report', str(t / 'short.txt')] + list(extra))
    return r, log, sorted(p.name for p in (t / 'cache').glob('*.json.gz')), sorted(p.name for p in (t / 'cache' / 'short').glob('*.json.gz')) if (t / 'cache' / 'short').is_dir() else []


def fresh(t):
    import shutil
    for d in ('cache', 'outlines'): shutil.rmtree(t / d, ignore_errors=True)
    (t / 'cache').mkdir(); (t / 'outlines').mkdir()
    json.dump({'format': 1, 'layers': {}, 'caches': {'W-AS': {'expected_count': 1711}, 'W-DE': {'expected_count': 100}, 'W-AU': {'expected_count': 3743432}}}, open(t / 'outlines' / 'layers.json', 'w'))


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); fresh(t)
    b = write_copy(t / 'cache' / 'W-AS.json.gz', recs(2, 'nps') + recs(1, 'fws', 10))
    r, log = quiet(CLI.main, ['bundle-manifest', str(t / 'cache' / 'W-AS.json.gz'), '--by', 'KPC owner', '--made', '2026-11-11', '--source-full', 'nps=1700', '--source-full', 'fws=11'])
    m = M.load_saved(t / 'cache' / 'W-AS.json.gz').get('manifest') or {}
    check('bundle-manifest writes the manifest INTO the copy (trimmed, per layer, total, who / when, sha256, source full counts)',
          r == 0 and m.get('trimmed') is True and m.get('layers') == {'src:nps': 2, 'src:fws': 1} and m.get('total') == 3 and m.get('made_by') == 'KPC owner'
          and m.get('made') == '2026-11-11' and len(m.get('recs_sha256', '')) == 64 and m.get('source_full') == {'nps': 1700, 'fws': 11})
    r, _ = quiet(CLI.main, ['bundle-manifest', str(t / 'cache' / 'W-AS.json.gz'), '--check']); check('bundle-manifest --check passes on the copy it stamped', r == 0)
    r, _ = quiet(CLI.main, ['bundle-manifest', str(t / 'cache' / 'W-AS.json.gz'), '--by', 'KPC owner']); check('a second manifest needs --replace', r == 1)
    write_copy(t / 'cache' / 'W-DE.json.gz', recs(100))
    r, log, kept, aside = gate(t, '--allow-trimmed')
    check('trimmed copy with its manifest: checked against the manifest (3), not the full 1,711: used', r == 0 and kept == ['W-AS.json.gz', 'W-DE.json.gz'] and 'is not used here and not changed' in log)
    check('the gate wrote no baseline (layers.json unchanged)', json.load(open(t / 'outlines' / 'layers.json'))['caches']['W-AS'] == {'expected_count': 1711})
    r, log, kept, aside = gate(t)
    check('without --allow-trimmed (US / Canada gates) a trimmed copy is refused, moved aside', r == 7 and aside == ['W-AS.json.gz'])

    fresh(t)
    mm = M.make_manifest('W-AS.json.gz', {'recs': recs(3)}, 'KPC owner', '2026-11-11')
    write_copy(t / 'cache' / 'W-AS.json.gz', recs(2), mm)
    r, log, kept, aside = gate(t, '--allow-trimmed')
    check('trimmed copy with fewer records than its manifest = SHORT, moved aside (exact)', r == 7 and aside == ['W-AS.json.gz'] and 'SHORT against its own manifest' in log)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(4), mm)
    r, log, kept, aside = gate(t, '--allow-trimmed')
    check('trimmed copy with records its manifest does not list = refused', r == 7 and aside == ['W-AS.json.gz'] and 'does not match' in log)
    fresh(t); changed = recs(3); changed[1]['n'] = 'renamed'; write_copy(t / 'cache' / 'W-AS.json.gz', changed, mm)
    r, log, kept, aside = gate(t, '--allow-trimmed')
    check('trimmed copy whose records changed after the manifest (same count) = refused (recs_sha256)', r == 7 and aside == ['W-AS.json.gz'] and 'recs_sha256' in log)
    fresh(t); bad = dict(mm); bad.pop('made_by'); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3), bad)
    r, log, kept, aside = gate(t, '--allow-trimmed')
    check('trimmed copy whose manifest lacks a field = refused', r == 7 and aside == ['W-AS.json.gz'] and 'no made_by' in log)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3), dict(mm, area='W-VI'))
    r, log, kept, aside = gate(t, '--allow-trimmed')
    check('a manifest written for another area = refused', r == 7 and aside == ['W-AS.json.gz'])
    fresh(t); write_copy(t / 'cache' / 'W-DE.json.gz', recs(99)); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3), dict(M.make_manifest('W-AS.json.gz', {'recs': recs(3)}, 'x', '2026-11-11', trimmed=False)))
    r, log, kept, aside = gate(t, '--allow-trimmed')
    check('full copies keep the full baseline: 99 of 100 is short; a full copy with a manifest is still checked against 1,711', r == 7 and aside == ['W-AS.json.gz', 'W-DE.json.gz'])

    # a trimmed copy never records or replaces a baseline
    fresh(t); json.dump({'format': 1, 'layers': {}, 'caches': {}}, open(t / 'outlines' / 'layers.json', 'w'))
    write_copy(t / 'cache' / 'W-AS.json.gz', recs(3), mm)
    r, _ = quiet(CLI.main, ['baseline', str(t / 'cache' / 'W-AS.json.gz'), '--root', str(t / 'outlines')])
    check('baseline: a trimmed copy never records a full baseline', r == 1 and json.load(open(t / 'outlines' / 'layers.json'))['caches'] == {})
    why = CLI.save_check(str(t / 'cache' / 'W-AS.json.gz'), str(t), {'W-AS': {'expected_count': 1}}, assets=set(), first_ok=True)
    check('save-check: a bot never uploads a trimmed copy over the release copy', 'trimmed' in why)

    # 3) approved baselines
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    sha_as, sha_au = M.sha256_file(t / 'cache' / 'W-AS.json.gz'), M.sha256_file(t / 'cache' / 'W-AU.json.gz')
    def appr(name, by='KPC owner', date='2026-11-11', **ent):
        d = {'approved_by': by, 'approved_date': date, 'baselines': {'W-AS': dict({'expected_count': 3, 'kind': 'trimmed', 'reason': 'hand bundle', 'copy_sha256': sha_as}, **ent),
                                                                        'W-AU': {'expected_count': 5, 'kind': 'full', 'reason': 'the copy as it is', 'copy_sha256': sha_au}}}
        p = t / name; p.write_text(json.dumps(d)); return str(p)
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.proposed.json'))
    check('the PROPOSED file is never read, even when named: both copies held', r == 7 and aside == ['W-AS.json.gz', 'W-AU.json.gz'] and 'never read' in log)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.approved.json', by=''))
    check('an approved file without approved_by is not read: held', r == 7 and len(aside) == 2 and 'not signed off' in log)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    fut = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.approved.json', date=fut))
    check('an approval dated in the future is not read: held', r == 7 and len(aside) == 2)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.approved.json', by='a bot'))
    check('an approval by a bot (not the owner or a listed person) is not read: held', r == 7 and len(aside) == 2)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.approved.json'))
    check('a signed approved file: both copies pass at their approved counts (3, 5), layers.json untouched', r == 0 and kept == ['W-AS.json.gz', 'W-AU.json.gz']
          and json.load(open(t / 'outlines' / 'layers.json'))['caches']['W-AU'] == {'expected_count': 3743432})
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.approved.json', expected_count=4))
    check('approved count is exact: 3 records against an approved 4 = SHORT', r == 7 and aside == ['W-AS.json.gz'])
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(4)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.approved.json'))
    check('an approval is for one file: a different W-AS copy (other sha256) is refused', r == 7 and aside == ['W-AS.json.gz'] and 'for another copy' in log)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', appr('world-baselines.approved.json', copy_sha256='FILL IN'))
    check('an entry without a real copy_sha256 makes the whole file unread (fail closed)', r == 7 and len(aside) == 2 and 'copy_sha256' in log)
    fresh(t); write_copy(t / 'cache' / 'W-AS.json.gz', recs(3)); write_copy(t / 'cache' / 'W-AU.json.gz', recs(5))
    r, log, kept, aside = gate(t, '--allow-trimmed', '--approved', str(t / 'world-baselines.approved-missing.json'))
    check('no approved file: the layers.json baselines apply (both copies short against 1,711 / 3,743,432)', r == 7 and len(aside) == 2)

# the shipped files
P = json.load(open(ROOT / 'data/outlines/world-baselines.proposed.json', encoding='utf-8'))
want = {'W-AS': 3, 'W-BS': 53, 'W-BW': 9, 'W-BZ': 503, 'W-GL': 63, 'W-NZ': 2837, 'W-UM': 10, 'W-VI': 11, 'W-AU': 365915}
check('the proposed file lists AU and 8 hand bundles at the counts the gate read in run 43082247085, a reason each',
      {k: v['expected_count'] for k, v in P['baselines'].items()} == want and all(len(v['reason']) > 40 for v in P['baselines'].values()))
check('MT is not proposed (its bundle is below the records its key joins)', 'W-MT' not in P['baselines'] and 'W-MT' in P['not_proposed'])
check('the proposed file is unsigned and its sha256 fields are placeholders', not P['approved_by'] and not P['approved_date']
      and M.load_approved_baselines(ROOT / 'data/outlines/world-baselines.proposed.json')[0] == {})
# KPC owner, 2026-11-11: the owner signed data/outlines/world-baselines.approved.json. It must be read in full (signed, every entry valid),
# list only copies it pins by sha256, and never sign MT, AU or the five stale-baseline countries.
_A = list(ROOT.glob('data/**/*baselines.approved.json'))
_ae, _aw = M.load_approved_baselines(ROOT / 'data/outlines/world-baselines.approved.json')
check('the signed approved baselines file is the only one, read in full, and signs only the 8 checked hand bundles',
      [str(x.relative_to(ROOT)) for x in _A] == ['data/outlines/world-baselines.approved.json'] and not _aw
      and set(_ae) == {'W-AS', 'W-BS', 'W-BW', 'W-BZ', 'W-GL', 'W-NZ', 'W-UM', 'W-VI'}
      and all(_ae[k]['expected_count'] == want[k] and _ae[k]['kind'] == 'trimmed' for k in _ae)
      and not {'W-AU', 'W-MT', 'W-BE', 'W-CH', 'W-CZ', 'W-DE', 'W-PT'} & set(_ae))

# ------------------------------------------------------------------ 6) the workflow
import yaml  # noqa: E402
W = yaml.safe_load(open(ROOT / '.github/workflows/kpc-world-key.yml', encoding='utf-8'))
bs = W['jobs']['build']['steps']; js = W['jobs']['join']['steps']
gate_run = next(s for s in bs if s.get('id') == 'kept_green_master')['run']
check('build: the gate reads manifests and the APPROVED baselines file, and keeps its exit code', '--allow-trimmed' in gate_run and '--approved data/outlines/world-baselines.approved.json' in gate_run
      and 'master-gate.rc' in gate_run)
part = next(s for s in bs if s.get('name') == "This job's part")
check("build: the verdict is written into the part, last, before the upload", 'kpc_world_key_join.py verdict --part part' in part['run'] and part['env']['MINE'] == '${{ matrix.g.countries }}')
ups = [s for s in bs if 'upload-artifact' in str(s.get('uses', ''))]
check('build: 3 upload tries, the same artifact name, overwrite on the retries, every one continue-on-error',
      len(ups) == 3 and len({u['with']['name'] for u in ups}) == 1 and ups[0]['with']['name'] == 'world-key-part-${{ matrix.g.i }}'
      and [u['with'].get('overwrite') for u in ups] == [None, True, True] and all(u.get('continue-on-error') is True for u in ups))
check('build: retry 2 only after try 1 failed, retry 3 only after 1 and 2 failed, with waits between',
      "steps.retry_up1.outcome == 'failure'" in ups[1]['if'] and "steps.retry_up2.outcome == 'failure'" in ups[2]['if']
      and sum(1 for s in bs if str(s.get('run', '')).startswith('sleep ')) == 2)
last = next(s for s in bs if 'every try failed' in s.get('name', ''))
check('build: all 3 tries failed = red', all(f"steps.retry_up{i}.outcome == 'failure'" in last['if'] for i in (1, 2, 3)) and 'exit 1' in last['run'])
names = [s.get('name', '') for s in bs]
check('build: verdict in the part -> uploads -> gate verdict step', names.index("This job's part") < names.index(ups[0]['name']) < names.index(last['name'])
      < next(i for i, n in enumerate(names) if n.startswith('Master gate verdict')))
vstep = next(s for s in bs if s.get('name', '').startswith('Master gate verdict'))['run']
with tempfile.TemporaryDirectory() as t:
    def vrun(rc, short):
        for n in ('master-gate.rc', 'master-short.txt'):
            if os.path.exists(os.path.join(t, n)): os.remove(os.path.join(t, n))
        if rc is not None: open(os.path.join(t, 'master-gate.rc'), 'w').write(rc + '\n')
        if short: open(os.path.join(t, 'master-short.txt'), 'w').write(short)
        return subprocess.run(['bash', '-e', '-c', vstep], env=dict(os.environ, RUNNER_TEMP=t), capture_output=True, text=True).returncode
    check('build gate verdict step: green = 0, short = red, NO exit code (gate never ran) = red', vrun('0', '') == 0 and vrun('7', 'W-AU\n') == 1 and vrun(None, '') == 1)
dls = [s for s in js if 'download-artifact' in str(s.get('uses', ''))]
check('join: 3 download tries, each after an empty folder; the last one fails the job', len(dls) == 3 and all(d['with']['pattern'] == 'world-key-part-*' for d in dls)
      and dls[0].get('continue-on-error') and dls[1].get('continue-on-error') and not dls[2].get('continue-on-error')
      and sum(1 for s in js if 'rm -rf parts; sleep' in str(s.get('run', ''))) == 2)
tn = next(s for s in js if s.get('id') == 'tonight')['run']
check('join: the parts are put together with --gate and the held list', 'kpc_world_key_join.py parts/world-key-part-* --gate --held-out /tmp/world-held.txt' in tn)
save = next(s for s in js if s.get('name') == 'Save')
check('join: Save only after a finished join with something built', "steps.tonight.outcome == 'success'" in save['if'] and "steps.tonight.outputs.built != '0'" in save['if'])
jg = next(s for s in js if s.get('name', '').startswith('Master gate verdict of the join'))
check('join: a held country makes the join red (the run ends red)', jg['if'] == 'always()' and '/tmp/world-held.txt' in jg['run'] and 'exit 1' in jg['run'])
pc = W['jobs']['postcheck']['if']
check('postcheck (the "Key check after the key build" commit): only when the join saved a country', "needs.join.outputs.built != '0'" in pc and "needs.join.outputs.built != ''" in pc
      and W['jobs']['join']['outputs']['built'] == '${{ steps.tonight.outputs.built }}')
txt = (ROOT / '.github/workflows/kpc-world-key.yml').read_text(encoding='utf-8')
check('no third-party action in the world workflow', set(re.findall(r'uses:\s*([\w.-]+)/', txt)) <= {'actions'})
import kpc_key_freeze as KF  # noqa: E402
check('the gate / join helpers are not rule files (the world rules hash does not move)', {'kpc_master.py', 'kpc_master_cli.py', 'kpc_world_key_join.py'} <= KF.NOT_RULES
      and not any(x.endswith(('kpc_master.py', 'kpc_master_cli.py', 'kpc_world_key_join.py', '.yml')) for x in KF.RULE_FILES['world-key']))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)

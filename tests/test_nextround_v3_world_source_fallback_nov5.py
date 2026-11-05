"""Next round v3 C11 (Quality's grade of next round v2, Part 5 NO, Nov 5 2026). The DE key build 6d8d79b2 (World build W-41901828387,
5:45 PM CST Nov 4) came back without BfN Naturparke (105) and Nationalparke (16); 42 DE parks silently became pins. v2 took the saved
copy's records for a failed source, but (1) kpc-world-key.yml never had a saved copy on the runner, (2) it matched saved records by
LABEL, and DE has two 'Naturpark' sources (AU two 'Protected areas and forests of Queensland'), (3) a failed source with no saved
records still built the country without it. Now: the build job downloads W-<CC>.json.gz (read only; GEO_CACHE_MODE stays off);
records carry a source id (kind, address, layer) and the fallback matches by it (a pre-v3 saved copy without ids: only a unique
label); a failed source with no saved records HOLDS the country (no file written, previous key kept, logged, exit 3).
Runs the real source-loop block of kpc_world_key.py with stand-in readers (no network); fails on the old code."""
import functools, pathlib, textwrap, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_FILE = ROOT / '.github' / 'scripts' / 'kpc_world_key.py'
WF = ROOT / '.github' / 'workflows' / 'kpc-world-key.yml'
START, END = '    if recs is None:\n        recs, failed = [], False', '\n    if not recs: continue'


def _text(): return SRC_FILE.read_text(encoding='utf-8')


def _block():
    s = _text(); i = s.index(START); j = s.index(END, i)
    return textwrap.dedent(s[i:j])


@functools.lru_cache(maxsize=None)
def _src_id():
    s = _text(); i = s.index('def src_id(s):'); j = s.index('\n\n\n', i)
    ns = {}; exec(s[i:j], ns); return ns['src_id']


NSG = ('BfN Naturschutzgebiete', 'wfs', 'https://geodienste.bfn.de/x', 'NSG')
NP = ('BfN Naturparke', 'wfs', 'https://geodienste.bfn.de/x', 'NaturParke')
NAT = ('BfN Nationalparke', 'wfs', 'https://geodienste.bfn.de/x', 'Nationalparke')
LUBW = ('Naturpark', 'arcgis', 'https://rips-gdi.lubw.baden-wuerttemberg.de/arcgis/rest/services/wfs/Naturpark/MapServer/0')
NDS = ('Naturpark', 'arcgis', 'https://www.umweltkarten-niedersachsen.de/arcgis/rest/services/Natur_wms/MapServer/1')


def _rec(s, n, sid=True, tag=''):
    out = [{'src': s[0], 'n': f'{s[0]} {tag}{i}', 'id': f'{s[0]}-{tag}{i}'} for i in range(n)]
    if sid:
        for r in out: r['sid'] = _src_id()(s)
    return out


def _run(sources, answers, old):
    """answers: source tuple -> records, or an Exception. Returns (recs, saved, notices, held, went_on)."""
    saved, notes, held = [], [], []

    def pull(name, url, *_):
        a = answers[next(s for s in sources if s[0] == name and s[2] == url)]
        if isinstance(a, Exception): raise a
        return [dict(r, sid=None) if 'sid' in r else dict(r) for r in a]   # a fresh read has no id yet
    ns = {'cc': 'DE', 'CMODE': 'refresh', 'recs': None, 'SRC': {'DE': sources}, 'pull_wfs': pull, 'pull_arcgis': pull,
          'pull_find': None, 'pull_a10': None, 'pull_a10n': None, 'pull_chshp': None, 'collections': collections, 'HELD': held,
          'src_id': _src_id(), 'wload': lambda cc: [dict(r) for r in old] if old is not None else None,
          'wsave': lambda cc, r: saved.append(list(r)), 'notice': lambda t, m: notes.append(str(m)), 'print': lambda *a, **k: None}
    code = 'went_on = False\nfor _once in [0]:\n' + textwrap.indent(_block(), '    ') + '\n    went_on = True\n'
    exec(compile(code, 'kpc_world_key.py (source loop)', 'exec'), ns)
    return ns['recs'], saved, notes, held, ns['went_on']


N = 23783   # the other DE areas: 121 lost of ~23,904 is ~0.5%, under the old 3% test


def _by(recs, s): return sum(1 for r in recs if r['src'] == s[0] and r['id'].startswith(s[0]))


def test_failed_and_empty_layer_use_the_saved_copy_and_nothing_is_saved():
    old = _rec(NSG, N) + _rec(NP, 105) + _rec(NAT, 16)
    recs, saved, notes, held, on = _run([NSG, NP, NAT], {NSG: _rec(NSG, N), NP: TimeoutError('read timed out'), NAT: []}, old)
    assert on and not held and _by(recs, NP) == 105 and _by(recs, NAT) == 16 and _by(recs, NSG) == N
    assert saved == [], 'the saved copy is never written when a source failed'
    assert any('BfN Naturparke' in n and 'source id' in n for n in notes)


def test_fresh_records_carry_the_source_id_and_a_good_read_is_saved():
    recs, saved, _, held, on = _run([NSG, NP, NAT], {NSG: _rec(NSG, 300), NP: _rec(NP, 105), NAT: _rec(NAT, 16)}, None)
    assert on and not held and len(saved) == 1 and len(saved[0]) == 421
    sid = _src_id()
    assert all(r['sid'] == sid(NP) for r in recs if r['src'] == NP[0]) and sid(LUBW) != sid(NDS)


def test_two_sources_with_one_label_are_kept_apart():
    # DE 'Naturpark' (LUBW) fails; the saved copy has 20 LUBW and 30 Niedersachsen records under the same label
    old = _rec(NSG, 300) + _rec(LUBW, 20, tag='bw') + _rec(NDS, 30, tag='ni')
    recs, saved, notes, held, on = _run([NSG, LUBW, NDS], {NSG: _rec(NSG, 300), LUBW: OSError('503'), NDS: _rec(NDS, 30, tag='ni')}, old)
    assert on and not held
    assert sum(1 for r in recs if r['src'] == 'Naturpark') == 50, 'LUBW 20 from the saved copy + Niedersachsen 30 fresh, never 30 twice'
    assert sum(1 for r in recs if 'bw' in r['id']) == 20 and saved == []


def test_a_saved_copy_without_ids_uses_a_unique_label_only():
    old = _rec(NSG, 300, sid=False) + _rec(NP, 105, sid=False) + _rec(LUBW, 20, sid=False, tag='bw') + _rec(NDS, 30, sid=False, tag='ni')
    recs, _, _, held, on = _run([NSG, NP, LUBW, NDS], {NSG: _rec(NSG, 300), NP: OSError('503'), LUBW: _rec(LUBW, 20, tag='bw'),
                                                       NDS: _rec(NDS, 30, tag='ni')}, old)
    assert on and not held and _by(recs, NP) == 105, 'a unique label still finds its records in an old saved copy'
    recs, saved, notes, held, on = _run([NSG, NP, LUBW, NDS], {NSG: _rec(NSG, 300), NP: _rec(NP, 105), LUBW: OSError('503'),
                                                               NDS: _rec(NDS, 30, tag='ni')}, old)
    assert held == ['DE'] and not on, 'a shared label in an old saved copy cannot be told apart: the country is held'


def test_a_failed_source_with_no_saved_records_holds_the_country():
    old = _rec(NSG, 300) + _rec(NP, 105)
    recs, saved, notes, held, on = _run([NSG, NP, NAT], {NSG: _rec(NSG, 300), NP: _rec(NP, 105), NAT: OSError('503')}, old)
    assert held == ['DE'] and not on and saved == [], 'no file is written: the previous DE key stays'
    assert any('HELD' in n and 'BfN Nationalparke' in n and 'previous key' in n for n in notes)
    recs, saved, notes, held, on = _run([NSG, NP, NAT], {NSG: _rec(NSG, 300), NP: ValueError('bad'), NAT: _rec(NAT, 16)}, None)
    assert held == ['DE'] and not on and any('no saved copy' in n for n in notes)


def test_an_empty_source_with_saved_records_uses_the_saved_copy():
    """Empty live read, but the saved copy has that source's records: use them, do not hold."""
    old = _rec(NSG, 300) + _rec(NP, 105) + _rec(NAT, 16)
    recs, saved, notes, held, on = _run([NSG, NP, NAT], {NSG: _rec(NSG, 300), NP: _rec(NP, 105), NAT: []}, old)
    assert on and not held and _by(recs, NAT) == 16 and any('returned 0 records' in n for n in notes)


def test_an_empty_source_with_no_saved_records_holds_the_country():
    """Quality v3 Part 5 should-fix: EMPTY (0 records) + no saved copy for that source = HOLD (previous key stays)."""
    old = _rec(NSG, 300) + _rec(NP, 105)   # no NAT in the saved copy
    recs, saved, notes, held, on = _run([NSG, NP, NAT], {NSG: _rec(NSG, 300), NP: _rec(NP, 105), NAT: []}, old)
    assert held == ['DE'] and not on and saved == [], 'empty + no saved NAT records: hold, no file written'
    assert any('HELD' in n and 'BfN Nationalparke' in n for n in notes)
    # no saved copy at all
    recs, saved, notes, held, on = _run([NSG, NP, NAT], {NSG: _rec(NSG, 300), NP: _rec(NP, 105), NAT: []}, None)
    assert held == ['DE'] and not on and any('no saved copy' in n for n in notes)


def test_the_script_exits_3_when_a_country_is_held():
    s = _text(); tail = s[s.rindex('\nif HELD:'):]
    assert 'sys.exit(3)' in tail and 'previous key kept' in tail


def test_the_workflow_downloads_the_saved_copy_before_the_build():
    import yaml
    d = yaml.safe_load(WF.read_text(encoding='utf-8'))
    steps = d['jobs']['build']['steps']; names = [x.get('name', '') for x in steps]
    b = next(i for i, n in enumerate(names) if n.startswith('Build (this job'))
    dl = [x for x in steps[:b] if 'gh release download boundary-cache' in (x.get('run') or '') and 'W-$c.json.gz' in x['run']]
    assert dl and 'cache/world' in dl[0]['run'] and dl[0]['env'].get('GH_TOKEN') == '${{ github.token }}'
    assert 'upload' not in dl[0]['run'] and 'GEO_CACHE_MODE' not in (steps[b].get('env') or {}), 'download only; the build reads live'
    assert d['permissions'] == {'contents': 'write'}, 'no new permission'
    on = d.get(True) or d.get('on'); assert [c['cron'] for c in on['schedule']] == ['17 11 3 * *', '7 10 * * *'], 'no new cron'


def test_key_check_warns_when_outline_to_pin_jumps():
    import sys
    sys.path.insert(0, str(SRC_FILE.parent))
    import kpc_key_postcheck as KP
    de42 = {'outline_to_pin': [f'DE-{i:04d}' for i in range(42)] + ['FR-0001', 'US-0001']}   # W-41901828387: DE 42
    assert KP.pin_jump(de42) == {'DE': 42}
    assert KP.pin_jump({'outline_to_pin': [f'CA-{i:04d}' for i in range(8)]}) == {}             # CA-41739774609: 8, no warning
    assert KP.pin_jump({'outline_to_pin': []}) == {} and KP.PIN_JUMP == 10

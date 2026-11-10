#!/usr/bin/env python3
"""Nov 10: a saved copy the master gate holds is refilled, then gated again; services*.arcgis.com is saved-copy only.

US key run 42821613637 held AZ CT DE FL ID MT NC NH NJ NM UT: their boundary-cache copies (Nov 3 to Nov 5) lacked the
saved PAD-US ids loaded by id, newer state layers, and (FL) most of a page-capped layer. Only the build's own top-up
fills that in, and a held state was never built, so it was held on every run. This test does not import kpc_us_key
(that would run the builder): it execs one helper and reads the source and the workflow.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


# 1. saved_only: every services*.arcgis.com host, plus the listed hosts
start = src.index('SAVED_ONLY_HOSTS = ')
end = src.index('def notice(')
ns = {'os': __import__('os'), 're': re, 'urllib': __import__('urllib.parse')}
exec(compile(src[start:end], 'kpc_us_key.py', 'exec'), ns)
so = ns['saved_only']
for h in ['services', 'services1', 'services2', 'services3', 'services5', 'services6', 'services7', 'services8', 'services9', 'services12']:
    check(f'{h}.arcgis.com is saved-copy only', so(f'https://{h}.arcgis.com/abc/arcgis/rest/services/x/FeatureServer/0/query'))
check('svc: form on services3 is saved-copy only', so('svc:https://services3.arcgis.com/x/arcgis/rest/services/y/FeatureServer|.'))
check('apps.fs.usda.gov stays saved-copy only', so('https://apps.fs.usda.gov/arcx/rest/services/x/MapServer/0/query'))
for u in ['https://ca.dep.state.fl.us/arcgis/rest/services/OpenData/STATE_OWNED_LANDS/MapServer/0/query',
          'https://gis.blm.gov/azarcgis/rest/services/recreation/BLM_AZ_RECS/MapServer/1/query',
          'https://edits.nationalmap.gov/arcgis/rest/services/PAD-US/PAD_US/MapServer/0/query',
          'https://nhgeodata.unh.edu/nhgeodata/rest/services/EC/Conservation/MapServer/0/query']:
    check('allowed host still read live: ' + u.split('/')[2], not so(u))

# 2. refill-only mode: tops up and re-saves, writes no key file
check('KPC_REFILL_ONLY needs GEO_CACHE_MODE=use', "REFILL_ONLY = os.environ.get('KPC_REFILL_ONLY') == '1' and CMODE == 'use'" in src)
i_ref = src.index('        if REFILL_ONLY:\n            notice(f\'US key {st}\', f\'refill: saved copy now')
i_top = src.index("if st not in FAILED_READ: save_cache(st, recs, seen)\n    else:".replace('\n    else:', ''))
i_match = src.index('    recs = prefer_state_layer(st, recs, P)')
check('refill returns after the saved-copy top-up and before any matching', i_top < i_ref < i_match)
i_exit = src.index("if REFILL_ONLY:\n    for st in STATES:")
i_loop = src.index("done = []\nSTATE_S = {}\nfor st in STATES:")
check('refill run exits before the build loop (no index or key file written)', i_exit < i_loop and 'sys.exit(0)' in src[i_exit:i_loop])
check('no saved copy = nothing refilled (no fresh full read)', "refill: no saved copy to refill; skipped'); return None" in src)

# 3. workflow: gate, refill the held copies, the SAME gate again, then drop what is still short
g1 = wf.index('python3 .github/scripts/kpc_master_cli.py gate --cache cache/us --report "$RUNNER_TEMP/master-short.txt"')
rf = wf.index('KPC_REFILL_ONLY=1 python3 .github/scripts/kpc_us_key.py')
g2 = wf.index('python3 .github/scripts/kpc_master_cli.py gate --cache cache/us --report "$RUNNER_TEMP/master-short.txt"', rf)
drop = wf.index('for st in $STATES; do [ -f "cache/us/short/US-$st.json.gz" ] || ok="$ok $st"; done; export STATES', g2)
build = wf.index('python3 .github/scripts/kpc_us_key.py 2>&1 | tee us-key-${{ matrix.g.i }}.log', drop)
check('order: gate -> refill -> gate again -> drop still-short states -> build', g1 < rf < g2 < drop < build)
check('second gate failing to run stops the job (fail closed)', 'second gate stopped (exit $mg)' in wf)
check('the gate script is not bypassed: no --no-gate / skip flag', '--skip' not in wf[g1:build] and 'KPC_MASTER_GATE' not in wf[g1:build])
# 4. the stamp names a held state as failed
st = wf.index("for f in parts/us-key-part-*/master-short.txt; do")
stamp = wf.index('python3 .github/scripts/kpc_key_freeze.py stamp us-key')
check('master-gate held states go into the failed list before the stamp', st < stamp and "sed 's/^US-//' \"$f\" >> /tmp/kpc-build-failed.txt" in wf[st:stamp])

# 5. the gate and its baselines are untouched by this change
cli = (ROOT / '.github/scripts/kpc_master_cli.py').read_text(encoding='utf-8')
check('gate still holds a copy with no baseline', "no baseline in the manifest (caches): held, not used" in cli and 'return 7 if short else 0' in cli)

# 6. run the workflow's gate + refill + gate lines in a scratch folder with a stand-in refill
import gzip, json, os, shutil, subprocess, tempfile
try:
    import yaml
    d = yaml.safe_load(wf)
    run = [s_['run'] for s_ in d['jobs']['build']['steps'] if s_.get('name', '').startswith('Build the answer key')][0]
    snip = run[run.index('# Nov 10 (master outlines'):run.index('python3 .github/scripts/kpc_us_key.py 2>&1 | tee us-key-')].replace('${{ matrix.g.i }}', '0')
    FAKE = ("import gzip, json, os\n"
            "assert os.environ.get('KPC_REFILL_ONLY') == '1'\n"
            "n = int(os.environ.get('FAKE_REFILL_TO') or 0)\n"
            "for st in os.environ['STATES'].split():\n"
            "    json.dump({'seen': 1, 'recs': [{}] * n}, gzip.open(f'cache/us/US-{st}.json.gz', 'wt'))\n")
    for fill, want_states, want_short in ((21993, 'FL TN KY', []), (21992, 'TN KY', ['US-FL'])):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t); (t / 'cache/us').mkdir(parents=True); (t / '.github/scripts').mkdir(parents=True); (t / 'data/outlines').mkdir(parents=True)
            for fn in ('kpc_master.py', 'kpc_master_cli.py'): shutil.copy(ROOT / '.github/scripts' / fn, t / '.github/scripts' / fn)
            (t / '.github/scripts/kpc_us_key.py').write_text(FAKE)
            json.dump({'format': 1, 'layers': {}, 'caches': {'US-FL': {'expected_count': 21993}, 'US-TN': {'expected_count': 100}, 'US-KY': {'expected_count': 5}}}, open(t / 'data/outlines/layers.json', 'w'))
            for st, nrecs in (('FL', 5198), ('TN', 100), ('KY', 5)):
                with gzip.open(t / f'cache/us/US-{st}.json.gz', 'wt') as fh: json.dump({'seen': 1, 'recs': [{}] * nrecs}, fh)
            r = subprocess.run(['bash', '-e', '-c', 'set -o pipefail\nSTATES="FL TN KY"\n' + snip + '\necho "STATES NOW: $STATES"'], cwd=t, capture_output=True, text=True,
                               env=dict(os.environ, RUNNER_TEMP=str(t), GEO_CACHE_MODE='use', FAKE_REFILL_TO=str(fill)))
            ms = (t / 'master-short.txt').read_text().split() if (t / 'master-short.txt').exists() else []
            check(f'refill to {fill} of 21993: builds {want_states}; held {want_short or "none"} (got rc {r.returncode}, {r.stdout.strip().splitlines()[-1:]}, {ms}, {r.stderr.strip()[-200:]})',
                  r.returncode == 0 and f'STATES NOW: {want_states}' in r.stdout and ms == want_short)
            check(f'refill to {fill}: a still-short copy is set aside again, a full one stays in place', (t / 'cache/us/short/US-FL.json.gz').exists() == bool(want_short))
except ImportError:
    print('SKIP yaml not installed')

# 7. Canada and world keys: the same services*.arcgis.com rule
for fn, a, b in (('kpc_ca_key.py', 'SAVED_ONLY_HOSTS = ', 'def get('), ('kpc_world_key.py', 'SAVED_ONLY_HOSTS = ', 'def fetch_bytes(')):
    s2 = (ROOT / '.github/scripts' / fn).read_text(encoding='utf-8')
    ns2 = {'os': __import__('os'), 're': re, 'urllib': __import__('urllib.parse')}
    exec(compile(s2[s2.index(a):s2.index(b)], fn, 'exec'), ns2)
    so2 = ns2['saved_only']
    check(f'{fn}: services2 / services7 / services9 .arcgis.com are saved-copy only', all(so2(f'https://services{n}.arcgis.com/x/arcgis/rest/services/y/FeatureServer/0') for n in ('', '1', '2', '7', '9')))
    check(f'{fn}: a provincial / national host is still read live', not so2('https://maps.gov.bc.ca/arcgis/rest/services/x/MapServer/5') and not so2('https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/'))
ca = (ROOT / '.github/scripts/kpc_ca_key.py').read_text(encoding='utf-8')
check('Canada: the GeoJSON and zipped-shapefile pulls ask saved_only first', ca.count("if saved_only(url): raise RuntimeError(f'saved copy only:") == 2 and 'if saved_only(url): raise RuntimeError' in ca[ca.index('def get('):ca.index('def get(') + 200])
wk = (ROOT / '.github/scripts/kpc_world_key.py').read_text(encoding='utf-8')
check('world: fetch_bytes asks saved_only first', 'if saved_only(u): raise LayerStall(' in wk[wk.index('def fetch_bytes('):wk.index('def fetch_bytes(') + 600])
# 8. a smaller re-read never replaces a saved layer
g = src[src.index('            if missing or short:'):src.index('        if REFILL_ONLY:\n            notice(')]
check('a short layer keeps its saved records when the re-read has fewer', 'if n_new < len(old_l):' in g and 'recs += old_l' in g and g.index('kept_old = {pre:') < g.index('add = extra_state(') < g.index('if n_new < len(old_l):'))
check('resolve() and the zipped-shapefile layers ask saved_only too', "def rq(u):\n        if saved_only(u): raise RuntimeError" in src and "if saved_only(url): SAVED_ONLY_SKIPPED.setdefault(st, set()).add(pre); continue" in src)

if __name__ == '__main__':
    sys.exit(0 if ok else 1)

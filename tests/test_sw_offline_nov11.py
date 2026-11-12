"""Nov 11 (site review S): service worker + offline packers, no browser and no network.
 - the two cache names are unchanged everywhere and nothing deletes them
 - every file the packers (kpc-offline.js, kpc-kit.js, kpc-logger.js) name exists in the tree (a name that does not exist is a 404 on every save)
 - all four pages' scripts register the same worker address with no scope option
 - the logger: imported call sign is escaped, an unreadable saved log is copied aside first
 - runs tests/sw_sim_nov11.js (the worker in a fake worker) when node is installed
Prints PASS / FAIL lines."""
import os, re, subprocess, shutil, sys
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
bad = 0
def ok(c, m):
    global bad
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: bad += 1
rd = lambda f: open(os.path.join(R, f), encoding='utf8').read()
sw, off, trip, kit, lg = (rd(f) for f in ['kpc-finder-sw.js', 'kpc-offline.js', 'kpc-trip-offline.js', 'kpc-kit.js', 'kpc-logger.js'])
for name, src in [('kpc-finder-sw.js', sw), ('kpc-offline.js', off), ('kpc-trip-offline.js', trip), ('kpc-kit.js', kit), ('kpc-logger.js', lg)]:
    ok("kpc-finder-v1" in src and "kpc-tiles-v1" in src, f'{name} uses the cache names kpc-finder-v1 and kpc-tiles-v1')
    ok(not re.search(r"kpc-(finder|tiles)-v[02-9]", src), f'{name} has no renamed cache name')
ok("k !== APP && k !== TILES" in sw, 'the worker only ever deletes caches other than the two named ones')
ok(not re.search(r"caches\.delete\((?!APP\)|TILES\)|k\))", sw), 'the worker has no other cache delete')
regs = {n: re.findall(r"serviceWorker\.register\(([^)]*)\)", s) for n, s in [('kpc-offline.js', off), ('kpc-trip-offline.js', trip), ('kpc-kit.js', kit), ('kpc-logger.js', lg)]}
ok(all(v == ["'kpc-finder-sw.js'"] for v in regs.values()), f'all four register exactly kpc-finder-sw.js with no scope option: {regs}')
ok('addAll' not in sw and "'install'" in sw, 'the worker has no precache list (nothing can fail the install with one 404)')
# packer lists
m = re.search(r"const FILES = \[(.*?)\];", off, re.S)
files = re.findall(r"'([^']+)'", m.group(1))
miss = [f for f in files if not os.path.isfile(os.path.join(R, f))]
ok(len(files) > 20 and not miss, f'kpc-offline.js FILES: {len(files)} names, missing: {miss}')
m = re.search(r"const files = \[(.*?)\]\.concat", kit, re.S)
kf = re.findall(r"'([^']+)'", m.group(1))
miss = [f for f in kf if not os.path.isfile(os.path.join(R, f))]
ok(len(kf) > 8 and not miss, f'kpc-kit.js save list: {len(kf)} names, missing: {miss}')
m = re.search(r"const urls = new Set\(\[(.*?)\]\);", lg, re.S)
lf = [u.split('?')[0] for u in re.findall(r"'([^']+)'", m.group(1)) if not u.startswith('http')]
miss = [f for f in lf if not os.path.isfile(os.path.join(R, f))]
ok(len(lf) > 8 and not miss, f'kpc-logger.js save list: {len(lf)} same-site names, missing: {miss}')
ok("'data/parkinfo/index.json'" not in m.group(1), 'the logger save list does not name data/parkinfo/index.json on this site (it lives on KPC-Data and 404s here)')
# logger
ok("<b>${esc(q.call)}</b>: <b>OK</b>" in lg and "<b>${q.call}</b>" not in lg, 'logger: the call sign in the QRZ answer line is escaped (an imported ADIF CALL can hold HTML)')
ok("'Bad-' + raw.length" in lg, 'logger: a saved log that cannot be read is copied aside before the empty one is started')
# packers keep released ?v=
ok("REL.test(k.pathname)" in trip and "REL.test(k.pathname)" in kit, 'kit and trip planner save a released file under its own ?v=')
# node worker test
if shutil.which('node'):
    r = subprocess.run(['node', os.path.join(R, 'tests', 'sw_sim_nov11.js')], capture_output=True, text=True, cwd=R)
    for line in r.stdout.splitlines():
        if line.startswith('FAIL'): ok(False, 'worker: ' + line[5:])
    ok(r.returncode == 0 and 'ALL PASSED' in r.stdout, f'worker in a fake worker: {sum(l.startswith("PASS") for l in r.stdout.splitlines())} checks passed')
else:
    print('SKIP: node is not installed, worker simulation not run')
print('SOME FAILED' if bad else 'ALL PASSED')
sys.exit(1 if bad else 0)

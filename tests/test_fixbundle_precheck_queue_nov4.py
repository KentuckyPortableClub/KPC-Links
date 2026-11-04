"""Nov 4 PM fix bundle item 11b: the queued pre-check re-run for the German rebuild (ddd815b34 counts: at or after) (no cron; kept by the key check).
Run: python3 -B tests/test_fixbundle_precheck_queue_nov4.py   (makes a throw-away git repo in a temp folder)"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile
R = pathlib.Path(__file__).resolve().parents[1]; S = R / '.github/scripts/kpc_precheck_queue.py'
ok = True
def check(what, got, want):
    global ok
    good = got == want; ok &= good
    print(('PASS ' if good else 'FAIL ') + f'{what}: got {got!r}' + ('' if good else f', want {want!r}'))
q0 = json.load(open(R / 'data/status/key-check/precheck-queue.json'))
e0 = q0['queue'][0]
check('the queue has the German entry, waiting, due AT OR AFTER the DE build on main (ddd815b34 counts)', (e0['id'], e0['area'], e0['key_file'], e0['state'], e0.get('from_commit'), 'after_commit' in e0),
      ('de-after-german-rebuild', 'DE', 'data/world-key/DE.json', 'waiting', 'ddd815b34', False))
wf = open(R / '.github/workflows/kpc-key-postcheck.yml').read()
check('the key check runs the queue step after the pre-check, before the save', wf.index('Pre-check (REVIEW_PILE') < wf.index('kpc_precheck_queue.py') < wf.index('Save the report'), True)
check('the key check still has no schedule', re.search(r'^\s*schedule:', wf, re.M) is None, True)
td = tempfile.mkdtemp(prefix='fbq_')
try:
    g = lambda *a: subprocess.run(['git', '-C', td, '-c', 'user.name=t', '-c', 'user.email=t@t', *a], capture_output=True, text=True, check=True).stdout.strip()
    g('init', '-q'); os.makedirs(f'{td}/data/world-key'); os.makedirs(f'{td}/data/status/key-check')
    open(f'{td}/data/world-key/DE.json', 'w').write('{"v": 1}'); g('add', '-A'); g('commit', '-qm', 'old DE build'); old = g('rev-parse', 'HEAD')
    e = {k: v for k, v in e0.items() if k != 'from_commit'}; e['after_commit'] = old; json.dump({'queue': [e]}, open(f'{td}/data/status/key-check/precheck-queue.json', 'w'))
    pre = f'{td}/pre'; os.makedirs(pre)
    run = lambda: subprocess.run([sys.executable, '-B', str(S)], cwd=td, env=dict(os.environ, PRECHECK_OUT=pre), capture_output=True, text=True)
    st = lambda: json.load(open(f'{td}/data/status/key-check/precheck-queue.json'))['queue'][0]
    p = run(); check('no rebuild yet: still waiting, exit 0', (st()['state'], p.returncode), ('waiting', 0))
    open(f'{td}/data/world-key/AT.json', 'w').write('{}'); g('add', '-A'); g('commit', '-qm', 'AT only')
    run(); check('another country rebuilt: still waiting', st()['state'], 'waiting')
    open(f'{td}/data/world-key/DE.json', 'w').write('{"v": 2}'); g('add', '-A'); g('commit', '-qm', 'new DE build'); new = g('rev-parse', 'HEAD')
    p = run(); check('DE rebuilt but the pre-check did not finish (no counts.json): waits, with the reason', (st()['state'], 'did not finish' in st().get('last_try', ''), p.returncode), ('waiting', True, 0))
    json.dump({'status': 'red'}, open(f'{pre}/counts.json', 'w')); run()
    check('a red pre-check: still waiting', (st()['state'], 'red' in st()['last_try']), ('waiting', True))
    json.dump({'status': 'green', 'pile': 700}, open(f'{pre}/counts.json', 'w'))
    open(f'{pre}/review-pile.csv', 'w').write('park,area,name\nDE-0095,DE,x\nAT-0001,AT,y\nDE-0001,DE,z\n')
    open(f'{pre}/BAD_POTA_PIN_FLAGS.csv', 'w').write('park,area,flag\nUS-1,US-KY,f\n')
    p = run(); s = st(); d = pathlib.Path(td) / 'data/status/key-check/precheck-queue/de-after-german-rebuild'
    check('DE rebuilt + a finished pre-check: DONE with the build commit and the DE rows kept',
          (s['state'], s['build_commit'], s['kept'], sorted(x.name for x in d.iterdir())),
          ('done', new[:12], {'review-pile.csv': 2, 'BAD_POTA_PIN_FLAGS.csv': 0}, ['BAD_POTA_PIN_FLAGS-DE.csv', 'counts.json', 'review-pile-DE.csv']))
    before = open(f'{td}/data/status/key-check/precheck-queue.json').read(); run()
    check('a done entry is never redone (the file does not change)', open(f'{td}/data/status/key-check/precheck-queue.json').read(), before)
    # from_commit (Brandon 5:36 PM CST relayed): the named build itself counts; the queue is due without any new build
    open(f'{td}/data/world-key/DE.json', 'w').write('{"v": 3}'); g('add', '-A'); g('commit', '-qm', 'the counted DE build'); counted = g('rev-parse', 'HEAD')
    open(f'{td}/data/world-key/AT.json', 'w').write('{"v": 2}'); g('add', '-A'); g('commit', '-qm', 'AT after it')
    shutil.rmtree(d.parent, ignore_errors=True)
    json.dump({'queue': [dict(e0, from_commit=counted[:9])]}, open(f'{td}/data/status/key-check/precheck-queue.json', 'w'))
    p = run(); s = st()
    check('from_commit = the last DE build itself: DONE on the next key check, no new build needed', (s['state'], s.get('build_commit'), p.returncode), ('done', counted[:12], 0))
    json.dump({'queue': [dict(e0, from_commit=new[:9])]}, open(f'{td}/data/status/key-check/precheck-queue.json', 'w')); run()
    check('from_commit older than the last DE build: DONE too (at OR after)', st()['state'], 'done')
    open(f'{td}/data/world-key/DE.json', 'w').write('{"v": 4}'); g('add', '-A'); g('commit', '-qm', 'later DE'); later = g('rev-parse', 'HEAD')
    g('checkout', '-q', counted)
    json.dump({'queue': [dict(e0, from_commit=later[:9])]}, open(f'{td}/data/status/key-check/precheck-queue.json', 'w')); run()
    check('from_commit newer than the checked-out DE build: still waiting', st()['state'], 'waiting')
finally:
    shutil.rmtree(td, ignore_errors=True)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)

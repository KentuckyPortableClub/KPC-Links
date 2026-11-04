#!/usr/bin/env python3
"""Offline test for the Nov 4 key freeze (links-04; Brandon 4:51 AM CST Nov 4, relayed via Super Head Bot; FINAL-v2 after Quality's grade, Nov 4 5:30 AM CST): .github/scripts/kpc_key_freeze.py
and the plan steps of kpc-us-key.yml / kpc-ca-key.yml / kpc-world-key.yml. No network, no gh: gh_json is replaced by a dict.
The stamps used are the real ones on main on Nov 4 (KPC-Links data/<kind>/index.json and KPC-Data's waiting room)."""
import datetime, importlib.util, json, os, pathlib, re, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
TOOL = HERE / '.github/scripts/kpc_key_freeze.py'
spec = importlib.util.spec_from_file_location('kpc_key_freeze', TOOL); KF = importlib.util.module_from_spec(spec); spec.loader.exec_module(KF)
ok = True
BASE = next((r for r in ('origin/main', 'main') if subprocess.run(['git', 'rev-parse', '-q', '--verify', r], cwd=HERE, capture_output=True).returncode == 0), 'main')   # in an apply-check clone 'main' has the patches


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


NOW = datetime.datetime(2026, 11, 4, 11, 0, tzinfo=datetime.timezone.utc)
# the real stamps (Nov 4 main)
LIVE = {'us-key': {'build': 'US-41695918852', 'built': '2026-11-03 19:40 UTC'}, 'ca-key': {'build': 'CA-41739774609', 'built': '2026-11-03 23:49 UTC'}, 'world-key': {}}
HELD = {'us-key': {'build': 'US-f3d48d30899'}, 'ca-key': {'build': 'CA-41513281651'}, 'world-key': {'build': 'W-f54cce915b8'}}
APPROVED = {'items': [{'what': 'ca-key', 'build': 'CA-41513281651', 'chat11': 'WITHDRAWN'}]}


def run(kind, live, held=None, approved=None, used=None, force='', verdict_file=None, max_days=None):
    with tempfile.TemporaryDirectory() as t:
        cwd = os.getcwd(); os.chdir(t)
        try:
            os.makedirs(f'data/{kind}', exist_ok=True); json.dump(live or {}, open(f'data/{kind}/index.json', 'w'))
            if verdict_file:
                os.makedirs('data/status/key-check/verdicts', exist_ok=True); json.dump(verdict_file, open(f"data/status/key-check/verdicts/{verdict_file['build']}.json", 'w'))
            env = pathlib.Path(t) / 'env'; env.write_text('')
            os.environ['GITHUB_ENV'] = str(env); os.environ['FORCE'] = force
            os.environ.pop('KPC_FREEZE_MAX_DAYS', None)
            if max_days is not None: os.environ['KPC_FREEZE_MAX_DAYS'] = str(max_days)
            G = {f'data/waiting/in/data/{kind}/index.json': held, 'data/waiting/approved.json': approved or {'items': []}, 'data/waiting/approved-used.json': used or {}}
            KF.gh_json = lambda p: G.get(p)
            res = KF.check(kind, NOW)
            return res, env.read_text()
        finally: os.chdir(cwd)


R = {k: KF.rules_hash(k) for k in KF.RULE_FILES}
fresh = lambda b, **kw: dict({'build': b, 'built': '2026-11-04 09:40 UTC', 'rules': R[b.split('-')[0] and {'US': 'us-key', 'CA': 'ca-key', 'W': 'world-key'}[b.split('-')[0]]]}, **kw)

# --- before / after on the real stamps
for kind in ('us-key', 'ca-key', 'world-key'):
    (fz, bid, why), env = run(kind, LIVE[kind], HELD[kind], APPROVED)
    check(not fz and 'RULES_CHANGED=1' in env and 'FROZEN=1' not in env, f'{kind}: the Nov 4 held builds ({LIVE[kind].get("build") or "none"} / {HELD[kind]["build"]}) have no rules hash: superseded, not frozen, RULES_CHANGED=1 (the next run builds the whole key, no force)')

# --- a build on the current rules
(fz, bid, why), env = run('us-key', fresh('US-1001'))
check(fz and bid == 'US-1001' and 'FROZEN=1' in env and 'RULES_CHANGED' not in env, 'current rules, fresh, no verdict: FROZEN (Quality grades it first)')
D = '2026-11-04 10:00 UTC'
vf = lambda **kw: dict({'build': 'US-1001', 'verdict': 'YES', 'by': 'Brandon', 'date': D}, **kw)
(fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf(verdict='PASS', by='Quality'))
check(fz, 'FINAL-v2: a Quality verdict file does NOT unfreeze (a Quality note is a report, not a person\'s sign-off)')
(fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf())
check(not fz, 'a Brandon sign-off (verdict file, dated after the restart) unfreezes')
(fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf(by='KZ4CP'))
check(not fz, 'a KZ4CP sign-off unfreezes')
(fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf(verdict='NO'))
check(not fz, 'a Brandon NO unfreezes too: the next build fixes it')
for by in ('key bot', 'Brandon via Super Head Bot', 'not Brandon', 'Quality for Brandon', 'Mapping', 'chat 11', ''):
    (fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf(by=by))
    check(fz, f'by {by!r}: not a person\'s sign-off, still FROZEN')
for d, why in (('2026-11-02 15:36 UTC', 'one minute before the restart (9:36 AM CST Nov 2)'), ('2026-11-02 09:00 CST', '9:00 AM CST Nov 2'),
               ('2026-11-02', 'a bare Nov 2 date (cannot be after 9:37 AM)'), ('2026-11-01T22:00:00-06:00', 'Nov 1 (ISO)'),
               ('', 'no date'), ('yesterday', 'an unreadable date'), ('2026-12-25 10:00 UTC', 'a future date')):
    (fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf(date=d))
    check(fz, f'a Brandon YES dated {why} does not count')
for d in ('2026-11-02 15:37 UTC', '2026-11-02 09:37 CST', '2026-11-03', '2026-11-04T04:10:00-06:00'):
    (fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf(date=d))
    check(not fz, f'a Brandon YES dated {d} (at or after the restart) counts')
(fz, *_), env = run('us-key', fresh('US-1001'), verdict_file=vf(build='US-9999'))
check(fz, 'a sign-off for another build does not count')
(fz, *_), env = run('us-key', fresh('US-1001'), approved={'items': [{'what': 'us-key', 'build': 'US-1001', 'verdict': 'KEY YES', 'by': 'Brandon', 'date': D}]})
check(not fz, 'an approved.json item what=us-key build=US-1001 by Brandon, dated after the restart, unfreezes (Links build, nothing held to release)')
(fz, *_), env = run('us-key', fresh('US-1001'), approved={'items': [{'what': 'us-key', 'build': 'US-1001', 'verdict': 'KEY YES', 'by': 'Brandon'}]})
check(fz, 'the same approved.json item with no date does not count')
(fz, *_), env = run('us-key', fresh('US-1001'), approved={'items': [{'what': 'us-key', 'build': 'US-1001', 'verdict': 'KEY YES', 'by': 'some bot', 'date': D}]})
check(fz, 'an approved.json verdict by a bot does not count')
(fz, *_), env = run('us-key', fresh('US-1001'), approved={'items': [{'what': 'us-key', 'build': 'US-1001', 'chat11': 'KEY YES', 'approved_date': D}]})
check(fz, 'old chat 11 text (a chat11 YES) never counts')
(fz, *_), env = run('us-key', {}, fresh('US-1002'), approved={'items': [{'what': 'us-key', 'build': 'US-1002', 'verdict': 'YES', 'by': 'Brandon', 'date': D}]})
check(fz, 'a held KPC-Data build signed YES and not yet released: still FROZEN until its release (Brandon Nov 2)')
(fz, *_), env = run('us-key', {}, fresh('US-1002'), approved={'items': [{'what': 'us-key', 'build': 'US-1002', 'verdict': 'YES', 'by': 'Brandon', 'date': D}]},
                    used={'{"what": "us-key", "build": "US-1002"}': 1})
check(not fz, '... and free once approved-used.json shows it released')
# graded_no: a hold signal for 2-fers only (Quality and old chat 11 NO still hold; never an unfreeze)
check(KF.graded_no('ca-key', 'CA-41513281651', APPROVED['items']) == ('WITHDRAWN', 'chat 11 (old)'), 'graded_no: the old chat 11 WITHDRAWN still HOLDS 2-fers on CA-41513281651')
check(KF.graded_no('us-key', 'US-1', [{'what': 'us-key', 'build': 'US-1', 'verdict': 'NO', 'by': 'Quality'}]) is not None, 'graded_no: a Quality NO holds 2-fers')
check(KF.graded_no('us-key', 'US-1', [{'what': 'us-key', 'build': 'US-1', 'verdict': 'YES', 'by': 'Quality'}]) is None and KF.verdict('us-key', 'US-1', [{'what': 'us-key', 'build': 'US-1', 'verdict': 'YES', 'by': 'Quality', 'date': D}]) is None,
      'a Quality YES is neither a NO nor a sign-off')
check(KF.graded_no('us-key', 'US-1', [{'what': 'us-key', 'build': 'US-1', 'verdict': 'NO', 'by': 'a bot'}]) is None, 'graded_no: a bot NO is ignored')
check(KF.graded_no('us-key', 'US-1', [{'what': 'us-key', 'build': 'US-1', 'verdict': 'NOT SURE', 'by': 'Brandon'}]) is None, "graded_no: 'NOT SURE' is not NO")
os.environ['KPC_PERSONS'] = 'Brandon,KZ4CP,Quality'
check(KF.verdict('us-key', 'US-1', [{'what': 'us-key', 'build': 'US-1', 'verdict': 'YES', 'by': 'Quality', 'date': D}]) is None, 'KPC_PERSONS cannot make Quality a person')
os.environ.pop('KPC_PERSONS')

# --- N days
check(KF.not_blocking({'build': 'US-1', 'rules': R['us-key'], 'built': 'not a date'}, 'us-key', NOW, R['us-key']).startswith('its build date cannot be read'), 'FINAL-v2 should-fix: an unreadable build date counts as expired (never blocks)')
check(KF.not_blocking({'build': 'US-1', 'rules': R['us-key']}, 'us-key', NOW, R['us-key']) != '', 'FINAL-v2 should-fix: a missing build date counts as expired too')
(fz, *_), env = run('us-key', fresh('US-1007', built='3 Nov'))
check(not fz, 'a held build whose date cannot be read does not freeze')
old = fresh('US-1003', built='2026-11-01 09:40 UTC')
(fz, *_), env = run('us-key', old)
check(not fz, 'a held build older than 3 days (KPC_FREEZE_MAX_DAYS default) never blocks')
(fz, *_), env = run('us-key', old, max_days=10)
check(fz, 'KPC_FREEZE_MAX_DAYS=10: the same build blocks again (the N is a setting)')
(fz, *_), env = run('us-key', fresh('US-1004', built='2026-11-01 12:00 UTC'))
check(fz, 'a build 2 days 23 h old still blocks (inside N)')

# --- rules change
(fz, *_), env = run('us-key', fresh('US-1005', rules='0123456789ab'))
check(not fz and 'RULES_CHANGED=1' in env, 'a held build on other rules never blocks, and RULES_CHANGED=1')
(fz, *_), env = run('us-key', fresh('US-1006'), force='yes')
check(not fz and 'FROZEN=1' not in env, 'force=yes by hand still skips the freeze')

# --- rules hash
with tempfile.TemporaryDirectory() as t:
    root = pathlib.Path(t)
    for rel in set(sum(KF.RULE_FILES.values(), [])) | {KF.VERSION_FILE, '.github/scripts/kpc_host_pace.py'}:
        (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_bytes((HERE / rel).read_bytes() if (HERE / rel).exists() else b'x')
    h0 = KF.rules_hash('us-key', root)
    (root / '.github/scripts/kpc_host_pace.py').write_text('changed')
    check(KF.rules_hash('us-key', root) == h0, 'a change to kpc_host_pace.py (pacing, not a rule) does not change the rules hash')
    (root / '.github/scripts/kpc_us_key.py').write_text((root / '.github/scripts/kpc_us_key.py').read_text() + '\n# rule change\n')
    h1 = KF.rules_hash('us-key', root)
    check(h1 != h0, 'a change to kpc_us_key.py changes the US rules hash')
    v = json.load(open(root / KF.VERSION_FILE)); v['us-key'] = 'v6'; json.dump(v, open(root / KF.VERSION_FILE, 'w'))
    check(KF.rules_hash('us-key', root) != h1, 'a person bumping .github/key-rules-version.json changes the hash (no code change needed)')
check(all((HERE / f).is_file() for f in sum(KF.RULE_FILES.values(), [])) and (HERE / KF.VERSION_FILE).is_file(), 'every rule file and the version file exist')
for kind, wf in (('us-key', 'kpc-us-key.yml'), ('ca-key', 'kpc-ca-key.yml'), ('world-key', 'kpc-world-key.yml')):
    used_s = set(re.findall(r'\.github/scripts/(kpc_[a-z0-9_]+\.(?:py|sh))', (HERE / '.github/workflows' / wf).read_text()))
    rules = {os.path.basename(f) for f in KF.RULE_FILES[kind]}
    imp = set()
    for f in KF.RULE_FILES[kind]:
        imp |= {m + '.py' for m in re.findall(r'^\s*(?:import|from)\s+(kpc_[a-z0-9_]+)', (HERE / f).read_text(), re.M)}
    left = (used_s | imp) - rules - KF.NOT_RULES
    check(not left, f'{wf}: every script it runs (and every kpc_ module the rule files import) is a rule file or listed as not a rule ({sorted(left) or "none left"})')

# --- stamp
with tempfile.TemporaryDirectory() as t:
    cwd = os.getcwd(); os.chdir(t)
    try:
        os.makedirs('data/us-key'); json.dump({'build': 'US-1', 'rules': 'oldoldoldold'}, open('data/us-key/index.json', 'w'))
        os.environ['GITHUB_RUN_ID'] = '777'; os.environ.pop('KPC_BUILD_FAILED_FILE', None); os.environ.pop('KPC_FULL_BUILD', None)
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()): KF.stamp('us-key')
        d = json.load(open('data/us-key/index.json'))
        check(d['build'] == 'US-777' and d['rules'] == 'oldoldoldold', 'a partial build (no KPC_FULL_BUILD) keeps the OLD rules hash (states not rebuilt stay on old rules)')
        os.environ['KPC_FULL_BUILD'] = '1'; open('failed.txt', 'w').write('TX\n'); os.environ['KPC_BUILD_FAILED_FILE'] = 'failed.txt'
        with contextlib.redirect_stdout(io.StringIO()): KF.stamp('us-key')
        d = json.load(open('data/us-key/index.json'))
        check(d['rules'] == 'oldoldoldold' and d['failed'] == ['TX'], 'a full build with a failed part keeps the old hash too')
        os.environ.pop('KPC_BUILD_FAILED_FILE')
        with contextlib.redirect_stdout(io.StringIO()): KF.stamp('us-key')
        d = json.load(open('data/us-key/index.json'))
        check(d['rules'] == R['us-key'] and 'failed' not in d and KF.VERSION_FILE in d['rules_files'], 'a full, complete build stores the current rules hash')
        os.environ.pop('KPC_FULL_BUILD')
    finally: os.chdir(cwd)

# --- the US plan step (extracted from the workflow and run as it is)
wf = (HERE / '.github/workflows/kpc-us-key.yml').read_text()
m = re.search(r"python3 - <<'PY' >> \"\$GITHUB_OUTPUT\"\n(.*?)\n\s*PY\n", wf[wf.index('      - id: p'):], re.S)
code = '\n'.join(l[10:] for l in m.group(1).split('\n'))
def plan(**env):
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(f'{t}/data/us-key'); today = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        json.dump({'built': today + ' 23:59 UTC', 'states': {}}, open(f'{t}/data/us-key/index.json', 'w'))   # 'a build already finished today'
        open(f'{t}/data/us-key/answers-states.txt', 'w').write('TN\n')
        e = {k: v for k, v in os.environ.items() if k not in ('FROZEN', 'RULES_CHANGED', 'STATES', 'SCHED')}; e.update(env)
        out = subprocess.run([sys.executable, '-c', code], cwd=t, env=e, capture_output=True, text=True).stdout
        g = re.search(r'^groups=(.*)$', out, re.M); f = re.search(r'^full=(.*)$', out, re.M)
        sts = sorted(sum((x['states'].split() for x in json.loads(g.group(1))), [])) if g else []
        return sts, (f.group(1) if f else ''), out
sts, full, out = plan(RULES_CHANGED='1', SCHED='17 9 * * *', NJOBS='3')
check(len(sts) == 50 and 'KY' not in sts and full == '1', f'US plan, rules changed, nightly start, a build already finished today: ALL {len(sts)} states (not skipped), full=1')
sts, full, out = plan(SCHED='17 9 * * *', NJOBS='3')
check(sts == [] or sts == ['TN'], f'US plan, same rules: the old nightly behaviour (skip / answers-states only): {sts}')
sts, full, out = plan(RULES_CHANGED='1', STATES='TN OH', NJOBS='3')
check(sts == ['OH', 'TN'] and full == '0', 'US plan: states given by hand still win (and it is not a full build)')
sts, full, out = plan(RULES_CHANGED='1', FROZEN='1', NJOBS='3')
check(sts == [], 'US plan: FROZEN still builds nothing')
check(not (base := subprocess.run(['git', 'show', f'{BASE}:.github/workflows/kpc-us-key.yml'], cwd=HERE, capture_output=True, text=True).stdout)
      or sorted(re.findall(r"cron: '([^']+)'", wf)) == sorted(re.findall(r"cron: '([^']+)'", base)), 'kpc-us-key.yml: the same crons as main (no new cron)')
check("KPC_FULL_BUILD: ${{ (needs.plan.outputs.full == '1' && needs.build.result == 'success') && '1' || '0' }}" in wf and 'full: ${{ steps.p.outputs.full }}' in wf,
      'US join: the stamp gets KPC_FULL_BUILD=1 only for a full plan whose build jobs all succeeded')
for wf_, sched in (('kpc-ca-key.yml', '49 9 * * *'), ('kpc-world-key.yml', '7 10 * * *')):
    s = (HERE / '.github/workflows' / wf_).read_text()
    check('if [ "${RULES_CHANGED:-}" = 1 ] && [ "${SKIP:-}" != 1 ]' in s and 'KPC_FULL_BUILD' in s, f'{wf_}: RULES_CHANGED overrides the nightly skip (FROZEN still skips) and the stamp is told when the build was full')
    crons = lambda t: sorted(re.findall(r"cron: '([^']+)'", t))
    base = subprocess.run(['git', 'show', f'{BASE}:.github/workflows/' + wf_], cwd=HERE, capture_output=True, text=True).stdout
    check(not base or crons(s) == crons(base), f'{wf_}: the same crons as main (no new cron): {crons(s)}')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)

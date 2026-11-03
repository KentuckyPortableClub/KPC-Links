"""Nov 2 review (Quality 5a / 5b, Mapping #7 / #18): the shared save keeps other bots' waiting-room lines, skips stamp-only
saves, and the build stamp names failed parts. Run: python3 tests/test_save_merge.py (needs git + bash, no network)."""
import json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUSH = ROOT / '.github/scripts/kpc_push_data.sh'
FREEZE = ROOT / '.github/scripts/kpc_key_freeze.py'
ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}
fails = 0


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env=ENV).stdout


def w(p, s):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s)


def check(name, ok):
    global fails
    print(('ok   ' if ok else 'FAIL ') + name)
    fails += 0 if ok else 1


with tempfile.TemporaryDirectory() as T:
    sh('git init -q --bare -b main origin.git && git clone -q origin.git a', T)
    a = f'{T}/a'
    w(f'{a}/data/waiting/in/data/x/a.json', '{}'); w(f'{a}/data/waiting/in/data/x/b.json', '{}')
    w(f'{a}/data/waiting/verdicts.jsonl', '{"l":1}\n')
    w(f'{a}/data/waiting/verdicts.json', json.dumps({'checked': '2026-11-02T10:00Z', 'results': [{'path': 'data/x/a.json', 'verdict': 'HOLD'}]}))
    w(f'{a}/data/waiting/held-since.json', json.dumps({'data/x/a.json': '2026-11-01'}))
    w(f'{a}/data/waiting/heartbeat.json', json.dumps({'ok': '2026-11-02T10:00Z'}))
    sh('git add -A && git commit -qm init && git push -q origin main && cd .. && git clone -q origin.git b && git clone -q origin.git c', a)
    b, c = f'{T}/b', f'{T}/c'
    w(f'{b}/data/waiting/verdicts.jsonl', '{"l":1}\n{"l":2}\n')
    w(f'{b}/data/waiting/verdicts.json', json.dumps({'checked': '2026-11-02T12:00Z', 'results': [{'path': 'data/x/a.json', 'verdict': 'HOLD'}]}))
    w(f'{c}/data/waiting/verdicts.jsonl', '{"l":1}\n{"l":3}\n')
    w(f'{c}/data/waiting/verdicts.json', json.dumps({'checked': '2026-11-02T11:00Z', 'results': [{'path': 'data/x/a.json', 'verdict': 'HOLD'}, {'path': 'data/x/b.json', 'verdict': 'HOLD'}]}))
    w(f'{c}/data/waiting/held-since.json', json.dumps({'data/x/a.json': '2026-11-01', 'data/x/b.json': '2026-11-02'}))
    sh(f'bash {PUSH} . "c save" data', c)
    sh(f'bash {PUSH} . "b save" data', b)
    sh('git pull -q origin main', a)
    lines = pathlib.Path(f'{a}/data/waiting/verdicts.jsonl').read_text().split()
    check('log lines from both bots are kept', sorted(lines) == ['{"l":1}', '{"l":2}', '{"l":3}'])
    v = json.loads(pathlib.Path(f'{a}/data/waiting/verdicts.json').read_text())
    check("the other bot's verdict for a still-held file is kept", sorted(r['path'] for r in v['results']) == ['data/x/a.json', 'data/x/b.json'])
    hs = json.loads(pathlib.Path(f'{a}/data/waiting/held-since.json').read_text())
    check('held-since keeps both files', hs == {'data/x/a.json': '2026-11-01', 'data/x/b.json': '2026-11-02'})
    head = sh('git rev-parse HEAD', a)
    w(f'{a}/data/waiting/heartbeat.json', json.dumps({'ok': '2026-11-02T14:00Z'}))
    v['checked'] = '2026-11-02T14:00Z'; w(f'{a}/data/waiting/verdicts.json', json.dumps(v, indent=1))
    out = sh(f'bash {PUSH} . "stamp only" data', a)
    check('a save that only moves checked / ok times is skipped', sh('git ls-remote origin main', a).split()[0] == head.strip() and 'nothing new to save' in out)
    w(f'{T}/k/data/world-key/index.json', json.dumps({'countries': {}, 'previous_build': 'W-1'})); w(f'{T}/failed.txt', 'DE\nAU\n')
    subprocess.run([sys.executable, str(FREEZE), 'stamp', 'world-key'], cwd=f'{T}/k', capture_output=True, env={**ENV, 'GITHUB_RUN_ID': '7', 'KPC_BUILD_FAILED_FILE': f'{T}/failed.txt'})
    d = json.loads(pathlib.Path(f'{T}/k/data/world-key/index.json').read_text())
    check('the stamp names failed countries', d.get('build') == 'W-7' and d.get('failed') == ['AU', 'DE'] and d.get('complete') is False)
print(f'{5 - fails} of 5 right')
sys.exit(1 if fails else 0)

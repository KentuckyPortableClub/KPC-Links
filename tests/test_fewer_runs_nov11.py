#!/usr/bin/env python3
"""Offline test, Nov 11 2026 (fewer runs, package B). Zero live network.
  1. pages-deploy.yml: a push that changes only tests/ or docs/ (or the old bookkeeping folders) starts no deploy, and the 2-hour
     timer treats them the same way (one list); no page of the site fetches anything under tests/ or docs/; the timer, the
     concurrency (one run + one waiting, the newest wins, nothing cancelled mid-deploy) and the Settle step are unchanged.
  2. kpc-discord-relay.yml: a started run's quick look checks out only the four files it reads (proved by running the look
     in a folder holding only those four files, with a stand-in GitHub CLI and Discord: it ends 'nothing new' there); the site
     is checked out only for a full run, before every step that reads it; a failed / hung look goes full; secrets only through
     env, never echoed; the relay's error notes never carry an address (no_addr).
  3. kpc-ky-key.yml (trigger only): the push paths are exactly the files the KY key run reads; every other line of the file is
     as on main.
"""
import ast, contextlib, fnmatch, io, json, os, pathlib, re, shutil, subprocess, sys, tempfile, types
import yaml

HERE = pathlib.Path(__file__).resolve().parent.parent
W = HERE / '.github/workflows'
ok = True


def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m, flush=True); ok = ok and bool(c)


def load(n): return yaml.safe_load((W / n).read_text(encoding='utf-8'))


def on_of(d): return d.get(True) or d.get('on') or {}


BASE = 'origin/main' if subprocess.run(['git', 'rev-parse', '-q', '--verify', 'origin/main'], cwd=HERE, capture_output=True).returncode == 0 else 'HEAD~1'


def main_yaml(n): return yaml.safe_load(subprocess.run(['git', 'show', f'{BASE}:.github/workflows/{n}'], cwd=HERE, capture_output=True, text=True).stdout or '{}') or {}


def gh_match(path, pat):
    """GitHub's paths filter: '**' any depth, '*' inside one folder."""
    rx = re.escape(pat).replace(r'\*\*', '\0').replace(r'\*', '[^/]*').replace('\0', '.*')
    return re.fullmatch(rx, path) is not None


# ---------------------------------------------------------------- 1. pages deploy
pd, pd0 = load('pages-deploy.yml'), main_yaml('pages-deploy.yml')
ign = on_of(pd)['push']['paths-ignore']
check({'tests/**', 'docs/**', '.claude/**', '.github/**', 'data/status/**'} <= set(ign), f'push filter skips tests/ and docs/ too: {ign}')
starts = lambda files: not all(any(gh_match(f, p) for p in ign) for f in files)
check(not starts(['tests/test_x.py', 'docs/notes.md']) and not starts(['tests/a/b.js', '.github/workflows/x.yml', 'data/status/board.json']),
      'a push of only tests / docs / workflow / status files starts no deploy')
check(starts(['tests/test_x.py', 'kpc-bounds.js']) and starts(['data/trails/US-1.json']) and starts(['index.html']), 'a push that also changes a site file still deploys')
run = pd['jobs']['changed']['steps'][0]['run']
regs = re.findall(r"grep -v -E '\^\(([^)]*)\)'", run)
want = sorted(p.replace('/**', '/').replace('.', r'\.') for p in ign)
check(len(regs) == 2 and all(sorted(r.split('|')) == want for r in regs), f'the timer counts the same folders as bookkeeping ({regs})')
cfg = (HERE / '_config.yml').read_text(encoding='utf-8')
fetches = []
for f in list(HERE.glob('*.html')) + list(HERE.glob('*.js')) + list(HERE.glob('app/**/*.js')) + list(HERE.glob('app/**/*.html')):
    for m in re.finditer(r"""(?:fetch\(|src=|href=|import\(|new Worker\()\s*['"`](?:\./|/KPC-Links/|/)?(tests|docs)/""", f.read_text(encoding='utf-8', errors='replace')):
        fetches.append(f'{f.name}:{m.group(0)[:60]}')
check(fetches == [], f'no page or script of the site loads anything under tests/ or docs/ {fetches[:5]}')
check(on_of(pd).get('schedule') == on_of(pd0).get('schedule') and pd.get('concurrency') == pd0.get('concurrency') and pd['jobs']['deploy'] == pd0['jobs']['deploy'] and pd['jobs']['build'] == pd0['jobs']['build'],
      'timer, concurrency (cancel-in-progress false), build and deploy + Settle unchanged vs main')
check(not pd['jobs']['changed'].get('if') and set(pd['jobs']) == {'changed', 'build', 'deploy'}, 'the first job has no if: a run never starts with zero jobs')

# ---------------------------------------------------------------- 2. relay
rl, rl0 = load('kpc-discord-relay.yml'), main_yaml('kpc-discord-relay.yml')
st = rl['jobs']['relay']['steps']
names = [s.get('name') or s.get('uses') for s in st]
sp = st[0]; pk = next(s for s in st if s.get('id') == 'peek'); full = next(s for s in st if (s.get('name') or '').startswith('Check out the site'))
peek_files = [x.strip() for x in sp['with']['sparse-checkout'].split('\n') if x.strip()]
check(sp.get('uses', '').startswith('actions/checkout') and sp['with'].get('path') == '.peek' and sp.get('if') == pk.get('if') and pk.get('working-directory') == '.peek',
      'started runs: a small checkout in its own folder, then the look runs there')
check(pk.get('continue-on-error') is True and 0 < int(pk.get('timeout-minutes') or 99) <= 5, 'a look that fails or hangs is cut off and counts as a full run')
_rl_text = (HERE / '.github' / 'workflows' / 'kpc-discord-relay.yml').read_text(encoding='utf-8')
_peek_coe = re.search(r'id: peek\n(?:[^\n]*\n){0,3}?\s*continue-on-error: true\s*# ok: \S', _rl_text)
check(bool(_peek_coe), "the look's continue-on-error carries an '# ok: <why>' marker (G8 reports a failed look)")
check(full.get('if') == "steps.peek.outputs.skip != '1'" and not full.get('with'), 'the whole site is checked out only when the full run goes ahead')
i_full = st.index(full)
reads_tree = [s for s in st if re.search(r'\.github/scripts/|kpc_save|git add', str(s.get('run') or ''))]
check(all(st.index(s) > i_full and s.get('if') == "steps.peek.outputs.skip != '1'" for s in reads_tree if s is not pk),
      f'every step that reads the site tree runs after the full checkout and only on a full run ({len(reads_tree) - 1} steps)')
always = [s for s in st if 'always()' in str(s.get('if'))]
check(all(not re.search(r'\.github/scripts/|python3 [^-]', str(s.get('run') or '')) or 'Report hidden' in (s.get('name') or '') for s in always),
      'the always() steps (heartbeats, report) need no checkout')
check(on_of(rl) == on_of(rl0) and rl.get('concurrency') == rl0.get('concurrency'), 'triggers (cron 5,35 + dispatch) and concurrency unchanged')
check(not rl['jobs']['relay'].get('if'), 'no job-level if: a start always has its job')
# the look in a folder that holds ONLY the sparse files
with tempfile.TemporaryDirectory() as t:
    td = pathlib.Path(t)
    for f in peek_files:
        (td / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy(HERE / f, td / f)
    st_ = json.loads((td / 'kpc-relay-state.json').read_text()); st_.update(queue=[], due='', last_id='1000')
    (td / 'kpc-relay-state.json').write_text(json.dumps(st_))
    sys.path.insert(0, str(td / '.github/scripts'))
    cwd = os.getcwd(); os.chdir(td)
    os.environ.update(GITHUB_OUTPUT=str(td / 'out.txt'), DISCORD_BOT_TOKEN='stand-in', KPC_RELAY_CHANNEL='42', GITHUB_RUN_ID='9', FULL='')
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    calls = []

    def fake_run(cmd, **k):
        calls.append(cmd[:3])
        if 'runs?per_page=8' in cmd[2]:
            return types.SimpleNamespace(returncode=0, stdout=f"7\t{(now - dt.timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ')}\tcompleted\n", stderr='')
        return types.SimpleNamespace(returncode=0, stdout='success\n', stderr='')

    class R(io.BytesIO):
        def __enter__(self): return self

        def __exit__(self, *a): pass
    import urllib.request
    seen = []
    real_urlopen = urllib.request.urlopen
    urllib.request.urlopen = lambda req, timeout=None: (seen.append(req.full_url), R(json.dumps({'last_message_id': '1000'}).encode()))[1]
    import kpc_relay_peek as PK
    PK.subprocess = types.SimpleNamespace(run=fake_run)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out): PK.main()
    except SystemExit: pass
    urllib.request.urlopen = real_urlopen
    os.chdir(cwd)
    res = (td / 'out.txt').read_text() if (td / 'out.txt').exists() else ''
    check('skip=1' in res and 'nothing new' in out.getvalue(), f'the look runs from the four sparse files alone and ends "nothing new" ({out.getvalue().strip()[:120]})')
    check(seen == ['https://discord.com/api/v10/channels/42'] and PK.kpc_net_guard is not None, 'its one Discord read went to the stand-in (host guard loaded from the sparse files)')
    for k in ('GITHUB_OUTPUT', 'DISCORD_BOT_TOKEN', 'KPC_RELAY_CHANNEL', 'GITHUB_RUN_ID', 'FULL'): os.environ.pop(k, None)
# secrets: only through env, never echoed
txt = (W / 'kpc-discord-relay.yml').read_text(encoding='utf-8')
sec_env = {k for s in st for k, v in (s.get('env') or {}).items() if 'secrets.' in str(v)}
bad = [s.get('name') for s in st if 'secrets.' in str(s.get('run') or '') + str(s.get('if') or '') + str(s.get('with') or '')]
echo = [l.strip()[:80] for s in st for l in str(s.get('run') or '').split('\n') for k in sec_env if re.search(r'\b(echo|printf)\b[^;&|]*\$\{?' + k + r'\b', l)]
check(bad == [] and echo == [], f'secrets reach the steps only through env, and no step prints one ({bad} {echo})')
# no_addr from the relay script (taken out with ast: the script runs when imported)
src = (HERE / '.github/scripts/kpc_discord_relay.py').read_text(encoding='utf-8')
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == 'no_addr')
ns = {'re': re}; exec(compile(ast.Module([fn], []), 'no_addr', 'exec'), ns)
fake = 'https://hooks.example.invalid/api/webhooks/0/not-a-real-token?thread_id=1'
for msg in (f"unknown url type: '{fake}'", f'<urlopen error {fake[:30]}>', f'URLError: refused {fake.split("?")[0]}'):
    o = ns['no_addr'](msg, fake)
    check('example.invalid' not in o and 'not-a-real' not in o and '<address>' in o, f'no_addr takes the address out: {o!r}')
check(ns['no_addr']('HTTP Error 400: Bad Request', fake) == 'HTTP Error 400: Bad Request', 'no_addr keeps a plain error as it is')
check(src.count('clip(no_addr(e), 150)') == 6 and 'no_addr(e)[:150]' not in src and 'str(e)[:150]' not in src and "return 0, no_addr(" in src, 'every problem note and the network helper use no_addr')

# ---------------------------------------------------------------- 3. KY key trigger
ky, ky0 = load('kpc-ky-key.yml'), main_yaml('kpc-ky-key.yml')
paths = on_of(ky)['push']['paths']
bounds = (HERE / 'kpc-bounds.js').read_text(encoding='utf-8')
kylist = re.search(r'const KY = \[(.*?)\]\.map', bounds, re.S).group(1)
read_js = set(re.findall(r"'(ky-[a-z-]+\.geojson)'", kylist))
read_tr = set(re.findall(r'ky-[a-z-]+\.geojson', (HERE / '.github/scripts/kpc_ky_tracts.py').read_text(encoding='utf-8')))
geo = {p for p in paths if p.endswith('.geojson')}
check(geo == read_js | read_tr, f'push paths = the KY layers kpc-bounds.js loads + kpc_ky_tracts.py reads ({len(geo)} files)')
dropped = {p.name for p in HERE.glob('ky-*.geojson')} - geo
check(dropped and not any(d in bounds or d in (HERE / '.github/scripts/kpc_ky_key.js').read_text() for d in dropped), f'the ky-*.geojson files left out are read by neither: {sorted(dropped)}')
check(all(any(fnmatch.fnmatch(str(x.relative_to(HERE)), p) for x in HERE.glob(p.split('/')[0] if '/' not in p else p.rsplit('/', 1)[0] + '/*')) for p in paths), 'every push path names a file that exists')
strip = lambda d: json.dumps({**{str(k): v for k, v in d.items() if k is not True}, 'on': {k: (dict(v, paths=None) if k == 'push' else v) for k, v in on_of(d).items()}}, sort_keys=True, default=str)
check(strip(ky) == strip(ky0) and {'kpc-ky-data.json', 'kpc-bounds.js', '.github/scripts/kpc_ky_key*'} <= set(paths), 'trigger-only change: everything but the push paths is as on main')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)

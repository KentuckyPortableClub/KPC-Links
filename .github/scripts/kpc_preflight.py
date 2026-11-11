#!/usr/bin/env python3
"""Run before opening a PR: python3 .github/scripts/kpc_preflight.py [--quick]. Offline, read-only, stdlib only (PyYAML and
actionlint are used when present). One PASS / WARN / SKIP / FAIL line per check; exit 1 on any FAIL. See docs/PREFLIGHT.md."""
import json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.github/scripts'))
BASE, DECL = 'origin/main', 'docs/key-rules-change.txt'
LABEL = {'us-key': 'US', 'ca-key': 'CA', 'world-key': 'world', 'fers': 'fers'}
HOST = re.compile(r'services[0-9]*(-[a-z0-9]+)?\.arcgis\.com|apps\.fs\.usda\.gov|ncnhde\.natureserve\.org')
GUARDS = ('kpc_net_guard', 'kpc_host_pace', 'kpc_http_cache', 'kpc_master')
WDPA = re.compile(r'(wdpa|protectedplanet|protected-?planet)[^\s\'"]*\.(zip|shp|geojson|json)|protectedplanet\.net/\S*(outline|geojson|download)', re.I)
PEOPLE = re.compile(r'\bt\d{3,4}u\b|\b[AKNW][A-Z]?\d[A-Z]{1,3}\b')   # ticket ids; callsigns (comment / doc lines only)

def git(*a):
    r = subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

def changelog_hashes(text, kind):
    """(old, new) of the NEWEST changelog line that moves `kind` (first line in the file; new = its FINAL arrow, else its last)."""
    pat = re.compile(r'(?<![A-Za-z])' + LABEL[kind] + r'(?: rules| v\d)? ([0-9a-f]{12}) -> ([0-9a-f]{12})')
    for ln in text.splitlines():
        m = list(pat.finditer(ln))
        if m:   # the arrow marked FINAL, else the last one (re-stamps come after the first arrow)
            fin = next((x for x in m if 'FINAL' in ln[x.end():x.end() + 40]), m[-1])
            return m[0].group(1), fin.group(2), ln
    return None, None, ''

def newest_hash(kind, text=None):
    """The hash the changelog says `kind` has now (tests compare rules_hash with this instead of a literal); None when unknown."""
    p = ROOT / DECL
    return changelog_hashes(text if text is not None else (p.read_text(encoding='utf-8') if p.is_file() else ''), kind)[1]

def base_hash(kind, KF):
    """rules_hash of origin/main: its rule files copied out with git show; None when origin/main is not in this clone."""
    if git('rev-parse', '--verify', BASE) is None: return None
    with tempfile.TemporaryDirectory() as td:
        for rel in list(KF.RULE_FILES[kind]) + [KF.VERSION_FILE]:
            b = subprocess.run(['git', 'show', f'{BASE}:{rel}'], cwd=ROOT, capture_output=True).stdout
            if b: (pathlib.Path(td) / rel).parent.mkdir(parents=True, exist_ok=True); (pathlib.Path(td) / rel).write_bytes(b)
        return KF.rules_hash(kind, td)

def check_hash_pair(kind, old, new, text, scope=None):
    """FAIL text or '': a moved hash needs the newest changelog line `old -> new` + APPROVED, decided_by KPC owner, and a scope entry from=old."""
    o, n, ln = changelog_hashes(text, kind)
    if f'{old} -> {new}' not in ln: return f'{kind}: newest changelog line for it does not say "{old} -> {new}" (found {o} -> {n})'
    if 'APPROVED, decided_by KPC owner' not in ln: return f'{kind}: changelog line lacks "APPROVED, decided_by KPC owner"'
    if scope is not None and not any(c.get('from') == old for c in scope.get('changes') or []): return f'{kind}: no scope entry with from = {old}'
    return ''

def added_lines(base_text, text):
    old = {l.strip() for l in (base_text or '').splitlines()}   # an indent change alone is not an added line
    return [l for l in text.splitlines() if l.strip() not in old]

def scan_added(path, lines):
    """(fails, warns) for the added lines of one file."""
    fails, warns, p = [], [], str(path)
    code = p.endswith(('.py', '.yml', '.yaml')) and not p.startswith(('tests/', 'docs/', 'data/'))
    guarded = any(g in '\n'.join(lines) for g in GUARDS) and p.endswith('.py')
    for l in lines:
        if code and not guarded and HOST.search(l) and 'preflight' not in p: fails.append(f'{p}: forbidden host: {l.strip()[:90]}')
        if WDPA.search(l) and not p.startswith(('tests/', 'docs/')): fails.append(f'{p}: WDPA / Protected Planet outline URL: {l.strip()[:90]}')
        doc = p.endswith(('.md', '.txt')) or l.lstrip().startswith(('#', '//', '"""', '*'))
        if (doc or re.search(r'\bt\d{3,4}u\b', l)) and PEOPLE.search(l) and 'preflight' not in p: warns.append(f'{p}: name / callsign / ticket id? {l.strip()[:80]}')
    return fails, warns

def step_env_problems(wf):
    """Expressions that GitHub rejects in a step-level env value."""
    bad = []
    for jn, job in (wf.get('jobs') or {}).items():
        for st in job.get('steps') or []:
            for k, v in (st.get('env') or {}).items():
                if re.search(r'\b(success|failure|always|cancelled)\(\)', str(v)): bad.append(f'{jn}: env {k} uses a status function')
    return bad

def undeclared_inputs(wf, text):
    on = wf.get(True, wf.get('on')) or {}
    decl = set()
    for t in ('workflow_dispatch', 'workflow_call'): decl |= set(((on.get(t) if isinstance(on, dict) else None) or {}).get('inputs') or {})
    return sorted(set(re.findall(r'\binputs\.([A-Za-z0-9_-]+)', text)) - decl)

def run():
    quick, out = '--quick' in sys.argv, []
    def say(st, name, msg=''): out.append(st); print(f'{st} {name}' + (f': {msg}' if msg else ''), flush=True)
    import kpc_key_freeze as KF
    changed = [x for x in (git('diff', '--name-only', '--diff-filter=AM', BASE) or '').split('\n') if x]
    untracked = [x for x in (git('ls-files', '--others', '--exclude-standard') or '').split('\n') if x]
    files = sorted(set(changed + untracked))
    if quick: say('SKIP', 'suite', '--quick')
    else:
        env = dict(os.environ, DATA=os.environ.get('DATA', '../kpc-data'), LINKS='.')
        r = subprocess.run([sys.executable, '-B', '.github/scripts/kpc_full_suite.py'], cwd=ROOT, capture_output=True, text=True, env=env)
        gate = [l for l in r.stdout.splitlines() if 'GATE ' in l or l.startswith('FAIL NEW') or 'stale baseline' in l]
        say('PASS' if r.returncode == 0 else 'FAIL', 'suite vs baseline', ' | '.join(gate[-4:]))
    text = (ROOT / DECL).read_text(encoding='utf-8') if (ROOT / DECL).is_file() else ''
    moved, problems = [], []
    for kind in LABEL:
        old, new = base_hash(kind, KF), KF.rules_hash(kind)
        if old is None: say('SKIP', 'rules hashes', f'{BASE} not in this clone (no fetch here)'); break
        if old == new: continue
        sc = None
        if kind in KF.SCOPE_FILES:
            try: sc = json.load(open(ROOT / KF.SCOPE_FILES[kind], encoding='utf-8'))
            except Exception: sc = {}   # noqa: BLE001
        moved.append(f'{LABEL[kind]} rules {old} -> {new}')
        why = check_hash_pair(kind, old, new, text, sc)
        if why:
            diff = [f for f in KF.RULE_FILES[kind] if f in files]
            problems.append(why + (' (rule files changed: ' + ', '.join(diff) + ')' if diff else ''))
    else:
        say('FAIL' if problems else 'PASS', 'rules hashes', '; '.join(problems) if problems else ('; '.join(moved) if moved else 'no rules hash moved'))
    wfs = [f for f in files if f.startswith('.github/workflows/') and f.endswith(('.yml', '.yaml'))]
    try: import yaml
    except ImportError: yaml = None
    bad = []
    for f in wfs:
        if yaml is None: break
        t = (ROOT / f).read_text(encoding='utf-8')
        try: wf = yaml.safe_load(t)
        except Exception as e: bad.append(f'{f}: not YAML ({str(e)[:60]})'); continue   # noqa: BLE001
        bad += [f'{f}: {b}' for b in step_env_problems(wf)] + [f'{f}: undeclared inputs.{x}' for x in undeclared_inputs(wf, t)]
    say('SKIP' if yaml is None else ('FAIL' if bad else 'PASS'), 'workflows', 'PyYAML missing (pip install pyyaml)' if yaml is None else '; '.join(bad) or f'{len(wfs)} workflow file(s) changed')
    if subprocess.run(['which', 'actionlint'], capture_output=True).returncode: say('SKIP', 'actionlint', 'not installed (go install github.com/rhysd/actionlint/cmd/actionlint@latest, or brew install actionlint)')
    elif wfs:
        r = subprocess.run(['actionlint', '-oneline', '-no-color', '-shellcheck=', '-pyflakes=', *wfs], cwd=ROOT, capture_output=True, text=True)
        say('PASS' if r.returncode == 0 else 'FAIL', 'actionlint', r.stdout.strip()[:300])
    r = subprocess.run([sys.executable, '-B', '.github/scripts/kpc_master_cli.py', 'check'], cwd=ROOT, capture_output=True, text=True)
    say('PASS' if r.returncode == 0 else 'FAIL', 'master check', (r.stdout + r.stderr).strip().splitlines()[-1][:200] if (r.stdout + r.stderr).strip() else '')
    _new = lambda f: subprocess.run(['git', 'cat-file', '-e', f'{BASE}:{f}'], cwd=ROOT, capture_output=True).returncode != 0   # noqa: E731  only a NEW file is held to the size limit
    big = [f for f in files if (ROOT / f).is_file() and (ROOT / f).stat().st_size > 1_000_000 and _new(f) or re.search(r'\.(zip|gdb|shp|gpkg)$|(^|/)raw/', f)]
    say('FAIL' if big else 'PASS', 'big / raw files', ', '.join(big[:6]) or 'none over 1 MB, no zip or raw layer')
    fails, warns, crons = [], [], []
    for f in files:
        if not (ROOT / f).is_file() or (ROOT / f).stat().st_size > 2_000_000: continue
        cur = (ROOT / f).read_text(encoding='utf-8', errors='replace')
        base = None if f in untracked else git('show', f'{BASE}:{f}')
        add = added_lines(base, cur)
        a, b = scan_added(f, add); fails += a; warns += b
        if f.startswith('.github/workflows/'): crons += [f'{f}: {l.strip()}' for l in add if re.match(r'\s*-?\s*(cron:|schedule:)', l)]
    say('FAIL' if fails else 'PASS', 'hosts / WDPA in added lines', '; '.join(fails[:4]) or 'clean')
    say('WARN' if warns else 'PASS', 'names / callsigns / ticket ids in added text', '; '.join(warns[:4]) or 'clean')
    say('FAIL' if crons else 'PASS', 'no new schedule', '; '.join(crons[:4]) or 'none added')
    return 1 if 'FAIL' in out else 0

if __name__ == '__main__':
    sys.exit(run())

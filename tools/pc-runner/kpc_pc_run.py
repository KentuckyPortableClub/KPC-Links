#!/usr/bin/env python3
"""KPC 2-FER PC RUNNER: run the club's OWN 2-fer code on this PC, against the PC outline store (KPC owner, 2026-11-15).

It runs the SAME code GitHub runs. There is no second copy of the rules here:
  * the KPC-Links code (kpc_fers.py, kpc_fers_store.py and the rest of the 2-fer rule files) comes from a checkout of KPC-Links at
    the PINNED commit in pins.json. 1-GET-CODE.bat makes that checkout. The pin is checked before anything runs.
  * the KPC-Data code (the key gate, the memory guard, the POTA pair reader, pick, annotate, the waiting room) is SHIPPED in
    pinned\\kpcdata, taken from the pinned KPC-Data commit, and every file's sha256 is checked against pinned\\MANIFEST.json.
  * the KPC-Store code (the bot wrapper, the run plan, the push check) is shipped in pinned\\kpcstore the same way.
This program only DRIVES them, in the same order as KPC-Store keeper/fers_store_run.sh does on GitHub.

    python tools\\kpc_pc_run.py check    [--settings settings.json]
    python tools\\kpc_pc_run.py run      [--settings settings.json] [--world] [--areas US-RI,US-DE] [--minutes 350] [--fresh]
    python tools\\kpc_pc_run.py summary  [--settings settings.json]

Nothing is uploaded. The 2-fer run itself makes no network request at all (the store module shuts the door). The only step that
uses the network is 1-GET-CODE.bat (git clone / fetch of the two public repos).
Python 3 standard library only.
"""
import argparse, datetime, hashlib, json, os, pathlib, re, shutil, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent.parent
AREA_RX = re.compile(r'\A(US|CA|W)-[A-Z]{2}\Z')
SHA_RX = re.compile(r'\A[0-9a-f]{40}\Z')


def say(*a): print(*a, flush=True)


def load_json(p, d=None):
    try: return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError): return d


def settings(path):
    s = load_json(path)
    if not isinstance(s, dict):
        say(f'STOPPED: {path} cannot be read. Open it in Notepad and check it is still proper JSON.'); sys.exit(2)
    return s


def pins():
    p = load_json(HERE / 'pins.json')
    if not isinstance(p, dict): say('STOPPED: pins.json cannot be read.'); sys.exit(2)
    return p


def git(args, cwd=None, quiet=False):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0')
    r = subprocess.run(['git', *args], cwd=str(cwd) if cwd else None, capture_output=True, text=True, env=env)
    if r.returncode and not quiet: say(f'   git {" ".join(args)} -> exit {r.returncode}: {(r.stderr or "").strip()[:200]}')
    return r


def head_of(repo):
    r = git(['rev-parse', 'HEAD'], repo, quiet=True)
    return r.stdout.strip() if r.returncode == 0 else ''


def manifest_problems(root, man):
    out = []
    for rel, want in sorted((man or {}).get('files', {}).items()):
        f = root / rel
        if not f.is_file(): out.append(f'missing: {rel}'); continue
        got = hashlib.sha256(f.read_bytes()).hexdigest()
        if got != want: out.append(f'changed: {rel}')
    return out


# ------------------------------------------------------------------ check
def cmd_check(a):
    s, pn = settings(a.settings), pins()
    bad = []
    say('KPC 2-FER PC RUNNER: setup check')
    say('')
    say(f'   today            {datetime.date.today().isoformat()}')
    say(f'   python           {sys.version.split()[0]}')
    r = git(['--version'], quiet=True)
    say(f'   git              {(r.stdout or "not found").strip()}')
    if r.returncode: bad.append('git is not installed (1-GET-CODE needs it). Install Git for Windows.')
    say('')
    say('SHIPPED CODE (taken from the pinned commits; every file checked by sha256)')
    man = load_json(HERE / 'pinned' / 'MANIFEST.json', {})
    say(f'   KPC-Data scripts  commit {man.get("kpcdata_commit", "?")}')
    say(f'   KPC-Store keeper  commit {man.get("kpcstore_commit", "?")}')
    probs = manifest_problems(HERE / 'pinned', man)
    if probs:
        bad.append('the shipped code does not match pinned\\MANIFEST.json: ' + '; '.join(probs[:4]))
    else: say(f'   {len(man.get("files", {}))} files, all as shipped')
    # Nov 16: the 2-fer code imports numpy and cv2 (the GitHub runs pip-install numpy and opencv-python-headless). Without
    # them every area dies in the first second of pass 1, so say it here, before anything runs.
    for mod, pkg in (('numpy', 'numpy'), ('cv2', 'opencv-python-headless')):
        r = subprocess.run([sys.executable, '-c', f'import {mod}'], capture_output=True, text=True)
        if r.returncode: bad.append(f'the Python package {pkg} is not installed (the 2-fers need it). Run INSTALL-PACKAGES.bat.')
        else: say(f'   python package   {pkg}: yes')
    say('')
    say('KPC-LINKS CHECKOUT (the 2-fer rules; 1-GET-CODE.bat makes it)')
    links = pathlib.Path(s.get('links_checkout') or '')
    want = str(pn.get('kpc_links_commit') or '')
    if not links.is_dir():
        bad.append(f'no KPC-Links checkout at {links}. Run 1-GET-CODE.bat first.')
    else:
        got = head_of(links)
        say(f'   folder           {links}')
        say(f'   wanted commit    {want}')
        say(f'   this checkout    {got or "(not a git checkout)"}')
        if got != want:
            bad.append('the KPC-Links checkout is NOT at the pinned commit. Run 1-GET-CODE.bat again.')
        else:
            anc = git(['merge-base', '--is-ancestor', want, 'origin/main'], links, quiet=True)
            if anc.returncode == 0: say('   on main          yes (the pinned commit is part of main)')
            else:
                say('')
                say('   *** WARNING: the pinned commit is NOT yet part of KPC-Links main. ***')
                say('   *** It is the prep/partial-view branch. Once the two pull requests are merged, move the  ***')
                say('   *** pin in pins.json to main\'s commit and run 1-GET-CODE.bat again.                      ***')
            for f in ('.github/scripts/kpc_fers.py', '.github/scripts/kpc_fers_store.py', '.github/fers-store-areas.json'):
                if not (links / f).is_file(): bad.append(f'the KPC-Links checkout has no {f}')
            # Nov 16: LINE ENDINGS. The rules hash and the per-area 2-fer fingerprint are worked out from the BYTES of
            # files in this checkout. Git for Windows writes CRLF by default, and a CRLF checkout then gave a different
            # hash than the club's own builds: the key gate called every green key stale and refused all 65 areas.
            crlf = crlf_rule_files(links)
            hs, why = rules_hashes(links)
            for k, v in sorted(hs.items()): say(f'   rules hash {k:<10} {v}')
            if crlf: say(f'   line endings     {len(crlf)} rule file(s) are CRLF (the club builds them LF)')
            exp = pn.get('expected_hashes') or {}
            if not hs:
                # never pass quietly: without the hashes this check cannot tell a good checkout from a stale one
                bad.append('could not work out the rules hashes from the KPC-Links checkout' + (f': {why}' if why else ''))
            for k, v in sorted(exp.items()):
                if hs and not hs.get(k): bad.append(f'the KPC-Links checkout gave no {k} rules hash; pins.json expects {v}')
            for k, v in sorted(exp.items()):
                if hs.get(k) and hs[k] != v:
                    bad.append(f'the {k} rules hash is {hs[k]}, pins.json expects {v}.' + (
                        '  Windows line endings are the usual cause: the hash is worked out from the BYTES of the rule '
                        'files. Run 1-GET-CODE.bat again (it now asks git for LF), then this check again.' if crlf else
                        '  The checkout is at the pinned commit, so the pin in pins.json is behind the club code: move it '
                        'to the newest KPC-Links main commit and run 1-GET-CODE.bat again.'))
    say('')
    say('KPC-DATA CHECKOUT (the data the bot reads and writes: data/ only, no code)')
    kd = pathlib.Path(s.get('kpcdata_checkout') or '')
    if not kd.is_dir(): bad.append(f'no KPC-Data checkout at {kd}. Run 1-GET-CODE.bat first.')
    else:
        say(f'   folder           {kd}')
        say(f'   commit           {head_of(kd) or "(not a git checkout)"}')
        # a cone-mode sparse checkout always brings the repository's own ROOT files (README.md, index.html and the like).
        # That is normal and harmless. What must not be here is another FOLDER of code; .github may hold fers-areas.json only.
        extra = sorted(p.name for p in kd.iterdir() if p.is_dir() and p.name not in ('data', '.git', '.github'))
        if extra: bad.append('the KPC-Data checkout must hold the data folder only; it also holds these folders: ' + ', '.join(extra[:6]))
        gh = sorted(p.name for p in (kd / '.github').iterdir()) if (kd / '.github').is_dir() else []
        if gh and gh != ['fers-areas.json']:
            bad.append('the KPC-Data checkout\'s .github folder must hold fers-areas.json only; it holds: ' + ', '.join(gh[:6]))
        if not (kd / '.github' / 'fers-areas.json').is_file():
            bad.append('fers-areas.json is not there (the run plan reads it). Run 1-GET-CODE.bat again.')
        # the shipped scripts in pinned\kpcdata read the same file from their own folder
        if not (HERE / 'pinned' / 'kpcdata' / '.github' / 'fers-areas.json').is_file():
            bad.append('pinned\\kpcdata\\.github\\fers-areas.json is not there (the key gate reads it). Run 1-GET-CODE.bat again.')
        if not (kd / 'data' / 'fers').is_dir(): bad.append(f'{kd}\\data\\fers is not there (the 2-fer files live there)')
    say('')
    say('THE PC OUTLINE STORE')
    for lab, key, pat in (('US and Canada', 'store_us_ca', r'(US|CA)-[A-Z]{2}'), ('world', 'store_world', r'W-[A-Z]{2}')):
        d = pathlib.Path(s.get(key) or '')
        n = len([p for p in d.glob('index-*.json') if re.fullmatch(pat, p.stem[len('index-'):])]) if d.is_dir() else 0
        say(f'   {lab:<14}   {d}')
        say(f'   {"":<14}   {n} area(s) found' if d.is_dir() else f'   {"":<14}   NOT THERE')
        if key == 'store_us_ca' and n == 0: bad.append(f'no US / Canadian area files in {d} (build the store first: 3-BUILD-ALL.bat)')
    say('')
    out = pathlib.Path(s.get('results') or (HERE / 'RESULTS'))
    say(f'RESULTS folder      {out}')
    say(f'PRIVATE folder      {private_dir(s)}   (club room only: never upload it)')
    say('')
    if bad:
        say('SOMETHING IS NOT READY:')
        for b in bad: say('   - ' + b)
        say('')
        say('Fix those, then run 0-CHECK-SETUP.bat again.')
        return 1
    say('ALL READY. Next: 2-RUN-2FERS.bat (US and Canada), then 4-CHECK-AND-SUMMARY.bat.')
    return 0


def rules_hashes(links):
    """The rules hashes the pinned KPC-Links code works out for itself (kpc_key_freeze.rules_hash): no copy of the rules here.
    Returns (hashes, why): 'why' is the reason when nothing came back, so the setup check can say it out loud (Nov 16)."""
    # Nov 16: the folder must be the FULL path. The child runs with cwd=links, so a relative settings path such as
    # repos\KPC-Links would be read a second time from inside itself and the import would fail.
    links = pathlib.Path(links).resolve()
    code = ('import json,sys;sys.path.insert(0,r"%s");import kpc_key_freeze as f;'
            'print(json.dumps({k:f.rules_hash(k) for k in f.RULE_FILES}))' % str(links / '.github' / 'scripts'))
    try:
        r = subprocess.run([sys.executable, '-c', code], cwd=str(links), capture_output=True, text=True)
    except OSError as e:
        return {}, str(e)[:200]
    got = load_json_str(r.stdout)
    if got: return got, ''
    return {}, (((r.stderr or '').strip().splitlines() or [''])[-1][:200] or f'exit {r.returncode}, nothing printed')


def crlf_rule_files(links):
    """The rule files in this checkout that hold Windows line endings. The rules hash is worked out from their bytes, so a CRLF
    copy of the right commit can still give the wrong hash and the 2-fer key gate then refuses every area (Nov 16)."""
    links = pathlib.Path(links).resolve()   # Nov 16: the full path, for the same reason as rules_hashes
    code = ('import json,pathlib,sys;sys.path.insert(0,r"%s");import kpc_key_freeze as f;'
            'fs=set()\n'
            'for v in f.RULE_FILES.values(): fs|=set(v)\n'
            'fs.add(f.VERSION_FILE)\n'
            'print(json.dumps([r for r in sorted(fs) if pathlib.Path(r).is_file() and b"\\r\\n" in pathlib.Path(r).read_bytes()]))'
            % str(links / '.github' / 'scripts'))
    try:
        r = subprocess.run([sys.executable, '-c', code], cwd=str(links), capture_output=True, text=True)
    except OSError:
        return []
    got = load_json_str(r.stdout)
    return got if isinstance(got, list) else []


def load_json_str(t):
    try: return json.loads(t.strip().splitlines()[-1])
    except Exception: return None   # noqa: BLE001


def private_dir(s):
    return pathlib.Path(s.get('private_folder') or (HERE / 'PRIVATE'))


# ------------------------------------------------------------------ the GitHub job's set-up steps, on the PC (Nov 16)
# KPC owner, 2026-11-16: the first two PC runs measured NOTHING. GitHub's store 2-fer job (KPC-Store kpc-store-fers.yml)
# does four things before the passes that this runner did not: it lays KPC-Data's moved data over the KPC-Links checkout
# (kpc_overlay.sh), gets the key's saved copy (boundary-cache release), copies the last 2-fer files in, and for each area
# reads the POTA activation history. Without the overlay the bot stops on its first line ("data/parkinfo is missing") and
# exits 0, so every area looked done. These are those steps, in the same order, plus a check that a pass which says
# STOPPED is never counted as done.
MOVED_LIST = '.github/kpc-moved.txt'
CACHE_RELEASE = 'https://github.com/KentuckyPortableClub/KPC-Links/releases/download/boundary-cache/'
CACHE_API = 'https://api.github.com/repos/KentuckyPortableClub/KPC-Links/releases/tags/boundary-cache'


def lay_overlay(links, kd):
    """kpc_overlay.sh in Python: every path in KPC-Links' .github/kpc-moved.txt is copied from the KPC-Data data checkout
    over the KPC-Links checkout. Returns a list of problems (empty = all laid in, none empty)."""
    lst = links / MOVED_LIST
    if not lst.is_file(): return [f'{MOVED_LIST} is not in the KPC-Links checkout']
    paths = [ln.strip() for ln in lst.read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.strip().startswith('#')]
    bad = []
    for rel in paths:
        src, dst = kd / rel, links / rel
        if src.is_dir():
            if dst.exists(): shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst)
            if not any(dst.iterdir()): bad.append(f'{rel} is empty')
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            if dst.stat().st_size == 0: bad.append(f'{rel} is empty')
        else:
            bad.append(f'{rel} is not in the KPC-Data checkout')
    # the old copies are still tracked in KPC-Links: tell git to leave the laid-in files alone (as kpc_overlay.sh does)
    git(['update-index', '--skip-worktree', '--'] + [r for r in paths if (links / r).is_file()], links, quiet=True)
    return bad


def lay_last_fers(links, kd):
    """'The last 2-fer files' step: KPC-Data's data/fers copied into the KPC-Links checkout, .json.gz unpacked."""
    import gzip
    dst = links / 'data' / 'fers'
    if dst.exists(): shutil.rmtree(dst)
    src = kd / 'data' / 'fers'
    if src.is_dir(): shutil.copytree(src, dst)
    else: dst.mkdir(parents=True, exist_ok=True)
    for f in list(dst.glob('*.json.gz')):
        f.with_suffix('').write_bytes(gzip.decompress(f.read_bytes())); f.unlink()
    return len(list(dst.glob('*.json')))


def lay_released_world_key(links, kd):
    """KPC owner, 2026-11-16 (one key for every reader): a world run reads the RELEASED world key, from the KPC-Data checkout,
    not the newer unreleased build in KPC-Links. The PC world store tool builds from the released key, so the 2-fers then read
    the same joins the store holds. Only the country files and layers.json are laid in; no rule file is touched, so no rules hash
    moves. Returns (countries laid in, problem or '')."""
    src, dst = kd / 'data' / 'world-key', links / 'data' / 'world-key'
    if not src.is_dir(): return 0, 'the KPC-Data checkout has no data/world-key (run 1-GET-CODE.bat again)'
    files = sorted(f for f in src.glob('*.json') if re.fullmatch(r'[A-Z]{2}', f.stem))
    if len(files) < 50: return len(files), f'only {len(files)} country files in the released world key (expected about 83)'
    for f in dst.glob('*.json'):
        if re.fullmatch(r'[A-Z]{2}', f.stem): f.unlink()   # a country only the unreleased build has is left out, as in the store
    for f in files: shutil.copy2(f, dst / f.name)
    if (src / 'layers.json').is_file(): shutil.copy2(src / 'layers.json', dst / 'layers.json')
    laid = [str(p.relative_to(links)).replace('\\', '/') for p in dst.glob('*.json') if re.fullmatch(r'[A-Z]{2}', p.stem)] + ['data/world-key/layers.json']
    git(['update-index', '--skip-worktree', '--'] + laid, links, quiet=True)
    return len(files), ''


def cache_missing(links):
    """The key's saved copy the store run reads its Wild and Scenic corridor records from: cache/us/US-*.json.gz, cache/ca/CA-ALL.json.gz."""
    us = list((links / 'cache' / 'us').glob('US-*.json.gz')) if (links / 'cache' / 'us').is_dir() else []
    ca = (links / 'cache' / 'ca' / 'CA-ALL.json.gz').is_file()
    out = []
    if not us: out.append('cache\\us\\US-*.json.gz')
    if not ca: out.append('cache\\ca\\CA-ALL.json.gz')
    return out


def cmd_get_cache(a):
    """1-GET-CODE.bat: download the key's saved copy (public KPC-Links release 'boundary-cache', about 86 MB) into the
    KPC-Links checkout, as the GitHub job's 'key's saved copy' step does. Only US-*.json.gz and CA-ALL.json.gz."""
    import urllib.request
    s = settings(a.settings)
    links = pathlib.Path(s['links_checkout']).resolve()
    try:
        with urllib.request.urlopen(urllib.request.Request(CACHE_API, headers={'User-Agent': 'kpc-pc-runner'}), timeout=60) as r:
            sizes = {x['name']: int(x.get('size') or 0) for x in json.loads(r.read().decode('utf-8')).get('assets') or []}
            assets = list(sizes)
    except Exception as e:  # noqa: BLE001
        say(f'STOPPED: the boundary-cache release list could not be read ({type(e).__name__}: {str(e)[:120]})'); return 2
    want = [n for n in assets if re.fullmatch(r'US-[A-Z]{2}\.json\.gz', n)] + [n for n in assets if n == 'CA-ALL.json.gz']
    if not want: say('STOPPED: the boundary-cache release lists no US-*.json.gz or CA-ALL.json.gz'); return 2
    got = kept = 0
    for n in want:
        d = links / 'cache' / ('ca' if n.startswith('CA-') else 'us'); d.mkdir(parents=True, exist_ok=True)
        if (d / n).is_file() and (d / n).stat().st_size == sizes.get(n, -1): kept += 1; continue   # already here, same size
        try:
            with urllib.request.urlopen(urllib.request.Request(CACHE_RELEASE + n, headers={'User-Agent': 'kpc-pc-runner'}), timeout=300) as r:
                (d / n).write_bytes(r.read()); got += 1
        except Exception as e:  # noqa: BLE001
            say(f'STOPPED: {n} could not be downloaded ({type(e).__name__}: {str(e)[:120]})'); return 2
    say(f'the key\'s saved copy: {got} downloaded, {kept} already here, in {links / "cache"}')
    return 0


def pass_stopped(log):
    """The bot's own 'STOPPED:' line in a pass log, or ''. The bot can stop on its first line and still exit 0."""
    try: txt = pathlib.Path(log).read_text(encoding='utf-8', errors='replace')
    except OSError: return ''
    for ln in txt.splitlines():
        if 'title=2-fer bot::STOPPED' in ln: return ln.split('::STOPPED', 1)[1].lstrip(': ').strip()[:200]
    return ''


def pass1_read_nothing(*logs):
    """Nov 16: pass 1 that read NO outline while the area has official parks measured nothing (a world store run once did
    this and still exited 0). The why, or ''. Reads the LAST 'pass 1' lines of the logs given (the pass log; for a world run
    also the private run log, where the bot writes its own lines)."""
    txt = ''
    for f in logs:
        try: txt += pathlib.Path(f).read_text(encoding='utf-8', errors='replace') + '\n'
        except OSError: pass
    read = [m for m in re.findall(r'title=2-fer bot::pass 1: (\d+) parks (?:to read from the outline store|from saved outlines, (\d+) to download)', txt)]
    counts = re.findall(r'title=2-fer bot::\{"pass": 1, [^\n]*?"official parks": (\d+)', txt)   # the line may be cut short
    if not read or not counts: return 'pass 1 wrote none of its count lines (it measured nothing)'
    n, off = int(read[-1][0]) + int(read[-1][1] or 0), int(counts[-1])
    if n == 0 and off > 0: return f'pass 1 read 0 outlines for {off} official parks (it measured nothing)'
    return ''


def world_ready(links):
    """(countries the 2-fer ready list opens, the rule's own words). KPC-Links .github/fers-ready-areas.json decides."""
    d = load_json(links / '.github' / 'fers-ready-areas.json', {}) or {}
    pats = [v.get('match') for v in (d.get('areas') or {}).values() if isinstance(v, dict) and v.get('match')]
    return [p for p in pats if str(p).startswith('^W')], str(d.get('about') or '')


# ------------------------------------------------------------------ run
def cmd_run(a):
    s, pn = settings(a.settings), pins()
    if cmd_check(argparse.Namespace(settings=a.settings)) != 0:
        say('STOPPED: the setup check found a problem (above). Nothing was run.'); return 2
    links = pathlib.Path(s['links_checkout']).resolve()
    kd = pathlib.Path(s['kpcdata_checkout']).resolve()
    store = pathlib.Path(s['store_world' if a.world else 'store_us_ca']).resolve()
    out = pathlib.Path(s.get('results') or (HERE / 'RESULTS')).resolve()
    priv = private_dir(s).resolve()
    scripts = HERE / 'pinned' / 'kpcdata' / '.github' / 'scripts'
    keeper = HERE / 'pinned' / 'kpcstore' / 'keeper'
    for d in (out, priv, priv / 'logs', priv / 'withheld'): d.mkdir(parents=True, exist_ok=True)
    if priv.is_relative_to(links) or priv.is_relative_to(kd):
        say('STOPPED: the private folder must be OUTSIDE both checkouts (its files are club room only).'); return 2

    areas = [x.strip().upper() for x in (a.areas or '').replace(',', ' ').split() if x.strip()]
    for x in areas:
        if not AREA_RX.fullmatch(x): say(f'STOPPED: {x!r} is not an area code like US-RI, CA-ON or W-GB.'); return 2
    if a.world and not areas:
        areas = sorted(p.stem[len('index-'):] for p in store.glob('index-W-*.json'))
        if not areas: say(f'STOPPED: no world areas in {store}.'); return 2
    if a.world:   # Nov 16: say it before anything runs, not after 80 countries that each skip
        opened, about = world_ready(links)
        if not opened:
            say('STOPPED: the 2-fer ready list (KPC-Links .github/fers-ready-areas.json) opens no world country.')
            say('   Its own words: ' + (about[:300] or '(no words)'))
            say('   World 2-fers need ownership AND management data wired for the world first. Nothing was run.')
            return 2
    # --- the baseline: today's public 2-fer files, before this run (for the never-worse comparison)
    base = out / 'baseline'
    if base.exists(): shutil.rmtree(base)
    (base / 'data' / 'fers').mkdir(parents=True)
    for f in sorted((kd / 'data' / 'fers').glob('*.json')) + sorted((kd / 'data' / 'fers').glob('*.json.gz')):
        shutil.copy2(f, base / 'data' / 'fers' / f.name)
    say(f'baseline: {len(list((base / "data" / "fers").iterdir()))} of today\'s 2-fer files copied to {base}')

    # --- the plan (KPC-Store keeper/fers_run_plan.py: the same rows GitHub would do)
    plan_f = priv / 'plan.json'
    if a.world:
        rows = [{'area': x, 'tag': x.lower().replace('-', ''), 'seed': None, 'skip': ''} for x in areas]
        plan_f.write_text(json.dumps({'rows': rows}), encoding='utf-8')
    else:
        pa = ['plan', '--states', ','.join(areas) if areas else 'all', '--target', 'prep/fers-store-test',
              # the plan reads .github/fers-areas.json out of this folder. pinned\kpcdata holds only the scripts, so point
              # it at the KPC-Data checkout, where 1-GET-CODE.bat puts that one file from the PINNED commit.
              '--kpcdata', str(kd), '--links', str(links), '--store', str(store), '--out', str(plan_f)]
        if a.fresh: pa.append('--fresh')
        prog = priv / 'progress.json'
        if prog.is_file(): pa += ['--progress', str(prog)]
        r = subprocess.run([sys.executable, str(keeper / 'fers_run_plan.py'), *pa], capture_output=True, text=True)
        say((r.stdout or '').strip()[-2000:])
        if r.returncode: say(f'STOPPED: the run plan refused this request (exit {r.returncode}). {(r.stderr or "")[:300]}'); return 2
        rows = (load_json(plan_f) or {}).get('rows') or []
    todo = [r for r in rows if not r.get('skip')]
    for r in rows:
        if r.get('skip'): say(f'   {r["area"]}: left out this run ({str(r["skip"])[:90]})')
    if not todo: say('Nothing to do: every area of this request is left out or already finished. Use --fresh to start the cycle again.'); return 0
    say(f'{len(todo)} area(s) to do: ' + ' '.join(r['area'] for r in todo))

    env = dict(os.environ)
    env.pop('KPC_FERS_WORLD_STORE', None)
    env.update({'REGION': 'world' if a.world else 'na', 'KPC_FERS_FROM_STORE': 'on',
                'KPC_FERS_STORE_KIND': 'private' if a.world else 'public',
                'KPC_FERS_STORE_DIR': str(store), 'KPC_FERS_PRIVATE_LOG': str(priv),
                'KPC_FERS_LIVE_DIR': str(priv / 'cache-fers'), 'KPC_STATUS_NAME': 'kpc_fers',
                # privacy grade 2026-11-16 (F2): the per-pair "not shown" reasons go here, never into a published file
                'KPC_FERS_NOT_SHOWN_DIR': str(priv),
                'KPC_HARD_END': str(int(time.time()) + int(a.minutes) * 60), 'PYTHONDONTWRITEBYTECODE': '1'})
    if a.world:
        env['KPC_FERS_WORLD_STORE'] = 'on'                 # off GitHub only; the repo file still says "world": "off"
        env['KPC_FERS_PRIVATE_OUT'] = str(priv / 'world-out')
        (priv / 'world-out').mkdir(parents=True, exist_ok=True)
    env['KPC_FERS_PARK_S'] = env.get('KPC_FERS_PARK_S') or '600'   # the GitHub job's per-park limit
    # --- the GitHub job's set-up steps (Nov 16): without them the bot stops on its first line
    bad = lay_overlay(links, kd)
    if bad:
        say('STOPPED: KPC-Data\'s moved data could not be laid over the KPC-Links checkout: ' + '; '.join(bad[:4]))
        say('   Run 1-GET-CODE.bat again. Nothing was run.'); return 2
    say('overlay: KPC-Data\'s moved data laid over the KPC-Links checkout (the GitHub job\'s first step)')
    say(f'the last 2-fer files: {lay_last_fers(links, kd)} copied in')
    if a.world:
        n, why = lay_released_world_key(links, kd)
        if why:
            say('STOPPED: the released world key could not be laid in: ' + why + '. Nothing was run.'); return 2
        say(f'world key: the RELEASED key from KPC-Data ({n} countries, commit {head_of(kd)[:12] or "?"}), not KPC-Links\' unreleased build')
    if not a.world:
        miss = cache_missing(links)
        if miss:
            say('STOPPED: the key\'s saved copy is not in the KPC-Links checkout (' + ', '.join(miss) + '). Run 1-GET-CODE.bat again.')
            return 2
    t_end = int(time.time()) + int(a.minutes) * 60
    done, red = [], []
    for r in todo:
        A, TAG = r['area'], r['tag']
        left = (t_end - int(time.time())) // 60
        if left < 10: say(f'   {A}: not started (only {left} minutes left; run it again later)'); break
        say('')
        say(f'== {A} (tag {TAG}): up to {min(int(s.get("minutes_per_area") or 120), left)} minutes')
        budget = min(int(s.get('minutes_per_area') or 120), left)
        if not a.world:   # the key gate: every state measured must be built green on the current rules (the GitHub step)
            rc = run_log(priv / 'logs' / f'{A}-keygate.log', [sys.executable, str(scripts / 'kpc_fers_key_gate.py')],
                         cwd=links, env=dict(env, REGION='na', STATES=A))
            if rc:
                say(f'   {A}: the answer-key gate refused this area; it keeps its previous files'); red.append((A, 'key gate refused')); continue
        seed = r.get('seed')
        if seed:   # the area's saved pair answers start from its group's (as the GitHub job does)
            for p in (1, 2, 3, 5):
                tgt, src = links / 'data' / 'fers' / f'reuse-p{p}-{TAG}.json', links / 'data' / 'fers' / f'reuse-p{p}-{seed}.json'
                if not tgt.is_file() and src.is_file(): shutil.copy2(src, tgt)
        # POTA activation history: OFF unless settings.json says "pota_history": "on" (owner, Nov 16: official boundaries are the
        # proof, not what activators logged; the step read every park from POTA before every area, 24 minutes for CA-BC)
        if not a.world and str(s.get('pota_history') or 'off').strip().lower() == 'on':
            pm = min(budget // 4, 40)
            if pm >= 1:
                try:
                    prc = run_log(priv / 'logs' / f'{A}-pota.log', [sys.executable, str(scripts / 'kpc_pota_pairs_run.py')],
                                  cwd=links, env=dict(env, STATES=A, PAIR_MINUTES=str(pm), LINKS='.', DATA=str(kd)))
                except Exception as e:  # noqa: BLE001
                    prc = f'{type(e).__name__}'
                if prc: say(f'   {A}: the POTA activation history stopped ({prc}); the missing check uses the copy it has')
        a_end = int(time.time()) + budget * 60
        ok, why = True, ''
        for p in (1, 2, 3, 5):
            l = (a_end - int(time.time())) // 60
            cap = {1: budget * 2 // 5, 2: l // 2, 3: l * 4 // 5, 5: l}[p]
            cap = min(cap, l)
            if cap < 5: ok, why = False, f'no time left for pass {p}'; break
            log = priv / 'logs' / f'{A}-p{p}.log'
            rc = run_log(log, [sys.executable, str(scripts / 'kpc_mem_guard.py'), '--label', f'{A} pass {p}', '--',
                               sys.executable, str(keeper / 'fers_bot_run.py'), 'run',
                               str(links / '.github' / 'scripts' / 'kpc_fers.py'), f'{TAG}-p{p}'],
                         cwd=links, env=dict(env, PASS=str(p), MINUTES=str(cap), STATES=A, RUN_TAG=TAG,
                                             KPC_MEM_STOP_FILE=str(priv / 'mem-stop.txt')))
            for ln in keep_lines(log): say('   ' + ln)
            # KPC owner, 2026-11-16: in a store run pass 2 does nothing (every pass reads the same store outlines), so say so
            # rather than printing a bare 'exit 0' that reads as if it had measured something.
            _noop = p == 2 and rc == 0 and 'pass 2 not run' in log.read_text(encoding='utf-8', errors='replace')
            say(f'   {A} pass {p}: nothing to do (this run reads the store, so pass 3 does this test on its finer grid)'
                if _noop else f'   {A} pass {p}: exit {rc} (the full log is in the private folder)')
            if rc == 89:
                say('')
                say('*** The write guard refused a public file (exit 89). The run STOPS and nothing may be used. ***')
                (priv / 'LEAK').write_text(f'89 {A} pass {p}\n', encoding='utf-8'); return 89
            if rc == 0 and not (priv / 'withheld' / f'{TAG}-p{p}.json').is_file():
                say('*** A pass ended without its withheld list. The run STOPS and nothing may be used. ***')
                (priv / 'LEAK').write_text(f'nolist {A} pass {p}\n', encoding='utf-8'); return 89
            stop_why = pass_stopped(log) if rc == 0 else ''
            if stop_why:   # Nov 16: the bot can stop on its first line and still exit 0; that is never "done"
                ok, why = False, f'pass {p}: the 2-fer bot STOPPED ({stop_why})'; say(f'   {A}: {why}'); break
            if rc == 0 and p == 1:
                nothing = pass1_read_nothing(log, *( [priv / 'world-out' / 'run-log.txt'] if a.world else []))
                if nothing: ok, why = False, nothing; say(f'   {A}: {why}'); break
            if rc == 87: ok, why = False, 'not ready in the store (exit 87)'; break
            if rc == 88: ok, why = False, 'will not fit in memory (exit 88)'; break
            if rc == 3: ok, why = False, 'stopped for time (exit 3)'; break
            if rc == 86: ok, why = False, 'stopped by the memory guard (exit 86)'; break
            if rc: ok, why = False, f'pass {p} stopped with an error (exit {rc})'; break
        # KPC owner, 2026-11-16 (proof of work, item 1; KPC-Links #222): "done" comes from the RECEIPT, not from the exit codes.
        # Every pass writes one, with what it expected, what it read, what it held and why, and its POTA request count. No receipt,
        # a pass missing from it, an area it never measured (store empty, store missing, 0 of N read) or another rules hash = red,
        # and the area keeps its previous files. The GitHub job does the same check (KPC-Data #96).
        if ok:
            rcp = links / '.github' / 'scripts' / 'kpc_fers_receipt.py'
            out = (priv / 'world-out') if a.world else (links / 'data' / 'fers')
            if rcp.is_file():
                rc = run_log(priv / 'logs' / f'{A}-receipt.log', [sys.executable, str(rcp), 'check', '--dir', str(out),
                                                                 '--passes', '1,2,3,5', '--tag', TAG, '--allow-time-stop'],
                             cwd=links, env=env)
                if rc:
                    ok, why = False, f'the receipt says this area is not done (exit {rc}; see {A}-receipt.log)'
                    say(f'   {A}: {why}')
            else:
                say(f'   {A}: no receipt checker in this KPC-Links checkout (older pin): "done" is the exit codes only')
        if ok:
            rc = run_log(priv / 'logs' / f'{A}-expected.log', [sys.executable, str(links / '.github' / 'scripts' / 'kpc_fers_expected.py')],
                         cwd=links, env=dict(env, STATES=A, RUN_TAG=TAG))
            if rc: ok, why = False, 'the missing check stopped with an error'
        if not ok:
            say(f'   {A}: {why}; the area keeps its previous files'); red.append((A, why)); continue
        if a.world:
            say(f'   {A}: done (club room only: its files are in {priv / "world-out"}, never uploaded)')
            done.append(A); continue
        # ---- the save steps, exactly as the GitHub job does them, into the KPC-Data checkout
        rc = run_log(priv / 'logs' / f'{A}-pick.log', [sys.executable, str(scripts / 'kpc_fers_states.py'), 'pick'],
                     cwd=links, env=dict(env, STATES=A, REGION='na', KPCDATA=str(kd), LINKS=str(links),
                                         JOB=f'store 2-fers {A}', KPC_FERS_NO_BASE_CHECK='1'))
        if rc == 2:
            say(f'   {A}: pick refused (two files hold one pair): nothing of it saved'); red.append((A, 'pick refused')); continue
        for k in ('reuse-p1', 'reuse-p2', 'reuse-p3', 'reuse-p5', 'report', 'looked', 'missing', 'store-missing', 'expected'):
            for nm in (f'{k}-{TAG}.json', f'{k}-{TAG}.json.gz'):
                f = links / 'data' / 'fers' / nm
                if f.is_file(): shutil.copy2(f, kd / 'data' / 'fers' / nm)
        run_log(priv / 'logs' / f'{A}-annotate.log', [sys.executable, str(scripts / 'kpc_fers_annotate.py'), '--new',
                                                      str(links / 'data' / 'fers'), '--live', str(kd), '--states', A], cwd=links, env=env)
        rc = run_log(priv / 'logs' / f'{A}-divert.log', [sys.executable, str(scripts / 'kpc_waiting_room.py'), 'divert', 'data/fers'],
                     cwd=kd, env=dict(env, DATA='.', LINKS=str(links)))
        if rc:
            say(f'   {A}: the waiting-room step failed; nothing of it may be used'); red.append((A, 'divert failed')); continue
        say(f'   {A}: saved into the KPC-Data folder (held in the waiting room)')
        done.append(A)
    (priv / 'run.json').write_text(json.dumps({'world': bool(a.world), 'done': done, 'red': red,
                                               'when': datetime.datetime.now().isoformat(timespec='seconds'),
                                               'minutes': round((int(time.time()) - (t_end - int(a.minutes) * 60)) / 60, 1),
                                               'areas': [r['area'] for r in todo],
                                               'tags': [r['tag'] for r in todo]}), encoding='utf-8')
    # KPC owner, 2026-11-16: record what finished, so the NEXT run carries on instead of starting at the first area again.
    # GitHub writes this after a successful push (keeper/fers_save_log.sh calls 'result' per area then 'progress'); there is no
    # push here, so nothing on this PC ever wrote it: progress.json never existed and every run began again at the first area.
    # The owner's run of 2026-11-16 finished 24 of 41 areas and the next one started over at CA-AB.
    if not a.world:   # the world plan is built here, not by fers_run_plan, and world runs do not read a progress file
        def _note(area, final, why):
            subprocess.run([sys.executable, str(keeper / 'fers_run_plan.py'), 'result', '--priv', str(priv),
                            area, 'final' if final else 'again', (why or '-')[:200]], capture_output=True, text=True)
        for _A in done: _note(_A, True, 'finished on this PC')
        for _A, _w in red: _note(_A, False, _w)
        pg = priv / 'progress.json'
        r = subprocess.run([sys.executable, str(keeper / 'fers_run_plan.py'), 'progress', '--priv', str(priv)]
                           + (['--progress', str(pg)] if pg.is_file() else []), capture_output=True, text=True)
        line = (r.stdout or '').strip().splitlines()
        say('   ' + (line[-1] if line else f'progress NOT recorded (exit {r.returncode}): the next run starts at the first area again'))
    say('')
    say(f'{len(done)} area(s) finished, {len(red)} not. Next: 4-CHECK-AND-SUMMARY.bat')
    return 0


def run_log(log, cmd, cwd, env):
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, 'w', encoding='utf-8', errors='replace') as fh:
        return subprocess.run(cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT, env=env).returncode


def keep_lines(log):
    """Only the lines the store module and the memory guard print for a public log (counts and area reasons, never a park)."""
    try: t = pathlib.Path(log).read_text(encoding='utf-8', errors='replace')
    except OSError: return []
    return [ln[:400] for ln in t.splitlines()
            if re.match(r'::(error|warning|notice) title=(2-fer outline store|memory guard)', ln)][:12]


# ------------------------------------------------------------------ summary
def cmd_summary(a):
    s = settings(a.settings)
    kd = pathlib.Path(s['kpcdata_checkout']).resolve()
    out = pathlib.Path(s.get('results') or (HERE / 'RESULTS')).resolve()
    priv = private_dir(s).resolve()
    keeper = HERE / 'pinned' / 'kpcstore' / 'keeper'
    run = load_json(priv / 'run.json', {}) or {}
    out.mkdir(parents=True, exist_ok=True)
    if (priv / 'LEAK').is_file():
        say('*** The last run was refused by the write guard. Nothing may be used. Send the PRIVATE folder to nobody. ***')
        return 10
    if not run: say('No run to check yet. Run 2-RUN-2FERS.bat first.'); return 2
    L = ['KPC 2-FER PC RUN: SUMMARY', '=========================', '',
         f'when          {run.get("when")}', f'kind          {"WORLD (club room only)" if run.get("world") else "US and Canada"}',
         f'minutes       {run.get("minutes")}', f'areas done    {len(run.get("done") or [])}: ' + ' '.join(run.get('done') or []),
         f'areas not     {len(run.get("red") or [])}' + (': ' + '; '.join(f'{x[0]} ({x[1]})' for x in (run.get('red') or [])) if run.get('red') else ''), '']
    # ---- the files this run would push, copied into RESULTS
    # KPC owner, 2026-11-17: the US / Canada files waiting in the KPC-Data checkout are checked whatever ran LAST. A world run
    # (club room only) writes nothing there, so after one the US / Canada files of the run before are still the ones a push
    # would carry, and the push check must still look at them. The areas and tags come from those files themselves.
    _r0 = git(['status', '--porcelain', '-uall', '--', 'data'], kd, quiet=True)
    _waiting = [ln[3:].strip().strip('"') for ln in (_r0.stdout or '').splitlines() if ln.strip()]
    if run.get('world') and _waiting:
        L += ['The last run was WORLD (club room only). The US / Canada files still waiting in the KPC-Data checkout from the run',
              'before are checked below, because they are what a push would carry.', '']
    if not run.get('world') or _waiting:
        push = out / 'to-kpc-data'
        if push.exists(): shutil.rmtree(push)
        (push / 'data' / 'fers').mkdir(parents=True)
        r = git(['status', '--porcelain', '-uall', '--', 'data'], kd, quiet=True)
        changed = [ln[3:].strip().strip('"') for ln in (r.stdout or '').splitlines() if ln.strip()]
        for rel in changed:
            src = kd / rel
            if src.is_file():
                dst = push / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
        L += [f'FILES THIS RUN WOULD PUSH TO KPC-DATA: {len(changed)} (copied to {push})'] + \
             [f'   {x}' for x in sorted(changed)[:40]] + (['   ...'] if len(changed) > 40 else []) + ['']
        # ---- the push check, on the staged change (nothing is committed and nothing is pushed)
        git(['add', '-A', '--', 'data'], kd, quiet=True)
        _ar = sorted({m.group(1) for x in changed for m in [re.search(r'data/fers/(?:stamps/)?((?:US|CA)-[A-Z]{2})\.json', x)] if m})
        _tg = sorted({a.lower().replace('us-', '').replace('-', '') for a in _ar})   # = fers_run_plan.tag_of
        areas = ' '.join(run.get('areas') or []) if not run.get('world') else ' '.join(_ar)
        tags = ' '.join(run.get('tags') or []) if not run.get('world') else ' '.join(_tg)
        pc = subprocess.run([sys.executable, str(keeper / 'fers_push_check.py'), '--repo', str(kd), '--staged',
                             '--private', str(priv), '--areas', areas or 'US-RI', '--tags', tags or 'x'],
                            capture_output=True, text=True)
        (out / 'push-check.txt').write_text((pc.stdout or '') + (pc.stderr or ''), encoding='utf-8')
        git(['reset', '-q'], kd, quiet=True)
        verdict = {0: 'CLEAN (a GitHub run would be allowed to push this)',
                   10: 'REFUSED (something in the files is not allowed to go public)'}.get(pc.returncode, f'COULD NOT RUN (exit {pc.returncode})')
        L += [f'PUSH CHECK: {verdict}', f'   the full output is in {out / "push-check.txt"}', '']
        for ln in (pc.stdout or '').splitlines()[:12]: L.append('   ' + ln[:200])
        L.append('')
    # ---- never worse, against today's public 2-fers
    # Nov 16: a run's new file lands in the WAITING ROOM (data/waiting/in/data/fers); data/fers is the live copy, which a run
    # never changes. Comparing the baseline with data/fers could only ever say "same". Compare with this run's own files.
    L += never_worse(out / 'baseline' / 'data' / 'fers', kd / 'data' / 'waiting' / 'in' / 'data' / 'fers',
                     only=[str(x) for x in (run.get('done') or [])])
    L += ['', 'Nothing was uploaded by this tool. The PRIVATE folder is club room only: never put it in a repo.']
    (out / 'SUMMARY.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    say('\n'.join(L))
    say('')
    say(f'Written: {out / "SUMMARY.txt"}')
    return 0


def read_spots(f):
    import gzip
    try:
        raw = pathlib.Path(f).read_bytes()
        t = gzip.decompress(raw) if str(f).endswith('.gz') else raw
        d = json.loads(t.decode('utf-8'))
    except Exception: return None   # noqa: BLE001
    if not isinstance(d, dict) or not isinstance(d.get('spots'), list): return None
    return d['spots']


def shown(spots):
    """The pairs a 2-fer file SHOWS: a row whose status is not a denial or a merge (the site shows 'candidate' rows)."""
    out = {}
    for x in spots or []:
        if not isinstance(x, dict) or not x.get('refs'): continue
        if str(x.get('status') or '').startswith(('dropped', 'merged')): continue
        out[(tuple(sorted(x['refs'])), x.get('kind'))] = str(x.get('status'))[:60]
    return out


def never_worse(base_dir, new_dir, only=None):
    """Today's public 2-fer files (the baseline) against the files THIS run made (the waiting room). Only the areas this
    run finished are compared: an area the run did not measure says nothing either way (Nov 16)."""
    L = ['NEVER WORSE, this run\'s files against today\'s public 2-fers', '----------------------------------------------------']
    base_dir, new_dir = pathlib.Path(base_dir), pathlib.Path(new_dir)
    if not base_dir.is_dir(): return L + ['   no baseline was taken (run 2-RUN-2FERS.bat first)']
    if not only: return L + ['   this run finished no area, so there is nothing to compare (and nothing new to use)']
    tot = {'same': 0, 'new': 0, 'gone': 0, 'partial': 0}
    rows = []
    for area in sorted(set(only)):
        if not re.fullmatch(r'(US|CA)-[A-Z]{2}', area): continue
        f = next((base_dir / n for n in (f'{area}.json', f'{area}.json.gz') if (base_dir / n).is_file()), None)
        nf = next((new_dir / n for n in (f'{area}.json', f'{area}.json.gz') if (new_dir / n).is_file()), None)
        if nf is None: rows.append(f'   {area}: finished, but its new file is not in the waiting room: NOT COMPARED'); continue
        a = shown(read_spots(f)) if f else {}
        b = shown(read_spots(nf))
        if b is None: rows.append(f'   {area}: the new file could not be read: NOT COMPARED'); continue
        same = len(set(a) & set(b)); new = len(set(b) - set(a)); gone = sorted(set(a) - set(b))
        part = sum(1 for x in (read_spots(nf) or []) if isinstance(x, dict) and x.get('partial_boundary'))
        tot['same'] += same; tot['new'] += new; tot['gone'] += len(gone); tot['partial'] += part
        rows.append(f'   {area}: {same} same, {new} new, {len(gone)} gone, {part} marked "partial boundary"'
                    + ('   <<< LOOK: a pair the live file shows is not shown here: ' + ', '.join('+'.join(g[0]) for g in gone[:4]) if gone else ''))
    L += rows
    L += ['', f'   TOTAL over {len(rows)} area(s) this run measured: {tot["same"]} same, {tot["new"]} new, {tot["gone"]} gone, {tot["partial"]} partial-boundary rows']
    if tot['gone']: L += ['   *** NOT never-worse: some pairs the live files show are not shown by this run. Do not use it. ***']
    else: L += ['   never worse: every pair the live files show is still shown.']
    return L


def cmd_sync_pinned(a):
    """Nov 16: lay the shipped KPC-Data scripts down again, straight out of the PINNED KPC-Data commit, and check each one
    against pinned\\MANIFEST.json. 1-GET-CODE.bat calls this, so a pin that moves brings its code with it and a shipped copy
    can never quietly fall behind. Git hands over the repository's own bytes, which is what the manifest's sha256 is of."""
    s, pn = settings(a.settings), pins()
    kd = pathlib.Path(s.get('kpcdata_checkout') or '').resolve()
    commit = str(pn.get('kpc_data_commit') or '')
    man = load_json(HERE / 'pinned' / 'MANIFEST.json', {}) or {}
    want = {k: v for k, v in (man.get('files') or {}).items() if k.startswith('kpcdata/')}
    if not kd.is_dir():
        say(f'STOPPED: no KPC-Data checkout at {kd}.'); return 2
    if not commit or not want:
        say('STOPPED: pins.json or pinned\\MANIFEST.json is not readable.'); return 2
    wrote, same, bad = 0, 0, []
    for rel, sha in sorted(want.items()):
        inside = rel[len('kpcdata/'):]                       # .github/scripts/kpc_fers_states.py
        dst = HERE / 'pinned' / 'kpcdata' / pathlib.Path(inside)
        r = subprocess.run(['git', '-C', str(kd), 'show', f'{commit}:{inside}'], capture_output=True)
        if r.returncode or not r.stdout:
            bad.append(f'{inside} is not in KPC-Data at {commit[:12]}'); continue
        got = hashlib.sha256(r.stdout).hexdigest()
        if got != sha:
            bad.append(f'{inside}: the pinned commit holds {got[:16]}, the manifest wants {sha[:16]}'); continue
        if dst.is_file() and dst.read_bytes() == r.stdout:
            same += 1; continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(r.stdout); wrote += 1
    say(f'shipped KPC-Data code: {same} already right, {wrote} laid down again, from {commit[:12]}')
    for b in bad: say('   PROBLEM: ' + b)
    if bad:
        say('')
        say('Nothing was run. Either pins.json and pinned\\MANIFEST.json disagree, or that commit is not on this PC yet.')
        return 2
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('check', 'run', 'summary', 'sync-pinned', 'get-cache'):
        p = sub.add_parser(name)
        p.add_argument('--settings', default=str(HERE / 'settings.json'))
        if name == 'run':
            p.add_argument('--world', action='store_true')
            p.add_argument('--areas', default='')
            p.add_argument('--minutes', type=int, default=350)
            p.add_argument('--fresh', action='store_true')
    a = ap.parse_args(argv)
    return {'check': cmd_check, 'run': cmd_run, 'summary': cmd_summary, 'sync-pinned': cmd_sync_pinned, 'get-cache': cmd_get_cache}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""BEFORE / AFTER PROOF for any 2-fer line code change (chat 2, Oct 28 2026; Brandon 10:54 PM: 'item 2').
Runs Kentucky's SAVED bundle (no internet, no GitHub run, no email) through ALL the passes (1, 2, 3, 5) twice: with the OLD
code (a git ref, default origin/main) and with the NEW code (this working copy), then the known-answers test on both, and
compares every pair row by row. The change may go live only when:
  - the known answers still pass on the new code (19/19 today), and
  - every changed pair is one the fix was meant to change (the list is printed for a person to read).
usage (from the KPC-Links root):
  python3 .github/scripts/kpc_fers_proof.py [--old origin/main] [--bundle bundle-ky.tar.gz] [--work DIR] [--data ../kpc-data] [--parallel]
Writes DIR/proof.md (the short report) and prints it. Exit code 0 = PASS, 1 = FAIL (known answers lost on the new code)."""
import argparse, collections, json, os, pathlib, re, shutil, subprocess, sys, tarfile, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
ORDER = ['candidate', 'very tight', 'water only', 'not sure', 'dropped', 'merged', 'waiting', 'pass']


def sh(cmd, cwd=None, env=None, quiet=False):
    r = subprocess.run(cmd, cwd=cwd, env=env, shell=isinstance(cmd, str), capture_output=True, text=True)
    if r.returncode and not quiet: print(f'  ! {cmd if isinstance(cmd, str) else " ".join(cmd)}: {(r.stderr or r.stdout)[-300:]}', flush=True)
    return r


def get_bundle(work):
    """The newest Kentucky bundle from KPC-Data's release (REST only: GraphQL is blocked in Claude's sessions); kept for 24 h."""
    p = work / 'bundle-ky.tar.gz'
    if p.exists() and time.time() - p.stat().st_mtime < 86400: return p
    aid = sh(['gh', 'api', 'repos/KentuckyPortableClub/KPC-Data/releases/tags/fers-bundles', '--jq',
              '.assets[]|select(.name=="bundle-ky.tar.gz")|.id']).stdout.strip()
    if not aid: sys.exit('no bundle-ky.tar.gz on KPC-Data release fers-bundles')
    with open(p, 'wb') as f:
        subprocess.run(['gh', 'api', '-H', 'Accept: application/octet-stream', f'repos/KentuckyPortableClub/KPC-Data/releases/assets/{aid}'], stdout=f, check=True)
    return p


def make_side(side, ref, work, bundle, data):
    d = work / side
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    if ref:   # the OLD code: the repo as it is at that ref
        a = subprocess.run(['git', 'archive', ref], cwd=ROOT, capture_output=True, check=True).stdout
        subprocess.run(['tar', 'x'], cwd=d, input=a, check=True)
    else:     # the NEW code: this working copy (tracked files, as they are now)
        files = sh(['git', 'ls-files'], cwd=ROOT).stdout.split('\n')
        for f in files:
            if not f or not (ROOT / f).is_file(): continue
            q = d / f; q.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / f, q)
    sh(['bash', '.github/scripts/kpc_overlay.sh', str(data)], cwd=d, quiet=True)
    with tarfile.open(bundle) as t:
        t.extractall(d, members=[m for m in t.getmembers() if m.name.startswith(('bundle/http', 'bundle/water', 'data/fers'))])
    for f in (d / 'data/fers').glob('reuse-*'): f.unlink()   # every pair computed fresh on both sides
    return d


def run_side(d, log):
    env = dict(os.environ, HTTP_CACHE='bundle/http', HTTP_OFFLINE='1', HTTP_CACHE_DAYS='400', WATER_STORE='bundle/water',
               REGION='ky', STATES='US-KY', RUN_TAG='ky', MINUTES='60')
    env.pop('PARKS', None)
    t0 = time.time()
    for p in (1, 2, 3, 5):
        r = subprocess.run([sys.executable, '.github/scripts/kpc_fers.py'], cwd=d, env=dict(env, PASS=str(p)), capture_output=True, text=True)
        (d / f'p{p}.log').write_text(r.stdout + r.stderr)
        log(f'  {d.name}: pass {p} done ({time.time() - t0:.0f} s{", EXIT " + str(r.returncode) if r.returncode else ""})')
    r = subprocess.run([sys.executable, '.github/scripts/kpc_fers_known.py'], cwd=d, capture_output=True, text=True)
    m = re.search(r'(PASS|FAIL): (\d+) of (\d+)[^\n]*', r.stdout)
    return m.group(0) if m else 'known answers: no result'


def rows(d):
    out = {}
    for s in json.load(open(d / 'data/fers/US-KY.json')).get('spots') or []:
        st = str(s.get('status', ''))
        c = next((o for o in ORDER if st.startswith(o)), st[:15])
        k = ('+'.join(sorted(s.get('refs') or [])), s.get('kind'))
        if k not in out or (c in ORDER and (out[k][0] not in ORDER or ORDER.index(c) < ORDER.index(out[k][0]))):
            out[k] = (c, st, s.get('acres'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--old', default='origin/main'); ap.add_argument('--bundle'); ap.add_argument('--parallel', action='store_true')
    ap.add_argument('--work', default=os.environ.get('PROOF_WORK') or '/tmp/kpc-fers-proof'); ap.add_argument('--data', default=str(ROOT.parent / 'kpc-data'))
    a = ap.parse_args()
    work = pathlib.Path(a.work); work.mkdir(parents=True, exist_ok=True)
    log = lambda m: print(m, flush=True)
    sh(['git', 'fetch', '-q', 'origin'], cwd=ROOT, quiet=True)
    bundle = pathlib.Path(a.bundle) if a.bundle else get_bundle(work)
    log(f'bundle: {bundle} · old code: {a.old} · new code: this working copy')
    old = make_side('old', a.old, work, bundle, a.data); new = make_side('new', None, work, bundle, a.data)
    if a.parallel:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(2) as ex: ko, kn = ex.map(lambda d: run_side(d, log), (old, new))
    else: ko, kn = run_side(old, log), run_side(new, log)
    ro, rn = rows(old), rows(new)
    co, cn = collections.Counter(v[0] for v in ro.values()), collections.Counter(v[0] for v in rn.values())
    L = [f"# 2-fer code change: before / after on Kentucky's saved data ({time.strftime('%Y-%m-%d %H:%M')})", '',
         f'- old code `{a.old}`: {ko}', f'- new code (working copy): {kn}', '',
         '| status (one per pair + kind) | old | new |', '|---|---|---|']
    L += [f'| {k} | {co.get(k, 0)} | {cn.get(k, 0)} |' for k in ORDER if co.get(k) or cn.get(k)]
    ch = [(k, ro.get(k, ('-', '', None)), rn.get(k, ('-', '', None))) for k in sorted(set(ro) | set(rn)) if ro.get(k, ('-',))[0] != rn.get(k, ('-',))[0]]
    ac = [(k, ro[k][2], rn[k][2]) for k in sorted(set(ro) & set(rn)) if ro[k][0] == rn[k][0] and ro[k][2] and rn[k][2] and abs(ro[k][2] - rn[k][2]) > max(1.0, ro[k][2] * .05)]
    L += ['', f'## {len(ch)} pairs changed status'] + [f'- {k[0]} ({k[1]}): {o[0]} → {n[0]} · {(n[1] or o[1])[:120]}' for k, o, n in ch]
    if ac: L += ['', f'## {len(ac)} pairs changed size by more than 5%'] + [f'- {k[0]} ({k[1]}): {o} → {n} ac' for k, o, n in ac]
    ok = kn.startswith('PASS')
    L += ['', f"**{'PASS' if ok else 'FAIL'}**: " + ('known answers hold on the new code; read the changed pairs above: each must be one the fix was meant to change.'
                                                  if ok else 'the new code LOSES known answers: do not put it live.')]
    (work / 'proof.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

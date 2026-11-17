"""Nov 17 2026: a waiting-room release must save the DELETE of the held copy (data/waiting/in/<path>).

mode_release moves the held copy live and keeps the old live copy in data/waiting/previous/<path>. When the held copy and the old
live copy are alike, git's rename detection reads 'held copy deleted + previous copy added' as ONE rename. kpc_push_data.sh listed
changes with --diff-filter=AMR (names the new path only) and --diff-filter=D (empty for a rename), so the delete was never redone
on top of main and the held copy stayed (D4FF, KFF, ONFF, VEFF on Nov 17; PYFF's copies were not alike, so it saved right).
The fix lists with --no-renames. Throwaway repos only, no network. Run: python3 -B tests/test_save_release_delete_nov17.py"""
import json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PUSH = ROOT / '.github/scripts/kpc_push_data.sh'
ENV = {**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t', 'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t',
       'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'KPC_QUIET_HOURS': '0'}
fails = 0


def sh(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, env=ENV).stdout


def w(p, s):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s)


def check(name, ok):
    global fails
    print(('ok   ' if ok else 'FAIL ') + name)
    fails += 0 if ok else 1


def doc(n):   # a WWFF-directory-like file; two versions differ in one row, so git sees them as alike
    return json.dumps({'updated': '2026-11-17', 'refs': {f'XFF-{i:04d}': {'name': f'Park {i}', 'n': (n if i == 7 else i)} for i in range(60)}}, indent=1) + '\n'


with tempfile.TemporaryDirectory() as T:
    sh('git init -q --bare -b main origin.git && git clone -q origin.git a', T)
    a = f'{T}/a'
    held, live, prev = 'data/waiting/in/data/wwff/XFF.json', 'data/wwff/XFF.json', 'data/waiting/previous/data/wwff/XFF.json'
    w(f'{a}/{live}', doc(1)); w(f'{a}/{held}', doc(2)); w(f'{a}/data/waiting/in/data/wwff/YFF.json', doc(3))
    sh('git config diff.renames true && git add -A && git commit -qm base && git push -q origin HEAD:main', a)
    # what mode_release does on disk: old live -> previous, held -> live, held copy unlinked
    w(f'{a}/{prev}', doc(1)); w(f'{a}/{live}', doc(2)); pathlib.Path(f'{a}/{held}').unlink()
    sh('git add -A', a)
    check('the setup is the Nov 17 case: git reads the held delete as a rename to the previous copy',
          sh('git diff --cached --name-status', a).startswith('R'))
    sh('git reset -q', a)
    out = sh(f'bash {PUSH} . "waiting room: release {live}" data', a)
    tree = sh('git ls-tree -r --name-only origin/main', a).split() if not sh('git fetch -q origin', a) else []
    check(f'the release save removes the held copy from main ({out.strip()[-80:]})', held not in tree)
    check('the live file and the previous copy are saved', live in tree and prev in tree
          and sh(f'git show origin/main:{live}', a) == doc(2) and sh(f'git show origin/main:{prev}', a) == doc(1))
    check('the other held copy is untouched', 'data/waiting/in/data/wwff/YFF.json' in tree)
print(f'{4 - fails} of 4 right')
sys.exit(1 if fails else 0)

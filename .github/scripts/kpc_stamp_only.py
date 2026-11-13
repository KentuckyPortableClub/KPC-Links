#!/usr/bin/env python3
"""PR2 (fewer saves, Nov 2 2026): put back every STAGED file whose only change is a time stamp, so a quiet run commits nothing.
Run inside the repo after 'git add' and before 'git diff --cached --quiet' / 'git commit'.
A file counts as stamp-only when, compared with HEAD:
  JSON  - the only differences are in stamp keys (updated, updated_at, generated, generated_at, last_checked, checked_at, built, made, last_run; Nov 3) AND the
          stamp's DATE part did not change (so a file's 'updated' still moves once a day), or in GitHub run links (actions/runs/N),
          or in a 'build' id (Nov 3);
  text  (.md .txt .log, ONLY status-type files: a path with /status/ or a name with board, flow, heartbeat, summary, watchdog,
          health) - the only differences are clock times (12:34, 2026-11-02T12:34Z, '3 h old', '5 min ago') or run links; the dates
          themselves still count as a change. (Other text files may hold real times, e.g. opening hours, so they are never touched.)
The files are only put back when EVERY changed file is stamp-only: a run with one real change saves everything as before.
Anything else (new file, deleted file, unreadable, a real change) is left alone. Never fails. KPC_SAVE_STAMPS=keep switches it off."""
import json, os, re, subprocess, sys

STAMP = {'updated', 'updated_at', 'generated', 'generated_at', 'last_checked', 'checked_at', 'built', 'made', 'last_run'}   # Nov 3: + built, made, last_run
IDS = set()   # X5: a build id is material (key-check / key index); not ignored as a stamp
RUN = re.compile(r'actions/runs/\d+(/jobs?/\d+)?(/attempts/\d+)?')
CLOCK = [(re.compile(r'(\d{4}-\d\d-\d\d)[T ]\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:?\d\d| ?UTC| ?CST| ?CDT| ?CT)?'), r'\1'),
         (re.compile(r'\b\d{1,2}:\d\d(:\d\d)?( ?[AaPp]\.?[Mm]\.?)?( ?(UTC|CST|CDT|CT|Z))?\b'), 'HH:MM'),
         (re.compile(r'\b\d+(\.\d+)? ?(min|mins|minutes|h|hrs|hours|s|sec|seconds)( old| ago)\b'), 'N ago'),
         (RUN, 'actions/runs/N')]
TEXT = ('.md', '.txt', '.log')
STATUSY = re.compile(r'(^|/)status/|(board|flow|heartbeat|summary|watchdog|health)[^/]*$', re.I)


def norm(x, key=None):
    if isinstance(x, dict): return {k: norm(v, k) for k, v in x.items()}
    if isinstance(x, list): return [norm(v) for v in x]
    if isinstance(x, str):
        if key in IDS: return 'ID'
        if key in STAMP: return x[:10]   # the date part still counts
        return RUN.sub('actions/runs/N', x)
    return x


def text_norm(s):
    for rx, rep in CLOCK: s = rx.sub(rep, s)
    return s


def git(*a, binary=False):
    r = subprocess.run(['git', *a], capture_output=True)
    return r.returncode, (r.stdout if binary else r.stdout.decode('utf-8', 'replace'))


def stamp_only(f):
    rc, old = git('show', f'HEAD:{f}', binary=True)
    if rc != 0: return False
    rc, new = git('show', f':{f}', binary=True)   # the staged copy
    if rc != 0 or old == new: return False
    if len(old) > 60_000_000 or len(new) > 60_000_000: return False
    try: o, n = old.decode('utf-8'), new.decode('utf-8')
    except UnicodeDecodeError: return False
    if f.endswith(('.json', '.geojson')):
        try: return norm(json.loads(o)) == norm(json.loads(n))
        except ValueError: return False
    if f.endswith(TEXT) and STATUSY.search(f): return text_norm(o) == text_norm(n)
    return False


def main():
    if os.environ.get('KPC_SAVE_STAMPS') == 'keep': return
    rc, out = git('diff', '--cached', '--name-only', '-z', '--diff-filter=M')
    if rc != 0: return
    files = [f for f in out.split('\0') if f]
    if not files: return
    rc, other = git('diff', '--cached', '--name-only', '-z', '--diff-filter=ADRCT')   # added / deleted / renamed = a real change
    if rc != 0 or other.strip('\0'): return
    put_back = [f for f in files if stamp_only(f)]
    if len(put_back) != len(files):
        if put_back: print(f'stamp filter: {len(files) - len(put_back)} real change(s), so everything is saved as before')
        return
    for f in put_back:
        git('reset', '-q', 'HEAD', '--', f); git('checkout', '-q', 'HEAD', '--', f)
    if put_back:
        print(f"stamp filter: only time stamps changed ({len(put_back)} file(s): {' '.join(put_back)[:400]}), nothing to save")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f'stamp filter: failed ({type(e).__name__}: {str(e)[:120]}): the save stops')
        sys.exit(1)
    sys.exit(0)

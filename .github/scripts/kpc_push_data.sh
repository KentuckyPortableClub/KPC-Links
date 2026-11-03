#!/bin/bash
# Oct 27 (chat 2): ONE safe save for the KPC-Data bots. The Kentucky river-bank run lost its whole result: its 'pull --rebase'
# save failed 5 times while other bots pushed. This keeps ONLY the files this job changed, puts them on top of a fresh copy of
# main (no rebase, no conflicts) and pushes; a failure prints the git error as a notice. Never fails.
# STRICT=1 = exit 1 when the save failed (the run goes red and emails: the assembly line). Otherwise never fails.
# usage: kpc_push_data.sh <repo dir> "<commit message>" <path> [path…]   (paths to look for changes in, e.g. data)
cd "$1" || exit 0; shift; MSG="$1"; shift
git config user.name 'github-actions[bot]'; git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
# PR2 (fewer saves, Nov 2): a save whose only changes are time stamps / run links is skipped (KPC_SAVE_STAMPS=keep = off).
# The same code is .github/scripts/kpc_stamp_only.py; it is inline here because the KPC-Data bots fetch only this one file.
kpc_stamp_filter() {
python3 - <<'KPC_STAMP_PY' || true
"""PR2 (fewer saves, Nov 2 2026): put back every STAGED file whose only change is a time stamp, so a quiet run commits nothing.
Run inside the repo after 'git add' and before 'git diff --cached --quiet' / 'git commit'.
A file counts as stamp-only when, compared with HEAD:
  JSON  - the only differences are in stamp keys (updated, updated_at, generated, generated_at, last_checked, checked_at) AND the
          stamp's DATE part did not change (so a file's 'updated' still moves once a day), or in GitHub run links (actions/runs/N);
  text  (.md .txt .log, ONLY status-type files: a path with /status/ or a name with board, flow, heartbeat, summary, watchdog,
          health) - the only differences are clock times (12:34, 2026-11-02T12:34Z, '3 h old', '5 min ago') or run links; the dates
          themselves still count as a change. (Other text files may hold real times, e.g. opening hours, so they are never touched.)
The files are only put back when EVERY changed file is stamp-only: a run with one real change saves everything as before.
Anything else (new file, deleted file, unreadable, a real change) is left alone. Never fails. KPC_SAVE_STAMPS=keep switches it off."""
import json, os, re, subprocess, sys

STAMP = {'updated', 'updated_at', 'generated', 'generated_at', 'last_checked', 'checked_at'}
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
    try: main()
    except Exception as e: print(f'stamp filter: left everything alone ({type(e).__name__}: {str(e)[:120]})')  # noqa: BLE001
    sys.exit(0)
KPC_STAMP_PY
}
for p in "$@"; do git add -A -- "$p" 2>/dev/null; done   # Nov 1 (chat 10): one path at a time: ONE missing path (data/intake/found-layers-stage2.json) made git add nothing at all, so the world finder saved nothing since Oct 30
# B7 (Oct 30): file names are read NUL-separated, so a path with a space is one path, not two
mapfile -d '' CH < <(git diff --cached --name-only -z --diff-filter=AMR); mapfile -d '' DEL < <(git diff --cached --name-only -z --diff-filter=D)
[ ${#CH[@]} -eq 0 ] && [ ${#DEL[@]} -eq 0 ] && { echo "nothing changed"; exit 0; }
T=$(mktemp -d)
for f in "${CH[@]}"; do mkdir -p "$T/$(dirname "$f")" && cp -a "$f" "$T/$f"; done
for i in 1 2 3 4 5 6; do
  if git fetch -q --depth=1 origin main && git reset -q --hard FETCH_HEAD; then
    cp -a "$T"/. . 2>/dev/null
    for f in "${DEL[@]}"; do git rm -q --ignore-unmatch -- "$f" >/dev/null 2>&1; done
    [ ${#CH[@]} -gt 0 ] && git add -A -- "${CH[@]}" 2>/dev/null
    kpc_stamp_filter
    git diff --cached --quiet && { echo "nothing new to save"; exit 0; }
    git commit -qm "$MSG"
    ERR=$(git push -q origin HEAD:main 2>&1) && { echo "saved: ${#CH[@]} files"; exit 0; }
  else ERR="fetch failed"; fi
  WHY=$(echo "$ERR" | grep -v "Trace:" | grep -v "^remote: *$" | tr "\n" " "); echo "::notice title=Save try $i::${WHY:0:600}"   # Oct 29: the Alaska save hid its reason behind 6 Trace lines
  sleep $((i * 10))   # Oct 30: this wait had slipped into the comment above, so the 6 tries ran back to back
done
echo "::notice title=Save FAILED::${#CH[@]} files not saved"
[ "$STRICT" = 1 ] && exit 1   # the assembly line: a failed save = a red run (HQ Oct 27)
exit 0

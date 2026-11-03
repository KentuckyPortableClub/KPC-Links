#!/usr/bin/env bash
# SAVE BY OVERWRITE (Nov 2 2026 review, not yet switched on: needs a test build first).
# Why: BOT A's save ('git pull --rebase' then push, hidden by '|| true') failed on every run since Oct 30 ("cannot pull with rebase:
# You have unstaged changes"), so chat 11's answers were applied and then thrown away, and ruled pins came back. The monthly key
# save failed 6 times on rebase conflicts (Nov 1). A generated file never needs a merge: it is written again on top of the NEWEST
# main and pushed.
#
#   kpc_save_overwrite.sh [--copy] "<commit message>" "<redo command>|-" -- <paths...>
#
#   --copy   the files THIS run changed under <paths> (git status) are kept aside and copied back on top of the newest main
#            (for generated-only files: the US key state files, index, layers, review pages). Names in KPC_SAVE_SKIP
#            (space list, e.g. "data/us-key/overrides.json") are never copied back: hand-edited files are not overwritten.
#   redo     a command run after the copy-back on top of the newest main. BOT A passes its answers writers here, so a hand edit
#            to overrides.json made while the run was going is KEPT and the answers are applied on top of it. '-' = none.
#
# Switches (env):  KPC_SAVE_MODE  overwrite (default) | rebase (the old way, kept as a fallback; still loud on failure)
#                  KPC_SAVE_TRIES 5
#                  KPC_SAVE_RED   yes (default) = a save that never lands exits 1 (red job) | no = ::error only, exit 0 (the Oct 22
#                                 rule for the busy bots: a lost race is loud but does not email). Nov 2 review.
#                  KPC_SAVE_WORDS / KPC_SAVE_LINES (Nov 2 review, space lists): hand-kept files that are MERGED, not copied back:
#                    WORDS = a space list like answers-countries.txt (newest main's list - what this run took off + what it added),
#                    LINES = an inbox like .claude/inbox/chat-11.md (this run's new lines go into the newest copy). kpc_save_merge.py.
# Loud: a save that never lands prints ::error and exits 1 (the job goes red). Nothing is hidden with '|| true'.
set -u
copy=0; [ "${1:-}" = "--copy" ] && { copy=1; shift; }
msg=$1; redo=$2; shift 2; [ "${1:-}" = "--" ] && shift
tries=${KPC_SAVE_TRIES:-5}; mode=${KPC_SAVE_MODE:-overwrite}; skip=" ${KPC_SAVE_SKIP:-} ${KPC_SAVE_WORDS:-} ${KPC_SAVE_LINES:-} "
stash=$(mktemp -d); merge=$(mktemp -d)
here=$(dirname "$0")
if [ "$mode" != rebase ]; then
  [ -n "${KPC_SAVE_WORDS:-}" ] && python3 "$here/kpc_save_merge.py" keep "$merge" words $KPC_SAVE_WORDS
  [ -n "${KPC_SAVE_LINES:-}" ] && python3 "$here/kpc_save_merge.py" keep "$merge" lines $KPC_SAVE_LINES
fi
if [ "$copy" = 1 ]; then
  git status --porcelain --untracked-files=all -- "$@" | sed -E 's/^.. //; s/^"(.*)"$/\1/; s/.* -> //' | while IFS= read -r f; do
    case "$skip" in *" $f "*) continue ;; esac
    [ -f "$f" ] && mkdir -p "$stash/$(dirname "$f")" && cp -p "$f" "$stash/$f"
  done
fi
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
add_paths() { for p in "$@"; do [ -e "$p" ] && git add -A -- "$p"; done; return 0; }
for i in $(seq 1 "$tries"); do
  if [ "$mode" = rebase ]; then
    add_paths "$@"; [ "$i" = 1 ] && kpc_stamp_filter
    # Nov 2 review: after a lost race the commit is already made (nothing staged), so 'nothing staged' alone is not 'nothing changed'
    if git diff --cached --quiet && [ -z "$(git rev-list origin/main..HEAD 2>/dev/null)" ]; then echo "::notice title=Save::$msg: nothing changed"; exit 0; fi
    git diff --cached --quiet || git commit -qm "$msg" >/dev/null 2>&1 || echo "::warning title=Save::$msg: git commit said no (try $i)"
    if git pull -q --rebase --autostash && git push -q; then echo "::notice title=Save::$msg: saved (rebase, try $i)"; exit 0; fi
    git rebase --abort 2>/dev/null || true
  else
    if ! { git fetch -q origin main && git reset -q --hard origin/main; }; then sleep $((5 * i)); continue; fi
    if [ "$copy" = 1 ]; then (cd "$stash" && find . -type f -print) | while IFS= read -r f; do f=${f#./}; mkdir -p "$(dirname "$f")"; cp -p "$stash/$f" "$f"; done; fi
    python3 "$here/kpc_save_merge.py" apply "$merge"
    if [ "$redo" != "-" ]; then
      bash -c "$redo" || echo "::error title=Save::$msg: the redo step failed on try $i"
    fi
    add_paths "$@"; kpc_stamp_filter
    if git diff --cached --quiet; then echo "::notice title=Save::$msg: nothing to change on top of main"; exit 0; fi
    if git commit -qm "$msg" && git push -q origin HEAD:main; then echo "::notice title=Save::$msg: saved (overwrite, try $i)"; exit 0; fi
  fi
  sleep $((5 * i))
done
echo "::error title=Save::$msg was NOT saved after $tries tries (mode $mode)"
[ "${KPC_SAVE_RED:-yes}" = no ] && exit 0
exit 1

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
add_paths() { for p in "$@"; do [ -e "$p" ] && git add -A -- "$p"; done; return 0; }
for i in $(seq 1 "$tries"); do
  if [ "$mode" = rebase ]; then
    add_paths "$@"
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
    add_paths "$@"
    if git diff --cached --quiet; then echo "::notice title=Save::$msg: nothing to change on top of main"; exit 0; fi
    if git commit -qm "$msg" && git push -q origin HEAD:main; then echo "::notice title=Save::$msg: saved (overwrite, try $i)"; exit 0; fi
  fi
  sleep $((5 * i))
done
echo "::error title=Save::$msg was NOT saved after $tries tries (mode $mode)"
[ "${KPC_SAVE_RED:-yes}" = no ] && exit 0
exit 1

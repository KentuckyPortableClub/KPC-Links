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
# Loud: a save that never lands prints ::error and exits 1 (the job goes red). Nothing is hidden with '|| true'.
set -u
copy=0; [ "${1:-}" = "--copy" ] && { copy=1; shift; }
msg=$1; redo=$2; shift 2; [ "${1:-}" = "--" ] && shift
tries=${KPC_SAVE_TRIES:-5}; mode=${KPC_SAVE_MODE:-overwrite}; skip=" ${KPC_SAVE_SKIP:-} "
stash=$(mktemp -d)
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
    if git diff --cached --quiet; then echo "::notice title=Save::$msg: nothing changed"; exit 0; fi
    git commit -qm "$msg" >/dev/null 2>&1 || true
    if git pull -q --rebase --autostash && git push -q; then echo "::notice title=Save::$msg: saved (rebase, try $i)"; exit 0; fi
    git rebase --abort 2>/dev/null || true
  else
    if ! { git fetch -q origin main && git reset -q --hard origin/main; }; then sleep $((5 * i)); continue; fi
    if [ "$copy" = 1 ]; then (cd "$stash" && find . -type f -print) | while IFS= read -r f; do f=${f#./}; mkdir -p "$(dirname "$f")"; cp -p "$stash/$f" "$f"; done; fi
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
exit 1

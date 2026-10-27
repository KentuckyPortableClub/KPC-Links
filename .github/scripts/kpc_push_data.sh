#!/bin/bash
# Oct 27 (chat 2): ONE safe save for the KPC-Data bots. The Kentucky river-bank run lost its whole result: its 'pull --rebase'
# save failed 5 times while other bots pushed. This keeps ONLY the files this job changed, puts them on top of a fresh copy of
# main (no rebase, no conflicts) and pushes; a failure prints the git error as a notice. Never fails.
# STRICT=1 = exit 1 when the save failed (the run goes red and emails: the assembly line). Otherwise never fails.
# usage: kpc_push_data.sh <repo dir> "<commit message>" <path> [path…]   (paths to look for changes in, e.g. data)
cd "$1" || exit 0; shift; MSG="$1"; shift
git config user.name 'github-actions[bot]'; git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -A "$@" 2>/dev/null
CH=$(git diff --cached --name-only --diff-filter=AMR); DEL=$(git diff --cached --name-only --diff-filter=D)
[ -z "$CH$DEL" ] && { echo "nothing changed"; exit 0; }
T=$(mktemp -d)
for f in $CH; do mkdir -p "$T/$(dirname "$f")" && cp -a "$f" "$T/$f"; done
for i in 1 2 3 4 5 6; do
  if git fetch -q --depth=1 origin main && git reset -q --hard FETCH_HEAD; then
    cp -a "$T"/. . 2>/dev/null
    for f in $DEL; do git rm -q --ignore-unmatch "$f" >/dev/null 2>&1; done
    git add -A $CH 2>/dev/null
    git diff --cached --quiet && { echo "nothing new to save"; exit 0; }
    git commit -qm "$MSG"
    ERR=$(git push -q origin HEAD:main 2>&1) && { echo "saved: $(echo $CH | wc -w) files"; exit 0; }
  else ERR="fetch failed"; fi
  echo "::notice title=Save try $i::${ERR:0:300}"; sleep $((i * 10))
done
echo "::notice title=Save FAILED::$(echo $CH | wc -w) files not saved"
[ "$STRICT" = 1 ] && exit 1   # the assembly line: a failed save = a red run (HQ Oct 27)
exit 0

#!/bin/bash
# Oct 27 (chat 2): ONE safe save for the KPC-Data bots. The Kentucky river-bank run lost its whole result: its 'pull --rebase'
# save failed 5 times while other bots pushed. This keeps ONLY the files this job changed, puts them on top of a fresh copy of
# main (no rebase, no conflicts) and pushes; a failure prints the git error as a notice. Never fails.
# STRICT=1 = exit 1 when the save failed (the run goes red and emails: the assembly line). Otherwise never fails.
# usage: kpc_push_data.sh <repo dir> "<commit message>" <path> [path…]   (paths to look for changes in, e.g. data)
cd "$1" || exit 0; shift; MSG="$1"; shift
git config user.name 'github-actions[bot]'; git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -A "$@" 2>/dev/null
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

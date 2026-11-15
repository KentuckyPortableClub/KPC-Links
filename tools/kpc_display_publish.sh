#!/usr/bin/env bash
# kpc_display_publish.sh (KPC owner, 2026-11-14): publish built display-copy areas to the map-display branch, safely.
#
#   tools/kpc_display_publish.sh REMOTE NEW_DIR AREA [AREA ...]
#     REMOTE   the repository (an https address, or a local path in tests)
#     NEW_DIR  the build output (NEW_DIR/<AREA>/INDEX.json ... from tools/kpc_display_copy.py build)
#     AREA     the areas of this run (a park's areas are built and published together)
#
# What it does, in order. Any problem stops it before the push, and then nothing on the remote changes.
#   1. Reads what is published now. Branch missing = first publish (start empty). The remote cannot be read = STOP (a network
#      failure must never publish a tree that lacks the other areas).
#   2. Fetches that commit (depth 1) and checks it is exactly the one listed; unpacks it.
#   3. Replaces only the areas of this run.
#   4. Checks EVERY area in the new tree with `kpc_display_copy.py check --public` (every file listed, present, under its cap,
#      sha as listed, no preview stamp, no private words) and that nothing but area folders is at the top.
#   5. Makes ONE new commit (no history) and pushes it with ONE atomic push: map-display moves to it only if it still points at
#      the commit read in step 1 (a lease), and map-display-prev moves to that old commit, from the same local repository that
#      holds it. Both move or neither does.
# It never touches any other branch. Old copies: the previous commit stays on map-display-prev until the next publish.
set -euo pipefail
if [ $# -lt 3 ]; then echo "usage: $0 REMOTE NEW_DIR AREA [AREA ...]" >&2; exit 2; fi
REMOTE=$1; NEW=$2; shift 2
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${PYTHON:-python3}
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
git init -q "$WORK/repo"
G() { git -C "$WORK/repo" -c user.name="KPC owner" -c user.email="KentuckyPortableClub@users.noreply.github.com" -c commit.gpgsign=false "$@"; }
mkdir "$WORK/tree"

# 1-2. what is published now
set +e; LS=$(git ls-remote --exit-code "$REMOTE" refs/heads/map-display 2>"$WORK/ls.err"); RC=$?; set -e
if [ "$RC" -eq 0 ]; then
  OLD=${LS%%[[:space:]]*}
  G fetch -q --no-tags --depth 1 "$REMOTE" refs/heads/map-display || { echo "STOP: could not fetch map-display: nothing published" >&2; exit 1; }
  GOT=$(G rev-parse FETCH_HEAD)
  [ "$GOT" = "$OLD" ] || { echo "STOP: map-display moved while reading it ($OLD -> $GOT): nothing published" >&2; exit 1; }
  G archive "$OLD" | tar -x -C "$WORK/tree"
elif [ "$RC" -eq 2 ]; then
  OLD=""                                   # the branch does not exist yet: the first publish
else
  echo "STOP: cannot read $REMOTE (git ls-remote exit $RC): nothing published" >&2; cat "$WORK/ls.err" >&2; exit 1
fi

# 3. this run's areas replace theirs
for A in "$@"; do
  [[ "$A" =~ ^((US|CA)-[A-Z]{2,3}|W-[A-Z]{2})$ ]] || { echo "STOP: bad area name $A" >&2; exit 1; }
  [ -f "$NEW/$A/INDEX.json" ] || { echo "STOP: $NEW/$A/INDEX.json is missing: nothing published" >&2; exit 1; }
  rm -rf "${WORK:?}/tree/$A"; cp -R "$NEW/$A" "$WORK/tree/$A"
done

# 4. every area of the new tree must pass the public check; nothing else at the top
for D in "$WORK"/tree/* "$WORK"/tree/.[!.]*; do
  [ -e "$D" ] || continue
  N=$(basename "$D")
  [ -d "$D" ] && [[ "$N" =~ ^((US|CA)-[A-Z]{2,3}|W-[A-Z]{2})$ ]] || { echo "STOP: $N is not an area folder: nothing published" >&2; exit 1; }
  "$PY" "$HERE/kpc_display_copy.py" check --out "$WORK/tree" --area "$N" --public >"$WORK/check.txt" 2>&1 \
    || { echo "STOP: $N fails its check: nothing published" >&2; cat "$WORK/check.txt" >&2; exit 1; }
done

# 5. one commit, one atomic push
G --work-tree="$WORK/tree" add -A
G --work-tree="$WORK/tree" commit -q -m "Display copy: $* ($(date -u +%F))"
NEWC=$(G rev-parse HEAD)
if [ -n "$OLD" ]; then
  G push -q --atomic --force-with-lease="refs/heads/map-display:$OLD" "$REMOTE" "$NEWC:refs/heads/map-display" "+$OLD:refs/heads/map-display-prev"
else
  G push -q --atomic --force-with-lease="refs/heads/map-display:" "$REMOTE" "$NEWC:refs/heads/map-display"
fi
echo "published $NEWC to map-display (previous: ${OLD:-none}); areas of this run: $*"

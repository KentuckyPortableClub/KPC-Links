#!/usr/bin/env bash
# KPC-Archive store (Nov 9 2026 evening; Brandon t909u: saved outlines + saved 2-fer answers kept in KPC-Archive).
#   kpc_archive.sh get <dir> <dest> <name-glob>...   copy <dir>/<glob> from the archive into <dest>
#   kpc_archive.sh put <dir> <message> <file>...     add the files under <dir> and push to the archive's main (5 tries, rebase between)
# Exit 0 = done; 2 = not available (no KPC_ARCHIVE_TOKEN, clone failed, or nothing there): the caller falls back to the release
# copy with a warning, never a failure; 1 = the push failed after 5 tries. A file over 95 MB is never put in git (GitHub refuses
# 100 MB): it is named in a warning and left to the release copy. The token needs Contents: read and write on KPC-Archive only.
set -u
REPO="${KPC_ARCHIVE_REPO:-KentuckyPortableClub/KPC-Archive}"
cmd="${1:-}"; dir="${2:-}"; shift 2 2>/dev/null || { echo "usage: kpc_archive.sh get|put <dir> ..."; exit 2; }
if [ -z "${KPC_ARCHIVE_TOKEN:-}" ]; then
  echo "::warning title=KPC-Archive::secret KPC_ARCHIVE_TOKEN is not set in this repo; using the release copy instead ($cmd $dir)"; exit 2
fi
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
if ! git -c credential.helper= clone -q --depth 1 --filter=blob:none --no-checkout "${KPC_ARCHIVE_URL:-https://x-access-token:${KPC_ARCHIVE_TOKEN}@github.com/${REPO}.git}" "$W/a" 2>"$W/err" \
   || ! git -C "$W/a" sparse-checkout set --no-cone "/$dir/" 2>>"$W/err" || ! git -C "$W/a" checkout -q 2>>"$W/err"; then
  echo "::warning title=KPC-Archive::could not read $REPO (check KPC_ARCHIVE_TOKEN); using the release copy instead ($cmd $dir)"; exit 2
fi
case "$cmd" in
  get)
    dest="$1"; shift; mkdir -p "$dest"; n=0
    for g in "$@"; do for f in "$W/a/$dir"/$g; do [ -f "$f" ] && cp -f "$f" "$dest/" && n=$((n + 1)); done; done
    echo "KPC-Archive: $n file(s) from $dir"; [ "$n" -gt 0 ] || exit 2 ;;
  put)
    msg="$1"; shift; mkdir -p "$W/a/$dir"; big=""
    for f in "$@"; do
      [ -f "$f" ] || continue
      if [ "$(stat -c %s "$f")" -gt "${KPC_ARCHIVE_MAX:-95000000}" ]; then big="$big $(basename "$f")"; continue; fi
      cp -f "$f" "$W/a/$dir/"
    done
    [ -n "$big" ] && echo "::warning title=KPC-Archive::too big for git (over 95 MB), kept on the release only:$big"
    cd "$W/a" || exit 1
    git add -A "$dir"
    if git diff --cached --quiet; then echo "KPC-Archive: nothing new in $dir"; exit 0; fi
    git -c user.name='kpc-bot' -c user.email='kpc-bot@users.noreply.github.com' commit -qm "$msg"
    for i in 1 2 3 4 5; do
      git push -q origin HEAD:main 2>/dev/null && { echo "KPC-Archive: saved $(git show --stat --format= HEAD | tail -1) in $dir"; exit 0; }
      sleep $((i * 5)); git pull -q --rebase origin main 2>/dev/null || true
    done
    echo "::error title=KPC-Archive::push to $REPO failed 5 times ($dir)"; exit 1 ;;
  *) echo "usage: kpc_archive.sh get|put <dir> ..."; exit 2 ;;
esac

#!/usr/bin/env bash
# kpc_live_spots_push.sh (KPC owner, 2026-11-16, handoff item 7, v5): save the club spot file on its OWN data-only branch.
#   bash .github/scripts/kpc_live_spots_push.sh [data/pota/spots.json]
# Each call adds ONE ordinary commit to live-spots (parent = the branch's current tip; the very first call makes the branch) with
# spots.json and a short README, built with git plumbing from the file alone (the checkout, its branch and main are not touched),
# and pushes it as a normal fast-forward. No force-push, ever: when the push is refused the tip is fetched again and the commit is
# made again on top of it. The push uses the job's own GITHUB_TOKEN, so it starts no workflow, and live-spots is not the Pages
# branch, so no Pages build is triggered. Readers use the raw file address:
#   https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Links/live-spots/spots.json
set -euo pipefail
f="${1:-data/pota/spots.json}"
[ -s "$f" ] || { echo "::warning title=Club spot file::$f is missing or empty: not published"; exit 1; }
[ "$(wc -c < "$f")" -le 1000000 ] || { echo "::warning title=Club spot file::$f is over 1 MB: not published"; exit 1; }
readme=$(printf 'Data-only branch: the club spot file (POTA spots, read once per 5 minutes by the one club reader).\nOne ordinary commit per read. Never merged; no site build.\n' | git hash-object -w --stdin)
blob=$(git hash-object -w "$f")
tree=$(printf '100644 blob %s\tREADME.md\n100644 blob %s\tspots.json\n' "$readme" "$blob" | git mktree)
for i in 1 2 3; do
  parent=()
  if git fetch -q --depth=1 origin "+refs/heads/live-spots:refs/remotes/origin/live-spots" 2>/dev/null; then
    parent=(-p "$(git rev-parse refs/remotes/origin/live-spots)")
  fi
  commit=$(GIT_AUTHOR_NAME='KPC owner' GIT_AUTHOR_EMAIL='KentuckyPortableClub@users.noreply.github.com' \
           GIT_COMMITTER_NAME='KPC owner' GIT_COMMITTER_EMAIL='KentuckyPortableClub@users.noreply.github.com' \
           git commit-tree "$tree" "${parent[@]}" -m 'Club spot file' -m "KPC owner, $(date -u +%Y-%m-%d)")
  if git push -q origin "$commit:refs/heads/live-spots" 2>/dev/null; then exit 0; fi
  sleep $((i * 5))
done
echo "::warning title=Club spot file::not published this check (push refused); the next check tries again"
exit 1

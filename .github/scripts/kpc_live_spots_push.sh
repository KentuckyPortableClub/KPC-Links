#!/usr/bin/env bash
# kpc_live_spots_push.sh (KPC owner, 2026-11-16, handoff item 7, v4 answer 4): publish the club spot file on its OWN data-only branch.
#   bash .github/scripts/kpc_live_spots_push.sh [data/pota/spots.json]
# The branch live-spots holds ONE commit with spots.json (and a short README), replaced on every check: a new root commit (no parent)
# is made with git plumbing from the file alone (the checkout, its branch and main are not touched) and pushed with a forced update
# to refs/heads/live-spots. The forced update is allowed on this one data-only branch ONLY; the target is fixed here and nothing
# else is ever force-pushed. The push uses the job's own GITHUB_TOKEN, so it starts no workflow, and live-spots is not the Pages
# branch, so no Pages build is triggered. Readers use the raw file address:
#   https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Links/live-spots/spots.json
set -euo pipefail
f="${1:-data/pota/spots.json}"
[ -s "$f" ] || { echo "::warning title=Club spot file::$f is missing or empty: not published"; exit 1; }
[ "$(wc -c < "$f")" -le 1000000 ] || { echo "::warning title=Club spot file::$f is over 1 MB: not published"; exit 1; }
readme=$(printf 'Data-only branch: the club spot file (POTA spots, read once per 5 minutes by the one club reader).\nOne commit, replaced on every check. Never merged; no site build.\n' | git hash-object -w --stdin)
blob=$(git hash-object -w "$f")
tree=$(printf '100644 blob %s\tREADME.md\n100644 blob %s\tspots.json\n' "$readme" "$blob" | git mktree)
commit=$(GIT_AUTHOR_NAME='KPC owner' GIT_AUTHOR_EMAIL='KentuckyPortableClub@users.noreply.github.com' \
         GIT_COMMITTER_NAME='KPC owner' GIT_COMMITTER_EMAIL='KentuckyPortableClub@users.noreply.github.com' \
         git commit-tree "$tree" -m 'Club spot file (replaced on every check)' -m "KPC owner, $(date -u +%Y-%m-%d)")
for i in 1 2 3; do
  if git push -q --force origin "$commit:refs/heads/live-spots" 2>/dev/null; then exit 0; fi
  sleep $((i * 5))
done
echo "::warning title=Club spot file::not published this check (push refused); the next check tries again"
exit 1

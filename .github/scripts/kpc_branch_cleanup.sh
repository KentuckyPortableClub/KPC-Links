#!/usr/bin/env bash
# Nov 19 2026 (Brandon 6:12 PM 'Do the bot then'): ONE-TIME branch clean-up. Deletes only the branches named in
# .github/branch-cleanup-nov19.txt (name + the tip it had when it was listed), and only when ALL of these hold:
#   - it is not on the keep-list (main, tools-out, intake-files, lookup, picture-maps, engine-registry, opus/*)
#   - no open pull request uses it (as the branch or as the base)
#   - its tip is still the listed one (nothing was added since Nov 19)
# DRY=1 only says what it would do. Never touches main, never rewrites history. A deleted branch of a merged pull
# request can be brought back with the 'Restore branch' button on that pull request.
set -u
REPO="${GITHUB_REPOSITORY:?}"; LIST="${LIST:-.github/branch-cleanup-nov19.txt}"; DRY="${DRY:-1}"
KEEP=" main tools-out intake-files lookup picture-maps engine-registry "
OPEN="$(gh api "repos/$REPO/pulls?state=open&per_page=100" --paginate --jq '.[]|.head.ref,.base.ref')" || { echo "::error title=Branch clean-up::could not read the open pull requests: nothing deleted"; exit 1; }
gone=0; kept=0; fail=0
while read -r b sha; do
  [ -z "${b:-}" ] && continue; case "$b" in \#*) continue;; esac
  if [[ "$KEEP" == *" $b "* || "$b" == opus/* ]]; then echo "KEEP  $b (keep-list)"; kept=$((kept+1)); continue; fi
  if grep -qxF -- "$b" <<<"$OPEN"; then echo "KEEP  $b (open pull request)"; kept=$((kept+1)); continue; fi
  now="$(gh api "repos/$REPO/git/ref/heads/$b" --jq '.object.sha' 2>/dev/null || true)"
  if ! [[ "$now" =~ ^[0-9a-f]{40}$ ]]; then echo "GONE  $b (not there: already deleted)"; continue; fi
  if [ "$now" != "$sha" ]; then echo "KEEP  $b (new commits since the list was made)"; kept=$((kept+1)); continue; fi
  if [ "$DRY" = "1" ]; then echo "WOULD DELETE $b"; gone=$((gone+1)); continue; fi
  if gh api -X DELETE "repos/$REPO/git/refs/heads/$b" >/dev/null 2>&1; then echo "DELETED $b ($sha)"; gone=$((gone+1)); else echo "FAILED $b"; fail=$((fail+1)); fi
done < "$LIST"
[ "$DRY" = "1" ] && W="would be deleted (dry run)" || W="deleted"
echo "::notice title=Branch clean-up::$gone $W, $kept kept, $fail failed"
[ "$fail" -eq 0 ]

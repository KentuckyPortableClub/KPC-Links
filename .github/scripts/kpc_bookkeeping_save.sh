#!/usr/bin/env bash
# BOOKKEEPING SAVE (Nov 3 2026, Brandon YES 5:29 PM: "watchdogs stop saving bookkeeping to main on every run").
# The watchdog's own notes (data/status/watchdog.json, its board lines) used to be committed to main every time it restarted
# something: up to 24 commits a day per repo that only say "I looked". Now:
#   - every run: the notes go to the branch 'kpc-bookkeeping' (never main; it only carries these status files), and the run summary;
#   - main gets them ONCE A DAY (the 08 UTC slot, = 2 AM CST) or AT ONCE when a board line turns amber/red (an alarm must reach
#     the status board fast);
#   - repo variable KPC_BOOKKEEPING=main = the old way (every save to main).
# Usage (inside the repo, after the bot ran):  bash kpc_bookkeeping_save.sh "<commit message>" <path> [<path> ...]
# Restore before the bot runs (so the bot remembers what it did since main last got the notes):
#   bash kpc_bookkeeping_save.sh --restore <file> [<file> ...]
# Red when a save never lands (same as before).
set -u
BR="${KPC_BOOKKEEPING_BRANCH:-kpc-bookkeeping}"
if [ "${1:-}" = "--restore" ]; then
  shift
  git fetch -q origin "$BR" 2>/dev/null || { echo "bookkeeping: no '$BR' branch yet, main's copy is used"; exit 0; }
  for f in "$@"; do
    if git cat-file -e "FETCH_HEAD:$f" 2>/dev/null; then mkdir -p "$(dirname "$f")"; git show "FETCH_HEAD:$f" > "$f"; echo "bookkeeping: $f read from '$BR'"; fi
  done
  exit 0
fi
MSG="$1"; shift
git config user.name 'github-actions[bot]'; git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git add -- "$@" 2>/dev/null || true
python3 .github/scripts/kpc_stamp_only.py || true   # a look that only moved a time stamp saves nothing
git diff --cached --quiet && { echo "bookkeeping: nothing new"; exit 0; }
# Where to: main (daily slot / alarm / KPC_BOOKKEEPING=main) or the branch
to_main=no; why=''
[ "${KPC_BOOKKEEPING:-branch}" = main ] && { to_main=yes; why='KPC_BOOKKEEPING=main'; }
if [ "$to_main" = no ] && [ "$(date -u +%H)" = 08 ] && [ "$(date -u +%M | sed 's/^0//')" -lt 30 ]; then to_main=yes; why='the daily 08 UTC save'; fi
if [ "$to_main" = no ]; then
  alarm=$(python3 - <<'PY' 2>/dev/null || true
import json, subprocess
def load(spec):
    r = subprocess.run(['git', 'show', spec], capture_output=True, text=True)
    try: return json.loads(r.stdout) if r.returncode == 0 else {}
    except ValueError: return {}
names = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True).stdout.split()
for f in names:
    if not (f.endswith('board.json') or '/status/bots/' in f): continue
    old, new = load(f'HEAD:{f}'), load(f':{f}')
    rows_o = old.get('bots', {'_': old}) if isinstance(old, dict) else {}
    rows_n = new.get('bots', {'_': new}) if isinstance(new, dict) else {}
    for k, r in rows_n.items():
        if isinstance(r, dict) and r.get('result') in ('red', 'amber') and (rows_o.get(k) or {}).get('result') != r.get('result'):
            print(k); raise SystemExit(0)
PY
)
  [ -n "$alarm" ] && { to_main=yes; why="a board line turned $alarm amber/red"; }
fi
if [ "$to_main" = yes ]; then
  git commit -qm "$MSG"
  for i in 1 2 3 4; do
    if git pull -q --rebase --autostash origin main && git push -q origin HEAD:main; then
      echo "::notice title=Bookkeeping::saved to main ($why)"; exit 0; fi
    git rebase --abort 2>/dev/null || true; sleep $((i*6))
  done
  echo "::error title=Save::the bookkeeping save to main did not land after 4 tries; the next run tries again"; exit 1
fi
# The branch: copy the changed files onto the newest 'kpc-bookkeeping' (made from main the first time)
tmp=$(mktemp -d); files=$(git diff --cached --name-only)
for f in $files; do mkdir -p "$tmp/$(dirname "$f")"; cp "$f" "$tmp/$f"; done
git reset -q
for i in 1 2 3 4; do
  if git fetch -q origin "$BR" 2>/dev/null; then git checkout -q -f -B "$BR" FETCH_HEAD; else git checkout -q -f -B "$BR" "$(git rev-parse HEAD)"; fi
  for f in $files; do mkdir -p "$(dirname "$f")"; cp "$tmp/$f" "$f"; git add -- "$f"; done
  git diff --cached --quiet && { echo "bookkeeping: '$BR' already has these notes"; exit 0; }
  git commit -qm "$MSG (bookkeeping, not main)"
  if git push -q origin "HEAD:refs/heads/$BR"; then
    echo "::notice title=Bookkeeping::saved to branch '$BR', not main ($(echo $files | wc -w) file(s)); main gets them at the 08 UTC save or on an alarm"
    [ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "**Bookkeeping:** saved to branch \`$BR\` (not main): $files" >> "$GITHUB_STEP_SUMMARY"
    exit 0
  fi
  sleep $((i*6))
done
echo "::error title=Save::the bookkeeping save to '$BR' did not land after 4 tries; the next run tries again"; exit 1

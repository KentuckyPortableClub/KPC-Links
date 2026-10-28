#!/bin/bash
# Step B (chat 2, Oct 27; chat 8's old-way readers hunt): lay KPC-Data's copies of the MOVED paths (.github/kpc-moved.txt) over
# this KPC-Links checkout, so every bot reads the one true copy. Read only: nothing is ever saved back to KPC-Links (the moved
# folders are in .gitignore). usage: kpc_overlay.sh [existing KPC-Data clone]   (no argument = a small sparse clone of only
# the moved paths). Oct 28 (HQ): FAILS LOUDLY (red run) when KPC-Data cannot be read or a moved path comes out missing or
# empty: a bot must never run on nothing. Call it WITHOUT '|| true'.
LIST=$(grep -v '^\s*#' .github/kpc-moved.txt 2>/dev/null | grep -v '^\s*$')
[ -z "$LIST" ] && exit 0
D="$1"
if [ -z "$D" ]; then
  D=.kpcdata; rm -rf "$D"
  git clone -q --depth 1 --filter=blob:none --no-checkout https://github.com/KentuckyPortableClub/KPC-Data "$D" 2>/dev/null \
    && git -C "$D" sparse-checkout set --no-cone $LIST 2>/dev/null && git -C "$D" checkout -q 2>/dev/null \
    || { echo "::error title=Overlay::KPC-Data could not be read: the moved park data is missing, so this bot stops"; exit 1; }
fi
n=0
for p in $LIST; do
  if [ -d "$D/$p" ]; then rm -rf "$p" && mkdir -p "$(dirname "$p")" && cp -a "$D/$p" "$p" && n=$((n+1))
  elif [ -f "$D/$p" ]; then mkdir -p "$(dirname "$p")" && cp -a "$D/$p" "$p" && n=$((n+1)); fi
done
# until the old copies are deleted here (B6 part 2) they are still tracked: tell git to ignore the overlaid files, so a bot's
# 'git pull --rebase' / 'git add' never trips on them or saves them back
git ls-files -z -- $LIST 2>/dev/null | xargs -0 -r git update-index --skip-worktree 2>/dev/null
echo "overlay: $n moved paths laid over from KPC-Data"
bad=""
for p in $LIST; do
  if [ -d "$p" ]; then [ -n "$(ls -A "$p" 2>/dev/null)" ] || bad="$bad $p"
  elif [ ! -s "$p" ]; then bad="$bad $p"; fi
done
[ -n "$bad" ] && { echo "::error title=Overlay::missing or EMPTY after the overlay:$bad (KPC-Data). This bot stops rather than run on nothing"; exit 1; }
exit 0

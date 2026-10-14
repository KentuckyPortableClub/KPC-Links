#!/bin/sh
# Rebuild the five KPC web guides from the main files in this folder. Run from anywhere.
# Sources: <name>.main.html in this folder (placeholders @@HEAD@@ @@DISCLAIM@@ plus assemble.py ones). Writes the 5 kpc-guide-*.html pages.
S=$(dirname "$(readlink -f "$0")"); R=/home/claude/kpc-links
cd "$R" || exit 1
b() { python3 - "$S/$1.main.html" "$S/$1.tmp.html" "$S" "$2" <<'PY'
import sys
src,out,S,page=sys.argv[1:5]
t=open(src,encoding='utf-8').read()
t=t.replace('@@HEAD@@',open(S+'/head.html',encoding='utf-8').read().rstrip()).replace('@@DISCLAIM@@',open(S+'/disclaim.html',encoding='utf-8').read().rstrip())
open(out,'w',encoding='utf-8').write(t)
PY
python3 .claude/build/assemble.py "$S/$1.tmp.html" "$2" "$3" "$4"; }
b tools kpc-guide-tools-links.html "Tools & Essential Links | KPC" "KPC field-use reference: ham radio, POTA, propagation, weather, Kentucky parks and public lands, and portable antenna links."
b founders kpc-guide-founders-favorites.html "Founders Favorites: Apps & Tools | KPC" "The KPC founders' favorite apps and tools for POTA mapping, ham radio station work and Kentucky public lands."
b beginners kpc-guide-beginners.html "Beginner's Guide to Portable Operations | KPC" "A simple, practical starting point for portable ham radio: find an Elmer, build a simple station, set up your antenna and make your first POTA activation."
b antenna kpc-guide-antenna-efficiency.html "Antenna Efficiency & the Solar Minimum | KPC" "Why antenna efficiency matters more during the solar minimum, which modes and antennas help, and a KPC field checklist for portable operators."
b safety kpc-guide-safety.html "Portable Operations Safety Guide | KPC" "Outdoor safety for portable radio in Kentucky: power lines, lightning and weather, venomous snakes, poisonous plants, ticks, and WMA hunting seasons."

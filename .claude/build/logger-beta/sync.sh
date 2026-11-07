#!/bin/bash
# KPC Logger BETA on the website = the app's own screens (Brandon Oct 26 8:40 PM: 'put the app itself on the site').
# Copies kpc-app/www into kpc-links/logger-beta/, leaves out the remote + the builders' test screen, renames index.html to
# kpc-logger-beta.html (members-only: not on the gate's PUBLIC list) and adds the website bits (gate, noindex, kpc-web.js/css).
# Run after an app change:  bash .claude/build/logger-beta/sync.sh /home/claude/kpc-app
set -e
APP=${1:-/home/claude/kpc-app}; HERE=$(cd "$(dirname "$0")" && pwd); SITE=$(cd "$HERE/../../.." && pwd); OUT=$SITE/logger-beta
mkdir -p "$OUT"
find "$OUT" -mindepth 1 -maxdepth 1 ! -name 'kpc-web.js' ! -name 'kpc-web.css' ! -name 'index.html' -exec rm -rf {} +
( cd "$APP/www" && tar cf - --exclude=kpc-remote.js --exclude=test.js --exclude=radio-check.html --exclude=check.css --exclude=FROM-WEBSITE-COMMIT.txt --exclude=index.html . ) | ( cd "$OUT" && tar xf - )
cp "$HERE/kpc-web.js" "$HERE/kpc-web.css" "$OUT/"
python3 - "$APP/www/index.html" "$OUT/kpc-logger-beta.html" <<'PY'
import sys,re
s=open(sys.argv[1]).read()
s=s.replace('<meta charset="utf-8">','<meta charset="utf-8">\n<meta name="robots" content="noindex,nofollow">\n<script src="../kpc-gate.js"></script>',1)
s=s.replace('<title>KPC</title>','<title>KPC Logger (beta) | KPC</title>',1)
s=re.sub(r'(<link rel="stylesheet" href="app\.css[^"]*">)',r'\1\n<link rel="stylesheet" href="kpc-web.css?v=W">',s,count=1)
s=re.sub(r'<script src="kpc-remote\.js[^"]*"></script>\n?','',s)
s=re.sub(r'<script>[^<\n]*document\.write\(\'<script src="kpc-remote\.js[^\n]*</script>\n?','',s)   # Nov 7: the app loads it with document.write now
s=re.sub(r'<script src="capacitor\.js"></script>\n?','',s)   # Nov 7: Android-only bridge, a 404 on the website
s=s.replace('</body>','<script src="kpc-web.js?v=W"></script>\n</body>',1)
open(sys.argv[2],'w').write(s)
PY
V=$(date +%Y%m%d%H%M); sed -i "s/?v=W\"/?v=$V\"/g" "$OUT/kpc-logger-beta.html"
cat > "$OUT/index.html" <<'H'
<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>KPC Logger (beta)</title><meta http-equiv="refresh" content="0;url=kpc-logger-beta.html"><a href="kpc-logger-beta.html">KPC Logger (beta)</a>
H
C=$(git -C "$APP" rev-parse --short HEAD 2>/dev/null || cat "$APP/SOURCE-COMMIT.txt" 2>/dev/null || echo unknown); D=$(git -C "$APP" log -1 --format=%cs 2>/dev/null || date +%F)
echo "app commit $C $D" > "$OUT/FROM-APP-COMMIT.txt"   # Nov 7: works from a zip copy of the app too (SOURCE-COMMIT.txt)
echo "logger-beta synced from app $(cat "$OUT/FROM-APP-COMMIT.txt")"

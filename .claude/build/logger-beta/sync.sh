#!/bin/bash
# KPC Logger BETA on the website = the app's own screens (Brandon Oct 26 8:40 PM: 'put the app itself on the site').
# Copies kpc-app/www into kpc-links/logger-beta/, leaves out the remote + the builders' test screen, renames index.html to
# kpc-logger-beta.html (members-only: not on the gate's PUBLIC list) and adds the website bits (gate, noindex, kpc-web.js/css).
# Run after an app change:  bash .claude/build/logger-beta/sync.sh /home/claude/kpc-app
set -e
APP=${1:-/home/claude/kpc-app}; HERE=$(cd "$(dirname "$0")" && pwd); SITE=$(cd "$HERE/../../.." && pwd); OUT=$SITE/logger-beta
mkdir -p "$OUT"
find "$OUT" -mindepth 1 -maxdepth 1 ! -name 'kpc-web.js' ! -name 'kpc-web.css' ! -name 'kpc-web-pre.js' ! -name 'index.html' -exec rm -rf {} +
( cd "$APP/www" && tar cf - --exclude=kpc-remote.js --exclude=test.js --exclude=radio-check.html --exclude=check.css --exclude=FROM-WEBSITE-COMMIT.txt --exclude=index.html --exclude='kpc-dv*' --exclude=capacitor.js . ) | ( cd "$OUT" && tar xf - )
cp "$HERE/kpc-web.js" "$HERE/kpc-web.css" "$HERE/kpc-web-pre.js" "$OUT/"   # Nov 18: + kpc-web-pre.js (app-only switches off, in <head>)
python3 - "$APP/www/index.html" "$OUT/kpc-logger-beta.html" <<'PY'
import sys,re
s=open(sys.argv[1]).read()
s=s.replace('<meta charset="utf-8">','<meta charset="utf-8">\n<meta name="robots" content="noindex,nofollow">\n<script src="../kpc-gate.js"></script>',1)
s=s.replace('<title>KPC</title>','<title>KPC Logger (beta) | KPC</title>',1)
s=re.sub(r'(<link rel="stylesheet" href="app\.css[^"]*">)',r'\1\n<link rel="stylesheet" href="kpc-web.css?v=W">',s,count=1)
s=re.sub(r'<script src="kpc-remote\.js[^"]*"></script>\n?','',s)
s=re.sub(r'<script>[^<\n]*document\.write\(\'<script src="kpc-remote\.js[^\n]*</script>\n?','',s)   # Nov 7: the app loads it with document.write now
s=re.sub(r'<script src="capacitor\.js"></script>\n?','',s)   # Nov 7: Android-only bridge, a 404 on the website
s=re.sub(r'<script src="kpc-dv(-ui)?\.js[^"]*"></script>','',s)   # Nov 18 (KPC owner): FreeDV is Windows app only, never on the website
s=s.replace('<script src="../kpc-gate.js"></script>','<script src="../kpc-gate.js"></script>\n<script src="kpc-web-pre.js?v=W"></script>',1)   # Nov 18: app-only switches off before the app's scripts run
s=s.replace('</body>','<script src="kpc-web.js?v=W"></script>\n</body>',1)
# Nov 11 2026 (owner): the beta has no offline save yet, so the Log files card links the old logger (website copy only)
i=s.find('<h2>Log files</h2>'); j=s.find('  </section>',i)
if i>0 and j>0 and 'kpc-logger.html?old=1' not in s: s=s[:j]+'    <div class="row"><a class="b" href="../kpc-logger.html?old=1">🗂 OFFLINE / OLD LOGGER</a></div>\n    <p class="hint">Saving the logger for use with no signal lives in the old logger for now.</p>\n'+s[j:]
open(sys.argv[2],'w').write(s)
PY
# Nov 18 2026 (Lounge round stage 2; KPC owner Nov 16, item 7 'be polite to POTA'): on the website, POTA spots go through the
# site's ONE browser door (kpc-hunt.js has the master copy; relay address only in kpc-spots.json, POTA only as the backup, at most
# once per 5 minutes per browser). The app's own relay + POTA lines are swapped for it. The door is kept as KPCPotaDoor because the
# app's kpc-pota.js (POTA sign-in) loads later and takes the name window.KPCPota.
python3 - "$SITE/kpc-hunt.js" "$OUT/kpc-sources.js" <<'PY'
import sys,re
door=re.search(r'/\* KPC POTA door for the browser.*?return\{spots,spotsResponse,parkList,poll,age,setting\}\}\)\(\);\n',open(sys.argv[1]).read(),re.S).group(0)
s=open(sys.argv[2]).read()
a=s.index("  const RELAY = 'https://kpc-spots."); b=s.index('  SPx.potaVia = ')
new=("  /* website copy (sync.sh): spots come through the site's browser door (kpc-spots.json relay first, POTA only as its backup) */\n"
     "  const PS = { via: '', age: null, at: 0, direct: 0 };\n"
     "  async function potaList() { const L = await KPCPotaDoor.spots(); PS.via = 'the club spot feed'; PS.age = KPCPotaDoor.age(); PS.at = Date.now(); return L; }\n")
s=s[:a]+new+s[b:]
s=door+'const KPCPotaDoor = window.KPCPota;   /* kept: kpc-pota.js (POTA sign-in) takes the name window.KPCPota later */\n'+s
assert 'spot/activator' not in re.sub(re.escape(door),'',s) and 'kpc-spots.kentuckyportableclub' not in s
open(sys.argv[2],'w').write(s)
PY
V=$(date +%Y%m%d%H%M); sed -i "s/?v=W\"/?v=$V\"/g" "$OUT/kpc-logger-beta.html"
cat > "$OUT/index.html" <<'H'
<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>KPC Logger (beta)</title><meta http-equiv="refresh" content="0;url=kpc-logger-beta.html"><a href="kpc-logger-beta.html">KPC Logger (beta)</a>
H
C=$(git -C "$APP" rev-parse --short HEAD 2>/dev/null || cat "$APP/SOURCE-COMMIT.txt" 2>/dev/null || echo unknown); D=$(git -C "$APP" log -1 --format=%cs 2>/dev/null || date +%F)
echo "app commit $C $D" > "$OUT/FROM-APP-COMMIT.txt"   # Nov 7: works from a zip copy of the app too (SOURCE-COMMIT.txt)
echo "logger-beta synced from app $(cat "$OUT/FROM-APP-COMMIT.txt")"

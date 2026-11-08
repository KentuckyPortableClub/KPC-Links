#!/usr/bin/env python3
"""Nov 8 (Brandon 5:17 / 5:18 PM CST, t768u/t769u): NEAR A SPOT takes an address again (turned into GPS with the geocoder Check a place
uses), shows the GPS, sets the pin on the one map and searches there. Typed GPS numbers work. No device-GPS button. The dropped pin stays."""
import re, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
rj = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8'); mj = (ROOT / 'kpc-maprep.js').read_text(encoding='utf-8')
check('nominatim.openstreetmap.org/search' in mj and 'nominatim.openstreetmap.org/search' in rj, 'same geocoder as Check a place (OpenStreetMap Nominatim)')
check("format: 'jsonv2', countrycodes: 'us,ca', addressdetails: 1, limit: 1" in rj, 'same query as before')
check('1100 - (Date.now() - geoAt)' in rj and 'GEO[t] !== undefined' in rj, 'usage policy: at most one request a second, results kept, only on SEARCH')
check('gpsNums(t)' in rj and "showAt('GPS ' + la.toFixed(6)" in rj, 'typed GPS numbers work; the converted GPS is shown')
check('W.KPCMapCheck.showPoint(la, lo)' in rj and "run('pin', true)" in rj, 'pin goes on the one map and the search runs there')
check('geolocation' not in rj, 'no device GPS button (Brandon t769u)')
check("b('mrRsPinUse'" in rj and "lastPin = [e.latlng.lat, e.latlng.lng]" in rj, 'dropped pin still works (tap and USE THE DROPPED PIN)')
check('recs = await near(code, lastPin[0], lastPin[1], 6)' in rj, 'radius unchanged (about 6 km)')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8')
    check('id="mrRsLoc"' in h and 'id="mrRsLocAt"' in h and 'id="mrRsPinUse"' in h and 'USE MY GPS' not in h.split('data-rspane="pin"')[1].split('</form>')[0], f + ': address box, GPS shown, dropped pin; no GPS button')
    check('kpc-maprep-research.js?v=20261108w' in h, f + ': new script version')
sys.exit(0 if ok else 1)

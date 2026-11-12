#!/usr/bin/env python3
"""Nov 11 review of the Hunters Lounge / VIP Lounge / Activators Lounge pages (kpc-hunters.html, kpc-hunt.html, kpc-activators-lounge.html and
their scripts). Static + node checks, no browser, no network. The browser round is tests/lounge_review_nov11_browser.py (needs Chromium)."""
import pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
rd = lambda p: (ROOT / p).read_text(encoding='utf-8')
hunt, hx, lr, lounge, tabs = rd('kpc-hunt.js'), rd('kpc-hunt-x.js'), rd('kpc-lounge-radio.js'), rd('kpc-lounge.js'), rd('kpc-lounge-tabs.js')
PAGES = {n: rd(n) for n in ('kpc-hunters.html', 'kpc-hunt.html', 'kpc-activators-lounge.html')}
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
def node(code):
    r = subprocess.run(['node', '-e', code], capture_output=True, text=True); return (r.stdout + r.stderr).strip()

# links made from spot data are encoded AND escaped (WWFF refs are read from DX-cluster comments)
m = re.search(r"  const pageOf = .*\n", hunt)
check(bool(m) and m.group(0).lstrip().startswith('const pageOf = s => esc(') and 'encodeURIComponent(s.ref)' in m.group(0), 'pageOf: the ref is encoded and the whole address escaped')
out = node("const esc = s => String(s == null ? '' : s).replace(/[&<>\"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', \"'\": '&#39;' }[c]));" + m.group(0) +
           "console.log(pageOf({p:'WWFF',ref:'KFF-0001\"><IMG SRC=X ONERROR=X>'}) + ' | ' + pageOf({p:'SOTA',ref:'W4K/EC-001'}) + ' | ' + pageOf({p:'POTA',ref:'US-1234'}))")
check('"' not in out and '<' not in out and ' | https://sotl.as/summits/W4K/EC-001 | https://pota.app/#/park/US-1234' in out, 'pageOf: no quote or tag survives, real refs still give the same address: ' + out[:150])
check('${short ? \'\' : esc(base(s.call))' in hunt, 'award chips: the activator call is escaped')
# the sheet's STATE box and the filter's state list have different ids
for n, t in PAGES.items():
    ids = re.findall(r'\bid="([^"]+)"', t); dup = sorted({i for i in ids if ids.count(i) > 1})
    check(not dup, n + ': no id used twice %s' % dup)
for n in ('kpc-hunters.html', 'kpc-hunt.html'):
    check('<input id="lgSt"' in PAGES[n] and '<input id="fSt"' not in PAGES[n], n + ': the log sheet STATE box is #lgSt')
    check('aria-label="Call sign to add to my favorites"' in PAGES[n] and 'aria-label="Park numbers to add to my chase list"' in PAGES[n], n + ': favorites and chase boxes have a name for screen readers')
check("const shSt = () => document.getElementById('lgSt') ||" in hunt and "$('fSt').value = x.st" not in hunt and "st: $('fSt').value" not in hunt, 'kpc-hunt.js reads and writes the sheet state through shSt()')
# one run at a time
check('if (dkLog.busy) return;' in hunt and 'dkLog.busy = false' in hunt and 'if (lgBusy) return;' in hunt and 'if (respot.busy) return;' in hunt and 'respot.busy = false' in hunt, 'dock log, sheet save and respot ignore a second tap while one is running')
check('if (loadBusy) return;' in hunt and 'finally {' in hunt and "next = Date.now() + Math.min(300e3" in hunt, 'spot polling: the next check is always booked and backs off after failures')
check("...(PAGE === 'need' ? [needLoad] : [])" in hunt, 'the state park list loads only on the Park Checker page')
# ADIF read-back counts bytes
t = re.search(r"  const u8 = .*?\n  function take\(.*?\n", hunt, re.S)
check(bool(t), 'take() present')
out = node(t.group(0) + "console.log([take('café ñ',5), take('abc',2), take('éé',2), take('x\U0001F600y',5)].join('|'))")
check(out == 'café|ab|é|x\U0001F600', 'take(): cuts text at a number of BYTES (UTF-8): ' + out)
# storage
check("localStorage.setItem(k, JSON.stringify(v)); return true; } catch (e) { return false; }" in hunt and "QK + '-unreadable'" in hunt and 'would not save your log' in hunt, 'a log that cannot be saved warns; one that cannot be read is kept aside')
# radio window
check("(((k.RADIO || {})[k.get().radio] || {}).label || 'connected')" in hx, 'radio window status line: no "● undefined"')
check("G.addEventListener('pagehide', () => talkUp())" in hx and "document.hidden) talkUp()" in hx, 'HOLD TO TALK lets go of the radio when the tab is hidden or closed')
check('id="lrSwrHold"' in lr and 'id="lrSwr">' not in lr and "LS('kpcAppNr', null)" in lr, 'radio extras: no second #lrSwr, storage read is guarded')
# tab strip + official-website link
check("Object.prototype.hasOwnProperty.call(SETS, q)" in tabs, 'tab strip: ?from= must be one of its own names')
m = re.search(r"  const okUrl = .*\n", lounge)
out = node(m.group(0) + "console.log([okUrl('https://a.gov/x'), okUrl('javascript:alert(1)'), okUrl(' HTTP://b.org'), okUrl(null), okUrl('data:text/html,x')].join('|'))")
check(out == 'https://a.gov/x||HTTP://b.org||', 'okUrl(): only http(s) addresses become links: ' + out)
check('okUrl(o.web)' in lounge and 'okUrl(h.link)' in lounge, 'activators lounge: the official website and hours links use okUrl')
# the page source the two pages are built from (.claude/build/hunt/main.html) carries the same page edits
main = rd('.claude/build/hunt/main.html')
check('<input id="lgSt"' in main and '<input id="fSt"' not in main and 'aria-label="Park numbers to add to my chase list"' in main and 'kpc-hunt.js?v=20261111r' in main, '.claude/build/hunt/main.html: same state-box id, labels and script version as the built pages')
# page versions bumped for every file changed
for n in ('kpc-hunters.html', 'kpc-hunt.html'):
    for f in ('kpc-hunt.js', 'kpc-hunt-x.js', 'kpc-hunt.css', 'kpc-lounge-radio.js'):
        check(('%s?v=20261111r' % f) in PAGES[n], n + ' loads ' + f + ' with the new version')
check('kpc-lounge.js?v=20261111r' in PAGES['kpc-activators-lounge.html'] and all('kpc-lounge-tabs.js?v=20261111r' in t for t in PAGES.values() if 'kpc-lounge-tabs.js' in t), 'activators lounge and tab strip versions bumped')
# nothing in these files talks to a host the club never contacts, and no login is in them
HOST = re.compile(r'services[0-9]*(-[a-z0-9]+)?\.arcgis\.com|apps\.fs\.usda\.gov|ncnhde\.natureserve\.org|33TOOklri9xpic7U')
for n, t in [('kpc-hunt.js', hunt), ('kpc-hunt-x.js', hx), ('kpc-lounge.js', lounge), ('kpc-lounge-radio.js', lr), ('kpc-lounge-tabs.js', tabs)] + list(PAGES.items()):
    check(not HOST.search(t) and not re.search(r"(password|passwd|username|apikey|api_key|token)\s*[:=]\s*['\"][^'\"]{3,}", t, re.I), n + ': no blocked host, no stored login')
# Nov 11 round 2: the live-iframe height message only counts from our own origin, and the height is a number
for n, t2 in list(PAGES.items()) + [('.claude/build/hunt/main.html', main), ('.claude/build/lounge/main.html', rd('.claude/build/lounge/main.html'))]:
    if 'kpcLiveH' in t2:
        check("if(e.origin!==location.origin)return;" in t2 and "+d.kpcLiveH>0" in t2 and "Math.max(600,+d.kpcLiveH)" in t2, n + ': message listener checks origin and uses a number')
check('let fpq = 0; addEventListener(\'scroll\', () => { if (!fpq) fpq = requestAnimationFrame' in hunt, 'kpc-hunt.js: filter pop-up scroll handler runs once per frame')
print('ALL PASSED' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)

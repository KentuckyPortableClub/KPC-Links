#!/usr/bin/env python3
"""Map store hook (KPC owner, 2026-11-15): the wiring in kpc-padus-layer.js, and the headless Chromium check
tests/map_store_hook_nov15_browser.py (made-up display data; run here when playwright and Chromium are installed, else SKIP for
that part). Offline. Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED (or SKIP when the browser part cannot run)."""
import os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAILS = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: FAILS.append(name)


pad = (ROOT / 'kpc-padus-layer.js').read_text(encoding='utf-8')
disp = (ROOT / 'kpc-outline-display.js').read_text(encoding='utf-8')
check('the go-live list still ships empty (LIVE_AREAS = [])', 'var LIVE_AREAS = [];' in disp)
check('no page includes kpc-outline-display.js (it is fetched only when asked)',
      not [p.name for p in ROOT.glob('*.html') if 'kpc-outline-display.js' in p.read_text(encoding='utf-8', errors='replace')])
check("the loader is fetched only when the page has it or the visitor asked (?outlines=store | old, or the stored toggle)",
      "if (!storeAsked()) return Promise.resolve(null);" in pad and "if (q === 'store' || q === 'old') return true;" in pad
      and "localStorage.getItem(STORE_KEY) === '1'" in pad and "STORE_KEY = 'kpcOutlineStore'" in pad and "KEY = 'kpcOutlineStore'" in disp)   # the same toggle as the loader's
check('the hook is on the drawing only (kpcKeyOutlines, shared with "am I in the park", is unchanged)',
      "storeOr('US-' + String(s.a).toUpperCase(), KO.load(s.a))" in pad and 'storeOr(' not in pad.split('window.kpcKeyOutlines = window.kpcKeyOutlines ||')[1].split('window.KPCPad = function')[0])
check('any failure of the store path gives today\'s pack', pad.count('() => oldP') >= 2 and '.catch(() => oldP)' in pad)
check("line-only park: a second polyline, weight 12, opacity 0, interactive, carrying the popup",
      "L.polyline(lls, { pane: 'usoff', renderer: rend, weight: 12, opacity: 0, fill: false, interactive: true, className: 'kpc-usoff-hit' })" in pad
      and 't.bindPopup(popup(f)' in pad and "p.role === 'line' && p.ref && !hasHit[p.ref]" in pad)
vs = {m for p in list(ROOT.glob('*.html')) + list((ROOT / '.claude/build').rglob('*.html'))
      for m in re.findall(r'kpc-padus-layer\.js\?v=([A-Za-z0-9_-]+)', p.read_text(encoding='utf-8', errors='replace'))}
check(f'every page loads kpc-padus-layer.js at the new stamp ({sorted(vs)})', vs == {'20261115ms'})
check('the loader is asked for at its own stamp', "STORE_JS = 'kpc-outline-display.js?v=20261115ms'" in pad)

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        pw.chromium.launch().close()
    have = True
except Exception as e:  # noqa: BLE001
    have = False; why = str(e).splitlines()[0][:120] if str(e) else type(e).__name__
if have:
    r = subprocess.run([sys.executable, '-B', str(ROOT / 'tests' / 'map_store_hook_nov15_browser.py')], capture_output=True, text=True, timeout=600,
                       env=dict(os.environ, KPC_TEST_PORT=os.environ.get('KPC_TEST_PORT', '8816')))
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith(('PASS', 'FAIL'))]
    for ln in lines: print('  browser: ' + ln)
    check(f'headless Chromium on made-up display data: {len(lines)} checks', r.returncode == 0 and 'ALL PASS' in r.stdout and lines
          and not [ln for ln in lines if ln.startswith('FAIL')])
    if r.returncode and not lines: print(r.stdout[-800:], r.stderr[-800:])
print('ALL PASS' if not FAILS else f'SOME FAILED ({len(FAILS)})')
if not FAILS and not have: print(f'SKIP the browser part (playwright / Chromium not here: {why})')
sys.exit(1 if FAILS else 0)

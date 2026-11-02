#!/usr/bin/env python3
"""REF CHECK GUARD (chat 10, Nov 2 2026; chat 5's 'what wrong looks like' for kpc-ref-check.yml, HQ's held-wiring GO Oct 30).
Runs after kpc_refcheck.py, before its save. The reference check may only TAKE OFF parks POTA retired. A change is put back
(the site keeps the saved copy) and ONE line goes to chat 11's inbox when:
  - kpc-ky-data.json lost a park that is not in data/ky-retired.json, or lost more than 10 at once;
  - a ky-*.geojson is empty or 30%+ smaller (bytes) than the saved copy;
  - a KPC_Kentucky_*.gpx / .kml has no points.
Never fails.   python3 .github/scripts/kpc_refcheck_guard.py"""
import datetime as dt, glob, json, pathlib, re, subprocess

INBOX = pathlib.Path('.claude/inbox/chat-11.md')


def saved(f):
    r = subprocess.run(['git', 'show', f'HEAD:{f}'], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def main():
    bad, put_back = [], set()
    try:
        old = json.loads(saved('kpc-ky-data.json') or b'{}'); new = json.load(open('kpc-ky-data.json', encoding='utf-8'))
        o, n = {p['c'] for p in old.get('parks') or []}, {p['c'] for p in new.get('parks') or []}
        gone = o - n
        try: ret = json.dumps(json.load(open('data/ky-retired.json', encoding='utf-8')))
        except Exception: ret = ''  # noqa: BLE001
        stray = sorted(r for r in gone if r not in ret)
        if stray or len(gone) > 10:
            bad.append(f'kpc-ky-data.json lost {len(gone)} park(s){", not retired by POTA: " + ", ".join(stray[:8]) if stray else ""}')
            put_back.add('kpc-ky-data.json')
    except Exception as e: bad.append(f'kpc-ky-data.json not checked ({type(e).__name__})')  # noqa: BLE001
    for f in glob.glob('ky-*.geojson'):
        b = saved(f); now = pathlib.Path(f).stat().st_size
        if b and (now < 50 or now < 0.7 * len(b)):
            bad.append(f'{f} {len(b)} -> {now} bytes'); put_back.add(f)
    for f in glob.glob('KPC_Kentucky_*.gpx') + glob.glob('KPC_Kentucky_*.kml'):
        t = pathlib.Path(f).read_text(encoding='utf-8', errors='replace')
        if not re.search(r'<wpt\b|<Placemark\b', t):
            bad.append(f'{f} has no points'); put_back.add(f)
    if not bad: print('::notice title=Ref check guard::all lists whole'); return
    for f in put_back: subprocess.run(['git', 'checkout', 'HEAD', '--', f], check=False)
    why = '; '.join(bad)[:400]
    print(f'::warning title=Ref check guard::put back (the site keeps the saved copy): {why}')
    today = dt.date.today().isoformat()
    line = f"- FROM REF CHECK GUARD ({today}): the reference check's change was put back, the site keeps the last good copy: {why}. Look at the run; the next clean Monday saves again."
    if INBOX.exists():
        t = INBOX.read_text(encoding='utf-8')
        if f'REF CHECK GUARD ({today})' not in t:
            i = t.find('\n- ')
            INBOX.write_text(t[:i] + '\n' + line + t[i:] if i >= 0 else t + '\n' + line + '\n', encoding='utf-8')
            subprocess.run(['git', 'add', str(INBOX)], check=False)


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Ref check guard::not run ({type(e).__name__}: {e})')  # noqa: BLE001

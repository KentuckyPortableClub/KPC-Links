"""Owner rule, 2026-11-10: kpc_key_postcheck keeps only the newest 10 per-build reports per key (git history has the rest), never the
one just written and never another key's files. Offline, temp folder."""
import json, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github/scripts'))
import kpc_key_postcheck as PC
ok = True
def check(m, c):
    global ok
    ok &= bool(c); print(('ok   ' if c else 'FAIL ') + m)
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t)
    for i in range(14):
        (d / f'us-US-{i}.json').write_text(json.dumps({'checked': f'2026-11-{i + 1:02d} 10:00'})); (d / f'us-US-{i}.md').write_text('x')
    (d / 'ca-CA-1.json').write_text(json.dumps({'checked': '2026-10-01 10:00'})); (d / 'last-us.json').write_text('{}'); (d / 'trend-us.json').write_text('{}')
    PC.prune_reports(d, 'us', 'us-US-13')
    left = sorted(p.name for p in d.glob('us-US-*.json'))
    check(f'10 newest us reports stay ({len(left)})', len(left) == 10 and 'us-US-13.json' in left and 'us-US-3.json' not in left and 'us-US-4.json' in left)
    check('their .md pairs go with them', not (d / 'us-US-0.md').exists() and (d / 'us-US-13.md').exists())
    check('another key and the last-/trend- files are untouched', (d / 'ca-CA-1.json').exists() and (d / 'last-us.json').exists() and (d / 'trend-us.json').exists())
    PC.prune_reports(d, 'us', 'us-US-5', keep=1)
    check('the report just written is never deleted', (d / 'us-US-5.json').exists() and (d / 'us-US-13.json').exists() and not (d / 'us-US-6.json').exists())
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)

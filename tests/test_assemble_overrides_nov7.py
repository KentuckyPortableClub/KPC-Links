#!/usr/bin/env python3
"""assemble.py overrides.json hook guards (Nov 7 2026). Works in temp copies; writes nothing into the repo.
1. Every .claude/build/*/main.html assembles identically with the hook off (KPC_ASSEMBLE_NO_OVERRIDES=1) and on,
   for every page that has no overrides.json (so the hook cannot change other pages).
2. A stale or ambiguous replace entry in an overrides.json makes the assembler exit non-zero, naming page and entry.
3. drop_tail really drops news.html's closing script block (and the page still has it with the hook off)."""
import os, json, subprocess, sys, tempfile, shutil

repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
TITLE, DESC = 'Test page | KPC', 'Test description.'
ok = True
def check(name, cond, extra=''):
    global ok
    print(('PASS' if cond else 'FAIL'), name, extra)
    ok = ok and bool(cond)

def make_tree():
    tmp = tempfile.mkdtemp(prefix='asm_ov_')
    shutil.copy(os.path.join(repo, 'news.html'), tmp)
    shutil.copytree(os.path.join(repo, '.claude', 'build'), os.path.join(tmp, '.claude', 'build'),
                    ignore=shutil.ignore_patterns('__pycache__'))
    return tmp

def title_desc(page):
    if page != 'maprep':  # maprep's overrides.json names its og:title, so use the page's real title
        return TITLE, DESC
    import re
    b = open(os.path.join(repo, 'kpc-maprep.html'), encoding='utf-8').read()
    return (re.search(r'<title>(.*?)</title>', b).group(1).replace('&amp;', '&'),
            re.search(r'<meta name="description" content="(.*?)">', b).group(1).replace('&quot;', '"'))

def run(tmp, page, nohook=False):
    env = dict(os.environ)
    env.pop('KPC_ASSEMBLE_NO_OVERRIDES', None)
    if nohook:
        env['KPC_ASSEMBLE_NO_OVERRIDES'] = '1'
    out = 'zz-test-%s.html' % page
    r = subprocess.run([sys.executable, '-I', os.path.join(tmp, '.claude', 'build', 'assemble.py'),
                        os.path.join(tmp, '.claude', 'build', page, 'main.html'), out, *title_desc(page)],
                       capture_output=True, text=True, cwd=tmp, env=env)
    data = open(os.path.join(tmp, out), 'rb').read() if r.returncode == 0 else None
    return r, data

tmp = make_tree()
try:
    bd = os.path.join(tmp, '.claude', 'build')
    pages = sorted(d for d in os.listdir(bd) if os.path.isfile(os.path.join(bd, d, 'main.html')))
    plain = [p for p in pages if not os.path.isfile(os.path.join(bd, p, 'overrides.json'))]
    withov = [p for p in pages if p not in plain]
    check('found pages', len(plain) >= 10, '%d pages without overrides, %d with' % (len(plain), len(withov)))
    bad = []
    for p in plain:
        r1, a = run(tmp, p, nohook=True)
        r2, b = run(tmp, p)
        if r1.returncode or r2.returncode or a != b:
            bad.append(p)
    check('hook on == hook off for every page without overrides.json (%d pages)' % len(plain), not bad, str(bad))
    check('maprep has an overrides.json', 'maprep' in withov)

    # stale / ambiguous entry
    path = os.path.join(bd, 'maprep', 'overrides.json')
    orig = open(path, encoding='utf-8').read()
    ov = json.loads(orig)
    ov['replace'][0][0] = 'THIS TEXT IS NOT IN THE PAGE'
    open(path, 'w', encoding='utf-8').write(json.dumps(ov))
    r, d = run(tmp, 'maprep')
    check('stale entry makes the assembler fail', r.returncode != 0 and d is None, r.stderr[-200:])
    check('failure names the page and the entry', 'maprep' in r.stderr and 'entry #1' in r.stderr and 'matches 0 times' in r.stderr, r.stderr[-200:])
    ov['replace'][0][0] = '<script'
    open(path, 'w', encoding='utf-8').write(json.dumps(ov))
    r, d = run(tmp, 'maprep')
    check('entry matching more than once fails', r.returncode != 0 and 'entry #1' in r.stderr and 'matches' in r.stderr and 'matches 1 times' not in r.stderr, r.stderr[-200:])
    open(path, 'w', encoding='utf-8').write(orig)
    r, d = run(tmp, 'maprep')
    check('restored overrides.json assembles again', r.returncode == 0 and d is not None, r.stderr[-200:])

    # drop_tail
    check('maprep overrides use drop_tail', json.loads(orig).get('drop_tail') is True)
    marker = b'<script src="kpc-search.js'
    _, with_hook = run(tmp, 'maprep')
    _, no_hook = run(tmp, 'maprep', nohook=True)
    check('drop_tail drops the news.html tail script block', marker not in with_hook and marker in no_hook)
    # news.html without the tail it is supposed to drop: must fail, not pass quietly
    nh = os.path.join(tmp, 'news.html')
    t = open(nh, encoding='utf-8').read()
    open(nh, 'w', encoding='utf-8').write(t.replace('<script src="kpc-search.js', '<script src="kpc-gone.js'))
    r, d = run(tmp, 'maprep')
    check('missing tail makes the assembler fail instead of passing', r.returncode != 0 and d is None and 'kpc-search.js' in r.stderr and 'Traceback' not in r.stderr, r.stderr[-160:])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if ok else 1)

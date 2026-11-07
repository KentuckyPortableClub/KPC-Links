#!/usr/bin/env python3
"""Map Rep source guard (Nov 7 2026): assemble kpc-maprep.html from .claude/build/maprep/main.html
(+ overrides.json) in a temp copy of the build tree and require it to equal the committed page byte for byte.
If this fails, kpc-maprep.html was edited by hand: copy the change into .claude/build/maprep/main.html
(or overrides.json for head/tail changes), then run  python3 .claude/build/assemble.py .claude/build/maprep/main.html kpc-maprep.html "<title>" "<description>"
(title and description as in the page). Writes nothing into the repo."""
import os, re, subprocess, sys, tempfile, shutil, hashlib

repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
page = 'kpc-maprep.html'
built = open(os.path.join(repo, page), encoding='utf-8', newline='').read()
title = re.search(r'<title>(.*?)</title>', built).group(1).replace('&amp;', '&')
desc = re.search(r'<meta name="description" content="(.*?)">', built).group(1).replace('&quot;', '"')

tmp = tempfile.mkdtemp(prefix='maprep_src_')
try:
    bd = os.path.join(tmp, '.claude', 'build')
    os.makedirs(os.path.join(bd, 'maprep'))
    shutil.copy(os.path.join(repo, 'news.html'), tmp)
    src = os.path.join(repo, '.claude', 'build')
    for f in ('assemble.py', 'page-css.html', 'compare.html'):
        shutil.copy(os.path.join(src, f), bd)
    for f in os.listdir(os.path.join(src, 'maprep')):
        shutil.copy(os.path.join(src, 'maprep', f), os.path.join(bd, 'maprep'))
    r = subprocess.run([sys.executable, '-I', os.path.join(bd, 'assemble.py'),
                        os.path.join(bd, 'maprep', 'main.html'), page, title, desc],
                       capture_output=True, text=True, cwd=tmp)
    ok = True
    def check(name, cond, extra=''):
        global ok
        print(('PASS' if cond else 'FAIL'), name, extra)
        ok = ok and cond
    check('assembler ran', r.returncode == 0, r.stderr[-300:])
    out = open(os.path.join(tmp, page), encoding='utf-8', newline='').read() if r.returncode == 0 else ''
    same = out == built
    extra = ''
    if not same and out:
        a, b = out.split('\n'), built.split('\n')
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                extra = 'first difference at line %d: assembled %r vs committed %r' % (i + 1, a[i][:120], b[i][:120])
                break
        else:
            extra = 'line counts differ: %d vs %d' % (len(a), len(b))
    check('assembled maprep == committed kpc-maprep.html (byte-equal)', same, extra)
    check('no CR added', '\r' not in out or '\r' in built)
    print('sha256', hashlib.sha256(built.encode('utf-8')).hexdigest()[:12])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
sys.exit(0 if ok else 1)

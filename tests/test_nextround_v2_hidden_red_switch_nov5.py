"""Next round v2 (Quality grade of the next-round bundle, should-fix 'C4 tests'): the C4 tests only string-matched
"${{ vars.KPC_HIDDEN_RED != 'off' && '1' || '0' }}". This test EVALUATES that expression the way GitHub Actions does (an unset
variable is '', string compare ignores case, && / || return an operand) for KPC_HIDDEN_RED unset, 'off', 'OFF', 'on' and '1', then
runs each 'safe to fail' hidden-failure step's own Python with a caught error and that KPC_FAIL_SAFE value: unset / on -> the job
goes red (exit 1); off -> it stays green (exit 0). Part 2 (C4) is not changed. Runs in KPC-Links and KPC-Data (same file)."""
import os, pathlib, re, subprocess, sys, tempfile
import yaml

W = pathlib.Path(__file__).resolve().parent.parent / '.github' / 'workflows'
TOK = re.compile(r"\s*(?:(\|\||&&|==|!=|!|\(|\))|'((?:[^']|'')*)'|([A-Za-z_][\w.-]*))")


def gh_eval(expr, ctx):
    """A small evaluator for GitHub Actions expressions: literals, context paths, ! == != && || and parentheses."""
    toks, i, s = [], 0, expr.strip()
    while i < len(s):
        m = TOK.match(s, i)
        if not m or m.end() == i: raise ValueError(f'cannot read {s[i:]!r}')
        toks.append(('op', m.group(1)) if m.group(1) else ('str', m.group(2).replace("''", "'")) if m.group(2) is not None else ('id', m.group(3)))
        i = m.end()
    pos = [0]

    def peek(): return toks[pos[0]] if pos[0] < len(toks) else (None, None)

    def take(): pos[0] += 1; return toks[pos[0] - 1]

    def eq(a, b):
        if isinstance(a, str) and isinstance(b, str): return a.lower() == b.lower()
        return a == b

    def atom():
        k, v = take()
        if (k, v) == ('op', '('):
            r = or_(); take(); return r
        if (k, v) == ('op', '!'): return not truthy(atom())
        if k == 'str': return v
        if v in ('true', 'false'): return v == 'true'
        if v == 'null': return None
        cur = ctx
        for part in v.split('.'): cur = cur.get(part, '') if isinstance(cur, dict) else ''
        return cur   # an unset variable reads as ''

    def cmp():
        a = atom()
        while peek() in (('op', '=='), ('op', '!=')):
            op = take()[1]; b = atom(); a = eq(a, b) if op == '==' else not eq(a, b)
        return a

    def and_():
        a = cmp()
        while peek() == ('op', '&&'):
            take(); b = cmp(); a = b if truthy(a) else a
        return a

    def or_():
        a = and_()
        while peek() == ('op', '||'):
            take(); b = and_(); a = a if truthy(a) else b
        return a
    r = or_()
    if pos[0] != len(toks): raise ValueError(f'left over in {expr!r}')
    return r


def truthy(v): return v not in (False, None, '', 0)


CASES = [(None, '1', 1), ('off', '0', 0), ('OFF', '0', 0), ('on', '1', 1), ('1', '1', 1)]


def _safe_steps():
    for f in sorted(W.glob('*.yml')):
        d = yaml.safe_load(open(f, encoding='utf-8')) or {}
        for jn, j in (d.get('jobs') or {}).items():
            for st in j.get('steps') or []:
                v = (st.get('env') or {}).get('KPC_FAIL_SAFE')
                if v is not None and "<<'PY'" in str(st.get('run')): yield f.name, jn, str(v), st['run']


def test_the_expression_evaluates_as_intended():
    e = "vars.KPC_HIDDEN_RED != 'off' && '1' || '0'"
    for val, want, _ in CASES:
        assert gh_eval(e, {'vars': {} if val is None else {'KPC_HIDDEN_RED': val}}) == want, (val, want)


def test_every_safe_step_goes_red_unless_switched_off():
    steps = list(_safe_steps())
    assert steps, 'no hidden-failure step with KPC_FAIL_SAFE found'
    for n, jn, v, run in steps:
        m = re.fullmatch(r'\$\{\{(.*)\}\}', v.strip())
        assert m and 'KPC_HIDDEN_RED' in m.group(1), (n, jn, v)
        py = run.split("<<'PY'\n", 1)[1].rsplit('PY', 1)[0]
        for val, want, rc in CASES:
            got = gh_eval(m.group(1), {'vars': {} if val is None else {'KPC_HIDDEN_RED': val}})
            assert got == want, (n, jn, val, got)
            with tempfile.TemporaryDirectory() as tmp:
                for x in ('kpc-hidden.txt', 'kpc-hidden-errors.txt'): open(os.path.join(tmp, x), 'w').write('t - a caught error\n')
                env = dict(os.environ, RUNNER_TEMP=tmp, KPC_STEPS='{}', KPC_FAIL_SAFE=got, GITHUB_STEP_SUMMARY=os.path.join(tmp, 's'), GITHUB_JOB=jn, PYTHONDONTWRITEBYTECODE='1')
                p = subprocess.run([sys.executable, '-B', '-'], input=py, capture_output=True, text=True, env=env, cwd=tmp, timeout=60)
                assert p.returncode == rc, (n, jn, val, p.returncode, p.stdout[-300:], p.stderr[-300:])

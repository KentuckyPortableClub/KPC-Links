#!/usr/bin/env python3
"""Per-area input hashes (KPC owner, 2026-11-12; handoff part B; brief 4 'rebuild only what a rule change touches'; Nov 11 prototype
tools/kpc_area_hash.py moved here). Scheme: out/nov12/AB/SHARED-SCHEME.md (one scheme with the 2-fer half in KPC-Data).

Not a rule file (kpc_key_freeze.NOT_RULES): it never decides a join, it only decides WHICH areas a key run builds. Standard library only,
no network. It never imports or writes a rule file: it reads files (from a checkout or with `git show` at a commit) and prints hashes.
The key workflows call `plan` (which areas to build) and `stamp-rows` (record each saved area's hash); both are SHADOW by default:
  KPC_AREA_HASH (repo variable)  shadow (default, also when unset) = compute and print the run table; the list is NOT changed
                                 add    = rollout step 1 (D1): ADD every area whose inputs moved since its last build; nothing removed
                                 reuse  = step 3: also leave out an area whose inputs did not move (its main bytes are reused)
  input full_rebuild=yes         = every area of the list is built, reuse off (the 'force full rebuild')
Owner decisions D1-D9 (brief 4) are NOT signed: add / reuse must not be switched on before they are. The four region hashes it prints are worked out the same way as
.github/scripts/kpc_key_freeze.py rules_hash(kind) (its RULE_FILES are read from that file as text), so they can be compared.

What an AREA HASH is (the proposed composition, see DESIGN.md section 3): sha256 over named parts, each part a sha256 itself:
  code          the rule code every area of the kind runs (kpc_key_freeze RULE_FILES of the kind, scope files left out except the
                2-fer one that kpc_fers.py reads, plus the rule modules the builder imports that RULE_FILES misses), as TOKENS:
                comments, blank lines, spacing and docstrings do not count (they cannot change what Python runs). Level 1 = the
                file bytes as today, level 2 = tokens, level 3 (the design) = tokens with the per-area tables taken out of the code
                (BOX_ADD, the world SRC / KINDS / GEN ... tables): each table entry counts only for its own area.
  version       the kind's line in .github/key-rules-version.json (a person bumps it = every area moves, as today)
  code-area:*   level 3 only: this area's entries of the per-area tables in the code
  data:*        this area's slice of each data file the builder reads (overrides by park ref, state-gis.json by state,
                extra-layers.json by country, layers.json prefixes, state boxes, retired refs, POTA pins ...), as canonical JSON
                (key order and spacing do not count; 'about' / 'note' / 'updated' texts do not count)
  shared:*      inputs no slice can be proven for (a whole file; rows whose park is in no key file): every area of the kind
  gate:*        the saved-copy baseline / signed copy checksum of this area (decides whether its saved copy may be used)
  up:*          2-fers only: the key and outline CONTENT of each member state and each neighbour state (the per-park 'read' date
                left out), so a key rebuild that changed nothing in a state does not move a 2-fer area

  python3 .github/scripts/kpc_area_hash.py hashes [--rev REV]                       the four region hashes (as kpc_key_freeze rules)
  python3 .github/scripts/kpc_area_hash.py table KIND [--rev REV] [--level 3] [--parts]   per-area hash table (KIND us|ca|world|fers)
  python3 .github/scripts/kpc_area_hash.py diff KIND REV_A REV_B [--level 3]         which areas move between two commits, and why
  python3 .github/scripts/kpc_area_hash.py replay [--csv FILE] [--since REV]         every region-hash move on first-parent history:
                                                                           areas rebuilt today vs under levels 1-3
  common: --repo DIR (default: this checkout)  --data DIR (a KPC-Data checkout: pins data/parkinfo, 2-fer area lists)
          --rev WORKTREE = the files on disk (default for table)
Exit 0; 2 on a usage error. Fail closed: a file that cannot be read or parsed counts as a shared part named '<file>!unreadable'
(every area of the kind moves when it changes)."""
import argparse, ast, csv, gzip, hashlib, io, json, os, pathlib, re, subprocess, sys, tokenize

REPO = pathlib.Path(__file__).resolve().parents[2]
COMPOSITION = 'ah1'   # the area-hash composition id: it is in the `version` part, so a composition change moves every area once
FREEZE = '.github/scripts/kpc_key_freeze.py'
KINDS = {'us': 'us-key', 'ca': 'ca-key', 'world': 'world-key', 'fers': 'fers'}
US_ALL = ('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC '
          'SD TN TX UT VT VA WA WV WI WY').split()   # = the US key plan's ALL (KY has its own key)
WORLD_DEFAULT = 'AU DE GB JP PL ES FR CH AT NL PT SE CZ SI NO RO IT BE DK FI HU SK HR IE LT LV EE LU CO ZA CL'.split()
REF = re.compile(r'^[A-Z0-9]{1,4}-\d{3,6}$')
HEADER_KEYS = {'about', 'note', 'notes', 'updated', 'when', 'date', 'from', 'format', 'blocked_ids_about'}
# Rule modules a builder imports that today's RULE_FILES leave out, found by reading the imports (DESIGN.md 2.4). They decide
# results: kpc_fers_far_hold.hold_spots holds live 2-fer rows (kpc_fers.py pass 5); kpc_precheck.name_how is the name test of
# kpc_fers_guard.py. In the design they are rule files of the kind.
CLOSURE_ADD = {'fers': ['.github/scripts/kpc_fers_far_hold.py', '.github/scripts/kpc_precheck.py']}
# Scope files the BUILDER reads (an input); the other scope files are read only by the freeze check (a record, not an input).
SCOPE_READ = {'fers': '.github/fers-rule-scope.json'}
# Step 1 of the design (close the hole): the modules every key build runs that decide WHICH layer is read live, read from the saved
# copy only, or never contacted. Today they are in NOT_RULES. --reader shared (the step-1 default) puts their tokens in every area's
# hash; --reader verdict (the later step) puts instead, per area, the host verdict (live / saved-only / never) of every layer address the
# area reads, worked out by these modules themselves, so a host-rule edit moves only the areas with a layer on that host.
READER = ['.github/scripts/kpc_master.py', '.github/scripts/kpc_net_guard.py']
URL_RE = re.compile(r'(?:svc:)?https?://[^\s\'"\]\)|,]+')
# Level 3: per-area tables inside the rule code (the 'move to data files' list of DESIGN.md 2.2). dict = NAME = {area: ...};
# sub = NAME['XX'] = ... statements; manual = whole statements that belong to named areas; listset = list entries whose item
# [i] is a set of area codes.
TABLES = {
    '.github/scripts/kpc_us_key.py': {'dict': ['BOX_ADD'], 'listset': {'XS': 7}},
    '.github/scripts/kpc_world_key.py': {'dict': ['SRC', 'GEN', '_LOC', 'KINDS', 'SIDE_NOT'], 'sub': ['SRC', 'KINDS'],
                                         'manual': {'CHB': ['CH'], 'CHPREF': ['CH'], 'QLD_PAF': ['AU'], 'QLD_SF': ['AU'],
                                                    'QLD_REST': ['AU'], 'QLD_LAYERS': ['AU'], 'NO_N2K': ['CH', 'NO']}},
}


def H(b): return hashlib.sha256(b if isinstance(b, bytes) else str(b).encode()).hexdigest()


def canon(x): return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str).encode()


# ---------------------------------------------------------------- reading files at a commit (or on disk)
class Tree:
    """Files of one commit (git ls-tree + cat-file --batch) or of the working tree (rev None)."""
    _cat = {}

    def __init__(self, repo, rev=None):
        self.repo, self.rev = pathlib.Path(repo), (None if rev in (None, '', 'WORKTREE') else rev)
        self.blobs = {}
        if self.rev:
            out = subprocess.run(['git', '-C', str(self.repo), 'ls-tree', '-r', '-z', self.rev], capture_output=True, check=True).stdout
            for ent in out.split(b'\0'):
                if not ent: continue
                meta, path = ent.split(b'\t', 1); parts = meta.split()
                if parts[1] == b'blob': self.blobs[path.decode()] = parts[2].decode()
        self._json = {}

    def _catfile(self, oid):
        key = str(self.repo)
        p = Tree._cat.get(key)
        if p is None or p.poll() is not None:
            p = Tree._cat[key] = subprocess.Popen(['git', '-C', key, 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        p.stdin.write(oid.encode() + b'\n'); p.stdin.flush()
        hdr = p.stdout.readline().split()
        if len(hdr) < 3 or hdr[1] == b'missing': return None
        data = p.stdout.read(int(hdr[2])); p.stdout.read(1)
        return data

    def oid(self, path):
        if self.rev: return self.blobs.get(path)
        f = self.repo / path
        if not f.is_file(): return None
        st = f.stat(); return f'wt:{path}:{st.st_size}:{st.st_mtime_ns}'

    def read(self, path):
        if self.rev:
            o = self.blobs.get(path)
            return self._catfile(o) if o else None
        f = self.repo / path
        return f.read_bytes() if f.is_file() else None

    def json(self, path):
        """(object, ok). ok False = missing (None) or unreadable (the text '!unreadable')."""
        o = self.oid(path)
        if o is None: return None, False
        if o in self._json: return self._json[o]
        b = self.read(path)
        try:
            if path.endswith('.gz'): b = gzip.decompress(b)
            v = (json.loads(b.decode('utf-8')), True)
        except Exception: v = ('!unreadable', False)  # noqa: BLE001
        self._json[o] = v
        return v

    def ls(self, prefix, pattern):
        rx = re.compile(pattern)
        if self.rev: return sorted(p for p in self.blobs if p.startswith(prefix) and rx.match(p[len(prefix):]))
        d = self.repo / prefix
        return sorted(prefix + f.name for f in d.iterdir() if f.is_file() and rx.match(f.name)) if d.is_dir() else []


# ---------------------------------------------------------------- today's region hash (kpc_key_freeze.rules_hash, read as text)
def freeze_lists(tree):
    """RULE_FILES / SCOPE_FILES / VERSION_FILE of kpc_key_freeze.py at this tree, with its two append loops applied."""
    src = (tree.read(FREEZE) or b'').decode('utf-8', 'replace')
    mod = ast.parse(src)
    vals = {}
    for s in mod.body:
        if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name) and s.targets[0].id in ('RULE_FILES', 'SCOPE_FILES', 'VERSION_FILE'):
            vals[s.targets[0].id] = ast.literal_eval(s.value)
    rf = {k: list(v) for k, v in vals['RULE_FILES'].items()}
    sf = vals.get('SCOPE_FILES', {})
    if re.search(r'for _kind, _f in SCOPE_FILES\.items\(\): RULE_FILES\[_kind\]\.append\(_f\)', src):
        for k, f in sf.items(): rf[k].append(f)
    if "RULE_FILES[_kind].append('.github/scripts/kpc_key_facts.py')" in src:
        for k in rf:
            if k != 'fers': rf[k].append('.github/scripts/kpc_key_facts.py')
    return rf, sf, vals.get('VERSION_FILE', '.github/key-rules-version.json')


def region_hash(tree, kind):
    rf, sf, vf = freeze_lists(tree)
    if kind not in rf: return None
    h = hashlib.sha256()
    for rel in sorted(rf[kind]):
        b = tree.read(rel)
        if rel in sf.values() and b is None: continue
        h.update(rel.encode() + b'\0' + (b if b is not None else b'missing') + b'\0')
    v, ok = tree.json(vf)
    ver = v.get(kind) if ok and isinstance(v, dict) else None
    h.update(b'version\0' + str(ver).encode())
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- code normalising
def tokens(src_bytes, drop_lines=()):
    """The token stream without comments, blank lines and docstrings, as bytes. drop_lines: line numbers whose tokens are left out
    (level 3: the per-area table statements). A file that does not tokenise falls back to its bytes (fail closed)."""
    drop = set(drop_lines)
    try:
        doc_lines = set()
        txt = src_bytes.decode('utf-8')
        if '__doc__' not in txt:   # a docstring the code reads is not left out
            for n in ast.walk(ast.parse(txt)):
                if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    doc_lines.update(range(n.lineno, (n.end_lineno or n.lineno) + 1))
        out = []
        for t in tokenize.tokenize(io.BytesIO(src_bytes).readline):
            if t.type in (tokenize.COMMENT, tokenize.NL, tokenize.ENCODING): continue
            if t.start[0] in drop: continue
            if t.type == tokenize.STRING and t.start[0] in doc_lines: continue
            out.append(f'{tokenize.tok_name[t.type]} {t.string}' if t.type not in (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE) else tokenize.tok_name[t.type])
        # a dropped docstring can leave a NEWLINE alone; collapse runs so a docstring change never shows up as a structure change
        cl = []
        for x in out:
            if x == 'NEWLINE' and cl and cl[-1] == 'NEWLINE': continue
            cl.append(x)
        return '\n'.join(cl).encode()
    except Exception:  # noqa: BLE001
        return b'!untokenised\0' + src_bytes


def seg_tokens(txt, node):
    """Tokens of exactly this node's source (an expression is wrapped in brackets so it tokenises on its own)."""
    seg = ast.get_source_segment(txt, node) or ''
    return tokens(('(\n' + seg + '\n)\n').encode()) if not isinstance(node, ast.stmt) else tokens((seg + '\n').encode())


def split_tables(path, src_bytes, areas):
    """Level 3: (shared token bytes, {area: [(label, token bytes)]}). Entries for codes that are not areas of the kind stay shared."""
    cfg = TABLES.get(path)
    if not cfg: return tokens(src_bytes), {}
    try:
        txt = src_bytes.decode('utf-8'); mod = ast.parse(txt)
    except Exception:  # noqa: BLE001
        return tokens(src_bytes), {}
    drop, per, extra_shared = set(), {}, []
    def put(area, label, node):
        if area in areas: per.setdefault(area, []).append((label, seg_tokens(txt, node)))
        else: extra_shared.append(label.encode() + b'\0' + seg_tokens(txt, node))
    for s in mod.body:
        if not isinstance(s, (ast.Assign, ast.AugAssign)): continue
        tg = s.targets if isinstance(s, ast.Assign) else [s.target]
        if len(tg) != 1: continue
        t = tg[0]
        if isinstance(t, ast.Name) and t.id in cfg.get('dict', ()) and isinstance(s, ast.Assign) and isinstance(s.value, ast.Dict) \
                and all(isinstance(k, ast.Constant) and isinstance(k.value, str) for k in s.value.keys):
            for k, v in zip(s.value.keys, s.value.values): put(k.value, f'{t.id}[{k.value}]', v)
            drop.update(range(s.lineno, s.end_lineno + 1)); extra_shared.append(f'{t.id}=dict'.encode())
        elif isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id in cfg.get('sub', ()) \
                and isinstance(t.slice, ast.Constant) and isinstance(t.slice.value, str):
            put(t.slice.value, f'{t.value.id}[{t.slice.value}] stmt@{s.lineno}', s)
            drop.update(range(s.lineno, s.end_lineno + 1))
        elif isinstance(t, ast.Name) and t.id in cfg.get('manual', {}):
            for a in cfg['manual'][t.id]: put(a, t.id, s)
            drop.update(range(s.lineno, s.end_lineno + 1)); extra_shared.append(f'{t.id}=manual'.encode())
        elif isinstance(t, ast.Name) and t.id in cfg.get('listset', {}) and isinstance(s, ast.Assign) and isinstance(s.value, ast.List):
            i = cfg['listset'][t.id]
            for e in s.value.elts:
                own = None
                if isinstance(e, ast.Tuple) and len(e.elts) > i and isinstance(e.elts[i], ast.Set) \
                        and all(isinstance(c, ast.Constant) and isinstance(c.value, str) for c in e.elts[i].elts):
                    own = sorted(c.value for c in e.elts[i].elts)
                if own and all(a in areas for a in own):
                    for a in own: put(a, f'{t.id}[{own}]', e)
                else: extra_shared.append(f'{t.id}[]'.encode() + b'\0' + seg_tokens(txt, e))
            drop.update(range(s.lineno, s.end_lineno + 1))
    return tokens(src_bytes, drop) + b'\0' + b'\0'.join(extra_shared), per


# ---------------------------------------------------------------- data slicing
def ref_rows(obj):
    """{ref: row} of a data file keyed by park ref (top level, under 'parks' / 'refs', or a 'rows' list with 'ref'), and the rest
    (anything that is not a header text and not a ref row), or (None, obj) when the file has no ref rows at all."""
    if isinstance(obj, list):
        rows, rest = {}, []
        for r in obj:
            ref = r[1] if isinstance(r, list) and len(r) > 1 and isinstance(r[1], str) and REF.match(r[1]) else None
            if ref: rows.setdefault(ref, []).append(r)
            else: rest.append(r)
        return (rows, rest) if rows else (None, obj)
    if not isinstance(obj, dict): return None, obj
    if obj and all(REF.match(k) for k in obj): return dict(obj), {}
    rows, rest = {}, {}
    for k, v in obj.items():
        if k in HEADER_KEYS: continue
        if k in ('parks', 'refs') and isinstance(v, dict): rows.update(v); continue
        if k in ('rows', 'blocked_ids') and isinstance(v, list) and all(isinstance(r, dict) and r.get('ref') for r in v):
            for r in v: rows.setdefault(str(r['ref']), []).append(r)
            continue
        rest[k] = v
    return (rows, rest) if rows or ('parks' in obj or 'rows' in obj or 'blocked_ids' in obj) else (None, obj)


class Kind:
    """The areas of one kind at one tree and each area's parts."""

    def __init__(self, tree, kind, level=3, data=None, other=None, reader='shared', env=None):
        self.t, self.kind, self.level, self.data, self.reader, self.env = tree, kind, level, data, reader, dict(env or {})
        self.urls = {}   # area -> layer addresses seen in its parts ('*' = every area)
        self.areas = self.area_list()
        self.ref_area = self.ref_map()
        if other is not None:   # a diff: a park counts for the areas it is in at EITHER commit (a retired or moved park included)
            for r, a in other.ref_area.items(): self.ref_area.setdefault(r, set()).update(a)

    # ---- areas
    def area_list(self):
        t = self.t
        if self.kind == 'us': return list(US_ALL)
        if self.kind == 'ca':
            a = {p.split('/')[-1][3:5] for p in t.ls('data/ca-key/', r'^CA-[A-Z]{2}\.json$')}
            ix, ok = t.json('data/ca-key/index.json')
            if ok and isinstance(ix, dict): a |= set((ix.get('provinces') or {}))
            return sorted(a)
        if self.kind == 'world':
            a = {p.split('/')[-1][:2] for p in t.ls('data/world-key/', r'^[A-Z]{2}\.json$')} | set(WORLD_DEFAULT)
            for f, k in (('data/world-key/extra-layers.json', 'countries'), ('data/world-key/sheet-countries.json', 'countries')):
                v, ok = t.json(f)
                if ok and isinstance(v, dict): a |= set(v.get(k) or {})
            return sorted(a)
        return sorted(fers_areas(self.data))

    def ref_map(self):
        """park ref -> {areas}: the key files of this tree (+ the POTA pin files of --data). A ref in two areas belongs to both."""
        m = {}
        kinds = [self.kind] if self.kind != 'fers' else ['us', 'ca']
        for k in kinds:
            d, rx, nm = {'us': ('data/us-key/', r'^US-[A-Z]{2}\.json$', lambda p: p[3:5]), 'ca': ('data/ca-key/', r'^CA-[A-Z]{2}\.json$', lambda p: p[3:5]),
                         'world': ('data/world-key/', r'^[A-Z]{2}\.json$', lambda p: p[:2])}[k]
            for p in self.t.ls(d, rx):
                v, ok = self.t.json(p)
                if ok and isinstance(v, dict):
                    a = ('CA-' if k == 'ca' and self.kind == 'fers' else 'US-' if self.kind == 'fers' else '') + nm(p.split('/')[-1])
                    for r in (v.get('parks') or {}): m.setdefault(r, set()).add(a)
        if self.data:
            pdir = pathlib.Path(self.data) / 'data/parkinfo'
            for f in sorted(pdir.glob('*.json')) if pdir.is_dir() else []:
                st = f.stem
                if self.kind in ('us', 'ca') and not st.startswith(('US-', 'CA-')[self.kind == 'ca']): continue
                if self.kind == 'world' and '-' in st: continue
                try: pk = json.load(open(f, encoding='utf-8')).get('parks') or {}
                except Exception: continue  # noqa: BLE001
                a = st if self.kind == 'fers' else (st[3:] if self.kind in ('us', 'ca') else st)
                for r in pk: m.setdefault(r, set()).add(a)
        return m

    # ---- parts
    def code_files(self):
        rf, sf, vf = freeze_lists(self.t)
        k = KINDS[self.kind]
        keep = [f for f in rf.get(k, []) if f not in sf.values() or f == SCOPE_READ.get(self.kind)]
        return sorted(set(keep) | set(CLOSURE_ADD.get(self.kind, []))), vf

    def shared_parts(self):
        """{part name: digest} common to every area, and {area: {part: digest}} level-3 code entries."""
        files, vf = self.code_files()
        sh, per = {}, {}
        code_areas = set(self.areas) if self.kind != 'fers' else set()
        for f in files:
            b = self.t.read(f)
            if b is None: sh['code:' + f] = H(b'missing'); continue
            if f.endswith('.json'):
                v, ok = self.t.json(f)
                sh['code:' + f] = H(canon(v) if ok and self.level >= 2 else b)
                continue
            if self.level == 1: sh['code:' + f] = H(b)
            elif self.level == 2: sh['code:' + f] = H(tokens(b))
            else:
                s, pa = split_tables(f, b, code_areas)
                sh['code:' + f] = H(s)
                for a, items in pa.items():
                    for label, tb in items:
                        per.setdefault(a, {})[f'code-area:{f.split("/")[-1]}:{label}'] = H(tb)
                        self.urls.setdefault(a, set()).update(URL_RE.findall(tb.decode('utf-8', 'replace')))
                self.urls.setdefault('*', set()).update(URL_RE.findall(s.decode('utf-8', 'replace')))
        v, ok = self.t.json(vf)
        sh['version'] = H(COMPOSITION + '\0' + str(v.get(KINDS[self.kind]) if ok and isinstance(v, dict) else None))
        if self.kind != 'fers' and self.reader == 'shared':
            for f in READER:
                b = self.t.read(f)
                if b is not None: sh['reader:' + f] = H(tokens(b) if self.level >= 2 else b)
        # repo variables the key workflow passes to the build (KPC_KEY_LIVE, KPC_SAVED_ONLY_HOSTS, ...): not in git, so the plan job
        # must hash the values it was given. --var NAME=VALUE.
        if self.env: sh['vars'] = H(canon(self.env))
        return sh, per

    def slice_file(self, path, parts, shared, key_of=None, label=None):
        """Slice one data file into the areas' parts. key_of(obj) -> {area: slice} for files keyed by area; else ref rows."""
        label = label or path
        v, ok = self.t.json(path)
        if v is None and not ok:
            if self.t.oid(path) is None: shared[f'shared:{label}'] = H(b'missing'); return
        if not ok: shared[f'shared:{label}!unreadable'] = H(self.t.read(path) or b''); return
        if key_of:
            got, rest = key_of(v)
            for a, x in got.items():
                if a in self.areas_set:
                    parts.setdefault(a, {})[f'data:{label}'] = H(canon(x)); self.urls.setdefault(a, set()).update(URL_RE.findall(canon(x).decode()))
                else: rest = dict(rest or {}, **{f'?{a}': x})
            if rest: shared[f'shared:{label}'] = H(canon(rest))
            return
        rows, rest = ref_rows(v)
        if rows is None: shared[f'shared:{label}'] = H(canon(rest)); return
        by, un = {}, {}
        for r, x in rows.items():
            areas = self.ref_area.get(r) or (({r.split('-')[0]} if self.kind == 'world' and r.split('-')[0] in self.areas_set else set()))
            if not areas: un[r] = x; continue
            for a in areas: by.setdefault(a, {})[r] = x
        for a, x in by.items():
            if a in self.areas_set: parts.setdefault(a, {})[f'data:{label}'] = H(canon(x))
        # A row of a park in no key file and no pin file of this kind is never read: the builder's park list IS the pin file
        # (data/parkinfo/<area>.json) and it looks a row up by the park's ref. That holds only when the pin files are given (--data);
        # without them such rows stay a shared part (fail closed).
        if un and not self.data: shared[f'shared:{label}#rows-in-no-key'] = H(canon(un))
        if rest: shared[f'shared:{label}#other'] = H(canon(rest))

    def parts(self):
        """{area: {part: digest}} for every area of the kind."""
        self.areas_set = set(self.areas)
        sh, code_per = self.shared_parts()
        parts = {a: dict(code_per.get(a, {})) for a in self.areas}
        t = self.t
        if self.kind == 'us':
            self.slice_file('data/us-key/overrides.json', parts, sh)
            self.slice_file('data/state-gis.json', parts, sh, lambda v: ({k: x for k, x in (v.get('states') or {}).items() if k in self.areas_set} if isinstance(v, dict) else {}, {}),
                            label='data/state-gis.json(states; other codes are not read by this key)')
            # data/us-key/layers.json is NOT an input: the US key writes it (kpc_us_key.py:2652-2665) and reads it back only so a state
            # layer keeps the prefix it was first given (kpc_us_key.py:843-856); the layer list itself is data/state-gis.json (above).
            self.slice_file('kpc-us-states.json', parts, sh, key_of=lambda v: ({a: boxes_near(v, a) for a in self.areas}, {}), label='kpc-us-states.json(own+neighbour boxes)')
            for f in ('data/retired-refs.json', 'data/park-transfers.json'): self.slice_file(f, parts, sh)
            self.locations(parts, sh, 'US-')
            for f in ('data/nps-units.json',): self.slice_file(f, parts, sh)
            self.gate(parts, sh, lambda a: f'US-{a}')
        elif self.kind == 'ca':
            self.slice_file('data/ca-key/overrides.json', parts, sh)
            self.slice_file('data/ca-key/hardlook-joins.json', parts, sh)
            self.slice_file('data/state-gis.json', parts, sh, lambda v: ({k: x for k, x in (v.get('states') or {}).items() if k in self.areas_set} if isinstance(v, dict) else {}, {}))
            self.slice_file('data/ca-key/layers.json', parts, sh, key_of=lambda v: (
                {a: {k: x for k, x in v.items() if k.startswith(a + ' ') or k.startswith(a + '-')} for a in self.areas},
                {k: x for k, x in v.items() if not any(k.startswith(a + ' ') or k.startswith(a + '-') for a in self.areas)}))
            self.slice_file('data/retired-refs.json', parts, sh); self.locations(parts, sh, 'CA-')
            cb = {}
            for p in t.ls('data/canada-bounds/', r'^CA-\d+\.json$'):
                r = p.split('/')[-1][:-5]
                for a in self.ref_area.get(r) or {'?'}: cb.setdefault(a, {})[r] = t.oid(p) if t.rev else H(t.read(p) or b'')
            for a, x in cb.items():
                if a in self.areas_set: parts[a]['data:data/canada-bounds/*'] = H(canon(x))
                else: sh['shared:data/canada-bounds#rows-in-no-key'] = H(canon(x))
            self.gate(parts, sh, lambda a: 'CA-ALL', shared=True)   # one saved copy for all of Canada
        elif self.kind == 'world':
            self.slice_file('data/world-key/overrides.json', parts, sh)
            self.slice_file('data/world-key/extra-layers.json', parts, sh, lambda v: ((v.get('countries') or {}) if isinstance(v, dict) else {}, {}),
                            label='data/world-key/extra-layers.json(countries; dropped is not read)')
            self.slice_file('data/world-key/sheet-countries.json', parts, sh, lambda v: ((v.get('countries') or {}) if isinstance(v, dict) else {}, {}))
            self.slice_file('data/world-key/eea-designations.json', parts, sh, lambda v: (group(v, lambda k: k[:2]), {}))
            for f in ('data/world-key/jp-wikidata.json', 'data/retired-refs.json'): self.slice_file(f, parts, sh)
            self.locations(parts, sh, None)
            self.gate(parts, sh, lambda a: f'W-{a}')
        else:
            self.fers_parts(parts, sh)
        if self.data and self.kind in ('us', 'ca', 'world'):
            for a in self.areas:
                f = pathlib.Path(self.data) / 'data/parkinfo' / ({'us': f'US-{a}', 'ca': 'CA', 'world': a}[self.kind] + '.json')
                try: pk = json.load(open(f, encoding='utf-8')).get('parks') or {}
                except Exception: parts[a]['pins'] = H(b'missing'); continue  # noqa: BLE001
                if self.kind == 'ca': pk = {r: v for r, v in pk.items() if a in (self.ref_area.get(r) or ())}
                parts[a]['pins'] = H(canon({r: (v[:7] if isinstance(v, list) else v) for r, v in pk.items()}))   # name..lat, lon; not the activation counts
        if self.kind != 'fers' and self.reader == 'verdict': self.host_verdicts(parts, sh)
        for a in self.areas: parts[a].update(sh)
        return parts

    def host_verdicts(self, parts, sh):
        """The host rules as they stand in this tree (kpc_master.live_ok over kpc_net_guard, run from their own source in a private
        namespace: install() is never called, nothing is contacted), applied to every layer address an area reads."""
        fn = host_rule_fn(self.t, self.env.get('KPC_SAVED_ONLY_HOSTS', ''))
        def verdicts(us):
            out = []
            for u in sorted(us):
                try: ok, why = fn(u) if fn else (None, 'no shared host rules in this tree (they were in the rule files)')
                except Exception as e: ok, why = None, f'!error {e}'  # noqa: BLE001
                w = str(why).lower()   # the verdict CLASS, not its wording (a reworded message is not a rule change)
                cls = 'live' if ok is True else 'unknown' if ok is None else 'never' if ('never' in w or 'no request' in w) else 'saved-only' if 'saved' in w else 'refused'
                out.append((u, cls))
            return out
        for a in self.areas: parts[a]['hosts'] = H(canon(verdicts(self.urls.get(a, ()))))
        sh['hosts:shared-code-urls'] = H(canon(verdicts(self.urls.get('*', ()))))

    def locations(self, parts, sh, prefix):
        """locations.json (the site's pin list; the key reads it only as a pin fallback): POTA rows of this kind's parks only. A park in
        no key file and no pin file of this kind is never read by this key (its park list is the pin file), so it is not a part."""
        v, ok = self.t.json('locations.json')
        if not ok: sh['shared:locations.json' + ('!unreadable' if v is not None else '')] = H(b'missing' if v is None else b'!'); return
        by = {}
        for r in v if isinstance(v, list) else []:
            if not (isinstance(r, list) and len(r) > 4 and r[0] == 'POTA' and isinstance(r[1], str)): continue
            if prefix and not r[1].startswith(prefix): continue
            for a in self.ref_area.get(r[1]) or ():
                if a in self.areas_set: by.setdefault(a, []).append(r[1:5])
        for a, x in by.items(): parts[a]['data:locations.json(POTA pins of its parks)'] = H(canon(sorted(x)))
        if not self.data: sh['shared:locations.json#no-pin-files-given'] = H(canon(sorted(r[1:5] for r in v if isinstance(r, list) and len(r) > 4 and r[0] == 'POTA' and isinstance(r[1], str) and not self.ref_area.get(r[1]) and (not prefix or r[1].startswith(prefix)))))

    def gate(self, parts, sh, name, shared=False):
        lay, ok = self.t.json('data/outlines/layers.json')
        signed, ok2 = self.t.json('data/outlines/world-baselines.approved.json')
        base = (signed.get('baselines') or {}) if ok2 and isinstance(signed, dict) else {}
        rows = (lay.get('layers') or {}) if ok and isinstance(lay, dict) else {}
        by = {}
        # Only what a PERSON sets counts: the signed baseline (copy sha256 + count) and the layer rows' url / areas / never_contact /
        # outside_box_ok. The expected counts, read dates and match tallies are written by the key builds themselves (data/outlines/
        # layers.json is saved by every US / Canada key run): a build's own output is never its input, or every build would invalidate
        # itself. A baseline only decides whether a copy may be used (a hold writes nothing); the copy's own checksum is the input.
        for k, r in rows.items():
            if not isinstance(r, dict): continue
            if not any(x in r for x in ('never_contact', 'outside_box_ok')): continue   # rows the builds add themselves are state
            keep = {x: r.get(x) for x in ('url', 'areas', 'never_contact', 'outside_box_ok') if x in r}
            for ar in r.get('areas') or [k.split('.')[0] if '.' in k else '?']: by.setdefault(ar, {})[k] = keep
        for a in self.areas:
            g = {'signed': base.get(name(a)), 'layers': by.get(name(a))}
            if shared: sh['gate:' + name(a)] = H(canon(g))
            else: parts[a]['gate'] = H(canon(g))
        known = {name(a) for a in self.areas}
        rest = {ar: x for ar, x in by.items() if ar not in known and ar.startswith(('US-', 'CA-', 'W-')[('us', 'ca', 'world').index(self.kind)]) or ar == '?'}
        if rest: sh['gate:layer-rows-of-no-area'] = H(canon(rest))

    # ---- 2-fers
    def fers_parts(self, parts, sh):
        t = self.t; members = fers_areas(self.data)
        st_box = t.json('kpc-us-states.json')[0]
        ups = {}
        def up(state):
            if state in ups: return ups[state]
            k = 'us-key' if state.startswith('US-') else 'ca-key' if state.startswith('CA-') else 'world-key'
            f = f'data/{k}/{state if k != "world-key" else state[2:]}.json'
            v, ok = t.json(f)
            if ok and isinstance(v, dict):
                pk = {r: {x: y for x, y in p.items() if x != 'read'} if isinstance(p, dict) else p for r, p in (v.get('parks') or {}).items()}
                kd = H(canon({'parks': pk, 'st': v.get('st') or v.get('cc')}))
            else: kd = H(b'missing' if v is None else b'!unreadable')
            outs = t.ls('data/outlines/', r'^' + re.escape(state) + r'(\.p\d+)?\.geojson\.gz$')
            od = []
            for o in outs:
                b = t.read(o)
                try: od.append(H(gzip.decompress(b)))
                except Exception: od.append(H(b'!unreadable'))  # noqa: BLE001
            ups[state] = (kd, H('\n'.join(od)))
            return ups[state]
        scope, ok = t.json(SCOPE_READ['fers'])
        st_scoped, sh_scope = {}, []
        for c in (scope.get('changes') or []) if ok and isinstance(scope, dict) else []:
            sc = c.get('scope') if isinstance(c, dict) else None
            if isinstance(sc, dict) and sc.get('states') and not any(sc.get(x) for x in ('kinds', 'flags', 'parks', 'all')):
                for s in sc['states']: st_scoped.setdefault(s if '-' in s else 'US-' + s, []).append(c)
            else: sh_scope.append(c)
        # the scope file is already a code part (SCOPE_READ); level 3 replaces it by its state-scoped slices + the rest
        if self.level >= 3:
            sh['code:' + SCOPE_READ['fers']] = H(canon(sh_scope))
        lay, okl = t.json('data/us-key/layers.json')
        for tag in self.areas:
            mem = members[tag]
            nb = sorted(set(neighbours(st_box, mem)) - set(mem))
            p = parts[tag]
            for s in mem:
                kd, od = up(s); p[f'up:key:{s}'] = kd; p[f'up:outline:{s}'] = od
                if s in st_scoped and self.level >= 3: p[f'code-area:fers-rule-scope:{s}'] = H(canon(st_scoped[s]))
            for s in nb:
                kd, od = up(s); p[f'up:key:{s}(neighbour)'] = kd; p[f'up:outline:{s}(neighbour)'] = od
            if okl and isinstance(lay, dict):
                p['data:data/us-key/layers.json(sg prefixes)'] = H(canon({k: v for k, v in lay.items() if any(k.startswith('sg' + s[3:].lower()) for s in mem if s.startswith('US-'))}))
        if okl and isinstance(lay, dict): sh['shared:data/us-key/layers.json(national)'] = H(canon({k: v for k, v in lay.items() if not k.startswith('sg')}))
        # per-park files 2-fers read: point circles, approximate outlines, overrides (by the member states' parks)
        for f in ('data/point-circles.json', 'data/fers-approx-outlines.json', 'data/us-key/overrides.json', 'data/ca-key/overrides.json'):
            v, ok = t.json(f)
            if not ok: sh[f'shared:{f}' + ('!unreadable' if v is not None else '')] = H(b'missing' if v is None else b'!'); continue
            rows, rest = ref_rows(v)
            if rows is None: sh[f'shared:{f}'] = H(canon(v)); continue
            un = {}
            for tag in self.areas:
                mem = set(members[tag])
                parts[tag][f'data:{f}'] = H(canon({r: x for r, x in rows.items() if self.ref_area.get(r, set()) & mem}))
            un = {r: x for r, x in rows.items() if not self.ref_area.get(r)}
            if un and not self.data: sh[f'shared:{f}#rows-in-no-key'] = H(canon(un))   # see slice_file
            if rest: sh[f'shared:{f}#other'] = H(canon(rest))
        self.slice_file('data/state-gis.json', parts, sh, label='data/state-gis.json', key_of=lambda v: (
            {tag: {s: (v.get('states') or {}).get(s.split('-')[1]) for s in members[tag]} for tag in self.areas} if isinstance(v, dict) else {}, {}))


def host_rule_fn(tree, extra_hosts=''):
    """live_ok(url) of this tree's kpc_master.py (with its kpc_net_guard.py), or None when the tree has no kpc_master.live_ok."""
    import types, tempfile
    ng_src, km_src = tree.read(READER[1]), tree.read(READER[0])
    if not km_src or b'def live_ok' not in km_src: return None
    td = tempfile.mkdtemp(prefix='kpc-area-hash-')
    lj = tree.read('data/outlines/layers.json') or b'{}'
    open(os.path.join(td, 'layers.json'), 'wb').write(lj)
    old = {k: os.environ.get(k) for k in ('KPC_LAYERS_JSON', 'KPC_SAVED_ONLY_HOSTS')}
    os.environ['KPC_LAYERS_JSON'] = os.path.join(td, 'layers.json'); os.environ['KPC_SAVED_ONLY_HOSTS'] = extra_hosts
    try:
        ng = types.ModuleType('kpc_net_guard'); ng.__file__ = os.path.join(td, 'kpc_net_guard.py')
        if ng_src: exec(compile(ng_src, 'kpc_net_guard.py', 'exec'), ng.__dict__)   # before Nov 10 (#120) kpc_master had the rules alone
        mod = ast.parse(km_src.decode('utf-8'))
        keep = [n for n in mod.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) or (isinstance(n, ast.Assign) and not any(
            isinstance(x, ast.Call) and getattr(x.func, 'attr', '') == 'install' for x in ast.walk(n)))
            or (isinstance(n, (ast.Import, ast.ImportFrom)) and all(a.name.split('.')[0] in sys.stdlib_module_names for a in n.names))]
        km = {'__name__': 'kpc_master_hosts', '__file__': os.path.join(td, 'kpc_master.py'), 'kpc_net_guard': ng}
        exec(compile(ast.Module(body=keep, type_ignores=[]), 'kpc_master.py', 'exec'), km)
        lo = km['live_ok']
        def fn(u):
            keep = {k: os.environ.get(k) for k in ('KPC_LAYERS_JSON', 'KPC_SAVED_ONLY_HOSTS')}
            os.environ['KPC_LAYERS_JSON'] = os.path.join(td, 'layers.json'); os.environ['KPC_SAVED_ONLY_HOSTS'] = extra_hosts
            try: return lo(u)
            finally:
                for k, v in keep.items():
                    if v is None: os.environ.pop(k, None)
                    else: os.environ[k] = v
        import atexit, shutil; atexit.register(shutil.rmtree, td, True)
        return fn
    except Exception:  # noqa: BLE001
        return lambda u: (None, '!host rules could not be loaded: every area moves when they change')
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def group(v, fn):
    out = {}
    if isinstance(v, dict):
        for k, x in v.items(): out.setdefault(fn(k), {})[k] = x
    return out


def state_box(v, st):
    for b in v if isinstance(v, list) else []:
        if isinstance(b, dict) and b.get('a') == st:
            try:
                xs = [q[0] for pl in b['p'] for q in pl[0]]; ys = [q[1] for pl in b['p'] for q in pl[0]]
                return [min(xs), min(ys), max(xs), max(ys)]
            except Exception: return None  # noqa: BLE001
    return None


def boxes_near(v, st, pad=0.3):
    """The state's own drawn outline + the outlines of the states whose box is within `pad` degrees (the PAD-US cross-state ask)."""
    me = state_box(v, st); out = {}
    for b in v if isinstance(v, list) else []:
        if not isinstance(b, dict): continue
        if b.get('a') == st: out[st] = b; continue
        bb = state_box(v, b.get('a'))
        if me and bb and not (bb[2] < me[0] - pad or bb[0] > me[2] + pad or bb[3] < me[1] - pad or bb[1] > me[3] + pad): out[b.get('a')] = b
    return out


def neighbours(v, members, pad=0.5):
    """Areas (US-XX) whose state box is within `pad` degrees of the members' boxes. Canada has no boxes here: every CA province
    of the same key is a neighbour (the safe side)."""
    out = set()
    us = [m[3:] for m in members if m.startswith('US-')]
    for m in us:
        me = state_box(v, m)
        if not me: return ['US-' + s for s in US_ALL]   # no box = every state (fail closed)
        for b in v if isinstance(v, list) else []:
            bb = state_box(v, b.get('a')) if isinstance(b, dict) else None
            if bb and b.get('a') in US_ALL and not (bb[2] < me[0] - pad or bb[0] > me[2] + pad or bb[3] < me[1] - pad or bb[1] > me[3] + pad):
                out.add('US-' + b['a'])
    if any(m.startswith('CA-') for m in members):
        out |= {'CA-' + c for c in 'AB BC MB NB NL NS NT NU ON PE QC SK YT SI SP'.split()}
    return sorted(out)


FERS_FALLBACK = {   # the chain list R of KPC-Data .github/scripts/kpc_fers_chain_plan.py (sha 827d39c4), used when --data is not given
    'southeast': 'US-TN US-NC US-VA US-WV US-GA US-AL US-SC US-FL US-MS', 'midwest': 'US-IN US-IL US-MO US-WI US-MN US-IA US-ND US-SD',
    'northeast': 'US-PA US-NY US-NJ US-CT US-RI US-MA US-VT US-NH US-ME US-MD US-DE US-DC', 'southcentral': 'US-AR US-LA US-OK US-TX US-KS US-NE',
    'mountain': 'US-CO US-WY US-ID US-MT US-NV US-AZ US-NM', 'pacific': 'US-CA US-OR US-WA US-AK US-HI', 'oh': 'US-OH', 'mi': 'US-MI', 'ut': 'US-UT',
    'canadaeast': 'CA-ON CA-QC CA-NB CA-NS CA-PE CA-NL', 'canadawest': 'CA-MB CA-SK CA-AB CA-BC CA-YT CA-NT CA-NU'}


def fers_area_groups(data):
    """(source, {tag: [states]}): the 2-fer area list as one source of truth. Nov 12 (KPC owner, 2026-11-12; part C in KPC-Data retires the
    chain's own list R and drives the chain from the bot's list): KPC-Data .github/fers-areas.json first; the chain's R only when that
    file is absent (a KPC-Data checkout from before part C that has no fers-areas.json); the frozen copy above only when no checkout is
    given or neither can be read. Never raises. World areas (W-*) are left out: no world country is 2-fer ready."""
    if data:
        root = pathlib.Path(data)
        try:
            a = json.load(open(root / '.github/fers-areas.json', encoding='utf-8')).get('areas')
            if isinstance(a, dict) and a:
                return 'fers-areas.json', {k: v.split() for k, v in a.items() if isinstance(v, str) and not v.startswith('W-')}
        except Exception: pass  # noqa: BLE001
        try:
            for st in ast.parse((root / '.github/scripts/kpc_fers_chain_plan.py').read_text(encoding='utf-8')).body:
                if isinstance(st, ast.Assign) and isinstance(st.targets[0], ast.Name) and st.targets[0].id == 'R':
                    r = ast.literal_eval(st.value)
                    if isinstance(r, dict) and r: return 'chain R', {k: v.split() for k, v in r.items() if isinstance(v, str) and not v.startswith('W-')}
        except Exception: pass  # noqa: BLE001
    return 'frozen fallback', {k: v.split() for k, v in FERS_FALLBACK.items()}


def fers_areas(data):
    """{'US-FL': ['US-FL'], ...}: the 2-fer UNIT is the state / province (SHARED-SCHEME section 1, the same as KPC-Data part C); the
    named areas only group jobs. Every state / province of the area list is one unit; its neighbours enter through the up: parts."""
    _, groups = fers_area_groups(data)
    units = sorted({s for v in groups.values() for s in v if re.fullmatch(r'(US|CA)-[A-Z]{2}', s)})
    return {u: [u] for u in units}


# ---------------------------------------------------------------- hashing, diff, replay
def area_hashes(parts):
    return {a: H(b''.join(k.encode() + b'\0' + v.encode() + b'\n' for k, v in sorted(p.items())))[:12] for a, p in parts.items()}


def compute(repo, rev, kind, level=3, data=None, other_rev=None, reader='shared', env=None):
    k = Kind(Tree(repo, rev), kind, level, data, Kind(Tree(repo, other_rev), kind, level, data) if other_rev else None, reader, env)
    p = k.parts()
    return area_hashes(p), p


def diff_parts(pa, pb):
    """{area: [why, ...]} for the areas whose parts differ (a part added, removed or changed)."""
    out = {}
    for a in sorted(set(pa) | set(pb)):
        x, y = pa.get(a), pb.get(a)
        if x is None: out[a] = ['new area']; continue
        if y is None: out[a] = ['area removed']; continue
        w = [f'{n} changed' if n in x and n in y else (f'{n} added' if n in y else f'{n} removed') for n in sorted(set(x) | set(y)) if x.get(n) != y.get(n)]
        if w: out[a] = w
    return out


def git(repo, *a):
    return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True).stdout


def declared_today(ta, tb, kind, areas):
    """What today's system rebuilds for the move: the US key honours the scope entries this commit added (states); Canada builds as
    one whole-country job; the world key and the 2-fer chain have no per-area rows, so everything. (count, note)"""
    if kind != 'us': return len(areas), {'ca': 'one whole-Canada job', 'world': 'no per-country rows: every country', 'fers': 'every area starts (area fingerprint holds the 2-fer hash); pairs reused per declared scope'}[kind]
    f = '.github/us-key-rule-scope.json'
    va, _ = ta.json(f); vb, ok = tb.json(f)
    if not ok: return len(areas), 'no scope file: every state'
    old = {c.get('id') for c in (va or {}).get('changes', [])} if isinstance(va, dict) else set()
    new = [c for c in vb.get('changes', []) if c.get('id') not in old]
    if not new: return len(areas), 'no new scope entry: every state'
    st = set()
    for c in new:
        sc = c.get('scope')
        if sc == 'none': continue
        if not isinstance(sc, dict) or sc.get('all') or not (sc.get('states') or sc.get('parks')): return len(areas), f"scope all ({c.get('id')})"
        st |= {x[3:] if str(x).startswith('US-') else x for x in sc.get('states') or []}
    return len(st), 'declared: ' + (' '.join(sorted(st)) or 'none')


def region_moves(repo, since=None):
    revs = git(repo, 'rev-list', '--first-parent', '--reverse', f'{since}..HEAD' if since else 'HEAD').split()
    prev, out = None, []
    for r in revs:
        files = git(repo, 'diff-tree', '--no-commit-id', '--name-only', '-r', r + '^', r).split() if prev else None
        if prev and files is not None and not any(f.startswith('.github/') for f in files):
            continue   # region hashes only read .github files
        t = Tree(repo, r)
        try: hs = {k: region_hash(t, KINDS[k]) for k in KINDS}
        except Exception: continue  # noqa: BLE001  (before kpc_key_freeze had RULE_FILES)
        if prev and hs != prev[1]:
            out.append((r + '^', r, {k: (prev[1][k], hs[k]) for k in hs if prev[1][k] != hs[k]}))   # skipped commits touch no .github file
        prev = (r, hs)
    return out


MODES = (('L1_bytes', 1, 'off'), ('L2_tokens', 2, 'off'), ('L3_step1', 3, 'shared'), ('L3_design', 3, 'verdict'))


def moved(ta, tb, kind, data, lv, reader):
    A0, B0 = Kind(ta, kind, lv, data, None, reader), Kind(tb, kind, lv, data, None, reader)
    A = Kind(ta, kind, lv, data, B0, reader); B = Kind(tb, kind, lv, data, A0, reader)
    return len(B.areas), diff_parts(A.parts(), B.parts())


def replay(repo, data, since, csv_path, kinds=None):
    """Every region-hash move on first-parent history: how many areas today's system rebuilds and how many each level would."""
    rows = []
    for pa, pb, mv in region_moves(repo, since):
        ta, tb = Tree(repo, pa), Tree(repo, pb)
        subj = git(repo, 'show', '-s', '--format=%ci|%s', pb).strip()
        for kind, (ha, hb) in mv.items():
            if kinds and kind not in kinds: continue
            if ha is None: continue   # the kind did not exist before this commit
            res = {name: moved(ta, tb, kind, data, lv, rd) for name, lv, rd in MODES}
            n, d3 = res['L3_design']
            today, note = declared_today(ta, tb, kind, Kind(tb, kind, 3, data).areas if kind != 'fers' else list(fers_areas(data)))
            why = sorted({w.split(' ')[0] for ws in d3.values() for w in ws})
            # the areas that still move when the shared-code part is set aside: what a proven 'no result change' stamp leaves
            nc = sorted(a for a, ws in d3.items() if any(not w.startswith(('code:', 'version ', 'hosts:shared')) for w in ws))
            r = {'commit': pb[:10], 'date': subj.split('|')[0][:16], 'subject': subj.split('|', 1)[-1][:80], 'kind': kind,
                 'region_old': ha, 'region_new': hb, 'areas': n, 'today_rebuilt': today, 'today_note': note}
            r.update({name: len(res[name][1]) for name, _, _ in MODES})
            r.update({'L3_design_areas': ' '.join(sorted(d3)) if len(d3) < n else 'ALL', 'L3_design_parts_moved': ' | '.join(why)[:600],
                      'with_proof_stamp': len(nc), 'with_proof_areas': ' '.join(nc)})
            rows.append(r)
            print(f"{pb[:10]} {kind:5} {ha}->{hb} areas {n:3} today {today:3} " + ' '.join(f"{k.split('_')[0]}{'s' if k == 'L3_step1' else ''} {r[k]:3}" for k, _, _ in MODES)
                  + f" proof {len(nc):3} | {r['L3_design_areas'][:40]} | {' '.join(nc)[:40]}", flush=True)
    if csv_path:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['commit']); w.writeheader(); w.writerows(rows)
    return rows


INPUT_PATHS = ['data/us-key/overrides.json', 'data/ca-key/overrides.json', 'data/world-key/overrides.json', 'data/state-gis.json',
               'data/world-key/extra-layers.json', 'data/world-key/sheet-countries.json', 'data/world-key/eea-designations.json',
               'data/world-key/jp-wikidata.json', 'data/ca-key/layers.json', 'data/ca-key/hardlook-joins.json', 'kpc-us-states.json',
               'data/retired-refs.json', 'data/park-transfers.json', 'data/nps-units.json', 'data/outlines/layers.json',
               'data/outlines/world-baselines.approved.json', 'data/us-key/layers.json'] + READER


def build_marks(repo, kind):
    """[(commit time, commit, {areas built})] of the key builds on first-parent history, oldest first. US: a state's index row
    changed (its 'seconds' change every build); Canada / world: the index 'build' stamp changed (every area not named failed)."""
    ix = {'us': 'data/us-key/index.json', 'ca': 'data/ca-key/index.json', 'world': 'data/world-key/index.json'}[kind]
    out, prev = [], None
    for line in git(repo, 'log', '--first-parent', '--reverse', '--format=%H %ct', '--', ix).split('\n'):
        if not line.strip(): continue
        c, ts = line.split()
        v, ok = Tree(repo, c).json(ix)
        if not ok or not isinstance(v, dict): continue
        rows = v.get({'us': 'states', 'ca': 'provinces', 'world': 'countries'}[kind]) or {}
        if kind == 'us':
            nr = lambda r: {k: x for k, x in (r or {}).items() if k != 'rules'} if isinstance(r, dict) else r   # a re-stamp of 'rules' is not a build
            got = {a for a, r in rows.items() if prev is None or nr((prev.get('states') or {}).get(a)) != nr(r)}
        else:
            got = set(rows) - set(v.get('failed') or []) if prev is None or prev.get('build') != v.get('build') else set()
        if got: out.append((int(ts), c, got))
        prev = v
    return out


def holes(repo, data, since, csv_path):
    """The soundness hole, measured: first-parent commits that changed a build input but moved NO region hash. For each, the areas
    whose design hash moves, and how long until each of them was next built (from the index files)."""
    revs = git(repo, 'log', '--first-parent', '--reverse', '--format=%H %ct', *( [f'{since}..HEAD'] if since else []), '--', *INPUT_PATHS).split('\n')
    marks = {k: build_marks(repo, k) for k in ('us', 'ca', 'world')}
    head_t = int(git(repo, 'show', '-s', '--format=%ct', 'HEAD').strip())
    rows = []
    for line in revs:
        if not line.strip(): continue
        c, ts = line.split(); ts = int(ts)
        try: ta, tb = Tree(repo, c + '^'), Tree(repo, c)
        except subprocess.CalledProcessError: continue   # the shallow clone's first commit
        try:
            if any(region_hash(ta, KINDS[k]) != region_hash(tb, KINDS[k]) for k in ('us', 'ca', 'world')): continue
        except Exception: continue  # noqa: BLE001
        files = [f for f in git(repo, 'diff-tree', '--no-commit-id', '--name-only', '-r', c + '^', c).split() if f in INPUT_PATHS]
        subj = git(repo, 'show', '-s', '--format=%ci|%an|%s', c).strip().split('|', 2)
        for kind in ('us', 'ca', 'world'):
            n, d = moved(ta, tb, kind, data, 3, 'verdict')
            if not d: continue
            waits = []
            for a in d:
                nxt = next((t for t, _, got in marks[kind] if t > ts and a in got), None)
                waits.append((nxt - ts) / 3600.0 if nxt else None)
            known = [w for w in waits if w is not None]
            rows.append({'commit': c[:10], 'date': subj[0][:16], 'author': subj[1][:30], 'subject': subj[2][:80], 'kind': kind,
                         'files': ' '.join(files), 'areas': n, 'areas_moved': len(d), 'which': ' '.join(sorted(d))[:300],
                         'next_build_h_max': round(max(known), 1) if known else '', 'not_rebuilt_since': sum(1 for w in waits if w is None),
                         'not_rebuilt_areas': ' '.join(sorted(a for a, w in zip(d, waits) if w is None))[:300],
                         'hours_to_head': round((head_t - ts) / 3600.0, 1), 'parts': ' | '.join(sorted({w.split(' ')[0] for ws in d.values() for w in ws}))[:300]})
            r = rows[-1]
            print(f"{c[:10]} {kind:5} {r['areas_moved']:3}/{n:3} max wait {r['next_build_h_max']!s:>6} h, never rebuilt since: {r['not_rebuilt_since']:3} {r['not_rebuilt_areas'][:50]} | {r['files'][:60]}", flush=True)
    if csv_path and rows:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows


def migrate(repo, data, kind, reader, window_h=6.0, csv_path=None, quiet=False):
    """Which areas can be stamped honestly with the design hash of HEAD without a rebuild. An area is PROVEN when (1) git shows its
    last build (build_marks), (2) its parts at the parent of that build's save commit equal its parts at HEAD, and (3) its parts were the
    same at every commit that touched an input or rule file in the window_h hours before that save (the build checked out an earlier
    main than the one it saved onto). Anything else = rebuild in the migration run."""
    marks = build_marks(repo, kind)
    head = Kind(Tree(repo, 'HEAD'), kind, 3, data, None, reader); hp = head.parts()
    cache = {}
    def parts_at(rev):
        if rev not in cache:
            try: cache[rev] = Kind(Tree(repo, rev), kind, 3, data, head, reader).parts()
            except Exception: cache[rev] = {}  # noqa: BLE001
        return cache[rev]
    rows = []
    for a in head.areas:
        last = next(((t, c) for t, c, got in reversed(marks) if a in got), None)
        if not last: rows.append((a, '', 'no build of this area in the reachable history', 'rebuild')); continue
        t, c = last
        pa = parts_at(c + '^').get(a)
        if pa is None: rows.append((a, c[:10], 'inputs at the build cannot be read', 'rebuild')); continue
        d = diff_parts({a: pa}, {a: hp[a]}).get(a)
        if d: rows.append((a, c[:10], 'inputs changed since its last build: ' + '; '.join(d)[:200], 'rebuild')); continue
        win = [] if window_h <= 0 else git(repo, 'log', '--first-parent', '--format=%H', f'--since={t - int(window_h * 3600)}', f'--until={t - 1}', c + '^', '--',
                  *INPUT_PATHS, '.github/').split()
        bad = next((w for w in win if diff_parts({a: parts_at(w).get(a) or {}}, {a: hp[a]})), None)
        if bad: rows.append((a, c[:10], f'an input changed while its last build ran (commit {bad[:10]})', 'rebuild')); continue
        rows.append((a, c[:10], 'proven: same inputs at its last build as at HEAD', 'stamp'))
    n = sum(1 for r in rows if r[3] == 'stamp')
    if not quiet:
        print(f'# {kind} (reader {reader}): {n} of {len(rows)} areas can be stamped from git; {len(rows) - n} need the migration rebuild')
        print('area | last build commit | why | action')
        for r in rows: print(' | '.join(r))
    if csv_path:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['kind', 'reader', 'area', 'last_build_commit', 'why', 'action']); w.writerows([(kind, reader) + r for r in rows])
    return rows


# ================================================================ Nov 12 (KPC owner, 2026-11-12): the key workflows' side (part B)
ROWS_KEY = {'us': 'states', 'ca': 'provinces', 'world': 'countries'}
KEY_PATH = {'us': 'data/us-key/US-{a}.json', 'ca': 'data/ca-key/CA-{a}.json', 'world': 'data/world-key/{a}.json'}
MODES_RUN = ('shadow', 'add', 'reuse')
# parts that only a shared-code change moves (the same for every area): the D4 proof stamp may bridge these, nothing else
CODE_PARTS = ('code:', 'version', 'hosts:shared', 'reader:')
STAMP_FILE = '.github/no-result-change.json'
PROOF_DIR = 'data/status/no-result-change'


def short(parts):
    return {k: v[:12] for k, v in sorted(parts.items())}


def sha_file(p):
    try: return H(pathlib.Path(p).read_bytes())
    except OSError: return None


def code_hash(repo, kind):
    """The region CODE hash = kpc_key_freeze rules_hash (today's 'rules hash'), read the same way (from the files on disk)."""
    return region_hash(Tree(repo, None), KINDS[kind])


def _signed(by, date, persons, today=None):
    """A real person's sign-off ('KPC owner' alone is not a signature), dated, not in the future."""
    import datetime
    who = {str(w).strip().lower() for w in persons if str(w).strip().lower() != 'kpc owner'}
    names = set()
    for part in re.split(r'[,;+&]|\band\b', str(by or '')):
        m = re.fullmatch(r'\s*(.+?)\s*\(([^)]+)\)\s*', part)
        if m: names |= {m.group(1).strip().lower(), m.group(2).strip().lower()}
        elif part.strip(): names.add(part.strip().lower())
    if not names & who: return False
    try: d = datetime.date.fromisoformat(str(date or '').strip()[:10])
    except ValueError: return False
    return d <= (today or datetime.date.today())


def proof_valid(repo, kind, frm, to, persons=None, today=None):
    """(True, id) when a VALID 'no result change' stamp (D4) covers the code-hash move frm -> to of this kind; else (False, why).
    Valid only when: an entry of .github/no-result-change.json names this kind, from, to, claim no-result-change and a proof id, and is
    signed by a real person; its proof record data/status/no-result-change/<id>.json has format 1, the same id / kind / from / to,
    result pass, network_attempts 0, a non-empty sample and every compared file pair equal (two sha256 values). Missing, failed,
    unsigned or stale (to is not the current code hash) = not valid: the shared-code change rebuilds every area (fail closed)."""
    repo = pathlib.Path(repo)
    if not frm or not to: return False, 'no code hash recorded for the area\'s last build'
    if frm == to: return True, 'same code hash'
    if persons is None:
        persons = [x.strip() for x in (os.environ.get('KPC_PERSONS') or 'Brandon,KZ4CP').split(',') if x.strip()]
    try: doc = json.loads((repo / STAMP_FILE).read_text(encoding='utf-8'))
    except FileNotFoundError: return False, f'no proof stamp file ({STAMP_FILE})'
    except Exception as e: return False, f'{STAMP_FILE} unreadable ({type(e).__name__})'  # noqa: BLE001
    why = f'no stamp for {KINDS[kind]} {frm} -> {to}'
    for e in (doc.get('stamps') if isinstance(doc, dict) else None) or []:
        if not isinstance(e, dict) or e.get('kind') != KINDS[kind] or e.get('from') != frm or e.get('to') != to: continue
        if e.get('claim') != 'no-result-change': why = 'stamp claim is not no-result-change'; continue
        if not _signed(e.get('approved_by'), e.get('approved_date'), persons, today): why = 'stamp not signed by a person'; continue
        pid = str(e.get('proof') or '')
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,80}', pid): why = 'stamp names no proof record'; continue
        try: rec = json.loads((repo / PROOF_DIR / f'{pid}.json').read_text(encoding='utf-8'))
        except Exception: why = f'proof record {pid} missing or unreadable'; continue  # noqa: BLE001
        if not isinstance(rec, dict) or rec.get('format') != 1 or rec.get('id') != pid or rec.get('kind') != KINDS[kind] or rec.get('from') != frm or rec.get('to') != to:
            why = f'proof record {pid} does not match the stamp'; continue
        if rec.get('result') != 'pass': why = f"proof {pid} result {rec.get('result')!r}"; continue
        if rec.get('network_attempts') != 0: why = f'proof {pid} tried the network'; continue
        files = rec.get('files')
        if not isinstance(rec.get('sample'), list) or not rec['sample'] or not isinstance(files, dict) or not files:
            why = f'proof {pid} has no sample or no compared files'; continue
        if not all(isinstance(v, list) and len(v) == 2 and re.fullmatch(r'[0-9a-f]{64}', str(v[0])) and v[0] == v[1] for v in files.values()):
            why = f'proof {pid}: a compared file differs'; continue
        return True, pid
    return False, why


def decide(kind, wanted, hashes, parts, rows, cur_code, mode='shadow', force_full=False, repo=REPO, proof=proof_valid):
    """The plan's per-area decision. wanted = the areas today's plan builds. Returns (final list, table rows
    [(area, old hash, new hash, reason, action)], added, reused). Step 1 (add) only ADDS areas whose inputs moved; reuse leaves out a
    wanted area whose inputs did not move (or moved only in shared code covered by a valid D4 proof), whose key file is still the
    recorded bytes and whose row is on the current code hash. shadow changes nothing. force_full = no reuse."""
    if mode not in MODES_RUN: mode = 'shadow'
    wanted = list(dict.fromkeys(wanted)); table, added, reused = [], [], []
    for a in sorted(set(hashes) | set(wanted)):
        row = rows.get(a) if isinstance(rows.get(a), dict) else {}
        old, new = row.get('area_hash'), hashes.get(a)
        np = short(parts.get(a) or {}); op = row.get('area_parts') if isinstance(row.get('area_parts'), dict) else None
        if new is None: reason = 'not an area of this kind (no hash): built as asked'
        elif not old: reason = 'no area hash recorded (never built with one): moved'
        elif old == new: reason = 'no input changed'
        elif op is None: reason = 'area hash moved (no parts recorded)'
        else: reason = 'moved: ' + '; '.join(sorted({k for k in set(op) | set(np) if op.get(k) != np.get(k)}))[:300]
        moved = new is None or old != new
        ok_file = row.get('out_sha') and row.get('out_sha') == sha_file(pathlib.Path(repo) / KEY_PATH[kind].format(a=a))
        can = False; how = ''
        if not force_full and a in wanted and ok_file and row.get('complete', True) is not False:
            if not moved and row.get('rules') == cur_code: can, how = True, 'inputs and code unchanged'
            elif op is not None and new is not None and row.get('rules') and row.get('rules') != cur_code \
                    and all(op.get(k) == np.get(k) for k in set(op) | set(np) if not k.startswith(CODE_PARTS)):
                pv, pid = proof(repo, kind, row.get('rules'), cur_code)
                if pv: can, how = True, f'only shared code moved, proven no result change ({pid})'
                else: reason += f' (shared code only; no valid proof: {pid})'
        if a in wanted:
            if can and mode == 'reuse': action = 'reuse'; reused.append(a); reason = how
            elif can: action = 'rebuild (would reuse: ' + how + ')'
            else: action = 'rebuild'
        elif moved and new is not None:
            if mode in ('add', 'reuse'): action = 'rebuild (added: inputs moved since its last build)'; added.append(a)
            else: action = 'would add (shadow)'
        else: action = 'not planned'
        table.append((a, old or '-', new or '-', reason, action))
    final = [a for a in wanted if a not in reused] + [a for a in added if a not in wanted]
    return final, table, added, reused


def run_plan(repo, kind, wanted, index, mode, force_full, data=None, env=None, out_json=None, summary=None):
    repo = pathlib.Path(repo)
    try: idx = json.loads(pathlib.Path(index).read_text(encoding='utf-8'))
    except Exception: idx = {}  # noqa: BLE001
    rows = idx.get(ROWS_KEY[kind]) or {}
    hs, parts = compute(repo, None, kind, 3, data, None, 'verdict', env)
    cur = code_hash(repo, kind)
    final, table, added, reused = decide(kind, wanted, hs, parts, rows, cur, mode, force_full, repo)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo, capture_output=True, text=True).stdout.strip()
    t = (f'**Area hashes ({kind}, mode {mode}{", full rebuild asked: no reuse" if force_full else ""}; code hash {cur}; composition {COMPOSITION})**'
         + (f' - added {len(added)}: {" ".join(added)}' if added else '') + (f' - reused {len(reused)}: {" ".join(reused)}' if reused else '')
         + '\n\n| area | old hash | new hash | reason | action |\n|---|---|---|---|---|\n'
         + ''.join('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |\n' for r in table if r[4] != 'not planned' or r[3] != 'no input changed'))
    dest = summary or os.environ.get('GITHUB_STEP_SUMMARY')
    if dest: open(dest, 'a', encoding='utf-8').write(t + '\n')
    rec = {'kind': kind, 'mode': mode, 'force_full': bool(force_full), 'code_hash': cur, 'composition': COMPOSITION, 'plan_sha': head, 'pins': bool(data),
           'list': final, 'added': added, 'reused': reused, 'hashes': {a: hs[a] for a in sorted(hs)}, 'parts': {a: short(parts[a]) for a in sorted(parts)}}
    if out_json: pathlib.Path(out_json).write_text(json.dumps(rec, sort_keys=True, separators=(',', ':')), encoding='utf-8')
    return rec, t


def stamp_rows_parts(repo, kind, index, saved, part_dirs):
    """The US: each build job hashed its own states on its own checkout (part/area-plan.json, part/built-sha.txt). A saved state is
    stamped from the part that owns it; the rest as stamp_rows."""
    done_all, same_all, owner = [], True, {}
    for d in sorted(pathlib.Path(x) for x in part_dirs):
        try: sts = (d / 'states.txt').read_text().split()
        except OSError: continue
        for st in sts: owner.setdefault(st, d)
    for d in sorted(set(owner.values())):
        mine = [a for a in saved if owner.get(a) == d]
        if not mine: continue
        try: plan = json.loads((d / 'area-plan.json').read_text(encoding='utf-8'))
        except Exception: plan = {}  # noqa: BLE001
        try: bs = (d / 'built-sha.txt').read_text().strip()
        except OSError: bs = ''
        done, same = stamp_rows(repo, kind, index, mine, dict(plan, reused=[]), bs, rebuilt=saved)
        done_all += done; same_all = same_all and same
    if not owner: stamp_rows(repo, kind, index, [], {}, '', rebuilt=saved)
    return sorted(done_all), same_all


def stamp_rows(repo, kind, index, saved, plan, built_sha, rebuilt=None):
    """Record, for each area SAVED this run, its area hash, its parts, the sha256 of its key file and the commit it was built from, in
    its index row; and the lists areas_rebuilt / areas_reused at the top (Quality grades the rebuilt areas plus the whole-key check).
    Written only when the build checked out the commit the plan hashed (else the hash would not be the build's; the area then has no
    area_hash and is planned again). Rows of areas not saved are not touched."""
    repo = pathlib.Path(repo); ip = pathlib.Path(index)
    d = json.loads(ip.read_text(encoding='utf-8')); rows = d.setdefault(ROWS_KEY[kind], {})
    plan = plan or {}
    same = bool(plan.get('plan_sha')) and plan.get('plan_sha') == built_sha
    done = []
    for a in saved:
        r = rows.get(a)
        if not isinstance(r, dict): continue
        for k in ('area_hash', 'area_parts', 'out_sha', 'built_sha'): r.pop(k, None)
        if same and a in (plan.get('hashes') or {}):
            r['area_hash'] = plan['hashes'][a]; r['area_parts'] = (plan.get('parts') or {}).get(a) or {}
            r['out_sha'] = sha_file(repo / KEY_PATH[kind].format(a=a)); r['built_sha'] = built_sha; done.append(a)
    d['areas_rebuilt'] = sorted(rebuilt if rebuilt is not None else saved)
    d['areas_reused'] = sorted(plan.get('reused') or [])
    ip.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding='utf-8')   # the stamp's own format (json.dump indent 1)
    return done, same


def sanity(repo, kind, index=None):
    """The whole-key sanity check (after every run, reused areas included). [problems]; empty = pass.
      1 every area key file has an index row, every index row a key file (an area named failed or held may lack a file);
      2 a row with out_sha matches its key file's sha256 (a reused or kept file is what was built);
      3 a row with area_hash also carries the code hash it was built on (rules) and its parts;
      4 a key-wide 'rules' never claims more than the rows: on a build that says it is complete, no row (not failed / held) carries
        another code hash;
      5 areas_rebuilt and areas_reused do not overlap."""
    repo = pathlib.Path(repo)
    ip = pathlib.Path(index) if index else repo / {'us': 'data/us-key', 'ca': 'data/ca-key', 'world': 'data/world-key'}[kind] / 'index.json'
    try: d = json.loads(ip.read_text(encoding='utf-8'))
    except Exception as e: return [f'index unreadable ({type(e).__name__})']  # noqa: BLE001
    rows = d.get(ROWS_KEY[kind]) or {}
    rx = {'us': r'^US-([A-Z]{2})\.json$', 'ca': r'^CA-([A-Z]{2})\.json$', 'world': r'^([A-Z]{2})\.json$'}[kind]
    files = {re.match(rx, f.name).group(1) for f in (ip.parent).iterdir() if re.match(rx, f.name)}
    failed = set(d.get('failed') or []) | set(d.get('held_expected') or [])
    bad = []
    for a in sorted(files - set(rows)): bad.append(f'1 {a}: key file with no index row')
    for a in sorted(set(rows) - files - failed): bad.append(f'1 {a}: index row with no key file')
    for a, r in sorted(rows.items()):
        if not isinstance(r, dict): continue
        if r.get('out_sha') and r['out_sha'] != sha_file(repo / KEY_PATH[kind].format(a=a)): bad.append(f'2 {a}: out_sha is not the key file\'s sha256')
        if r.get('area_hash') and not (r.get('rules') and isinstance(r.get('area_parts'), dict)): bad.append(f'3 {a}: area_hash without rules / parts')
    kw = d.get('rules')
    if kw and d.get('complete') is not False:
        off = sorted(a for a, r in rows.items() if isinstance(r, dict) and r.get('rules') and r['rules'] != kw and a not in failed)
        if off: bad.append(f"4 key-wide rules {kw} but rows on other code hashes and the build says complete: {' '.join(off[:20])}")
    both = set(d.get('areas_rebuilt') or []) & set(d.get('areas_reused') or [])
    if both: bad.append(f"5 rebuilt and reused at once: {' '.join(sorted(both))}")
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('cmd', choices=['hashes', 'table', 'diff', 'replay', 'holes', 'migrate', 'plan', 'stamp-rows', 'proof-check', 'sanity'])
    ap.add_argument('--list', default='', help='plan: the areas today\'s plan builds'); ap.add_argument('--index', default=None)
    ap.add_argument('--mode', default=None, help='plan: shadow | add | reuse (default: the KPC_AREA_HASH variable, else shadow)')
    ap.add_argument('--full', default='', help='plan: yes = full rebuild asked (no reuse)'); ap.add_argument('--out', default=None)
    ap.add_argument('--plan', default=None, help='stamp-rows: the plan JSON'); ap.add_argument('--saved', default='')
    ap.add_argument('--part', action='append', default=[], help='stamp-rows (US): a build part with area-plan.json, built-sha.txt, states.txt')
    ap.add_argument('--built-sha', default=''); ap.add_argument('--from', dest='frm', default=''); ap.add_argument('--to', default='')
    ap.add_argument('args', nargs='*')
    ap.add_argument('--repo', default=str(REPO)); ap.add_argument('--data', default=None); ap.add_argument('--rev', default=None)
    ap.add_argument('--level', type=int, default=3, choices=[1, 2, 3]); ap.add_argument('--parts', action='store_true')
    ap.add_argument('--csv', default=None); ap.add_argument('--since', default=None); ap.add_argument('--kinds', default='')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--reader', default='shared', choices=['shared', 'verdict', 'off'],
                    help='shared = kpc_master / kpc_net_guard tokens in every area (step 1); verdict = per-area host verdicts (step 3); off = today (not in the hash)')
    ap.add_argument('--window', type=float, default=6.0, help='migrate: hours before a build save in which an input change makes it unproven (0 = trust the save parent)')
    ap.add_argument('--var', action='append', default=[], help='a repo variable the build is given, NAME=VALUE (hashed as part vars)')
    a = ap.parse_args(argv)
    env = dict(x.split('=', 1) for x in a.var if '=' in x)
    if a.cmd == 'hashes':
        t = Tree(a.repo, a.rev)
        for k, kk in KINDS.items(): print(f'{kk:10} {region_hash(t, kk)}')
        return 0
    if a.cmd == 'table':
        if len(a.args) != 1 or a.args[0] not in KINDS: ap.error('table KIND (us|ca|world|fers)'); return 2
        hs, parts = compute(a.repo, a.rev, a.args[0], a.level, a.data, None, a.reader, env)
        if a.json: print(json.dumps({'kind': a.args[0], 'level': a.level, 'areas': hs, **({'parts': parts} if a.parts else {})}, indent=1, sort_keys=True)); return 0
        print(f'# kind {a.args[0]}  level {a.level}  {len(hs)} areas  (region hash {region_hash(Tree(a.repo, a.rev), KINDS[a.args[0]])})')
        for ar in sorted(hs):
            print(f'{ar:22} {hs[ar]}')
            if a.parts:
                for n, v in sorted(parts[ar].items()): print(f'    {n:70} {v[:12]}')
        return 0
    if a.cmd == 'diff':
        if len(a.args) != 3 or a.args[0] not in KINDS: ap.error('diff KIND REV_A REV_B'); return 2
        kind, ra, rb = a.args
        ha, pa = compute(a.repo, ra, kind, a.level, a.data, rb, a.reader, env); hb, pb = compute(a.repo, rb, kind, a.level, a.data, ra, a.reader, env)
        d = diff_parts(pa, pb)
        print(f'# kind {kind} level {a.level}: {len(d)} of {len(hb)} areas move ({ra} -> {rb}); region '
              f'{region_hash(Tree(a.repo, ra), KINDS[kind])} -> {region_hash(Tree(a.repo, rb), KINDS[kind])}')
        print('area | old hash | new hash | reason | action')
        for ar in sorted(set(ha) | set(hb)):
            if ar in d: print(f"{ar} | {ha.get(ar, '-')} | {hb.get(ar, '-')} | {'; '.join(d[ar])[:300]} | rebuild")
            else: print(f"{ar} | {ha.get(ar)} | {hb.get(ar)} | no input changed | reuse")
        return 0
    if a.cmd == 'replay':
        replay(a.repo, a.data, a.since, a.csv, set(a.kinds.split()) if a.kinds else None)
        return 0
    if a.cmd == 'migrate':
        if len(a.args) != 1 or a.args[0] not in ('us', 'ca', 'world'): ap.error('migrate us|ca|world'); return 2
        migrate(a.repo, a.data, a.args[0], a.reader, a.window, csv_path=a.csv)
        return 0
    if a.cmd == 'plan':
        if len(a.args) != 1 or a.args[0] not in ROWS_KEY: ap.error('plan us|ca|world'); return 2
        mode = (a.mode or os.environ.get('KPC_AREA_HASH') or 'shadow').strip().lower()
        if mode not in MODES_RUN: print(f'::warning title=Area hashes::unknown mode {mode!r}: shadow', file=sys.stderr); mode = 'shadow'
        try:
            rec, t = run_plan(a.repo, a.args[0], a.list.split(), a.index or str(pathlib.Path(a.repo) / KEY_PATH[a.args[0]].format(a='index')), mode,
                              a.full.strip().lower() in ('yes', 'true', '1', 'full'), a.data, env, a.out)
        except Exception as e:  # noqa: BLE001  shadow / add: the plan's own list stands; reuse is never applied on an error
            print(f'::warning title=Area hashes::not computed ({type(e).__name__}: {str(e)[:160]}): the plan\'s own list is built (nothing reused)', file=sys.stderr)
            if a.out: pathlib.Path(a.out).write_text(json.dumps({'kind': a.args[0], 'mode': mode, 'list': a.list.split(), 'added': [], 'reused': [], 'error': str(e)[:200]}), encoding='utf-8')
            print(' '.join(a.list.split())); return 0
        print(f"::notice title=Area hashes::{a.args[0]} mode {mode}: {len(rec['added'])} added, {len(rec['reused'])} reused (code hash {rec['code_hash']})", file=sys.stderr)
        print(' '.join(rec['list']))
        return 0
    if a.cmd == 'stamp-rows':
        if len(a.args) != 1 or a.args[0] not in ROWS_KEY: ap.error('stamp-rows us|ca|world'); return 2
        if a.part: done, same = stamp_rows_parts(a.repo, a.args[0], a.index, a.saved.split(), a.part)
        else:
            try: plan = json.loads(pathlib.Path(a.plan).read_text(encoding='utf-8')) if a.plan else {}
            except Exception: plan = {}  # noqa: BLE001
            done, same = stamp_rows(a.repo, a.args[0], a.index, a.saved.split(), plan, a.built_sha)
        print(f"::notice title=Area hashes::{len(done)} area row(s) carry their area hash" + ('' if same else ' (none: the build did not check out the commit the plan hashed, so no area hash is claimed)'), flush=True)
        return 0
    if a.cmd == 'proof-check':
        if len(a.args) != 1 or a.args[0] not in KINDS: ap.error('proof-check KIND --from H --to H'); return 2
        v, why = proof_valid(a.repo, a.args[0], a.frm, a.to)
        print(('VALID ' if v else 'NOT VALID ') + why); return 0 if v else 1
    if a.cmd == 'sanity':
        if len(a.args) != 1 or a.args[0] not in ROWS_KEY: ap.error('sanity us|ca|world'); return 2
        bad = sanity(a.repo, a.args[0], a.index)
        for b in bad: print(f'::error title=Whole-key sanity check ({a.args[0]})::{b}', flush=True)
        print(f"whole-key sanity check {a.args[0]}: {'PASS' if not bad else 'FAIL'} ({len(bad)} problem(s))")
        return 1 if bad else 0
    if a.cmd == 'holes':
        holes(a.repo, a.data, a.since, a.csv)
        return 0
    return 2


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Refuse a key rule-file edit that declares no scope (keys-first hand-off rev 3.1, S2, F7; Opus 19 Nov 2026).

A change that moves the US key's rules hash (any file in kpc_key_freeze.RULE_FILES['us-key']) must add one NEW entry to
.github/us-key-rule-scope.json, and the run's own reader (kpc_key_freeze.pending_scope) must find the change declared: the
chain of entries starts at the one whose 'from' is the last build (data/us-key/index.json 'rules'). Without it the next run
reads the change as undeclared and rebuilds all 50 states.

    python3 .github/scripts/kpc_key_scope_check.py --base <main checkout> --head <this checkout> [--kind us-key]

Exit 0 = no rule file changed, or the change declares its scope. Exit 1 = refused (an ::error line says why).
Reads files only. Not a rule file itself, so it moves no hash.
"""
import argparse, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_key_freeze as F  # noqa: E402

INDEX = {'us-key': 'data/us-key/index.json'}
SCOPES = ('none', 'all')


def _load(p, default):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return default


def check(base, head, kind='us-key'):
    """[] when fine; else the reasons it is refused (plain sentences)."""
    base, head = pathlib.Path(base), pathlib.Path(head)
    hb, hh = F.rules_hash(kind, base), F.rules_hash(kind, head)
    if hb == hh:
        return []
    scope_rel = F.SCOPE_FILES[kind]
    old_ids = {c.get('id') for c in (_load(base / scope_rel, {}).get('changes') or []) if isinstance(c, dict)}
    new = [c for c in (_load(head / scope_rel, {}).get('changes') or []) if isinstance(c, dict) and c.get('id') not in old_ids]
    built = str((_load(head / INDEX[kind], {}) or {}).get('rules') or '')
    why = []
    if not new:
        why.append(f'the {kind} rule files changed (rules hash {hb} -> {hh}) but {scope_rel} has no new entry: '
                   f"add one (id, when, why, from: '{built}', scope: 'none' when it is merged OFF)")
    for c in new:
        cid = c.get('id') or '(no id)'
        if not c.get('id') or not c.get('why') or not c.get('when'):
            why.append(f'the new scope entry {cid} needs an id, a when and a why')
        sc = c.get('scope')
        if not (sc in SCOPES or isinstance(sc, dict)):
            why.append(f"the new scope entry {cid} has scope {sc!r}: use 'none', 'all' or {{'states': [...], 'parks': [...]}}")
    # Fable's review of #294 (19 Nov, 2): ask the run's own reader. pending_scope starts at the entry whose 'from' is the last
    # build and takes every entry after it (a chain), so a stacked draft whose entry is from the hash the draft before it moved to
    # is declared. Undeclared = None = the run would rebuild every state.
    if new and built and F.pending_scope(kind, built, head)[0] is None:
        why.append(f'the run would read this change as UNDECLARED (no scope entry chains from the last build {built}) and rebuild '
                   f"every state: the first new entry since that build needs from: '{built}'")
    return why


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--base', required=True)
    ap.add_argument('--head', default='.')
    ap.add_argument('--kind', default='us-key', choices=sorted(INDEX))
    a = ap.parse_args(argv)
    why = check(a.base, a.head, a.kind)
    for w in why:
        print(f'::error title=Key scope check::{w}', flush=True)
    if not why:
        print(f'Key scope check ({a.kind}): fine (no rule file changed, or the change declares its scope).')
    return 1 if why else 0


if __name__ == '__main__':
    sys.exit(main())

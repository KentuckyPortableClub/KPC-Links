#!/usr/bin/env python3
"""KEY BUILD ORDER after a rules change (Nov 4 2026; per Brandon via Super Head Bot (relayed), 5:48 AM CST Nov 4, the key-order
part of his message: "Full world rebuild yes after us and Canada..stand by for more"). On the first runs after a rules change the keys build in this order: US, then Canada, then
the world. A key whose next build is a NEW-RULES build (its newest stamp is not a full build on the current rules, links-04's
RULES_CHANGED) waits until every key it follows (WAIT_FOR) has finished its own new-rules build (KPC-Links data/<key>/index.json
'rules' == kpc_key_freeze.rules_hash). No cron: a waiting key is picked up by workflow_run when the key before it finishes
(kpc-ca-key.yml on 'KPC US answer key'; kpc-world-key.yml on 'KPC US answer key' + 'KPC Canada answer key').

  check ca-key|world-key   writes SKIP=1 (+ ORDER_WAIT=1) to $GITHUB_ENV when the key must wait, and one notice. Never fails.
      * its own build is already on the current rules: nothing to wait for (a normal nightly / monthly run goes on as before);
        a workflow_run start (GITHUB_EVENT_NAME=workflow_run) then has nothing to catch up and skips cleanly
      * FORCE=yes (by hand only) skips the order check
      * an error = the run waits (SKIP=1): it is picked up again when the key before it finishes
      * KPC-Links without links-04 (no rules hash): no order at all, the run goes on as before (never a key that waits forever)
      * Nov 4 PM fix bundle (item 2): a workflow_run start whose newest build (read from the NEWEST main when KPC_INDEX_REF is set)
        has the current rules_of_run and the same inputs is a DUPLICATE and skips (DUPLICATE=1), even when that build failed a part
      * next round C1 (Nov 5): a workflow_dispatch with KPC_CHAINED=us-key / ca-key (the input 'chained', set only by the key before
        it after a bot-started run) is checked as a workflow_run start
To change or extend the order, edit WAIT_FOR (one line per key)."""
import json, os, pathlib, sys

WAIT_FOR = {
    'ca-key': ('us-key',),               # Canada after the US
    'world-key': ('us-key', 'ca-key'),   # the world after the US and Canada (Brandon, relayed via Super Head Bot, 5:48 AM CST Nov 4)
}
NAMES = {'us-key': 'US', 'ca-key': 'Canada', 'world-key': 'world'}


def _env(**kv):
    env = os.environ.get('GITHUB_ENV')
    if env:
        with open(env, 'a') as f: f.write(''.join(f'{k}={v}\n' for k, v in kv.items()))


def notice(m): print(f'::notice title=Key build order::{m}', flush=True)


def on_current(kind, root='.'):
    """(True|False, why): is KPC-Links' newest build of this key a full build on the current rules?"""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import kpc_key_freeze as KF
    st = _index(kind, root)
    cur = KF.rules_hash(kind, root) if root != '.' else KF.rules_hash(kind)
    have = str(st.get('rules') or '')
    return have == cur, f"build {st.get('build') or 'none'} rules {have or 'none'} vs current {cur}"


def upstream_done(kind, root='.'):
    """(True|False, why): has the key before this one FINISHED a build on the current rules? Its full stamp ('rules') or the rules
    of its newest run ('rules_of_run', also for a build with a failed area): one short area must not hold the keys after it forever."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import kpc_key_freeze as KF
    st = _index(kind, root)
    cur = KF.rules_hash(kind, root) if root != '.' else KF.rules_hash(kind)
    have = {str(st.get('rules') or ''), str(st.get('rules_of_run') or '')}
    return cur in have, f"build {st.get('build') or 'none'} rules {st.get('rules') or 'none'} / of its run {st.get('rules_of_run') or 'none'} vs current {cur}"


def _index(kind, root='.'):
    """Nov 4 PM fix bundle (items 1-2): KPC_INDEX_REF=origin/main (set by the key workflows) = the NEWEST main's stamp: the queued
    second Canada start of Nov 4 (41891453412) read the stamp of its trigger-time checkout, from before the first Canada build."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import kpc_key_freeze as KF
    if hasattr(KF, 'load_index'): return KF.load_index(kind, cwd=None if root == '.' else str(root))
    try: return json.load(open(pathlib.Path(root) / f'data/{kind}/index.json', encoding='utf-8')) or {}
    except Exception: return {}  # noqa: BLE001


def same_build_exists(kind, root='.'):
    """Nov 4 PM fix bundle (item 2, Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4): '' or why a chained start is a
    duplicate: the newest build of this key was made on the CURRENT rules (rules_of_run, set by kpc_key_freeze.py stamp even for a
    partial or failed build) from the SAME inputs (the builds of the keys before it). Nov 4: the world build W-41895532587 (AU timed
    out, so 'rules none') was started again (41901828387) by the second Canada completion with exactly the same rules and inputs."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import kpc_key_freeze as KF
    if not hasattr(KF, 'inputs_of'): return ''
    st = _index(kind, root)
    cur = KF.rules_hash(kind, root) if root != '.' else KF.rules_hash(kind)
    if str(st.get('rules_of_run') or '') != cur: return ''
    want = KF.inputs_of(kind, cwd=None if root == '.' else str(root))
    have = st.get('inputs') if isinstance(st.get('inputs'), dict) else {}
    if any(not v for v in want.values()) or have != want: return ''
    bad = st.get('failed') or []
    return (f"build {st.get('build')} was already made on the current rules {cur} from the same inputs ("
            + ', '.join(f'{NAMES[k]} {v}' for k, v in want.items()) + ')' + (f"; its failed part(s) {' '.join(bad[:10])} need a fix or a by-hand run" if bad else ''))


def check(kind, env=os.environ, root='.'):
    """-> 'go' | 'wait' | 'skip' (also written to $GITHUB_ENV as SKIP=1 for wait / skip)"""
    ev = env.get('GITHUB_EVENT_NAME') or ''
    # Next round C1 (Nov 5; Brandon's yes relayed via Super, 4:32 AM CST Nov 5): a run started with the GITHUB_TOKEN fires no
    # workflow_run, so a bot-started US (or Canada) key DISPATCHES the keys after it with chained=<that key>. Such a start is a
    # chained start exactly like a workflow_run one (catch-up only; a duplicate or an up-to-date key skips cleanly). A by-hand
    # dispatch (chained blank) still builds.
    chained = (env.get('KPC_CHAINED') or '').strip().lower()
    if ev == 'workflow_dispatch' and chained in NAMES and chained in WAIT_FOR.get(kind, ()):
        notice(f'{NAMES[kind]} key: started by the {NAMES[chained]} key (a bot-started run fires no workflow_run): checked as a chained start'); ev = 'workflow_run'
    if (env.get('FORCE') or '').lower() == 'yes':
        notice(f'{NAMES[kind]} key: FORCE=yes by hand: the build order is not checked'); return 'go'
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import kpc_key_freeze as KF
        if not hasattr(KF, 'rules_hash'):
            notice(f'{NAMES[kind]} key: kpc_key_freeze.py has no rules hash (links-04 not merged): no build order, the run goes on as before'); return 'go'
        mine, why = on_current(kind, root)
        dup = same_build_exists(kind, root) if ev == 'workflow_run' else ''
        if dup:
            _env(SKIP=1, DUPLICATE=1); notice(f'{NAMES[kind]} key: DUPLICATE chained start skipped: {dup}. A by-hand run (workflow_dispatch) still builds'); return 'skip'
        if mine:
            if ev == 'workflow_run':
                _env(SKIP=1); notice(f'{NAMES[kind]} key: already on the current rules ({why}): nothing to catch up, this chained start skips'); return 'skip'
            return 'go'
        todo = [(k, w) for k in WAIT_FOR.get(kind, ()) for ok, w in [upstream_done(k, root)] if not ok]
        if todo:
            _env(SKIP=1, ORDER_WAIT=1)
            notice(f"{NAMES[kind]} key WAITS (new-rules build; order US -> Canada -> world, per Brandon via Super Head Bot (relayed), 5:48 AM CST Nov 4): "
                   + '; '.join(f'{NAMES[k]} has not finished its new-rules build ({w})' for k, w in todo)
                   + f'. Nothing is built now; this key starts by itself when {NAMES[todo[-1][0]]} finishes (dispatched by that key, no cron)')
            return 'wait'
        notice(f'{NAMES[kind]} key: new-rules build; ' + (' and '.join(NAMES[k] for k in WAIT_FOR.get(kind, ())) or 'no key') + ' already finished theirs: it builds now')
        return 'go'
    except Exception as e:  # noqa: BLE001
        _env(SKIP=1, ORDER_WAIT=1); notice(f'{NAMES.get(kind, kind)} key: the order check could not run ({str(e)[:150]}): it waits (picked up when the key before it finishes)'); return 'wait'


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['check'] and len(a) > 1 and a[1] in NAMES: check(a[1])
    else: print(__doc__)
    sys.exit(0)

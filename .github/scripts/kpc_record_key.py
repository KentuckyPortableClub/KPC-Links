#!/usr/bin/env python3
"""kpc_record_key.py: ONE record lookup shared by the key, the outline store and the 2-fer bot (KPC owner, 2026-11-16; handoff
'proof of work', item 4). Started from kpc_fers_store.store_ids (KPC-Links #216).

A key join ('m' row) names a record the way its key builder found it; the outline store files the same record under a record KEY.
  US      data/us-key/US-XX.json   m row [record id, name, score, how]   -> store key = the record id as it is (57154)
  Canada  data/ca-key/CA.json      m row [record id, name, ...]          -> store key = the record id as it is ('abc1')
  world   data/world-key/XX.json   m row [record id, name, layer, ...]   -> store key = '<area>:<layer>:<record id>'
                                                                            (W-BE:EEA Natura 2000:352; a layer name may hold ':')
store_key() is the only place that knows this; kpc_fers_store.store_ids (the bot's store reads) calls it, and a key-side reader
that needs a store record (a store-mode key, a check) must call it too. split_key() reads a world store key back. A format change
on either side fails tests/test_record_key_contract_nov16.py (tiny made-up samples in the real store format), not a run.
Not a rule file by itself: it decides no join; it is imported by kpc_fers_store.py (2-fer rule file), so a change here is a change
of the 2-fer reads and must be declared like one. Standard library only."""
import re

AREA_RX = re.compile(r'(US|CA|W)-[A-Z]{2}')


def kind_of_area(area):
    a = str(area or '')
    return 'world' if a.startswith('W-') else 'ca' if a.startswith('CA-') else 'us' if a.startswith('US-') else ''


def store_key(area, join):
    """One key join (an 'm' row, or a bare record id for US / Canada) of a park filed under `area` -> its store record key."""
    k = kind_of_area(area)
    if k == 'world':
        if not isinstance(join, (list, tuple)) or len(join) < 3: raise ValueError(f'a world join needs [id, name, layer]: {join!r}')
        return f'{area}:{join[2]}:{join[0]}'
    if k in ('us', 'ca'):
        return join[0] if isinstance(join, (list, tuple)) else join
    raise ValueError(f'unknown area {area!r}')


def park_keys(p):
    """A park as kpc_fers.official_parks() holds it ({'st', 'ids', ['m']}) -> the store record keys of its records, in order.
    A world park (it carries 'm') is looked up by '<area>:<layer>:<id>'; a US / Canadian park by its ids as they are."""
    if 'm' in p: return [store_key(p['st'], x) for x in p['m']]
    return list(p['ids'])


def split_key(key):
    """A store record key -> (area, layer, record id); US / Canadian keys have no area or layer in them: ('', '', key)."""
    s = str(key)
    m = re.match(r'(W-[A-Z]{2}):(.+):([^:]+)$', s)
    return (m.group(1), m.group(2), m.group(3)) if m else ('', '', s)

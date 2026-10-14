"""Pre-approval for the KPC Google Form syncs (Park Notes, Community, Campground notes).
A row is published when:
  - its Approved cell says YES (or Y / APPROVED / X), or
  - the Approved cell is empty AND the call sign is pre-approved:
      * every club member in MEMBERS=[...] in kpc-tools.js (the one club roster), plus
      * the extra call signs in kpc-preapproved.json ("extra": [...]) for trusted non-members.
A NO (or N / REJECT / HIDE) in the Approved cell always keeps a row off the site, even for pre-approved calls.
Note: call signs are typed by the person filling in the form, so pre-approval trusts that they typed their own."""
import json, re

def base(call):
    """KZ4CP/P, W4/KZ4CP, KZ4CP/M all mean KZ4CP: keep the longest part."""
    parts = [p for p in re.sub(r'[^A-Z0-9/]', '', str(call).upper()).split('/') if p]
    return max(parts, key=len) if parts else ''

def load():
    calls = set()
    try:
        t = open('kpc-tools.js', encoding='utf-8').read()
        m = re.search(r'MEMBERS\s*=\s*\[([^\]]*)\]', t)
        if m:
            calls |= {base(x.strip().strip('\'"')) for x in m.group(1).split(',') if x.strip()}
    except Exception:
        pass
    try:
        calls |= {base(c) for c in json.load(open('kpc-preapproved.json', encoding='utf-8')).get('extra', [])}
    except Exception:
        pass
    calls.discard('')
    return calls

def ok(approved_cell, call, pre):
    a = str(approved_cell or '').strip().upper()
    if a in ('NO', 'N', 'REJECT', 'REJECTED', 'HIDE'):
        return False
    if a in ('YES', 'Y', 'APPROVED', 'X'):
        return True
    return base(call) in pre

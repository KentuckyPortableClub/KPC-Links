#!/usr/bin/env python3
"""Build the answers / solved ledger under data/research-inbox/answers/ (Nov 11 2026). Offline, no network, writes only the answers folder.

  stage  <handoff-inputs-dir> <answers-dir>   copy the Nov 5 + Nov 11 hand-backs and the prepared lists into the answers folder, WDPA / Protected
                                              Planet ids and addresses stripped (the row and every other cell stay; a flag says what was removed)
  ledger <answers-dir>                        build solved-ledger.csv (one row per park) and search-list.csv (the parks still to be handed out)
                                              from the filed files, using kpc_research_inbox.classify_solved (the one rule for "solved")

It never writes a key, an override, a pin, a fers file or a workflow, and nothing here feeds a rules hash."""
import csv, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / '.github/scripts'))
import kpc_research_inbox as RI  # noqa: E402

FLAG = 'WDPA lead removed'
# column roles per file kind: where the flag goes, and the cells that hold an id / its type / an address (blanked whole when they were only the WDPA lead)
KINDS = {
    'answers5': dict(flag='flags', ids=['official_id'], types=['id_type'], urls=['official_source_url']),
    'lists': dict(flag='nov5_flags', ids=['nov5_official_id'], types=['nov5_id_type'], urls=['nov5_source_url']),
    'solved': dict(flag='nov5_flags', ids=['nov5_official_id'], types=['nov5_id_type'], urls=['nov5_source_url']),
    'plain': dict(flag=None, ids=[], types=[], urls=[]),
}
# Nov 11 review: no filed sentence quotes or attributes words to the owner, and no tool is named as an author. Targeted rewrites first, then the name becomes "the owner".
NEUTRAL = [   # (regex, replacement), in order
    (r"\(Brandon: [^)]*\)", "(club rule: where no outline is published, record the official point)"),
    (r"Brandon's ruling tonight:[^.]*\.", "Club rule tonight: where an agency publishes no outline, record the official point."),
    (r"needs Brandon approval", "needs owner approval"), (r"needs Brandon (?:words|sign)\b", "needs an owner decision"),
    (r"Brandon's far-pin ruling", "The far-pin rule (owner decision pending)"),
    (r"Brandon's '[^']*' licence decision", "the owner licence decision on cite-the-source"),
    (r"Brandon's cite-the-source decision", "the owner cite-the-source decision"),
    (r"Brandon standing rule", "club standing rule"), (r"Brandon's yes on", "an owner yes on"),
    (r"Brandon's decision|Brandon decision|decision for Brandon", "owner decision"),
    (r"unless Brandon has already said otherwise", "unless the owner has already decided otherwise"),
    (r"Brandon still has to rule on", "the owner decision is still pending on"),
    (r"Brandon's", "the owner's"), (r"Brandon", "the owner"), (r"KZ4CP", "KPC"),
    (r"(?<=by )\w+ \(Fable\)", "an outside agent (Fable)"),
]


def neutral(t):
    for a, b in NEUTRAL: t = re.sub(a, b, t)
    return t


OWNER_QUOTE = re.compile(r"added per Brandon's answer to question 4 \([^)]*\)")


def read(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f); return list(r.fieldnames), list(r)


def write(path, cols, rows):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n'); w.writeheader(); w.writerows(rows)


def clean_rows(rows, kind):
    """strip WDPA from every cell; returns the number of rows that changed"""
    k = KINDS[kind]; changed = 0
    for r in rows:
        hit = False
        for c in k['ids'] + k['urls']:
            if RI.has_wdpa_data(r.get(c)):
                new = RI.scrub_wdpa(r[c]); r[c] = '' if new.strip() == RI.WDPA_MARK else new; hit = True
        for c in k['types']:
            if re.search(r'wdpa', r.get(c) or '', re.I): r[c] = ''; hit = True
        for c in list(r):
            if RI.has_wdpa_data(r[c]): r[c] = RI.scrub_wdpa(r[c]); hit = True
            if r[c] and OWNER_QUOTE.search(r[c]): r[c] = OWNER_QUOTE.sub("added on the owner's yes to question 4 (relayed Nov 5)", r[c])
            if r[c] and re.search(r'Brandon|KZ4CP|by \w+ \(Fable\)', r[c]): r[c] = neutral(r[c])
        if hit and k['flag']:
            r[k['flag']] = '; '.join(x for x in [r.get(k['flag'], ''), FLAG] if x)
        changed += hit
    return changed


def stage_csv(src, dst, kind, keep=None):
    cols, rows = read(src); n = clean_rows(rows, kind)
    if keep: cols = [c for c in keep if c in cols]
    write(dst, cols, [{c: r[c] for c in cols} for r in rows]); return len(rows), n


def stage_text(src, dst):
    t = pathlib.Path(src).read_text(encoding='utf-8')
    if RI.has_wdpa_data(t): t = RI.scrub_wdpa(t)
    t = neutral(t)
    pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True); pathlib.Path(dst).write_text(t, encoding='utf-8')


def append_sources(base_rows, add_rows):
    """append the additions that are not already in the ledger (the same 12 columns); a row already there is never added twice"""
    seen = {tuple(sorted(r.items())) for r in base_rows}; out = list(base_rows); added = 0
    for r in add_rows:
        t = tuple(sorted(r.items()))
        if t not in seen: seen.add(t); out.append(r); added += 1
    return out, added


def stage(inp, out):
    inp, out = pathlib.Path(inp), pathlib.Path(out); log = []
    log.append(('nov11/answers-nov11.csv', *stage_csv(inp / 'nov11-answers/mystery-parks-answers-nov11-final.csv', out / 'nov11/answers-nov11.csv', 'plain')))
    stage_text(inp / 'nov11-answers/MYSTERY_PARKS_NOV11_NOTES.md', out / 'nov11/MYSTERY_PARKS_NOV11_NOTES.md')
    log.append(('nov5/answers-nov5.csv', *stage_csv(inp / 'nov5-returned/answers-clean.csv', out / 'nov5/answers-nov5.csv', 'answers5')))
    # the held-for-Brandon file repeats answers-clean column for column (checked) and adds only intake_flags + decided_by: keep those
    log.append(('nov5/held-for-brandon-nov5.csv', *stage_csv(inp / 'nov5-returned/brandon-later.csv', out / 'nov5/held-for-brandon-nov5.csv', 'answers5',
                                                          keep=['ref', 'name', 'answer', 'proposed_action', 'flags', 'intake_flags', 'decided_by'])))
    log.append(('nov5/JP_A10_crosswalk.csv', *stage_csv(inp / 'nov5-returned/JP_A10_crosswalk.csv', out / 'nov5/JP_A10_crosswalk.csv', 'plain')))
    for n in ('HANDOFF.md', 'MYSTERY_PARKS_PASS9_FABLE.md'): stage_text(inp / 'nov5-returned' / n, out / 'nov5' / n)
    log.append(('lists/mystery-parks-open.csv', *stage_csv(inp / 'ledgers/mystery-parks-open.csv', out / 'lists/mystery-parks-open.csv', 'lists')))
    log.append(('lists/found-waiting-world-key.csv', *stage_csv(inp / 'ledgers/found-waiting-world-key.csv', out / 'lists/found-waiting-world-key.csv', 'lists')))
    log.append(('lists/solved-since.csv', *stage_csv(inp / 'ledgers/solved-since.csv', out / 'lists/solved-since.csv', 'solved')))
    stage_text(inp / 'ledgers/MYSTERY_PARKS_FABLE.md', out / 'lists/MYSTERY_PARKS_FABLE.md')
    # sources: the Nov 5 ledger, the Thailand Protected Planet page dropped (a WDPA page is not a source), then the Nov 11 additions appended once
    cols, base = read(inp / 'nov5-returned/research-sources-all.csv')
    keep = [r for r in base if not RI.has_wdpa_data(r['url']) and not re.search(r'protected\s*planet', r['url'] + r['layer_name'], re.I)]
    dropped = len(base) - len(keep)
    acols, add = read(inp / 'nov11-answers/research-sources-nov11-additions.csv')
    assert acols == cols, 'the additions must have the same 12 columns'
    merged, added = append_sources(keep, add); clean_rows(merged, 'plain')
    write(out / 'sources/research-sources-all.csv', cols, merged)
    log.append(('sources/research-sources-all.csv', len(merged), dropped))
    log.append(('sources/research-sources-nov11-additions.csv', *stage_csv(inp / 'nov11-answers/research-sources-nov11-additions.csv', out / 'sources/research-sources-nov11-additions.csv', 'plain')))
    # check against the prepared Nov 11 ledger: same rows once the Thailand WDPA row is left out
    _, prepared = read(inp / 'ledgers/research-sources-all.csv')
    prepared = [r for r in prepared if not re.search(r'protected\s*planet', r['url'] + r['layer_name'], re.I)]; clean_rows(prepared, 'plain')
    same = sorted(tuple(sorted(r.items())) for r in prepared) == sorted(tuple(sorted(r.items())) for r in merged)
    print(f'sources: base {len(base)} - {dropped} dropped + {added} appended = {len(merged)}; equals the prepared Nov 11 ledger (Thailand WDPA row left out): {same}')
    for f, n, c in log: print(f'{f}: {n} rows, {c} changed')


# ---- strength of a Nov 11 match, from the Nov 11 notes section 5 (how strong each match is)
STRENGTH = {}
for _tier, _refs in {
    'agency-layer-pin-tested': 'US-10184 US-10195 US-7374 FR-10548 FR-10432 FR-11106 FR-11650 FR-12366 FR-13422 FR-14049 FR-14482 FR-14979 RO-0880',
    'nrhp-listing-boundary-pin-inside': 'US-13474 US-11820 US-12735 US-10274',
    'nrhp-listing-boundary-within-0.45km': 'US-8142 US-3493 US-10521 US-7975',
    'official-record-pin-not-tested': 'CA-2506 MX-0016 MX-0141 MX-0147 MX-0180 MX-0191 MX-0221 CL-0012 CL-0037 CL-0049 PT-0382 NZ-0051',
    'boundary-in-law-no-map-file': 'DO-0027 DO-0085 DO-0095 DO-0132 BZ-0033 BZ-0034 GT-0005 LK-0026 UY-0049',
    'nov5-match-carried-key-still-pin': 'US-4376 US-0754 US-11900 US-11297 US-8422 US-6261 US-6259',
}.items():
    for _r in _refs.split(): STRENGTH[_r] = _tier

LEDGER_COLS = ['ref', 'name', 'country', 'state_province', 'answer', 'answer_from', 'solved', 'solved_basis', 'owner_decision', 'owner_decision_why', 'join_ready', 'join_note', 'source_list', 'key_status', 'key_location',
               'key_joined_record', 'official_id', 'official_id_type', 'official_source_url', 'match_strength', 'confirm', 'candidate_id', 'candidate_id_type',
               'official_point_lat', 'official_point_lon', 'official_point_kind', 'official_point_id', 'official_point_source_url',
               'official_point_km_from_pota_pin', 'pin_vs_polygon', 'pin_distance_km', 'flags']
SEARCH_COLS = ['ref', 'name', 'country', 'state_province', 'pota_lat', 'pota_lon', 'answer', 'solved_basis', 'source_list', 'reason_code', 'what_we_need',
               'candidate_id', 'candidate_id_type', 'official_point_kind', 'flags']


def id_type_of(oid):
    return oid.split(':', 1)[0] if ':' in oid else ''


def build_ledger(ans):
    ans = pathlib.Path(ans)
    _, a5 = read(ans / 'nov5/answers-nov5.csv'); _, a11 = read(ans / 'nov11/answers-nov11.csv')
    A5 = {r['ref']: r for r in a5}; A11 = {r['ref']: r for r in a11}
    LISTS = {}
    for lst, f in (('open', 'mystery-parks-open.csv'), ('solved-since', 'solved-since.csv'), ('found-waiting-world-key', 'found-waiting-world-key.csv')):
        _, rows = read(ans / 'lists' / f)
        for r in rows:
            assert r['ref'] not in LISTS, r['ref']; LISTS[r['ref']] = (lst, r)
    assert set(LISTS) == set(A5), 'the three prepared lists must cover the 832 Nov 5 rows exactly'
    assert set(A11) <= set(A5)
    out, search = [], []
    for ref in sorted(A5, key=lambda x: (x.split('-')[0], int(x.split('-')[1]) if x.split('-')[1].isdigit() else 0, x)):
        n5 = A5[ref]; n11 = A11.get(ref); lst, L = LISTS[ref]
        if n11: answer, frm = n11['answer'], 'nov11'
        else: answer, frm = n5['answer'], 'nov5'
        assert answer in RI.ANSWER_WORDS, (ref, answer)
        oid5, ty5 = n5['official_id'], n5['id_type']
        oid11 = (n11 or {}).get('other_official_id', '') or (n11 or {}).get('padus_id', '')
        oid, oty = (oid11, id_type_of(oid11)) if oid11 else (oid5, ty5)
        url = (n11 or {}).get('official_source_url', '') or n5['official_source_url']
        wdpa_removed = FLAG in (n5.get('flags') or '') or FLAG in (L.get('nov5_flags') or '')
        key_status = L.get('current_key_status', ''); key_loc = L.get('key_location', '')
        is_match = answer == 'match'
        strength = (STRENGTH.get(ref) or 'nov5-proposed') if is_match else ''
        confirm = n5['proposed_action'] if (is_match and frm == 'nov5' and n5['proposed_action'] in ('needs_brandon', 'confirm_candidate_name')) else ''
        K = RI.classify_row(answer, oid if is_match else '', url if is_match else '', key_loc, key_status, wdpa_removed, confirm, strength, ref)
        solved, basis = K['skip_search'], K['solved_basis']
        assert not (is_match and frm == 'nov11') or ref in STRENGTH, ('Nov 11 match without a strength tier', ref)
        row = {
            'ref': ref, 'name': n5['name'], 'country': n5['country'], 'state_province': n5['state_province'], 'answer': answer, 'answer_from': frm,
            'solved': 'yes' if solved else 'no', 'solved_basis': basis, 'owner_decision': K['owner_decision'],
            'owner_decision_why': K['owner_decision_why'], 'join_ready': K['join_ready'], 'join_note': K['join_note'], 'source_list': lst, 'key_status': key_status, 'key_location': key_loc,
            'key_joined_record': L.get('joined_record', ''),
            'official_id': oid if is_match else '', 'official_id_type': oty if is_match else '', 'official_source_url': url if is_match else '',
            'match_strength': strength, 'confirm': confirm,
            'candidate_id': '' if is_match else oid, 'candidate_id_type': '' if is_match else oty,
            'pin_vs_polygon': n5['pin_vs_polygon'], 'pin_distance_km': n5['pin_distance_km'], 'flags': n5['flags'],
        }
        for c in ('official_point_lat', 'official_point_lon', 'official_point_kind', 'official_point_id', 'official_point_source_url', 'official_point_km_from_pota_pin'):
            row[c] = (n11 or {}).get(c, '')
        out.append(row)
        if not solved:
            search.append(dict(row, pota_lat=L.get('pota_lat', ''), pota_lon=L.get('pota_lon', ''), reason_code=L.get('reason_code', ''), what_we_need=L.get('what_we_need', '')))
    write(ans / 'solved-ledger.csv', LEDGER_COLS, out); write(ans / 'search-list.csv', SEARCH_COLS, [{c: r.get(c, '') for c in SEARCH_COLS} for r in search])
    from collections import Counter
    print(f'ledger: {len(out)} rows; owner decision pending {sum(r["owner_decision"] == "pending" for r in out)}; join_ready no {sum(r["join_ready"] == "no" for r in out)}; solved {sum(r["solved"] == "yes" for r in out)} ({dict(Counter(r["solved_basis"] for r in out))}); search list {len(search)} rows')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage'] and len(a) == 3: stage(a[1], a[2])
    elif a[:1] == ['ledger'] and len(a) == 2: build_ledger(a[1])
    else: print(__doc__); sys.exit(2)

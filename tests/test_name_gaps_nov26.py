#!/usr/bin/env python3
"""26 Nov 2026 (owner 5:18 PM: 'no more putting stuff off'): the outline-to-pin parks of the 1654 PC test that were name gaps.
  A  POTA writes the agency's own name + POTA's type: 'Inspiration Peak State Wayside' + 'State Natural Site' is the park's full
     name; 'Toad River AMA (Becker/Otter Tail)' + 'State Conservation Area' too (brackets aside).
  B  FWS 'Upper Mississippi River National Wildlife and Fish Refuge' = POTA's 'Upper Mississippi River National Wildlife Refuge'.
  C  NY DEC's class names: 'Crystal Lake Wild Forest' / 'Burt Hill Multiple Use Area' = POTA's '... State Forest'; a name with no
     real word left ('Lake State Forest') never swaps.
  D  the new join: only a record holding POTA's pin, never water, an office or a NO; a bare name needs the park's kind.
Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_match_checks as MC  # noqa: E402
import kpc_same_land as SL  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


check('A: agency name + POTA type = the park name',
      MC.exact_name('Inspiration Peak State Wayside State Natural Site', 'Inspiration Peak State Wayside', 'State Natural Site')
      and MC.exact_name('Toad River AMA State Conservation Area', 'Toad River AMA (Becker/Otter Tail)', 'State Conservation Area')
      and not MC.exact_name('Horseshoe Bay Protected Area', 'Horseshoe Bay WMA', 'Protected Area'))
check('B: National Wildlife and Fish Refuge = National Wildlife Refuge',
      MC.exact_name('Upper Mississippi River National Wildlife Refuge', 'UPPER MISSISSIPPI RIVER NATIONAL WILDLIFE AND FISH REFUGE')
      and not MC.exact_name('Upper Mississippi River National Wildlife Refuge', 'Upper Mississippi River National Fish Hatchery'))
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
ns = {'MC': MC, 'SL': SL, 're': re}
exec(src[src.index('KIND_SWAPS = {'):src.index('def rec_names(rec):')], ns)
ks = ns['kind_swap']
check("C: NY DEC class names swap with State Forest; 'Lake State Forest' never does",
      ks('Crystal Lake State Forest', 'Crystal Lake Wild Forest') and ks('Burt Hill State Forest', 'Burt Hill Multiple Use Area')
      and not ks('Lake State Forest', 'Lake Wild Forest') and not ks('Crystal Lake State Park', 'Crystal Lake Wild Forest'))
blk = src[src.index("# 26 Nov 2026 (owner 5:18 PM 'no more putting stuff off'; the 1654 PC test"):src.index("        site = []\n        if not m and la is not None:")]
check('D: the new join needs the pin inside, no water, no office, no NO, and the park kind for a bare name',
      'inside_slack(la, lo, a[\'_g\'])' in blk and "a.get('Water')" in blk and 'KM.is_admin(nm)' in blk and '_no_all(ov, a)' in blk
      and "not kinds(nm) and not (set(a.get('_k') or ()) & kp)" in blk)
ns2 = {'MC': MC, 'SL': SL, 're': re}
a_ = src.index('PLACE_WORDS = {'); exec(src[a_:src.index('\n', a_)], ns2)
a_ = src.index('CORE_DROP = {'); exec(src[a_:src.index('KIND_SWAPS = {')], ns2)
nc = ns2['name_core']
check("E: core names: Nick's Lake and Reinstein Woods equal their records; Lake Vermilion begins the DNR park's name; 'Lake State Park' has no core",
      nc('Nick\u2019s Lake Campground and Day Use State Recreation Site', 'State Recreation Site') == nc('Nicks Lake Campground')
      and nc('Reinstein Woods State Nature Preserve', 'State Nature Preserve') == nc('Reinstein Woods Nature Preserve And Environmental Education Center')
      and nc('Lake Vermilion-Soudan Underground Mine State Park')[:2] == nc('Lake Vermilion State Park', 'State Park')
      and nc('Lake State Park', 'State Park') == ())
blk2 = src[src.index("# 26 Nov 2026 (owner 5:25 PM 'stop holding fixes back')"):src.index("        site = []\n        if not m and la is not None:")]
check('F: the core-name joins need the pin inside and agreeing kinds, never water, an office or a NO',
      "inside_slack(la, lo, a['_g'])" in blk2 and "a.get('Water')" in blk2 and 'KM.is_admin(nm)' in blk2 and '_no_all(ov, a)' in blk2
      and '_rk & _pk2' in blk2)
fs = (ROOT / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
check("G: the 2-fer live check never reads an agency id ('sgmnb06') as row 6", "if m.group(2).startswith('0'): return [], None, False" in fs)
f_ = {'page': {'kind': 'html', 'own_page': 'own', 'name_on_page': 'Kentucky Department of Fish and Wildlife', 'host': 'fw.ky.gov',
                'names': ['Perkins WMA', 'Perkins-Cooley WMA']}}
check("H: a name found anywhere on the park's own page names the land; another POTA park's name never does; no names = as before",
      MC.page_names_land(f_, 'Perkins Wildlife Management Area', 'Perkins WMA')
      and not MC.page_names_land(f_, 'Perkins Wildlife Management Area', 'Perkins-Cooley WMA', names_in_state={MC.full('Perkins-Cooley WMA')})
      and not MC.page_names_land({'page': dict(f_['page'], names=[])}, 'Perkins Wildlife Management Area', 'Perkins WMA'))
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)

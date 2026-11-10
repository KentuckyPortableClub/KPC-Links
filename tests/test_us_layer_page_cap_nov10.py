#!/usr/bin/env python3
"""Nov 10: state GIS paging must not stop on a silent ArcGIS page cap.

Run 42797939226: the FL DEP Division of State Lands layer (sgflf) was stored in the
boundary-cache as 199 records (one ~200-feature server page) against a live key of
21,993 shapes and ids up to sgflf17001. GEO_PAGE defaults to 500, so a 200-feature
page with exceededTransferLimit unset was treated as the last page.

This test execs only the two helpers (it does not import kpc_us_key, which would run the builder).
"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
start = src.index('def layer_page_size')
end = src.index('def fetch_geo')
ns = {}
exec(compile(src[start:end], 'kpc_us_key.py', 'exec'), ns)
layer_page_size = ns['layer_page_size']
keep_paging = ns['keep_paging']
ok = True

def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def test_page_size_honors_server_cap():
    check('500 asked, server cap 200 -> 200', layer_page_size(500, 200) == 200)
    check('no cap keeps 500', layer_page_size(500, None) == 500)
    check('cap above PAGE keeps PAGE', layer_page_size(500, 2000) == 500)
    check('invalid asked size falls back then cap applies', layer_page_size(0, 200) == 200)


def test_keep_paging_when_server_omits_exceeded_flag():
    pg = layer_page_size(500, 200)
    check('effective page is the server cap', pg == 200)
    check('full capped page continues (exceeded unset)', keep_paging(200, pg, None) is True)
    check('full capped page continues (exceeded false)', keep_paging(200, pg, False) is True)
    check('short last page stops', keep_paging(199, pg, None) is False)
    check('empty page stops', keep_paging(0, pg, None) is False)
    check('no new ids (offset ignored) stops', keep_paging(200, pg, True, n_new=0) is False)
    check('full page with new ids continues', keep_paging(200, pg, True, n_new=200) is True)


def test_old_stop_condition_is_what_failed():
    page, n_got, exceeded = 500, 200, None
    old_stop = (not n_got) or ((not exceeded) and n_got < page)
    check('old stop condition treated a 200-of-500 page as the last page', old_stop is True)
    new_page = layer_page_size(page, 200)
    check('fixed paging continues that page', keep_paging(n_got, new_page, exceeded) is True)


if __name__ == '__main__':
    test_page_size_honors_server_cap()
    test_keep_paging_when_server_omits_exceeded_flag()
    test_old_stop_condition_is_what_failed()
    sys.exit(0 if ok else 1)

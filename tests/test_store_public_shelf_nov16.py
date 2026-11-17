"""The public shelf of the outline store (KPC owner, 2026-11-16; Fable's brief): tools/kpc_store_public.py.

One synthetic area holds every kind of park the shelf must handle, and the shelf is then searched, byte by byte, for every
held thing: refs (in every way the KPC-Store push check looks for them), names, record keys, layer names, private fields,
WDPA words and the share-alike class. Then the 2-fer bot's own reader reads the shelf and must (1) read every park on it the
same way it reads the full store, and (2) treat every park the shelf left off as held privately, never as missing.

    US-9001  Open Meadow               one OPEN record                        -> on the shelf
    US-9002  Hidden Hollow Secretland  held, no public view                   -> off, never named
    US-9003  Wdpa Island               a Protected Planet record              -> off, never named
    US-9004  Sharealike Ridge          a SHARE-ALIKE record                   -> off, never named
    US-9005  Partial Peak              one public + one held record, a        -> on, the public record only, still partial
                                       PARTIAL view (owner decision, Nov 15)
    US-9006  Nocredit Flats            publishable but no credit line         -> off (the gate needs a credit to publish)
    US-9007  Twin Rings                a public record that shares the rings  -> on, rings copied in, the held twin gone
                                       of a held record (same_geometry_as)
"""
import gzip, hashlib, json, pathlib, re, shutil, sys, tempfile, unittest, zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests')); sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import display_copy_fixture as F  # noqa: E402
import kpc_display_copy as DC  # noqa: E402
import kpc_store_public as SP  # noqa: E402
import kpc_fers_store as FS  # noqa: E402

AREA = 'US-ZZ'
MADE = {'made': '2026-11-16T04:26:34-06:00'}   # the reader refuses an index with no build date (the real store has one)
VIEW = {'publish_view_basis': DC.VIEW_BASIS}
HELD_REFS = ['US-9002', 'US-9003', 'US-9004', 'US-9006']
HELD_NAMES = ['Hidden Hollow Secretland', 'Wdpa Island', 'Sharealike Ridge', 'Nocredit Flats']
HELD_KEYS = ['h1secret', 'w1secret', 's1secret', 'n1secret', 'p2secret', 't2secret']
HELD_LAYERS = ['heldlayerq', 'wdpalayerq', 'salayerq', 'nocreditlayerq']
# A PUBLIC record carries these too in the real store (US-RI, 16 Nov): they must be stripped even from a record that is on the shelf
PUBLIC_RECORD_EXTRAS = {'attributes': {'Own_Name': 'Landowner Secretname', 'GIS_Src': 'internal_secret_gdb'},
                        'owner': 'Landowner Secretname', 'request': 'https://example.invalid/query?token=secrettoken123',
                        'source_detail': 'internal_secret_gdb', 'join': {'how': 'secretjoinnote'}}


def sq(i, s=0.01):
    x = i * 0.05
    return [F.square(x, 0.0, x + s, s)]


def make_store(d):
    t2 = F.record('t2secret', 'heldlayerq', sq(7), publishable=False)
    t1 = F.record('t1', 'openlayer', sq(7), same_geometry_as='t2secret')
    t1['rings'] = None   # the store keeps one copy of the shared rings, on the held twin
    parks = [
        F.park('US-9001', [F.record('o1', 'openlayer', sq(1), **PUBLIC_RECORD_EXTRAS)], name='Open Meadow'),
        F.park('US-9002', [F.record('h1secret', 'heldlayerq', sq(2), publishable=False,
                                    attributes={'Own_Name': 'Private Owner Secretname'}, owner='Private Owner Secretname')],
               name='Hidden Hollow Secretland'),
        F.park('US-9003', [F.record('w1secret', 'wdpalayerq', sq(3), url='https://protectedplanet.example/arcgis/rest/services/w/MapServer/0')],
               name='Wdpa Island'),
        F.park('US-9004', [F.record('s1secret', 'salayerq', sq(4), cls='SHARE-ALIKE')], name='Sharealike Ridge'),
        dict(F.park('US-9005', [F.record('p1', 'openlayer', sq(5)), F.record('p2secret', 'heldlayerq', sq(5, 0.02), publishable=False)],
                    name='Partial Peak'), publish_view=DC.VIEW_NAME_PARTIAL, publish_view_records=['p1'], publish_view_ratio=0.4, **VIEW),
        F.park('US-9006', [F.record('n1secret', 'nocreditlayerq', sq(6), credit='')], name='Nocredit Flats'),
        dict(F.park('US-9007', [t1, t2], name='Twin Rings'), publish_view=DC.VIEW_NAME, publish_view_records=['t1'],
             publish_view_ratio=1.0, **VIEW),
    ]
    over = {p['ref']: {'park_public': p['ref'] in ('US-9001', 'US-9005', 'US-9007')} for p in parks}
    over['US-9005'].update(publish_view=DC.VIEW_NAME_PARTIAL, publish_view_records=['p1'], publish_view_ratio=0.4, **VIEW)
    over['US-9007'].update(publish_view=DC.VIEW_NAME, publish_view_records=['t1'], publish_view_ratio=1.0, **VIEW)
    F.write_store(d, AREA, parks, fmt='kpc-outline-store-index/4', index_override=over, top=MADE)
    return parks


def shelf_bytes(out):
    """Everything on the shelf as text: the index, and the store file fully unpacked (every gzip member)."""
    out = pathlib.Path(out)
    raw = (out / f'{AREA}.kpcstore.json.gz').read_bytes()
    txt, pos = [], 0
    while pos < len(raw):
        z = zlib.decompressobj(31); txt.append(z.decompress(raw[pos:]).decode('utf-8')); pos = len(raw) - len(z.unused_data)
    return (out / f'index-{AREA}.json').read_text(encoding='utf-8') + '\n' + ''.join(txt)


def ref_variants(ref):
    """the ways the KPC-Store push check looks for a withheld ref: any case, '-', ' ', '_' or an escaped hyphen"""
    a, b = ref.split('-')
    return [f'{a}{s}{b}' for s in ('-', ' ', '_', '\\u002d')]


class PublicShelf(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.store, self.out = self.tmp / 'store', self.tmp / 'shelf'
        make_store(self.store)
        self.before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.store.iterdir()}
        self.rep = SP.build_area(self.store, AREA, self.out)
        self.text = shelf_bytes(self.out)
        self.sidx = json.loads((self.out / f'index-{AREA}.json').read_text())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_which_parks_are_on_the_shelf(self):
        self.assertEqual(sorted(self.sidx['parks']), ['US-9001', 'US-9005', 'US-9007'])
        self.assertEqual(self.sidx['shelf'], 'public')
        self.assertEqual(self.sidx['parks']['US-9005']['records'], ['p1'])
        self.assertEqual(self.sidx['parks']['US-9007']['records'], ['t1'])

    def test_nothing_held_is_anywhere_on_the_shelf(self):
        low = self.text.lower()
        for ref in HELD_REFS:
            for v in ref_variants(ref):
                self.assertNotIn(v.lower(), low, f'held park {ref} named as {v!r}')
        for t in HELD_NAMES + HELD_KEYS + HELD_LAYERS + ['Private Owner Secretname', 'protectedplanet', 'Landowner Secretname',
                                                       'internal_secret_gdb', 'secrettoken123', 'secretjoinnote']:
            self.assertNotIn(t.lower(), low, f'held text {t!r} is on the shelf')
        # 'SHARE-ALIKE' is one of the class NAMES every index lists (licence_classes, the vocabulary the gate checks against);
        # what must never be here is a RECORD of that class
        self.assertNotRegex(low, r'"licence_class"\s*:\s*"share-alike"')
        for f in ('private_reason', 'terms_text_file', 'terms_text_sha256', 'attributes', '"owner"', 'same_geometry_as', 'publish_why',
                  'publish_basis_detail'):
            self.assertNotIn(f, self.text, f'private field {f} is on the shelf')

    def test_the_report_names_nobody(self):
        blob = json.dumps(self.rep)
        for t in HELD_REFS + HELD_NAMES + HELD_KEYS: self.assertNotIn(t, blob)
        self.assertEqual(self.rep['parks_on_shelf'], 3); self.assertEqual(sum(self.rep['left_off'].values()), 4)

    def test_the_private_store_is_never_changed(self):
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.store.iterdir()}
        self.assertEqual(after, self.before)

    def test_its_own_check_passes_and_refuses_a_tampered_shelf(self):
        self.assertEqual(SP.check_area(self.out, AREA), 3)
        idx = json.loads((self.out / f'index-{AREA}.json').read_text())
        idx['parks']['US-9001']['record_meta']['o1']['private_reason'] = 'leaked'
        (self.out / f'index-{AREA}.json').write_text(json.dumps(idx))
        with self.assertRaises(SP.ShelfError): SP.check_area(self.out, AREA)

    def test_the_two_fer_reader_reads_the_shelf_like_the_full_store(self):
        full, shelf = FS.Store(self.store, kind='public'), FS.Store(self.out, kind='public')
        fidx = json.loads((self.store / f'index-{AREA}.json').read_text())
        FS.PARTIAL_VIEW.clear()
        for ref, e in fidx['parks'].items():
            ids = list(e['records'])
            _, _, w1, i1 = full.examine(ref, AREA, ids)
            _, _, w2, i2 = shelf.examine(ref, AREA, ids)
            if ref in self.sidx['parks']:
                self.assertEqual((w1, i1.get('points'), i1.get('box')), (w2, i2.get('points'), i2.get('box')), ref)
                self.assertEqual(w2, '', ref)
            else:
                self.assertTrue(w2 and FS.PRIVATE_WHY.search(w2), f'{ref} off the shelf must be held privately, got {w2!r}')
        self.assertIn('US-9005', FS.PARTIAL_VIEW, 'a partial park must still be marked partial boundary')

    def test_a_licence_confirmed_later_puts_the_park_on_the_next_build(self):
        """the owner asked how a layer cleared later gets onto the shelf: nothing moves, the next build has it"""
        parks = make_store(self.store)
        for p in parks:
            if p['ref'] == 'US-9002':
                r = p['records'][0]
                r.update(publishable=True, publish_basis='verified-row', private_reason='',
                         publish_basis_detail={'evidence_url': 'https://example.invalid/terms', 'date_read': '2026-11-14'})
        over = {p['ref']: {'park_public': True} for p in parks}
        F.write_store(self.store, AREA, [p for p in parks if p['ref'] in ('US-9001', 'US-9002')], fmt='kpc-outline-store-index/4',
                      index_override=over, top=MADE)
        SP.build_area(self.store, AREA, self.out)
        self.assertIn('US-9002', json.loads((self.out / f'index-{AREA}.json').read_text())['parks'])

    def test_a_reader_on_the_private_store_is_unchanged(self):
        """the private path: a park the store does not have is still 'not in the outline store' (store-filler list)"""
        _, _, w, _ = FS.Store(self.store, kind='public').examine('US-9999', AREA, ['nope'])
        self.assertIn('is not in the outline store', w)
        self.assertFalse(FS.PRIVATE_WHY.search(w))



class ReviewCases(unittest.TestCase):
    """Fable's review of #237 (2026-11-16): the three ways a park left off the shelf could still be named, or measured wrongly."""

    def setUp(self):
        import kpc_fers as KF
        self.KF = KF
        self.tmp = pathlib.Path(tempfile.mkdtemp()); self.st, self.out = self.tmp / 's', self.tmp / 'o'
        for d in (FS.FLAGS, FS.STORE_LINES, FS.LINE_SKIPPED, FS.MAIN_LINES): d.clear()
        FS.HELD_PRIVATE.clear(); FS.READ_OK.clear(); FS.PRIVATE.clear()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_a_park_in_two_areas_held_in_one_is_never_named(self):
        """Fable's repro: US-9100 is public in US-AA and held in US-BB. The full store holds it privately; the shelf must too."""
        F.write_store(self.st, 'US-AA', [F.park('US-9100', [F.record('a1', 'openlayer', sq(1))], name='Border Park')],
                      fmt='kpc-outline-store-index/4', index_override={'US-9100': {'park_public': True}}, top=MADE)
        F.write_store(self.st, 'US-BB', [F.park('US-9100', [F.record('b1held', 'heldlayerq', sq(2), publishable=False)], name='Border Park'),
                                         F.park('US-9101', [F.record('c1', 'openlayer', sq(3))])], fmt='kpc-outline-store-index/4',
                      index_override={'US-9100': {'park_public': False}, 'US-9101': {'park_public': True}}, top=MADE)
        for a in ('US-AA', 'US-BB'): SP.build_area(self.st, a, self.out)
        ids = ['a1', 'b1held']
        _, _, w_full, _ = FS.Store(self.st, kind='public').examine('US-9100', 'US-AA', ids)
        _, _, w_shelf, _ = FS.Store(self.out, kind='public').examine('US-9100', 'US-AA', ids)
        self.assertTrue(FS.PRIVATE_WHY.search(w_full), w_full)
        self.assertTrue(FS.PRIVATE_WHY.search(w_shelf), f'the shelf must hold it privately too, got {w_shelf!r}')
        self.assertNotIn('b1held', w_shelf)

    def _line_area(self, parks, over):
        F.write_store(self.st, AREA, parks, fmt='kpc-outline-store-index/4', index_override=over, top=MADE)
        SP.build_area(self.st, AREA, self.out)

    def _lines(self, d, base):
        log0 = len(self.KF.LOG)
        for x in (FS.FLAGS, FS.STORE_LINES, FS.LINE_SKIPPED, FS.MAIN_LINES): x.clear()
        FS.HELD_PRIVATE.clear()
        out = FS.store_lines(self.KF, FS.Store(d, kind='public'), [AREA], base)
        return out, ' '.join(self.KF.LOG[log0:]), set(FS.HELD_PRIVATE), dict(FS.LINE_SKIPPED)

    def test_a_held_line_park_is_never_named(self):
        path = [[(-77.20, 41.20), (-77.19, 41.20)]]
        held = F.line_record('lh1secret', 'heldlayerq', path, publishable=False, boundary_rule='trail_100ft')
        self._line_area([F.park('US-9200', [held], name='Secret Ridge Trail')],
                        {'US-9200': {'park_public': False, 'geometry_kind': 'line'}})
        self.assertNotIn('US-9200', json.loads((self.out / f'index-{AREA}.json').read_text())['parks'])
        base = {'US-9200': {'lines': [[[-77.20, 41.20], [-77.19, 41.20]]], 'kind': 'trail', 'by': 'x', 'type': 'NRT'}}
        _, log_full, held_full, _ = self._lines(self.st, base)
        _, log_shelf, held_shelf, _ = self._lines(self.out, base)
        self.assertIn('US-9200', held_full)
        self.assertIn('US-9200', held_shelf, 'a line park left off the shelf must be held privately, as with the full store')
        for t in ('US-9200', 'Secret Ridge', 'lh1secret'): self.assertNotIn(t, log_shelf)

    def test_a_river_line_found_by_name_is_still_skipped(self):
        path = [[(-77.30, 41.30), (-77.29, 41.30)]]
        rec = F.line_record('ln1', 'openlayer', path, source='nhd-by-name', boundary_rule='river_100ft_from_bank',
                            river_class='water_trail', bank_status='covered')
        self._line_area([F.park('US-9300', [rec], name='By Name River')], {'US-9300': {'park_public': True, 'geometry_kind': 'line'}})
        idx = json.loads((self.out / f'index-{AREA}.json').read_text())
        park, _, _ = DC.read_park(self.out, 'US-9300', idx['parks']['US-9300'], {})
        self.assertEqual(park['records'][0].get('source'), 'nhd-by-name', 'the shelf keeps the record source the reader needs')
        base = {'US-9300': {'lines': [[[-77.30, 41.30], [-77.29, 41.30]]], 'kind': 'river', 'by': 'x', 'type': 'WT'}}
        _, _, _, skip_full = self._lines(self.st, base)
        _, _, _, skip_shelf = self._lines(self.out, base)
        self.assertIn('US-9300', skip_full)
        self.assertEqual(skip_shelf.get('US-9300'), skip_full['US-9300'], 'the shelf must skip a by-name river line exactly as the full store does')

    def test_an_odd_source_value_is_dropped_not_copied(self):
        rec = F.record('o9', 'openlayer', sq(9), source='have:C:/Users/someone/private/State_Land.geojson')
        F.write_store(self.st, AREA, [F.park('US-9400', [rec])], fmt='kpc-outline-store-index/4',
                      index_override={'US-9400': {'park_public': True}}, top=MADE)
        SP.build_area(self.st, AREA, self.out)
        txt = shelf_bytes(self.out)
        self.assertNotIn('someone', txt); self.assertNotIn('State_Land', txt)


if __name__ == '__main__':
    unittest.main()

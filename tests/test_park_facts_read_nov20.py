"""The keys' reader for KPC-Data's park facts file (kpc_park_facts_read.py): its own self-test, plus the key workflows carry
the read-only step that hands the official sizes to the size readers (the owner, 20 Nov 2026 2:51 PM)."""
import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_reader_selftest():
    r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_park_facts_read.py'), '--selftest'], capture_output=True, text=True)
    assert r.returncode == 0 and 'SELF-TEST PASSED' in r.stdout, r.stdout + r.stderr


def test_key_jobs_read_the_park_facts():
    want = {'kpc-us-key.yml': 2, 'kpc-ca-key.yml': 1, 'kpc-world-key.yml': 1, 'kpc-key-postcheck.yml': 1}
    for fn, n in want.items():
        txt = (ROOT / '.github/workflows' / fn).read_text(encoding='utf-8')
        assert txt.count('kpc_park_facts_read.py acres --out data/acres.json') == n, fn
        assert txt.count('Park facts from KPC-Data (read only') == n, fn


def test_the_copy_is_never_committed():
    ign = (ROOT / '.gitignore').read_text(encoding='utf-8').split()
    assert 'data/acres.json' in ign and '.pf/' in ign


if __name__ == '__main__':
    test_reader_selftest(); test_key_jobs_read_the_park_facts(); test_the_copy_is_never_committed(); print('ALL PASS')

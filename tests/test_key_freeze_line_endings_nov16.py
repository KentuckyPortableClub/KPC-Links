#!/usr/bin/env python3
"""Nov 16 2026 (KPC owner): the rules hash must not move with a checkout's LINE ENDINGS.

What went wrong: the PC 2-fer runner clones KPC-Links with Git for Windows, which writes CRLF by default. The rule files then
hold different bytes than the same commit does on Linux, so kpc_key_freeze.rules_hash worked out us-key 3759b3c8b122 while
every green key carried d4ebfafce438. The 2-fer key gate called all 65 areas stale and refused the whole run, with nothing
at all wrong with the keys.

These tests check both locks:
  1. rules_hash levels line endings, so a CRLF copy of a tree hashes the same as the LF original (all four kinds).
  2. .gitattributes names every file in RULE_FILES, so a fresh checkout gets LF on Windows too.
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_freeze as F  # noqa: E402


def rule_files():
    out = set()
    for v in F.RULE_FILES.values():
        out |= set(v)
    out.add(F.VERSION_FILE)
    return sorted(out)


class LineEndings(unittest.TestCase):
    def test_crlf_tree_hashes_the_same(self):
        """A copy of the rule files with CRLF endings gives the same hash as this checkout, for every kind."""
        here = {k: F.rules_hash(k) for k in F.RULE_FILES}
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            copied = 0
            for rel in rule_files():
                src = ROOT / rel
                if not src.is_file():
                    continue
                dst = tmp / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
                copied += 1
            self.assertGreater(copied, 10, 'the rule files were not found in this checkout')
            for k in sorted(F.RULE_FILES):
                self.assertEqual(F.rules_hash(k, root=tmp), here[k], f'{k}: the rules hash moved with the line endings')

    def test_lone_cr_counts_as_a_line_break(self):
        self.assertEqual(F.same_lines(b'a\r\nb\rc\nd'), b'a\nb\nc\nd')

    def test_lf_bytes_are_untouched(self):
        """A tree already stored with LF must keep the hash it has always had: same_lines changes nothing there."""
        for rel in rule_files():
            p = ROOT / rel
            if p.is_file():
                b = p.read_bytes()
                if b'\r' not in b:
                    self.assertEqual(F.same_lines(b), b, rel)

    def test_a_real_file_change_still_moves_the_hash(self):
        """The levelling must not make the hash blind: a changed rule file still moves it."""
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td)
            for rel in rule_files():
                src = ROOT / rel
                if src.is_file():
                    dst = tmp / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            before = F.rules_hash('us-key', root=tmp)
            t = tmp / '.github' / 'scripts' / 'kpc_key_rules.py'
            t.write_bytes(t.read_bytes() + b'\n# one more line\n')
            self.assertNotEqual(F.rules_hash('us-key', root=tmp), before)


class GitAttributes(unittest.TestCase):
    def test_every_rule_file_is_named(self):
        p = ROOT / '.gitattributes'
        self.assertTrue(p.is_file(), 'there is no .gitattributes: a Windows checkout would get CRLF')
        named = {}
        for line in p.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            bits = line.split()
            named[bits[0]] = set(bits[1:])
        for rel in rule_files():
            self.assertIn(rel, named, f'{rel} is a rule file but is not in .gitattributes')
            self.assertIn('eol=lf', named[rel], f'{rel} is in .gitattributes without eol=lf')

    def test_git_agrees_the_rule_files_are_lf(self):
        """git itself must report eol=lf for the rule files (so the attribute file is really in force)."""
        rels = rule_files()
        r = subprocess.run(['git', 'check-attr', 'eol', '--', *rels], cwd=str(ROOT), capture_output=True, text=True)
        if r.returncode != 0:
            self.skipTest('git check-attr is not available here')
        got = {}
        for line in (r.stdout or '').splitlines():
            if ': eol: ' in line:
                rel, _, val = line.rpartition(': eol: ')
                got[rel[:-len(': eol')] if rel.endswith(': eol') else rel.split(': eol')[0]] = val.strip()
        for rel in rels:
            self.assertEqual(got.get(rel), 'lf', f'git does not see eol=lf for {rel}: {got.get(rel)!r}')


class HashIsStillTheSame(unittest.TestCase):
    def test_the_four_kinds_hash_to_12_hex(self):
        for k in sorted(F.RULE_FILES):
            h = F.rules_hash(k)
            self.assertRegex(h, r'^[0-9a-f]{12}$', k)

    def test_the_levelling_matches_a_hand_worked_hash(self):
        """The hash is still a plain sha256 over the levelled bytes: no other change slipped in."""
        h = hashlib.sha256()
        for rel in sorted(F.RULE_FILES['ca-key']):
            f = ROOT / rel
            if rel in F.SCOPE_FILES.values() and not f.is_file():
                continue
            b = F.same_lines(f.read_bytes()) if f.is_file() else b'missing'
            h.update(rel.encode() + b'\0' + b + b'\0')
        import json
        try:
            ver = json.load(open(ROOT / F.VERSION_FILE, encoding='utf-8')).get('ca-key')
        except Exception:  # noqa: BLE001
            ver = None
        h.update(b'version\0' + str(ver).encode())
        self.assertEqual(F.rules_hash('ca-key'), h.hexdigest()[:12])


if __name__ == '__main__':
    unittest.main()

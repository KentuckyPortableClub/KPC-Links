# Nov 8 (KPC-Links #76, Brandon OK): a source that MOVED is declared in docs/key-rules-change.txt as
#   moved source (#NN, CC): <old url> -> <new url> (name field <old> -> <new>)
# and the key-file guards accept exactly that swap (same country, same label, nothing else changed).
import re as _re_ms, pathlib as _pl_ms
def moved_sources(root):
    p = _pl_ms.Path(root) / 'docs/key-rules-change.txt'
    t = p.read_text(encoding='utf-8') if p.is_file() else ''
    return [dict(cc=m.group(1), old=m.group(2), new=m.group(3), f0=m.group(4), f1=m.group(5)) for m in _re_ms.finditer(
        r'^moved source \(#\d+, ([A-Z]{2})\): (\S+) -> (\S+) \(name field (\S+) -> (\S+)\)\s*$', t, _re_ms.M)]
def apply_moved(text, moves):
    """the origin/main text of a key input file with the declared moves applied (url, then the name field next to it)."""
    for m in moves:
        i = text.find(m['old'])
        while i >= 0:
            text = text[:i] + m['new'] + text[i + len(m['old']):]
            j = text.find('"' + m['f0'] + '"', i)
            if 0 <= j - i < 300: text = text[:j] + '"' + m['f1'] + '"' + text[j + len(m['f0']) + 2:]
            i = text.find(m['old'], i)
    return text

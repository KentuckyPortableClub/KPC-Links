"""Small helper: open, update or close one GitHub issue per report (uses the gh CLI and GITHUB_TOKEN)."""
import json
import subprocess


def _gh(*args, input_text=None):
    r = subprocess.run(['gh', *args], input=input_text, text=True, capture_output=True)
    if r.returncode != 0:
        print('gh error:', r.stderr.strip())
    return r.stdout


def report(label, title, body, problems):
    """problems > 0: create or update the open issue with this label. problems == 0: close it."""
    _gh('label', 'create', label, '--color', 'D5A63A', '--description', 'Opened automatically by a KPC workflow', '--force')
    found = json.loads(_gh('issue', 'list', '--label', label, '--state', 'open', '--json', 'number', '--limit', '1') or '[]')
    num = found[0]['number'] if found else None
    if problems:
        if num:
            _gh('issue', 'edit', str(num), '--title', title, '--body-file', '-', input_text=body)
            print('Updated issue #%s' % num)
        else:
            print(_gh('issue', 'create', '--title', title, '--label', label, '--body-file', '-', input_text=body).strip())
    elif num:
        _gh('issue', 'close', str(num), '--comment', 'All clear on the latest check. Closing automatically.')
        print('Closed issue #%s' % num)
    else:
        print('All clear; no issue needed.')

#!/usr/bin/env python3
"""Oct 25: undo a state file whose only change is a time stamp, so the Save step finds nothing to commit.
Usage: python3 kpc_save_filter.py file1.json file2.json ...   (run before `git add`).
A file is put back to the committed copy when, with the STAMP keys left out, it equals the committed copy.
Never fails: any doubt (new file, unreadable, not JSON) leaves the file alone."""
import json, subprocess, sys

STAMP = {'updated', 'commands_from', 'checked', 'last_run', 'last_checked', 'ts', 'time', 'when', 'generated', 'run_at'}


def strip(x):
    if isinstance(x, dict): return {k: strip(v) for k, v in x.items() if k not in STAMP}
    if isinstance(x, list): return [strip(v) for v in x]
    return x


for f in sys.argv[1:]:
    try:
        old = subprocess.run(['git', 'show', f'HEAD:{f}'], capture_output=True, text=True)
        if old.returncode != 0: continue
        new = json.load(open(f))
        if strip(json.loads(old.stdout)) == strip(new):
            if json.loads(old.stdout) != new:
                subprocess.run(['git', 'checkout', '--', f], check=False)
                print(f'{f}: only time stamps changed, not saving')
    except Exception as e:  # noqa: BLE001
        print(f'{f}: left alone ({str(e)[:60]})')

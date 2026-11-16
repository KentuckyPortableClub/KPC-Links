#!/usr/bin/env python3
"""THE ONE CLUB SPOT READER (KPC owner, 2026-11-16, handoff item 7). Asks POTA for the activator spots at most once per 5 minutes
(through kpc_pota_door: stored copy first, paced, budget, club User-Agent) and saves them to a small file on the club's own site,
data/pota/spots.json = {"saved": <unix time>, "source": "POTA /spot/activator", "spots": [...POTA's rows as they came...]}.
The live pages, the Discord spotter (kpc_pota_spotter.py) and the hunters job (kpc_hunters.py) read that file and never call
POTA for spots. Run inside the Discord spotter's job, once per 5-minute check (kpc-pota-discord.yml; no schedule change).
Exit 0 when the file is fresh (written now or under 5 minutes old), 1 when POTA could not be read (the old file stays)."""
import json, os, pathlib, sys, time
import kpc_net_guard; kpc_net_guard.install()
import kpc_pota_door as DOOR
from kpc_scrub import clip   # every log line scrubbed first, then cut

KEEP_FIELDS = None   # POTA's rows as they came (the pages read their own fields)


def main():
    out = pathlib.Path(os.environ.get('KPC_POTA_SPOT_FILE') or DOOR.SPOT_FILE)
    try: spots, asked = DOOR.fetch_spots()
    except DOOR.DoorClosed as e:
        print(f'::warning title=Club spot reader::{clip(e, 300)}; the last spot file stays'); return 1
    if not asked:
        print('::notice title=Club spot reader::the spot file is under 5 minutes old; POTA not asked'); return 0
    if not isinstance(spots, list):
        print('::warning title=Club spot reader::POTA answered with something that is not a list; the last spot file stays'); return 1
    doc = {'saved': int(time.time()), 'source': 'POTA /spot/activator (one club reader, every 5 minutes)', 'spots': spots}
    out.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(doc, separators=(',', ':'), ensure_ascii=False) + '\n'
    if len(body.encode()) > DOOR.MAX_FILE:
        print(f'::warning title=Club spot reader::{len(body):,} bytes is over the 1 MB cap; the last spot file stays'); return 1
    tmp = out.with_name(out.name + '.tmp'); tmp.write_text(body, encoding='utf-8', newline='\n'); os.replace(tmp, out)
    print(f'::notice title=Club spot reader::{len(spots)} spots saved to {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

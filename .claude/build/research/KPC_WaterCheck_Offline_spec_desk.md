# Water check that survives a USGS outage: spec for the builder chat (desk, Oct 28 2026)
Desk is read only, so this is a spec, not code. Builder: chat 2.

1. Fetcher stage: for each state's candidate pairs, fetch NHD High Resolution flowlines + waterbodies only inside a small box (about 500 m) around each candidate spot. Do not fetch whole states.
2. Save them as one small file per state in the bundle (release asset), e.g. `water-US-KY.json`, with `fetched` date and `source` (USGS NHD HR) inside.
3. Water check order: (a) live USGS answer; (b) else the saved copy, and the result carries "water data from <date>" (rule 13); (c) else NOT SURE, as now.
4. Only replace the saved copy after a live fetch fully succeeds. Never overwrite a good copy with an empty or partial one.
5. A spot added after the last good fetch has no saved pieces: that spot is NOT SURE, not "no water".
6. Test once: block the live URL on purpose for one state, confirm the answer comes from the saved copy and shows its date; delete the copy, confirm NOT SURE.
7. The one rerun: same land = 2-fer, trail x trail on public land, the 35 Ohio rows fix. Name-match stays OFF until Brandon's OK (Rulings list).

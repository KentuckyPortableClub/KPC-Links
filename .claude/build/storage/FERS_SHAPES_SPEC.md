# 2-fer area files: big shapes stored apart (chat 3, Oct 29 6:20 PM; for chat 2's save step) 
Problem: data/fers/US-AK.json.gz = 135 MB (> GitHub's 100 MB). Cause: each spot's `shape` (patch), `lines` (park edges) and `zone` (trail band) are inline, ~95% of the file.
## The format (Rule G R-G6 3 m detail unchanged; nothing is thinned)
- Area file keeps every spot, but a spot whose shape+lines+zone weigh > 20,000 bytes loses those three and gets:
  `"heavy": "shapes/US-AK/<14-hex hash of the spot id>"`, `"heavy_n": <bytes moved>`, `"shape_sig": "<12-hex fingerprint of the shape>"`; it keeps `box`, `center`, `acres`, `status`, `refs`, `names`, `passes`, `wide_m`… (everything the checker / far-hold / far-check / layered read).
- `data/fers/shapes/US-AK/<hash>.json.gz` = `{"id": <spot id>, "shape":…, "lines":…, "zone":…}` (gzip, only the keys the spot had).
- The Overlap Finder loads that file ONLY when the row is opened (KPCOverlap `hydrate()` in kpc-overlap-finder.js); the list and the map of other rows never touch it. Duplicate stretches still hide (shape_sig).
## How chat 2's save step uses it
`python3 .claude/build/storage/split_fers_shapes.py data/fers/US-AK.json [--gz] [--max-inline 20000]` after the line writes the area file (copy the script next to kpc_fers.py in KPC-Data, or call `split()` from it). It rewrites the area file slim and writes the shape files. `--check` re-joins a copy and proves it is identical (LOSSLESS) — run it in the line's test. Commit the `shapes/<region>/` folder with the area file.
## Size guard (for the line, not the script)
If the slim file is still over 50 MB gz, lower --max-inline (5,000 then 2,000). One file per shape = thousands of tiny files for Alaska: if the folder passes ~5,000 files, tell chat 3 and we pack them in per-region bundles (same loader contract).
## Tested (chat 3)
US-AZ (2.9 MB, 509 spots) split at 3 KB: 76 spots moved apart, slim file 0.7 MB, re-join LOSSLESS; Finder at 390 px: list loads with 0 shape requests, opening a row fetches only its shapes, the open row draws the same 29 outline pieces as the unsplit file, no errors, no sideways scroll. US-AK (the 3.2 MB old copy) also LOSSLESS. The real 135 MB Alaska bundle (pakhi@worker) is not available to chat 3: chat 2 please run `--check` on it.
## Where it lives (frozen)
Finder change = branch `stage-shapes` (kpc-overlap-finder.js v=20261029h: hydrate + lazy open), goes out with the mass dump. Until chat 2's files carry `heavy`, the Finder behaves exactly as before.

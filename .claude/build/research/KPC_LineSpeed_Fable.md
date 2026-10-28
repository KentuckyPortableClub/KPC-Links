# Speeding up the 2-fer assembly line (Fable, chat 2, Oct 28 2026 ~2:40 AM; HQ 2:18 AM + Brandon's 'balance the stations')
Study + plan only. NOTHING changed live (Kentucky's run was going). RULE for every change below: accepted only when Kentucky +
Ohio come out IDENTICAL to the slow line (same rows, same verdicts, same NOT SURE); built on a branch after the morning verdicts.

## 1. Where the time goes (measured)
**Wall time of the real runs** (GitHub step timings):
| run | fetcher: passes 1+2 | water copy | worker: passes 3+5 | checker |
|---|---|---|---|---|
| KY last night (40608978435, NHD mostly down) | 88.9 min | – | 107.1 min | ~2 min |
| KY tonight (40637781196, NHD up) | 23.0 min | 1.2 min | **173.9 min** (pass 3: 853 server requests, 88 parks downloaded fresh at fine detail; pass 5: 50 boundary lines + 60 rule-15 zones) | 0.5 min |
| OH last night (40619274002) | 1.5 min | – | 18.1 min | ~2 min |
| OH tonight (40640176578) | 0.8 min | 10.6 min | 4.1 min | ~2 min |
So the **worker (pass 3 + 5) is the slowest station for Kentucky by a wide margin**; the fetcher is second; the checker is minutes.
Ohio is fast because it has no water-route trails: Kentucky's cost is the Ohio River / Kentucky Lake water routes (Trail of Tears,
Lewis and Clark, Clarks River…) and its 273 official line pieces.

**Where the compute goes** (Kentucky run again here, OFFLINE from tonight's bundle = every server answer already on disk, so this is
pure compute; cProfile):
- **Pass 1: 7.4 min compute** (of the 23-min fetcher). `line_spots` 292 s = `sample()` 119 s (the trail line re-sampled every 10 m
  in a Python loop, 763,000 calls: the SAME line is re-sampled for every pair it is in) + `F.lines` 151 s (the other park's line
  drawn segment by segment: 7.2 MILLION one-point `px()` calls, 98 s of them) · `water_route_spots` 136 s = `np.nonzero(lab == L)`
  81 s (one call per water blob, 25,000 blobs).
- **Pass 2: 7.8 min compute**. `water_route_spots` 398 s = the same nonzero-per-blob loop 238 s + `F.area` of the NHD water 123 s
  (259,000 separate `fillPoly` calls, one ring at a time) · `line_spots` 46 s · everything else (distance transforms, outlines,
  JSON) under 20 s. Distance transforms (the real geometry) total **4 s**.
- So the fetcher's 23 min ≈ 15 min compute + ~8 min for its 855 server requests (NHD water tiles, PAD-US fresh outlines at the
  pass's detail, roads): about 0.5-1 s a request with the 2-s politeness gap where one host is asked twice running.
- **Pass 3 (worker): not profiled offline** (its answers are in the worker bundle, which was still being written). Its cell is
  5 m = 4× the pixels of pass 2, and the two hot loops above scale with pixels × blobs, so the estimate is **25-40 min of the same
  loops**, + 94 fresh PAD-US downloads at fine detail (bigger answers) + 391 server requests + pass 5's water re-check and
  boundary lines (the KY run's "spots given their boundary lines: 56, trail stretches given their true zone: 60" = the rule-15
  zones, each a fine raster). That adds up to the 107 min seen.
- Requests are repeated across passes by design: PAD-US outlines and NHD tiles are asked with each pass's own detail
  (`maxAllowableOffset` 0.0005 / 0.0002 / 0.00002), so the bundle cache (keyed by the full query) cannot serve pass 3 from pass 2.

**Verdict: the time is in Python per-segment / per-blob loops, not in the geometry and not mainly in the servers.**

## 2. The ideas, ranked (saving = Kentucky, the slow case; identical = can it be proven bit-for-bit)
| # | idea | expected saving | risk to 'identical' | rank |
|---|---|---|---|---|
| A1 | `water_route_spots`: get each water blob's box from `cv2.connectedComponentsWithStats` (one call) instead of `np.nonzero(lab == L)` per blob; build the route mask with one `np.isin(lab, accepted)` | pass 2: −4 min of 7.8; pass 3: −15-25 min | none: the same blobs, the same boxes, the same mask | **1** |
| A2 | `line_spots`: resample each line ONCE per pass (cache by line + step, numpy with the same arithmetic in the same order) and draw the other park's segments with ONE `px()` over all points (split indices) and one `polylines` call | pass 1: −4 min of 7.4; pass 3: −5-10 min | none when the floats are computed in the same order (checked by comparing the sampled points bit-for-bit) | **2** |
| A3 | `F.area`: draw all rings of ONE record in one `fillPoly` call (OpenCV fills multi-contour even-odd) instead of ring-by-ring XOR | pass 2: −1.5 min; pass 3: −5 min | small: OpenCV's multi-contour fill must equal the ring XOR on every frame (test on all KY + OH frames first; if any pixel differs, keep the XOR) | 5 |
| G | Reuse last run's rows for a pair whose INPUTS did not change: a fingerprint of both outlines (ids + acres + read date), the line pieces, the water tiles' dates, the rules version; unchanged → copy the rows, recompute nothing | nightly reruns: −60-80% of the worker; first runs: 0 | low: the fingerprint must cover every input (outline, lines, water, ownership answers, code version); a stale copy is the only failure, and 'identical' is exact by construction | **3** |
| D | **Balance the stations (Brandon):** keep one fetcher; split pass 3's PAIRS over 2-3 worker jobs (deterministic chunks of the sorted pair list; each job writes `US-KY.part-k.json`; a JOIN step merges in pair order, then runs the whole-state steps that today sit at the end of pass 3: n-fers, 'one row per line pair', dedupe, same-land rows, tidy); the checker waits for the join | worker wall: ÷2-3 on compute; requests run in parallel across jobs (each job keeps the 2-s gap per host, so USGS sees 2-3× the rate: cap at 3) | medium: the end-of-pass steps must move after the join and see every piece; pair ids / merge order must not depend on which job ran them (today `find_spots` walks `sorted(pairs)`, so a chunk per sorted range keeps order) | **4** (after A1/A2: the worker may already be short enough) |
| C | Same split INSIDE one job: `multiprocessing` over pairs on the runner's 4 cores | ÷2.5 on compute, no extra server load if the pool shares the politeness clock | medium: shared caches (NHD tiles, downloaded outlines, ownership) must be filled before the fork or returned by the workers; result order fixed by pair order | 6 |
| B | Fetch NHD water ONCE at the finest detail and let passes 1-2 use it (today each pass re-asks at its own detail) | −300 requests a KY run (~5 min) and 3× less load on USGS | medium: passes 1-2 are screens; finer water can change which spots survive the screen (it should only keep more), so it must be proven identical on KY + OH | 7 |
| E | Fewer, bigger requests: NHD tiles of 0.2° instead of 0.1° (same records come back), PAD-US ids in batches of 200 | −200 requests (~3 min) | low (the same features), but 504s on big NHD answers were the reason tiles went small: keep 0.1° for water | 8 |
| F | Box screens before any raster: a shared box narrower than a 50-yard spot (+pad) cannot hold one → drop the area pair at once | small (a few pairs; KY's 555 pairs all touch already) | none (true by construction) | 9 |
| I | Simplify outlines only for the 'could they touch' screen | small (pass 1 is already coarse: 20-m cells + box test) | none for screens | 10 |
| H | shapely 2 / STRtree / vectorised geometry instead of the raster | large in theory | **NOT identical**: a different engine rasterises and measures differently; allowed only for screens (F / I), never for the 50-yard / 100-ft decisions | rejected for decisions |

Also worth doing while there: the saved water copy (`bundle/water`, Oct 28) keys tiles by (i, j) only: a tile saved by pass 1 at
coarse detail would feed pass 3 when USGS is down. Key by detail too (or save the finest only) so the fallback equals the live read.

## 3. The plan (after the KY / OH verdicts, on a branch)
1. **Build A1 + A2 (+ A3 if it proves pixel-identical)** on branch `line-speed`. Prove: run passes 1-2 OFFLINE from tonight's KY
   and OH bundles with the old and the new code; compare `US-KY.json` / `US-OH.json`, `line-*.json`, `looked-*.json` field by field
   (every row, every status, every shape) — the harness is already in my scratch (the worktree + both bundles + 50 saved outlines).
   For pass 3 the proof needs the worker bundle (up tonight when KY finishes): same comparison.
   Expected: fetcher 23 → ~10 min, worker 107 → ~45-60 min for Kentucky, Ohio unchanged (already fast).
2. **Build G (reuse unchanged pairs)** with a fingerprint per pair and a 'code version' stamp; prove: a second run right after the
   first reproduces the first byte for byte and reports 'N pairs reused'. Expected: nightly reruns ÷3-5.
3. **Measure again**; if the Kentucky worker is still over ~40 min, build **D (2-3 worker jobs by pair chunk + a join step)**: the
   join step carries the end-of-pass steps; prove identical against the single-worker output of the same bundle. Only then C.
4. Merge; the nightly Kentucky + Ohio runs keep the identity test as a standing check (`kpc_fers_line_check.py` already compares
   the known answers; add a 'same as last run' row count so a speed change that drifts shows up red).

What NOT to do: change the cell sizes, the pads, the rasteriser, the distance transform, or the order of the passes — every one of
those changes answers.

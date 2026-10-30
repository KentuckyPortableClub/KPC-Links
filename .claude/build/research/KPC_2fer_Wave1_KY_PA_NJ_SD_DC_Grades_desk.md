# 2-fer grading: Wave 1 (chat 8, Oct 30 2026)
These 5 saved straight to the site before the waiting room existed, so they're already live and ungraded. Grading now per Brandon's Oct 30 instruction. Files: `US-KY.json` (425 rows), `US-PA.json` (636), `US-NJ.json` (155), `US-SD.json` (51), `US-DC.json` (2); verdicts `line-ky.json`, `line-pa.json`, `line-dcnj.json` (shared NJ+DC), `line-sd.json`; missing-check detail in `expected-ky.json` / `expected-pa.json` / `expected-dcnj.json` / `expected-sd.json`.

## All 5 — PASS
- All 5 verdicts say READY FOR CHAT 8, known_answers 19/19.
- **Checked first for the same-land duplicate bug found while grading ME/HI (32 other states, 643 extra rows): all 5 of these live states are clean, zero self-referential merge stubs.** This matches what I already told chat 2 (the live wave-1 states are not affected) -- re-confirmed here state by state rather than assumed.
- Live candidate counts match Brandon's table: KY 70 (he said "72" -- a 2-row gap, not alarming, likely counted at a slightly different moment; worth a recheck next time KY rebuilds), PA 45, NJ 24, SD 12, DC 1.
- Missing-check reasons: every DROPPED and NEVER LOOKED AT row in all 4 expected-*.json files (KY 221+116, PA 288+2097, DC+NJ 158+1358, SD 25+386) carries a real, specific geometric reason -- no blank/placeholder reasons anywhere. Spot-checked a sample from each state; reasons read like "no shared ground... not within 100 ft of a trail/river line" (DROPPED) and "the outlines' boxes do not touch" (NEVER), both sound.
- Sampled candidate rows (KY: 4 random of 70) look geometrically sensible -- area-kind rows carry acres, river/trail-kind rows don't carry acres (expected, they're linear not areal).
- **Field note, not a bug:** `tier` is null on every candidate row in every one of these 5 states, and `wide_m` is null on every trail-kind row in every state too (KY 15/15, PA 3/3; NJ/SD have no trail candidates to check). This is consistent across all 5 states and matches what I'd expect to see elsewhere too -- reads as a field the pipeline doesn't populate yet (or computes live on the site rather than storing), not a per-state defect. Flagging so chat 2 can confirm it's by design rather than a gap, but not holding anything on it.

## Bottom line
Wave 1 PASSES grading as released. No new holds beyond the already-flagged same-land merge-step bug (which doesn't touch these 5).

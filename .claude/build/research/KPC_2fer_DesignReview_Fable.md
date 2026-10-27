# 2-FER PROGRAM: ONE-TIME DESIGN REVIEW (Fable, chat 2, Tue Oct 27 ~10:45 AM, before the Ohio test)

Read: 2-fer rules 1-14 + every FINAL ruling (mapping.md), kpc_fers.py (1,842 lines as of fdfae09a) + kpc-fers.yml, chat 8's US+Canada and World pre-flights, the Kentucky re-check. No edits, no runs. The rules are settled; the two contradictions below are the only rule points raised.

## 1. Is the approach sound?
**Yes, for what it is asked to do.** The bot works on rasters: fill both outlines, keep the overlap, measure the distance to the nearest edge (distance transform), and keep a spot only where a circle of the required size fits. That IS the "circle across" rule (rule 4), it handles holes (inholdings) by even-odd fill, and it is cheap: the Kentucky three-pass run takes about 1.5 h. The funnel (pass 1 saved outlines → pass 2 fresh → pass 3 finest) is the right shape for scale: the coarse pass throws away ~90% of pairs with a box test and nothing expensive runs until a pair survives. Owned-land masks (Forest Service, BLM, Park Service, Corps, FWS, state) are applied as a second raster AND-ed onto the park, which is the simplest correct way to do rule 1b. Corridors as areas and lines as 100-ft zones are both in. Water-only and n-fers are in (but n-fers stop at 4, see #6).

**Where it is NOT yet sound at US + Canada scale:**
- **Time budget (real risk of a red run = an email).** `pass: all` runs passes 1, 2, 3 back to back, each with the full MINUTES (320) budget, inside a 335-minute step. Kentucky fit because it is small. For the US the old pass 3 alone handled ~6,000 candidate spots; each now costs an ownership-map tile, a PAD-US point query, an NHD water query and an access-pin query. Three passes cannot fit in one 335-minute job; the step would be killed mid-pass-3 (red). The resume logic ("waiting for pass N") already exists, so the fix is splitting the budget, not new code.
- **Memory.** Every ownership parcel and water polygon fetched at pass-3 detail is kept in process caches (`FSO`, `OWN_T`, `NHDC`) for the whole run. Across the whole country that can pass the runner's memory. Needs eviction (keep the tiles around the current box).
- **Accuracy at the 25-yard floor.** Pass 1 runs at 20-m cells and needs `dist ≥ 11.4 m + 10 m`, i.e. an overlap about 43 m wide, to keep a spot. So most VERY TIGHT spots (23-46 m) die in pass 1 and never reach pass 3, where the tier is decided. The tier Brandon added on Oct 27 is therefore mostly empty by construction. Pass 1-2 should only screen (keep anything one cell wide); pass 3 decides.

## 2. What would still produce WRONG 2-fers (ranked by how likely)
1. **Two designations stacked over private land.** `ownership_step` reads PAD-US at the spot centre; when it finds NO fee record (only designation / overlay records, or nothing) and neither park has an owned-land mask, both owners read as '' and the pair is called "layered" = candidate. A wild-river corridor over a scenic-area designation over a farm would pass. Rule 2 says the spot must be public land; with no fee owner at the spot the honest status is NOT SURE.
2. **Ownership sampled at ONE point.** The spot centre may sit on the right owner while most of the patch is on another. Sample several points of the patch (or rasterize the fee records like the masks) and require one owner across the patch.
3. **A wrong outline from the answer key.** Only the 39 LOW-confidence outlines are kept out; MEDIUM (1,046) can still be the wrong land (name joins, pin far outside). Not fixable in the bot; it is what chat 8's spot-check and the observations log are for. Keep the 'reviewed' joins growing.
4. **Approximate trail lines.** National historic trail lines are ~1:100,000: the 100-ft zone can sit 100 m from the real path. Allowed by Brandon's ruling (grey 6) with the 'approximate' note; it is still the most likely public "that's not a real spot" complaint. Keep the note on every such row and never place the access pin on them without saying "approximate".
5. **Two state agencies side by side read as one owner** (state park beside a state WMA with a map-edge overlap): both are 'STATE', so the ownership step says layered. Mostly harmless (same landlord), but it is exactly the Cumberland-Falls-style edge mismatch inside one government. Use the manager (Mang_Name / agency) as a second key when both owners are STATE.
6. **Water that is not NHD.** Canada and the world have no water source: lake and sea patches come out as land spots. Pre-flight items already say so; nothing ships for Canada until a water layer is in.
7. **Same land, two park numbers.** Kentucky shows them (Brandon's ruling); the US/Canada code still files them in same-outline.json and skips the pair. Not wrong, but inconsistent (see contradiction B).
8. **Pass-3 "agree" by box overlap within ~50 m** can match a pass-3 spot to a different nearby patch of the same pair. Low impact (same pair, near place).

## 3. Simplest design that fixes the pre-flight items
Keep the raster funnel. Make these the only changes (all small except #9-10):

| # | Change (what) | Why | Effort |
|---|---|---|---|
| 1 | **Split the time budget**: `pass: all` gives each pass MINUTES/3 (or run passes as three dispatches queued one after another, which the concurrency group already serialises); pass 3 also takes `STATES` batches | the only thing that can turn the big run red (email) | S |
| 2 | **"No public owner at the spot" = NOT SURE**: in `ownership_step`, if PAD-US (CPCAD) returns no fee record at the spot and no park has an owned-land mask, return not sure, not "layered" | closes the private-land gap (section 2, #1); matches rule 2 + 7 | S |
| 3 | **Sample the patch, not one point**: ask PAD-US at up to 5 points spread over the patch (centre + 4 farthest inside pixels); one owner across all = ok; mixed = not sure | section 2, #2 | S |
| 4 | **Mask empties the overlap = NOT SURE, not silence**: when an owned-land mask removes the whole overlap of a pair that touched in pass 1, write a row 'not sure: not shown as agency-owned on the ownership map (Basic Ownership 2015); PAD-US cross-check' instead of dropping it with no row | the 6:49 FINAL says "not shown as Forest Service = NOT SURE, never no"; today the pair just vanishes (contradiction A) | S |
| 5 | **Pass 1-2 screen, pass 3 decides**: pass 1-2 core threshold = one cell (anything that could hold a 25-yd circle at finer detail), pass 3 keeps the exact 25/50/100-yd tiers | the very-tight tier is unreachable today | S |
| 6 | **n-fers to 9** (`for n in range(3, 10)`), same "same patch" test; stop a level when it adds nothing | HQ hand-off (6:31 AM) and rule 11 | S |
| 7 | **Same-land rows for US + Canada**, shown and labelled, like Kentucky | HQ 8:10 ruling; contradiction B | S |
| 8 | **Cache eviction**: keep only ownership / water tiles touching the current box; drop the rest after each pair | memory at national scale | S |
| 9 | **Canada water + roads from official services**: NRCan's hydrography (National Hydrographic Network) and a road network (Statistics Canada / provincial) found by the portal scout first; until then Canada rows get access_pin 'none (no road source yet)' and water-only is NOT decided (status 'not sure: water not checked') | pre-flight item 6; never guess | M (a probe first) |
| 10 | **Test order gets one WESTERN state**: Ohio → Michigan → Utah (or Nevada) → all | Ohio and Michigan never touch a BLM planning area, so the BLM surface-management mask (field name guessed, unverified) and the herd-area join would be tested for the first time on the whole-country run | S (plan only) |

Already right and worth keeping: owned-land masks by agency kind; W&S corridors joined as areas; LOW-confidence outlines kept out; NHD in 0.1° tiles; closures note on every row; line parks with no line listed as such; retired refs out; 'checked' + 'map_dates' on every row; the observations log.

## 4. Rules that contradict themselves
- **A. "Not shown as Forest Service-owned = NOT SURE, never no" (FINAL 6:49 AM) vs the owned-land mask + "Sunny Brook and Hoskins decided by Basic Ownership" (6:32 AM).** The mask makes a pair with no Forest Service-owned patch simply disappear (no row), and the 7:00 AM owner test called Sunny Brook / Sinking Creek "DROP". Reconcile: the mask decides the SHAPE, but a pair that touched and has no owned patch is a NOT SURE row with the 2015-map caveat (change #4). Pairs Brandon ruled by name (KY_DROP) stay dropped.
- **B. "Two park numbers on one outline = an answer-key mistake, never a 2-fer" (bot header, rule text, same-outline.json 'never a spot', world pre-flight item 11) vs "Same land, two park numbers: NOT hidden, shown in the normal list" (HQ 8:10 AM, Kentucky).** Pick one for the whole program; the Kentucky ruling is the later one, so the simplest fix is #7 and a one-line edit to the rule text.
- **C. Cosmetic:** CLAUDE.md summarises "the 8 rules … rules 9-13"; mapping.md has 14 (rule 14 = the ownership step). Update the summary so a new chat does not miss rule 14.
- Checked and NOT contradictory: PF-1 (Park Service = owned land) with PF-5 (parkways = area parks): both apply, a parkway is an area masked to NPS-owned land. B-G2 (private land with its own number counts for that number only) with the 7 KDFWR-managed WMAs: those are Forest Service-owned, so they layer. Rule 6 (pins never count) with the rows' `pins_inside`: information only.

## 5. Top-10 ranked changes (what / why / effort)
1. Split the pass-'all' time budget (S): avoids a red run on the big job.
2. No fee owner at the spot = NOT SURE (S): the one remaining way a private-land 2-fer gets through.
3. Sample the patch at several points for ownership (S): one point is not a patch.
4. Mask empties the overlap = a NOT SURE row (S): resolves contradiction A.
5. Pass 1-2 screen only; pass 3 decides the tiers (S): makes the 25-50-yd tier real.
6. n-fers to 9 (S): HQ hand-off.
7. Same-land rows shown for US + Canada (S): resolves contradiction B.
8. Evict cached tiles outside the current box (S): memory at scale.
9. Canada water + roads from official services, else 'not checked' (M, probe first): no guessing in Canada.
10. Add Utah (or Nevada) to the test order (plan only): the BLM mask gets tested before the whole-country run.

Everything else in the pre-flight (hand 'reviewed' joins for the 39 LOW parks, California access pins, closures feeds) is data work, not design, and can follow the Ohio run.

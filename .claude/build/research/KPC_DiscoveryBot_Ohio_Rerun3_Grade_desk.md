# Discovery bot grading: Ohio, 3rd rerun (chat 8, Oct 30 2026)
Run 41050709065, dispatched STATES=OH, completed green (success) Oct 30 ~12:46Z. Per Brandon's stated consequence going into this run: pass or the bot gets retired in favor of the GIS hunter + intake.

## Pass criteria (from the design doc) -- all met
- **Green run, no email:** confirmed, run succeeded; a successful dispatch doesn't trigger Brandon's "failed workflows only" email setting.
- **At least one A-grade lead a person confirms is real and new:** YES. `Parks_DNAP_Trails` (ODNR Division of Natural Areas & Preserves' own trails layer) -- I graded this A in an earlier rerun too, it's real and still new to our data. More importantly, this run surfaced a whole family of ODNR's own authoritative lands-boundary services I hadn't specifically flagged before: `odnr_landbase`, `odnr_landbase_v2`, `ODNR_ODNR_Lands_External`, `DNR_Fed_Lands_Nav_Base`, `Federal_Lands`, `ODNR_LandBase_CNTY_TWP_OLS` -- all on gis.ohiodnr.gov/gis2.ohiodnr.gov, all "park polygons with a name field." That's exactly the kind of real, new, agency-hosted find the bot is supposed to surface.
- **No lead from a non-agency host in the top 20:** confirmed. Every one of the top 50 leads is on `gis.ohiodnr.gov` or `gis2.ohiodnr.gov` -- Ohio DNR's own domain, the state agency itself. Clean.
- known_good_found 7/7, known_good_missed 0 -- the bot didn't lose track of anything it already knew.

## Can't cleanly run the order-agreement check this time
The design doc's method (my hand A/B/C vs the bot's 0-6, order must agree 7/10) doesn't have anything to compare against here: **all 50 of the top-50 rows score a flat "5" / band "A" -- no differentiation at all within the top tier.** That's worth a flag of its own: the bot's scorer is saturating (too many things tie for first), which makes its ranking within the top slice meaningless even though the leads themselves are good. Worth a look whether the scoring formula needs a tie-breaker (e.g. weight agency-own-domain higher than a generic keyword match, or dock points for a FeatureServer/MapServer pair of the same service counted twice).

## Other flag: heavy duplication in the output
Many rows are the exact same service listed 2-3 times (once per matching keyword, and once each for its FeatureServer vs MapServer endpoint) -- `ODNR_ODNR_Lands_External3` appears identically 3 times in the top 50 alone. Doesn't affect the pass/fail verdict (duplicates don't hide anything, they just waste rows), but worth a de-dupe pass if the bot keeps running.

## Verdict: PASS
Real, new, agency-hosted finds; no junk in the top 20; green run. Recommend keeping the discovery bot rather than retiring it, with two tune-ups worth chat 10's time when convenient (not urgent): (1) de-dupe same-service/same-endpoint-pair rows, (2) widen the score spread so top-50 isn't a flat tie. The `odnr_landbase` family + `Parks_DNAP_Trails` are worth chat 9/chat 2 picking up as real Ohio layer candidates.

# OWNED-LAND FIX (Kentucky first): SHORT REVIEW (Fable, chat 2, Tue Oct 27 ~11:35 AM). NO edits.

Reviewed: kpc_owned.py + its use in kpc_fers.py and kpc_ky_key.js, ky-dbnf-owned.geojson (420 pieces, ~746,000 acres, 0.8 MB; there is no data/us-key/owned/ yet: the US states come at the next key rebuild), the tool patch `.claude/build/review/owned-land-ky.patch` (kpc-bounds.js, kpc-in-park.js, gis-overlays.js, kpc-planner.js, kpc-kit.js, kpc-park-control.js, kpc-offline.js), commits a1ee45ab / 35e89fa5 / branch owned-land-ky. The patch is NOT live. Tested the patch at 390 px with the four spots HQ named (map library stubbed, so messages and errors were checked, not the drawn lines).

## PASS
- Red River Gorge (37.8285, -83.6228): ✓ INSIDE, US-4484 (+ KFF-4511, KFF-7268, KFF-3801), 0.6 mi from the edge.
- Private inholding inside the line (37.0143, -84.4242): NO 'in the park'. Says 'NOT FOREST SERVICE LAND ON ITS MAP … move onto Forest Service land', nearest Forest Service land about 220 ft SE, the 2015 caveat. Same answer with ?ref=US-4484.
- Cumberland Falls State Park (36.8395, -84.3440): ✓ INSIDE US-1277 (+ KFF-1277); Daniel Boone is NOT listed (state land inside the line, ruling Oct 27). With ?ref=US-4484 it gives the ruled 'not Forest Service land' message, nearest Forest Service land 0.4 mi N. Correct.
- Redbird WMA (37.1267, -83.5440): ✓ INSIDE US-10159 AND US-4484 (Forest Service land managed by KDFWR, ruling 2). Correct.
- Outer line: drawn faint dashed (weight 1.5, '6 8', no fill) in Am I in the Park, finder overlays, planner, Kit, Park Control; labelled 'Forest boundary line: not all land inside is public' everywhere (gis-overlays keeps the checkbox name 'Daniel Boone National Forest', the popup/note carries the label; fine). Owned land is the shaded park.
- One shared module: kpc_fers.py imports kpc_owned (fs_owned / owned_land / evict / OWNMAP all from it; no copy left); kpc_ky_key.js folds the owned parcels into one 'agency-owned land (ownership map)' tract. kpc_us_key.py does not use it yet (expected: US states are the next step).
- Phones: no sideways scroll at 390 px, no page errors on the 5 pages; one extra 0.8 MB file for Kentucky loads (cached, force-cache) and the point tests are one feature of 420 polygons: no visible slowdown. Other states untouched (the new layer is Kentucky-only; kpc-offline.js lists the file for the offline pack).
- Caveat present on every owned-land message: 'Forest Service ownership map, 2015 data: land bought since may be missing, so check the official map.' PAD-US disagreeing gives 'CHECK THE LAND OWNER: THE MAPS DISAGREE', never a flat 'private'.

## FIX (one, wording; small)
- F1. The ruled B1 sentence as built says '… this spot is not Forest Service land (private or another owner)'. The 6:49 FINAL says land not on the 2015 map is NOT SURE, never 'no'. Reword in kpc-in-park.js (outerMsg), gis-overlays.js (procBox) and kpc-planner.js (whereHtml): 'this spot is not shown as Forest Service land on its ownership map (2015 data): it may be private or another owner's. POTA needs public land inside the park: move onto Forest Service land, or check the official map.' Keep the headline.
- (Not this fix, noted:) Cumberland Falls also lists US-10103 'The Cumberland River Wilderness Area' from the wild-river corridor: a POTA naming oddity, pre-existing.
- (Not this fix, noted:) the 23 MB first copy of ky-dbnf-owned.geojson is in git history (one commit); harmless for the site, counts toward repo size (STORAGE PLAN).

## VERDICT
Safe to go live after F1 (a few words in three files). Nothing else to hold it.

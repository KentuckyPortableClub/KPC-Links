Verdict on "v2-keys\2026-11-27-080935": NO (don't publish or merge "#393" yet).

The build itself is solid — 51/51 US areas built (0 Canada in this zip), 9,962/13,321 outlined, 0 shared records, 0 same-named-other-park, 0 missing records, cold = warm, and all 251 trail joins are under 100 ft (max 98 ft, all still private until trail licences are read). But real wrong land slipped past every gate:

1. Fake "two sources" bug (causes NV H1 + 79 parks across US): "other_services()" treats two layers as independent whenever the service URL is blank, so two identical copies of the same record prove a park up to 6.2 mi away with the pin outside (28 of 79 parks have pins outside, including 20 NV BLM herd areas).
2. Confirmed wrong land (3) + partial-land drops (11):
   - HI "US-6423" Manuka State Preserve (26,044 ac) took the 14-ac Manuka State Wayside (wrong park).
   - UT "US-11094" Glenwood State Fish Hatchery took a 1,043-ac BLM "Glenwood" area.
   - AL "US-10428" Walls of Jericho (12,617 ac in AL) took Tennessee's 753-ac natural area (pin outside).
   - 11 other parks shrank to a tiny piece (e.g., TN Chuck Swan 24,353 → 755 ac; RI Buck Hill 2,034 → 60 ac; CT Campbell Falls 152 → 2 ac from MA).
3. H2 states split cleanly into measuring vs. real land:
   - IL (7/68), NJ (23/39), VA (30/51), PA: measuring bugs, not wrong land (IL "sgild" 1.67× flat-map stretch; NJ 1.89× / VA 1.25× / PA 1.19× from summing overlapping PAD-US polygons).
   - MI (52/146): real extra land — "mid" draws boundaries >1.5× v1 on 41 of 93 parks (Three Rivers 2,137 → 7,588 ac; Brownstown Prairie 53 → 757 ac; Leidy Lake 110 → 1,330 ac) — looks like project boundaries instead of owned land.
   - TX (51/76): refuges lost units (Aransas 116,097 → 90,383 ac), though v2 fixed v1's lake-sized errors on Caddo/Cooper Lake SP.
4. ID-join leaks ("v2-id-other-names.csv"): "NPS Easement" records joined to battlefields up to 15 mi away (Fredericksburg-Spotsylvania, Petersburg, Manassas, Prince William, Cumberland Gap), plus suspicious NY joins (Lake George WF → Hudson River SMA 21–25.5 mi away; Pigeon Lake → Twitchell Lake 5.6 mi; Raquette Boreal → White Hill 7.8 mi; Mount Loretto → Butler Manor Woods).
5. G1 & pin-only hygiene: All 5 G1 diffs are normal POTA list changes (no real drops), but the 11 new parks have blank names in park facts. And ~100 of 135 store-gap parks are mislabelled "no_record_with_this_name".
   - True pin-only totals (3,359 rows / 3,250 parks): "no_record_with_this_name" 2,496 · "name_but_no_pin_or_size_proof" 666 · "water_only" 80 · "record_shared_with_another_park" 70 · "record_layer_not_in_store" 46 · "office_only" 1 · "park_has_no_pin" 0 · "two_records_fit" 0.

Paste-Ready Message for the Builder

GRADE: v2-keys\2026-11-27-080935 — build integrity YES, publish/merge NO.
Hard gates are clean in all 51 US areas (0 shared, 0 same-name-other-park, 0 missing records, cold = warm, all 251 trails <=98 ft). Real wrong land slipped past the gates:

1. name+two_sources counts copies as independent: other_services() returns True when svc is blank. 79 parks are proven only by identical-acre copies (hma/sgnvi, cow/sgcoa, rst/sgakg/sgnmc...), 28 with pins outside (causes NV H1). Fix: require distinct non-blank services and reject identical acres/IDs.
2. Confirmed wrong land (pin outside + different/smaller record): fix US-6423 Manuka (took 14-ac Wayside), US-11094 Glenwood Hatchery (took 1,043-ac BLM 'Glenwood'), US-10428 Walls of Jericho AL (took TN land). Review partial-land drops: US-3935, 7714, 1655, 8335, 2282, 5735, 9317, 12191, 4271, 9832, 6992.
3. Key acres measuring bug (kpc_us_key_v2.py ~1627): IL sgild is flat-map inflated (1.67x) and PAD-US overlaps are summed in NJ (1.89x), VA (1.25x), PA (1.19x). Use measured union outline (or drop acres fields disagreeing with drawn outline by >10%).
4. MI 'mid' layer is real extra land (>1.5x v1 on 41 of 93 parks; Three Rivers 2,137 -> 7,588 ac, Brownstown Prairie 53 -> 757 ac): verify owned land vs project boundary.
5. ID joins: exclude 'NPS Easement' records (Fredericksburg-Spotsylvania, Petersburg up to 15 mi away, Manassas, Prince William, Cumberland Gap); review Lake George WF -> Hudson River SMA (21-25.5 mi), Pigeon Lake -> Twitchell Lake (5.6 mi), Raquette Boreal -> White Hill (7.8 mi), Mount Loretto -> Butler Manor Woods; AT 384 records up to 487 mi away.
6. Refresh park facts for 11 new parks with blank names (US-13665-72, US-6253/6257/6274). Kure Atoll US-0121 moved to US-KI.
7. Pin-only reasons: ~100 of 135 store-gap parks (sgidb 54, wld 21, arw 10, mszw 9, sgnca 8, sgwyd 6) are labelled no_record_with_this_name — give them a store-gap reason.
8. TX/AL unit drops: check Aransas (-26k ac) and Little River SF (took only its 'Addition').
9. Canada had 0 areas in this zip — include Canada in the next test run.

Rerun after fixes and send the zip; I'll regrade.
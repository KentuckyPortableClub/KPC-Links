# Fable review, 26 Nov 2026 (read-only; pasted by Brandon 2:49 PM)


# Review, 26 Nov: the merged code puts the wrong forest on 16 Minnesota parks

The 26a test key gives 16 MN state forests a second record that belongs to another forest. Everything else I found is smaller. I ran no build and wrote nothing to the PC or GitHub.

## Findings

**1. Sixteen MN forests carry another forest's record. Sure of the rows; likely of the cause.**
- **What:** each row has the park's own name but another forest's id and acres. That id is confirmed on the other forest by its own agency id.

  | Park | Row id | Whose land it is |
  |---|---|---|
  | US-4815 Northwest Angle | sgmnb6 | Big Fork (127,933 ac) |
  | US-4797 Foot Hills | sgmnb7 | Birch Lakes |
  | US-4799 George Washington | sgmnb12 | Chengwatana |
  | US-4785 Birch Lakes | sgmnb15 | D.A.R. |
  | US-4791 Cloquet Valley | sgmnb17 | Finland (311,801 ac) |
  | US-4788 Buena Vista | sgmnb20 | looks like General C.C. Andrews (7,771 ac) |
  | US-4813 Mississippi Headwaters | sgmnb22 | Golden Anniversary |
  | US-4811 Lost River | sgmnb23 | Grand Portage |
  | US-4780 Badoura | sgmnb29 | Lake Isabella |
  | US-4807 Koochiching | sgmnb34 | Mississippi Headwaters |
  | US-4827 Smokey Bear | sgmnb38 | Paul Bunyan |
  | US-4789 Burntside | sgmnb47 | Smokey Bear |
  | US-4816 Pat Bayle | sgmnb52 | Wealthwood |
  | US-4782 Bear Island | sgmnb55 | Whiteface River |
  | US-4821 Remer | sgmnb57 | Lost River |
  | US-4806 Kabetogama | sgmnb59 | Waukenabo |

- **Likely cause:** since #383 the id file seems to hold one forest under two ids, its agency number and an old row number. The row number can equal another forest's agency number.
- **Where:**
  - `kpc_us_key.py:2787` takes the candidate from the index but checks only that the id exists.
  - `kpc_same_land.py:571-573` then picks between the two copies by ground share, then id text.
  - `kpc_same_land.py:540-544` keeps views by id, so a second record under one id reads as the first.
- **Why the gate missed it:** the "record carries another name" check runs only for parks proven by name (`kpc_us_key.py:2633`). It caught the same mistake on US-4792 Crow Wing, but these 16 are confirmed by id.
- **Side effects:** US-4792 Crow Wing and US-4798 General C.C. Andrews lost their own forest record.
- **What to do:** the builder opens the PC's id file and confirms the two ids for one forest. The fix moves the US rules hash, so it goes as a draft PR under section 13. A good test is "no id on two parks under two names".
- **Not checked:** whether this is new since #383. I did not have the earlier test folder.

**2. Shared ground, twin rule, count once: no false yes seen. Likely fine.**
- In 328 proven rows of the proof list, no old and fresh pair has different names. That list covers only parks that lost a row.
- Weak spot: shared ground has no name check (`kpc_same_land.py:519`). It matters only if the true twin is missing from the fresh file.
- "Count once" compares boxes, not ground (`kpc_us_key.py:2568`). A small separate piece inside a big piece's box is skipped. Low risk.

**3. The thin rule is wider than its name. Sure.**
- `mean_width_m` (`kpc_same_land.py:442`) marks every square parcel under 40 acres as thin, not only strips.
- For those, "different ground" can no longer say no (`:516`). My test: two different 30-acre parcels side by side, same name and size, were "different ground" before batch 17 and are "name + size" now.
- No real wrong case found. One to look at: US-10083 Lake George Wild Forest, 8 rough rows proven by name and size.
- It can hide a park when a thin record's fresh twin has another name or size. None seen in MN or NY.
- What to do: add a length test so only long strips count. That is a rule change.

**4. The 60 MN rows: about 24 are harmless repeats.** These are the old forest rows whose land is still drawn under the new id. The five most likely good records:
- **US-0673 Saint Croix:** `wsrc9` (70,577 ac) left because the `wsrc` layer is not in the store. Run LAYER-RECORDS for it. Sure.
- **US-0356 Big Stone:** 23 Fish and Wildlife tracts. The district rule (`kpc_us_key.py:3825`) runs only for a park with no rows, and this one came in with 23 old rows. Likely.
- **US-4798 and US-4792:** fixed by finding 1.
- **US-2506 and US-7148 Lake Vermilion / Soudan:** one record, two park numbers, one shared DNR id. No existing rule covers it, so it needs a rule sheet.
- **US-12389 Devils Track Falls:** six 40-acre parcels dropped. Likely the apostrophe in "DEVIL'S"; I did not test it. The same 240 acres stays drawn from other layers.

**5. The 8 NY parks: name + size is not too strict for five of them. Sure of the sizes.**
- For Lock 32, Schunnemunk, Reinstein Woods, Ludlow Creek and Charles Flood, two official layers agree on size within about 1%. Only the name test stops them.
- The existing proof that should carry them is the park's own page. In the park facts, 564 dec.ny.gov pages say "robots-unreadable" and 196 parks.ny.gov pages say "crawl-delay", so they were not read.
- What to do: get those pages read, and check that "robots-unreadable" follows your robots rule.
- Cheap check: see whether NY State Parks' `MasterAreaID` equals the park number in the link (113 Artpark, 184 Schunnemunk). If so, the id rule proves them. Can't tell from here.
- **US-2006 Artpark:** right as a pin. The sizes disagree (203, 162, 170).
- **US-0681 Upper Delaware and US-8319 Palisades:** right as pins for now. Their land sits in the next state's file. Run GET-CROSS-STATE.

**6. Minnesota page facts are blank. Sure.** 246 MN parks share five page addresses (58 forests all show `sft00033`). The link ids are right, but the page proofs have nothing to read. The key's evidence block also reads old row numbers as new ids (`kpc_match_checks.py:482`, `:900`), so about 45 forests show another forest's id and a pin miles off. It is report-only, but fix it before anyone grades from it.

**7. #384 speed: same answers. Likely.** I compared old and new code on 2,100 made-up outline pairs, including many-ring shapes and points on box edges. None differed. Read by hand, the box filing and the kept grid points are exact.

**8. KPC-Store #38: two gaps. Sure.**
- A hand file's own record count is taken as the layer's count (`kpc_layer_records.py:375`), so a short hand download still says complete. Check it against the server's count or the keeper's last count.
- A hand-file alias matches on area and label only (`:320-323`). The area must match, so no wrong-area risk. The file is not tied to the layer's address, and hand files skip the "older address" check (`:400`, `:609`). Add the address as a column.
- The key side checks "complete" the same way in all three places it trusts it.

**9. #386: fine to merge.** Tools only, no rule file.

## Leads

The 194 leads are 194 rows, which is 73 parks. 34 already have an outline on the website key.

**How to prove one:**
1. Get the whole layer into the store.
2. Let the key join by its normal rules. Never use the engine's record id.
3. Prove it by agency id from the park's link, name plus official size, or two sources.
4. Outside MN and NY, check with the grade tools, not a build.

**Ten to check first:**
1. CA-4864 Fort Henry
2. CA-4866 Fort Mississauga
3. CA-4900 Cartier-Brébeuf (sizes disagree, a good test)
4. US-1080 DeGray Lake Resort
5. US-11955 Genoa Fish Hatchery
6. US-7893 Augusta Canal
7. CA-3408 Denetiah Corridor
8. CA-0831 Inuujarvik (the hand file is already there)
9. US-4424 Ouachita NF in Oklahoma (the lead is the whole forest line; the rule draws Forest Service-owned land only)
10. US-0655 National Mall (expected to fail: the lead matched "MALL")

## Notes
- I made no fix PR. Finding 1 needs the PC's id file to confirm, and the fix moves the rules hash.
- `handoff-matching-nov26.md` is not on main yet. I read it from PR #385.
- I read `CLAUDE.md`, the rule sheet and the handoff. I did not open `RULES-NOW.md` or `key-quality.md` sections 9 and 13.
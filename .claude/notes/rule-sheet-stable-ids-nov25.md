# RULE SHEET: when is a record "the same record"? (Opus, 25 Nov 2026 5:15 AM; grey areas G1-G4 RULED by the owner 5:02 AM: 'i guess' to 'yes to all', so each suggestion in brackets below is the rule)

Why: the map server's row number (OBJECTID) is NOT an id. Servers hand out new row numbers when an agency republishes a layer.
Proof (25 Nov): the store asked Minnesota's server for row 210 (Nov 14) and got Lost Valley Prairie (agency code SNA01041);
our Nov 12 copy has it as row 55. 3,161 of 3,163 re-found MN records have the key's own name. Land, names and agency ids did
not change; only row numbers did. Today we still join, save answers and compare on row numbers, so every republish looks like
"renumbering", "lost records" or "carried parks", and can put one record's facts on another (B1).

## 1. What counts as the same record (best first)
1. The agency's own id field is the same (e.g. MN's natural-areas layer has `pgrm_project` = SNA01041, the same code POTA's own link uses; not checked yet for other layers). One field per layer, listed in a table (`data/us-key/stable-ids.json`), found by a bot, checked by a person.
2. No such field: the same name (any of the record's names, `KR.rec_names`) AND size within 10% (20 acres slack) AND boxes that overlap. This is D1's `saved_row_ok` plus the box test.
3. Inside ONE read, the row number is fine as a handle. Between two reads (key vs store, key vs saved answer, key vs website, keeper old vs new), never alone.

## 2. What does not count
- The same row number in two reads. The same name alone (two "Mud Lake" WMAs). The same size alone.
- A store `key_record_id` alone (it is the store's guess at the time of its build): it is used only with test 1 or 2.

## 3. Sources, best first
The layer's own id field (read from the saved copy's attributes) > name + size + box > nothing.

## 4. When unsure
Not the same record. The fields are not copied, the saved answer is not applied, and the park keeps what it had (never loses an outline because of this test). Counted on the report line ("N refused: another record", as #379 does).

## 5. What people see
Nothing new on the map. The report says per state: "same record by agency id N, by name + size N, refused N". Saved answers that point at a row number that now holds another record show as "saved answer needs a look" in the review list, never silently re-pointed.

## 6. Real examples
- MN US-4793 D.A.R. State Forest: our row sgmnb20 = D.A.R., store row @20 = another forest -> by agency id SFT00015 the store's D.A.R. record is found (it is row @something else) -> right id. (Done by #379 with name + size.)
- MN US-10722 Lost Valley Prairie: our row 55, server row 210 (Nov 14): same SNA01041 -> same record.
- MN sgmne: 3,080 pieces re-found twice (Nov 14 and Nov 21): every republish renumbers; with the agency id the key would not notice at all.
- MN sgmnc@97 St. Croix Savanna: a 14-acre piece of a 140-acre record: size test fails, agency id would pass (G2).
- NY sgnya: 1,509 store id fields; NY's row numbers DID move (the reviewer's re-grade, 25 Nov; first written wrongly as 'did not move'); no NY result changed.
- A saved answer (overrides `join: ["sgmnb20"]`) made before a republish: after it, row 20 is another forest -> today D1 refuses it by name + size; with the table, it is re-pointed to the record with the same agency id (G3).
- PAD-US (national): its own `OBJECTID` changes between releases (4.0 -> 4.1) and between the GDB download and the web service: test 2 only.

## GREY AREAS (RULED 25 Nov 5:02 AM: the bracketed suggestion is the rule)
- G1. Who fills the id-field table? [A bot proposes the field per layer (a field that is unique, never empty and code-like in the saved copy); an agent checks 10 records per layer against the agency's own page; only then it is used.]
- G2. Split / merged records (pieces): same agency id, different sizes. [Same record when the agency id matches, whatever the size; with no id field, pieces are matched to the whole only by name + box, and the size test is skipped for pieces.]
- G3. Saved answers that name a row number: re-point them automatically when the agency id proves which record it is now? [Yes, and list each re-point in the review list; with no id field, refuse as today.]
- G4. Order of work. [1) the id-field table for the 20 layers with the most re-found records; 2) key vs store (B1, extends #379); 3) saved answers; 4) keeper old vs new; 5) the website-vs-test comparison line.]

Not in scope: changing what a park is joined to (this sheet only decides "same record"), Canada and world (they do not use store id fields today).

## TIGHTENINGS from the other builder's re-grade (25 Nov ~6 AM; part of the sheet, the owner sees them with the PR)
T1. What happens TODAY: D1 already moves a person's saved join to the same-name, same-size record near the pin ("join moved 46" in MN). G3 adds agency-id re-pointing on top of that; it is not new behaviour.
T2. Saved answers with NO fingerprint (72 join rows in 57 parks, 301 NO rows, list in the re-grade zip) are trusted by row number alone. Fix: give each the name and size from the read it was made on, or list it as "saved answer needs a look". Never trusted by number alone after a republish.
T3. G1's field test is "unique per record GROUP" (pieces of one unit share a code), not "unique per record". Ids are compared after normalising ("SNA01041" = "SNA 01041"; 1041 = "1041.0"). The field must be in kpc_store_attrs' wanted list, or the store copy drops it.
T4. G2: the same agency id is the same record only when the boxes overlap too. A size change over 2x is reported ("same id, size changed"). A piece is matched to a whole by name + box only when its box is inside the whole's box, it is smaller, and the pieces add up to no more than the whole (+ slack).
T5. No acres on either side: name + box, never name alone (today saved_row_ok skips the size test when an acres value is 0).
T6. Generic names never count as "the same name": "Unit 1", "Tract 3", "Wildlife Management Area", a name of only kind words. A short stop list.
T7. G3 re-pointing limits: a dry-run count on the report first; a join re-points only if the name also matches, else "needs a look"; NO rows follow their land the same way; a per-state cap stops the run if passed.
T8. Process: data/us-key/stable-ids.json is data: each batch needs the owner's OK (or goes through the waiting room). Canada's saved answers and hard-look ids are row numbers too: on the list for later. The keeper's old-vs-new step is KPC-Store work.

## FIRST REAL CASE: Illinois (25 Nov)
The key's Illinois conservation layer (sgilc, 6,908 records, numbers up to 9,197, read 11 Nov) now answers "Invalid URL". The owner's hand download of the same compiler's newer list (2,171 records, numbered 1-2,171) has the parks by name (Chain O'Lakes, Channahon, Illini, Gebhard Woods, Illinois Beach...) but none of the numbers. The store already has the tool for this: replacement-layers.csv, fetch "hand", match "by-name" (exact name, exactly one record, keeps both ids, never publishable without its own licence row).

## THE BETTER MATCHER (KPC owner, 25 Nov 6:20 AM "APPROVED, one PR" + 6:28 AM "Accuracy first ... no hand-offs to the reps")
What we trust: the fresh agency layers (the outline store's reads), POTA's list and pages (pin, official link), the agency's own pages. Old saved copies, old saved answers and old store notes are HINTS: used only where fresh data backs them.
What we found (25 Nov, real MN data): our 12 Nov saved copy and the store's 14 Nov read number the SAME records differently on three MN layers (state forests 57 of 59, natural areas 12 of 12, state land 64 of 66), while names, sizes (to 8 decimals) and outlines match. Wildlife areas, the federal layers and PAD-US kept their numbers. So row numbers do change between reads; the agency's own codes (SFT00065, SNA01041) do not.
1. Same land, record to record (kpc_same_land.py, switch KPC_SAME_LAND), best proof first: (a) the agency id field (keep-record-fields.json, one list per layer), normalised, boxes overlap; a different id of the same field = never the same record; (b) shared ground on the outlines: 80% of the smaller and 50% of the larger; (c) a piece: 90% of the smaller inside the larger (not when both carry different specific names: a waterfowl area inside a refuge is not a piece of it); (d) the same non-generic name and size within 10%, never when the outlines show different ground. Never the row number; it only breaks a tie between two records already proven.
2. Proof or the pin (switch KPC_PROVEN_ONLY): a joined row draws only when the park is confirmed (POTA link id, tagged official size, the park's own page...), or it is a code row, or a person's join whose fingerprint still fits. Never when a fresh record with another agency id holds its ground. Every other row: 'check (code to fix: why)' and the POTA pin. A code job, never the reps'.
3. Saved answers: a join whose fingerprint no longer fits never draws. A join with no fingerprint draws only if the park is otherwise confirmed. A NO with no fingerprint is still applied (it can only take land away). Every saved answer with no fingerprint is listed for the owner (PC test: saved-answers-no-fingerprint.csv); new fingerprints go into data/ only with his OK.
4. One line per state: by agency id, by shared ground, pieces, by name and size, not proven, other id on the same ground, no store record near; rows that left the map; parks now pin only.
5. Test order: MN, then NY (switches on for those two only). Kentucky later, after its own handling is sorted.
MN dry run on the saved files (25 Nov, before the gate): of the store's 552 MN records, every renumbered state record found its twin (forests 59 by shared ground, natural areas 12, state land 64 by agency id su_id); 0 two-fits left after the tie rule; 3 'another agency id on the same ground'.


## ROUND 2 (25 Nov, after the other builder's grade; owner 7:18 AM "Use today's store records as the FRESH source for both matching and drawing outlines, not the Nov 11-12 saved copies. Old copies are hints only.")
- FRESH SOURCE (switch KPC_STORE_FRESH, MN + NY): the outline store's own records (today's store, reads of 14-21 Nov) stand in for the old saved copy. An old record proven to a fresh one lends it only its layer's kind and owner words. An old record with no proven fresh twin is a HINT: it may be joined, but it never draws ('code to fix: only in the old saved copy'). Saved answers follow their land to the fresh record by proof; every move or miss is listed (saved-answers-moved.csv).
- The store keeps only land it joined to parks, not whole layers: a park whose land is not in the store shows its pin until the store holds it.
- MN dry run (today's store vs the 12 Nov copy): 6,984 fresh records; 6,175 old records proven to one (5,624 by shared ground, 551 by name and size); 5,583 of them carry ANOTHER row number (state land 5,513, forests 57, natural areas 12). NY: 2,655 fresh; 2,653 proven; 1,173 renumbered (DEC lands 1,158).
- Grade fixes: only UNIT id fields prove or refuse (never a 'record id' field; a web address by the id inside it); leading zeros never differ; the row number breaks a tie only on one ground (id, overlap); a piece needs a real name in common; a rough outline is 'can't tell'; the gate counts the park's own name + official size within 10%; a confirmed park's row on ground with another agency id is kept and LISTED; D1 does not re-point under proof-or-pin; the PC test lists every pin-only park and why.
- Exception for the owner to OK: code rows (Park Service unit code, official line) still draw from their record even when it is an old-copy record.
- Before any release: the outline cutter (kpc_outlines_from_key.py) reads shapes from the saved copy by id, so today it SKIPS fresh rows (fail closed, no wrong outline). It must read their shapes from the store first.

## ROUND 10 (25 Nov ~10:30 AM CT; the grade after the owner's 9:11 AM MN test, "all pre-approved"; owner 9:50 AM pick "Two sources agree")
- R1 agency RECORD id (sgmne su_id, sgmna uniqueid): proves 'id' only with boxes overlapping AND (a real name in common OR size within 10%). A different value never refuses.
- R2 a rough outline: the OLD record's grid points measured against the FRESH outline, 0.001-degree edge allowance: 80% / 50% = overlap; 90% inside + a shared name = piece. A rough outline never says "different ground".
- R3 name + size "two fits": the one record holding half the old ground or more (R2 measure), every other less, wins. Never the row number.
- R4 park level, no tagged official size: the park's OLD joined land (website key 'ac', else its rows, same ground once) is the size; the FRESH records carrying the park's real name, in the old land's boxes, within 10% = proven.
- Owner's pick: two named FRESH records of DIFFERENT layers (two official sources) on the same ground, sizes within 10% = proven.
- Real name (R4 + pick): full name, or bare name + the park's kind word, or the same with single-letter initials set aside when 2+ real words remain ('George H. Crosby-Manitou' = 'George Crosby Manitou State Park'; 'Area C' never = 'Area D').
- A park proven by R4 or two sources keeps its named rows; a row carrying ANOTHER real name leaves (code to fix).
- R5 wetland districts: tracts from the layer file's fws records (CMPXNAME '<core>...WETLAND MANAGEMENT DISTRICT', RSL_TYPE WPA, INTTYPE1 O). R6 per-row proof list on the PC (row-proof.csv). R7 Catskill: hand download in layer-files\hand\US-NY\sgnyd\ (KPC-Store).
- GREY AREAS for the owner (built the careful way; say if not): (a) initials set aside in names; (b) PAD-US counts as a second source next to a state layer although PAD-US often copies state data; (c) R4 trusts the website key's old joined size, which was itself matched by name.
- ROUND 11 (grade of round 10, ~10:35 AM CT): S1 the R2 edge allowance = min(0.001 degree, 10% of the old record box's shorter side), and a rough overlap / piece also needs half of the old record's points STRICTLY inside the fresh outline (a tiny parcel never proves its neighbour). S2 R4's old land = the old copy's own boxes only (OLD_BOX), never a fresh record that now carries the old number. Optional item (PAD-US copying the same agency layer as the second source) NOT built: it is grey area (b) above, the owner's call.
- ROUND 13 (KPC owner, 25 Nov 12:07 PM: "Delete any holds they maybe wrong idk."): switch KPC_SAVED_HINTS_ONLY (MN, NY). At the start of a state's build its old saved answers (overrides*.json: joins, NOs, blocked ids, tracts, aliases; the answer sheet) are set aside as HINTS: never obeyed, never deleted. Fresh proof decides (agency id, overlap, name + size, two sources); a saved row is a plain row; unproven = pin only, listed in pin-only-parks.csv with its old saved ids to prove at the end. No questions to the owner about any park or hold.

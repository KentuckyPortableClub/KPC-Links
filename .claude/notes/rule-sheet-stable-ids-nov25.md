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
- NY sgnya: 1,509 store id fields; NY's numbers did not move; nothing changes.
- A saved answer (overrides `join: ["sgmnb20"]`) made before a republish: after it, row 20 is another forest -> today D1 refuses it by name + size; with the table, it is re-pointed to the record with the same agency id (G3).
- PAD-US (national): its own `OBJECTID` changes between releases (4.0 -> 4.1) and between the GDB download and the web service: test 2 only.

## GREY AREAS (RULED 25 Nov 5:02 AM: the bracketed suggestion is the rule)
- G1. Who fills the id-field table? [A bot proposes the field per layer (a field that is unique, never empty and code-like in the saved copy); an agent checks 10 records per layer against the agency's own page; only then it is used.]
- G2. Split / merged records (pieces): same agency id, different sizes. [Same record when the agency id matches, whatever the size; with no id field, pieces are matched to the whole only by name + box, and the size test is skipped for pieces.]
- G3. Saved answers that name a row number: re-point them automatically when the agency id proves which record it is now? [Yes, and list each re-point in the review list; with no id field, refuse as today.]
- G4. Order of work. [1) the id-field table for the 20 layers with the most re-found records; 2) key vs store (B1, extends #379); 3) saved answers; 4) keeper old vs new; 5) the website-vs-test comparison line.]

Not in scope: changing what a park is joined to (this sheet only decides "same record"), Canada and world (they do not use store id fields today).

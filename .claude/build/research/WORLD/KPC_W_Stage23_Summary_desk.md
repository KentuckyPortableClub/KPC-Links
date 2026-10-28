# WORLD STAGES 2 + 3 SUMMARY (desk, Oct 27 2026)
Grades: A opened and read, B search only, C inference. Read only. Files in this folder: KPC_X1..X4 (Stage 2), KPC_Y_* (Stage 3). WDPA never used. Each Stage 2 country is past the top 10, so **Brandon must lift the "no new boundaries" rule for each one he wants.**

## Stage 2: is there any official outline source?
| Step | Country / pack | Parks | Outline source | Licence | Public land | Status | Work |
|---|---|---|---|---|---|---|---|
| X1 | Dominican Republic | 200 | Ministry KMZ (SINAP, Feb 2026) | none named, "all rights reserved" | national parks public by law, titling unfinished | NOT READY (ask Ministry) | small, half a day |
| X2 | Caribbean pack | ~880 | only the French islands (INPN: GP MQ MF BL, 71 parks); nothing open elsewhere | INPN unnamed | trust/government, no layer | French four READY-ish; rest NOT READY | French small; rest pins only |
| X3 | Mexico + Central America | 853 | Mexico: CONANP SHAPE_ANPS.zip (185 federal ANP, 2022); Central America: none found | CONANP blank | Mexico ANPs largely ejido/private (W-2) | Mexico NOT READY (licence); CA NOT READY | Mexico ~1 day; CA large, little payoff |
| X4 | Greenland + St Pierre & Miquelon | 40 | GL: Nunagis (not opened); PM: none (INPN has no PM) | unknown | Greenland all public | NOT READY | tiny; value nil (12 activations) |
Recommendation: lift for DO (cheap), the four French islands, and Mexico (after CONANP answers on licence). Leave the rest.

## Stage 3: the list
170 POTA programs are not in the key, Stage 1 or Stage 2 (KPC_Y_Stage3_List_desk.md). **I could not get activation numbers** (no source I can read); the list is ranked by park count, top: RU 4,265, CN 1,845, KR 1,287, NZ 893, TH 858, BR 813. Chat 2 or one small no-fail bot should sum activations per prefix from the park files and re-rank. Note: PR, VI, GU, AS, MP, UM are US territories, so US sources (PAD-US) may already cover them: not checked.
My guessed order (C): NZ, KR, BR, RU, TH, then AR, ZA, PH, CN, CO, CL, TR.

## Top 5 scouted
| Country | Parks | Outline source | Licence | Public land data | Status |
|---|---|---|---|---|---|
| **New Zealand** | 893 | **DOC Public Conservation Land FeatureServer, updated 12 Oct 2026** | **CC BY 4.0** (A) | **yes: the DOC layer is itself Crown land, with a Private_Ownership flag** | **READY after adds** (+ regional-park layers) |
| South Korea | 1,287 | data.go.kr Korea Protected Areas SHP (2016, 64,394 sites) + KLIP zoning | "no restriction" | none; 60 % are city parks | NOT READY (city-park rule, 2016 age) |
| Brazil | 813 | **MMA CNUC polygons 2025_03 shapefile** | **CC BY**, updated May 2025 (A) | none; APAs/RPPNs private | outlines READY; rule 14 NOT READY |
| Russia | 4,265 | none official found | unknown | none | NOT READY |
| Thailand | 858 | only third-party copies of DNP data | unknown | none | NOT READY |
Light scout: South Africa (SANBI NPAES, copyright, no licence), Argentina (no download), Philippines (service says "shall not be used for any legal purposes").

## Recommended order
1. **New Zealand** (best data in the world, cheap, CC BY, owner built in).
2. Dominican Republic (cheap, ask Ministry).
3. Brazil (CC BY file; needs the city-park and APA rulings).
4. South Korea (after the city-park ruling), Mexico (after licence), French Caribbean (INPN).
5. Leave Russia, Thailand, Central America, rest of the Caribbean, Greenland/PM.

## NEW grey areas for Brandon (my lean)
- X1-1 KMZ rights reserved: ask the Ministry. X1-2 untitled state parks: public for parks/monuments, NOT SURE for buffer zones. X1-3 buffer zones never count.
- X2-1 beach strips: pin only. X2-2 Cuban historic/battlefield: never. X2-3 Saint-Martin/Sint Maarten border: keep apart. X2-4 trust-run parks: public if open daily.
- X3-1 Mexican ANP on ejido/private land: W-2. X3-2 CONANP blank licence: ask. X3-3 biosphere buffer zone never counts.
- X4-1 Ramsar-only sites: pin. X4-2 PM numbered reserves: pin only.
- Y1-1 NZ marginal strips: not their own park. Y1-2 conservation park + scenic reserve inside = real layered 2-fer. Y1-3 DOC polygons with Private_Ownership = yes: exclude. Y1-4 Māori-owned land managed by DOC (s.58 Whenua Rahui): out. Y1-5 regional parks vs DOC borders: check per pair.
- Y2-1 Korean city parks labelled "Provincial Park": **list only national/provincial/county parks, reserves and recreation forests**. Y2-2 private land inside national parks (W-2). Y2-3 2016 file age.
- Y3-1 São Paulo city parks: never. Y3-2 APAs/RPPNs: out. Y3-3 unexpropriated Parque: NOT SURE.
- Y4-1 Russian nature monuments: pin only. Y4-2 sanctions/data access: Brandon's call. Y4-3 Cyrillic names.
- Y5-1 Thai municipal parks: never. Y5-2 third-party copy of agency data: need the agency's own file.

## Could not do
No polygon queries; per-country activation numbers; several portals (data.govt.nz catalogue) would not open. Caribbean UK/Dutch territories and Central America were searched only once, so "nothing found" there means "I did not find it", not "does not exist".

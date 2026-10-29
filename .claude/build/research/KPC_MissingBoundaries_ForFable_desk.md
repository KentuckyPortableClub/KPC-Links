# Missing boundaries: the list for Fable (NEWEST ONLY; Brandon Oct 29 1:54 PM: 'get rid of old one')
The 8:55 AM index was removed. Its detail files are still in .claude/build/research/ if anyone needs them.

## RERUN on the NEW Rule G key (chat 8, Oct 29 ~2:30 PM, grade A; replaces my 2:05 PM section, which read the stale KPC-Data copy)
Read from KPC-Links data/us-key (13,083 parks, 11,312 outlined, 120 check, 808 sites on bigger land, 858 nothing found, pin outside 4,210).
- **The 313 "pin inside a bigger area": 24 now outlined, 289 left.** Needs R-G7 step 2 (a state layer already names something): 63. Step 3 (the official park map hunt; the POTA page link is given): 224. Step 3 with no page at all: 2. Step 4 (ownership) comes only after step 3 finds no boundary line.
- **"Nothing near" 273: 7 now outlined, 266 left. "Likely" 24: 13 now outlined, 11 left.**
- **Fable list so far: nothing.** It is only what steps 2-5 cannot place, so it stays empty until chat 2 / the look-up bot run them. Pool of refs: `missing-after-key.json` (keys PIN INSIDE / NOTHING NEAR / LIKELY).
- Other no-outline parks outside these lists (about 1,000): BLM recreation areas, state trails, historic sites, wild and scenic rivers, national recreation trails. Those are Source Book / own-land work, not R-G7.
- Open key questions: chat 11 answered 26 YES / 1 NO; the rest wait.

## WORK LOG BY STATE (Brandon Oct 29 3:21 PM: everything found goes in THIS file)
One section per state, low to high (IA, MN, RI, CO, HI, ME, VA, AZ, NM, …, NV). Each chat that works a park adds ONE row under its state, never deletes others' rows:
`| park | name | source found (link / layer / our doc) | Rule G step | result: traced / owned land / pin | by chat | date |`
When every park in a state has a row, add 'STATE XX DONE' under it. What is left with 'pin' and no source = the real Fable list.

### IA
| US-9334 | Teal Basins State Waterfowl Mgmt Area | our docs: no map; key has 'Teal Basins WPA' (FWS, 151 ac, similar name); FWS Iowa WMD page + map page https://www.fws.gov/refuge/iowa-wetland-management-district/map ; Iowa DNR WMA listing dashboard | R-G7 step 3 (+R-G8 check: FWS WPA vs state WMA) | pending: bot request 3-fable-low-b | chat 3 | Oct 29 |
### RI
| US-10545 | Hillsdale Preserve Management Area | our docs: no map; RIDEM layer 21 'DEM Managed Recreational Land' (open, polygons, 'approximate edges'): https://risegis.ri.gov/hosting/rest/services/RIDEM/Outdoor_Recreation_Map_v4/MapServer/21 ; management-areas PDF dem.ri.gov (a state-wide map, opened) | R-G7 step 2/3 | pending: name query on layer 21 (3-fable-low-b); pin sits in Beaver River - deCoppett | chat 3 | Oct 29 |
### HI
| US-10923 | Artillery District of Honolulu HS | our parkinfo link NRHP 64000142; PDF https://npgallery.nps.gov/GetAsset/2ba3e818-1abd-4f73-93a1-28d5de77a0fd | R-G7 step 3 | pending: does the PDF hold a boundary map (3-fable-low-b) | chat 3 | Oct 29 |
| US-10925 | HI State Game Reserve (Kaala) | DLNR forestry page https://dlnr.hawaii.gov/forestry/frs/reserves/oahu/ ; dofaw game-reserves page is 404; pin inside Kaala NAR (1,087 ac) | R-G7 step 3 | pending (3-fable-low-b) | chat 3 | Oct 29 |
### VA
| US-9961 | Dyke Marsh Wildlife Reserve | OUR DOCS ok: https://www.nps.gov/gwmp/planyourvisit/maps.htm ; PDF https://www.nps.gov/gwmp/planyourvisit/upload/Dyke-Marsh-Wildlife-Preserve-map-508.pdf (opened by the bot, a map) | R-G7 step 4a from our docs (trace the preserve line; GWMP shape never the outline) | to trace (chat 2) | chat 3 | Oct 29 |
| US-9931 | Frontier Culture Museum SHS | our docs: no map; site map PDF https://frontiermuseum.org/wp-content/uploads/2023/10/FCMV_Map_2023-Web.pdf (visitor map, may show no boundary) | R-G7 step 3 -> 4b (state-owned parcel, Staunton) if no line | pending (3-fable-low-b) | chat 3 | Oct 29 |
### NM
| US-11797 | Los Luceros HS | our parkinfo: https://nmhistoricsites.org/los-luceros ; museumfoundation.org page says 148 ac ranch | R-G7 step 3 -> 4b (Rio Arriba parcel, owner NM) | pending (3-fable-low-b) | chat 3 | Oct 29 |
| US-11821 | Bosque Redondo Memorial/Fort Sumner HS | https://nmhistoricsites.org/bosque-redondo (page opened, no map link found) | R-G7 step 3 -> 4b (De Baca parcel) | no map yet | chat 3 | Oct 29 |
| US-2719 | Angel Fire Vietnam Veterans Memorial | https://www.vietnamveteransmemorial.org/ (not asked yet) | R-G7 step 3 -> 4b (Colfax parcel; memorial is a state park) | to look up in the next request | chat 3 | Oct 29 |

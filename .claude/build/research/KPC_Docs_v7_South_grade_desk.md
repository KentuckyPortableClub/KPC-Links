# Documents bot v7, southern states (chat 11, Oct 29 ~12:10 PM): AL FL GA IN KY MS NC SC TN VA WV (2,482 parks, all ver 7)
Maps ok 1,010 (41%). Random 12 (seed 1129) judged by URL + the bot's own 'how' (agency sites do not open from my side): **10/12 = 83%, FAIL the 90% bar**. Whole-file counts show WHY: a few bulk faults.

## Wrong (whole file)
1. **Indiana State Historic Sites: 10 parks all get 'indianamuseum.org/visit-museum/museum-map-and-parking' (a museum in Indianapolis)**, names_park = true (Corydon Capitol, Culbertson Mansion, Gene Stratton-Porter, New Harmony, Lanier Mansion ...). Wrong map, wrongly marked as naming the park. Chat 2: a name test must see the PARK's name on the page, not the agency's.
2. **fws.gov/rivers/map (the Fish and Wildlife rivers system map) on 5 Wild and Scenic Rivers** (Chattooga = Forest Service, Wekiva ...), names_park = true. Generic system map, wrong agency.
3. **Dawson Forest WMA (US-3743, GA) gets 'carters-lake-wma'** (a different area), names_park = true.
Definite wrong: 16 of 1,010 maps = 1.6% (98.4% clean). The 83% in the sample is two of twelve landing on these classes.

## Watch
- 137 'ok' maps do not name the park (names_park false/none): generic agency map pages on many parks (conservationgis.alabama.gov/dcnr 15 and /fwlt 11, fs.usda.gov r08 North Carolina 11, Mississippi 10, Alabama 4). Fine if the card says 'agency map page' and not 'this park's map'. Chat 3: check the wording.
- Recall did NOT drop with v7: AL 79 -> 82, FL 161 -> 165, GA 138 -> 139, IN 23 -> 22 (v4 -> v7). Per state: KY 78%, WV 78%, GA 59%, VA 60%, AL 53%, NC 48%, FL 36%, SC 16%, MS 21%, TN 9% (WMAs), IN 10%.
- Rules: 1,229 rows, but 758 (62%) never opened ('did not open' 465, 'resting: next run' 293); 'ok' 304+. Agency-wide pages cover 196 IN, 175 FL, 175 TN (did not open), 53 GA, 47 KY parks. Only 'ok' rows may show as a rules link; not-opened ones show nothing or 'agency rules page (not checked)'. Chat 3 to confirm. rules_scope 'agency' is set on 19 FL rows only; the other big groups carry no scope tag.

## Send
- Chat 2: faults 1-3 (a park-name test; the 10 Indiana sites; the FWS rivers page; Dawson). Gate: no URL on 5+ parks with names_park true unless it is a real multi-park NPS page (Trail of Tears, Appalachian Trail, Overmountain Victory are fine).
- Chat 3: wording for generic map pages; unopened rules pages not shown as verified.

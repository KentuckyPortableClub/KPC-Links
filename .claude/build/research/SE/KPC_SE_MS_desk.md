# Southeast Source Book: MISSISSIPPI (desk, Oct 27 2026)
Grades: A opened and read, B surfaced by search only, C inference. Read only. **MS is the biggest gap: no state layer in our key, 66 of 155 POTA parks have no outline.** It is also fixable: MARIS (the state clearinghouse) lists the layers.

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / license | Read? |
|---|---|---|---|---|
| WMAs (+ dog hunting areas, refuges, youth hunt, lakes, 16th Section leases, state parks as TYPE values) | MARIS rest: https://www.maris.state.ms.us/server/rest/services/Vector/WildL_Areas/MapServer (A: path from MARIS REST index; I did not open the service itself). Metadata: MS_WildlifeManagementAreas_2019 (A): 318 polygons, MDWFP, published 2019-09-11, "updated as needed", **no access or use limits**, features marked state_owned = yes, no download link | MDWFP via MARIS | 2019 | **NO** |
| State parks | …/Vector/State_Parks/MapServer (A path). Metadata MS_StateParks_2019: 53 polygons, MDWFP, published Jan 16 2019, no use limits; metadata does not say whether recreation areas or Corps-leased parks are in it | MDWFP via MARIS | 2019 | **NO** |
| Recreational facilities (points, 2017) | …/Vector/Rec_Facils/MapServer | MARIS | 2017 | NO |
| National Forests, NWRs, National Parks, Natchez Trace | …/Vector/NatFor_OwnerBnd, Nat_Forest_Proc_Bnds, NWildRefuge, Ntnl_lParks, NatchezTrace_Bound (A paths) | MARIS from federal | | NO. **Use OwnerBnd (ownership), not the proclamation line.** Matches Brandon's agency-land ruling. |
| Protected areas (PAD-US subset) | https://gis.mississippi.edu/server/rest/services/Environmental/MS_USGSProtectedAreasData_2021/MapServer (A): USGS GAP, PAD-US 2.1, "2021" title but 2020 citation, license "none" | USGS via MARIS | 2020 | NO. A fallback that holds Corps lakes and county land too. |
| Natural areas / heritage | MS Museum of Natural Science heritage program: none found | | | NO |
| State trails | none found | | | NO |
| Statewide open-data portal | MARIS is it (maris.mississippi.edu). Also gisonline.ms.gov (MDEQ folder, B). | | | |

## 2. POTA parks with no outline (66) and the layer that would cover each
- **54 WMAs** US-7072…7121 (Sunflower, Choctaw, Chickasaw, Bienville, Tallahala, etc.) → WildL_Areas (318 polygons incl. these). Those on national forest land (Bienville, Chickasaw, Choctaw, Tallahala, Caney Creek and others, C) overlap the USFS ownership layer: rule 14.
- **16 State Fishing Lakes** US-12193…12208 → probably in WildL_Areas ("Lakes" TYPE) (C); else uncovered.
- **24 State Recreation Areas** US-7124…7134 (Corps lakes: Arkabutla, Sardis, Enid, Grenada), Davis Lake, Chewalla, Archusa Creek, etc. → **UNCOVERED by the MDWFP state-parks layer if it only holds true state parks** (metadata does not say). Corps lake SRAs are leased/managed from Corps land; Corps boundary needed.
- State parks/sites Percy Quin US-2549, Clark Creek US-9847 (NA/WMA), Deer Island Coastal Park US-9849, Owl Creek Mounds US-7631 (NPS? no, state), Dancing Rabbit/Grand Village historic sites (MDAH, not MDWFP): State_Parks layer or MDAH, **UNCOVERED for the historic sites**.
- Gulf Islands NS US-0661, Emerald Mound (NPS, Natchez Trace Pkwy): Ntnl_lParks / NatchezTrace_Bound.

## 3. Trail lines and access
None in our key. Rec_Facils points (2017) are the only access list I found; MDWFP WMA pages carry maps (PDF, B).

## 4. Tricky land
- **Corps-lake SRAs** (Sardis/Arkabutla/Enid/Grenada, plus Pickwick Landing TVA area): state or Corps managed; the water is the lake (rule 9 water-only). Expect "WMA and Corps Recreation Area both claim the same shore".
- **WMAs on national forest land:** MDWFP runs WMAs on all six MS national forests; ownership is USFS (Delta, Holly Springs, Tombigbee, Bienville, De Soto, Homochitto). Proclamation lines include private inholdings; **use ownership**.
- **16th Section lands:** school-trust lands in MS leased to the state for WMA/public hunting, listed in the WMA layer as a TYPE (A, metadata). **Grey area**: school-district land by lease. Brandon's rule (private/by agreement not park land except its own POTA number) applies by analogy: ask him.
- **Natchez Trace Parkway** is a long NPS line is a long NPS line, not a polygon (use line rules).
- Delta farmland WMAs on leased or privately owned land (C).

## 5. KNOWN-GOOD layers (MS), what the Discovery Bot should return
1. MARIS Vector/WildL_Areas (MDWFP WMAs)
2. MARIS Vector/State_Parks
3. MARIS Vector/NatFor_OwnerBnd (use for ownership)
4. MARIS Vector/NWildRefuge
5. MARIS Vector/Ntnl_lParks + NatchezTrace_Bound
6. MARIS Vector/Rec_Facils (points/access)
7. MS_USGSProtectedAreasData_2021 (PAD-US fallback)
8. MARIS metadata catalog (maris.mississippi.edu/HTML/DATA/…) for any new layer

## 6. 2-fers to expect
Confident (C, to be proven by polygons): national forest vs. each WMA wholly on its land (e.g. Bienville NF vs. Bienville WMA; Choctaw WMA inside Tombigbee NF): "same land, two park numbers". Hard: Natchez Trace Pkwy vs. Clarkco/Jeff Busby/Rocky Springs areas; Corps SRA vs. WMA on the same lake; Gulf Islands NS vs. Deer Island Coastal Park (adjacent, no overlap expected).

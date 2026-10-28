# Southeast Source Book: FLORIDA (desk, Oct 27 2026)
Grades: A opened and read, B surfaced by search only, C inference. Read only. FL is the best-covered state; its gap is water management district land.

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / license | Read? |
|---|---|---|---|---|
| State parks | sgfla ca.dep.state.fl.us OpenData PARKS_BOUNDARIES | FL DEP | | YES |
| State forests | sgflb | FL Forest Service | | YES |
| WMAs | sgflc / sgflg; also https://gis.myfwc.com/mapping/rest/services/Open_Data/Wildlife_Management_Areas_Florida/MapServer layer 1 (A: "general reference only", copyright FWC, no date) and WMA entrances service Open_Data/Wildlife_Management_Area_Entrances_Florida (B) | FWC | | YES |
| Water management districts | sgfld SRWMD, sgfle SJRWMD; **NOT read: SFWMD, SWFWMD, NWFWMD.** SWFWMD DistLands server (www45.swfwmd.state.fl.us/arcgis10/rest/services/DistLands/DistrictLands) returned "could not access any server machines" when I opened it (A, may be down/moved). SFWMD hosts at geoweb.sfwmd.gov/agsext1 (B). | WMDs | | partial |
| State-owned lands (all agencies) | sgflf DEP State Owned Lands; FNAI/"Florida Managed Areas" (aquarius.at.geoplan.ufl.edu ARC_Lands_DQ "State Owned Florida Parks and Recreational Facilities", B) | DEP / UF GeoPlan | | YES (sgflf) |
| Other managed lands | services1.arcgis.com/nRHtyn3uE1kyzoYc Other_Managed_Lands_WFL1 (B, unknown publisher) | | | NO |
| Trails | Florida Trail US-4559 (NST: USFS/FTA line), Florida Greenways & Trails (DEP OGT; layer not located) | | | NO |

## 2. POTA parks with no outline (20)
- Water management district "State Conservation Area" recreation sites: US-12121, 12123, 12124, 12125, 12130, 12132, 12134 (**SFWMD** stormwater treatment areas and similar) → **UNCOVERED** until SFWMD conservation lands layer is read. US-7374 Wysong Park, US-8329, 8689, 8692, 8696, 8701, 8705, 8711, 8712, 8719 (SRWMD/NWFWMD recreation sites): SRWMD is read (sgfld); NWFWMD is not.
- Wekiva WSR US-0896 (NPS WSR corridor, no polygon rule), Florida Trail US-4559, Fort Foster US-3621 (state historic site inside Hillsborough River SP: should be in sgfla).

## 3. Trail lines and access
Read: SJRWMD/SRWMD parking and boat, FWC boat ramp inventory and WMA entrances, DEP park entrances/POIs, Aquatic Preserves beach access. Add: FWC Open_Data layers (Fish Management Areas Florida, atoll.floridamarine.org OpenData_FWMgmt, B).

## 4. Tricky land
- **WMAs on water management district land.** Many FWC WMAs (e.g. Three Lakes, Kissimmee, Triple N Ranch) sit on state or WMD land: layered with DEP "state owned lands" polygons (same land, two sources). WMD recreation sites carry their own POTA numbers (the 15 above).
- **WMAs on federal land:** Apalachicola NF, Ocala NF, Osceola NF with FWC-run WMAs: USFS land under agreement.
- **Private lease WMAs:** timber and ranch leases (C).
- **Water-only:** aquatic preserves, Biscayne Bay, Florida Keys; FWC "Fish Management Areas" are waters.
- **Everglades:** SFWMD Water Conservation Areas are managed by FWC as WMAs (B): WCA vs. Everglades NP touch.

## 5. KNOWN-GOOD layers (FL)
1. DEP PARKS_BOUNDARIES (sgfla)
2. FWC Wildlife_Management_Areas_Florida MapServer/1 (A)
3. FL Forest Service state forests (sgflb)
4. DEP State Owned Lands (sgflf)
5. SJRWMD and SRWMD conservation lands (sgfle, sgfld)
6. SFWMD conservation lands (**to add**)
7. SWFWMD DistrictLands (**to add; server down when I tried**)
8. FWC WMA entrances (access)

## 6. 2-fers to expect
Confident (B): any state park + its state forest or WMA where DEP lists the same land twice, e.g. Withlacoochee State Forest vs. Withlacoochee WMA; Blackwater River SP vs. Blackwater River State Forest (adjacent); Myakka River SP vs. Myakka River State Forest? (adjoining, not layered). Hard: Everglades NP vs. Everglades & Francis S. Taylor WMA (WCA3, FWC-managed, SFWMD-owned).

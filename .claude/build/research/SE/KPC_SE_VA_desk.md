# Southeast Source Book: VIRGINIA (desk, Oct 27 2026)
Grades: A opened and read, B surfaced by search only, C inference. Read only.

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / license | Read? |
|---|---|---|---|---|
| Wildlife management areas | https://services.dwr.virginia.gov/arcgis/rest/services/HUB_Layers/DWR_WMA_Boundaries/FeatureServer/0 (A) polygons; fields WMA_NAME, **Owner**, WMA_Manager, Complex_Name, Tract_Name, Property_Type, Property_Class. Also Public/DGIF_WMAs MapServer (B) and Public/DWR_WMA_Entrances (B) | VA Dept. of Wildlife Resources (DWR) | copyright blank, last-edit value not shown, no license text | **NO. Biggest VA gap in our key.** Owner + Property_Type fields would feed rule 14 directly. |
| State parks + tracts | sgvac / sgvad (DCR) | VA DCR | | YES |
| Natural area preserves | sgvab | DCR | | YES |
| State forests | sgvaa | VA Dept. of Forestry | | YES |
| All conservation lands | sgvae VA Conservation Lands; also "ConservationLands – Publicly Accessible" FeatureServer services2.arcgis.com/8uN5i97bMkq2Mzrt (B; page needed a token when I opened it, so it may not be public) | DCR / partners | | sgvae yes |
| Local parks | sgvaf Local Parks 2023 | | | YES (our rule: city/council parks = never new) |
| Trails | DCR trail data page (dcr.sitevision.com/recreational-planning/trail-data-mapping, B); DWR "Managed_Trails" (access list); no statewide state-trail line layer confirmed | | | trailheads only |

## 2. POTA parks with no outline (29)
Mostly national/long trails (NRTs, NHTs: Appalachian Trail etc.): NPS/USFS lines. Mount Rogers NRA US-9903 (USFS), Dyke Marsh US-9961 (NPS George Washington Memorial Pkwy), Cape Henry, Yorktown, Jamestowne, Fort Marcy (NPS/APVA), Frontier Culture Museum US-9931 (museum: probably not a park by our rules, ask Brandon). State trails US-9933/9934/9935: no layer; Virginia Creeper/New River/Washington & Old Dominion are DCR/local rail-trails (C).
WMAs: none in the unjoined list; the 29 are NOT WMAs. So adding DWR WMA boundaries is about **layering checks**, not filling empty gaps.

## 3. Trail lines and access
Read: DWR_WMA_Facilities, Boating_Access_Locations, SP_POI_assets, Gates, StatePark_FacilitiesPOI, DWR River Accesses, Managed_Trails, Aquatic_recreation_access_points. Good.

## 4. Tricky land
- **WMAs on national forest and Corps land.** DWR owns about half its WMAs; others sit on USFS (George Washington & Jefferson NFs) or Corps/power-company land under agreement (B, Wikipedia + DWR). The DWR layer's Owner field answers this. Examples to check in the data: Highland WMA, Big Survey, Clinch Mountain WMA (state-owned, next to Hungry Mother? no, don't assume), Gathright WMA (Corps, Lake Moomaw, B), Bark Camp Lake, Rapidan WMA (next to Shenandoah NP).
- **State parks touching national forests:** Hungry Mother SP, Grayson Highlands SP inside Mount Rogers NRA (USFS) – Grayson Highlands is an enclave of state land in a national recreation area, the outline will be touching, not layered.
- **Chesapeake Bay / river water:** state parks with water, e.g. Kiptopeke, Westmoreland, Leesylvania: water-only parts (rule 9).
- **Private by agreement:** DWR "Property_Class" includes cooperative areas (C: field exists, values not seen).

## 5. KNOWN-GOOD layers (VA)
1. DWR_WMA_Boundaries FeatureServer/0 (A)
2. DWR Public/DGIF_WMAs MapServer (B)
3. DCR State Parks (sgvac/sgvad)
4. DCR Natural Area Preserves (sgvab)
5. VDOF State Forests (sgvaa)
6. VA Conservation Lands (sgvae)
7. DWR_WMA_Entrances / Facilities (access)
8. DWR Managed_Trails (trailheads)

## 6. 2-fers to expect
Confident (B): Shenandoah NP vs. Rapidan WMA (they share a boundary; NP was carved from the WMA area: check, treat as touching); Mount Rogers NRA vs. Grayson Highlands SP (enclave: **inside the NRA proclamation line, not on NRA-owned land**, so by the agency-land rule not a 2-fer).
Not sure: Jefferson NF WMAs; Back Bay NWR vs. False Cape SP (adjoining, not layered).

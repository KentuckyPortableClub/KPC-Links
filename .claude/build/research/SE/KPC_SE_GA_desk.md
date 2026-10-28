# Southeast Source Book: GEORGIA (desk, Oct 27 2026)
Grades: A opened and read, B surfaced by search only, C inference. Read only.

## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / license | Read? |
|---|---|---|---|---|
| State parks | sggab State_Parks_Boundary (our key). Also services1.arcgis.com/aT1T0pU1ZdpuDk1t … StateParks FeatureServer (points; B) | GA DNR Parks | | YES (polygons) |
| WMAs | sggac WRD_WMA_Public/14 | GA DNR Wildlife Resources Division | | YES |
| License districts | sggaa Licenses_by_District | WRD | (not park land) | in key, harmless |
| State lands (older) | data.georgiaspatial.org/data/statewide/dnr/fed_lands/other_state14.html (B), geospat.gatech.edu Coast/GCAMP_Fisheries "GADNRLands2015" and "Other Conservation Lands 2015" (B) | GA DNR via GIS Clearinghouse / Georgia Tech | 2014-2015, old | NO |
| State forests | Georgia Forestry Commission: no public boundary layer found | | | NO |
| State trails | none found (Silver Comet/Rail trails are local/PATH) | | | NO |

## 2. POTA parks with no outline (17)
Okefenokee SP US-2200 (should be in the state parks layer: **name/geometry mismatch to check**); Suwannee River Eco-Lodge SP US-7861 (a lodge inside Stephen C. Foster SP area? C); Georgia National Fairgrounds SRA US-12772 (**not a park by our rules? ask**); state forests Bartram US-4648, Hitchiti US-4649 (Georgia Forestry Commission; the WMA layer holds "Bartram Forest" as a WMA, per the Land Access chart: so WRD_WMA_Public may cover it, A); Charlie Elliott WMA US-7140 (WRD layer); Corps parks Lake Nottely US-7459, Blue Ridge US-7460, Dames Ferry US-7858, Allatoona Pass Battlefield US-7471 (Corps/city: Corps land boundaries from USACE); DeSoto Falls NRA US-7473 (USFS); Little White House US-3724 (state historic site; may be in state parks layer); National Heritage Areas US-7139/7893 (no boundary rule: ask Brandon); Chattooga WSR US-9758; trails.

## 3. Trail lines and access
Read: WRD_WMA_Public layers 8, 3, 5 and WRD_Water_Access_Points. No official trail line layer found.

## 4. Tricky land (A: the Land Access chart, georgiawildlife.com/LandAccess)
- **WMAs on Corps land (no license needed to enter):** Allatoona, Carters Lake, West Point, Elbert County, Lula Bridge, Clarks Hill East/West, Di-Lane, Fishing Creek, Germany Creek, Keg Creek, Lower Broad River, Soap Creek, Lake Seminole, Walter F. George. Georgia state parks on the same lakes (Red Top Mountain on Allatoona, Hamburg?, Hart SP on Hartwell) touch the same shore.
- **WMAs on USFS land:** Cohutta, John's Mountain, Rich Mountain, Blue Ridge, Chattahoochee, Chestatee, Cooper's Creek, Lake Russell, Redlands, Swallow Creek, Warwoman, Cedar Creek. All overlap Chattahoochee-Oconee NF. **Same land, two park numbers** if the national forest and the WMA both have POTA numbers.
- **Georgia Power land (license required):** Oconee, Rum Creek, Blanton Creek, Rum Creek Berry Creek Area: private land by agreement → not park land (Brandon's ruling) except its own number.
- **Private / timber leases:** Paulks Pasture, Rogers, Little Satilla, Ceylon, Coosawattee. Same rule.
- **Others:** Berry College WMA, UGA B.F. Grant, Newton County Gaither, Georgia Forestry Commission (Bartram, Dixon Memorial, Spirit Creek), GDOT (Dixon Bay, Phinizy Swamp, Oliver Bridge).
- Water-only: coastal marsh WMAs (Altamaha, Sapelo).
The Land Access chart is the best list I found for rule 14 in GA. It does not name any TVA-owned WMA (A).

## 5. KNOWN-GOOD layers (GA)
1. GA DNR State_Parks_Boundary (sggab)
2. WRD_WMA_Public/14 (sggac)
3. WRD_WMA_Public entrances (layers 8, 3, 5)
4. WRD_Water_Access_Points
5. GADNRLands2015 (Georgia Tech copy; old, B) as a cross-check
6. USACE Corps boundaries (national)

## 6. 2-fers to expect
Confident (A, from the ownership chart): Chattahoochee-Oconee NF vs. each USFS-owned WMA listed above, e.g. Cohutta WMA inside the NF: layered, same land. Corps lake WMAs vs. Corps lake recreation parks: layered.
Not sure: Red Top Mountain SP vs. Allatoona WMA (same shore, different agencies, check polygons); Hart SP vs. Clarks Hill/Hartwell WMAs; Fort Mountain SP vs. Cohutta WMA (touching).

# Fable book: US-DC (DC pin-only parks)
ONE ROW PER PARK. Atlas: agency-atlas/US-DC.md


## chat 9 DC / trails probe (Oct 30 ~10 PM, HQ 5:45-6:00 PM): pin test = pin inside the NPS Land Resources Division boundary polygon (nps_boundary, FeatureServer/2); trail lines tested at 150 m from the pin (none touched: pins are not on the line). Container records (the NPS UNIT name, not the park's own name) are LEADS, not name matches.
| park | name | result |
|---|---|---|
| US-0015 | C&O Canal NHP | pin inside NPS boundary 'Chesapeake and Ohio Canal National Historical Park' (same name) -> T-2 SURE |
| US-0655 | National Mall and Memorial Parks | pin inside NPS boundary 'National Mall' (unit part): LIKELY, check the unit polygon covers the whole park |
| US-0657 | President's Park | pin inside NPS 'National Capital Parks' (container unit): LEAD only |
| US-13597 | George Mason Memorial | inside 'National Capital Parks' (container): LEAD only |
| US-13621 | Desert Shield / Desert Storm Memorial | inside 'National Capital Parks' (container): LEAD only |
| US-7891 | African American Civil War Memorial | inside 'National Capital Parks' (container): LEAD only |
| US-4567 | Captain John Smith Chesapeake NHT | NPS boundary layer HAS a polygon for the unit 'Captain John Smith Chesapeake National Historic Trail' (nps_boundary, UNIT_CODE CAJO); pin falls in 'National Capital Parks'. DoD REPI layer MiddleChesapeakeSL/2 (line, NAME) = lead only |
| US-4581 | Star-Spangled Banner NHT | UPDATE (relayed 9:55 PM): already wired in chat 2's trails-hand.json with the official NPS centerline; if it does not draw, it is a rebuild lag, not a missing source (look-up check filed by that chat). My pin test: pin inside Fort McHenry unit (a different unit) |
| US-4582 | Washington-Rochambeau NHT | UPDATE (relayed 9:55 PM): no official NPS GIS layer exists (designated 2021, newer than NPS's published trail layers); only the printed brochure map, filed as a save-map (picture only); stays a pin until NPS publishes a layer. One more broad search is queued by that chat |
| US-4564 | Potomac Heritage NST | NPS line layer found (below); pin not on the line |
| US-9898 | Mount Vernon Trail | NPS_Public_Trails has 'Mount Vernon Trail' (unit George Washington Memorial Parkway); pin in the GWMP boundary |
| US-9901 | Civil War Defenses of Washington NHT | NPS circuit trails layer found (below); pin inside GWMP boundary (container) |
LAYER | US-4564 Potomac Heritage NST | NPS Potomac Heritage NST centerline | https://services1.arcgis.com/fBc8EJBxQRMcHlei/ArcGIS/rest/services/POHE_Trail_Centerline_FTDS_view/FeatureServer/0 | name field: TRNAME | OFFICIAL NPS (credit: Potomac Heritage National Scenic Trail, National Park Service); polyline; trail rule R5 100 ft
LAYER | US-9901 Civil War Defenses of Washington | NPS NCR Circuit Trails 2023 | https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/CWDW_Circuit_Trails_2023_NPS/FeatureServer/19 | name field: NAME | OFFICIAL NPS National Capital Region GIS; polyline; note: 'does not reflect changes after 2023'
LAYER | US-9898 Mount Vernon NHT | NPS Public Trails (NPS home server) | https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Trails/FeatureServer/0 | name field: TRLNAME | OFFICIAL NPS; filter TRLNAME = 'Mount Vernon Trail'
LAYER | US-4567 Captain John Smith Chesapeake NHT | NPS LRD boundary (unit CAJO) | https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2 | name field: UNIT_NAME | OFFICIAL NPS polygon for the trail unit (filter UNIT_CODE = 'CAJO')

## US-4582 Washington-Rochambeau: sources checked (chat 9, Oct 30 10:30 PM; the three candidates relayed 10:00-10:05 PM)
- National_Historic_Trails FeatureServer/0 (services3 OYP7N6mAJJCyH6hd): CONFIRMED to hold 597 features named 'Washington Rochambeau Revolutionary Route' (TRAILNAME; polyline; 19 trails in all incl. Star-Spangled Banner and Captain John Smith). Publisher still NOT shown (copyright empty, no licence); owner check filed (item 8a1335cc...). Lead until the owner is known.
- NPS DataStore 2317939 'WARO Driving Route Centerline and Related Sites' (NPS, 2016): real NPS dataset; its file links point to an NPS ArcGIS Online item (nps.maps.arcgis.com item 0c01f8a10a5a47758f7be0b226cfb20a): item read filed to get the service URL. Note: a DRIVING route line, may follow roads, not the trail line.
- HPCC_Properties_WFL1 layer 4 (services2 8T9oLChn87ExnqDl): NOT usable: the service is 'Historic Properties in the Village of Montebello' (a village in NY), local only.

UPDATE US-4582 (chat 9, Oct 30 10:50 PM): owner of the National Historic Trails layer = ArcGIS account 'NBAM_Org' (item 8a1335cc..., no copyright/licence): NOT the Park Service -> lead only, never Official. The NPS item for WARO (0c01f8a1...) is a WEB MAP owned by an NPS account (JEFARRELL@nps.gov_nps, org fBc8EJBxQRMcHlei = the NPS org we use; title 'WARO ... URI 2016', credit 'URI, IR1 (NER) GIS', NPS licence line 'shall not be held liable'): its layers will be read next (filed). US-4582 stays a pin.

LAYER | US-4582 Washington-Rochambeau NHT | NPS (URI / NER GIS, NPS ArcGIS org) | https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/20200622_2016_URI_WARO_NST_trail_centerline_states_combined_web_mercator/FeatureServer/0 | name field: (probe filed 9-waro-lp) | OFFICIAL NPS org; the NPS WARO web map draws it as 'WARO driving route centerline (2016_URI)'. It is a DRIVING ROUTE line, not the trail corridor: needs chat 8/Brandon call under R5. Same web map has Historic_Sites + Campsites points (DRAFT). Oct 30 chat 9.

PROBE RESULT US-4582 (chat 9, Oct 30 10:50 PM): WARO centerline FeatureServer/0 = NPS org item 'WARO_driving_route_Centerline_URI_2016_ln' (owner JEFARRELL@nps.gov_nps), polyline, 11 records only, one per state/leg (CT, DC, DE, MA, MD, NJ: Rochambeau, NJ: Washington, NY...), name field: Name (value is a state, not the trail name), edited 2025-05-30. Source dataset: NPS DataStore 2317939. So: official NPS, one trail with 11 pieces; every piece is the WARO route, so use the whole layer (no name filter) for US-4582.

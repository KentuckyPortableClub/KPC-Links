# NPS / FWS boundary layers for the 9 round-5 leftovers (good bot, Oct 25 2026 ~7 PM, tested: 1 match each)

Layers (agencies' own ArcGIS accounts):
- NPS legal (legislated) boundary: https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2  (field UNIT_CODE). NPS-owned tracts instead: same service /FeatureServer/1, field ALPHA.
- FWS approved acquisition boundary (legal): https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSApproved_Authoritative/FeatureServer/0  (field ORGCODE)
- FWS land held (optional): https://services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSInterest_Simplified_Authoritative/FeatureServer/0  (INTTYPE1: O owned, S managed for another agency, E easement, R lease)

| Park | Layer | Filter | Note |
|---|---|---|---|
| US-0652 Curecanti NRA | NPS /2 | UNIT_CODE='CURE' | legal |
| US-0043 Kalaupapa NHP | NPS /2 | UNIT_CODE='KALA' | legal; mostly state land inside |
| US-0249 Merritt Island NWR | FWS approved | ORGCODE=41570 | legal; ~925 ac owned, ~129,000 ac managed for NASA KSC |
| US-0681 Upper Delaware S&RR | NPS /2 | UNIT_CODE='UPDE' | river corridor, much private land |
| US-0675 Missouri NRR | NPS /2 | UNIT_CODE='MNRR' | river corridor, 2 parts, mostly private |
| US-0732 Dayton Aviation Heritage NHP | NPS /2 | UNIT_CODE='DAAV' | 6 small sites, one feature |
| US-7971 Blackstone River Valley NHP | NPS /2 | UNIT_CODE='BLRV' | 10 small sites; smaller than the old heritage corridor |
| US-0909 Cape Krusenstern NM | NPS /2 | UNIT_CODE='CAKR' | much private land inside |
| US-0176 Imperial NWR | FWS approved | ORGCODE=22560 | ~888 of ~31,500 ac owned; ~28,500 managed for another agency |

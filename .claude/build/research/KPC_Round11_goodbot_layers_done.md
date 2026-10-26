# Round 11 results (good bot, Oct 26 2026 ~6:20 AM, tested) + HQ verdicts in [brackets]

## BLM Recreation Management Areas
- https://gis.blm.gov/arcgis/rest/services/recreation/BLM_Natl_Recs_poly/MapServer/0 | polygon | FET_NAME | 3,478 total; RMAs only: FET_SUBTYPE='SRMA' (1,108) or 'ERMA' (1,782) | BLM planning-area outlines, not a legal boundary
  [USE with the SRMA/ERMA filter; label 'official (BLM planning area)'; name match + pin, like other kind-'land' layers. Biggest single win: UT 281, ID 82, WY 72, NV 50 missing parks]

## National Historic Trails (NPS, one layer per trail; all at https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/<service>/FeatureServer/0; lines, no legal boundary)
- SAFE_NHT (Santa Fe) | TRNAME | 96
- TRTE_NHT (Trail of Tears) | TRNAME | 2,006  [KY! US-3791; busiest NHT]
- ELCA_NHT (El Camino Real de Tierra Adentro) | TRNAME | 5
- OLSP_CAS_Line_201801 (Old Spanish) | TR_NAME | 7
- BUOV_Congressionally_Designated_Alignment (Butterfield Overland) | TRNAME | 1,748
- JUBA_HistoricTrail_ln (Juan Bautista de Anza) | TRNAME | 3
- Lewis_and_Clark_National_Historic_Trail_Congressionally_Designated_Route | no name field (Exped_Seg, JOURNEY) | 62  [USE: one trail per layer, the layer itself names it]
- Selma_to_Montgomery_National_Historic_Trail_Official | TrailName | 1
- Sta_Spangled_Banner_National_Historic_Trail_Official_Centerline | Unit_Name | 1
- Overmountain_Victory_National_Historic_Trail_Official_Temp | TrailName | 43 | 'Temp'  [USE, label as provisional]
- Iditarod_National_Historic_Trail_BLM_Official_Temp | TrailName | 26 | 'Temp', BLM data  [USE, provisional]
- Ala_Kahakai_National_Historic_Trail_Official_Corridor | TrailName | 1 polygon corridor  [USE as an area]
- No name field, single unnamed line: OREG_NHT, CALI_NHT, POEX_NHT, MOPI_NHT, ELTE_NHT  [HQ: USE ANYWAY: one trail per layer, so the layer name IS the name (Oregon, California, Pony Express, Mormon Pioneer, El Camino Real de los Tejas)]
- NOT FOUND: Nez Perce, Washington-Rochambeau, Captain John Smith, the rest

## Wild and Scenic Rivers
- River lines, all agencies: https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_WildScenicRiverSegments_01/MapServer/0 | line | wsr_river_name | 249 rivers | designated centerlines  [USE for all 61 missing]
- NPS official corridor boundaries: https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/WildScenicRiverBoundaries/FeatureServer/0 | polygon | WSR_GNIS_NAME | 33 rivers | official, STATUS + Federal Register links  [USE FIRST where it exists (legal corridor), lines elsewhere]

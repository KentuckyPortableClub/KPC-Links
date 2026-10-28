# United Kingdom: WALES (desk, Oct 27 2026)
Grades: A = I opened and read it, B = search result only, C = inference. Read only; I could not query polygons. UK RULES: official sources first; WDPA never; a whole-line park (National Park, National Landscape/AONB, NSA, SSSI, SAC/SPA) is mostly private land, so a spot needs public land (World rules W-2/W-3: right to roam does NOT make land public); forests/MoD/charity land = "agency land" only with an ownership layer. Key = data/world-key/GB.json (7,074 parks, 2,804 with no outline, 1,073 pin outside the outline, 982 to check).
## 1. Official boundaries by park type
| Type | Layer | Publisher | Updated / licence | Read? |
|---|---|---|---|---|
| SSSI, NNR, LNR, National Parks, National Landscapes (AONB), Country Parks, SAC, SPA | Natural Resources Wales WFS / DataMapWales | NRW | OGL (B) | IN KEY (8 NRW layers) |
| **Open access (CRoW):** Open Country, Registered Common Land, Other Statutory Access Land | DataMapWales "Open Access - Open Country" / "Registered Common Land (CRoW Act)" / "Other Statutory Access Land" (metadata.naturalresources.wales NRW_DS100178, NRW_DS116536) (B) | NRW | OGL (B, not opened) | NO |
| Welsh Government woodland estate (managed by NRW) | NRW "Welsh Government Woodland Estate" (B, not opened) | NRW | OGL (B) | NO. The Welsh equivalent of Forestry England |
| Wales Coast Path / Offa\'s Dyke / Pembrokeshire Coast Path | NRW "Wales Coast Path" and Natural England-style trail lines (B) | NRW | OGL (B) | NO (GB-1120, GB-1122, GB-1113 NONE) |
## 2. No outline
Trail lines (Wales Coast Path GB-1120, Offa\'s Dyke GB-1122, Pembrokeshire Coast National Trail GB-1113); the Welsh names: **Eryri (Snowdonia) GB-0995 and Bannau Brycheiniog (Brecon Beacons) GB-0996 are joined, but older POTA names ("Snowdonia National Park", "Brecon Beacons") are the mismatch risk**: add the Welsh/English alias pairs. Gower AONB GB-0998 joined.
## 3. Trails / access: NRW trail lines (above). Rights of way: councils.
## 4. Tricky land
Wales has open country ("mountain, moor, heath, down, common") by statute; **most Welsh National Park land is private or common land** with grazing rights. Welsh Government woodland is public (agency land). Snowdonia includes Forestry (NRW) land and Snowdon summit (Snowdonia National Park Authority and NT). Pembrokeshire Coast NP includes NT and MoD land.
## 5. KNOWN-GOOD
NRW National Parks, NNR, LNR, SSSI (in key); CRoW open access layers; NRW woodland estate; Wales Coast Path.
## 6. 2-fers
Confident (C): Eryri NP GB-0995 vs its NNRs; Pembrokeshire Coast NP GB-0997 vs Gower-style coast NNRs. Hard: Gower Coast NNR GB-1055 vs Gower AONB GB-0998 (layered; NNR is public).

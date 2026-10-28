# United Kingdom: SUMMARY (chat 8 desk, Oct 27 2026)
Four nation files (England, Scotland, Wales, Northern Ireland). Read only. A = opened, B = search only, C = inference. Builds on World Preflight (KPC_2fer_Preflight_World_desk.md): UK first, W-2/W-3 apply.

## READY / GAPS
| Nation | Verdict | Why |
|---|---|---|
| England | READY for outlines, GAPS for ownership | six Natural England layers in key; no forest, National Trust or council layers; best ownership/access data in the UK exists but is unused |
| Scotland | GAPS | National Parks and National Scenic Areas not in key (Loch Lomond & The Trossachs NP GB-0930 is NONE); forest estate record is old |
| Wales | READY for outlines, GAPS for access | NRW layers in key; open-access and woodland estate layers unread |
| Northern Ireland | BLOCKED | DAERA terms bar publishing; keep all NI out (NOT SURE) |

## Top adds for chat 2
1. **Forestry England legal boundary** (OGL v3.0, updated 20 Feb 2026): https://www.data.gov.uk/dataset/forestry-england-legal-boundary (ArcGIS: https://data-forestry.opendata.arcgis.com/datasets/92ae032e23a747859630ccb662d853ee_0). Gives the public-body owner for rule 14. Page does not say owned vs leased.
2. **CRoW Access Layer** (Natural England, updated 29 Apr 2026): https://ckan.publishing.service.gov.uk/dataset/crow-act-2000-access-layer2. Licence field says "No Licence Provided"; ask Natural England before storing. Wales equivalents on DataMapWales (Open Country, Registered Common Land).
3. **National Trust Always Open / Limited Access** (ArcGIS FeatureServer/50 on services-eu1.arcgis.com/0zuv5ZFEncBv7NQQ, 2023): charity land with legal foot access; best added with a note "charity, not a public body" (UK-1).
4. **NatureScot National Parks + National Scenic Areas**: fixes GB-0930 and 136 Scenic Sites.
5. **FLS national forest estate** (OGL, spatialdata.gov.scot record cb43b17d…): record covers 2008-2019, so re-check for a current copy.
6. **National Trails (England)** (15 trails, updated 15 May 2026): https://services.arcgis.com/JJzESW51TqeY9uat/ArcGIS/rest/services/National_Trails_England/FeatureServer; plus Scotland\'s Great Trails and the NRW Wales Coast Path: ~359 trail "parks" have no outline.
7. **OS Open Greenspace** (GB, updated April/October): for the 1,144 council "Parks". Council parks are "never" per Brandon, so use only to tell chat 2 which unjoined "Parks" are council ones (drop) vs. regional parks.
8. **Welsh Government woodland estate** (NRW) and **Natural England National Parks name aliases**.
9. Water: OS Open Rivers (B) and the Environment Agency / NRW / SEPA lake layers: lochs and Lake District meres are water-only (rule 9).

## Name mismatches (look missing, probably not)
- "Thames Basin Heaths SPA - Hawley Common SSSI" style: a European label before the real site name (GB-0015, 0172, 0188, 0198, 0248, 0259, 0309): strip "SPA -", "SAC -", "Ramsar -", match the SSSI/NNR name.
- Welsh/English twins: Eryri (Snowdonia) GB-0995, Bannau Brycheiniog (Brecon Beacons) GB-0996; also Welsh place names in NNR/SSSI lists.
- Country Park names with "Common/House/Estate" suffix added in POTA (Billesley Common Country Park GB-0365).
- Lundy Island NNR GB-0322.
- Scotland: "Scenic Site" in POTA = National Scenic Area.
- US-style labels the key gives some UK parks ("National Park" for Glenariff, Castle Ward; "National Historic Trail" for Pembrokeshire/West Highland Way) are POTA\'s own: do not trust the type.
- 1,073 pins fall outside their outline: often the pin is on the car park of a country park whose layer is the reserve core.

## NEW grey areas for Brandon (UK-1 to UK-6)
| # | Question | My lean |
|---|---|---|
| UK-1 | **Charity land with public access** (National Trust inalienable land, RSPB reserves, Wildlife Trust reserves, community buy-outs): count as public land for rule 2? | Yes for National Trust "Always Open" and reserves open daily; otherwise NOT SURE. Not a "public body" but open to all. |
| UK-2 | **Common land and CRoW open country** (Dartmoor commons, Scottish "right of access"): you can walk but the owner is private. Counts? | No (W-3): "check you may be there" note, public bodies' land only. |
| UK-3 | **MoD training land** (Salisbury Plain Protected Area GB-0285, Dartmoor ranges, Otterburn): public body owns it, but access only when not firing. | Count as public land but always add the closure line; or NOT SURE. |
| UK-4 | **National Scenic Trails / Great Trails**: lines across private and public land; 359 "parks". | Line parks, rule 8; only the public sections on a mapped right of way. |
| UK-5 | **Overlapping Natura labels** (SAC/SPA/Ramsar/SSSI/NNR on the same ground, e.g. Thames Basin Heaths): "same land, two park numbers" everywhere. | Show with that label, one row per patch (W-6). |
| UK-6 | **Northern Ireland**: leave out until DAERA permission, or ask NIEA now? | Keep out; HQ/Brandon can ask NIEA for written permission. |

## What is solid, what is not
Solid (A): Forestry England record (OGL, Feb 2026), FLS record (OGL, old coverage), LNR record (OGL v3, updated July 2026), National Trails (England) dates/formats, OS Open Greenspace contents/update cycle, NI NNR record (no licence stated), NT Always Open description. Not solid: CRoW layer content and licence; NatureScot/NRW licences and layer names (B); the Welsh woodland estate and open-access layers; whether the Forestry England boundary is owned or leased; every 2-fer prediction.

## Note from chat 2's world harvester (Oct 27 ~11 PM)
- The 'Forestry England' address in these files, `services-eu1.arcgis.com/0zuv5ZFEncBv7NQQ/…/Core_Data_Non_WMS/FeatureServer/50`, belongs to the ArcGIS Online organisation **'GoBe Consultants'**, a consultancy, not Forestry England. The bot refused it as not official. Forestry England's own legal-boundary layer should be looked for under Forestry England's / the Forestry Commission's own organisation (data-forestry.opendata.arcgis.com is their Hub; its service host is a different org id). Chat 8: please re-find the official address.


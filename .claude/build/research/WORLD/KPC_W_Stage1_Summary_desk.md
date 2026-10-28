# WORLD STAGE 1 SUMMARY (desk, Oct 27 2026)
Grades: A opened and read, B search only, C inference. Read only. One file per country in this folder (KPC_W_<CC>_desk.md; Baltic pack = KPC_W_BALTIC_desk.md). WDPA never used.

## Per country
| W | Country | Outlines | Owned-land data (rule 14) | Status |
|---|---|---|---|---|
| 1 | GB | good (4 nations) | Forestry England (OGL), NT, CRoW; NI blocked | READY England/Scotland/Wales, NI not |
| 2 | AU | CAPAD (licence unclear) | NSW, VIC, WA tenure layers (CC BY) | READY after adds |
| 3 | JP | MoE 2023 layer, licence unstated | none | NOT READY (pairs NOT SURE) |
| 4 | DE | BfN | none usable | NOT READY for public pairs |
| 5 | PL | GDOŚ | **Lasy Państwowe BDL by ownership** (licence unstated) | READY after adds |
| 6 | FR | INPN | ONF licence unspecified | GAPS |
| 7 | ES | MITECO Red Natura Dec 2025 | none | NOT READY |
| 8 | IT | EUAP | none | NOT READY |
| 9 | NO | Naturvern NLOD, Feb 2026 | **statlig sikra friluftsliv** | READY |
| 10 | NL | PDOK (RVO) | none open | outlines READY, ownership no |
| 11 | CH | BAFU | none national | outlines READY after Pärke add |
| 12 | PT | ICNF POAP | none found | NOT READY |
| 13 | RO | EEA only | none | NOT READY (half the list is not protected land) |
| 14 | AT | per Land | none (ÖBf not found) | NOT READY |
| 15 | SE | **Naturvårdsregistret CC0** | national parks = state land (A) | READY for national parks |
| 16 | SI | EEA | none | NOT READY |
| 17 | CZ | EEA / AOPK | none | NOT READY for ownership |
| 18 | BE | EEA | **Flanders ANB lands** | READY Flanders only |
| 19 | DK | Fredede områder | none | NOT READY |
| 20 | IE | NPWS | **Coillte CC BY 4.0** | READY after adds |
| 21 | SK | EEA | none | fix 9 national park joins first |
| 22 | HR | INSPIRE WFS | none | READY after 3 name fixes |
| 23 | FI | EEA | Metsähallitus data restricted | NOT READY (ask them) |
| 24 | HU | EEA | none | NOT READY (strict-zone secrecy) |
| 25 | EE LV LT LU | EEA | **LU public forests CC0**; EE RMK maybe | LU READY; others outlines only |

## Top adds (cheapest, biggest gain)
1. Sweden Naturvårdsregistret (CC0; fixes 697 pins outside).
2. Poland BDL ownership WMS/WFS + Ireland Coillte + Luxembourg forests + Flanders ANB + Norway statlig sikra + AU state tenure: the six real public-land layers outside the UK.
3. Netherlands PDOK Nationale Parken; Croatia INSPIRE WFS; Switzerland BAFU Pärke.
4. Name-join fixes (no new data): SK national parks, HR 3 national parks, FI "luonnonsuojelualue" suffix, NL De Peel, BE accents.
5. Pin-only (never run): RO/SI/SK/AT/HR city parks, historic sites, castle parks, local walks (≈1,500 numbers across RO, SI, SK).

## NEW grey areas with my lean (UK-1..6 are in the UK summary)
- W2-1..4 (AU), W3-1..3 (JP), W4-1..2, W5-1..2, W6-1..3, W7-1..2, W8-1..2, W9-1..2: in each country file.
- W10-1 / W18-1: NGO reserves open to all (Natuurmonumenten, Natuurpunt). Lean: count if open daily without membership, else NOT SURE.
- W11-1: Swiss federal inventory objects on private land. Lean: whole-line rule W-2.
- W12-1: Portuguese Matas Nacionais labelled "National Park". Lean: judge by the land (state forest).
- W13-1: Romania ≈ 500 non-protected numbers. Lean: pin-only.
- W14-1: Vienna Bundesgärten. Lean: never (historic).
- W15-1: Swedish trail sections as parks. Lean: line rules.
- W16-1: Slovenian walks and monuments. Lean: pin-only.
- W19-1: Danish fredning on private dunes. Lean: W-2.
- W20-1/2: Coillte forests labelled National Park/Forest Reserve; CC BY with commercial-permission note. Lean: state forest; OK for KPC.
- W23-1: Finnish State Nature Preserve (public) vs private reserve (keep out). Lean: yes.
- W24-1/2: Hungarian strictly protected zones with non-public borders (do not show or count); 91 Blue Trail sections as parks. Lean: exclude zones; lines.
- W25-1/2: Estonian RMK recreation areas; communal forests count as public (with France W6-1).

## What I could not do
No polygon queries; several portals would not open (B grades). Licence lines missing for many layers: ask each publisher before any bot uses them.

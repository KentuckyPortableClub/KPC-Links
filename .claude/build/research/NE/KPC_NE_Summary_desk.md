# Region 3 NORTHEAST: SUMMARY (chat 8 desk, Oct 27 2026)
Files KPC_NE_<ST>_desk.md for PA NY NJ CT RI MA VT NH ME MD DE. Read only. Grades A/B/C; I could not query polygons. The Northeast files are thinner than the Southeast ones: several states hold only one or two key layers and I read fewer of the services.

| State | Parks / no outline | Verdict | Main reason |
|---|---|---|---|
| PA | 494 / 15 | READY after one add | state forest layer missing from key; 4 private conservation areas |
| NY | 850 / 27 | GAPS | Adirondack and Catskill "parks" (blue line regions); NPS Gateway units mis-typed; OK otherwise |
| NJ | 134 / 9 | GAPS | no parking/trail layers; Pinelands region; Garret Mountain is a county park |
| CT | 157 / 12 | READY | name mismatches |
| RI | 61 / 5 | READY | name mismatches |
| MA | 421 / 14 | READY | urban DCR parks, mismatches |
| VT | 109 / 18 | **GAPS (easy fix)** | key lacks the ANR state parks layer; 14 of 18 are state parks |
| NH | 205 / 14 | READY | mismatches; trails layer to add |
| ME | 148 / 12 | READY | one layer; mismatches |
| MD | 186 / 19 | GAPS | no parking/trails; city watershed and NPS heritage sites |
| DE | 89 / 11 | READY | best layered; rail-trail lines missing |

## Top adds for chat 2
1. **VT ANR Land Dataset (Unit)**, anrmaps.vermont.gov …/OPENDATA_ANR_CADASTRAL_SP_NOCACHE_v2/MapServer/38 (A; CC BY-SA 4.0, updated 2022): fixes 14 parks
2. **PA State Forests**, gis.dcnr.pa.gov/agsprod/rest/services/BOF/State_Forests/MapServer (A item page)
3. **NY DEC Lands** reference/MapServer/2 has CATEGORY (A) – use it to separate Forest Preserve from State Forest
4. **MD_ProtectedLands** (geodata.md.gov, A) for owner types
5. NH GRANIT Recreational Trails lines (B)
6. CT DEEP Areas Open for Hunting (B)
7. MA/CT/RI: strip suffixes like "State Park", "Wildlife Management Area" before matching
8. DE rail trails, NJ parking/trails, MD parking/trails (to find)
9. NPS Land Resources boundary for Gateway NRA, Delaware Water Gap, C&O Canal, Cape Cod (NPS layer in key only in some states)

## Name mismatches (look missing, only named differently)
NY: Crystal Lake SF, Dannemora SF, Split Rock SF, Iona Island, Thompsons Lake, Barcelona Neck, Jamaica Bay SWA. CT: Ferry Landing, Beckley Iron Furnace, Satan's Kingdom, Comer Memorial. RI: Hillsdale Preserve, Silver Spring, Beach Pond, Rome Point. MA: Rockdale Heights, Greycourt, Lynn Shores, Farnham-Connolly, Martini, Pope John Paul II. NH: Androscoggin Wayside, Gardner Memorial Wayside, Winslow, Max Israel, Nash Stream, White Farm, Wantastiquet, Gov. Wentworth, Taylor Saw Mill. ME: Little Ossippee, Dresden Bog, Bog Brook, Capitol SP, two ecological reserves. MD: Sideling Hill Creek, Idylwild, Monocacy, Sassafras, Heaters Island. DE: Masseys Millpond, Trussum Pond. VT: all 14 state parks (wrong layer, not a naming issue). PA: none.

## NEW grey areas (only)
| # | Question | Lean |
|---|---|---|
| NE-1 | **Adirondack and Catskill "State Parks"** (US-2001, US-8070): blue-line regions with private land. Count only DEC Forest Preserve/State Forest ownership inside? | Yes, agency-owned land only (your national forest rule). |
| NE-2 | **Private nature reserves listed as State Conservation Areas** (PA 4 sites: Audubon / WPC) | Not park land except own number (like SE-2). |
| NE-3 | **City watershed cooperative WMAs** (MD Frederick City) | By agreement (SE-2). |
| NE-4 | **NPS heritage sites / corridors** (Erie Canalway, Baltimore-Washington Pkwy, Pinelands NR, MD heritage sites) | No polygon rule: pin only (SE-7). |
| NE-5 | **State-held easements** on private forest (VT, ME) | Not park land. |
| NE-6 | **Mis-typed POTA names** (Garret Mountain "State Park" is county; Gateway "State Recreation Areas" are NPS) | Use the owner from the layer, not the POTA type. |

Corps-lake and watershed cases follow SE-1 / SE-5.

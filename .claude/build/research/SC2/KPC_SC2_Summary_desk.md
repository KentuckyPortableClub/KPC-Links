# Region 4 SOUTH CENTRAL: SUMMARY (chat 8 desk, Oct 27 2026)
Files KPC_SC2_<ST>_desk.md: AR LA OK TX KS NE. Read only; grades as before. I read fewer live services here; several came back "not started".

| State | Parks / no outline | Verdict | Main reason |
|---|---|---|---|
| AR | 304 / 54 | GAPS | AHTD public land + ARKANSAS_TRAILS unread; 15 "trails" are scenic byways (roads) |
| LA | 123 / 8 | **GAPS** | no state parks layer found |
| OK | 205 / 62 | GAPS | 22+ historic sites/museums with no layer; WMAs on Corps/military land |
| TX | 222 / 20 | READY | 10 historic sites name suspects; Fairchild SF uncovered |
| KS | 145 / 27 | GAPS | 14 historic sites; KARS service down; trails |
| NE | 196 / 21 | READY (questions) | city/NRD parks next to state SRAs |

## Top adds for chat 2
1. AR PUBLIC_LAND_BOUNDARIES_AHTD (Planning_Cadastre/MapServer/16, A)
2. AR ARKANSAS_TRAILS (Environment/MapServer/22, A)
3. TX Texas_State_Parks_Boundaries + WMA_Boundaries_4PublicDistribution FeatureServers (B)
4. LA Office of State Parks boundaries: find (bot task)
5. KS KARS Protected_Areas (retry when it restarts)
6. NE open data portal data-outdoornebraska.opendata.arcgis.com (A)
7. Corps lake project lands (AR, OK, TX, KS, NE)
8. Historic site lists for OK/KS/ND/TX: decide first (SC2-2)

## Name mismatches
TX: all 11 State Historic Sites. NE: nine Omaha/Lincoln SRAs. OK: WMAs (Carl Blackwell, Selman, Camp Gruber, Sparrow Hawk), fishing lakes. AR: Muddy Creek WMA, state recreation areas on lakes. KS: Cross Timbers SP.

## NEW grey areas
| # | Question | Lean |
|---|---|---|
| SC2-1 | **Scenic byways listed as "State Trail"** (AR 15, OK Cherokee Hills/ Talimena): roads. Treat as trail lines or drop? | Drop as polygons; pin/line only, ask Brandon. |
| SC2-2 | **State historic sites and museums** (OK 22, KS 14, TX 11, ND 36): "never" for markers, but these are state-run sites. Pin only? | Pin only (same as SE-7/MW-2). |
| SC2-3 | **Natural Resources District (NE) and city parks next to state SRAs.** Local land. | Not state; follow your "council and city parks = never". |
| SC2-4 | **Military/university WMAs** (OK Camp Gruber, Carl Blackwell): public by permit. | By agreement (SE-2). |
Corps-lake cases follow SE-1/SE-5.

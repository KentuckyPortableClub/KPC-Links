# Fable book: US-IA (4 rows, 2 parks)
HANDOFF (chat 3, Oct 30): Fable work moves to CHAT 8. Teal Basins (US-9334) name+pin match to 'Teal Basins WPA' 151 ac (USFWS) -> WAITING chat 2 trace -> chat 11 yes/no. Other IA rows: step 0 + P-2 done.
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-IA.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-9334 | | PAD-US at pin: Cerro Gordo County Waterfowl Production  (RMA, owner FWS/FED, manager FWS, 2719 ac, Fee, PAD id 3710); Cerro Gordo County Waterfowl Production  (RMA, owner FWS/FED, manager FWS, 2719 ac, Fee, PAD id 4644) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-9334 | Teal Basins State Waterfowl Management Area | look-up 9-p2-ia (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): TEAL BASINS WPA 151 ac [Public Hunting Areas, USFWS] *name; Teal Basins WPA 151 ac [Public Areas, FWS] *name. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-9334 IA | Teal Basins State Waterfowl Management Area | https://www.arcgis.com/apps/webappviewer/index.html?id=f9161b90cddb4fcfb35a96901882a4b7&query=Atlas_Web_Application_4143_1966%2CAREA_NAME%2CTEAL%20BASINS%20WPA | ⚠ NEARBY OFFICE, not the area: Iowa DNR, 6200 Park Ave Suite 200, Des Moines, IA 50321 | to read | 43.2137, -93.4424 |
| US-9334 IA | Teal Basins State Waterfowl Management Area | chat 9 found **'Teal Basins WPA' 151 ac** (Iowa Public Hunting Areas layer, USFWS; also in the FWS Public Areas layer): proper words match ('Teal Basins'; kind words 'State Waterfowl Management Area' / 'WPA' stripped, T-1). Pin is inside. PAD-US at the pin says 'Cerro Gordo County WPA' 2,719 ac (a larger FWS unit, same land owner FWS): that is a container, not the park. | R-G7 step 2 name+pin match, agency = USFWS/Iowa DNR | **READY FOR chat 2 TRACE** of the 151-ac 'Teal Basins WPA' polygon, then chat 11 yes/no. Website name = WPA (FWS). |

Chat 8 (Oct 30): confirmed T-1 match on Teal Basins WPA, only open IA park. Handed to chat 2 for trace. **STATE IA DONE** (1/1 resolved: trace candidate).

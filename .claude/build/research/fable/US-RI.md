# Fable book: US-RI (4 rows, 2 parks)
HANDOFF (chat 3, Oct 30): Fable work moves to CHAT 8. Hillsdale (US-10545): pin only inside deCoppet Preserve 1,825 ac (container, no shared name) -> needs Richmond RI town parcel (45 ac, DEM); parcel look-up NOT filed (format unknown to chat 3).
ONE ROW PER PARK from now on: update the park's row in place (add to its cells), don't add a new row. Read the Agency Atlas first: .claude/build/research/agency-atlas/US-RI.md

| park | name | source found | Rule G step | result | by chat | date |
|---|---|---|---|---|---|---|
| US-10545 | | PAD-US at pin: Beaver River - deCoppett (SOTH, owner SDNR/STAT, manager UNK, 1825 ac, Fee, PAD id 57103); Decoppet Estate (SOTH, owner SDNR/STAT, manager SDNR, 1825 ac, Fee, PAD id 78857) | R-G7 step 4b (owner) | owner listed; Rule G decides | 2 | Oct 29 |
| US-10545 | Hillsdale Preserve Management Area | look-up 9-p2-ri (state-gis.json layers + BLM rec polygons, FWS approved, NPS legal boundary) | R-G7 step 2 (point at the pin) | P-2 hit(s): deCoppet Preserve 1825 ac [State Conservation Land] *name; deCoppet Preserve 1825 ac [ENV_Conservation_Lands_State] *name. LEAD only: a polygon at the pin is not a name match; R-G7 decides; pin unchanged | chat 9 | 2026-10-29 |
| US-10545 RI | Hillsdale Preserve Management Area | https://dem.ri.gov/press-releases/dem-forest-restoration-project-aims-future-proof-45-acre-parcel-richmond-effects | to read | to read | 41.522, -71.6411 |
| US-10545 RI | Hillsdale Preserve Management Area | chat 9: only polygon at the pin is **deCoppet Preserve 1,825 ac** (State Conservation Land, owner RI DEM): NO shared proper word ('Hillsdale' vs 'deCoppet') -> a container, ownership only (T-1). RIDEM's own page: a **45-acre parcel in Richmond** (forest restoration project). | R-G7 step 4b candidate: owner = DEM, parcel needed | **needs-parcel**: Richmond, RI town parcel at the pin (45 ac, owner State of RI/DEM); P-3 one request for Richmond. Address: RIDEM HQ 235 Promenade St is the OFFICE, not the preserve. |

Chat 8 (Oct 30): found RIDEM's own statewide Tax_Parcels layer (RIGIS, risegis.ri.gov/hosting/rest/services/RIDEM/Tax_Parcels/MapServer/0 -- state agency, not county-by-county, so one layer covers it); filed look-up `8-parcel-ri` (point test at the pin). Only open RI park; **STATE RI DONE** (1/1: needs-parcel, filed, awaiting answer).

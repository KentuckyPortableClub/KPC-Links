# Who runs the parks outside the US + Canada, and where their GIS lives (chat 8, Fable, Oct 29 2026 ~10:15 PM; Brandon 9:51 PM side project)
Data file: `world_agencies.json` (42 POTA countries: agency name in the local language + English, its portals, the native park words, a grade). Everything marked grade C is from chat 8's own knowledge and must be opened before it is trusted; A/B = a probe or a lead already opened it.

## Rule W-9: Protected Planet is a phone book, nothing more (Brandon Oct 29 9:51 PM: 'reading Protected Planet for the agency's name')
1. From Protected Planet (WDPA, protectedplanet.net) we read ONE thing: the name of the agency that manages the park / supplied the country's data (the park page's 'Management Authority' and the country page's 'Sources' list).
2. We write that name down (local language + English) and go to the AGENCY'S OWN site. Nothing else from Protected Planet is read, drawn, stored, linked or credited; its boundaries stay out (second-hand, simplified, old).
3. Protected Planet pages are script-filled: a text reader sees nothing. Read them with the look-up bot (headless browser) or by hand in a real browser.
4. Any agency found this way is still graded like every other source (official site, licence line, polygons with a name field) before chat 9 seeds it.

## Note for Sonnet (chat 8's usual model): what to search, in this order, one country at a time
1. **Our own files first:** `world_agencies.json` (this folder), the country's `KPC_W_<CC>_desk.md` source book, `data/world-gis-sources.json`, and chat 9's `data/harvest/leads-<CC>.json` (KPC-Data). If the agency + a working portal are there, skip to step 5.
2. **Agency name:** take it from `world_agencies.json`; if the country is missing or the name is doubtful, file ONE look-up request for the Protected Planet country page (`https://protectedplanet.net/en/country/<ISO3>`) and read only the 'Sources' names (rule W-9).
3. **The country's open-data / INSPIRE portal first** (research order): search it for the native park words in `world_agencies.json` ('park narodowy', '国立公園', 'parc national' …) + the agency's abbreviation. EU countries: the INSPIRE 'Protected Sites' (PS) theme on the national geoportal is usually the official polygon set.
4. **The agency's own site** 'maps / data / geoportal / WFS / download' page; then ArcGIS Online (search `orgid:` of the agency's organisation); only then a plain web search (agency name + 'WFS' / 'shapefile' / 'open data' in the local language).
5. **Grade it:** official publisher (the managing agency or the national mapping/environment agency), an open licence line, polygons with a name field, a date. Write ONE line per layer for chat 9: `CC | kind (park/wild/forest/land/trail) | agency | name field | licence | address`.
6. **Hand-off:** put the lines in `.claude/inbox/chat-9.md` under OPEN as `FROM CHAT 8 (date):`, add the agency words to `world_agencies.json`, log the probe in the Canada/US-style 'GIS LAYERS WE PULLED' row of the country's source book. No world 2-fers (SCOPE): outlines, official documents and maps only.
7. **Pin-only countries** (no open official polygon service: today RU, CN, probably TH/PH/DO/TR): say so in one line, keep the agency name and page link for the documents bot, move on.

## Where the holes are (from chat 9's harvester, Oct 29 run)
- Nothing or almost nothing found yet: AR AT BR CH CN CZ DO EE HR HU IT JP KR LT LU LV MX PH RO RU SI SK TH TR ZA (band A+B+C = 0-1).
- Strong already: GB NZ AU PT NO ES NL FR DK.
- JP lead worth checking first: MLIT 国土数値情報 A10 (natural park areas) is the official polygon set and newer than the 2010 layer in the notes.

## First look-up filed
`8-pp-agencies` on the lookup branch: 24 Protected Planet country pages (the weak countries) + the MLIT A10 page, to confirm the 'Sources' agency names against this table.

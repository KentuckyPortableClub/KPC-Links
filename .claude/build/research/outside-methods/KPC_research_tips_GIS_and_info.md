# Tips for finding official GIS layers and park information (KPC)

From the Oct 31, 2026 hours/fees/closures build (13,083 US and 5,918 Canada parks). Companion to KPC_hours_fees_closures_METHOD.md.

## 1. Official sources only
- Use government agencies or the actual site operator. Skip Google results pages, Wikipedia, AllTrails, TripAdvisor, blogs, directories and resellers. Never use search snippets as a source.
- Check ownership: the domain should be the agency's (.gov, .gc.ca, gov.bc.ca, a city or a province), and the page title should match the park.
- Follow handovers. Parks change owners (a state to a city, for example), so use the current owner's page.
- A heritage register or designation list isn't a visitor page. Find the operator, such as Parks Canada, a province, a city or a museum society.

## 2. Work agency by agency
- Group rows by agency or domain and do the biggest first. One agency-wide page or GIS service often covers hundreds of parks.
- Write "agency-wide page" in Notes when one source covers many parks.

## 3. Finding GIS layers
- ArcGIS REST directories: try https://<host>/arcgis/rest/services and browse the folders. Common hosts are gis.<agency>.gov and services.arcgis.com/<orgId>.
- Add ?f=json to a layer URL to confirm its fields, geometry type, owner and copyright text before trusting it.
- Open-data hubs: the agency's ArcGIS Hub or open-data page usually links straight to the FeatureServer. Check the "Source" or "Owner" so it's the agency, not a hobbyist copy.
- Federal sources: PAD-US (USGS) for protected areas, NPS, USFS, BLM, USFWS and USACE each publish their own layers. In Canada, try Open Government (open.canada.ca), the CPCAD protected-areas layer and the provincial geohubs.
- Query a layer with a where clause and outFields=* to pull attributes. Use a resultOffset loop for large layers.

## 4. Finding pages built by scripts
- Many pages fill in their content with scripts, so a plain fetch looks empty. Look for the public data file behind them.
- Example: NPS has a public, keyless data file at https://www.nps.gov/<code>/structured_data_<code>.json, with operating hours.
- Old dead PDF links, such as the Forest Service ones, usually have a current page on the same site. Search inside the agency's own site.

## 5. How to read sites, in order
1. A plain script fetch: fast, parallel and cached.
2. The WebFetch tool for sites that block scripts. Keep a list of the domains that need it.
3. A browser pass for whatever is left. Make a targets CSV (row, park, official start URL, rows sharing that page). The browser agent copies text word for word, records the URLs from the address bar into a results CSV, and then you merge it.
4. If it's still blocked, leave the row blank and log it to blocked_rows.csv with the domain, row and reason. Retry at the end. Never mark it NOT FOUND unless the page was actually read.
- Never spoof a user agent, click through a certificate warning, sign in, or get around JavaScript or robot checks.

## 6. Bad links in the source data
- Expect dead links, moved pages, typos ("idaho.goc", a missing ".com") and links to the wrong park.
- Don't edit the source column. Put the verified correct page in Notes, in the form "Column F link wrong/dead; correct official page: <URL>", and log it to a fixes CSV.

## 7. Accuracy rules
- Copy text word for word, in the original language. Never turn prices into a range yourself; if the agency writes a range, copy it.
- Never guess a URL. Every link written must open.
- A general line, such as statewide tennis court rules or a tourist office's hours, goes in Notes, not in the park's fields.
- Standard wording: "not stated on the agency page", "no fee", "open all year, no hours stated".

## 8. Quality control
- Checkpoint every ~200 rows: save, copy to a checkpoint file and log progress.
- Before delivery, check that every URL opens, compare the identity columns to the original data (expect 0 mismatches) and spot-check 20 random rows.
- Watch for page boilerplate copied into cells, and for prices or hours taken from the wrong site.

## 9. Deliverables
- The filled workbook, the fixes CSV and blocked_rows.csv, so anyone can retry the blocked rows later.

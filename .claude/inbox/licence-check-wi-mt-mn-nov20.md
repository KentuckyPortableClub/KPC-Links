# Licence check: Wisconsin DNR, Montana State Library, Minnesota DNR

Independent, read-only check of each agency's own official terms, disclaimer, and data-use pages. Read 20 November 2026, late morning America/Chicago. No spatial data layers were downloaded. No one was contacted. Quotes are copied from the official pages named below.

This checks another agent's readings of six unlicensed sources (four Wisconsin DNR layers, one Montana State Library layer, one Minnesota DNR layer) that were proposed for publication with credit.

## Verdicts in short

| Agency | Other agent's reading | This check | Firm verdict |
|---|---|---|---|
| Wisconsin DNR (managed properties, managed-land parcels, and WSPS property boundaries) | "No licence, nothing granted or forbidden; an as-is disclaimer only." Propose publish with credit "Wisconsin DNR". | Mostly accurate for these public items: official licence boxes are disclaimer-only and bind the user to Legal Notices, not to a redistribution ban or a Creative Commons grant. | **YES publish with credit** "Wisconsin Department of Natural Resources" (add the bureau named on the item: Facilities and Lands, or Parks and Recreation Management). |
| Wisconsin DNR — State Natural Areas layer on the public "Managed Lands" service (SNAs) | Same "no licence / as-is only" claim if this is one of the four. | Accurate that there is no licence grant: the service `licenseInfo` is empty; the layer's copyright text is only "WDNR-ER". No ban was found on this service. | **YES publish with credit** "Wisconsin DNR" / "WDNR-ER". Thinner than the managed-properties items, because this service has no disclaimer text of its own. |
| Wisconsin DNR — Natural Area Parcel Ownership | Would be inaccurate if this was counted among the four "no licence" layers. | The layer itself tells external users to ask before using it. | **NO** until the Bureau of Natural Heritage Conservation, State Natural Area program, agrees to dissemination. |
| Montana State Library — Montana Managed Areas (MSDI) | "For informational purposes only, nothing on copying." Propose publish with credit. | The "informational purposes only" disclaimer is real, but "nothing on copying" is not. Current official metadata still says to refer other people to the Montana Natural Heritage Program rather than distribute the data to second parties. | **YES with conditions**: publish only the park outlines used (parts), with credit to Montana State Library and Montana Natural Heritage Program; do not republish the full Managed Areas dataset; point anyone who wants the source data to MSL/MTNHP; show as reference only, not legal boundaries, and do not imply public access. |
| Minnesota DNR | "Parts may be shared with credit, but not the layer in its entirety for commercial purposes or otherwise." Propose publish the 2 records used (parts only), with credit. | Accurate. That is the current official General Data and Software License Agreement. | **YES with conditions**: publish only the records used (parts / a derivative), not the layer in its entirety; acknowledge MNDNR; do not use MNDNR logos; show as reference only, not legal boundaries. KPC is non-commercial; a commercial use would need DNR's commercial-use form. |

No Creative Commons (or other standard open-data) licence was found on the official layer or agency terms pages read today.

---

## 1. Wisconsin DNR

### Official pages read

- Legal Notices: https://dnr.wisconsin.gov/legal
- Acceptable Use Policy (website, not GIS): https://dnr.wisconsin.gov/legal/acceptableuse
- Get GIS Data: https://dnr.wisconsin.gov/maps/GetGISData
- DNR GIS Open Data Portal home: https://data-wi-dnr.opendata.arcgis.com/
- Official Open Data / ArcGIS items (owner `Wi_DNR_Data`, org Wisconsin Department of Natural Resources):
  - DNR Managed Properties, item `0400005343db41bd850043f9f5f9176b`: https://www.arcgis.com/home/item.html?id=0400005343db41bd850043f9f5f9176b (JSON: https://www.arcgis.com/sharing/rest/content/items/0400005343db41bd850043f9f5f9176b?f=json). Same service as KPC `sgwia` / `wid`.
  - DNR Managed Land Parcels, item `7a03fc1c86f34298a3d79c6a62f96141`: https://www.arcgis.com/home/item.html?id=7a03fc1c86f34298a3d79c6a62f96141 (JSON: https://www.arcgis.com/sharing/rest/content/items/7a03fc1c86f34298a3d79c6a62f96141?f=json). Same service as KPC `sgwid`.
- Official map-service iteminfo (terms only, no features downloaded):
  - WSPS properties (`sgwib`): https://dnrmaps.wi.gov/arcgis2/rest/services/PR_Recreation/PR_WSPS_Property_Info_WTM_Ext/MapServer/info/iteminfo?f=pjson
  - SNAs (`sgwic`): service https://dnrmaps.wi.gov/arcgis/rest/services/ER_Biotics/ER_Biotics_WGS84_Managed_Lands/MapServer/info/iteminfo?f=pjson and layer 1 metadata `?f=pjson`
  - Natural Area Parcel Ownership (`sgwif`): service https://dnrmaps.wi.gov/arcgis/rest/services/LF_DML/ER_DNR_NA_StateNaturalAreas_WTM/MapServer/info/iteminfo?f=pjson and layer 2 metadata `?f=pjson`

Hub dataset pages on `data-wi-dnr.opendata.arcgis.com` are script-rendered and returned no usable licence field in this fetch. The official ArcGIS item `licenseInfo` and the map-service `licenseInfo` / layer descriptions are the licence text used here. The portal home page does not name a Creative Commons (or other) licence for the datasets; it says the data "are offered as-is and may be changed or removed at any time."

### Exact sentences that matter

**Legal Notices** (https://dnr.wisconsin.gov/legal):

> "The state provides this information on an "as is" basis."

> "Maps are not intended to be used for navigation, nor are maps an authoritative source of information about legal land ownership or public access."

> "By use of this system and any data contained therein, the user agrees that use shall conform to all applicable laws and regulations and user shall not violate the rights of any third parties."

That page is a disclaimer of liability and accuracy. It does not grant a licence, and it does not forbid copying or redistribution.

**Get GIS Data** (https://dnr.wisconsin.gov/maps/GetGISData):

> "Most geospatial data available from this portal can be downloaded free of charge."

> "DNR programs create and maintain a wide variety of geospatial data sets to support specific activities and services, and they may have different requirements for providing access to their data."

So there is no single site-wide GIS licence; each item still has to be read.

**Open Data Portal home** (https://data-wi-dnr.opendata.arcgis.com/):

> "The data and resources on this site are intended for short term access and/or download. They are offered as-is and may be changed or removed at any time."

**DNR Managed Properties and DNR Managed Land Parcels** (same `licenseInfo` on both official items; credit field: "Wisconsin Department of Natural Resources; Bureau of Facilities and Lands"):

> "This data is for informational purposes only and is not to be interpreted legal boundaries, nor is it suitable for engineering or surveying purposes. The user is solely responsible for verifying the accuracy of information before using for any purpose. By using this product for any purpose user agrees to be bound by all disclaimers found here: https://dnr.wisconsin.gov/legal."

**WSPS property boundaries** (official `PR_WSPS_Property_Info_WTM_Ext` service `licenseInfo`; credit field: "Wisconsin Department of Natural Resources - Parks and Recreation Management"):

> "This data is for informational purposes only and may not have been prepared for or be suitable for legal, engineering or surveying purposes. The user is solely responsible for verifying the accuracy of information before using for any purpose. By using this product for any purpose user agrees to be bound by all disclaimers found here: https://dnr.wisconsin.gov/legal."

Do **not** substitute the look-alike hosted layer "PR: WI State Park System Properties - layer" (item `6706a3b94bb5490ea20f6799ca3cbc7f`), whose licence says: "For use within the Wisconsin Department of Natural Resoures' Point of Contact Viewer only." and "This item is intended solely for use in the Department of Natural Resources' Point of Contact Viewer web map and application and is subject to change or removal at any time without notice. Use in other maps and apps without authorization is not recommended." That is a different service.

**SNAs layer** (`ER_Biotics_WGS84_Managed_Lands`, layer 1 "SNAs"): service `licenseInfo` is empty. Layer description is "State Natural Areas". Layer `copyrightText` is "WDNR-ER". No redistribution sentence was found on this service.

**Natural Area Parcel Ownership** (service `ER_DNR_NA_StateNaturalAreas_WTM`, layer 2). Layer description:

> "Contains public-facing parcels. For external use, contact NHC program for data dissemination."

Service `licenseInfo`:

> "Sensitive parcels and project boundaries-- For Internal use only. Do not share outside of DNR."

> "Public-facing parcels-- contact Bureau of Natural Heritage Conservation, State Natural Area program for data dissemination."

The service description also says public-with-sensitive parcels "are not to be shared outside the agency without permission from the Natural Heritage Conservation program" and that acquisition-authority project boundaries "should not be shared with the public." Layer 2 is the public-facing parcel layer, not the sensitive one, but external use still requires contacting the program.

**Acceptable Use Policy** (https://dnr.wisconsin.gov/legal/acceptableuse) is scoped to the website, not to these map services:

> "Access to and use of the Wisconsin Department of Natural Resource's official Internet site dnr.wi.gov -- is provided subject to these terms and conditions."

> "The material is for the noncommercial use of the general public."

> "For copy or use of information on the department website that is outside of the fair use provisions of copyright law, please seek permission from the individual listed as responsible for the page."

The official GIS items bind the user to https://dnr.wisconsin.gov/legal (Legal Notices), not to `/legal/acceptableuse`. The permission sentence is about website material, not the open-data map services.

### Was the other agent's Wisconsin reading accurate?

Partly. For the public managed-properties, managed-land-parcel, and WSPS property-boundary services, yes: there is no Creative Commons or other reuse licence, and the official text is an as-is / not-for-legal-use disclaimer. That is not a ban, and publishing with credit matches those items.

It is not accurate for Natural Area Parcel Ownership. That layer is not "no licence." It expressly requires contacting the State Natural Area program before external use. If that layer was one of the four, do not publish it on a "disclaimer only" reading.

A county-forest Wisconsin DNR layer is already recorded elsewhere as "public, no use constraints." That existing practice supports the managed-properties reading; it does not override the Natural Area Parcel contact requirement.

---

## 2. Montana State Library — Montana Managed Areas

The layer in KPC is Montana Managed Areas (MSDI Administrative Boundaries), served from the Montana State Library / MSDI stack (`gisservice.mt.gov` MapServer layer "Managed Areas"). Originator and publisher on the current official record: Montana State Library. The Montana Natural Heritage Program (MTNHP) built and maintains the stewardship mapping.

### Official pages read

- Current MSL metadata (publication date 12/30/2025): https://mslservices.mt.gov/Geographic_Information/Data/DataList/datalist_MetadataDetail.aspx?did=%7B80C2319F-17BC-4A67-B0DF-BB12B53D1D5E%7D
- Current MSL dataset details: https://mslservices.mt.gov/geographic_information/data/datalist/datalist_Details.aspx?did=%7B80C2319F-17BC-4A67-B0DF-BB12B53D1D5E%7D
- Older MTNHP metadata page (still posted; publication date 2011): https://mtnhp.org/help/metadata/files/managedareas.html

No Creative Commons or other standard open-data licence is named on these pages. Access constraints on the current MSL metadata: "None." The data are also offered as a public download from the Library's FTP area (the details page lists https://ftpgeoinfo.msl.mt.gov/data/Spatial/MSDI/AdministrativeBoundaries/ as data access). That FTP path was not downloaded.

### Exact sentences that matter

**Use constraints** on the current (12/30/2025) MSL metadata, and the same block on the details page:

> "The Montana State Library provides this product/service for informational purposes only. The Library did not produce it for, nor is it suitable for legal, engineering, or surveying purposes. Consumers of this information should review or consult the primary data and information sources to ascertain the viability of the information for their purposes. The Library provides these data in good faith but does not represent or warrant its accuracy, adequacy, or completeness. In no event shall the Library be liable for any incorrect results or analysis; any direct, indirect, special, or consequential damages to any party; or any lost profits arising out of or in connection with the use or the inability to use the data or the services provided. The Library makes these data and services available as a convenience to the public, and for no other purpose. The Library reserves the right to change or revise published data and/or services at any time."

That block, by itself, is a disclaimer. It does not grant a licence and does not mention copying.

**Distribution liability** on the same current official MSL metadata and details pages (this is the sentence the other reading missed):

> "Please be aware that these data are frequently changed and updated. Rather than distribute the data to second parties, please refer interested parties to the Montana Natural Heritage Program for the most recent version of the data."

Also from the same liability / abstract block:

> "Map features in this data set are not intended as a legal depiction of public or private surface land ownership boundaries and should not be used in place of a survey conducted by a licensed land surveyor. Similarly, map features do not imply public access to any lands."

The older MTNHP metadata page puts the same "Rather than distribute the data to second parties..." sentence in **Use constraints** as well as in distribution liability. The current official MSL record keeps it in distribution liability.

The sentence is a currency request (point people to the official source for the latest copy), not a copyright statute and not the words "you may not copy." It is still language about redistribution, so "nothing on copying" is wrong.

### Was the other agent's Montana reading accurate?

No, not fully. The "informational purposes only" disclaimer is correctly quoted in spirit. The claim that there is nothing on copying is not correct: the current official MSL record still asks users not to distribute the data to second parties and to refer them to MTNHP.

### Verdict

**YES with conditions**, for the park outlines actually used, not for a full-layer republish:

1. Credit **Montana State Library** and **Montana Natural Heritage Program**.
2. Do not host or redistribute the full Managed Areas dataset as a KPC copy. Use only the derived outlines needed.
3. If someone wants the source data, point them to the Montana State Library Data List / MTNHP (geoinfo@mt.gov is the contact on the official record), which is what the "refer interested parties" sentence asks.
4. Show the outlines as reference only; do not treat them as legal boundaries; do not imply public access.

A short ask to geoinfo@mt.gov would remove any leftover doubt, but it is not required to use parts-only outlines with credit under this reading, because the Library already offers the data as a public convenience with no access constraints, and the redistribution sentence is about keeping people on the official, up-to-date copy.

---

## 3. Minnesota DNR

### Official pages read

- General Data and Software License Agreement (plain text official page): https://www.dnr.state.mn.us/sitetools/data_software_license_plain.html
- Same agreement, printable page: https://www.dnr.state.mn.us/sitetools/data_software_license_print.html
- Same agreement, standard page (script-rendered; the plain and print pages carry the full text): https://www.dnr.state.mn.us/sitetools/data_software_license.html
- Data Requests for Commercial Use: https://www.dnr.state.mn.us/aboutdnr/data-requests-commercial-use.html
- Disclaimers, Legal Notices and Policies (site copyright notice): https://www.dnr.state.mn.us/aboutdnr/disclaimers_and_policies.html

Minnesota Geospatial Commons dataset HTML pages on gisdata.mn.gov were script-rendered and returned no text in this fetch. The metadata host `resources.gisdata.mn.gov` has `User-agent: *` / `Disallow: /` in robots.txt, so those metadata HTML files were not fetched. Public index listings and previously recorded official metadata for DNR boundary datasets on the Commons cite this same agreement at http://www.dnr.state.mn.us/sitetools/data_software_license.html. No dataset-specific licence that would override the general agreement (clause 2) was found on the official DNR pages read today. No Creative Commons licence is used.

An older "General Geographic Data License Agreement" still appears on some DNR pages (for example the WMA GPS licence page). The current agreement, and the URL the Commons metadata cites, is the General Data and Software License Agreement below.

### Exact sentences that matter

Granting clause and clause 1 (https://www.dnr.state.mn.us/sitetools/data_software_license_plain.html):

> "The Minnesota Department of Natural Resources (MNDNR) grants to you a personal, non-exclusive, non-transferrable, limited license to extract information from, use, reproduce, distribute, and modify data and/or software, in source and binary forms, with the acceptance of the following: Terms and Conditions of Use"

> "1. Data and/or software may be used for the creation of derivative works; however data and/or software in its entirety may not be resold, distributed or displayed for commercial purposes or otherwise."

Clause 3 (credit):

> "An MNDNR copyright notice will be included, as appropriate; or MNDNR must be acknowledged as having contributed to any derivative work."

Clause 6 (maps are reference only):

> "Map and geographic data should not be interpreted as establishing or describing legal boundaries or legal access and should not be used for navigational purposes. Map and geographic data should be used for reference only."

Clause 7 (no logos):

> "This license does not give the right to use the MNDNR name, marks, or any of its logos and is not an endorsement of the user's products."

**Commercial use page** (https://www.dnr.state.mn.us/aboutdnr/data-requests-commercial-use.html):

> "For data the Minnesota Department of Natural Resources publishes for the public, users must adhere to the General Data & Software License Agreement. Users intending to use these data sets for commercial use will need to complete and submit this form: Data License Agreement From"

The site-wide copyright notice on the disclaimers page is stricter about the website ("view or print ... for personal use"; commercial reuse of website material needs permission). The GIS datasets are under the more specific Data and Software License Agreement, which expressly allows derivative works and distribution of less than the entire dataset.

The phrase "in its entirety may not be resold, distributed or displayed for commercial purposes or otherwise" is best read as a ban on passing on or displaying the **complete** layer, including for non-commercial use. That is why parts are allowed and a full-layer republish is not.

### Was the other agent's Minnesota reading accurate?

Yes. Parts may be used in a derivative work, with credit. The layer may not be distributed or displayed in its entirety. Publishing the two records used, with an MNDNR acknowledgement and no DNR logos, fits the official licence. KPC's use is non-commercial, so the commercial-use request form does not apply.

### Verdict

**YES with conditions:**

1. Publish only the records used (parts / a derived outline), not the layer in its entirety.
2. Credit: acknowledge the Minnesota Department of Natural Resources (MNDNR) as having contributed to the derivative work.
3. Do not use MNDNR name, marks, or logos as branding.
4. Show as reference only; not a legal boundary or a statement of legal access.

---

## Bottom line for the owner

- **Wisconsin managed properties, managed-land parcels, and WSPS property boundaries: YES, with credit.** The other agent's "disclaimer only" reading is right for these. The Natural Area Parcel Ownership layer is **not** in that group: **NO** until NHC says yes. If that parcel layer was one of the four, take it out.
- **Montana Managed Areas: YES with conditions**, not a plain yes. The other agent missed the official "rather than distribute the data to second parties" sentence. Parts/outlines with credit, and a pointer back to MSL/MTNHP, are consistent with that sentence. A full-layer copy is not.
- **Minnesota DNR: YES with conditions**, as the other agent said. Parts with credit; not the whole layer.

Nothing from these sources should go live until the owner says GO on a build.

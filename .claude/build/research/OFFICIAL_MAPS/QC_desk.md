# CA-QC official maps: who runs it (desk, Oct 28 2026)

Source of this first pass: the 1,995 park map links already in data/parkinfo-web.json with the bot check result (grade A = the bot opened the link on 2026-10-27, "ok"). Rules pages, handovers and map dates not in that file are marked TO DO (grade C = not yet looked at).

| Agency site | parks | bot ok | address pattern (typical) | tested examples (park, link, bot result, map date) |
|---|---|---|---|---|
| parks.canada.ca | 6 | 6 | `parks.canada.ca/lhn-nhs/qc/chateauguay/activ/<page>` | CA-4896 Battle of the Chateauguay Na: https://www.parks.canada.ca/lhn-nhs/qc/chateauguay/activ/sentiers-trails → ok; date not stated<br>CA-4897 Battle of the Restigouche Na: https://parks.canada.ca/lhn-nhs/qc/ristigouche/visit/cartes-maps → ok; date not stated<br>CA-4899 Carillon Canal National Hist: https://parks.canada.ca/lhn-nhs/qc/canalcarillon/visit/cartes-maps → ok; date not stated |
| montreal.ca | 2 | 2 | `montreal.ca/en/places/<page>` | CA-4988 Parc de la Promenade-Belleri: https://montreal.ca/en/places/parc-de-la-promenade-bellerive → ok; date not stated<br>CA-5005 Parc des Rapides Regional Pa: https://montreal.ca/en/places/parc-des-rapides → ok; date not stated |
| carte.ptittraindunord.com | 1 | 1 | `carte.ptittraindunord.com/<page>` | CA-2034 Parc Lineaire Le P'tit Train: https://carte.ptittraindunord.com/ → ok; date not stated |
| vsj.ca | 1 | 1 | `vsj.ca/wp-content/uploads/2023/02/<file.pdf>` | CA-2159 Parc nature du Lac-Jerome Re: https://www.vsj.ca/wp-content/uploads/2023/02/Plan_LacJerome_Web.pdf → ok; date not stated |
| parcjeandrapeau.com | 1 | 1 | `parcjeandrapeau.com/en/publications/<page>` | CA-2176 Parc Jean-Drapeau Regional P: https://www.parcjeandrapeau.com/en/publications/ → ok; date not stated |
| ville.vaudreuil-dorion.qc.ca | 1 | 1 | `ville.vaudreuil-dorion.qc.ca/uploads/sections/Loisirs_culture/Installations_recreatives/Espaces_verts/<file.pdf>` | CA-2233 Parc de la Maison-Valois Rec: https://www.ville.vaudreuil-dorion.qc.ca/uploads/sections/Loisirs_culture/Installations_recreatives/Espaces_verts/Plan-directeur_PEV.pdf → ok; date not stated |
| montsaintjoseph.com | 1 | 1 | `montsaintjoseph.com/wp-content/uploads/2020/06/<file.pdf>` | CA-4948 Parc regional du Mont-Saint-: https://montsaintjoseph.com/wp-content/uploads/2020/06/Carte_rando_complete_MSJ_2020.pdf → ok; date not stated |
| pra.terrebonne.ca | 1 | 1 | `pra.terrebonne.ca/wp-content/uploads/2024/05/<file.pdf>` | CA-4954 Parc de la Riviere de Terreb: https://pra.terrebonne.ca/wp-content/uploads/2024/05/plan-directeur-corridor-de-biodiversite-juin-2021.pdf → ok; date not stated |
| parcdeschutes.com | 1 | 1 | `parcdeschutes.com/en/trails/<page>` | CA-4956 Parc des Chutes Regional Par: https://parcdeschutes.com/en/trails/ → ok; date not stated |
| st-hyacinthe.ca | 1 | 0 | `st-hyacinthe.ca/medias/loisirs-et-culture/installations/<file.pdf>` | CA-4959 Parc Les Salines Regional Pa: https://www.st-hyacinthe.ca/medias/loisirs-et-culture/installations/LCVC_Installations-recreatives_Parc-Les-Salines_carte-sentiers.pdf → no answer (<urlopen error [SSL: CERTIFICATE_VERIFY_); date not stated |
| cms.longueuil.quebec | 1 | 1 | `cms.longueuil.quebec/sites/default/files/medias/documents/2021-11/<file.pdf>` | CA-4960 Parc Michel-Chartrand Region: https://cms.longueuil.quebec/sites/default/files/medias/documents/2021-11/Rapport%20Table%20de%20concertation%20du%20parc%20Michel-Chartrand%20-%2022%20novembre%202021.pdf → ok; date not stated |
| mrcdrummond.qc.ca | 1 | 1 | `mrcdrummond.qc.ca/parc-regional-foret-drummond/<page>` | CA-4975 Parc regional de la Foret Dr: https://www.mrcdrummond.qc.ca/parc-regional-foret-drummond/ → ok; date not stated |
| gatineau.ca | 1 | 1 | `gatineau.ca/docs/activites_evenements_idees_sorties/plein_air_urbain/sites_plein_air/lac_leamy/<file.pdf>` | CA-5004 Centre de plein air du Lac-L: https://www.gatineau.ca/docs/activites_evenements_idees_sorties/plein_air_urbain/sites_plein_air/lac_leamy/20200220_carte_sentiers_ski_fond.fr-CA.pdf → ok; date not stated |
| valleyfield.ca | 1 | 1 | `valleyfield.ca/<page>` | CA-5019 Parc regional des Iles-de-Sa: https://valleyfield.ca/parc-des-iles → ok; date not stated |
| laval.ca | 1 | 0 | `laval.ca/sports-loisirs/centre-nature/acces-plan/<page>` | CA-5032 Centre de la nature de Laval: https://www.laval.ca/sports-loisirs/centre-nature/acces-plan/ → HTTP 403; date not stated |

**Totals:** 21 park map links, 19 bot-ok (90%).

## BOT LOOK-UP (script-loaded or failed links)
- st-hyacinthe.ca: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.
- laval.ca: 1 of 1 links did not open for the bot (403/404/400/SSL/530). BOT LOOK-UP: open in a real browser, find the current list page, re-harvest.

## Still to do (grade C)
- Rules page (hours, permits, hunting) per agency
- Who manages each park, and any handovers
- How to tell the map date for each agency

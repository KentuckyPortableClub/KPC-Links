# World W6: FRANCE (FR) (desk, Oct 27 2026)
Grades: A = opened and read, B = search result only, C = inference. Read only; nothing here queried a polygon. Builds on KPC_2fer_Preflight_World_desk.md (W-1 to W-8 not repeated). WDPA never; EEA Natura 2000 fine. Counts are from data/world-key/<CC>.json.
Key: 14,367 parks, 487 no outline, 778 to check, 3,553 pin outside, 10,114 saved-only. Sources: EEA Natura 2000/CDDA, IGN Géoplateforme ZNIEFF I/II/sea, ZNIEFF (INPN, Esri France).
## 1. Official layers
- **INPN** (Muséum): espaces protégés national parks, réserves naturelles, arrêtés de protection, PNR: https://inpn.mnhn.fr/telechargement/cartes-et-information-geographique/ep/pn (A earlier, data 07/2024; licence "freely downloadable subject to conditions of use", no named licence). data.gouv.fr "Espaces naturels protégés" and "INPN - Données du programme Espaces Protégés" exist (B; page would not open).
- Géoplateforme (IGN) WFS: in key for ZNIEFF only.
## 2. Public / owned land: PARTLY
- **ONF "Forêts publiques"** (domaniales = state, communales = municipal): data.gouv.fr "Forêts publiques (diffusion publique)" https://data.gouv.fr/en/datasets/forets-publiques-diffusion-publique (A: updated 20 Jul 2024, **licence not specified**, no direct file URL, source carmencarto.fr metadata). Also "Parcelles forestières publiques" (B).
- Conservatoire du littoral land (state, bought for public access) (B): data.gouv.fr/Conservatoire du littoral; not opened.
- Verdict: forêts domaniales + Conservatoire = public land candidates; **ZNIEFF = inventory, not park (W-1).**
## 3. No outline (487)
- **Biological Reserve 11,195 (408 none):** la Sainte-Baume FR-0012, Roc de Chère FR-0365: POTA's label for ZNIEFF and réserves; mostly ZNIEFF → W-1.
- **Recreation Park 365 (352 none):** Combe la Serpent FR-0324, Parc Messonier FR-12044: local parks.
- **Conservation Area 406 (317 none):** Massif des Corbières FR-10333, Archipel fossile du Marais rochefortais FR-10336, Reculée de Combe-Laval FR-10601: sites classés / ZNIEFF / ENS (départemental sensitive natural spaces): ENS layers by département.
- **Marine Conservation Area 85 (43 none):** Zone marine agathoise FR-10477, Les Aresquiers FR-10478.
- Natura 2000 1,718 (37 none): Massif de l'Anie FR-2517; réserve naturelle de Corse FR-15800.
## 4. Sea: Calanques NP FR-0590 plus FR-10502 Marine Conservation Area (Calanques de Marseille à Cassis), sea ZNIEFF type I, Marais, étangs: water-only.
## 5. NEW grey areas
| # | Question | My lean |
|---|---|---|
| W6-1 | **Forêt domaniale vs forêt communale**: communal forests are municipal land open to the public: public. Include? | Yes, both (public bodies). |
| W6-2 | **Espaces Naturels Sensibles (ENS) of départements**: public bought land, good, but per département layers. | Add on request; NOT SURE until a layer. |
| W6-3 | **Parcs naturels régionaux (PNR)**: whole-line parks over villages (like Naturparke). | W-2: not public land. |
## 6. Known-good: INPN espaces protégés; ONF Forêts publiques; EEA. **2-fers (C):** Parc national des Calanques FR-0590 vs FR-10502 marine part (water-only); Camargue (FR-0002) vs réserves nationales inside it; réserves vs ZNIEFF I stacks (W-1: not shown).
## 7. READY / NOT READY: **NOT READY**: ONF licence unspecified and ZNIEFF dominates the key; READY for a small list of national parks / réserves naturelles / forêts domaniales once INPN + ONF are loaded fresh and the 10,114 saved-only rows are dropped.

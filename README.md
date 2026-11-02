# Quay walls under uncertainty: code and data

Code and data behind the report *Quay walls under uncertainty: a risk-based
programming method for Utrecht, tested on the walmuren of the Wervengebied*
(CME4150 Managing Uncertainty & Data, TU Delft, 2026). The report itself is the
Overleaf project in `report/`.

The analysis computes a **failure probability (Pf and β) for each walmuur** in
the Wervengebied that still stands on its old timber foundation, combines it
with a consequence score into a risk class, and uses those results for the
fault tree, the trade-off between measures and the renewal-rate regression.

A walmuur is the low masonry wall between the werf (wharf) and the canal. It
holds back the soil under the werf. A rak is one stretch of canal between two
bridges; the register names a wall by its rak and bank (for example "Oude
Gracht - Rak 03 OZ").

The repository holds only what the report uses. Earlier drafts, notebooks and
exploratory scripts were removed after submission (1 November 2026) and are
still in the git history.

## Layout

```
data/raw/        source data, never edited by hand (except the hand-compiled CSVs listed below)
data/processed/  everything the scripts produce
scripts/         data, screening, risk and regression scripts
scripts/StressCaclulation/   the load, resistance and failure probability model
figures/         figures for the report and the per-wall data table
docs/            notes on the register and on the failure formula
report/          the report (Overleaf project, kept in sync as a git subtree)
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The scripts need only numpy, pandas, scipy and matplotlib. Run them from the
repository root, for example `python3 scripts/StressCaclulation/FailureProbability.py`.

## Running it

Run the scripts in this order; each reads the outputs of the ones before. All
outputs go to `data/processed/` or `figures/`. The Monte Carlo runs use fixed
seeds, so a rerun gives the same files.

| Step | Script | Writes | In the report |
|---|---|---|---|
| 1 | `build_groundwater_layer.py` | `objects_groundwater.csv` | groundwater check, App. A |
| 2 | `build_soil_type.py` | `masonry_walls_soil.csv` | soil class per wall, App. A |
| 3 | `build_walmuur_height.py` | `walmuur_height.csv` | werf level and H, App. A |
| 4 | `build_walmuur_traffic.py` | `walmuur_traffic.csv` | road distance and axle limit, App. A |
| 5 | `build_walmuur_foundation.py` | `walmuur_foundation.csv` | renewed or still on timber, App. A |
| 6 | `build_masonry_data_gaps.py` | `masonry_walls_data_gaps.csv` | missing register fields, App. A |
| 7 | `table_wervengebied_data.py` | `figures/wervengebied_data_table.md` | per-wall data table |
| 8 | `StressCaclulation/FailureProbability.py` | `walmuur_failure_probability.csv`, `_draws.json`, `_inputs.csv` | Pf per wall, Ch. 2, App. B (about 2 min) |
| 9 | `StressCaclulation/SensitivityDependence.py` | `walmuur_sensitivity.csv` | correlations, groundwater, soil class, App. B (about 5 min) |
| 10 | `StressCaclulation/SensitivityTornado.py` | `walmuur_tornado.csv` | one input fixed at a time, App. B (about 15 min) |
| 11 | `StressCaclulation/ModelChecks.py` | `walmuur_model_checks.csv` | model checks, App. B (about 5 min) |
| 12 | `build_walmuur_consequence.py` | `walmuur_consequence.csv` | consequence score, App. C |
| 13 | `plot_results_map.py` | `walmuur_risk_class.csv`, `figures/results_map*.png` | risk classes, Ch. 4, App. C |
| 14 | `regression_production_rate.py` | `production_rate_walls.csv`, `production_rate_risk.csv` | renewal-rate regression, Section 4.1 |
| 15 | `fault_tree.py` | printed only | fault tree and decision tree, Ch. 3 |
| 16 | `ranking_robustness.py` | `walmuur_ranking_robustness.csv`, `walmuur_tornado_class_changes.csv` | robustness of the ranking, App. B |
| 17 | `fault_tree_figure.py` | `report/figures/fault_tree_tikz.tex` | fault tree figure, Ch. 3 |
| 18 | `plot_appendix_figures.py` | `figures/app_*.png`, `figures/fig_production_step.png` | figures of App. B and Section 4.1 |

All scripts are in `scripts/`. Notes:

- Step 1 needs the BRO head series (about 1.2 GB), which are not in the
  repository. Run `scripts/fetch_bro_grondwater.py --series` first, or skip the
  step: its output is in the repository.
- Steps 3–5 download AHN, BGT, NDW and the UtrechtOpen layer when their files
  in `data/raw/` are missing.
- `scripts/screening.py` holds the green / orange / red screening of the
  register that most scripts import. Run on its own, it prints the screening
  counts of App. A.
- The PNGs in `figures/` are copied by hand to `report/figures/`.
- The replacement-cost regression of App. D has no script in this repository.

## What the model does

### Which walls get a Pf

The municipal asset register has 51 named walmuren.

- **Foundation** (`build_walmuur_foundation.py`): from the city's progress
  reports, 32 of the 51 are already renewed on steel sheet or tube piles. The
  timber model does not describe them, so they are not computed.
- **Screening** (`screening.py`): a wall is past its design life when
  `Eindjaar` (= `Aanlegjaar` + 80 years) is before 2026. Past design life and
  masonry puts it in red/orange: 18 of the 51. The register's `Aanlegjaar` is
  often not updated after a renewal, so a renewed wall counts from its renewal
  year; on the register year alone, 11 renewed walls would also be red/orange
  (29 of the 51).
- **Werf check** (`data/raw/walmuur_werf_check.csv`, done on a map): 2 of the
  remaining 19 have no werf (Kromme Nieuwe Gracht 001, Oude Gracht Rak 07 OZ).
  There the street runs to the water, which is a different structure.

That leaves **17 walls** with a Pf.

### The wall

Two types of low walmuur stand on timber piles (IBU design note):

| | Type 1 | Type 2 |
|---|---|---|
| Built | late 19th, early 20th century | after WWII until the 1970s |
| Wall | stepped masonry, 0.39 m at the top | one-brick facing with tamped concrete behind it |
| Floor | timber floor on a timber beam (watersloof) | reinforced concrete, 1.37 m wide |
| Piles | two vertical rows of pine piles, about 180 mm | the same, but the front row is raked 10:1 |

Both cross-sections are measured from the drawings (report 156 Afb. 3.1 and
IBU Afb. 2.1.1a) and stored as polygons in `SECTIONS` of
`scripts/StressCaclulation/WallResistance.py`. Which type a wall is, is not
known. TNO's dive notes say per rak whether the divers found a watersloof
(type 1) or a concrete floor (type 2), so each rak gets a chance of type 2:
20% for rak 3–6, 50% for rak 21, 90% for rak 22, 80% elsewhere
(`data/raw/walmuur_tno2009_type.csv`).

### The load

```
S_total = S_soil + S_water + S_q                    [kNm/m, about the base]

S_soil  = K (γ_s H³ − γ_w h_w³) / 6                 soil, effective below the groundwater
S_water = γ_w (h_w³ − h_c³) / 6                     groundwater behind minus canal water in front
S_q     = ½ K q_eff H²,  q_eff = q H² / (H² + a²)   surcharge q at distance a behind the wall
```

- **H** runs from the werf (AHN, per wall) to the wall underside at −0.08 m
  NAP (report 158). The median is 1.21 m. The canal bed is not measured, so H
  is a lower bound; S grows with H³, so 0.1 m more adds about 25%.
- **K and γ_s** follow from the soil class of the nearest DINO boring (soft
  clay / peat, mixed, or sand). K is lognormal, γ_s normal.
- **Water:** the canal is fixed at +0.6 m NAP (report 158); the groundwater
  under the werf is Uniform(+0.5, +0.9) m NAP, a guess. Both are set in
  `WaterLoad.py`.
- **Surcharge:** q ~ Normal(7 kPa, CoV 0.20) (Hemel et al. 2024) at
  a ~ Uniform(0, 3) m. That is heavy for a pedestrian werf.

Code: `SoilForce.py`, `WaterLoad.py`, `TraficLoad.py`, `TotalStress.py`.

### Two ways to fail

A wall fails when either happens (a series system).

1. **Overturning** (`WallResistance.py`). The wall, its floor and the soil on
   the floor tip about the front pile row. The weight of each part (below the
   water γ − γ_w) and the wall friction on the back (δ = ⅔φ) resist; S_total
   drives.
2. **Pile bending** (`PileStrength.py`), the mechanism of Hemel (2023). The
   horizontal force that the raked front row doesn't take bends the piles,
   modelled as long beams on springs (Hetényi): head fixed in the concrete
   floor for type 2, pinned for type 1. A pile fails when
   `θ_M M / W(d) + N / A(d) > MOR`, with d the sound core inside the rotted
   shell: `d = D0 − 2 × shell`.

### Proven strength

Every one of these walls stands today. Draws in which the wall would already
fail under its soil and water alone, without surcharge, cannot be the real
wall, so they are left out (Hemel et al. 2024, eq. 12). This gives the updated
Pf (`pf_updated`, `beta_updated` in the output). The same check also updates
the chance of each wall type.

### Inputs

From the data, per wall: the werf level, the soil class and the chance of each
wall type. Everything else is a distribution, the same for every wall:

| Input | Distribution | Source |
|---|---|---|
| Werf level | Normal(AHN median, 0.05 m) | AHN; Kromme Nieuwe Gracht 005–007: Uniform(1.0, 1.6) m NAP |
| K, γ_s | per soil class, K CoV 0.20–0.25 | team judgement (report Table A.6) |
| Unit weights | masonry N(19, 0.05), tamped concrete N(23, 0.05), reinforced concrete 25, timber 10 kN/m³ | typical values |
| Foundation level | drawing ± Uniform(−0.15, 0.15) m | schematic drawings |
| Model factor on the resisting moment | Lognormal(1, CoV 0.15) | dimensions read from schematic drawings |
| Pile diameter D0 | Normal(180 mm, CoV 0.10) | IBU p. 4; CoV from Hemel 2023 |
| Pile spacing along the wall | Uniform(0.8, 1.2) m | IBU, "ca. 1 meter" |
| Soft shell of the piles today | Uniform(0, 45) mm | Hemel 2023 ch. 3: 21 mm on average, up to 45 mm |
| Shell growth after 2026 | Uniform(0.10, 0.25) mm/yr | Hemel 2023 §7.3.2: 0.17 mm/yr |
| MOR, E | Normal(22 MPa, 0.10), Normal(9 GPa, 0.20) | Hemel 2023 Table 7.1 |
| Subgrade modulus k | Uniform(4,300, 10,000) kN/m³ | Hemel 2023 Table 7.1 (clay and peat) |
| Model factor on the pile moment θ_M | Lognormal(1, CoV 0.10) | JCSS, as Hemel et al. 2024 |

Every input, its distribution and its source is also written to
`data/processed/walmuur_failure_inputs.csv`.

The Monte Carlo uses 400,000 draws per wall and type, for 2026 and for 2041
(the end of the 15-year reference period of NEN 8700). Only the pile rot
changes between the two years.

### Results

Base model, updated with proven strength:

| | β in 2026 | β in 2041 | Walls below 1.8 (2026) |
|---|---|---|---|
| Best estimate (type weighted per rak) | −0.06 (Rak 03 OZ) to 1.52 (Kromme Nieuwe Gracht 003) | −0.08 to 1.40 | 17 of 17 |
| Type 2 only | 1.27 to 2.46 | 1.11 to 2.23 | 9 of 17 |
| Type 1 only | −0.91 to 1.07 | −0.92 to 1.04 | 17 of 17 |

- For type 2 the piles fail more often than the wall tips over: median Pf 0.054
  against 0.004.
- Rak 03 OZ is lowest because type 1 is likely there (TNO found a watersloof)
  and it holds back soft clay. The proven-strength check raises its chance of
  type 2 only from 0.20 to 0.34.
- No consequence class is chosen. β is held against the three rejection
  levels of NEN 8700 Table B.2 for orientation: 1.8 (CC1b), 2.5 (CC2) and
  3.3 (CC3).
- With only the masonry block (`M_R = γ_m H t² / 2`, an earlier version of
  `WallResistance.py`) Pf is about 1 for every wall. That is why the model uses
  the real cross-sections with their floor.
- `SensitivityDependence.py` reruns the model with one change at a time.
  Correlating K with γ_s, or MOR with E, changes β by 0.01 at most. Groundwater
  0.1 m higher moves β by −0.38 to +0.08. The soil class matters most: taking a
  mix of the borings within 150 m moves β by −0.70 to +0.56.
- Combined with the consequence score, 9 of the 17 walls (398 m) are red,
  3 orange and 5 green (`walmuur_risk_class.csv`). How stable that ranking is
  under the model variants is in App. B.

### Main limitations

- The wall type per wall is unknown and has the largest effect: type 1 gives a
  β 1.4 to 2.4 lower than type 2.
- The pile condition is unknown. The broad shell range is the same for every
  wall and dominates the type-2 Pf.
- The cross-sections are schematic and come from the Oudegracht. The Kromme
  Nieuwegracht walls may differ.
- H is a lower bound, because the canal bed is not measured.
- There is no traffic model; q is one assumed distribution.
- Not modelled: sliding, axial pile capacity and settlement, failure of the
  screen. Settlement from pile rot is the damage actually seen on these walls
  (report 156, IBU).

## Sources

The key in brackets is the one used in the data table README and in
`walmuur_foundation_sources.csv`.

### Data sets (in `data/raw/`)

| Data | Where to find it | In the repo | What the model uses it for |
|---|---|---|---|
| Asset register of the municipality | delivered to TU Delft for the challenge, 26 Aug 2025 | `Output areaal GU TU Delft 26-08.json`; overview in `docs/output_areaal_overview.md` | the 51 walmuren, length, material, `Aanlegjaar` and `Eindjaar` for the screening |
| AHN ground level (dtm_05m) | PDOK WMS, https://service.pdok.nl/rws/ahn/wms/v1_0 | `AHN/walmuur_ahn_points.csv` | werf level per wall, so H |
| DINO borehole logs | BROloket, https://www.broloket.nl | `BRO_GeotechnischBooronderzoek/` (76 logs) | soil class per wall, so K and γ_s |
| BRO groundwater wells and head series | PDOK OGC API, https://api.pdok.nl/tno/bro-grondwatermonitoring-in-samenhang-karakteristieken/ogc/v1 | `APIDatacollection/` (wells, tubes, series list; the series themselves are not kept) | GHG/GLG per wall. Not used in the Pf: the wells are 143–418 m from the walmuren and under raised streets |
| BGT road areas (wegdeel) | PDOK OGC API, https://api.pdok.nl/kadaster/bgt/ogc/v1 | `BGT/walmuur_wegdeel.geojson` | distance from each wall to the nearest road |
| NDW traffic signs | https://data.ndw.nu/api/rest/static-road-data/traffic-signs/v5/current-state | `NDW/traffic_signs_utrecht.geojson` | axle limit (2.0 t on all canal streets) |
| Werfmuren layer, UtrechtOpen | WFS, https://geodata.utrecht.nl/geoserver/UtrechtOpen/ows | `UtrechtOpen/werfmuren.geojson` | rak and bank of each register wall |
| Foundation per rak (hand-compiled) | the city reports and letters listed below | `walmuur_foundation_sources.csv`, `walmuur_foundation_documents.csv` | renewed or still on timber piles |
| Wall type per rak (hand-compiled) | [TNO] Bijlage G | `walmuur_tno2009_type.csv` | chance of type 2 per rak |
| Werf check (filled in by hand) | Google Maps, Street View and the AHN viewer, links in the file | `walmuur_werf_check.csv` | werf yes or no, and the level, for 9 walls |
| Hospitality in the inner city | OpenStreetMap, Overpass API | `osm_hospitality_binnenstad.json` | people and terraces on the werf, for the consequence score |

Download dates, coverage and known gaps for each file are in
`data/raw/SOURCES.md`.

### Reports on the Utrecht walls

Most of these are on the city council's document site
(utrecht.bestuurlijkeinformatie.nl) or the Erfgoed Utrecht site, and are free
to open.

- **[IBU]** IBU Stadsingenieurs, *Ontwerpnotitie herstel lage walmuren*, about 2010.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/7a80a169-48bb-4f58-964c-518caf0f6d7c
  Used: the two wall types and their drawings, pile diameter (about 180 mm),
  length (4 m), two rows about 1 m apart, the raked front row of type 2, and
  the damage found in the 2007–08 dive inspections.
- **[TNO]** TNO, *Eindbeoordeling kademuren Utrecht*, TNO-034-DTM-2009-01978, 14 May 2009.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/6b59e223-7ec8-40fe-a845-c1223322df17
  Used: what the divers found per rak (Bijlage G), so the wall type. The pile
  values (Bijlagen A and B) are blank in the public copy.
- **[E156]** Erfgoed Utrecht, *Basisrapportage Archeologie 156: Oudegracht rakken 1, 4, 10, 11 en 15 west*.
  https://erfgoed.utrecht.nl/fileadmin/uploads/documenten/zz-erfgoed/publicaties/rapporten-archeologie/156-Oudegracht-rakken.pdf
  Used: the type-2 cross-section (Afb. 3.1, p. 18), the cause of the damage
  (p. 7), the 1960s walls being largely concrete (p. 23), peaty fill in rak 1
  west only.
- **[E158]** Erfgoed Utrecht, *Basisrapportage Archeologie 158: Oudegracht rakken 1 oost, 3 west en 12 oost*.
  https://erfgoed.utrecht.nl/fileadmin/uploads/documenten/zz-erfgoed/publicaties/rapporten-archeologie/158-Rapportage.pdf
  Used: werf +1.10 m NAP, wall underside −0.08 m NAP, canal level +0.6 m NAP.
- **[E114]** Erfgoed Utrecht, *Basisrapportage Archeologie 114: Oudegracht rakken 12, 13 en 14 west*.
  https://erfgoed.utrecht.nl/fileadmin/uploads/documenten/zz-erfgoed/publicaties/rapporten-archeologie/114-Rapportage.pdf
  Used: the piles and screen date from the 1950s–60s; renovation then,
  restoration in 1975–1985.
- **[ANTEA]** Antea Group, *Onderzoek Wal- en Kluismuren, eindrapportage*, 14 Nov 2019.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/8fdd67ee-61f8-493c-a7b2-aa38c58ff36c
- **[UP2528]** Gemeente Utrecht, *Programma Werk aan de Werf, Uitvoeringsprogramma 2025–2028*.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/d3f21423-a615-4f53-add6-78f0fa775498

[ANTEA], [UP2528] and the other progress reports, city news and neighbourhood
letters give which walls are renewed. The full list with links is in the
"Foundation" section of `figures/wervengebied_data_table_README.md`.

### Literature and standards

- **[HEMEL23]** Hemel, M.-J. (2023). *Amsterdam quays under pressure:
  modelling and testing of historic canal walls*. PhD thesis, TU Delft.
  TU Delft repository (repository.tudelft.nl). Used: the pile-bending
  mechanism, the soft shell (ch. 3), MOR, E, k and the CoV of D0 (Table 7.1),
  the shell growth (§7.3.2).
- **[HEMEL24]** Hemel, M.-J., Peters, D.J., Schweckendiek, T., & Jonkman, S.N.
  (2024). Reliability updating for lateral failure of historic quay walls.
  *Georisk*, 18(4), 882–903. Through the TU Delft library. Used: the
  surcharge q, the model factor on the pile moment and updating with proven
  strength (eq. 12). `docs/failure_formula_notes.md` follows this paper.
- **[NEN8700]** NEN 8700:2011+A1:2020, Table B.2: the target β (1.8 / 2.5 /
  3.3) and the 15-year reference period. NEN 8707:2018 (existing geotechnical
  structures) uses the same values. Not in the repo (copyright); open them
  through NEN Connect via the TU Delft library.
- **[NEN1991]** NEN-EN 1991-1-1: 5 kN/m² for pedestrians on the werf (not
  checked against the standard text).
- **[JCSS]** JCSS Probabilistic Model Code (2001), https://www.jcss-lc.org:
  model factors and the MOR–E correlation used in the sensitivity run.

The BibTeX entries of the report are in `report/report.bib`.

## Where to read more

| Question | File |
|---|---|
| Where does each value per wall come from, and how far can it be trusted? | `figures/wervengebied_data_table_README.md` |
| The values per wall | `figures/wervengebied_data_table.md` |
| Pf and β per wall, type and year | `data/processed/walmuur_failure_probability.csv` |
| Every model input with its distribution and source | `data/processed/walmuur_failure_inputs.csv` |
| Download date and gaps of each raw file | `data/raw/SOURCES.md` |
| The fields of the asset register | `docs/output_areaal_overview.md` |
| The pile-bending formula of Hemel et al. (2024) | `docs/failure_formula_notes.md` |
| The report | `report/report.tex` |

## The report folder

`report/` is the team's Overleaf project, kept in sync with git subtree through
the `overleaf` remote (branch `main`). Edits made in the Overleaf editor arrive
as commits there, so always pull before pushing, and never force push:

```
git subtree pull --prefix=report overleaf main
git subtree push --prefix=report overleaf main
```

The Overleaf Git token goes in `.env` at the repo root as `OVERLEAF_TOKEN=...`
(`.env` is git-ignored). Each clone needs its own credential helper in
`.git/config` that reads the token from there.

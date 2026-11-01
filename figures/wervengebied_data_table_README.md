# How the values in the Wervengebied data table are determined

This file explains every column of
[`wervengebied_data_table.md`](wervengebied_data_table.md): where each value
comes from, which rules or assumptions are applied, and how far it can be
trusted. Counts and ranges quoted here are from the run of 20 October 2026
(the traffic, foundation and soil type columns: 21 October 2026; the werf
level, H and screening columns: 30 October 2026).
The table itself is always generated from the data, so rerun the scripts after
the data changes. This file is written by hand.

## Rebuilding the table

Run the scripts in this order. Each one reads the output of the one before.

| Step | Script | Writes |
|---|---|---|
| 1 | `scripts/build_groundwater_layer.py` | `data/processed/objects_groundwater.csv` (groundwater and location per wall) |
| 2 | `scripts/build_soil_type.py` | `data/processed/masonry_walls_soil.csv` (soil type per wall) |
| 3 | `scripts/build_walmuur_height.py` | `data/processed/walmuur_height.csv` (werf level and H per walmuur) |
| 4 | `scripts/build_walmuur_traffic.py` | `data/processed/walmuur_traffic.csv` (distance to the road and axle limit per walmuur) |
| 5 | `scripts/build_walmuur_foundation.py` | `data/processed/walmuur_foundation.csv` (foundation type and renewal year per walmuur) |
| 6 | `scripts/build_masonry_data_gaps.py` | `data/processed/masonry_walls_data_gaps.csv` (not used by the table, but kept in step) |
| 7 | `scripts/table_wervengebied_data.py` | `figures/wervengebied_data_table.md` |
| 8 | `scripts/StressCaclulation/FailureProbability.py` | `data/processed/walmuur_failure_*` (Pf and β per walmuur; see the section on failure probability) |

## Which walls are in the table

The table has one row per walmuur: the 51 objects in the municipal asset
register with `Kunstwerktype Utrecht` = Walmuur and a non-empty `Naam`. Two
unnamed walmuren (WF060901, WF060903) are left out.

A walmuur is the masonry wall between the werf (wharf) and the canal. It holds
back the soil under the werf.

## Columns from the asset register

These columns are copied from `Output areaal GU TU Delft 26-08.json`.

| Column | Register field | Notes |
|---|---|---|
| Nummer | `Nummer` | Asset ID. |
| Name | `Naam` | `\|` is replaced by `/` so the Markdown table doesn't break. |
| Material | `Bouwmateriaal` | 50 Metselwerk, 1 Beton (KM060056). |
| Length [m] | `Lengte` | Used to report results per metre of wall. |

## Screening

This column is computed in `scripts/screening.py`. The design
life is the register's own: `Eindjaar` − `Aanlegjaar` is 80 years for all 51
walmuren. For the 32 walls renewed on steel (see Foundation) it runs from the
renewal year instead (`with_renewals`), because the register keeps the year of
the old wall for 11 of them.

| Result | Rule |
|---|---|
| green | Within design life: `Eindjaar` (= `Aanlegjaar` + design life) is 2026 or later. |
| red/orange | Past design life and masonry (`Bouwmateriaal` lists Metselwerk). These walls need a failure probability. Red against orange is decided later, by comparing Pf with Pf,target. |
| orange | Past design life and not masonry. |
| not classified | `Eindjaar` is missing, or at or before `Aanlegjaar`. |

The result is 33 green (3,445 m) and 18 red/orange (617 m). On the register
years alone it would be 22 green (2,177 m) and 29 red/orange (1,885 m).

## Built

The value is `Aanlegjaar`, used for the design life (screening) and for the
foundation age t of a timber decay model. Three markers flag years that can't be taken at
face value:

- **[a] 1917:** possibly a default year in the register.
- **[b] before 1850:** the year of the original wall. The walmuren were
  renovated in the 1950s–60s and restored in 1975–1985, so this isn't the age
  of the current foundation.
- **[d] KM060028:** the register says 2118, a year in the future. This is read
  as 2018, a typo.

For the [a] and [b] walls the foundation age is unknown. The renovation year
per rak has to be requested from the city.

## Werf level [m NAP] and H [m]: retained height

H is the height from the werf to the canal bottom: H = werf level − canal
bottom. `Hoogte` is empty for all 51 walmuren, so H is estimated in
`scripts/build_walmuur_height.py`, which writes
`data/processed/walmuur_height.csv`.

**Werf level (measured):**
1. The script reads the AHN ground level (`dtm_05m`, from PDOK) at 6 places
   spread evenly along each wall, 2.5 m to the left and right of the wall
   line.
2. Over the water AHN has no value, so the side with values is the werf. If
   both sides have values, it takes the side with more values, or if that is
   equal, the lower side.
3. The werf level is the median of the values at or below +1.6 m NAP. A point
   above that is on the street, a stair or a bridge, not on the werf.

The AHN values are saved in `data/raw/AHN/walmuur_ahn_points.csv`. Delete
that file to download them again.

Result: 38 walls have a werf at +0.91 to +1.40 m NAP. The median is +1.12 on
the Oudegracht, +1.16 on the Nieuwegracht and +1.14 on the Kromme
Nieuwegracht. This matches +0.95 to +1.15 m NAP in Erfgoed Utrecht reports
156 and 158.

Until 30 October 2026 the median was taken over all points on the werf side.
For 15 walls that included points on a stair or the street, which raised
their werf level by up to 0.55 m: Rak 03 OZ (+1.48, now +1.14), Kromme Nieuwe
Gracht 002 (+1.57, now +1.11) and 009 (+1.53, now +0.98), and 0.01–0.14 m for
the other 12.

**Canal bottom (assumed):** it isn't measured anywhere. It is taken at the
underside of the wall, −0.08 m NAP (report 158, rak 3 west), for every wall:
a quay wall is normally founded at about the level of the canal bed. The bed
may be deeper, so this H is a lower bound. The table shows it marked [g]; it
is counted as an estimate, not as data.

Result: H is 0.99 to 1.48 m, with a median of 1.21 m (1.20 m on the
Oudegracht, 1.25 m on the Nieuwegracht, 1.21 m on the Kromme Nieuwegracht).
The scripts in `scripts/StressCaclulation/` use the median, 1.21 m.

**Suggested distribution for the Monte Carlo:** werf level ~ N(werf level of
the wall, 0.05 m), because AHN's height accuracy is about 5 cm, with the
canal bottom fixed at −0.08 m NAP until it is measured.

Because S ∝ H³, the canal bottom still matters most: at H ≈ 1.2 m, every
0.1 m that the bed lies deeper adds about a quarter to the soil load.

**[h] Walls that may have no werf (13):** the ground beside these walls is
above +1.6 m NAP.
- **High at every point (7):**
  - Oude Gracht Rak 07 OZ and 09 NOZ
  - Nieuwe Gracht Rak 16 NOZ
  - Kromme Nieuwe Gracht 001, 005, 006 and 007
- **Mixed (6):**
  - Oude Gracht Rak 06 NZ, 06 ZZ and 08 OZ
  - Nieuwe Gracht Rak 17 OZ and 20 OZ
  - Kromme Nieuwe Gracht 008

Either the street reaches the canal there, which would make H about 3–4.5 m,
or the points hit a bridge, a stair or a building. H isn't estimated for these
walls until they are checked on a map.

**How far to trust it:**
- **The median hides variation along a wall:** up to about 0.3 m on the
  Oudegracht. For a long wall the highest section governs.
  `walmuur_height.csv` gives the minimum and maximum per wall.
- **The canal bottom is weak:** it is a single measured foundation level, from
  one rak, used for all walls.
  - Soundings per rak would replace it with a normal around the measured
    bottom (σ about 0.1 m).
  - In design, Eurocode 7 (9.3.2.2) adds an unplanned excavation of 10% of the
    retained height, at most 0.5 m, for scour or over-dredging.

## t [m]: wall thickness

t is used for the resisting moment M_R. The value is `Breedte`, the width of
the object seen from above. It is not confirmed that this is the wall
thickness.

- **[c] above 1.5 m:** too large for a wall. `Breedte` probably means a strip
  of 2–3 m here. These values are shown but not counted as data.
- **[e] assumption:** applies to Oudegracht masonry walmuren with an empty or
  unusable `Breedte`. They get t ~ Uniform(0.40, 0.45) m, based on these
  measurements:
  - 0.41 m (Rak 02 OZ, 1880)
  - 0.45 m (Rak 12–14, rebuilt 2015–16)
  - 0.40 m for a removed walmuur (Erfgoed Utrecht, Rapportages archeologie 156)

  These are thicknesses at the top; the wall may be thicker lower down. The
  assumption isn't used for the Nieuwegracht and Kromme Nieuwegracht.

## Canal level [m]

This is the drop from the top of the wall to the water, from `Valhoogte`. It
is needed for the water load and for uplift. It is empty for all walmuren.

## Groundwater [m]

The value is a range from GHG to GLG, as depth below ground. It is computed in
`scripts/build_groundwater_layer.py`. The water load does not use it: the
wells stand under the streets and give groundwater above the werf itself, so
`WaterLoad.py` uses a range on the werf instead, Uniform(+0.5, +0.9) m NAP
around the canal level of +0.6 m NAP (report 158). Until 30 October 2026
`WaterLoad.py` and `TotalStress.py` used the median well depths (1.73–2.13 m)
and put the canal 2.0 m below the street; at H ≈ 1.2 m that left the wall dry.

1. **Data:** BRO head series fetched from the PDOK API. Only series from
   phreatic filters (screen top within 8 m of the surface) that were still
   measured after 2020 are used. See `data/raw/SOURCES.md`.
2. **Per well:**
   - Readings on the 14th and 28th of each month are kept, as in the Dutch
     GxG convention.
   - Each hydrological year (1 April – 31 March) with at least 16 readings
     gives a lowest and a highest value, each the mean of its 3 lowest or 3
     highest readings.
   - GLG and GHG are the averages over the years.
   - The depth below ground is the well's ground level minus the head.
3. **Per wall:** a weighted average over the 6 nearest wells, with weight
   1/distance². The GHG depth is the GLG depth minus the average swing
   (GHG − GLG).

**How far to trust it:**
- No well is at a walmuur. The nearest well is 143–418 m away (median 263 m).
  The 6 wells in the average reach up to about 800 m.
- In `objects_groundwater.csv`, 23 walmuren are labelled "interpolated"
  (nearest well 100–250 m) and 28 "weakly supported" (250–500 m).
- The depth is below the ground level at the wells, not below the werf. For
  the level in m NAP, use `glg_m_nap` in `objects_groundwater.csv`.

## Soil type

The value is the soil class of the nearest boring, with the distance to that
boring in brackets. The class chooses K and γ_s in `SOIL_TYPES` of
`scripts/StressCaclulation/SoilForce.py`. It is computed in
`scripts/build_soil_type.py`.

| Class | K mean (CoV) | γ_s mean (CoV) | K·γ_s |
|---|---|---|---|
| soft clay / peat | 0.60 (0.20) | 15.0 kN/m³ (0.05) | 9.0 |
| mixed | 0.45 (0.25) | 16.5 kN/m³ (0.06) | 7.4 |
| sand | 0.35 (0.20) | 18.0 kN/m³ (0.05) | 6.3 |

The K and γ_s values are assumptions from the group report (App. C,
table C.5). The soil load scales with K·γ_s, so a wall in soft clay / peat gets
about 43% more load than the same wall in sand.

**How a walmuur gets its class:**

1. **Data:** the 76 DINO borings in
   `data/raw/BRO_GeotechnischBooronderzoek/DINO_GeologischBooronderzoekBoormonsterprofiel/`.
   The 71 with a known ground level are used. Each boring describes its
   layers by main soil type (`Hoofdgrondsoort`), in m below its own ground
   level.
2. **Soil range:** the soil a walmuur holds back runs from the werf at
   +1.10 m NAP down to the underside of the wall at −0.08 m NAP, both from
   report 158 (rak 3 west). For a boring with ground level z (m NAP), this is
   the range from z − 1.10 to z + 0.08 m below its surface. Every boring
   reaches that level, whether it was drilled on the street or on the werf.
3. **Count the metres** in that range for each group:
   - clay-like: klei, veen, leem, mergel
   - sand-like: zand, grind, schelpen
   - other: fill (puin, baksteen, stenen, wegverhardingsmateriaal) and
     undescribed layers (niet benoemd, geen monster)
4. **Classify:**
   - at least 70% clay-like → soft clay / peat
   - at least 70% sand-like → sand
   - otherwise → mixed

   A profile with a lot of fill therefore ends up mixed.
5. **Pick the boring:** the nearest one within 250 m that describes this range.

**Result:** 23 soft clay / peat, 16 sand and 12 mixed. The boring is 20–144 m
from the wall (median 75 m). Until 21 October 2026 the range ran down to
−0.65 m NAP; the shorter range turned 13 walls from mixed into soft clay /
peat.

**How far to trust it:**
- **Nearby borings often disagree.** For only 9 of the 51 walmuren do all
  borings within 150 m give the same class. `masonry_walls_soil.csv` lists per
  wall the boring, the clay/sand/other shares, `n_nearby_borings` and
  `n_agree`.
- **The descriptions are often old and coarse.** The borings date from 1862 to
  2014, and many lithology fields are `onbekend`.
- **The werf level and wall underside are measured at one rak only**
  (Oudegracht rak 3 west), but are used for all three canals, not a value per
  wall.
- **Report 156 only partly agrees.** Erfgoed Utrecht report 156 found peaty
  fill layers here and there around 0.0 m NAP in rak 1 west; in rakken 4, 10,
  11 and 15 west the ground had been disturbed when the walmuren were built.
  Rak 01 WZ itself comes out as mixed, with 68% clay-like soil, just under the
  70% limit. The borings are tens of metres away and may describe peaty fill
  as klei or leave it undescribed, so weigh the two sources in the report.

**Why other data isn't used:**
- The BRO CPTs that came in the same download are mostly pre-drilled through
  the top 2 m.
- The BRO hand borings are a single site about 650 m from the canals.

Both were removed from the repository. See the README in
`data/raw/BRO_GeotechnischBooronderzoek/`.

## Road a [m] and Axle limit [t]: traffic

The surcharge model (`scripts/StressCaclulation/TraficLoad.py`) needs a load
q and its distance a to the wall:

```
q_eff = q · H² / (H² + a²)
```

The register has neither. Two open data sets give what can be measured.
Both are made by `scripts/build_walmuur_traffic.py`.

**Road a: distance to the nearest road.**
- **Method:** at 6 places along the wall, a line is drawn at right angles
  towards the werf side. The werf side is the same side that
  `build_walmuur_height.py` finds with AHN. The distance is read to the first
  BGT road area the line enters: a carriageway (`rijbaan`) or a parking bay
  (`parkeervlak`), up to 30 m.
- **What is left out:** footpaths, cycle paths, stairs, and roads on a bridge
  (`relatieve_hoogteligging` ≠ 0).
- **What the table shows:** the lowest and highest of the 6 places. The CSV
  also has the median and the road function.
- **Source:** BGT `wegdeel` via the PDOK OGC API, saved in
  `data/raw/BGT/walmuur_wegdeel.geojson`.

| Canal | Walls with a werf: a (median of the walls) | Walls marked [h]: a |
|---|---|---|
| Oudegracht | 2.5–17.9 m (6.7 m), 26 walls | 2.8–21.8 m (3.7 m), 5 walls |
| Nieuwegracht | 2.4–6.5 m (3.9 m), 8 walls | 1.7–4.6 m (2.4 m), 3 walls |
| Kromme Nieuwegracht | 2.6–5.6 m (4.2 m), 4 walls | 0.9–7.8 m (1.7 m), 5 walls |

Oude Gracht Rak 15 OZ has no road within 30 m (shown as > 30). BGT has
buildings 3.0–3.5 m behind the wall there, not a street.

**Axle limit: the heaviest axle allowed on the street.**
- **Method:** the posted maximum axle load of the nearest NDW traffic sign
  C20 within 150 m of the wall line, with the distance in brackets.
- **Source:** NDW traffic signs API, all C20, C21 and C7 signs in Utrecht,
  saved in `data/raw/NDW/traffic_signs_utrecht.geojson`.
- **Result:** every wall gets 2.0 t.
  - 37 walls have the sign within 30 m.
  - For the other 14 the sign is 38–134 m away and may stand on another
    street. These include all of the Kromme Nieuwegracht, Rak 06–07 and
    Rak 09 WZ.
- **Other signs:**
  - No C21 (maximum vehicle mass) stands within 150 m of any walmuur.
  - 47 walls have a C7 (no lorries) sign within 150 m, 19 of them within
    30 m. Some carry time windows for deliveries, such as 6.00–11.30.
- **So:** the canal streets are an area with a 2 t axle limit and no lorries.
  The heaviest normal vehicle is a van or a small delivery vehicle with a 2 t
  axle, about 20 kN per axle.

**Why this is not q yet:**
- **Walls with a werf:** the road is at street level, over the werfkelders.
  In plan it is 2.5–7 m from the walmuur on the Nieuwegracht and Kromme
  Nieuwegracht, and mostly 3–10 m on the Oudegracht. It does not stand on
  the soil the walmuur holds back. Its load reaches the walmuur only through
  the werfkelder.
  - The load on the werf itself is people and terraces: 5 kN/m² for
    pedestrians (NEN-EN 1991-1-1), at a = 0.
  - With q_eff = q · H²/(H² + a²), H ≈ 1.2 m and a ≈ 5 m, a road load counts
    for only about 5% of q.
- **[h] walls (street directly behind):** a of 1–3 m is a real input. q
  follows from the 2 t axle limit, for example by spreading a van over its
  footprint, or by a NEN-EN 1991 load model. That conversion belongs to the
  traffic model (other group members) and is not done here.
- **Traffic counts:** they only matter for the spread or the extreme value
  of q. The counts in `data/raw/*_csv/` are from streets outside the
  Wervengebied; see `data/raw/SOURCES.md`.

## Foundation and Foundation renewed

A timber decay model assumes that a wall stands on timber piles that have
been rotting since `Aanlegjaar`. That is only true for walls whose foundation
was never replaced.

**Background:**
- **Original foundation:** pine timber piles, about 180 mm in diameter and
  on average 4 m long, in two rows, with a timber screen about 2.5 m high
  between them [IBU, p. 4]. The piles and screen removed on rak 12–14 west
  date from the 1950s or 1960s [E114].
- **Why they rot:** in the 1980s the piles stood dry while a sewer was laid
  in the canal. They partly rotted, the walls settled and cracked
  horizontally and vertically [E156, p. 7]. The 2007–08 dive inspections found
  rotted pile heads and a screen in very poor state or gone [IBU]; TNO rated
  the foundations poor, with a poor to very poor outlook where the decay could
  be judged [TNO].
- **Renewal programme:** since 2013 the city has replaced the foundations rak
  by rak, with two methods (11th progress report, Antea Group 2019):
  - **steel sheet piles:** the old wall is dug free and removed, and the new
    wall is placed on a steel sheet pile. This was the only method until
    mid-2015.
  - **steel tube piles:** steel tube piles are screwed through the old wall,
    and a new prefabricated wall is placed on them. It is used where the werf
    is narrower than 3.5 m (3.0 m on the Nieuwegracht) or near trees.

**The register can't show this.** It has no foundation data. Its
`Aanlegjaar` is often not updated after a renewal: Rak 02 OZ still says 1880,
renewed in 2022, and Rak 11 WZ says 1650, renewed in 2019. No Damwand object
lies within 6 m of any walmuur.

**How it is filled:**
- **Hand-compiled source table:** status, method and year per rak and bank,
  in `data/raw/walmuur_foundation_sources.csv`. It is compiled from progress
  reports, the Antea study, the Erfgoed Utrecht archaeology reports 114, 156
  and 158, city news and neighbourhood letters. Every row names its
  documents, which are listed in `walmuur_foundation_documents.csv`.
- **Matching a register wall to a rak and bank:** through the city's
  `Werfmuren` layer (UtrechtOpen WFS), which labels every wall polygon with
  its rak and bank. This is needed because the projects say "rak 5 west"
  where the register says "Rak 05 ZZ". It also places Kromme Nieuwe Gracht
  001–004 in rak 22 and 005–009 in rak 21.
- **Single-wall overrides:** a row can apply to one wall only. This is used
  for Rak 04 ZZ and Rak 09 ZOZ.
- **Fallback:** a wall with no row counts as renewed if its `Aanlegjaar` is
  2013 or later (only Rak 10 OZ), and otherwise as still on timber piles.

| Foundation | Walls | Length |
|---|---|---|
| Renewed, steel sheet piles (one also part tube piles) | 11 | 1,450 m |
| Renewed, steel tube piles | 13 | 1,303 m |
| Renewed, concrete sheet piles (Rak 15 OZ, existing, stabilised in 2014) | 1 | 149 m |
| Renewed, method not stated (rak 4 west/zuid, 9 oost, 10 oost, 11 oost, 16) | 7 | 529 m |
| Timber piles, documented as not renewed (Rak 04 OZ, 05 NZ) | 2 | 140 m |
| Timber piles, renewal in progress (Rak 06 NZ, October 2026 to April 2027) | 1 | 44 m |
| Timber piles [t], assumed: no renewal found (Rak 07 OZ, 08 OZ, 09 WZ, 09 WZ 01, Kromme Nieuwe Gracht 001–004) | 8 | 147 m |
| Unclear [u] (Rak 03 OZ, 06 ZZ, 09 ZOZ, Kromme Nieuwe Gracht 005–009) | 8 | 301 m |

**Markers:**
- **? (4 walls: Rak 13 OZ, 14 OZ, 18 OZ, 18 WZ):** the method is inferred,
  not stated for that rak. Rak 13 OZ and 14 OZ are dated 2015, when only
  sheet piles were used. Rak 18 got tube piles like the rest of the
  Nieuwegracht.
- **[p] (Rak 12 OZ, 18 OZ and WZ, 20 OZ and WZ):** part of the wall is not
  renewed yet. That is the last 30 m of Rak 12 OZ near the Weesbrug, and
  about 40 m spread over rak 18 and 20, whose location is not given.

**Check against the city's totals:** the renewed walls add up to 3.43 km.
Without the parts still to do, that is about 3.36 km, close to the city's
3,356 m of restored walmuur (Uitvoeringsprogramma 2025–2028). The city's total
of 4,136 m is longer than the register's 51 walmuren (4,062 m).

**What it means for the strength model:** 11 of the 29 red/orange walls are
already renewed on steel, 1,267 m of their 1,885 m:
- Rak 01 WZ, 02 OZ, 02 WZ and 11 WZ
- Rak 16 NOZ, WZ and ZOZ
- Rak 18 OZ and WZ, 19 WZ and 20 WZ

Their old `Aanlegjaar` put them in the screening, but the timber decay model
doesn't describe their foundation. Only 11 red/orange walls (331 m) are on
timber piles, 8 of them by assumption. The status of 7 more (287 m) is
unclear. Since 30 October 2026 the screening counts the renewed walls from
their renewal year, so these 11 are green there.

**How far to trust it:**
- **Unclear walls:** rak 3 oost started in 2022 and rak 6 west was planned
  for 2023/2024, but no document found says either was finished. Rak 21 was
  stopped in 2017 after sheet piles were placed. The city's records
  (Wervenkadaster) would settle these.
- **Rak 9 ZOZ:** rak 9 oost was delivered in 2021, but the register keeps
  1800 for this part, and the 2025–2028 programme still lists remaining
  walls on rak 9.
- **Renewal years:** the completion year in the documents, or the register
  year when it falls inside the works.
- **Effect on Foundation renewed:** for a renewed wall this is the year of the
  new steel foundation. It no longer gives t for timber decay.

**Sources.** The key in brackets is the one used in the `sources` column of
`walmuur_foundation_sources.csv` and `walmuur_foundation.csv`.

Programme reports:
- [ANTEA] Antea Group, *Onderzoek Wal- en Kluismuren, eindrapportage*,
  14 November 2019. Its appendix summarises progress reports 1–12
  (2009–2019).
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/8fdd67ee-61f8-493c-a7b2-aa38c58ff36c
- [VGR11] Gemeente Utrecht, *11e voortgangsrapportage project herstel wal- en
  kluismuren*, 23 February 2018.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/a313d731-0d9d-49d0-a14a-9a33ef0ebe19
- [VGR2122] Gemeente Utrecht, *Programma Wervengebied voortgangsrapportage
  juli 2021 – februari 2022*.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/eb37e3b0-ae3f-4488-838b-9181f3d18dea
- [VGR2223] Gemeente Utrecht, *Programma Wervengebied voortgangsrapportage
  september 2022 – maart 2023*.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/4dc08c25-a48d-432d-a518-8f2dd44e62c3
- [UP2427] Gemeente Utrecht, *Programma Werk aan de Werf,
  Uitvoeringsprogramma 2024–2027*.
  https://www.keldergewelf.nl/wp-content/uploads/2024/07/Uitvoeringsprogramma-wervengebied-2024-2027.pdf
- [UP2528] Gemeente Utrecht, *Programma Werk aan de Werf,
  Uitvoeringsprogramma 2025–2028*.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/d3f21423-a615-4f53-add6-78f0fa775498

Archaeology reports (Erfgoed Utrecht):
- [E114] *Basisrapportage Archeologie 114: Oudegracht rakken 12 west, 13 west
  en 14 west*. Also used: the timber piles and plank screen date from the
  1950s or 1960s; renovation in the 1950s–60s and restoration in 1975–1985.
  https://erfgoed.utrecht.nl/fileadmin/uploads/documenten/zz-erfgoed/publicaties/rapporten-archeologie/114-Rapportage.pdf
- [E156] *Basisrapportage Archeologie 156: Oudegracht rakken 1, 4, 10, 11 en
  15 west*. Also used: the cross-section of a type 2 walmuur (Afb. 3.1, p. 18,
  2 m scale bar); the cause of the damage (p. 7); the removed all-masonry
  walmuur of 40 cm and the usual 1960s walls being largely concrete (p. 23);
  peaty fill around 0.0 m NAP in rak 1 west only (pp. 24, 33); the piles
  S13–S19 belong to a stair (pp. 24–26).
  https://erfgoed.utrecht.nl/fileadmin/uploads/documenten/zz-erfgoed/publicaties/rapporten-archeologie/156-Oudegracht-rakken.pdf
- [E158] *Basisrapportage Archeologie 158: Oudegracht rakken 1 oost, 3 west
  en 12 oost*. Also used: werf +1.10 m NAP and the underside of the walmuur at
  −0.08 m NAP (rak 3 west), canal level +0.6 m NAP. Its "+0,05 m NAP" is the
  depth of the excavation behind the new sheet pile, not a pile-head level.
  https://erfgoed.utrecht.nl/fileadmin/uploads/documenten/zz-erfgoed/publicaties/rapporten-archeologie/158-Rapportage.pdf

Wall structure, piles and the failure model:
- [IBU] IBU Stadsingenieurs, *Ontwerpnotitie herstel lage walmuren,
  Restauratie wal- en kluismuren*, about 2010. The two types of low walmuur
  with their drawings (Afb. 2.1.1a and 2.2.1a); the timber piles (about
  180 mm, on average 4 m, two rows, front row of type 2 raked 10:1, screen
  about 2.5 m); the damage found in the 2007–08 dive inspections.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/7a80a169-48bb-4f58-964c-518caf0f6d7c
- [TNO] TNO, *Eindbeoordeling kademuren Utrecht*, TNO-034-DTM-2009-01978,
  14 May 2009. A re-rating of the Baars-CIPRO and SHR inspections of 2008.
  Used: what the divers found per rak, watersloof or concrete floor
  (Bijlage G, in `data/raw/walmuur_tno2009_type.csv`), and the conclusions
  (p. 7). Compiled but not used: the Pilodyn classes of the planks and
  watersloof per rak (Bijlage G)
  and the remaining-diameter rule d = D − 2(I + 5) (Bijlage C). Bijlagen A and
  B, with the pile values, are blank in the public copy.
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/6b59e223-7ec8-40fe-a845-c1223322df17
- [HEMEL23] Hemel, M.-J. (2023). *Amsterdam quays under pressure: modelling and
  testing of historic canal walls*. PhD thesis, TU Delft. Used: the mechanism
  (lateral failure of the pile foundation, section 1.2.2), the soft shell of
  115-year-old pine piles, 21 mm on average and up to 45 mm (chapter 3
  conclusions), MOR, E, the CoV of the diameter and the subgrade moduli of
  clay and peat (Table 7.1), the shell growth of 0.17 mm/yr (section 7.3.2),
  and the Amsterdam case wall for comparison (section 7.3.2).
- [HEMEL24] Hemel, M.-J., Peters, D.J., Schweckendiek, T., & Jonkman, S.N.
  (2024). Reliability updating for lateral failure of historic quay walls.
  *Georisk*, 18(4), 882–903. Used: the surcharge q ~ Normal(7 kPa, 0.2) and
  updating with proven strength (eq. 12).
- [NEN8700] NEN 8700:2011+A1:2020, *Beoordeling van de constructieve
  veiligheid van een bestaand bouwwerk*, Table B.2: β at the rejection level
  1.8 (CC1), 2.5 (CC2), 3.3 (CC3), reference period 15 years.
- [NEN1991] NEN-EN 1991-1-1: 5 kN/m² for pedestrians on the werf (not checked
  against the standard text).
- Checked, no pile data: Royal HaskoningDHV, *Second opinion herstart
  werkzaamheden kademuren Kromme Nieuwegracht Utrecht*, 11 October 2018,
  https://utrecht.bestuurlijkeinformatie.nl/Document/View/6ce7424b-761d-46a2-92d0-bf343cf15fc5

City news:
- [NEWS20220428] *7 vergroeide werfbomen bij de Jansbrug moeten worden
  gekapt*, 28 April 2022.
  https://www.utrecht.nl/nieuws/nieuwsbericht-gemeente-utrecht/7-vergroeide-werfbomen-bij-de-jansbrug-moeten-worden-gekapt
- [NEWS20220929] *149 meter extra walmuur aan de Oudegracht hersteld*,
  29 September 2022.
  https://www.utrecht.nl/nieuws/nieuwsbericht-gemeente-utrecht/149-meter-extra-walmuur-aan-de-oudegracht-hersteld

Neighbourhood letters (wijkberichten):
- [WB202503J] Oudegracht Viebrug–Jacobibrug, werk walmuur in najaar verder,
  March 2025.
  https://wijkberichten.utrecht.nl/wijkberichten/2025-jan-apr/2025-03-wijkbericht-oudegracht-viebrug-jacobibrug-werk-walmuur-in-najaar-verder.pdf
- [WB202507J] Tweede deel walmuur Oudegracht Jacobibrug–Viebrug, July 2025.
  https://wijkberichten.utrecht.nl/wijkberichten/2025-mei-aug/2025-07-wijkbericht-2e-deel-walmuur-Oudegracht-Jacobibrug-Viebrug.pdf
- [WB202608J] Walmuur Oudegracht tussen Jacobibrug en Viebrug is klaar,
  August 2026.
  https://wijkberichten.utrecht.nl/wijkberichten/2026-mei-aug/2026-08-wijkbericht-walmuur-oudegracht-tussen-jacobibrug-en-viebrug-is-klaar.pdf
- [WB202503B] Rak 5 west, vertraging werkzaamheden Bakkerbrug–Bezembrug,
  March 2025.
  https://wijkberichten.utrecht.nl/wijkberichten/2025-jan-apr/2025-03-wijkbericht-rak-5-west-vertraging-werkzaamheden-Bakkerbrug-Bezemstraat.pdf
- [WB202606B] Werkzaamheden walmuur tussen Bakkerbrug en Bezembrug afgerond,
  June 2026.
  https://wijkberichten.utrecht.nl/wijkberichten/2026-mei-aug/2026-06-wijkbericht-werkzaamheden-walmuur-tussen-bakkerbrug-en-bezembrug-afgerond.pdf
- [WB202608S] Start werkzaamheden Stadhuisbrug–Bezembrug, August 2026.
  https://wijkberichten.utrecht.nl/wijkberichten/2026-mei-aug/2026-08-wijkbericht-start-werkzaamheden-stadhuisbrug-bezembrug.pdf

Also used, but not cited per rak:
- **Werven project overview:** status of the current projects and the totals
  of walmuur restored and to go.
  https://www.utrecht.nl/wonen-en-leven/bouwprojecten-en-stedelijke-ontwikkeling/bouwprojecten/binnenstad/herstel-werven/
- **News on the Uitvoeringsprogramma 2026–2030 (April 2026):** 3,356 of
  4,136 m restored.
  https://utrecht.nieuws.nl/stadsnieuws/gemeente-utrecht-stelt-uitvoeringsprogramma-wervengebied-2026-2030-vast
- **UtrechtOpen GeoServer, layer `Werfmuren`:** rak and bank of every wall
  polygon, used for the matching and saved in
  `data/raw/UtrechtOpen/werfmuren.geojson`.
  https://geodata.utrecht.nl/geoserver/UtrechtOpen/ows

## Failure probability per wall

Computed by `scripts/StressCaclulation/FailureProbability.py` (step 8 above) for
the 17 walmuren that still stand on their old timber foundation (foundation
status not renewed, in progress or unclear) and have a werf. The 32 renewed
walls stand on a new steel foundation that this model does not describe. Two
walls on timber have no werf, as the map check below found: Kromme Nieuwe
Gracht 001 and Oude Gracht Rak 07 OZ. There the street runs to the water, so
the wall holds up the street, a different structure from the two types below;
they are not computed. Output:
`data/processed/walmuur_failure_probability.csv` (Pf and β per wall, wall type
and year), `walmuur_failure_draws.json` (600 draws per wall and type, for the
scatter plots) and `walmuur_failure_inputs.csv` (every input, its distribution
and source).

**The wall.** Two types of low walmuur stand on timber piles [IBU, pp. 4–5]:

| | Type 1 | Type 2 |
|---|---|---|
| Built | late 19th, early 20th century | after WWII until the 1970s |
| Wall | stepped masonry, 0.39 m at the top, 0.78 m at the base | one-brick facing with a tamped-concrete backing |
| Floor | timber floor on two timber beams (kesp), 0.91 m wide | reinforced concrete, 1.37 m wide, 0.34 m thick |
| Piles | two vertical rows about 0.7 m apart | front row raked 10:1, rows about 0.9 m apart |
| Underside of the floor | −0.55 m NAP | −0.22 m NAP (about 0.5 m higher) |

Both are measured on the drawings at the same scale: type 2 on [E156] Afb. 3.1
with its 2 m scale bar (the same drawing as [IBU] Afb. 2.2.1a), type 1 on [IBU]
Afb. 2.1.1a. Checks: the type 2 drawing puts the werf at +1.14 m NAP and the
water at +0.67 m NAP, and the type 1 top width of 0.39 m matches the 40 cm
all-masonry walmuur removed on rak 1 west [E156]. The polygons are in
`SECTIONS` of `WallResistance.py`.

**Which type a wall is** is not known, but TNO's notes of the 2008 dive
inspections [TNO, Bijlage G] say what the divers found per rak. A watersloof,
the timber beam on the pile heads, only exists in type 1; type 2 replaced it
with a concrete floor [IBU, p. 5]. So each rak gets a chance of type 2
(`data/raw/walmuur_tno2009_type.csv`):

| Rak | Found | Chance of type 2 |
|---|---|---|
| 3, 4, 5, 6 | watersloof, no concrete floor | 20% |
| 21 (Kromme Nieuwe Gracht 005–009) | watersloof in two segments, a concrete floor in one, most not reachable | 50% |
| 22 (Kromme Nieuwe Gracht 001–004) | concrete floor in three segments | 90% |
| 7, 8, 9 | no hint | 80%, as [E156] calls the usual 1960s walls largely concrete |

TNO does not say on which bank each segment lies, so these are chances, not
certainties.

**Two ways to fail.** A wall fails when either happens.
1. **Overturning.** The wall, its floor and the soil on the floor tip about the
   front pile row. What resists: the weight of each part (below the water
   γ − γ_w) and wall friction on the back of the body (δ = ⅔φ, with φ from K).
   What drives: S_total over the height from the werf to the underside of the
   floor (`TotalStress.py`).
2. **Pile bending** [HEMEL23]. The rear row carries what the moment balance
   gives it, the front row the rest of the weight. The front row of type 2 is
   raked and takes a tenth of its force horizontally; the rest of the
   horizontal force bends the piles of both rows (beam on springs: head fixed
   in the concrete floor for type 2, pinned into the kesp for type 1). A pile
   fails when bending plus axial stress in its sound core passes the bending
   strength (MOR). The sound core is what is left inside the rotted outer
   shell: d = D0 − 2 × shell. The condition of the piles is not known per
   wall and will not become known, so every wall gets the same broad range:
   a shell of 0 to 45 mm today, uniform. That is the whole range Hemel
   measured in 115-year-old pine piles in Amsterdam, 21 mm on average and up
   to 45 mm [HEMEL23, chapter 3]. After today the shell grows 0.10–0.25 mm
   per year (0.17 mm/yr in [HEMEL23], 7.3.2). `PileStrength.py`.

**Proven strength** [HEMEL24, eq. 12]. Every one of these walls stands today.
Draws in which the wall would already fail under its soil and water alone,
without surcharge, cannot be the real wall and are left out of the updated Pf.
The same check updates the type: a type for which few draws stand becomes less
likely. The CSV has both the plain Pf (`pf`, `beta`) and the updated one
(`pf_updated`, `beta_updated`).

**Years.** 2026, and 2041 at the end of a 15-year reference period [NEN8700].
Only the rot of the piles changes between the two.

**From the data, per wall:** the werf level (AHN, or a map check, see below),
the soil type (DINO) and the chance of each wall type (TNO, above). The
Pilodyn classes TNO measured on the screen planks and the watersloof are not
used: they are not the piles, and the broad range above covers them.

**Guesses, the same for every wall** (all in `walmuur_failure_inputs.csv`):

| Input | Distribution | Basis |
|---|---|---|
| Werf level of Kromme Nieuwe Gracht 005–007 (werf seen, level not read) | Uniform(1.0, 1.6) m NAP | the range of the measured werven |
| Soft shell of the piles today | Uniform(0, 45) mm | [HEMEL23] chapter 3 |
| Foundation level | drawing ± Uniform(−0.15, 0.15) m | schematic drawings; [E158] gives −0.08 m NAP for the wall underside |
| Model factor on the resisting moment | Lognormal(1, CoV 0.15) | dimensions read from schematic drawings |
| Tamped concrete, reinforced concrete, timber | 23 (CoV 0.05), 25, 10 kN/m³ | typical values |
| Groundwater under the werf | Uniform(+0.5, +0.9) m NAP | around the canal level of +0.6 m NAP [E158] |
| Surcharge q at distance a | Normal(7 kPa, CoV 0.2) at Uniform(0, 3) m | [HEMEL24]; heavy for a pedestrian werf |
| Pile diameter D0 | Normal(180 mm, CoV 0.10) | [IBU] p. 4; CoV [HEMEL23] Table 7.1 |
| Pile spacing along the wall | Uniform(0.8, 1.2) m | [IBU] p. 4, "ca. 1 meter" |
| Shell growth after 2026 | Uniform(0.10, 0.25) mm/yr | around [HEMEL23] 7.3.2 |
| MOR, E, subgrade modulus k | Normal(22 MPa, 0.10), Normal(9 GPa, 0.20), Uniform(4,300, 10,000) kN/m³ | [HEMEL23] Table 7.1 (Amsterdam pine, clay and peat) |

**Results** (run of 30 October 2026, updated Pf, 2026): the best estimate,
with the chance of each type per rak, runs from β −0.06 (Rak 03 OZ: soft clay,
likely type 1) to 1.52 (Kromme Nieuwe Gracht 003); all 17 are below 1.8. For
type 2 alone β runs from 1.27 to 2.46 (9 of 17 below 1.8), for type 1 alone
from −0.91 to 1.07. For type 2 the piles fail more often than the wall tips
over (median Pf 0.054 against 0.004). By 2041 β drops another 0.02 to 0.15.
Walls with the same soil, rak and no werf measurement (Kromme Nieuwe Gracht
005–007) get the same result, as nothing in the data tells them apart. The
werf correction of 30 October 2026 (see the section on H) raised Kromme Nieuwe
Gracht 002 from 0.79 to 1.37 and 009 from 0.73 to 1.45. Rak 03 OZ went from
0.12 to −0.06: both types do better with the lower werf, but more type-1 draws
now stand today, so the proven-strength check moves its chance of type 2 less
(0.20 → 0.34 instead of 0.60).

**Checking the [h] walls on a map.** For 9 walls AHN found street-level ground
(+1.6 m NAP or more) beside the wall, so the model now assumes a werf level.
`data/raw/walmuur_werf_check.csv` lists them, with a Google Maps link and a
Street View link for each, and the lowest and highest AHN level beside the
wall. For each wall:
1. Open the map link (switch to satellite) and the Street View link.
2. Decide whether there is a werf: a low quay at about 1 m above the water,
   in front of the street, usually with steps down. Then fill in
   `has_werf` = `yes`. If the street runs straight to the water and the
   wall holds up the street, fill in `no`.
3. For `yes`: the werf level is usually the lowest AHN value
   (`ahn_lowest_nap`) when that is below +1.6 m NAP; the high values are a
   bridge, stairs or the street. Put it in `werf_nap`. When all values are
   high (Rak 07 OZ, Kromme Nieuwe Gracht 005–007), leave `werf_nap` empty: the
   model then keeps Uniform(1.0, 1.6) m NAP. To read the level yourself, the
   AHN viewer on ahn.nl gives the height of any point you click.
4. Add what you saw in `note`, then rerun `FailureProbability.py`. A wall with
   `no` is left out, since it is a different structure from the low walmuur
   sections; a wall with a level gets Normal(level, 0.05 m).

Done on 21 October 2026: Kromme Nieuwe Gracht 001 and Rak 07 OZ have no werf;
the other 7 have one. For Rak 06 NZ, Rak 06 ZZ, Rak 08 OZ and Kromme Nieuwe
Gracht 008 the level is the lowest AHN point beside the wall (+0.99 to
+1.21 m NAP), not a level read on site; for Kromme Nieuwe Gracht 005–007 every
AHN point is at street level, so their level stays assumed.

**What is still missing, and what it changes:**

| Missing | Used now | Effect |
|---|---|---|
| Wall type per wall | chance per rak from TNO's dive notes | largest: type 1 gives a β 1.4 to 2.4 lower |
| Pile condition | not available; a shell of 0–45 mm for every wall | the pile part of Pf, the larger part for type 2 |
| Werf level of Kromme Nieuwe Gracht 005–007 | Uniform(1.0, 1.6) m NAP (werf seen on the map, level not read) | those three walls get identical results |
| A model for walls without a werf (Kromme Nieuwe Gracht 001, Rak 07 OZ) | not computed | two walls on timber have no Pf |
| Pile spacing and the foundation level (old design drawings, "bestektekeningen") | guesses above | load per pile, H |

The consequence class is not chosen; the results are shown against all three
rejection levels of NEN 8700: β 1.8 (CC1), 2.5 (CC2) and 3.3 (CC3).

## Columns not in the data

These columns are a dash for every wall. Each needs an assumption or a data
request to the city.

| Column | Needed for | What is used now |
|---|---|---|
| Canal bottom | H = werf level − canal bottom | Soundings per rak, to request from the city. Until then the bottom is taken at the wall underside, −0.08 m NAP; see the section on H. |
| Pile diameter | D0, the initial pile diameter | About 180 mm for every wall [IBU, p. 4]. The 15–20 cm piles S13–S19 in report 156 held an earlier stair, not the walmuur, and are not used. |
| Traffic load q | q [kN/m²] behind the wall | 5 kN/m² for pedestrians on the werf (NEN-EN 1991-1-1). q from the 2 t axle limit is for the traffic model of other group members; see the section on traffic. |
| CC | Consequence class, which sets β_min (NEN 8700) | Not chosen yet. |

## Bottom row ("with data")

Each column shows how many of the 51 walls have a value from the data:
- Dashes don't count.
- Cells marked [c] (not a wall thickness) don't count.
- Cells marked [e] (assumed thickness) are counted separately as "assumed".
- Cells marked [g] (estimated H) are counted separately as "estimated".
- Cells marked [h] (maybe no werf) don't count.
- Cells marked [t] (timber piles assumed) are counted separately as "assumed".
- Cells marked [u] (foundation unclear) don't count.

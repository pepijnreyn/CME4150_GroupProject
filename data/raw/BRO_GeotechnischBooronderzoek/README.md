# DINO borehole logs: Utrecht city centre

This folder holds the 76 DINO borehole logs (CSV) from a BROloket download,
plus the download's map file. `scripts/build_soil_type.py` uses them to give
each wall a soil type. The folder name is left over from the original
download.

Treat the data as read-only and write anything derived to `data/processed/`.

- **Source:** BROloket (broloket.nl), downloaded on 2026-10-14.
- **Area (WGS84):** lon 5.110–5.128, lat 52.083–52.096.

## Contents

| Path | What | Used by |
|---|---|---|
| `DINO_GeologischBooronderzoekBoormonsterprofiel/B31H*.csv` | 76 borehole logs: location, ground level, layers | `build_soil_type.py` |
| `locatie_levering.kml` | Map file of the download: one point per file | `build_soil_type.py` (boring lon/lat) |

## Removed on 2026-10-20

The original download had 8 datasets (162 MB). Everything no script used was
deleted:

| Removed | Why it wasn't kept |
|---|---|
| BRO CPTs (`BRO_GeotechnischSondeeronderzoek/`, 33 CPTs) | 27 of 33 were pre-drilled ≥1 m (median 2 m), so they miss most of the retained height of the walls. |
| BRO hand borings (`BRO_GeotechnischBooronderzoek/`, 13) | One site, about 650 m from the canals. |
| BRO groundwater wells and level records (`BRO_Grondwatermonitoring/`) | Already covered by `data/raw/APIDatacollection/`. |
| BRO groundwater usage (`BRO_Grondwatergebruik/`) | Permits for soil-energy (WKO) wells 17–37 m deep, not relevant to quay walls. |
| DINO CPTs (`DINO_GeotechnischSondeeronderzoek/`) | Scanned images and stubs pointing to the BRO CPTs. |
| DINO groundwater levels and chemistry | Historic series (e.g. 1959–1984), largely duplicating the BRO wells. |
| DINO borehole `.gef` files and scans (`.jpg`, `.pdf`) | Same layers as the CSV, or images only. |

To get any of these back, download the same area again from BROloket.

`locatie_levering.kml` still lists every file of the original download. Most
of those files are no longer on disk. The KML is about 3,800 lines, so search
it for `<name>` rather than reading it whole.

## DINO borehole CSV format

Each CSV holds several tables stacked in one file. Each table has a quoted
title row and then a header row, and an empty `,,,,` row ends the table.

- **`ALGEMENE GEGEVENS BORING`:** NITG ID, RD x/y (EPSG:28992),
  `Maaiveldhoogte (m tov NAP)`, `Datum boring`, `Einddiepte`, owner.
- **`ALGEMENE GEGEVENS LITHOLOGIE`:** who described the layers, and the
  description quality.
- **`LITHOLOGIE LAGEN`:** one row per layer.
  - Top and bottom are in m below ground level.
  - The other columns are `Hoofdgrondsoort`, `Zandmediaanklasse` and the
    admixtures (`Bijmenging …`).

Values of `Hoofdgrondsoort` across the 76 logs:
- zand, klei, leem, veen, grind, mergel, schelpen
- fill: puin, baksteen, stenen, wegverhardingsmateriaal
- no description: niet benoemd, geen monster

## Things to know

- **Depths are below the boring's own ground level.** To get m NAP, take
  `Maaiveldhoogte` minus the depth. Five logs have no ground level;
  `build_soil_type.py` skips them.
- **Wharf and street borings:**
  - Borings drilled on the werf start at +0.9 to +1.7 m NAP. Street-level
    borings start at +2.3 m NAP and higher.
  - For a wall that holds back the soil under the street, the top metres of a
    werf boring are the wrong soil.
- **The logs are old and coarse.** They date from 1862 to 2014; e.g.
  `B31H0175` (1925) has description quality `E`, and many fields are
  `onbekend`.
- **Some borings share one location** (e.g. B31H0176/0177/0178). They count
  as separate borings.
- **Nearby borings often disagree on the main soil type.** For the method and
  its caveats, see `figures/wervengebied_data_table_README.md`.

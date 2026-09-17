# Sources for files in data/raw

One row per file. Fill in when you add data.

| File | Source | URL | Downloaded | Notes / known gaps |
|---|---|---|---|---|
| `Output areaal GU TU Delft 26-08.json` | Gemeente Utrecht, delivered to TU Delft for the team challenge | n/a (direct delivery) | 2025-08-26 (file date) | 3,817 objects. No condition scores, no foundation or cost data. `Eindjaar` is design life, not remaining life. See `docs/output_areaal_overview.md`. |
| `APIDatacollection/gm_gmw.geojson` | BRO grondwatermonitoring via PDOK OGC API | https://api.pdok.nl/tno/bro-grondwatermonitoring-in-samenhang-karakteristieken/ogc/v1 | 2026-09-16 | 1,664 monitoring wells in bbox 4.93,52.02,5.25,52.16. Has ground level (m NAP), construction/removal date, owner. Fetched by `scripts/fetch_bro_grondwater.py`. |
| `APIDatacollection/gm_gmw_monitoringtube.geojson` | idem | idem | 2026-09-16 | 2,527 tubes. Screen top/bottom in m NAP; ground level minus screen top tells you whether a tube is phreatic or in a deep aquifer. Needed to filter the head series. |
| `APIDatacollection/gm_gld.geojson` | idem | idem | 2026-09-16 | 1,849 head time series (metadata only) covering 319,590 observations. `series_*_csv_url` points at the values themselves. 843 series still measured in 2024 or later. |
| `APIDatacollection/gm_gar.geojson` | idem | idem | 2026-09-16 | 823 water quality samples. Composition only; no use for pile rot unless we look at aggressive groundwater. |
| `APIDatacollection/series/*.csv` | idem, `publiek.broservices.nl` CSV export | see `series_index.csv` | 2026-09-16 | Head values per date in m NAP for the 805 phreatic series (screen top within 8 m of the surface) still measured after 2020. `series_index.csv` lists location, screen depth and record length per file. Assessed values where available, otherwise preliminary. |
| `APIDatacollection/APIdocumentationBRO.JSON` | PDOK | idem, `/api` | 2026-09-16 | OpenAPI 3.0 spec for the API above. Documentation, not data. |

Known gap for the BRO data: the wells are not on the quays. Only 1 of 158
`Kademuur` objects has a head series within 50 m and 19 within 100 m; 74% have
one within 250 m. Groundwater is therefore a neighbourhood-level driver that has
to be interpolated, not a per-wall measurement. Pile head levels are not in the
BRO either, so the series give the head in m NAP, not the depth of water above
or below the timber.

Starting points from the assignment: data.utrecht.nl, kaart.utrecht.nl,
kenniscentrum-werven.utrecht.nl, pdok.nl, broloket.nl, ahn.nl,
bodemdalingskaart.nl, knmi.nl/klimaatscenarios, cbs.nl, hdsr.nl.
trees: https://gu-geo.maps.arcgis.com/apps/instant/sidebar/index.html?appid=bc057cc234c741f38af88417288e9efb
rainfall: https://www.daggegevens.knmi.nl/klimatologie/daggegevens

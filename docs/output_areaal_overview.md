# `Output areaal GU TU Delft 26-08.json` — practical overview

Asset register of the Municipality of Utrecht (Gemeente Utrecht, "GU"), delivered
to TU Delft on 26-08. This is the primary object inventory for the quay wall
challenge: every quay wall, werfmuur, bank protection and bridge the municipality
manages, with geometry and a fixed set of attributes.

## Format at a glance

| | |
|---|---|
| Format | GeoJSON `FeatureCollection`, 3.9 MB, one flat layer |
| Features | 3,817 |
| Geometry | 2,341 Polygon, 1,247 LineString, 229 Point (all 2D) |
| CRS | none declared, so WGS84 lon/lat per the GeoJSON spec |
| Extent | lon 4.986–5.181, lat 52.030–52.132 (Utrecht municipality) |
| Attributes | 20 fields, present on every feature, **all typed as string** |

Geometry type follows object type, not a rule of the file. Walls, quay walls,
bank protections and sheet piles are lines; bridges, stairs and steigers are
polygon footprints; mooring posts are points. A handful of objects break that
pattern, so never assume geometry type from `Objecttype`.

## The 20 attribute fields

| Field | Filled | Unique | Notes |
|---|---|---|---|
| `Thema` | 100% | 5 | Top level: Kunstwerk 2343, Meubilair 1082, Water 225, Gebouwen 166, Wegen 1 |
| `Subthema` | 100% | 23 | Vaste brug 1123, Muur 913, Beschoeiing 450, Damwand 359, Kademuur 158 |
| `Nummer` | 100% | 3,807 | Asset ID with a meaningful prefix, see below. Not unique |
| `Naam` | 99% | 3,726 | Free text. 693 carry a "RAK" canal-section code |
| `Modaliteit` | 23% | 26 | Traffic load class, effectively bridges only |
| `Status` | 99% | 7 | In gebruik 3702, Vervallen 61, Niet te beoordelen 18 |
| `Objecttype` | 100% | 22 | The workhorse classification field |
| `Type` | 17% | 22 | Sub-variant, too sparse to rely on |
| `Nen2767 beheerobject` | 92% | 17 | NEN 2767 maintenance class: Grondkering 1894, Bruggen (vast) 1113 |
| `Kunstwerktype` | 61% | 38 | Werfmuur 723, Brug klein 397, Damwand 281, Keerwand 137 |
| `Kunstwerktype Utrecht` | 61% | 38 | **Exact duplicate of `Kunstwerktype`. Drop one** |
| `Bouwmateriaal` | 85% | 25 | Metselwerk 1038, Hout 978, Beton 649, Staal 253. Multi-value, comma separated |
| `Aanlegjaar` | 88% | 185 | Year built, 1250–2118 |
| `Eindjaar` | 84% | 232 | End of theoretical design life, 1330–2198 |
| `Lengte` | 93% | — | Metres |
| `Breedte` | 63% | — | Metres |
| `Oppervlakte` | 66% | — | m² |
| `Hoogte` | 19% | — | Metres. Sparse, but present for most werfmuren |
| `Lengteoppervlak` | 94% | — | Length for line objects, area for polygon objects. **Mixed units in one column** |
| `Valhoogte` | 23% | — | Drop height, relevant to the safety branch of the fault tree |

### `Nummer` prefixes

The first two letters encode the object family and are more reliable than the
sparse classification fields.

| Prefix | Meaning | Count |
|---|---|---|
| `BR` | Vaste brug | 1,117 |
| `WF` | Werfmuur | 832 |
| `BS` | Beschoeiing / damwand / kademuur | ~750 |
| `WC` | Meerpaal, geleidewerk, meerstoel | ~220 |
| `ST` | Steiger | 160 |
| `KW` | Keerwand | 146 |
| `TP` | Trap | 143 |
| `KM` | Kademuur / damwand | 165 |
| `DW` | Damwand | 50 |
| `VD`, `OD`, `BB`, `SL` | Viaduct, onderdoorgang, beweegbare brug, sluis | small |

## The subset that matters for this challenge

Filtering `Objecttype` to Muur, Kademuur, Beschoeiing and Damwand gives **1,951
objects, 146.8 km of soil-retaining structure**. That is the study population.

| Objecttype | n | Total length | Median | Longest |
|---|---|---|---|---|
| Beschoeiing | 451 | 75.4 km | 99 m | 1,282 m |
| Damwand | 358 | 46.9 km | 66 m | 1,514 m |
| Muur | 984 | 12.9 km | 6.3 m | 461 m |
| Kademuur | 156 | 11.7 km | 45 m | 427 m |

The `Muur` group is misleading at first look. Those 984 short segments are mostly
the historic canal walls: 721 are `Kunstwerktype` Werfmuur and 110 Kluismuur,
cut into per-address segments of a few metres each along the Oude Gracht and
Nieuwegracht. Materials for the whole family are Metselwerk 926, Hout 407, Beton
151, Staal 128, which cleanly separates the historic masonry stock from the
modern timber and steel bank protection.

Construction years split the population into two very different assets:

| Period | n |
|---|---|
| 1250–1499 (medieval canal walls) | 206 |
| 1500–1899 | 190 |
| 1900–1949 | 515 |
| 1950–1999 | 341 |
| 2000+ | 515 |
| missing | 184 |

A separate `Subthema` value **`Onderzoek werfmuren`** holds 73 polygons, 61
werfmuur and 12 kluismuur, with material blank on 71 of them. These read as an
active investigation programme rather than normal register entries. Decide
explicitly whether to include them and say so in the report.

## Data quality, read this before modelling

1. **Everything is a string.** Cast on load. Six `Lengte`, one `Breedte`, nine
   `Valhoogte` values use a comma decimal separator, and 44 `Lengteoppervlak`
   values carry a unit suffix such as `0.58 m2`. Naive `float()` drops them.
2. **Empty is spelled two ways.** Blank string, and the literal text `None` in 61
   `Hoogte`, 21 `Oppervlakte`, 18 `Breedte` and 4 `Eindjaar` cells.
3. **`Eindjaar` is a design-life bookkeeping figure, not a prediction.** It is
   `Aanlegjaar` plus a standard term: 80 years for 1,602 objects, 25 for 689, 40
   for 477, 60 for 368. For the medieval walls this produces end years in the
   1500s. **1,084 in-use quay-family objects already have an `Eindjaar` in the
   past.** Treat the pair as (build year, assumed design life), never as a
   remaining-life estimate.
4. **13 objects have `Eindjaar` at or before `Aanlegjaar`**, four of them exactly
   40 years earlier. Data entry errors.
5. **Stray values in categorical columns.** `Status` contains one `29`,
   `Nen2767 beheerobject` one `101`, `Modaliteit` six JSON-looking strings such
   as `["21","06"]`. A handful of rows are shifted by one column.
6. **Duplicate IDs.** `WF06` appears 9 times, `DW050005` and `BR090019` twice.
   `Nummer` is not a safe join key without deduplication.
7. **Implausible outliers.** `Aanlegjaar` max 2118, `Eindjaar` max 2198,
   `Hoogte` max 380 m, `Valhoogte` min −0.2. Clip or exclude.
8. **Sparse columns.** `Hoogte` 19%, `Type` 17%, `Valhoogte` 23%. Any model using
   them is fitted on a fifth of the data, and that fifth is not a random sample.
9. **`Lengteoppervlak` mixes metres and square metres.** Use `Lengte` and
   `Oppervlakte` separately instead.

## Loading it

```python
import geopandas as gpd
import pandas as pd

gdf = gpd.read_file("data/raw/Output areaal GU TU Delft 26-08.json")
gdf = gdf.set_crs(4326).to_crs(28992)          # RD New, for metric work

NUM = ["Aanlegjaar", "Eindjaar", "Lengte", "Breedte",
       "Oppervlakte", "Hoogte", "Valhoogte"]

def to_num(s):
    return pd.to_numeric(
        s.astype(str)
         .str.replace(r"\s*m2?$", "", regex=True)
         .str.replace(",", ".", regex=False)
         .replace({"None": None, "": None}),
        errors="coerce",
    )

gdf[NUM] = gdf[NUM].apply(to_num)
gdf = gdf.drop(columns=["Kunstwerktype Utrecht"])   # duplicate of Kunstwerktype

quay = gdf[gdf["Objecttype"].isin(["Muur", "Kademuur", "Beschoeiing", "Damwand"])]
```

Reproject before measuring anything. Lengths computed in degrees are meaningless,
and the `Lengte` column should be checked against the geometry rather than
trusted outright.

## What this file does not contain

No condition scores or inspection results, no NEN 2767 condition grade despite
the object-class column, no load capacity, no foundation type or pile
information, no maintenance history, and no cost data. Those have to come from
other sources listed in `data/raw/SOURCES.md`.

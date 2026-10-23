"""Soil type per wall from the DINO borings, as input for SoilForce.SOIL_TYPES.

For every wall:

  1. Decide which soil the wall holds back:
       walmuur      the soil under the werf, from +1.10 to -0.08 m NAP;
       other walls  the soil under the street, the top H metres.
  2. Find the nearest boring within 250 m that describes that soil.
  3. In that boring, add up how many metres of clay-like and sand-like soil
     lie in that range.
  4. Classify: at least 70% clay-like -> soft_clay_peat,
               at least 70% sand-like -> sand,
               otherwise              -> mixed.

The walls are the ones of build_masonry_data_gaps.py (they get a failure
probability) plus the 22 green walmuren, so that table_wervengebied_data.py
can show all 51 walmuren.

Choices, so they can be checked or changed (all are constants below):
  - Only the DINO borings are used. The BRO CPTs are mostly pre-drilled
    through the top 2 m, and the BRO hand borings are one site about 650 m
    from the canals (see the README in the BRO_GeotechnischBooronderzoek folder).
  - A walmuur stands between the werf and the canal and holds back the soil
    under the werf, from the werf down to the underside of the wall. Erfgoed
    Utrecht report 158 (rak 3 west) puts the werf at +1.10 m NAP and the
    underside at -0.08 m NAP; `Hoogte` is empty for all walmuren. Every
    boring reaches that level, so all borings can be used.
  - A werfmuur holds back the soil under the street, from street level down
    to the werf. Borings drilled on the werf (ground level below +2.0 m NAP)
    start below that soil, so they are skipped for these walls. This is an
    assumption about the wall geometry, not something the data says.
  - Fill (puin, baksteen, ...) and undescribed layers count as neither clay
    nor sand, so a profile with a lot of fill ends up "mixed".
  - Other walls without a usable height get H = 3 m (the median is 3.1 m).
  - Wall locations are the centroids in objects_groundwater.csv, so run
    build_groundwater_layer.py first.

To show how certain the result is, the output also counts the borings within
150 m that describe the same soil, and how many of them give the same type.

Writes data/processed/masonry_walls_soil.csv, one row per wall.
Run: python scripts/build_soil_type.py
Order: build_groundwater_layer.py, then this script, then
build_masonry_data_gaps.py and table_wervengebied_data.py.
"""

import csv
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from build_masonry_data_gaps import H_MAX, H_MIN, walls as masonry_walls
from build_walmuur_height import BED_AT_WALL_NAP
from plot_screening_sankey import load, to_num, walmuren

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / "data" / "raw" / "BRO_GeotechnischBooronderzoek"
BORINGS = DELIVERY / "DINO_GeologischBooronderzoekBoormonsterprofiel"
KML = DELIVERY / "locatie_levering.kml"
LOCATIONS = ROOT / "data" / "processed" / "objects_groundwater.csv"
OUT = ROOT / "data" / "processed" / "masonry_walls_soil.csv"

# Soil names in the column `Hoofdgrondsoort`, sorted into two groups.
# Every other name (puin, baksteen, niet benoemd, geen monster, ...) is "other".
CLAY_LIKE = {"klei", "veen", "leem", "mergel"}
SAND_LIKE = {"zand", "grind", "schelpen"}

MAJORITY = 0.70             # share needed to call a profile clay or sand
WHARF_LEVEL_NAP = 1.10      # m NAP; werf level of Oudegracht rak 3 west (report 158)
WALMUUR_H = WHARF_LEVEL_NAP - BED_AT_WALL_NAP   # m; werf to the underside of the wall
STREET_LEVEL_MIN = 2.0      # m NAP; wharf borings start at +0.9 to +1.7, street ones at +2.3 and up
DEFAULT_H = 3.0             # m; for other walls without a usable height (H_MIN-H_MAX)
MAX_DIST_M = 250.0          # farther than this, the wall gets no soil type
NEARBY_M = 150.0            # radius for counting borings that agree

# Metres per degree at the latitude of Utrecht, as in build_groundwater_layer.py.
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(52.09))
M_PER_DEG_LAT = 111132.0


def boring_locations() -> dict:
    """Lon/lat per boring ID, from the map file that came with the delivery."""
    k = "{http://earth.google.com/kml/2.1}"
    locations = {}
    for placemark in ET.parse(KML).getroot().iter(k + "Placemark"):
        name = placemark.findtext(k + "name", "")
        if name.startswith("B31H") and name.endswith(".csv"):
            lon, lat = placemark.findtext(f".//{k}coordinates", "").split(",")
            locations[name[:-4]] = (float(lon), float(lat))
    return locations


def read_boring(path: Path) -> dict:
    """Ground level and layers (top, bottom, soil) of one DINO boring CSV.

    The file holds several tables under each other, each with a title row
    and a header row, separated by empty rows.
    """
    with open(path, encoding="utf-8", errors="replace") as f:
        rows = list(csv.reader(f))

    header, values = rows[1], rows[2]       # the table "ALGEMENE GEGEVENS BORING"
    ground = values[header.index("Maaiveldhoogte (m tov NAP)")]

    layers = []
    for i, row in enumerate(rows):
        if row and row[0] == "LITHOLOGIE LAGEN":
            layer_header = rows[i + 1]
            soil_col = layer_header.index("Hoofdgrondsoort")
            for layer in rows[i + 2:]:
                if not any(layer):          # empty row: end of the table
                    break
                layers.append((float(layer[0]), float(layer[1]), layer[soil_col]))

    return {
        "id": path.stem,
        "ground_nap": float(ground) if ground else None,
        "layers": layers,
    }


def read_borings() -> list:
    """All DINO borings with a known ground level, with their lon/lat."""
    locations = boring_locations()
    borings = []
    for path in sorted(BORINGS.glob("B31H*.csv")):
        b = read_boring(path)
        if b["ground_nap"] is None:
            continue
        b["lon"], b["lat"] = locations[b["id"]]
        borings.append(b)
    return borings


def soil_group(soil: str) -> str:
    if soil in CLAY_LIKE:
        return "clay"
    if soil in SAND_LIKE:
        return "sand"
    return "other"


def shares(layers: list, top: float, bottom: float):
    """Share of clay, sand and other soil between `top` and `bottom`.

    Both are in metres below the ground level of the boring. Returns None
    when the boring has no layers in that range.
    """
    metres = {"clay": 0.0, "sand": 0.0, "other": 0.0}
    for layer_top, layer_bottom, soil in layers:
        thickness = min(layer_bottom, bottom) - max(layer_top, top)   # part inside the range
        if thickness > 0:
            metres[soil_group(soil)] += thickness

    total = metres["clay"] + metres["sand"] + metres["other"]
    if total == 0:
        return None
    return {group: m / total for group, m in metres.items()}


def soil_type(share: dict) -> str:
    if share["clay"] >= MAJORITY:
        return "soft_clay_peat"
    if share["sand"] >= MAJORITY:
        return "sand"
    return "mixed"


def support(distance: float) -> str:
    """How much the soil type is worth, judged by the distance to the boring."""
    if distance < 50:
        return "close"
    if distance < NEARBY_M:
        return "nearby"
    return "far"


def distance_m(lon1, lat1, lon2, lat2) -> float:
    """Straight-line distance; a flat map is accurate enough within a city."""
    dx = (lon1 - lon2) * M_PER_DEG_LON
    dy = (lat1 - lat2) * M_PER_DEG_LAT
    return math.hypot(dx, dy)


def walls() -> pd.DataFrame:
    """The walls of build_masonry_data_gaps.py plus all walmuren, with lon/lat."""
    cols = ["Nummer", "Naam", "Kunstwerktype", "Hoogte"]
    w = pd.concat([masonry_walls()[cols], walmuren(load())[cols]]).drop_duplicates("Nummer")
    w["Hoogte"] = to_num(w["Hoogte"])
    loc = pd.read_csv(LOCATIONS).drop_duplicates("Nummer")   # a few IDs repeat
    return w.merge(loc[["Nummer", "lon", "lat"]], on="Nummer", how="left")


def soil_for_wall(wall: pd.Series, borings: list) -> dict:
    """Soil type of one wall from the nearest boring that describes its soil."""
    walmuur = wall["Kunstwerktype"] == "Walmuur"
    if H_MIN <= wall["Hoogte"] <= H_MAX:
        H = wall["Hoogte"]
    elif walmuur:
        H = WALMUUR_H
    else:
        H = DEFAULT_H
    result = {
        "Nummer": wall["Nummer"],
        "retained_soil": "under the werf" if walmuur else "under the street",
        "H_used_m": H,
    }

    # Every boring within reach that describes the soil of this wall, nearest first.
    candidates = []
    for b in borings:
        if walmuur:
            top = b["ground_nap"] - WHARF_LEVEL_NAP   # depth of the werf level in this boring
        elif b["ground_nap"] >= STREET_LEVEL_MIN:
            top = 0.0
        else:
            continue                                  # a werf boring, for a wall under the street
        d = distance_m(wall["lon"], wall["lat"], b["lon"], b["lat"])
        share = shares(b["layers"], top, top + H)
        if d <= MAX_DIST_M and share is not None:
            candidates.append((d, b["id"], b["ground_nap"], share))
    candidates.sort(key=lambda c: c[0])

    if not candidates:
        result["support"] = f"no boring within {MAX_DIST_M:.0f} m"
        return result

    d, boring_id, ground, share = candidates[0]
    result.update({
        "soil_type": soil_type(share),
        "boring": boring_id,
        "boring_dist_m": round(d),
        "boring_ground_nap": ground,
        "clay_share": round(share["clay"], 2),
        "sand_share": round(share["sand"], 2),
        "other_share": round(share["other"], 2),
        "support": support(d),
    })

    # Agreement: how many borings within NEARBY_M give the same soil type.
    nearby = [c for c in candidates if c[0] <= NEARBY_M]
    result["n_nearby_borings"] = len(nearby)
    result["n_agree"] = sum(1 for c in nearby if soil_type(c[3]) == result["soil_type"])
    return result


def main() -> None:
    borings = read_borings()
    w = walls()
    rows = [soil_for_wall(wall, borings) for _, wall in w.iterrows()]
    out = w[["Nummer", "Naam", "Kunstwerktype"]].merge(pd.DataFrame(rows), on="Nummer")
    out.to_csv(OUT, index=False)

    print(f"{len(borings)} borings, {len(out)} walls -> {OUT.relative_to(ROOT)}\n")
    print(pd.crosstab(out["soil_type"].fillna("none"), out["retained_soil"]).to_string(), "\n")
    print(out["support"].value_counts().to_string())


if __name__ == "__main__":
    main()

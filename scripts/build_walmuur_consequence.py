"""Consequence score per walmuur: what a failure would hit.

The failure model gives the probability side of the risk. This script gives a
simple consequence side per wall, from open data, with three indicators scored
1 (low) to 3 (high):

  people       people on the werf: OSM restaurants, cafes, bars and outdoor
               seating within D_PEOPLE of the wall, per 100 m of wall (terraces
               on the werf are mapped there); data/raw/osm_hospitality_binnenstad.json
  cellars      wharf cellars behind the wall: share of the wall with a werfmuur
               or kluismuur (the front of a cellar) within D_CELLAR, from the
               municipal Werfmuren layer; data/raw/UtrechtOpen/werfmuren.geojson
  reachability the street behind the werf: distance a to the nearest BGT road
               area (walmuur_traffic.csv). A failure that reaches the street
               closes it and hinders access to the area.

The consequence score is the mean of the three, rounded to a class: low below
1.75, high from 2.5, medium between. Heritage value is the same for every wall
(national monument) and is not scored. Cables, pipes and trees on the werf are
not in open data and are left out; they are a known gap.

Writes data/processed/walmuur_consequence.csv.
Run: python3 scripts/build_walmuur_consequence.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_walmuur_height import M_PER_DEG_LAT, M_PER_DEG_LON
from plot_screening_sankey import load, walmuren

ROOT = Path(__file__).resolve().parents[1]
OSM = ROOT / "data" / "raw" / "osm_hospitality_binnenstad.json"
WERFMUREN = ROOT / "data" / "raw" / "UtrechtOpen" / "werfmuren.geojson"
TRAFFIC = ROOT / "data" / "processed" / "walmuur_traffic.csv"
OUT = ROOT / "data" / "processed" / "walmuur_consequence.csv"

# ---- Inputs ----------------------------------------------------------------
D_PEOPLE = 20.0                 # [m] hospitality within this distance counts for the werf
PEOPLE_BANDS = (0.5, 3.0)       # per 100 m: below the first 1, from the second 3
D_CELLAR = 15.0                 # [m] a cellar front within this distance is behind the wall
CELLAR_BANDS = (0.25, 0.75)     # share of the wall: below the first 1, from the second 3
ROAD_BANDS = (3.0, 6.0)         # [m] road closer than the first 3, farther than the second 1
CLASS_BANDS = (1.75, 2.5)       # mean score: below the first low, from the second high
STEP = 1.0                      # [m] spacing of the points along a wall
# ----------------------------------------------------------------------------


def xy(lon, lat):
    return np.column_stack([np.asarray(lon) * M_PER_DEG_LON, np.asarray(lat) * M_PER_DEG_LAT])


def densify(coords, step=STEP):
    """Points every `step` metres along a line given as (lon, lat) pairs."""
    p = xy(*np.array(coords).T)
    out = [p[0]]
    for a, b in zip(p[:-1], p[1:]):
        n = max(int(np.hypot(*(b - a)) // step), 1)
        out.extend(a + (b - a) * k / n for k in range(1, n + 1))
    return np.array(out)


def lines(geometry):
    g = geometry
    if g["type"] == "LineString":
        return [g["coordinates"]]
    if g["type"] == "MultiLineString":
        return g["coordinates"]
    if g["type"] == "Polygon":
        return g["coordinates"]
    if g["type"] == "MultiPolygon":
        return [ring for poly in g["coordinates"] for ring in poly]
    return []


def nearest(points, others):
    """Distance from each point to the nearest of `others` [m]."""
    d = np.full(len(points), np.inf)
    for i in range(0, len(others), 2000):
        chunk = others[i:i + 2000]
        d = np.minimum(d, np.sqrt(((points[:, None, :] - chunk[None, :, :])**2).sum(-1)).min(1))
    return d


def score(value, bands, high_is_more=True):
    low, high = bands
    s = 1 + (value >= low) + (value >= high)
    return int(s if high_is_more else 4 - s)


def main() -> None:
    features = json.loads((ROOT / "data" / "raw" / "Output areaal GU TU Delft 26-08.json")
                          .read_text())["features"]
    geom = {f["properties"]["Nummer"]: f["geometry"] for f in features if f.get("properties")}
    walls = walmuren(load())[["Nummer", "Naam", "Lengte"]]

    osm = json.loads(OSM.read_text())["elements"]
    poi = xy([e.get("lon", e.get("center", {}).get("lon")) for e in osm],
             [e.get("lat", e.get("center", {}).get("lat")) for e in osm])
    cellar_pts = np.vstack([densify(ring) for f in json.loads(WERFMUREN.read_text())["features"]
                            if f["properties"]["TYPE_MUUR"] in ("Werfmuur", "Kluismuur")
                            for ring in lines(f["geometry"])])
    road = pd.read_csv(TRAFFIC).set_index("Nummer")

    rows = []
    for _, w in walls.iterrows():
        pts = np.vstack([densify(c) for c in lines(geom[w["Nummer"]])])
        n_poi = int((nearest(poi, pts) <= D_PEOPLE).sum())
        per_100m = 100 * n_poi / (w["Lengte"] + 2 * D_PEOPLE)
        cellar_share = float((nearest(pts, cellar_pts) <= D_CELLAR).mean())
        a_road = road.loc[w["Nummer"], "a_min_m"] if w["Nummer"] in road.index else np.nan
        s = {"people": score(per_100m, PEOPLE_BANDS), "cellars": score(cellar_share, CELLAR_BANDS),
             "reachability": score(a_road, ROAD_BANDS, high_is_more=False) if a_road == a_road else 2}
        mean = np.mean(list(s.values()))
        cls = "low" if mean < CLASS_BANDS[0] else "high" if mean >= CLASS_BANDS[1] else "medium"
        rows.append({"Nummer": w["Nummer"], "Naam": w["Naam"], "length_m": round(w["Lengte"], 1),
                     "hospitality_within_20m": n_poi, "hospitality_per_100m": round(per_100m, 2),
                     "cellar_share": round(cellar_share, 2), "road_distance_m": a_road,
                     **{f"score_{k}": v for k, v in s.items()},
                     "consequence_score": round(mean, 2), "consequence_class": cls})
    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)
    print(d.to_string(index=False))
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

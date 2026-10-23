"""Distance to the road and the posted axle limit per walmuur, the data behind q and a.

The surcharge model (StressCaclulation/TraficLoad.py) needs a load q and
its distance a to the wall. Neither is in the asset register, so two open
data sets give what can be measured:

  a             Distance in plan from the wall to the nearest carriageway or
                parking bay, from the BGT road areas (wegdeel). At 6 places along the
                wall a line is drawn at right angles towards the werf side
                (the side build_walmuur_height.py finds with AHN), and the
                distance to the first road area it enters is read, up to
                MAX_A_M. Roads on a bridge or in a tunnel
                (relatieve_hoogteligging not 0) are left out.
                Where no road is that close, a is more than MAX_A_M.
  axle limit    The heaviest axle allowed on the street behind the wall,
                from the NDW traffic signs: the nearest C20 sign (maximum
                axle load) within SIGN_RADIUS_M of the wall line, with its
                distance. A sign far from the wall may stand on another
                street. C21 (maximum vehicle mass) and C7 (no lorries) are
                recorded the same way.

Neither gives q itself. a is a distance in plan: on the walls with a werf the
road runs at street level, over the werfkelders, and not on the soil the
walmuur holds back. The axle limit bounds the heaviest vehicle; turning it
into q [kN/m²] is left to the traffic model.

The BGT and NDW data are downloaded once from PDOK and NDW and saved in
data/raw/BGT/ and data/raw/NDW/. Delete those files to download them again.

Writes data/processed/walmuur_traffic.csv, one row per walmuur.
Run: python scripts/build_walmuur_traffic.py, after build_walmuur_height.py
"""

import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from build_walmuur_height import (AHN_CACHE, M_PER_DEG_LAT, M_PER_DEG_LON, N_PLACES,
                                  places_along, walmuur_lines, werf_side)
from plot_screening_sankey import load, walmuren

ROOT = Path(__file__).resolve().parents[1]
BGT_CACHE = ROOT / "data" / "raw" / "BGT" / "walmuur_wegdeel.geojson"
NDW_CACHE = ROOT / "data" / "raw" / "NDW" / "traffic_signs_utrecht.geojson"
OUT = ROOT / "data" / "processed" / "walmuur_traffic.csv"
BGT_API = "https://api.pdok.nl/kadaster/bgt/ogc/v1/collections/wegdeel/items"
NDW_API = "https://data.ndw.nu/api/rest/static-road-data/traffic-signs/v5/current-state"

MAX_A_M = 30.0              # m; look this far from the wall for a road
SIGN_RADIUS_M = 150.0       # m; look this far from the wall line for a sign
MUNICIPALITY = "GM0344"     # Utrecht
SIGN_CODES = ["C20", "C21", "C7"]   # max axle load, max vehicle mass, no lorries

# BGT road functions a vehicle may drive or stand on. Footpaths, cycle
# paths, pedestrian areas and stairs are left out.
VEHICLE_FUNCTIONS = ("rijbaan", "woonerf", "parkeervlak", "inrit", "OV-baan", "busbaan")


def to_metres(lon, lat, lon0: float, lat0: float):
    """Metres east and north of (lon0, lat0), as in build_walmuur_height.py."""
    return (np.asarray(lon) - lon0) * M_PER_DEG_LON, (np.asarray(lat) - lat0) * M_PER_DEG_LAT


def wall_bbox(line: list, margin_m: float) -> tuple:
    """Box around the wall line, margin_m wider on every side, in lon/lat."""
    lons, lats = [c[0] for c in line], [c[1] for c in line]
    d_lon, d_lat = margin_m / M_PER_DEG_LON, margin_m / M_PER_DEG_LAT
    return (min(lons) - d_lon, min(lats) - d_lat, max(lons) + d_lon, max(lats) + d_lat)


def fetch_bgt(bbox: tuple) -> list:
    """Current BGT road areas in the box. The API also returns old versions."""
    features = []
    url = BGT_API + "?" + urllib.parse.urlencode(
        {"f": "json", "bbox": ",".join(f"{x:.7f}" for x in bbox), "limit": 1000})
    while url:
        with urllib.request.urlopen(url, timeout=60) as response:
            page = json.loads(response.read())
        features += page["features"]
        url = next((link["href"] for link in page["links"] if link["rel"] == "next"), None)
    return [f for f in features if f["properties"]["eind_registratie"] is None]


def bgt_roads(lines: dict) -> list:
    """BGT road areas near the walmuren; downloaded once, then read from disk."""
    if BGT_CACHE.exists():
        return json.loads(BGT_CACHE.read_text())["features"]

    print(f"Downloading BGT road areas around {len(lines)} walmuren from PDOK ...")
    keep = ("lokaal_id", "functie", "fysiek_voorkomen", "relatieve_hoogteligging")
    roads = {}
    for line in lines.values():
        for f in fetch_bgt(wall_bbox(line, MAX_A_M + 5)):
            p = f["properties"]
            roads[p["lokaal_id"]] = {"type": "Feature", "geometry": f["geometry"],
                                     "properties": {k: p[k] for k in keep}}
    BGT_CACHE.parent.mkdir(parents=True, exist_ok=True)
    BGT_CACHE.write_text(json.dumps({"type": "FeatureCollection",
                                     "features": list(roads.values())}))
    return list(roads.values())


def ndw_signs() -> list:
    """NDW traffic signs SIGN_CODES in Utrecht; downloaded once, then read from disk."""
    if NDW_CACHE.exists():
        return json.loads(NDW_CACHE.read_text())["features"]

    print("Downloading NDW traffic signs ...")
    query = {"countyCode": MUNICIPALITY, "rvvCode": ",".join(SIGN_CODES),
             "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}
    with urllib.request.urlopen(NDW_API + "?" + urllib.parse.urlencode(query),
                                timeout=180) as response:
        signs = json.loads(response.read())
    NDW_CACHE.parent.mkdir(parents=True, exist_ok=True)
    NDW_CACHE.write_text(json.dumps(signs))
    return signs["features"]


def rings(geometry: dict) -> list:
    """Outer and inner rings of a (multi)polygon."""
    if geometry["type"] == "Polygon":
        return geometry["coordinates"]
    if geometry["type"] == "MultiPolygon":
        return [ring for polygon in geometry["coordinates"] for ring in polygon]
    return []


def entry_distance(lon0: float, lat0: float, east: float, north: float, road: dict):
    """Distance along a ray from (lon0, lat0) to where it enters the road area.

    0 if the ray starts inside it, None if it never enters it.
    """
    crossings = []
    for ring in rings(road["geometry"]):
        x, y = to_metres([c[0] for c in ring], [c[1] for c in ring], lon0, lat0)
        ax, ay, dx, dy = x[:-1], y[:-1], np.diff(x), np.diff(y)
        den = east * dy - north * dx
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (ax * dy - ay * dx) / den               # along the ray
            s = (ax * north - ay * east) / den          # along the edge
        crossings += list(t[(den != 0) & (t >= 0) & (s >= 0) & (s <= 1)])
    if not crossings:
        return None
    # An odd number of crossings means the start is inside the area.
    return 0.0 if len(crossings) % 2 else min(crossings)


def road_distances(line: list, side: str, roads: list) -> list:
    """Per place along the wall: (distance to the nearest road, its function)."""
    sign = 1 if side == "left" else -1
    # Only roads whose bounding box overlaps the box around the wall can be hit.
    west, south, east_edge, north_edge = wall_bbox(line, MAX_A_M)
    nearby = []
    for road in roads:
        outer = np.array(rings(road["geometry"])[0])
        if (outer[:, 0].max() >= west and outer[:, 0].min() <= east_edge
                and outer[:, 1].max() >= south and outer[:, 1].min() <= north_edge):
            nearby.append(road)

    result = []
    for lon, lat, east, north in places_along(line, N_PLACES):
        # Turn the wall direction 90 degrees towards the werf side, as in
        # build_walmuur_height.side_points().
        step_east, step_north = -north * sign, east * sign
        hits = [(d, road["properties"]["functie"]) for road in nearby
                if (d := entry_distance(lon, lat, step_east, step_north, road)) is not None
                and d <= MAX_A_M]
        result.append(min(hits) if hits else (None, None))
    return result


def distance_to_line(lon: float, lat: float, line: list) -> float:
    """Shortest distance in metres from a point to the wall line."""
    x, y = to_metres([c[0] for c in line], [c[1] for c in line], lon, lat)
    ax, ay, dx, dy = x[:-1], y[:-1], np.diff(x), np.diff(y)
    length2 = dx**2 + dy**2
    with np.errstate(divide="ignore", invalid="ignore"):
        f = np.clip(np.where(length2 > 0, -(ax * dx + ay * dy) / length2, 0), 0, 1)
    return float(np.hypot(ax + f * dx, ay + f * dy).min())


def nearest_sign(line: list, signs: list, code: str):
    """(distance, restrictions) of the nearest sign of this code, or None."""
    found = [(distance_to_line(*s["geometry"]["coordinates"][:2], line),
              s["properties"].get("conditions", {}).get("restrictions", {}))
             for s in signs if s["properties"]["rvvCode"] == code]
    found = [f for f in found if f[0] <= SIGN_RADIUS_M]
    return min(found, key=lambda f: f[0]) if found else None


def traffic_for_wall(wall: pd.Series, line: list, side: str, roads: list, signs: list) -> dict:
    vehicle_roads = [r for r in roads
                     if r["properties"]["functie"].startswith(VEHICLE_FUNCTIONS)
                     and r["properties"]["relatieve_hoogteligging"] == 0]
    places = road_distances(line, side, vehicle_roads)
    a = pd.Series([d for d, _ in places], dtype=float).dropna()
    functions = pd.Series([f for _, f in places]).dropna()

    result = {"Nummer": wall["Nummer"], "Naam": wall["Naam"], "werf_side": side,
              "n_places": len(places), "n_places_road": len(a)}
    if not a.empty:
        result.update({"a_min_m": round(a.min(), 1), "a_median_m": round(a.median(), 1),
                       "a_max_m": round(a.max(), 1), "road_function": functions.mode()[0]})

    c20, c21, c7 = (nearest_sign(line, signs, code) for code in SIGN_CODES)
    if c20:
        result.update({"axle_limit_t": c20[1].get("axleWeight"), "axle_sign_m": round(c20[0])})
    if c21:
        result.update({"mass_limit_t": c21[1].get("weight"), "mass_sign_m": round(c21[0])})
    if c7:
        result["no_lorries_sign_m"] = round(c7[0])
    return result


def main() -> None:
    lines = walmuur_lines()
    roads = bgt_roads(lines)
    signs = ndw_signs()
    points = pd.read_csv(AHN_CACHE)
    w = walmuren(load())
    out = pd.DataFrame([traffic_for_wall(wall, lines[wall["Nummer"]],
                                         werf_side(points, wall["Nummer"]), roads, signs)
                        for _, wall in w.iterrows()])
    out = out.sort_values("Naam")
    out.to_csv(OUT, index=False)

    print(f"{len(out)} walmuren -> {OUT.relative_to(ROOT)}\n")
    print(f"Road within {MAX_A_M:.0f} m at some place: {out['a_min_m'].notna().sum()}")
    print(f"C20 sign within {SIGN_RADIUS_M:.0f} m: {out['axle_limit_t'].notna().sum()}")
    print(out["axle_limit_t"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()

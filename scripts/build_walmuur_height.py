"""Retained height H per walmuur, from AHN ground levels and an assumed canal bottom.

H = werf level - canal bottom. `Hoogte` is empty for all 51 walmuren, so
both levels are estimated:

  werf level    Measured, per wall. The AHN ground level (dtm_05m) is read
                at 6 places along the wall, 2.5 m to the left and right of
                it. Over the water AHN has no value, so the side with values
                is the werf. The werf level is the median of the values at
                or below +1.6 m NAP: a point above that hits the street, a
                stair or a bridge, not the werf.
  canal bottom  Not measured; soundings per rak would give it. Taken at
                the underside of the wall, -0.08 m NAP (Erfgoed Utrecht
                report 158, rak 3 west), the same for every wall. The bed
                may be deeper, so H is a lower bound.

A wall with a median ground level above +1.6 m NAP beside it seems to have
no werf. Either the street reaches the canal there (H would then run from
street level, much larger), or the points hit a bridge, a stair or a building.
These walls are flagged in the column `werf`; check them on a map.

The AHN values are downloaded once from PDOK and saved in
data/raw/AHN/walmuur_ahn_points.csv. Delete that file to download them again.

Writes data/processed/walmuur_height.csv, one row per walmuur.
Run: python scripts/build_walmuur_height.py
"""

import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from plot_screening_sankey import AREAAL, load, walmuren

ROOT = Path(__file__).resolve().parents[1]
AHN_CACHE = ROOT / "data" / "raw" / "AHN" / "walmuur_ahn_points.csv"
OUT = ROOT / "data" / "processed" / "walmuur_height.csv"
AHN_WMS = "https://service.pdok.nl/rws/ahn/wms/v1_0"

N_PLACES = 6                # places along each wall where AHN is read
OFFSET_M = 2.5              # m to the left and right of the wall line
NO_WERF_ABOVE = 1.6         # m NAP; werven lie at +1.0 to +1.4, streets at +2 to +5
BED_AT_WALL_NAP = -0.08     # m NAP; underside of the walmuur, rak 3 west (report 158)

# Metres per degree at the latitude of Utrecht, as in build_groundwater_layer.py.
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(52.09))
M_PER_DEG_LAT = 111132.0


def walmuur_lines() -> dict:
    """Line coordinates (lon, lat) of the 51 walmuren, by Nummer."""
    numbers = set(walmuren(load())["Nummer"])
    lines = {}
    for f in json.loads(AREAAL.read_text())["features"]:
        if f["properties"]["Nummer"] in numbers:
            lines[f["properties"]["Nummer"]] = f["geometry"]["coordinates"]
    return lines


def places_along(line: list, n: int) -> list:
    """n places spread evenly along the line, with the wall direction there.

    Each place is (lon, lat, east, north), where (east, north) is the
    direction of the wall as a vector of length 1 in metres.
    """
    segments = []
    for (lon0, lat0), (lon1, lat1) in zip(line[:-1], line[1:]):
        dx = (lon1 - lon0) * M_PER_DEG_LON      # metres east
        dy = (lat1 - lat0) * M_PER_DEG_LAT      # metres north
        segments.append((lon0, lat0, dx, dy, math.hypot(dx, dy)))
    total = sum(s[4] for s in segments)

    places = []
    for k in range(n):
        distance = (k + 0.5) / n * total        # how far along the wall
        for lon0, lat0, dx, dy, length in segments:
            if distance <= length and length > 0:
                f = distance / length
                places.append((lon0 + f * dx / M_PER_DEG_LON,
                               lat0 + f * dy / M_PER_DEG_LAT,
                               dx / length, dy / length))
                break
            distance -= length
    return places


def side_points(line: list) -> list:
    """Points OFFSET_M to the left and right of the wall: (side, lon, lat)."""
    points = []
    for lon, lat, east, north in places_along(line, N_PLACES):
        for side, sign in (("left", 1), ("right", -1)):
            # Turn the wall direction 90 degrees to step sideways.
            step_east = -north * sign * OFFSET_M
            step_north = east * sign * OFFSET_M
            points.append((side, lon + step_east / M_PER_DEG_LON,
                           lat + step_north / M_PER_DEG_LAT))
    return points


def ahn_ground_level(lon: float, lat: float):
    """AHN ground level in m NAP at one point, or None (water, buildings)."""
    d = 0.00001                                 # a box of about 1 m around the point
    query = {
        "service": "WMS", "version": "1.3.0", "request": "GetFeatureInfo",
        "layers": "dtm_05m", "query_layers": "dtm_05m", "styles": "",
        "crs": "EPSG:4326", "bbox": f"{lat - d},{lon - d},{lat + d},{lon + d}",
        "width": 21, "height": 21, "i": 10, "j": 10,
        "info_format": "application/json",
    }
    url = AHN_WMS + "?" + urllib.parse.urlencode(query)
    with urllib.request.urlopen(url, timeout=30) as response:
        features = json.loads(response.read())["features"]
    if not features:
        return None
    return float(features[0]["properties"]["value_list"])


def ahn_points(lines: dict) -> pd.DataFrame:
    """AHN ground levels beside every walmuur; downloaded once, then read from disk."""
    if AHN_CACHE.exists():
        return pd.read_csv(AHN_CACHE)

    print(f"Downloading AHN for {len(lines)} walmuren from PDOK ...")
    rows = []
    for nummer, line in lines.items():
        for side, lon, lat in side_points(line):
            rows.append({"Nummer": nummer, "side": side, "lon": round(lon, 7),
                         "lat": round(lat, 7), "ground_nap": ahn_ground_level(lon, lat)})
    points = pd.DataFrame(rows)
    AHN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    points.to_csv(AHN_CACHE, index=False)
    return points


def werf_side(points: pd.DataFrame, nummer: str) -> str:
    """The side of the wall line ("left" or "right") the werf is on.

    The werf is the side with AHN values; over the water there are none.
    If both sides have values, take the side with more of them, and if
    that is equal, the lower side (the werf is the lowest ground).
    """
    p = points[(points["Nummer"] == nummer) & points["ground_nap"].notna()]
    left = p[p["side"] == "left"]["ground_nap"]
    right = p[p["side"] == "right"]["ground_nap"]
    if len(left) > len(right) or (len(left) == len(right) and left.median() <= right.median()):
        return "left"
    return "right"


def height_for_wall(wall: pd.Series, points: pd.DataFrame) -> dict:
    """Werf level and H of one walmuur."""
    p = points[(points["Nummer"] == wall["Nummer"]) & points["ground_nap"].notna()]
    ground = p[p["side"] == werf_side(points, wall["Nummer"])]["ground_nap"]

    rak = re.search(r"Rak (\d+)", wall["Naam"])
    result = {
        "Nummer": wall["Nummer"],
        "Naam": wall["Naam"],
        "canal": wall["group"],
        "rak": int(rak.group(1)) if rak else None,
        "n_points": len(ground),
    }
    if ground.empty:
        result["werf"] = "no AHN values"
        return result

    has_werf = ground.median() <= NO_WERF_ABOVE
    # On a wall with a werf, leave out the points on the street, a stair or a bridge.
    werf = ground[ground <= NO_WERF_ABOVE].median() if has_werf else ground.median()
    result.update({
        "werf_nap": round(werf, 2),
        "ground_min_nap": round(ground.min(), 2),
        "ground_max_nap": round(ground.max(), 2),
        "n_points_above_1_6": int((ground > NO_WERF_ABOVE).sum()),
        "werf": "yes" if has_werf else "no werf? check map",
        "H_bed_at_wall_m": round(werf - BED_AT_WALL_NAP, 2),
    })
    return result


def main() -> None:
    lines = walmuur_lines()
    points = ahn_points(lines)
    w = walmuren(load())
    out = pd.DataFrame([height_for_wall(wall, points) for _, wall in w.iterrows()])
    out = out.sort_values(["canal", "rak", "Naam"])
    out.to_csv(OUT, index=False)

    print(f"{len(out)} walmuren -> {OUT.relative_to(ROOT)}\n")
    print(out["werf"].value_counts().to_string(), "\n")
    with_werf = out[out["werf"] == "yes"]
    print("Walls with a werf, per canal (m):")
    print(with_werf.groupby("canal")[["werf_nap", "H_bed_at_wall_m"]]
          .agg(["min", "median", "max"]).round(2).to_string())


if __name__ == "__main__":
    main()

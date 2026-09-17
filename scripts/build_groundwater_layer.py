"""Reduce the BRO head series to a groundwater attribute per Utrecht asset.

Two steps, both cheap enough to rerun:

  1. Per head series, compute the statistics that matter for a quay wall on
     timber piles: GLG (the Dutch mean lowest groundwater level), GHG, the
     annual swing, and the trend. GLG is the one that decides whether pile
     heads dry out, so it is what the map colours by.
  2. Interpolate those onto the retaining structures in the areaal file with
     inverse distance weighting, and record how far the nearest well was, so a
     reader can tell an interpolated value from a supported one.

Writes data/processed/wells_groundwater.csv, objects_groundwater.csv, and
groundwater_layer.json (the compact file the Utrecht Areaal artifact loads).
"""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BRO = RAW / "APIDatacollection"
PROC = ROOT / "data" / "processed"

# Structures that retain ground and can stand on timber piles. The quay walls
# proper are `Kademuur`, but the other three fail the same way.
RETAINING = {"Kademuur", "Muur", "Beschoeiing", "Damwand"}

# Interpolation settings. 400 m is generous but the wells are sparse; the
# distance column is what carries the honesty, not a hard cutoff.
IDW_POWER = 2.0
IDW_NEIGHBOURS = 6
IDW_MAX_DIST_M = 400.0

# Latitude of Utrecht, for the local metre-per-degree conversion. Over a city
# this is accurate to a few decimetres, well inside the interpolation error.
LAT0 = 52.09
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(LAT0))
M_PER_DEG_LAT = 111132.0


def read_series(path):
    """Read one BRO head CSV into a dated series of levels in m NAP."""
    df = pd.read_csv(path, header=None, usecols=[0, 1, 2],
                     names=["time", "level", "status"],
                     dtype={"status": "string"})
    df = df.dropna(subset=["time", "level"])
    if df.empty:
        return None
    t = pd.to_datetime(df["time"], format="ISO8601", utc=True, errors="coerce")
    level = pd.to_numeric(df["level"], errors="coerce")
    s = pd.Series(level.values, index=t).dropna()
    return s.sort_index() if not s.empty else None


def hydro_year(idx):
    """Hydrological year runs 1 April to 31 March."""
    return idx.year.where(idx.month >= 4, idx.year - 1)


def gxg(series):
    """GLG, GHG and GVG from a head series, following the Dutch convention.

    The convention is built on readings on the 14th and 28th of each month, so
    continuous loggers are resampled down to those dates first — otherwise a
    logger's 8,000 hourly readings would define "the three lowest" out of noise
    rather than out of the season.
    """
    daily = series.resample("D").mean().dropna()
    if daily.empty:
        return {}
    picks = daily[daily.index.day.isin([14, 28])]
    if len(picks) < 12:
        picks = daily
    hy = hydro_year(picks.index)
    lows, highs, springs = [], [], []
    for year, group in picks.groupby(hy):
        if len(group) < 16:          # need most of a year for a real GxG
            continue
        lows.append(group.nsmallest(3).mean())
        highs.append(group.nlargest(3).mean())
        spring = group[(group.index.month == 3) | (group.index.month == 4)]
        if len(spring):
            springs.append(spring.mean())
    if not lows:
        return {}
    out = {"glg": float(np.mean(lows)), "ghg": float(np.mean(highs)),
           "n_years": len(lows)}
    if springs:
        out["gvg"] = float(np.mean(springs))
    out["swing"] = out["ghg"] - out["glg"]
    return out


def trend_mm_per_year(series):
    """Least squares slope through the yearly means, in mm/yr."""
    yearly = series.resample("YE").mean().dropna()
    if len(yearly) < 5:
        return None
    x = yearly.index.year.values.astype(float)
    slope = np.polyfit(x - x.mean(), yearly.values, 1)[0]
    return float(slope * 1000.0)


def ground_levels():
    """Ground level in m NAP per GLD, via its tube and well.

    Needed because a head of -1.6 m NAP means something different on the
    Oudegracht than in Leidsche Rijn. What a timber pile head cares about is
    how far the water sits below the surface, not its absolute level.
    """
    wells = json.loads((BRO / "gm_gmw.geojson").read_text())["features"]
    tubes = json.loads((BRO / "gm_gmw_monitoringtube.geojson").read_text())["features"]
    glds = json.loads((BRO / "gm_gld.geojson").read_text())["features"]
    gl = {w["properties"]["gm_gmw_pk"]: w["properties"].get("ground_level_position")
          for w in wells}
    tube_gl = {t["properties"]["gm_gmw_monitoringtube_pk"]: gl.get(t["properties"].get("gm_gmw_fk"))
               for t in tubes}
    return {g["properties"]["bro_id"]: tube_gl.get(g["properties"].get("gm_gmw_monitoringtube_fk"))
            for g in glds}


def build_wells():
    index = pd.read_csv(BRO / "series" / "series_index.csv")
    ground = ground_levels()
    rows = []
    for i, r in enumerate(index.itertuples(), 1):
        path = BRO / "series" / r.file
        if not path.exists():
            continue
        s = read_series(path)
        if s is None or len(s) < 24:
            continue
        stats = gxg(s)
        if not stats:
            continue
        rows.append({
            "gld_bro_id": r.gld_bro_id,
            "lon": r.lon, "lat": r.lat,
            "screen_depth_below_ground_m": r.screen_depth_below_ground_m,
            "first_date": r.first_date, "last_date": r.last_date,
            "n_readings": len(s),
            "mean_level_m_nap": float(s.mean()),
            "trend_mm_per_year": trend_mm_per_year(s),
            "ground_level_m_nap": ground.get(r.gld_bro_id),
            **stats,
        })
        if i % 50 == 0:
            print(f"  {i}/{len(index)} series", flush=True)
    df = pd.DataFrame(rows)
    # Depth of the mean lowest groundwater below the surface. Positive means
    # the water table drops that far below ground in a dry summer.
    df["glg_depth_m"] = df["ground_level_m_nap"] - df["glg"]
    PROC.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROC / "wells_groundwater.csv", index=False)
    print(f"  {len(df)} wells with a usable GxG -> wells_groundwater.csv")
    return df


def centroid(geom):
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
        else:
            for part in c:
                walk(part)

    walk(geom["coordinates"])
    return sum(xs) / len(xs), sum(ys) / len(ys)


def build_objects(wells):
    areaal = json.loads((RAW / "Output areaal GU TU Delft 26-08.json").read_text())
    feats = [f for f in areaal["features"]
             if f["properties"].get("Objecttype") in RETAINING]

    wx = wells["lon"].values * M_PER_DEG_LON
    wy = wells["lat"].values * M_PER_DEG_LAT
    usable = wells[wells["glg_depth_m"].notna()].reset_index(drop=True)
    wx = usable["lon"].values * M_PER_DEG_LON
    wy = usable["lat"].values * M_PER_DEG_LAT
    wells = usable
    glg = wells["glg"].values
    depth = wells["glg_depth_m"].values
    swing = wells["swing"].values
    trend = pd.to_numeric(wells["trend_mm_per_year"], errors="coerce").values

    rows = []
    for f in feats:
        lon, lat = centroid(f["geometry"])
        d = np.hypot(wx - lon * M_PER_DEG_LON, wy - lat * M_PER_DEG_LAT)
        order = np.argsort(d)[:IDW_NEIGHBOURS]
        near, dn = d[order], d[order]
        w = 1.0 / np.maximum(near, 1.0) ** IDW_POWER
        tr = trend[order]
        finite = np.isfinite(tr)
        p = f["properties"]
        rows.append({
            "Nummer": p.get("Nummer"),
            "Objecttype": p.get("Objecttype"),
            "lon": round(lon, 7), "lat": round(lat, 7),
            "glg_m_nap": float(np.sum(w * glg[order]) / np.sum(w)),
            "glg_depth_below_ground_m": float(np.sum(w * depth[order]) / np.sum(w)),
            "swing_m": float(np.sum(w * swing[order]) / np.sum(w)),
            "trend_mm_per_year": (float(np.sum(w[finite] * tr[finite]) / np.sum(w[finite]))
                                  if finite.any() else None),
            "nearest_well_m": float(dn[0]),
            "n_wells_within_400m": int((d <= IDW_MAX_DIST_M).sum()),
        })

    df = pd.DataFrame(rows)
    # Support class: how much the interpolated value is worth. The cut-offs
    # follow what the data can carry, not a standard.
    df["support"] = pd.cut(df["nearest_well_m"], [0, 100, 250, 500, np.inf],
                           labels=["measured nearby", "interpolated",
                                   "weakly supported", "no support"])
    df.to_csv(PROC / "objects_groundwater.csv", index=False)
    print(f"  {len(df)} retaining objects -> objects_groundwater.csv")
    print(df["support"].value_counts().to_string())
    return df


def write_layer(wells, objects):
    """Compact JSON for the artifact: one row per object, plus the wells."""
    layer = {
        "generated_from": "BRO grondwatermonitoring (PDOK OGC API), CC0",
        "statistic": "GLG, mean lowest groundwater level; glg in m NAP, dp in m below ground",
        "idw": {"power": IDW_POWER, "neighbours": IDW_NEIGHBOURS},
        "objects": [
            {"n": r.Nummer,
             "glg": round(r.glg_m_nap, 2),
             "dp": round(r.glg_depth_below_ground_m, 2),
             "sw": round(r.swing_m, 2),
             "tr": None if pd.isna(r.trend_mm_per_year) else round(r.trend_mm_per_year, 1),
             "d": round(r.nearest_well_m)}
            for r in objects.itertuples()
        ],
        "wells": [
            {"id": r.gld_bro_id,
             "lon": round(r.lon, 6), "lat": round(r.lat, 6),
             "glg": round(r.glg, 2),
             "dp": round(r.glg_depth_m, 2),
             "sw": round(r.swing, 2),
             "yr": int(r.n_years),
             "dep": round(r.screen_depth_below_ground_m, 1),
             "last": str(r.last_date)[:10]}
            for r in wells.itertuples()
        ],
    }
    path = PROC / "groundwater_layer.json"
    path.write_text(json.dumps(layer, separators=(",", ":")))
    print(f"  {path.name}: {path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    print("series statistics:")
    wells = build_wells()
    print("interpolation onto assets:")
    objects = build_objects(wells)
    write_layer(wells, objects)

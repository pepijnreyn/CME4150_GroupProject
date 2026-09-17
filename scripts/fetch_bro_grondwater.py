"""Download BRO groundwater monitoring data for the Utrecht study area.

Source: PDOK OGC API Features, "BRO - Grondwatermonitoring (GM) in samenhang -
karakteristieken". Open data (CC0), no API key.

Collections, and how they hang together:

    gm_gmw                 monitoring well: location, ground level (m NAP), owner
      gm_gmw_monitoringtube  one tube per well: screen top/bottom (m NAP)
        gm_gld               head time series: metadata + CSV download URLs
        gm_gar               water quality sample

Writes GeoJSON per collection to data/raw/APIDatacollection/. With --series it
also downloads the head time series themselves (one CSV per GLD).

    python3 scripts/fetch_bro_grondwater.py
    python3 scripts/fetch_bro_grondwater.py --series --max-screen-depth 8
"""

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = ("https://api.pdok.nl/tno/bro-grondwatermonitoring-in-samenhang-"
        "karakteristieken/ogc/v1")

# Municipality of Utrecht plus a margin, in WGS84 lon/lat (the API default CRS,
# and the CRS the areaal file is already in).
UTRECHT_BBOX = (4.93, 52.02, 5.25, 52.16)

COLLECTIONS = ("gm_gmw", "gm_gmw_monitoringtube", "gm_gld", "gm_gar")

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "APIDatacollection"


def get(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == retries - 1:
                raise
            print(f"    retry after {exc}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))


def fetch_collection(name, bbox, page_size=1000):
    """Page through /items and return the features for the bbox."""
    url = f"{BASE}/collections/{name}/items?" + urllib.parse.urlencode(
        {"bbox": ",".join(str(v) for v in bbox), "limit": page_size, "f": "json"})
    features = []
    while url:
        page = json.loads(get(url))
        features.extend(page["features"])
        url = next((l["href"] for l in page.get("links", []) if l["rel"] == "next"), None)
        print(f"    {len(features)} features", end="\r", file=sys.stderr)
    print(file=sys.stderr)
    return features


def screen_depths(wells, tubes):
    """Depth of each tube's screen top below ground level, keyed by tube pk.

    Screen positions are in m NAP, so ground level minus screen top gives depth
    below the surface. That is what separates a phreatic tube (the one that says
    something about timber pile heads) from a deep aquifer tube.
    """
    ground = {w["properties"]["gm_gmw_pk"]: w["properties"].get("ground_level_position")
              for w in wells}
    depths = {}
    for t in tubes:
        p = t["properties"]
        gl, top = ground.get(p.get("gm_gmw_fk")), p.get("screen_top_position")
        if gl is not None and top is not None:
            depths[p["gm_gmw_monitoringtube_pk"]] = gl - top
    return depths


def download_series(glds, depths, max_screen_depth, min_last_date, out_dir):
    """Download the head time series CSV for the GLDs that pass the filters."""
    out_dir.mkdir(parents=True, exist_ok=True)
    index_rows = []
    selected = []
    for g in glds:
        p = g["properties"]
        d = depths.get(p.get("gm_gmw_monitoringtube_fk"))
        if d is None or d > max_screen_depth:
            continue
        if (p.get("research_last_date") or "") < min_last_date:
            continue
        selected.append((g, d))

    print(f"  {len(selected)} series pass the filters", file=sys.stderr)
    for i, (g, depth) in enumerate(selected, 1):
        p = g["properties"]
        bro_id = p["bro_id"]
        # Prefer assessed values; fall back to preliminary, then unvalidated.
        for kind in ("fully_assessed", "preliminary", "unknown"):
            url = p.get(f"series_{kind}_csv_url")
            if not url:
                continue
            body = get(url)
            # An empty series still returns a few blank lines.
            if body.count(b"\n") < 5 or body.lstrip().startswith(b"{"):
                continue
            path = out_dir / f"{bro_id}_{kind}.csv"
            path.write_bytes(body)
            lon, lat = g["geometry"]["coordinates"]
            index_rows.append({
                "gld_bro_id": bro_id,
                "kind": kind,
                "lon": lon,
                "lat": lat,
                "screen_depth_below_ground_m": round(depth, 2),
                "first_date": p.get("research_first_date"),
                "last_date": p.get("research_last_date"),
                "n_observations": p.get("number_of_observations"),
                "file": path.name,
            })
            break
        print(f"    {i}/{len(selected)}", end="\r", file=sys.stderr)
    print(file=sys.stderr)

    if not index_rows:
        print("  no series matched", file=sys.stderr)
        return

    index = out_dir / "series_index.csv"
    with index.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(index_rows[0]))
        w.writeheader()
        w.writerows(index_rows)
    print(f"  wrote {len(index_rows)} series and {index.name}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bbox", nargs=4, type=float, default=UTRECHT_BBOX,
                    metavar=("MINLON", "MINLAT", "MAXLON", "MAXLAT"))
    ap.add_argument("--series", action="store_true",
                    help="also download the head time series CSVs")
    ap.add_argument("--max-screen-depth", type=float, default=8.0,
                    help="only series whose screen top is within this many metres "
                         "of the surface (default 8, i.e. phreatic)")
    ap.add_argument("--min-last-date", default="2020-01-01",
                    help="only series still measured after this date")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = {}
    for name in COLLECTIONS:
        print(f"{name}:", file=sys.stderr)
        feats = fetch_collection(name, args.bbox)
        data[name] = feats
        path = OUT_DIR / f"{name}.geojson"
        path.write_text(json.dumps(
            {"type": "FeatureCollection", "features": feats}, ensure_ascii=False))
        print(f"  {len(feats)} features -> {path.relative_to(OUT_DIR.parents[2])}",
              file=sys.stderr)

    if args.series:
        print("time series:", file=sys.stderr)
        depths = screen_depths(data["gm_gmw"], data["gm_gmw_monitoringtube"])
        download_series(data["gm_gld"], depths, args.max_screen_depth,
                        args.min_last_date, OUT_DIR / "series")


if __name__ == "__main__":
    main()

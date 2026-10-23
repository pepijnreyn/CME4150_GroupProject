"""Foundation of each walmuur: original timber piles, or renewed (steel sheet or tube piles).

The asset register has no foundation data, and its `Aanlegjaar` is often not
updated after a renewal (Rak 02 OZ still says 1880, renewed in 2022). So the
foundation follows from the records of the werven programme, compiled by hand
per rak and bank in data/raw/walmuur_foundation_sources.csv (documents in
walmuur_foundation_documents.csv). Since 2013 the walmuren are renewed rak by
rak; the old foundation is pine timber piles. Two methods are used:

  sheet-pile method   old wall dug free and removed, new wall on a steel sheet
                      pile (the only method until mid-2015);
  tube-pile method    steel tube piles screwed through the old wall, new
                      prefabricated wall on top (narrow werven, near trees).

Matching a register wall to a rak and bank: the project names sides "rak 5
west", the register "Rak 05 ZZ", and the Kromme Nieuwegracht walls have no
rak in their name. The city's werfmuren layer (UtrechtOpen WFS) gives each
wall polygon its rak and bank (OOSTOEVER, WESTOEVER), so each walmuur gets
the rak and bank of the polygons at 10 places along it.

A row in the sources file with a `nummer` applies to that wall only and
overrides the row for its rak and bank. A wall without any row is taken as
renewed when `Aanlegjaar` is 2013 or later (method unknown), and otherwise as
still on timber piles, an assumption.

The werfmuren layer is downloaded once and saved in data/raw/UtrechtOpen/.
Delete that file to download it again.

Writes data/processed/walmuur_foundation.csv, one row per walmuur.
Run: python scripts/build_walmuur_foundation.py
"""

import collections
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from build_walmuur_height import places_along, walmuur_lines
from build_walmuur_traffic import distance_to_line, entry_distance, rings
from plot_screening_sankey import load, to_num, walmuren

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "raw" / "walmuur_foundation_sources.csv"
DOCUMENTS = ROOT / "data" / "raw" / "walmuur_foundation_documents.csv"
WERFMUREN_CACHE = ROOT / "data" / "raw" / "UtrechtOpen" / "werfmuren.geojson"
OUT = ROOT / "data" / "processed" / "walmuur_foundation.csv"
WFS = "https://geodata.utrecht.nl/geoserver/UtrechtOpen/ows"

N_PLACES = 10               # places along each wall where the layer is read
MATCH_M = 3.0               # m; a layer polygon this close to a place counts
PROGRAMME_START = 2013      # first year of the renewals; later register years are renewals
BANKS = {"OOSTOEVER": "oost", "WESTOEVER": "west"}


def werfmuren() -> list:
    """Wall polygons of the werven with rak, bank and wall type; downloaded once."""
    if WERFMUREN_CACHE.exists():
        return json.loads(WERFMUREN_CACHE.read_text())["features"]

    print("Downloading the werfmuren layer from UtrechtOpen ...")
    query = {"service": "WFS", "version": "2.0.0", "request": "GetFeature",
             "typeNames": "UtrechtOpen:Werfmuren", "outputFormat": "application/json",
             "srsName": "EPSG:4326"}
    with urllib.request.urlopen(WFS + "?" + urllib.parse.urlencode(query),
                                timeout=180) as response:
        layer = json.loads(response.read())
    keep = ("IMGEO_LOKAALID", "TYPE_MUUR", "ZIJDE", "RAK")
    features = [{"type": "Feature", "geometry": f["geometry"],
                 "properties": {k: f["properties"][k] for k in keep}}
                for f in layer["features"]]
    WERFMUREN_CACHE.parent.mkdir(parents=True, exist_ok=True)
    WERFMUREN_CACHE.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    return features


def distance_to_polygon(lon: float, lat: float, polygon: dict) -> float:
    """Distance in metres from a point to a polygon; 0 inside it."""
    if entry_distance(lon, lat, 1.0, 0.0, polygon) == 0.0:
        return 0.0
    return min(distance_to_line(lon, lat, ring) for ring in rings(polygon["geometry"]))


def rak_and_bank(line: list, polygons: list) -> dict:
    """Rak, bank and wall type of the layer polygons along the wall (majority)."""
    lons, lats = [c[0] for c in line], [c[1] for c in line]
    margin = 0.0002                             # about 15-20 m, a coarse box first
    nearby = [p for p in polygons
              if any(min(lons) - margin < c[0] < max(lons) + margin
                     and min(lats) - margin < c[1] < max(lats) + margin
                     for ring in rings(p["geometry"]) for c in ring)]
    votes = collections.Counter()
    for lon, lat, _, _ in places_along(line, N_PLACES):
        found = [(distance_to_polygon(lon, lat, p), p) for p in nearby]
        found = [f for f in found if f[0] <= MATCH_M]
        if found:
            p = min(found, key=lambda f: f[0])[1]["properties"]
            votes[(p["RAK"], p["ZIJDE"], p["TYPE_MUUR"])] += 1
    if not votes:
        return {}
    (rak, bank, wall_type), n = votes.most_common(1)[0]
    return {"rak": int(rak.split()[-1]), "side": BANKS.get(bank), "layer_type": wall_type,
            "layer_share": n / N_PLACES}


def sources() -> pd.DataFrame:
    s = pd.read_csv(SOURCES, dtype={"nummer": str})
    known = set(pd.read_csv(DOCUMENTS)["key"])
    missing = {k for keys in s["sources"] for k in keys.split(";")} - known
    if missing:
        raise SystemExit(f"Sources without a document in {DOCUMENTS.name}: {sorted(missing)}")
    return s


def foundation_for_wall(wall: pd.Series, match: dict, s: pd.DataFrame) -> dict:
    result = {"Nummer": wall["Nummer"], "Naam": wall["Naam"], "Aanlegjaar": wall["Aanlegjaar"],
              **match}
    rows = s[s["nummer"] == wall["Nummer"]]
    if rows.empty and match:
        rows = s[(s["rak"] == match["rak"]) & (s["side"] == match["side"]) & s["nummer"].isna()]
    if not rows.empty:
        row = rows.iloc[0]
        result.update({k: row[k] for k in ("status", "method", "year", "certainty",
                                            "remaining", "sources", "note")})
    elif wall["Aanlegjaar"] >= PROGRAMME_START:
        result.update({"status": "renewed", "method": "unknown", "year": wall["Aanlegjaar"],
                       "certainty": "register", "note": "No document found; register "
                       f"Aanlegjaar {wall['Aanlegjaar']:.0f} is after the start of the "
                       "renewals in 2013."})
    else:
        result.update({"status": "not renewed", "method": "timber piles",
                       "certainty": "assumed", "note": "No renewal found in the documents."})
    return result


def main() -> None:
    lines = walmuur_lines()
    polygons = [p for p in werfmuren() if p["properties"]["RAK"]]
    s = sources()
    w = walmuren(load())
    w["Aanlegjaar"] = to_num(w["Aanlegjaar"])
    out = pd.DataFrame([foundation_for_wall(wall, rak_and_bank(lines[wall["Nummer"]], polygons), s)
                        for _, wall in w.iterrows()])
    out = out.sort_values(["rak", "side", "Naam"])
    out.to_csv(OUT, index=False)

    print(f"{len(out)} walmuren -> {OUT.relative_to(ROOT)}\n")
    print(out.groupby(["status", "method"]).size().to_string())
    print("\nCertainty:", out["certainty"].value_counts().to_dict())


if __name__ == "__main__":
    main()

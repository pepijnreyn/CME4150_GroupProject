"""Per-wall data gaps for the walls that get a failure probability.

Takes the walls that end in "red or orange" in the screening of
plot_screening_sankey.py (in use, past design life, masonry) and lists per
wall which inputs of the strength models are in the data:

  input            source                                    counted missing when
  H                areaal `Hoogte`                           empty, or outside 0.5-10 m
  t                areaal `Breedte` (meaning not confirmed)  empty, or above 1.5 m
  canal level      areaal `Valhoogte` (drop to the water)    empty
  groundwater      objects_groundwater.csv (GHG, GLG)        no value, or "no support"
  soil type        masonry_walls_soil.csv (DINO borings)     no boring within 250 m
  foundation age   areaal `Aanlegjaar`                       1917 (possibly a default) or
                                                             before 1850 (original wall)

The year rules: 1917 is possibly a default year in the register, and a
year before 1850 is that of the original wall, not of the current
foundation (the walmuren were renovated in the 1950s-60s and restored in
1975-1985, Erfgoed Utrecht report 114).

Missing for every wall, so not a column: traffic load q (its distance to the
wall and the axle limit are in walmuur_traffic.csv), pile data (the foundation
type and renewal year are in walmuur_foundation.csv), consequence class.

Writes data/processed/masonry_walls_data_gaps.csv, one row per wall.
Run: python scripts/build_masonry_data_gaps.py, after build_soil_type.py
"""

from pathlib import Path

import pandas as pd

from plot_screening_sankey import load, register, to_num

ROOT = Path(__file__).resolve().parents[1]
GROUNDWATER = ROOT / "data" / "processed" / "objects_groundwater.csv"
SOIL = ROOT / "data" / "processed" / "masonry_walls_soil.csv"
OUT = ROOT / "data" / "processed" / "masonry_walls_data_gaps.csv"

H_MIN, H_MAX = 0.5, 10.0    # m; Hoogte outside this is an entry error (max is 380 m)
T_MAX = 1.5                 # m; Breedte above this is no wall thickness (walmuren: 3.0 m)
DEFAULT_YEAR = 1917         # possibly a placeholder year
ORIGINAL_BEFORE = 1850      # year of the original wall; the foundation was renewed since

INPUTS = ["H", "t", "canal level", "groundwater", "soil type", "foundation age"]


def walls() -> pd.DataFrame:
    """The red-or-orange walls of the screening, numeric fields cast."""
    r = register(load())
    w = r[r["cls"] == "pf"].copy()
    for col in ("Hoogte", "Breedte", "Valhoogte"):
        w[col] = to_num(w[col])
    return w


def groundwater() -> pd.DataFrame:
    """GHG and GLG depth below ground per object, with the support label."""
    g = pd.read_csv(GROUNDWATER).drop_duplicates("Nummer")   # a few non-quay IDs repeat
    g["ghg_depth_m"] = g["glg_depth_below_ground_m"] - g["swing_m"]
    g = g.rename(columns={"glg_depth_below_ground_m": "glg_depth_m", "support": "gw_support"})
    return g.set_index("Nummer")[["ghg_depth_m", "glg_depth_m", "gw_support"]]


def soil() -> pd.DataFrame:
    """Soil type per wall from build_soil_type.py, with the distance to the boring."""
    s = pd.read_csv(SOIL).rename(columns={"boring_dist_m": "soil_boring_m",
                                          "support": "soil_support"})
    return s.set_index("Nummer")[["soil_type", "soil_boring_m", "soil_support"]]


def notes(row: pd.Series) -> str:
    """Values that are in the data but not usable as they stand."""
    out = []
    if pd.notna(row["H_m"]) and not H_MIN <= row["H_m"] <= H_MAX:
        out.append(f"Hoogte {row['H_m']:g} m out of range")
    if pd.notna(row["t_m"]) and row["t_m"] > T_MAX:
        out.append(f"Breedte {row['t_m']:g} m is no wall thickness")
    if row["Aanlegjaar"] == DEFAULT_YEAR:
        out.append(f"Aanlegjaar {DEFAULT_YEAR} possibly a default")
    elif row["Aanlegjaar"] < ORIGINAL_BEFORE:
        out.append(f"Aanlegjaar {row['Aanlegjaar']:.0f} is the original wall")
    if row["gw_support"] == "no support":
        out.append("groundwater: no well within 400 m")
    return "; ".join(out)


def gaps(w: pd.DataFrame, g: pd.DataFrame, s: pd.DataFrame) -> pd.DataFrame:
    t = pd.DataFrame({
        "Nummer": w["Nummer"],
        "Naam": w["Naam"],
        "Objecttype": w["Objecttype"],
        "Kunstwerktype": w["Kunstwerktype"].fillna("").replace("", "(blank)"),
        "Aanlegjaar": w["Aanlegjaar"].astype("Int64"),
        "Eindjaar": w["Eindjaar"].astype("Int64"),
        "Lengte_m": w["Lengte"].round(1),
        "H_m": w["Hoogte"],
        "t_m": w["Breedte"],
        "canal_depth_m": w["Valhoogte"],
    }).join(g.round(2), on="Nummer").join(s, on="Nummer")

    have = pd.DataFrame({
        "H": t["H_m"].between(H_MIN, H_MAX),
        "t": t["t_m"] <= T_MAX,
        "canal level": t["canal_depth_m"].notna(),
        "groundwater": t["gw_support"].notna() & (t["gw_support"] != "no support"),
        "soil type": t["soil_type"].notna(),
        "foundation age": (t["Aanlegjaar"] != DEFAULT_YEAR) & (t["Aanlegjaar"] >= ORIGINAL_BEFORE),
    })
    t["missing"] = have.apply(lambda r: "; ".join(k for k in INPUTS if not r[k]), axis=1)
    t["n_missing"] = (~have).sum(axis=1)
    t["notes"] = t.apply(notes, axis=1)
    return t.sort_values(["Kunstwerktype", "Nummer"]), have


def main() -> None:
    t, have = gaps(walls(), groundwater(), soil())
    t.to_csv(OUT, index=False)
    print(f"{len(t)} walls, {t['Lengte_m'].sum():,.0f} m -> {OUT.relative_to(ROOT)}\n")

    have = have.assign(group=t["Kunstwerktype"], length=t["Lengte_m"])
    s = have.groupby("group").agg(walls=("H", "size"), length_m=("length", "sum"),
                                  **{k: (k, "sum") for k in INPUTS})
    s["complete"] = (t["n_missing"] == 0).groupby(t["Kunstwerktype"]).sum()
    s.loc["total"] = s.sum()
    print("Walls with each input in the data:")
    print(s.round().astype(int).sort_values("walls", ascending=False).to_string())


if __name__ == "__main__":
    main()

"""Markdown table of the walmuren of the Wervengebied and the data per wall.

One row per walmuur: the 51 of screening.walmuren(). One column
per input the strength models need per wall, filled with the value from the data, or a dash if no
data set has it. The last row counts the walls with a value per column.

Values that are in the data but doubtful get a footnote marker, with the
same rules as build_masonry_data_gaps.py. The wall thickness of Oudegracht
masonry walmuren without a usable value is an assumption, marked [e] and
counted apart from the data in the last row. The soil type comes from
build_soil_type.py. The werf level and H come from build_walmuur_height.py:
H is an estimate (measured werf level minus an assumed canal bottom), marked
[g] and also counted apart; walls that may have no werf are marked [h]. The
distance to the road and the axle limit come from build_walmuur_traffic.py,
the foundation and its renewal year from build_walmuur_foundation.py.

Writes figures/wervengebied_data_table.md.
Run: python scripts/table_wervengebied_data.py, after build_soil_type.py,
build_walmuur_height.py, build_walmuur_traffic.py and build_walmuur_foundation.py
"""

from pathlib import Path

import pandas as pd

from build_masonry_data_gaps import DEFAULT_YEAR, ORIGINAL_BEFORE, T_MAX, groundwater, soil
from build_soil_type import WHARF_LEVEL_NAP
from build_walmuur_height import BED_AT_WALL_NAP, NO_WERF_ABOVE
from build_walmuur_traffic import MAX_A_M, SIGN_RADIUS_M
from screening import CANALS, YEAR_FIXES, load, to_num, walmuren, with_renewals

ROOT = Path(__file__).resolve().parents[1]
HEIGHT = ROOT / "data" / "processed" / "walmuur_height.csv"
TRAFFIC = ROOT / "data" / "processed" / "walmuur_traffic.csv"
FOUNDATION = ROOT / "data" / "processed" / "walmuur_foundation.csv"
OUT = ROOT / "figures" / "wervengebied_data_table.md"

DASH = "–"
T_ASSUMED = (0.40, 0.45)    # m, Uniform; Oudegracht walmuren without a usable thickness
SCREENING = {"pf": "red/orange", "green": "green", "orange": "orange",
             "unclassified": "not classified"}
SOIL_LABELS = {"soft_clay_peat": "soft clay / peat", "mixed": "mixed", "sand": "sand"}

# Header, what it is needed for, where it comes from.
COLUMNS = [
    ("Nummer", "register ID", "`Nummer`"),
    ("Name", "", "`Naam`"),
    ("Screening", "green if `Eindjaar` (Aanlegjaar + 80) ≥ 2026, else red/orange (Pf needed) "
     "for masonry; a wall renewed on steel counts from its renewal year",
     "`Aanlegjaar`, `Eindjaar`, `Bouwmateriaal`; renewal year (`walmuur_foundation.csv`)"),
    ("Material", "screening: masonry or not", "`Bouwmateriaal`"),
    ("Built", "design life (screening) and foundation age t (timber decay)", "`Aanlegjaar`"),
    ("Length [m]", "length of the wall, for reporting per metre", "`Lengte`"),
    ("Werf level [m NAP]", "top of the retained soil, gives H",
     "AHN ground level beside the wall (`walmuur_height.csv`)"),
    ("H [m]", "retained height, werf to canal bottom: soil load, overturning",
     "werf level − assumed canal bottom [g]; `Hoogte` is empty"),
    ("t [m]", "wall thickness: resisting moment M_R",
     "`Breedte` (width seen from above); Oudegracht gaps assumed [e]"),
    ("Canal level [m]", "drop from the top to the water: water load, uplift", "`Valhoogte`"),
    ("Canal bottom", "soundings per rak, gives H (to request from the city); now taken "
     f"at the wall underside, {BED_AT_WALL_NAP:.2f} m NAP [g]", "not in the data"),
    ("Groundwater [m]", "GHG–GLG depth below ground: water load",
     "BRO wells, interpolated (`objects_groundwater.csv`)"),
    ("Soil type", "K and γ_s per wall (`SOIL_TYPES` in SoilForce.py)", "DINO borings, nearest within 250 m, distance in brackets "
     "(`masonry_walls_soil.csv`)"),
    ("Foundation", "original timber piles, or renewed on steel sheet or tube piles: "
     "whether a timber decay model applies", "werven programme records per "
     "rak and bank (`walmuur_foundation.csv`)"),
    ("Pile diameter", "D0 per wall; now about 180 mm for all (IBU design note)", "not in the data"),
    ("Foundation renewed", "year of the last foundation renewal: the new steel foundation; "
     "gives t only for walls still on timber (to request from the city)",
     "werven programme records (`walmuur_foundation.csv`)"),
    ("Road a [m]", "distance a from the wall to the nearest carriageway or parking bay, "
     "in plan: q_eff in TraficLoad.py", "BGT road areas, at 6 places along the wall "
     "(`walmuur_traffic.csv`)"),
    ("Axle limit [t]", "heaviest axle allowed on the street: bounds the vehicle that sets q",
     f"NDW traffic sign C20, nearest within {SIGN_RADIUS_M:.0f} m, distance in brackets "
     "(`walmuur_traffic.csv`)"),
    ("Traffic load q", "q [kN/m²], from the axle limit (traffic model of other group "
     "members); on the werf itself, 5 kN/m² for pedestrians (NEN-EN 1991-1-1)",
     "not in the data"),
    ("CC", "consequence class for β_min (NEN 8700)", "not in the data"),
]
NOT_IN_DATA = [h for h, _, src in COLUMNS if src == "not in the data"]

FOOTNOTES = {
    "a": f"{DEFAULT_YEAR}, possibly a default year.",
    "b": "year of the original wall; the walmuren were renovated in the 1950s–60s and "
         "1975–1985, so this is not the age of the foundation.",
    "c": f"above {T_MAX:g} m, too large for a wall thickness: `Breedte` means something "
         "else here. Not counted in the bottom row.",
    "d": "register says {orig}, read as {fixed} (typo).",
    "e": f"assumption, t ~ Uniform({T_ASSUMED[0]:.2f}, {T_ASSUMED[1]:.2f}) m, for Oudegracht "
         "masonry walmuren where the register has no usable thickness (empty, or a 3 m "
         "strip). Based on 0.41 m (Rak 02 OZ, built 1880), 0.45 m (Rak 12–14, rebuilt "
         "2015–16) and a removed walmuur of 0.40 m (Erfgoed Utrecht, Rapportages "
         "archeologie 156). Thickness at the top; the wall may be thicker lower down. "
         "Not used for the Nieuwegracht and Kromme Nieuwegracht.",
    "g": "estimate, not data: H = werf level − canal bottom. The werf level is measured "
         "(AHN); the canal bottom is not, and is taken at the underside of the wall "
         f"({BED_AT_WALL_NAP:.2f} m NAP, Erfgoed Utrecht report 158). The bed may be "
         "deeper, so H is a lower bound. Counted apart from the data in the bottom row.",
    "h": f"AHN shows ground above +{NO_WERF_ABOVE:.1f} m NAP beside this wall (street "
         "level, or a bridge or stair), so it may have no werf and H is not estimated. "
         "Check on a map. Not counted in the bottom row.",
    "p": "part of this wall is not renewed yet (`remaining` in `walmuur_foundation.csv`).",
    "t": "no renewal found in the programme documents, so assumed to be still on the "
         "original timber piles. Counted apart from the data in the bottom row.",
    "u": "a renewal was started or planned, but no document confirms that it was "
         "finished or which method was used. Not counted in the bottom row.",
}


def cell(value, fmt: str = "{:.2f}") -> str:
    return DASH if pd.isna(value) else fmt.format(value)


def built(row: pd.Series) -> str:
    year = f"{row['Aanlegjaar']:.0f}"
    if row["Nummer"] in YEAR_FIXES:
        return f"{year} [d]"
    if row["Aanlegjaar"] == DEFAULT_YEAR:
        return f"{year} [a]"
    if row["Aanlegjaar"] < ORIGINAL_BEFORE:
        return f"{year} [b]"
    return year


def thickness(row: pd.Series) -> str:
    if row["assume_t"]:
        return f"{T_ASSUMED[0]:.2f}–{T_ASSUMED[1]:.2f} [e]"
    return cell(row["Breedte"]) + (" [c]" if row["Breedte"] > T_MAX else "")


def heights() -> pd.DataFrame:
    """Werf level and H per walmuur, from build_walmuur_height.py."""
    h = pd.read_csv(HEIGHT)
    return h.set_index("Nummer")[["werf_nap", "werf", "H_bed_at_wall_m"]]


def werf_level(row: pd.Series) -> str:
    if pd.isna(row["werf_nap"]):
        return DASH
    return f"{row['werf_nap']:.2f}" + ("" if row["werf"] == "yes" else " [h]")


def height(row: pd.Series) -> str:
    if pd.isna(row["werf_nap"]):
        return DASH
    if row["werf"] != "yes":
        return f"{DASH} [h]"
    return f"{row['H_bed_at_wall_m']:.2f} [g]"


def foundations() -> pd.DataFrame:
    """Foundation per walmuur, from build_walmuur_foundation.py."""
    f = pd.read_csv(FOUNDATION)
    return f.set_index("Nummer")[["status", "method", "year", "certainty", "remaining"]]


def foundation(row: pd.Series) -> str:
    part = " [p]" if pd.notna(row["remaining"]) else ""
    if row["status"] == "unclear":
        return "unclear [u]"
    if row["status"] == "in progress":
        return "timber piles, renewal in progress"
    if row["status"] == "not renewed":
        return "timber piles" + ("" if row["certainty"] == "documented" else " [t]")
    if row["method"] == "unknown":
        return f"renewed, method unknown{part}"
    return row["method"] + ("?" if row["certainty"] == "inferred" else "") + part


def renewed_year(row: pd.Series) -> str:
    if row["status"] == "in progress":
        return "in progress"
    return cell(row["year"], "{:.0f}") if row["status"] == "renewed" else DASH


def traffic() -> pd.DataFrame:
    """Distance to the road and axle limit per walmuur, from build_walmuur_traffic.py."""
    t = pd.read_csv(TRAFFIC)
    return t.set_index("Nummer")[["n_places", "n_places_road", "a_min_m", "a_max_m",
                                  "axle_limit_t", "axle_sign_m"]]


def road_distance(row: pd.Series) -> str:
    if row["n_places_road"] == 0:
        return f"> {MAX_A_M:.0f}"
    high = (f"{row['a_max_m']:.1f}" if row["n_places_road"] == row["n_places"]
            else f"> {MAX_A_M:.0f}")
    return f"{row['a_min_m']:.1f}–{high}"


def table() -> pd.DataFrame:
    w = (with_renewals(walmuren(load()))
         .join(groundwater(), on="Nummer").join(soil(), on="Nummer")
         .join(heights(), on="Nummer").join(traffic(), on="Nummer")
         .join(foundations(), on="Nummer"))
    for col in ("Hoogte", "Breedte", "Valhoogte"):
        w[col] = to_num(w[col])
    w["assume_t"] = ((w["group"] == "Oudegracht")
                     & w["Bouwmateriaal"].fillna("").str.contains("Metselwerk")
                     & ~(w["Breedte"] <= T_MAX))
    w["canal_rank"] = w["group"].map(list(CANALS.values()).index)
    w = w.sort_values(["cls", "canal_rank", "Naam"], key=lambda s: s.map(
        {"pf": 0, "green": 1}).fillna(2) if s.name == "cls" else s)

    t = pd.DataFrame({
        "Nummer": w["Nummer"],
        "Name": w["Naam"].str.strip().str.replace("|", "/", regex=False),
        "Screening": w["cls"].map(SCREENING),
        "Material": w["Bouwmateriaal"].fillna(DASH),
        "Built": w.apply(built, axis=1),
        "Length [m]": w["Lengte"].map(lambda x: cell(x, "{:.1f}")),
        "Werf level [m NAP]": w.apply(werf_level, axis=1),
        "H [m]": w.apply(height, axis=1),
        "t [m]": w.apply(thickness, axis=1),
        "Canal level [m]": w["Valhoogte"].map(cell),
        "Groundwater [m]": [DASH if pd.isna(lo) else f"{hi:.2f}–{lo:.2f}"
                            for hi, lo in zip(w["ghg_depth_m"], w["glg_depth_m"])],
        "Soil type": [DASH if pd.isna(s) else f"{SOIL_LABELS[s]} ({d:.0f} m)"
                      for s, d in zip(w["soil_type"], w["soil_boring_m"])],
        "Foundation": w.apply(foundation, axis=1),
        "Foundation renewed": w.apply(renewed_year, axis=1),
        "Road a [m]": w.apply(road_distance, axis=1),
        "Axle limit [t]": [DASH if pd.isna(t) else f"{t:.1f} ({d:.0f} m)"
                           for t, d in zip(w["axle_limit_t"], w["axle_sign_m"])],
    })
    for header in NOT_IN_DATA:
        t[header] = DASH
    return t[[h for h, _, _ in COLUMNS]]


def markdown(t: pd.DataFrame) -> str:
    n = len(t)
    marker = lambda m: t.apply(lambda col: col.astype(str).str.endswith(m))
    usable = (t.ne(DASH) & ~marker("[c]") & ~marker("[e]") & ~marker("[g]") & ~marker("[h]")
              & ~marker("[t]") & ~marker("[u]"))
    assumed = (marker("[e]") | marker("[t]")).sum()
    estimated = marker("[g]").sum()
    counts = {h: f"**{usable[h].sum()}/{n}**"
                 + (f" + {assumed[h]} assumed" if assumed[h] else "")
                 + (f" + {estimated[h]} estimated" if estimated[h] else "")
              for h in t.columns}
    counts["Nummer"], counts["Name"] = "**with data**", ""
    fixes = "; ".join(FOOTNOTES["d"].format(orig=fixed + 100, fixed=fixed)
                      for fixed in YEAR_FIXES.values())

    lines = [
        "# Walmuren of the Wervengebied: data per wall",
        "",
        f"All {n} walmuren of the Wervengebied in the municipal asset register "
        "(`Kunstwerktype Utrecht` = Walmuur, name not empty). Each column is an input the "
        "strength models need per wall. A dash (–) means no data set we have "
        "contains it for that wall. Cells marked [e] are an assumption and cells "
        "marked [g] an estimate, not data.",
        "",
        "Generated by `scripts/table_wervengebied_data.py`; rerun it after the data changes. "
        "How each value is determined: `wervengebied_data_table_README.md`.",
        "",
        "## Columns",
        "",
        "| Column | Needed for | Source |",
        "|---|---|---|",
        *[f"| {h} | {need} | {src} |" for h, need, src in COLUMNS],
        "",
        "## Walls",
        "",
        "| " + " | ".join(t.columns) + " |",
        "|" + "|".join("---" for _ in t.columns) + "|",
        *["| " + " | ".join(map(str, row)) + " |" for row in t.itertuples(index=False)],
        "| " + " | ".join(counts[h] for h in t.columns) + " |",
        "",
        f"[a] {FOOTNOTES['a']}  ",
        f"[b] {FOOTNOTES['b']}  ",
        f"[c] {FOOTNOTES['c']}  ",
        f"[d] {fixes}  ",
        f"[e] {FOOTNOTES['e']}  ",
        f"[g] {FOOTNOTES['g']}  ",
        f"[h] {FOOTNOTES['h']}  ",
        f"[p] {FOOTNOTES['p']}  ",
        f"[t] {FOOTNOTES['t']}  ",
        f"[u] {FOOTNOTES['u']}",
        "",
        "Groundwater is never measured at the wall: every value is a weighted average "
        "of the 6 nearest BRO wells, which lie a few hundred metres away "
        "(`nearest_well_m` in `objects_groundwater.csv`). The depth is below the ground level at "
        "the wells, not below the werf the walmuren stand on; `glg_m_nap` in "
        "`objects_groundwater.csv` gives the level in m NAP.",
        "",
        "Soil type is read from the nearest DINO boring over the soil the walmuur "
        f"holds back: from the werf at +{WHARF_LEVEL_NAP:.2f} m NAP down to the underside "
        f"of the wall at {BED_AT_WALL_NAP:.2f} m NAP (both from Erfgoed Utrecht report 158, "
        "as `Hoogte` is empty). It is soft clay / "
        "peat or sand when at least 70% of that range is clay-like or sand-like, and "
        "mixed otherwise. Nearby borings often disagree and many descriptions are old, "
        "so this is a best guess per wall. `masonry_walls_soil.csv` gives the boring, "
        "the shares and how many borings within 150 m agree; it is made by "
        "`scripts/build_soil_type.py`.",
        "",
        "Road a is the distance in plan from the wall to the first carriageway or parking "
        "bay towards the werf side, lowest and highest of 6 places along the wall "
        f"(> {MAX_A_M:.0f} m: none that close). On the walls with a werf that road runs at "
        "street level, over the werfkelders, and not on the soil the walmuur holds back; "
        "the load on the werf itself is people (5 kN/m² in NEN-EN 1991-1-1, at a = 0). The axle "
        "limit is the posted maximum axle load of the nearest C20 sign; a sign more than "
        "about 30 m away may stand on another street. Every C20 sign near a walmuur says "
        "2.0 t, and most canal streets are also closed to lorries (C7). Made by "
        "`scripts/build_walmuur_traffic.py`.",
        "",
        "Foundation is read from the records of the werven programme (progress reports, "
        "archaeology reports, neighbourhood letters), per rak and bank; the register has no "
        "foundation data, and its `Aanlegjaar` is often not updated after a renewal. Steel "
        "sheet piles: old wall dug free and replaced on a sheet pile (until mid-2015 the only "
        "method). Steel tube piles: piles screwed through the old wall. A ? means the method "
        "is inferred, not stated for that rak. A renewed wall no longer stands on timber "
        "piles, so a timber decay model does not apply to it, and the screening counts its "
        "design life from the renewal year. "
        "Sources per wall: "
        "`walmuur_foundation.csv`; made by `scripts/build_walmuur_foundation.py`.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    t = table()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(markdown(t))
    print(f"{len(t)} walmuren -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

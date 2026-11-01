"""Risk class per modelled walmuur, and the results map of the report.

The probability side is relative: the failure model is not calibrated, so a
wall's class follows from its best-estimate Pf (2026, updated) against the
median of the 17 modelled walls, not from the NEN 8700 levels:

  P high    Pf more than P_FACTOR times the median
  P low     Pf less than the median divided by P_FACTOR
  P medium  in between

The consequence class comes from build_walmuur_consequence.py. Both are scored
1 (low) to 3 (high); their sum gives the risk class, as in a 3 x 3 risk matrix:
5 or 6 red, 4 orange, 2 or 3 green. The list is ordered by risk class and,
within a class, by Pf. A wall whose prior chance of type 2 is 0.5 (no dive note
on the wall type) is flagged: its class rests on missing data rather than on
evidence of a weak wall. The script also prints the classes for P_FACTOR 1.25
and 2.0, with groundwater up to the werf (walmuur_sensitivity.csv), and the
walls that are red in every variant.

Figure: left, the walmuren of the Wervengebied, the 17 modelled walls coloured
by risk class; right, beta per wall (best estimate) with the range from type 1
to type 2, which shows how much the unknown wall type matters.

Writes data/processed/walmuur_risk_class.csv, figures/results_map.png and the map alone,
figures/results_map_only.png.
Run: MPLBACKEND=Agg python3 scripts/plot_results_map.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

from build_walmuur_consequence import lines
from screening import GREEN, INK, INK_2, MUTED, ORANGE, RED, load, walmuren

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "processed" / "walmuur_failure_probability.csv"
CONSEQUENCE = ROOT / "data" / "processed" / "walmuur_consequence.csv"
WERFMUREN = ROOT / "data" / "raw" / "UtrechtOpen" / "werfmuren.geojson"
OUT = ROOT / "data" / "processed" / "walmuur_risk_class.csv"
FIG = ROOT / "figures" / "results_map.png"
FIG_MAP = ROOT / "figures" / "results_map_only.png"

P_FACTOR = 1.5
CLASS_SCORE = {"low": 1, "medium": 2, "high": 3}
COLOURS = {"red": RED, "orange": ORANGE, "green": GREEN}
LAT0 = 52.09


def short(name):
    return (name.replace("Oude Gracht - Rak ", "OG ").replace("Kromme Nieuwe Gracht ", "KNG ")
            .replace(" (thv nr 018)", ""))


def risk_table(p_factor=P_FACTOR):
    r = pd.read_csv(RESULTS)
    r = r[r["year"].eq(2026)]
    best = r[r["type"] == "unknown"].set_index("Nummer")
    t1 = r[r["type"] == "type 1"].set_index("Nummer")["beta_updated"]
    t2 = r[r["type"] == "type 2"].set_index("Nummer")["beta_updated"]
    c = pd.read_csv(CONSEQUENCE).set_index("Nummer")
    d = pd.DataFrame({"Naam": best["Naam"], "length_m": best["length_m"],
                      "beta": best["beta_updated"], "pf": best["pf_updated"],
                      "p_type2": best["p_type2"], "beta_type1": t1, "beta_type2": t2})
    d = d.join(c[["consequence_score", "consequence_class"]])
    med = d["pf"].median()
    d["p_class"] = np.where(d["pf"] > p_factor * med, "high",
                            np.where(d["pf"] < med / p_factor, "low", "medium"))
    score = d["p_class"].map(CLASS_SCORE) + d["consequence_class"].map(CLASS_SCORE)
    d["risk_class"] = np.where(score >= 5, "red", np.where(score == 4, "orange", "green"))
    d["data_flag"] = best["p_type2_prior"].round(2).eq(0.5)
    order = {"red": 0, "orange": 1, "green": 2}
    d = d.assign(_c=d["risk_class"].map(order)).sort_values(["_c", "pf"], ascending=[True, False],
                                                             kind="stable").drop(columns="_c")
    d["risk_rank"] = np.arange(1, len(d) + 1)
    return d, med


def xy(coords):
    a = np.array(coords)
    return a[:, 0] * np.cos(np.radians(LAT0)), a[:, 1]


def main() -> None:
    d, med = risk_table()
    d.round(3).to_csv(OUT)
    print(f"median Pf of the modelled walls {med:.3f} (beta {-norm.ppf(med):.2f})")
    print(d[["Naam", "length_m", "beta", "p_class", "consequence_class", "risk_class", "risk_rank"]]
          .to_string())
    print(d.groupby("risk_class")["length_m"].agg(["count", "sum"]))
    print("flagged (prior P(type 2) 0.5):", ", ".join(short(n) for n in d.loc[d["data_flag"], "Naam"]))
    variants = {f"P_FACTOR {f}": risk_table(f)[0]["risk_class"] for f in (1.25, P_FACTOR, 2.0)}
    for name, cls in variants.items():
        print(f"{name}: " + ", ".join(f"{k} {(cls == k).sum()} ({d.loc[cls[cls == k].index, 'length_m'].sum():.0f} m)"
                                      for k in ("red", "orange", "green")))
    sens = pd.read_csv(ROOT / "data" / "processed" / "walmuur_sensitivity.csv").set_index("Nummer")
    pf = pd.Series(norm.cdf(-sens.loc[d.index, "beta_groundwater_werf"]), index=d.index)
    p_class = np.where(pf > P_FACTOR * pf.median(), 3, np.where(pf < pf.median() / P_FACTOR, 1, 2))
    score = p_class + d["consequence_class"].map(CLASS_SCORE)
    variants["groundwater to werf"] = pd.Series(np.where(score >= 5, "red", np.where(score == 4, "orange", "green")),
                                                index=d.index)
    print("groundwater to werf: " + ", ".join(f"{k} {(variants['groundwater to werf'] == k).sum()}"
                                              for k in ("red", "orange", "green")))
    always = pd.concat(variants, axis=1).eq("red").all(axis=1)
    print(f"red in every variant: {', '.join(short(n) for n in d.loc[always, 'Naam'])}"
          f" ({d.loc[always, 'length_m'].sum():.0f} m)")

    features = json.loads((ROOT / "data" / "raw" / "Output areaal GU TU Delft 26-08.json")
                          .read_text())["features"]
    geom = {f["properties"]["Nummer"]: f["geometry"] for f in features if f.get("properties")}
    all_walls = walmuren(load())["Nummer"]
    res = pd.read_csv(RESULTS)
    reason = res[res["type"] == "not computed"].set_index("Nummer")["reason"]

    plt.rcParams.update({"font.family": "sans-serif", "font.size": 7})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.4, 3.6), gridspec_kw={"width_ratios": [1.15, 1.0]})
    for f in json.loads(WERFMUREN.read_text())["features"]:
        for ring in lines(f["geometry"]):
            ax.plot(*xy(ring), color="#d9d8d2", lw=0.35, zorder=1)
    for n in all_walls:
        for c in lines(geom[n]):
            if n in d.index:
                ax.plot(*xy(c), color="white", lw=4.2, solid_capstyle="round", zorder=3)
                ax.plot(*xy(c), color=COLOURS[d.loc[n, "risk_class"]], lw=2.8,
                        solid_capstyle="round", zorder=4)
            else:
                ax.plot(*xy(c), color=MUTED, lw=0.9, ls=(0, (1, 1.5)) if reason.get(n) == "no werf" else "-",
                        zorder=2)
    # Each modelled wall carries its risk rank; offsets in metres, away from the canal.
    offsets = {"OG 03 OZ": (-45, 0), "KNG 008": (-25, -30), "KNG 007": (0, -32), "KNG 006": (20, -30),
               "KNG 005": (40, -18), "OG 05 NZ": (-10, 30), "OG 06 ZZ": (30, -25), "OG 04 OZ": (-45, 0),
               "OG 09 ZOZ": (35, -5), "OG 06 NZ": (5, 30), "OG 09 WZ": (-40, 5), "OG 08 OZ": (30, 15),
               "KNG 002": (-30, 18), "KNG 004": (35, 15), "KNG 003": (0, 30), "KNG 009": (35, -12),
               "OG 09 WZ 01": (8, -40)}
    deg_x = 1 / (111_320 * np.cos(np.radians(LAT0))) * np.cos(np.radians(LAT0))
    deg_y = 1 / 111_320
    for n, row in d.iterrows():
        x, y = xy(lines(geom[n])[0])
        x0, y0 = x.mean(), y.mean()
        dx, dy = offsets[short(row["Naam"])]
        tx, ty = x0 + dx * deg_x, y0 + dy * deg_y
        ax.plot([x0, tx], [y0, ty], color=INK_2, lw=0.4, zorder=5)
        ax.text(tx, ty, str(row["risk_rank"]), ha="center", va="center", fontsize=5.6, color=INK,
                bbox={"boxstyle": "circle,pad=0.18", "fc": "white", "ec": INK_2, "lw": 0.4}, zorder=6)
    lon = np.array([5.1158, 5.1266]) * np.cos(np.radians(LAT0))
    ax.set_xlim(*lon)
    ax.set_ylim(52.0888, 52.0942)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.text(lon[0], 52.0942, "Oudegracht", fontsize=6.5, color=MUTED, style="italic", va="top")
    ax.text(lon[1], 52.0898, "Kromme\nNieuwegracht", fontsize=6.5, color=MUTED, style="italic",
            ha="right", va="top")
    handles = [plt.Line2D([], [], color=COLOURS[k], lw=2.8, label=k.capitalize()) for k in ("red", "orange", "green")]
    handles += [plt.Line2D([], [], color=MUTED, lw=0.9, label="Renewed (not modelled)"),
                plt.Line2D([], [], color=MUTED, lw=0.9, ls=(0, (1, 1.5)), label="No werf (not modelled)")]
    ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=6, borderaxespad=0,
              handlelength=1.6)
    sx = lon[1] - 0.0028
    ax.plot([sx, sx + 100 * deg_x / np.cos(np.radians(LAT0)) * np.cos(np.radians(LAT0))],
            [52.0890, 52.0890], color=INK_2, lw=1)
    ax.text(sx + 50 * deg_x, 52.0891, "100 m", ha="center", va="bottom", fontsize=5.6, color=INK_2)

    order = d.sort_values("risk_rank", ascending=False)
    yy = np.arange(len(order))
    for y, (_, row) in zip(yy, order.iterrows()):
        bx.plot([row["beta_type1"], row["beta_type2"]], [y, y], color="#c3c2b7", lw=1.8,
                solid_capstyle="round", zorder=1)
        bx.scatter(row["beta"], y, s=26, color=COLOURS[row["risk_class"]], edgecolor="white",
                   linewidth=1.0, zorder=3)
        bx.text(3.15, y, f"{row['p_type2']:.2f}", va="center", ha="right", fontsize=5.8, color=INK_2)
    bx.set_yticks(yy, [f"{r}  {short(n)}{'*' if f else ''}" for r, n, f in
                       zip(order["risk_rank"], order["Naam"], order["data_flag"])],
                  fontsize=6, color=INK_2)
    bx.set_xlim(-1.1, 3.2)
    bx.set_xticks([-1, 0, 1, 2])
    bx.axvline(-norm.ppf(med), color=MUTED, lw=0.7, ls="--", zorder=0)
    bx.text(-norm.ppf(med) + 0.05, -0.9, "median", fontsize=5.6, color=MUTED, va="center")
    bx.text(3.15, len(order) - 0.2, "P(type 2)", fontsize=5.6, color=INK_2, va="bottom", ha="right")
    bx.set_xlabel("β (2026): dot best estimate; bar type 1 to type 2", fontsize=6.3, color=INK_2)
    bx.set_ylim(-1.4, len(order) - 0.3)
    bx.grid(axis="x", color="#e8e7e1", lw=0.5)
    bx.spines[["top", "right", "left"]].set_visible(False)
    bx.tick_params(axis="y", length=0)
    bx.tick_params(axis="x", colors=INK_2, labelsize=6)
    fig.tight_layout(w_pad=1.5)
    fig.savefig(FIG, dpi=300, bbox_inches="tight")
    # The map alone, for the results section of the report
    box = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(FIG_MAP, dpi=300, bbox_inches=box.expanded(1.02, 1.02))
    print(f"-> {FIG.relative_to(ROOT)}, {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""Risk class per modelled walmuur, and the results map of the report.

The probability side is relative: the failure model is not calibrated, so a
wall's class follows from its best-estimate Pf (2026, updated) against the
median of the 17 modelled walls, not from the NEN 8700 levels:

  P high    Pf more than P_FACTOR times the median
  P low     Pf less than the median divided by P_FACTOR
  P medium  in between

The consequence class comes from build_walmuur_consequence.py. Both are scored
1 (low) to 3 (high); their sum gives the risk class, as in a 3 x 3 risk matrix:
5 or 6 red, 4 orange, 2 or 3 green.

Figure: left, the walmuren of the Wervengebied, the 17 modelled walls coloured
by risk class; right, beta per wall (best estimate) with the range from type 1
to type 2, which shows how much the unknown wall type matters.

Writes data/processed/walmuur_risk_class.csv and figures/results_map.png.
Run: MPLBACKEND=Agg python3 scripts/plot_results_map.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm

from build_walmuur_consequence import lines
from plot_screening_sankey import GREEN, INK, INK_2, MUTED, ORANGE, RED, load, walmuren

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "processed" / "walmuur_failure_probability.csv"
CONSEQUENCE = ROOT / "data" / "processed" / "walmuur_consequence.csv"
WERFMUREN = ROOT / "data" / "raw" / "UtrechtOpen" / "werfmuren.geojson"
OUT = ROOT / "data" / "processed" / "walmuur_risk_class.csv"
FIG = ROOT / "figures" / "results_map.png"

P_FACTOR = 1.5
CLASS_SCORE = {"low": 1, "medium": 2, "high": 3}
COLOURS = {"red": RED, "orange": ORANGE, "green": GREEN}
LAT0 = 52.09


def short(name):
    return (name.replace("Oude Gracht - Rak ", "OG ").replace("Kromme Nieuwe Gracht ", "KNG ")
            .replace(" (thv nr 018)", ""))


def risk_table():
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
    d["p_class"] = np.where(d["pf"] > P_FACTOR * med, "high",
                            np.where(d["pf"] < med / P_FACTOR, "low", "medium"))
    score = d["p_class"].map(CLASS_SCORE) + d["consequence_class"].map(CLASS_SCORE)
    d["risk_class"] = np.where(score >= 5, "red", np.where(score == 4, "orange", "green"))
    d["risk_rank"] = (d["pf"] * d["consequence_score"]).rank(ascending=False).astype(int)
    return d.sort_values("risk_rank"), med


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
    offsets = {1: (-45, 0), 2: (-25, -30), 3: (0, -32), 4: (20, -30), 5: (40, -18), 6: (-10, 30),
               7: (30, -25), 8: (-45, 0), 9: (35, -5), 10: (5, 30), 11: (-40, 5), 12: (30, 15),
               13: (-30, 18), 14: (35, 15), 15: (0, 30), 16: (35, -12), 17: (8, -40)}
    deg_x = 1 / (111_320 * np.cos(np.radians(LAT0))) * np.cos(np.radians(LAT0))
    deg_y = 1 / 111_320
    for n, row in d.iterrows():
        x, y = xy(lines(geom[n])[0])
        x0, y0 = x.mean(), y.mean()
        dx, dy = offsets[row["risk_rank"]]
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
    bx.set_yticks(yy, [f"{r}  {short(n)}" for r, n in zip(order["risk_rank"], order["Naam"])],
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
    print(f"-> {FIG.relative_to(ROOT)}, {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""Figures for the appendices of the report.

  app_cross_sections.png   the two walmuur types with the loads and the pivot (App. B.2)
  app_proven_strength.png  draws of the median wall: rejected by the evidence, failing,
                           surviving (App. B.4)
  fig_production_step.png  renewed length per year with the straight line, the step model
                           and the plan (Section 4.1)
  app_fault_tree.png       failing walls among the 17 and E[C] against C_f (Sections 3.1, 3.2)
  app_werf_fit.png         AHN werf points against a normal distribution, and the error of
                           the werf median per wall against the model's 0.05 m (App. B.9)

Reads walmuur_height.csv and the AHN points, and reruns the median wall
(FailureProbability.simulate), the renewal data of regression_production_rate.py
and the fault tree (fault_tree.main, on the outputs of FailureProbability.py and
ModelChecks.py).

Writes figures/app_*.png. Run: MPLBACKEND=Agg python3 scripts/plot_appendix_figures.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, Polygon
from scipy import stats
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "StressCaclulation"))

import fault_tree as FT                                  # noqa: E402
import regression_production_rate as RP                  # noqa: E402
import FailureProbability as FP                          # noqa: E402
from WallResistance import SECTIONS                      # noqa: E402
from screening import GREEN, INK, INK_2, MUTED, ORANGE, RED  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"
MEDIAN_WALL = "Oude Gracht - Rak 09 WZ"
BLUE = "#2a78d6"
GREY = "#c3c2b7"
MATERIAL = {"masonry": ("#c9724b", "masonry"), "concrete": ("#b9b6ad", "tamped concrete"),
            "rc": ("#8d8a82", "reinforced concrete"), "timber": ("#a8814f", "timber floor"),
            "soil": ("#e8dcc0", "soil on the floor")}

plt.rcParams.update({"font.family": "sans-serif", "font.size": 7.5, "axes.edgecolor": INK_2,
                     "axes.labelcolor": INK, "xtick.color": INK_2, "ytick.color": INK_2,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.savefig(FIGURES / name, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"-> figures/{name}")


def arrow(ax, start, end, color=INK, lw=0.9):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=7, color=color, lw=lw))


def cross_sections():
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.3), sharey=True)
    for ax, (name, s) in zip(axes, SECTIONS.items()):
        for mat, pts in s["parts"]:
            ax.add_patch(Polygon(pts, closed=True, fc=MATERIAL[mat][0], ec=INK_2, lw=0.5,
                                 label=MATERIAL[mat][1]))
        base, back, werf = s["base"], s["back"], s["werf"]
        # piles: 4 m long, drawn 1.3 m; the front row of type 2 is raked 10:1 towards the canal.
        # Type 1 stands on timber beams (kesp) between the floor and the pile heads.
        for i, x in enumerate(s["piles"]):
            dx = -s["rake"] * 1.3 if i == 0 else 0.0
            if s["pile_head"] < s["base"]:
                ax.add_patch(Polygon([(x - 0.09, s["base"]), (x + 0.09, s["base"]),
                                      (x + 0.09, s["pile_head"]), (x - 0.09, s["pile_head"])],
                                     fc="#a8814f", ec=INK_2, lw=0.5))
            ax.plot([x, x + dx], [s["pile_head"], s["pile_head"] - 1.3], color="#7a5a32", lw=2.2,
                    solid_capstyle="butt")
        # water: canal in front, groundwater range behind
        ax.axhspan(-1.9, 0.6, xmin=0, xmax=0.18, color="#d6e6f7", zorder=0)
        ax.plot([-0.6, 0], [0.6, 0.6], color=BLUE, lw=0.8)
        ax.text(-0.62, 0.64, "canal\n+0.6", color=BLUE, fontsize=6.3, va="bottom")
        ax.fill_between([back, back + 0.9], 0.5, 0.9, color="#d6e6f7", lw=0, zorder=0)
        ax.text(back + 0.92, 0.7, "groundwater\n+0.5 to +0.9", color=BLUE, fontsize=6.3, va="center")
        # werf and surcharge at distance a from the front face
        ax.plot([0.0, back + 1.6], [werf, werf], color=INK_2, lw=0.6)
        a = 0.9
        for xq in np.linspace(a, back + 1.5, 6):
            arrow(ax, (xq, werf + 0.32), (xq, werf + 0.02), color=ORANGE)
        ax.plot([a, back + 1.5], [werf + 0.32, werf + 0.32], color=ORANGE, lw=0.8)
        ax.text(a + 0.02, werf + 0.37, "surcharge q at distance a", color=ORANGE, fontsize=6.5)
        # earth and water pressure on the back of the body, resultant S
        H = werf - base
        for z in np.linspace(werf - 0.1, base + 0.05, 6):
            length = 0.55 * (werf - z) / H + 0.05
            arrow(ax, (back + length, z), (back + 0.01, z), color=RED, lw=0.7)
        ax.text(back + 0.62, base + 0.1, "earth and water\npressure: S", color=RED, fontsize=6.5)
        # weight and pivot
        ax.plot(s["piles"][0], base, marker="o", ms=5, mfc="white", mec=INK, mew=1.0, zorder=5)
        ax.text(s["piles"][0] - 0.05, base - 0.17, "pivot", fontsize=6.5, ha="right")
        xc = 0.45 * back
        arrow(ax, (xc, base + 0.85), (xc, base + 0.35), color=INK, lw=1.2)
        ax.text(xc, base + 0.92, "weight: $M_W$", fontsize=6.3, ha="center",
                bbox={"fc": "white", "ec": "none", "alpha": 0.8, "pad": 0.5})
        ax.annotate("", (back + 2.35, werf), (back + 2.35, base),
                    arrowprops={"arrowstyle": "<->", "color": INK_2, "lw": 0.6})
        ax.text(back + 2.4, (werf + base) / 2, f"H\n{H:.2f} m", fontsize=6.3, va="center")
        title = ("Type 1: masonry on a timber floor,\nvertical piles, pinned heads" if name == "type 1"
                 else "Type 2: facing and tamped concrete on a\nconcrete floor, front row raked, fixed heads")
        ax.set_title(title, fontsize=7.5, loc="left", color=INK)
        ax.set_xlim(-0.65, back + 2.75)
        ax.set_ylim(-2.0, 1.75)
        ax.set_aspect("equal")
        ax.set_xlabel("x from the front face [m]")
    axes[0].set_ylabel("Level [m NAP]")
    handles, labels = [], []
    for ax in axes:
        for h, l in zip(*ax.get_legend_handles_labels()):
            if l not in labels:
                handles.append(h)
                labels.append(l)
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False, fontsize=6.5,
               bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "app_cross_sections.png")


def proven_strength():
    walls = FP.wall_table().set_index("Naam")
    wall = walls.loc[MEDIAN_WALL]
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.9), sharey=True)
    for i, (ax, t) in enumerate(zip(axes, ("type 1", "type 2"))):
        x = FP.simulate(wall, t, np.random.default_rng(100 + i))
        margin = x["M_R"] - x["S"]
        ratio = np.clip(np.nan_to_num(x["ratio_2026"], posinf=3.0), 0, 3.0)
        stands = x["stands"]
        fail = x["overturning"] | x["pile_2026"]
        idx = np.random.default_rng(7).choice(len(margin), 4000, replace=False)
        groups = [(~stands, GREY, "rejected: would fail today"),
                  (stands & ~fail, BLUE, "stands today, survives"),
                  (stands & fail, RED, "stands today, fails with surcharge")]
        for mask, colour, label in groups:
            j = idx[mask[idx]]
            ax.scatter(margin[j], ratio[j], s=2.5, color=colour, alpha=0.6, lw=0, label=label,
                       rasterized=True)
        ax.axvline(0, color=INK_2, lw=0.6, ls="--")
        ax.axhline(1, color=INK_2, lw=0.6, ls="--")
        p_e = stands.mean()
        pf = (fail & stands).sum() / stands.sum()
        ax.set_title(f"{t.capitalize()}: P(stands today) = {p_e:.2f}\n"
                     f"$P_f$ given that it stands = {pf:.3f} ($\\beta$ = {-norm.ppf(pf):.2f})",
                     fontsize=7, loc="left", color=INK)
        ax.set_xlabel("Overturning margin $M_R - S$ [kNm/m]")
        ax.set_xlim(-6, 14)
        ax.text(-5.7, 2.85, "pile breaks", fontsize=6.3, color=MUTED, va="top")
        ax.text(-5.7, 0.05, "overturns", fontsize=6.3, color=MUTED, va="bottom")
    axes[0].set_ylabel("Pile stress / MOR (2026) [-]")
    axes[0].set_ylim(0, 3.0)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, markerscale=4, fontsize=6.8,
               bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "app_proven_strength.png")


def production_step():
    """Renewed length per year with the straight line, the step model and the plan (report 4.1)."""
    per_year = RP.renewed_per_year(RP.lengths())
    years = np.array(list(RP.YEARS))
    fit = stats.linregress(years, per_year)
    before = per_year[years < RP.RECENT[0]].mean()
    after = per_year[years >= RP.RECENT[0]].mean()
    fig, ax = plt.subplots(figsize=(3.4, 2.15))
    ax.bar(years, per_year, color=GREY, width=0.75)
    for y, v in zip(years, per_year):
        ax.text(y, v + 15, f"{v:.0f}", ha="center", va="bottom", fontsize=5.4, color=INK_2)
    ax.plot(years, fit.intercept + fit.slope * years, color=INK, lw=0.8,
            label=f"Straight line, {fit.slope:.0f} m/yr per yr".replace("-", "\u2212"))
    ax.hlines(before, years[0] - 0.4, RP.RECENT[0] - 0.5, color=ORANGE, lw=1.6,
              label=f"Step model: {before:.0f}, then {after:.0f} m/yr")
    ax.hlines(after, RP.RECENT[0] - 0.5, years[-1] + 0.4, color=ORANGE, lw=1.6)
    ax.axhline(RP.PLAN_RATE, color=MUTED, lw=0.7, ls="--", label=f"Plan, {RP.PLAN_RATE:.0f} m/yr")
    ax.set_ylabel("Renewed walmuur [m]", fontsize=6.5)
    ax.set_xticks(years[::2])
    ax.tick_params(labelsize=6)
    ax.set_ylim(0, 1050)
    ax.legend(frameon=False, fontsize=5.8, loc="upper right", handlelength=1.6)
    fig.tight_layout(pad=0.2)
    save(fig, "fig_production_step.png")


def fault_tree_results():
    r = FT.main()
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.4, 2.6))
    for k, (common, colour, label) in enumerate(((False, BLUE, "independent causes"),
                                                 (True, RED, "with common cause"))):
        c = r["counts"][common]
        n = np.arange(0, 8)
        share = np.array([(c == i).mean() for i in n])
        ax.bar(n + (k - 0.5) * 0.38, share, width=0.38, color=colour,
               label=f"{label}: mean {c.mean():.2f}")
    ax.set_xlabel("Walls among the 17 where the programme fails before renewal")
    ax.set_ylabel("Probability")
    ax.legend(frameon=False, fontsize=6.3)
    cf = np.linspace(100, 6000, 300)
    styles = {"A0": (INK, "-"), "A4": (ORANGE, "-"), "A6": (GREEN, "-"), "A1": (MUTED, ":"),
              "A2": (MUTED, "--"), "A3": (MUTED, "-."), "A5": (GREY, "-")}
    for name, (c, p, d) in r["res"].items():
        key = name.split()[0]
        colour, ls = styles[key]
        bx.plot(cf / 1000, c + p * cf * d, color=colour, ls=ls, lw=1.0 if key in ("A0", "A4", "A6") else 0.7,
                label=name)
    bx.plot(cf / 1000, [r["a7"](x)[0] for x in cf], color=BLUE, lw=1.0, label="A7 Monitor, then decide")
    bx.axvline(r["C_F"] / 1000, color=MUTED, lw=0.6, ls="--")
    bx.text(r["C_F"] / 1000 + 0.05, 20, "base $C_f$", fontsize=6, color=MUTED)
    bx.set_xlabel("Failure cost $C_f$ [M EUR]")
    bx.set_ylabel("Expected cost E[C] [k EUR]")
    bx.set_ylim(0, 450)
    bx.legend(frameon=False, fontsize=5.6, ncol=2, loc="upper left")
    fig.tight_layout()
    save(fig, "app_fault_tree.png")


def werf_fit():
    import build_walmuur_height as BH
    pts = pd.read_csv(ROOT / "data" / "raw" / "AHN" / "walmuur_ahn_points.csv")
    h = pd.read_csv(PROCESSED / "walmuur_height.csv")
    rng = np.random.default_rng(1)
    resid, se = [], []
    for n in h.loc[h["werf"] == "yes", "Nummer"]:
        p = pts[(pts["Nummer"] == n) & pts["ground_nap"].notna()]
        g = p[p["side"] == BH.werf_side(pts, n)]["ground_nap"]
        g = g[g <= BH.NO_WERF_ABOVE].to_numpy()
        if len(g) < 3:
            continue
        resid += list(g - np.median(g))
        se.append(np.std([np.median(rng.choice(g, len(g))) for _ in range(2000)]))
    r, se = np.array(resid), np.array(se)
    robust = 1.4826 * np.median(np.abs(r))
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.4, 2.6))
    (osm, osr), _ = stats.probplot(r, dist="norm")
    ax.scatter(osm, osr, s=6, color=BLUE, lw=0)
    ax.plot(osm, robust * osm, color=INK, lw=0.8, label=f"normal, robust SD {robust:.3f} m")
    ax.set_xlabel("Normal quantile")
    ax.set_ylabel("AHN point minus werf median [m]")
    ax.legend(frameon=False, fontsize=6.3, loc="upper left")
    ks = stats.kstest(r / r.std(ddof=1), "norm").pvalue   # Kolmogorov-Smirnov against a normal
    ks_text = "< 0.001" if ks < 0.001 else f"= {ks:.3f}"
    ax.text(0.98, 0.04, f"{len(r)} points, {len(se)} walls\nSD {r.std(ddof=1):.3f} m; Kolmogorov-Smirnov p {ks_text}",
            transform=ax.transAxes, ha="right", fontsize=6.3, color=INK_2)
    bx.hist(se, bins=np.arange(0, se.max() + 0.02, 0.02), color=GREY)
    bx.axvline(0.05, color=RED, lw=1.0)
    bx.text(0.052, bx.get_ylim()[1] * 0.92, "model $\\sigma$ = 0.05 m", color=RED, fontsize=6.3)
    bx.set_xlabel("Bootstrap standard error of the werf median [m]")
    bx.set_ylabel("Walls")
    fig.tight_layout()
    save(fig, "app_werf_fit.png")
    print(f"werf fit: robust SD {robust:.3f}, SD {r.std(ddof=1):.3f}, SE of median: median {np.median(se):.3f},"
          f" share below 0.05 {np.mean(se <= 0.05):.2f}, max {se.max():.3f}")


def main() -> None:
    werf_fit()
    cross_sections()
    proven_strength()
    production_step()
    fault_tree_results()


if __name__ == "__main__":
    main()

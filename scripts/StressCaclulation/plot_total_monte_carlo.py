"""Scatter of the full Monte Carlo of the total load in TotalStress.

Every draw samples K, gamma_s, q, a and the groundwater depth d_w, and gives
S_total = S_soil + S_water + S_q. Each panel plots S_total against one of these
inputs, for the three soil types. A black-ringed dot marks S_total at the mean
inputs of each soil.

The share of variance in each panel title is one input at a time: the variance
of S_total with only that input random and the others at their mean, divided by
the full variance, as a range over the three soils. It shows which input
drives the spread.

The inputs (H, q, a, groundwater, canal level, draws) are set in TotalStress.py.

Run: python3 scripts/StressCaclulation/plot_total_monte_carlo.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import TotalStress as ts
from SoilForce import SOIL_TYPES

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures"

N_PLOT = 2_000     # draws per soil type shown, for legibility

LABELS = {"soft_clay_peat": "Soft clay / peat", "sand": "Sand", "mixed": "Mixed / layered"}
COLORS = {"soft_clay_peat": "#2a78d6", "sand": "#eb6834", "mixed": "#1baf7a"}
INK, MUTED = "#0b0b0b", "#52514e"

# (key in sample_inputs, short name, axis label)
INPUTS = [("K", "K", "Earth pressure coefficient K [-]"),
          ("gamma", "gamma_s", "Unit weight of soil gamma_s [kN/m3]"),
          ("q", "q", "Surcharge q [kPa]"),
          ("a", "a", "Distance wall to load a [m]"),
          ("d_w", "d_w", "Groundwater depth below ground d_w [m]")]
if not ts.WATER:
    INPUTS = INPUTS[:4]   # no groundwater to plot

d_c = ts.D_C if ts.WATER else np.inf


def S_total(x):
    """S_total for a dict of inputs (single values or arrays)."""
    return ts.total_stress(x["K"], x["gamma"], x["q"], x["a"], ts.H, x["d_w"], d_c)


rng = np.random.default_rng(ts.SEED)   # same draws as TotalStress.py
pick = np.random.default_rng(0)        # separate, so picking the plotted subset changes no draws

# plotted subset per soil, joined after the loop
x_parts: dict[str, list] = {key: [] for key, _, _ in INPUTS}
S_parts, c_parts = [], []
means, stats = {}, {}
shares: dict[str, list] = {key: [] for key, _, _ in INPUTS}
for soil_type, soil in SOIL_TYPES.items():
    x = ts.sample_inputs(soil_type, ts.N_MC, rng)
    S = S_total(x)
    x_mean = {"K": soil["K_mean"], "gamma": soil["gamma_mean"], "q": ts.Q_MEAN,
              "a": (ts.A_MIN + ts.A_MAX) / 2,
              "d_w": (ts.D_GHG + ts.D_GLG) / 2 if ts.WATER else np.inf}
    means[soil_type] = (x_mean, S_total(x_mean))
    # one input at a time random, the others at their mean
    for key, _, _ in INPUTS:
        shares[key].append(S_total({**x_mean, key: x[key]}).var() / S.var())
    stats[soil_type] = (S.mean(), np.percentile(S, 5), np.percentile(S, 95))

    idx = pick.choice(ts.N_MC, N_PLOT, replace=False)
    for key, _, _ in INPUTS:
        x_parts[key].append(x[key][idx])
    S_parts.append(S[idx])
    c_parts += [COLORS[soil_type]] * N_PLOT
    print(f"{LABELS[soil_type]:16s} S_total mean {stats[soil_type][0]:6.2f},"
          f" 5% {stats[soil_type][1]:6.2f}, 95% {stats[soil_type][2]:6.2f} kNm/m   variance share: "
          + "  ".join(f"{name} {shares[key][-1]:.1%}" for key, name, _ in INPUTS))

# Shuffle all soils together so no soil is painted on top just because it came last.
order = pick.permutation(len(c_parts))
x_p = {key: np.concatenate(v)[order] for key, v in x_parts.items()}
S_p = np.concatenate(S_parts)[order]
c_p = np.array(c_parts)[order]

fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), sharey=True)
axes = axes.flat
for ax, (key, name, label) in zip(axes, INPUTS):
    ax.scatter(x_p[key], S_p, s=8, c=c_p, alpha=0.35, lw=0)
    for soil_type in SOIL_TYPES:
        x_mean, S_mean = means[soil_type]
        ax.scatter(x_mean[key], S_mean, s=60, c=COLORS[soil_type], edgecolors=INK, lw=1.5, zorder=3)
    lo, hi = (f"{v:.0%}" if v >= 0.005 else "<1%" for v in (min(shares[key]), max(shares[key])))
    ax.set_title(f"{name}: {lo if lo == hi else f'{lo}-{hi}'} of variance", loc="left", fontsize=11)
    ax.set_xlabel(label)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2, lw=0.5)
    ax.tick_params(colors=MUTED)
for ax in (axes[0], axes[3]):
    ax.set_ylabel("Total load S_total [kNm/m]")
for ax in axes[len(INPUTS):]:
    ax.axis("off")

# legend and summary in the last, empty panel
info = axes[5]
handles = [plt.Line2D([], [], ls="", marker="o", ms=8, mfc=COLORS[s], mec=INK, label=LABELS[s])
           for s in SOIL_TYPES]
info.legend(handles=handles, frameon=False, loc="upper left", title="Dot = S_total at mean inputs",
            title_fontsize=9, alignment="left")
water = (f"groundwater {ts.D_GHG:g}-{ts.D_GLG:g} m below ground\ncanal {ts.D_C:g} m below ground"
         if ts.WATER else "no water")
summary = "\n".join(f"{LABELS[s]}: mean {m:.1f}, 5-95% {p5:.1f}-{p95:.1f}"
                    for s, (m, p5, p95) in stats.items())
info.text(0.0, 0.62, f"S_total [kNm/m], all {ts.N_MC:,} draws\n{summary}\n\n"
          f"H = {ts.H:g} m\n{water}", transform=info.transAxes, va="top", color=INK, fontsize=10,
          linespacing=1.5)

fig.suptitle(f"Full Monte Carlo: S_total = S_soil + S_water + S_q at H = {ts.H:g} m"
             f"  ({N_PLOT:,} of {ts.N_MC:,} draws per soil shown)", x=0.01, ha="left", fontsize=13)
fig.tight_layout()
FIGURES.mkdir(exist_ok=True)
fig.savefig(FIGURES / "total_monte_carlo_scatter.png", dpi=200, bbox_inches="tight")
plt.show()

"""Monte Carlo scatter of the surcharge load for the three soil types in SoilForce.

q is normal and a is uniform (sample_surcharge in TraficLoad). K is kept at the
mean of each soil type, so all spread comes from q and a.

Left panel: the sampled inputs, surcharge q against distance a.
Right panel: the resulting surcharge load S_q = 1/2 * K * q_eff * H^2 against a,
at a fixed retained height H. The line per soil is S_q at the mean q.

Run: python3 scripts/StressCaclulation/plot_surcharge_monte_carlo.py
"""

from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

from SoilForce import SOIL_TYPES
from TraficLoad import A_MAX, A_MIN, Q_MEAN, sample_surcharge, surcharge_moment

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures"

H = 1.22           # retained soil height, werf to canal bed [m]
N_MC = 100_000     # draws
N_PLOT = 2_000     # draws shown, for legibility

LABELS = {"soft_clay_peat": "Soft clay / peat", "sand": "Sand", "mixed": "Mixed / layered"}
COLORS = {"soft_clay_peat": "#2a78d6", "sand": "#eb6834", "mixed": "#1baf7a"}
INK, MUTED = "#0b0b0b", "#52514e"
HALO = [pe.withStroke(linewidth=4, foreground="white")]

rng = np.random.default_rng(1)

# One set of q and a draws for all soil types: they differ only in K.
q, a = sample_surcharge(N_MC, rng)
idx = rng.choice(N_MC, N_PLOT, replace=False)

# Shuffle the plotted subset of all soils together so no soil is painted on
# top of the others just because it was drawn last.
points = []
for soil_type, soil in SOIL_TYPES.items():
    S_q = surcharge_moment(soil["K_mean"], q, a, H)
    for a_i, s in zip(a[idx], S_q[idx]):
        points.append((a_i, s, COLORS[soil_type]))
    print(f"{LABELS[soil_type]:16s} S_q mean {S_q.mean():6.2f}, 5% {np.percentile(S_q, 5):6.2f},"
          f" 95% {np.percentile(S_q, 95):6.2f} kNm/m")
rng.shuffle(points)
a_p, S_p, c_p = zip(*points)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.scatter(a[idx], q[idx], s=8, c=MUTED, alpha=0.35, lw=0)
ax2.scatter(a_p, S_p, s=8, c=c_p, alpha=0.35, lw=0)

a_line = np.linspace(A_MIN, A_MAX, 200)
S_end = {}
for soil_type, soil in SOIL_TYPES.items():
    S_line = surcharge_moment(soil["K_mean"], Q_MEAN, a_line, H)
    ax2.plot(a_line, S_line, c=COLORS[soil_type], lw=2, label=LABELS[soil_type],
             path_effects=HALO)
    S_end[soil_type] = S_line[-1]

# direct label at the end of each line, pushed apart where the lines end close together
y_min, y_max = ax2.get_ylim()
gap = 0.04 * (y_max - y_min)
y_label = -np.inf
for soil_type, y_end in sorted(S_end.items(), key=lambda item: item[1]):
    y_label = max(y_end, y_label + gap)
    ax2.annotate(LABELS[soil_type], (a_line[-1], y_label), xytext=(6, 0),
                 textcoords="offset points", va="center", color=INK, fontsize=10)

ax1.axhline(Q_MEAN, c=INK, lw=1, ls="--")
ax1.annotate(f"mean q = {Q_MEAN:g} kPa", (A_MAX, Q_MEAN), xytext=(-4, 4),
             textcoords="offset points", ha="right", va="bottom", color=INK, fontsize=10,
             path_effects=HALO)
ax1.set_xlabel("Distance between wall and load a [m]")
ax1.set_ylabel("Surcharge q [kPa]")
ax1.set_title(f"Sampled inputs ({N_PLOT:,} of {N_MC:,} draws)", loc="left")

ax2.set_xlabel("Distance between wall and load a [m]")
ax2.set_ylabel("Surcharge load S_q [kNm/m]")
ax2.set_title(f"Surcharge load S_q = 1/2 K q_eff H^2 at H = {H:g} m", loc="left")
ax2.legend(frameon=False, loc="upper right", title="Line = mean q", title_fontsize=9)

for ax in (ax1, ax2):
    ax.set_xlim(A_MIN, A_MAX)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2, lw=0.5)
    ax.tick_params(colors=MUTED)

fig.tight_layout()
FIGURES.mkdir(exist_ok=True)
fig.savefig(FIGURES / "surcharge_monte_carlo_scatter.png", dpi=200, bbox_inches="tight")
plt.show()

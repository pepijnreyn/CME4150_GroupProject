"""Monte Carlo scatter of the soil load for the three soil types in SoilForce.

Left panel: the sampled inputs, K (lognormal) against gamma_s (normal).
Right panel: the resulting soil load S = 1/6 * K * gamma_s * H^3 against K,
at a fixed retained height H. A black-ringed dot marks each soil's mean.

Run: python3 scripts/StressCaclulation/plot_soil_monte_carlo.py
"""

from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np

from SoilForce import SOIL_TYPES, sample_soil, soil_stress

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures"

H = 3.0            # retained soil height [m]
N_MC = 100_000     # draws per soil type
N_PLOT = 2_000     # draws per soil type shown, for legibility

LABELS = {"soft_clay_peat": "Soft clay / peat", "sand": "Sand", "mixed": "Mixed / layered"}
COLORS = {"soft_clay_peat": "#2a78d6", "sand": "#eb6834", "mixed": "#1baf7a"}
INK, MUTED = "#0b0b0b", "#52514e"

rng = np.random.default_rng(1)

# Draw every soil type, then shuffle the plotted subset together so no soil
# is painted on top of the others just because it was drawn last.
points = []
for soil_type in SOIL_TYPES:
    K, gamma = sample_soil(soil_type, N_MC, rng)
    S = soil_stress(K, gamma, H)
    idx = rng.choice(N_MC, N_PLOT, replace=False)
    for k, g, s in zip(K[idx], gamma[idx], S[idx]):
        points.append((k, g, s, COLORS[soil_type]))
    print(f"{LABELS[soil_type]:16s} S mean {S.mean():6.2f}, 5% {np.percentile(S, 5):6.2f},"
          f" 95% {np.percentile(S, 95):6.2f} kNm/m")
rng.shuffle(points)
K_p, g_p, S_p, c_p = zip(*points)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.scatter(K_p, g_p, s=8, c=c_p, alpha=0.35, lw=0)
ax2.scatter(K_p, S_p, s=8, c=c_p, alpha=0.35, lw=0)

for soil_type, soil in SOIL_TYPES.items():
    K_m, g_m = soil["K_mean"], soil["gamma_mean"]
    S_m = soil_stress(K_m, g_m, H)
    for ax, y in ((ax1, g_m), (ax2, S_m)):
        ax.scatter(K_m, y, s=60, c=COLORS[soil_type], edgecolors=INK, lw=1.5, zorder=3,
                   label=LABELS[soil_type] if ax is ax2 else None)
    # direct label next to each mean dot, with a white halo over the cloud
    ax1.annotate(LABELS[soil_type], (K_m, g_m), xytext=(9, 0), textcoords="offset points",
                 va="center", color=INK, fontsize=10, zorder=4,
                 path_effects=[pe.withStroke(linewidth=3, foreground="white")])

ax1.set_xlabel("Earth pressure coefficient K [-]")
ax1.set_ylabel("Unit weight of soil gamma_s [kN/m3]")
ax1.set_title(f"Sampled inputs ({N_PLOT:,} of {N_MC:,} draws per soil)", loc="left")

ax2.set_xlabel("Earth pressure coefficient K [-]")
ax2.set_ylabel("Soil load S [kNm/m]")
ax2.set_title(f"Soil load S = 1/6 K gamma_s H^3 at H = {H:g} m", loc="left")
ax2.legend(frameon=False, loc="upper left", title="Dot = mean value", title_fontsize=9)

for ax in (ax1, ax2):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.2, lw=0.5)
    ax.tick_params(colors=MUTED)

fig.tight_layout()
FIGURES.mkdir(exist_ok=True)
fig.savefig(FIGURES / "soil_monte_carlo_scatter.png", dpi=200, bbox_inches="tight")
plt.show()

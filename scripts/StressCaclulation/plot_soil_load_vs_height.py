"""Mean soil load S against retained height H for the three soil types.

S = 1/6 * K * gamma_s * H^3, with the mean K and gamma_s from SOIL_TYPES.
K and gamma_s are sampled independently, so this is also the mean of the
Monte Carlo S.

Run: python3 scripts/StressCaclulation/plot_soil_load_vs_height.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from SoilForce import SOIL_TYPES, soil_stress_mean

ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "figures"

H_MAX = 5.0        # highest retained height shown [m]

LABELS = {"soft_clay_peat": "Soft clay / peat", "sand": "Sand", "mixed": "Mixed / layered"}
COLORS = {"soft_clay_peat": "#2a78d6", "sand": "#eb6834", "mixed": "#1baf7a"}
INK, MUTED = "#0b0b0b", "#52514e"

H = np.linspace(0, H_MAX, 200)

fig, ax = plt.subplots(figsize=(8, 5))
for soil_type in SOIL_TYPES:
    S = soil_stress_mean(soil_type, H)
    ax.plot(H, S, c=COLORS[soil_type], lw=2, label=LABELS[soil_type])
    # direct label at the end of each line, with its value
    ax.annotate(f"{LABELS[soil_type]}  {S[-1]:.0f}", (H[-1], S[-1]), xytext=(6, 0),
                textcoords="offset points", va="center", color=INK, fontsize=10)

ax.set_xlim(0, H_MAX)
ax.set_ylim(0, None)
ax.set_xlabel("Retained soil height H [m]")
ax.set_ylabel("Mean soil load S [kNm/m]")
ax.set_title("Mean soil load S = 1/6 K gamma_s H^3 per soil type", loc="left")
ax.legend(frameon=False, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.2, lw=0.5)
ax.tick_params(colors=MUTED)

fig.tight_layout()
FIGURES.mkdir(exist_ok=True)
fig.savefig(FIGURES / "soil_load_vs_height.png", dpi=200, bbox_inches="tight")
plt.show()

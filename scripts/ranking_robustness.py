"""Robustness of the ranking and of the risk classes (report sections 1.3 and 2.1).

The failure model is used only to rank the walls (report section 2.1.3), so the
test of its validity that matters is whether the ranking survives the changes
that Appendix B tests. For each variant the script gives the Spearman rank
correlation of beta (best estimate, updated, 2026) with the base run of the
same script, the number of walls whose risk class changes and the number of
the base red walls that stay red. In a variant every wall changes, so the
classes are relative to the median Pf of that variant, as the method would set
them.

For the one-at-a-time sensitivity (Table 1.3) it counts, per input, the walls
whose risk class changes when that input is fixed at its 5th or its 95th
percentile (walmuur_tornado.csv). Here an input stands for a measurement on one
wall, which does not move the other walls, so the class thresholds stay at the
median Pf of the base run.

Inputs: walmuur_sensitivity.csv (Table B.3), walmuur_model_checks.csv
(Table B.6), walmuur_failure_probability.csv (2041), walmuur_tornado.csv and
walmuur_consequence.csv. Classes as in plot_results_map.py.
Run: python3 scripts/ranking_robustness.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, spearmanr

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
P_FACTOR = 1.5
CLASS_SCORE = {"low": 1, "medium": 2, "high": 3}

VARIANTS = {  # label: (file, column), compared with beta_base of the same file
    "rho(K, gamma) = -0.5": ("walmuur_sensitivity.csv", "beta_kgamma"),
    "rho(MOR, E) = +0.8": ("walmuur_sensitivity.csv", "beta_more"),
    "Groundwater +0.6 to +1.0 m NAP": ("walmuur_sensitivity.csv", "beta_groundwater"),
    "Groundwater up to the werf": ("walmuur_sensitivity.csv", "beta_groundwater_werf"),
    "Soil class uncertain": ("walmuur_sensitivity.csv", "beta_soil_mixed"),
    "Survived service load": ("walmuur_model_checks.csv", "beta_service_load"),
    "No update of the type": ("walmuur_model_checks.csv", "beta_prior_type"),
    "No screen": ("walmuur_model_checks.csv", "beta_screen_failed"),
    "No wall friction": ("walmuur_model_checks.csv", "beta_no_friction"),
    "Restricted use": ("walmuur_model_checks.csv", "beta_restrict_use"),
    "Type 1 recalibrated": ("walmuur_model_checks.csv", "beta_calibrated"),
}
TORNADO_INPUTS = ["K", "a", "shell", "D0", "theta_R", "groundwater", "dz", "q", "werf", "s", "MOR",
                  "theta_M", "gamma_m", "gamma_s", "gamma_c", "E", "k", "rate"]


def risk_class(pf: pd.Series, consequence: pd.Series, med: float | None = None) -> pd.Series:
    """Red, orange or green from the relative probability class and the consequence class."""
    med = pf.median() if med is None else med
    p_class = np.where(pf > P_FACTOR * med, 3, np.where(pf < med / P_FACTOR, 1, 2))
    score = p_class + consequence.loc[pf.index].map(CLASS_SCORE).to_numpy()
    return pd.Series(np.where(score >= 5, "red", np.where(score == 4, "orange", "green")), index=pf.index)


def pf(beta: pd.Series) -> pd.Series:
    return pd.Series(norm.cdf(-beta.to_numpy()), index=beta.index)


def main() -> None:
    cons = pd.read_csv(PROCESSED / "walmuur_consequence.csv").set_index("Nummer")["consequence_class"]
    rows, red = [], {}
    for label, (file, col) in VARIANTS.items():
        d = pd.read_csv(PROCESSED / file).set_index("Nummer")
        if col not in d:
            print(f"{label}: column {col} not in {file}, skipped")
            continue
        base, var = d["beta_base"], d[col]
        c0, c1 = risk_class(pf(base), cons), risk_class(pf(var), cons)
        red[label] = c1 == "red"
        rows.append({"variant": label, "spearman": spearmanr(base, var)[0],
                     "class_changes": int((c0 != c1).sum()),
                     "red_stay_red": f"{int(((c0 == 'red') & (c1 == 'red')).sum())}/{int((c0 == 'red').sum())}",
                     "dbeta_min": (var - base).min(), "dbeta_max": (var - base).max()})
    r = pd.read_csv(PROCESSED / "walmuur_failure_probability.csv")
    r = r[r["type"] == "unknown"].pivot(index="Nummer", columns="year", values="beta_updated")
    c0, c1 = risk_class(pf(r[2026]), cons), risk_class(pf(r[2041]), cons)
    rows.append({"variant": "2041 instead of 2026", "spearman": spearmanr(r[2026], r[2041])[0],
                 "class_changes": int((c0 != c1).sum()),
                 "red_stay_red": f"{int(((c0 == 'red') & (c1 == 'red')).sum())}/{int((c0 == 'red').sum())}",
                 "dbeta_min": (r[2041] - r[2026]).min(), "dbeta_max": (r[2041] - r[2026]).max()})
    rob = pd.DataFrame(rows)
    print("Ranking against the base run (beta best estimate, 2026):")
    print(rob.round(3).to_string(index=False))
    print(f"Spearman: median {rob['spearman'].median():.2f}, lowest {rob['spearman'].min():.2f}"
          f" ({rob.loc[rob['spearman'].idxmin(), 'variant']})")
    rob.round(3).to_csv(PROCESSED / "walmuur_ranking_robustness.csv", index=False)
    red = pd.DataFrame(red)
    published = pd.read_csv(PROCESSED / "walmuur_risk_class.csv").set_index("Nummer")
    times = red.sum(axis=1).reindex(published.index)
    print(f"\nRed in how many of the {red.shape[1]} variants (base class in brackets):")
    for n, k in times.items():
        print(f"  {published.loc[n, 'Naam']:40s} {k:2d}  ({published.loc[n, 'risk_class']})")
    always = times.index[times == red.shape[1]]
    print(f"red in every variant: {', '.join(published.loc[always, 'Naam'])}"
          f" ({published.loc[always, 'length_m'].sum():.0f} m)")

    # Calibrated type 1: how much the type-1 model and the type update change
    m = pd.read_csv(PROCESSED / "walmuur_model_checks.csv").set_index("Nummer")
    if "beta_calibrated" in m:
        print("\nType 1 recalibrated: P(stands | type 1) "
              f"{m['p_stands_base_type1'].min():.2f}-{m['p_stands_base_type1'].max():.2f} ->"
              f" {m['p_stands_calibrated_type1'].min():.2f}-{m['p_stands_calibrated_type1'].max():.2f};"
              f" beta type 1 {m['beta_base_type1'].min():.2f}..{m['beta_base_type1'].max():.2f} ->"
              f" {m['beta_calibrated_type1'].min():.2f}..{m['beta_calibrated_type1'].max():.2f}"
              f" (change {(m['beta_calibrated_type1'] - m['beta_base_type1']).min():+.2f} to"
              f" {(m['beta_calibrated_type1'] - m['beta_base_type1']).max():+.2f});"
              f" P(type 2 | E) {m['p_type2_base'].min():.2f}-{m['p_type2_base'].max():.2f} ->"
              f" {m['p_type2_calibrated'].min():.2f}-{m['p_type2_calibrated'].max():.2f};"
              f" best estimate change {(m['beta_calibrated'] - m['beta_base']).min():+.2f} to"
              f" {(m['beta_calibrated'] - m['beta_base']).max():+.2f}")
        gap = m["beta_calibrated_type2"] - m["beta_calibrated_type1"]
        print(f"  gap type 2 - type 1: base median {(m['beta_base_type2'] - m['beta_base_type1']).median():.2f},"
              f" recalibrated median {gap.median():.2f} ({gap.min():.2f}-{gap.max():.2f})")
        c0, c1 = risk_class(pf(m["beta_base"]), cons), risk_class(pf(m["beta_calibrated"]), cons)
        for n in m.index[c0 != c1]:
            print(f"  class change {m.loc[n, 'Naam']}: {c0[n]} -> {c1[n]}")

    # One-at-a-time: walls whose risk class changes when one input is fixed (Table 1.3)
    t = pd.read_csv(PROCESSED / "walmuur_tornado.csv")
    base = t[t["input"] == "base"].set_index("Nummer")
    med = pf(base["beta_2026"]).median()
    c0 = risk_class(pf(base["beta_2026"]), cons, med)
    published = pd.read_csv(PROCESSED / "walmuur_risk_class.csv").set_index("Nummer")["risk_class"]
    print(f"\nOne-at-a-time, thresholds at the base median Pf {med:.3f}; base classes equal the"
          f" published ones for {(c0 == published.loc[c0.index]).sum()} of {len(c0)} walls")
    changes = {}
    for label, levels in [("wall type", None), ("soil class", ["soft_clay_peat", "sand", "mixed"])] + \
                         [(i, ["low", "high"]) for i in TORNADO_INPUTS]:
        moved = pd.Series(False, index=c0.index)
        if label == "wall type":
            for col in ("beta_type1_2026", "beta_type2_2026"):
                moved |= risk_class(pf(base[col]), cons, med) != c0
        else:
            inp = "soil_class" if label == "soil class" else label
            for lev in levels:
                v = t[(t["input"] == inp) & (t["level"] == lev)].set_index("Nummer")["beta_2026"]
                moved |= risk_class(pf(v), cons, med) != c0.loc[v.index]
        if label == "werf":  # Table 1.3 splits the werf level into assumed and measured
            res = pd.read_csv(PROCESSED / "walmuur_failure_probability.csv")
            assumed = set(res.loc[res["werf_assumed"].eq(True), "Nummer"])
            changes["werf assumed"] = int(moved[moved.index.isin(assumed)].sum())
            changes["werf measured"] = int(moved[~moved.index.isin(assumed)].sum())
            continue
        changes[label] = int(moved.sum())
    print("walls whose class changes at either end: " + ", ".join(f"{k} {v}" for k, v in changes.items()))
    pd.Series(changes, name="walls_class_change").to_csv(PROCESSED / "walmuur_tornado_class_changes.csv")


if __name__ == "__main__":
    main()

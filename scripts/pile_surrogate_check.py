"""Reproduce the pile surrogate written in the supplied manuscript.

ASSUMPTIONS for the ambiguous distribution table:
* Normal distributions are specified by arithmetic mean and CoV.
* Lognormal theta factors are specified by arithmetic mean 1 and CoV.
* Every input is independent, as stated in the manuscript.
* The q distribution is used exactly as written; no time-process is added.
This evaluates the stated surrogate, not the published Hemel pile model.
Requires numpy. Run: python pile_surrogate_check.py
"""
from pathlib import Path
from statistics import NormalDist
import json
import math
import numpy as np


def lognormal_mean_cov(rng, mean, cov, size):
    sigma_log = math.sqrt(math.log1p(cov**2))
    mu_log = math.log(mean) - sigma_log**2 / 2
    return rng.lognormal(mu_log, sigma_log, size)


def wilson(k, n):
    z = NormalDist().inv_cdf(0.975)
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return [c - h, c + h]


def main():
    rng = np.random.default_rng(1)
    n_total = 2_000_000
    batch_size = 100_000
    counts = {"time_0_random_q": 0, "time_15_random_q": 0,
              "time_15_fixed_q_7": 0}
    invalid = {"nonpositive_diameter": 0, "nonpositive_strength": 0,
               "negative_q": 0}
    checkpoints = []
    for start in range(0, n_total, batch_size):
        D0 = rng.normal(245, 245 * 0.10, batch_size)
        MOR = rng.normal(22, 22 * 0.10, batch_size)
        q = rng.normal(7, 7 * 0.20, batch_size)
        theta_M = lognormal_mean_cov(rng, 1, 0.10, batch_size)
        theta_N = lognormal_mean_cov(rng, 1, 0.05, batch_size)
        theta_S = lognormal_mean_cov(rng, 1, 0.20, batch_size)
        D15 = D0 - 0.34 * 15
        invalid["nonpositive_diameter"] += int((D15 <= 0).sum())
        invalid["nonpositive_strength"] += int((MOR <= 0).sum())
        invalid["negative_q"] += int((q < 0).sum())
        for name, D, load in (("time_0_random_q", D0, q),
                               ("time_15_random_q", D15, q),
                               ("time_15_fixed_q_7", D15, 7.0)):
            # Convert 20 kN to 20,000 N for N/mm^2 stresses and mm diameters.
            bending = theta_M * theta_S * (3.0 + 0.10 * load) * (240 / D)**4
            axial = theta_N * 4 * 20_000 / (np.pi * D**2)
            failed = (D <= 0) | (MOR < bending + axial)
            counts[name] += int(failed.sum())
        if start + batch_size in (100_000, 1_000_000, n_total):
            checkpoints.append({"n": start + batch_size,
                                "failure_probability_time_15": counts["time_15_random_q"] / (start + batch_size)})

    results = {}
    for name, k in counts.items():
        p = k / n_total
        results[name] = {"failure_count": k, "failure_probability": p,
                         "beta": -NormalDist().inv_cdf(p) if 0 < p < 1 else None,
                         "monte_carlo_95pct_wilson_interval": wilson(k, n_total)}
    D_c = 245 - 0.34 * 15
    central_bending = (3.0 + 0.1 * 7) * (240 / D_c)**4
    central_axial = 4 * 20_000 / (math.pi * D_c**2)
    assert math.isclose(D_c, 239.9)
    # Rounded hand checks catch a kN/N unit error and a diameter-unit error.
    assert 0.44 < central_axial < 0.45
    assert 4.14 < central_bending + central_axial < 4.16
    report = {
        "n": n_total, "seed": 1,
        "distribution_convention": "Normal(mean, CoV); Lognormal(arithmetic mean, CoV). Inputs independent.",
        "central_case": {"diameter_mm": D_c, "bending_stress_MPa": central_bending,
                         "axial_stress_MPa": central_axial,
                         "total_stress_MPa": central_bending + central_axial,
                         "MOR_MPa": 22.0},
        "claimed_beta_benchmark": 1.5,
        "failure_probability_corresponding_to_beta_1_5": NormalDist().cdf(-1.5),
        "results": results, "checkpoints": checkpoints,
        "unphysical_draw_counts": invalid,
        "caveat": "This checks an interpretation of the manuscript's surrogate and table, not its author's unseen implementation. Evaluating diameter at 15 years does not itself establish a 15-year failure probability.",
    }
    target = Path(__file__).resolve().with_name("pile_surrogate_results.json")
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

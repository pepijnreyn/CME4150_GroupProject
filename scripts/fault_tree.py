"""Fault tree (report section 3.1) and decision tree (section 3.2) for the walmuren.

Rebuilt from the report: basic events and ranges of Table 3.1, alternatives of
Table 3.2. The tree, for one wall over the 15-year reference period:

  top            = load OR (M AND not_repaired)
  load           = W2 OR Q1 OR Q2 OR Q3 OR E1 OR E2 OR E3 OR E4
  not_repaired   = not_recognised OR I3 OR repair_late
  not_recognised = (S1 OR S2 OR S3) AND (I1 OR I2)
  repair_late    = L1 OR L2 OR L3 OR L4

M is the failure probability of the model, Phi(-beta) with beta from
walmuur_sensitivity.csv (base column, 2026). The median wall gives M; the
range of M is the spread of its sensitivity columns. For the 17 walls
together, a Monte Carlo links the M events of the walls with a Gaussian
copula (RHO_WALLS, an assumption) and draws S3 and I1 once for all walls and
half of I2 once for all walls.

Decision: E[C] = c + P_f C_f; CE = c + R ln(1 - P_f + P_f exp(C_f / R));
pessimistic: every event at its upper bound, and a measure lowers an event by
the same factor as in the base case.

Run: python3 scripts/fault_tree.py          (current beta values)
     python3 scripts/fault_tree.py --check  (beta values of the old report table)
"""

import csv
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
SENS = ROOT / "data" / "processed" / "walmuur_sensitivity.csv"

# ---- Inputs ----------------------------------------------------------------
# L1: share of the modelled walls not renewed by 2041, at the recent pace and at the lower
# 95% bound of that pace (scripts/regression_production_rate.py). The earlier report
# derived 0.20 (0-0.37) from a backlog of 1.88 km; --check uses that.
L1 = (0.0, 0.0, 0.45) if "--check" not in sys.argv else (0.20, 0.0, 0.37)
EVENTS = {  # id: (base, low, high), Table 3.1 without M
    "W2": (0.001, 0.0002, 0.005), "Q1": (0.005, 0.001, 0.02), "Q2": (0.001, 0.0002, 0.005),
    "Q3": (0.001, 0.0002, 0.005), "E1": (0.001, 0.0002, 0.005), "E2": (0.005, 0.001, 0.02),
    "E3": (0.05, 0.02, 0.15), "E4": (0.001, 0.0002, 0.005), "S1": (0.10, 0.05, 0.20),
    "S2": (0.0, 0.0, 0.0), "S3": (0.10, 0.05, 0.20), "I1": (0.30, 0.10, 0.73),
    "I2": (0.16, 0.12, 0.28), "I3": (0.03, 0.008, 0.11), "L1": L1,
    "L2": (0.10, 0.05, 0.20), "L3": (0.10, 0.05, 0.20), "L4": (0.10, 0.05, 0.20),
}
ALTERNATIVES = {  # name: (cost [k EUR], changed events)
    "A0 Current programme": (0, {}),
    "A1 Scour/load control": (120, {"E3": 0.02, "Q1": 0.001, "E2": 0.001}),
    "A2 Inspection": (70, {"I1": 0.10, "I2": 0.12, "I3": 0.008, "S3": 0.05}),
    "A3 Organisation": (100, {"L1": 0.05 if "--check" in sys.argv else 0.0,
                               "L2": 0.05, "L3": 0.05, "L4": 0.05}),
    "A4 Strengthen now": (1300, {"M": 0.01, "E3": 0.02, "W2": 0.0002}),
}
ALTERNATIVES["A5 Package"] = (290, {**ALTERNATIVES["A1 Scour/load control"][1],
                                    **ALTERNATIVES["A2 Inspection"][1],
                                    **ALTERNATIVES["A3 Organisation"][1]})
C_F = 1500.0            # failure cost [k EUR]
R = 500.0               # risk tolerance [k EUR]
RHO_WALLS = 0.084       # copula correlation between the M events of the walls (assumption)
COMMON = {"S3": 1.0, "I1": 1.0, "I2": 0.5}   # share of the probability drawn once for all walls
N_MC = 400_000
SEED = 1
OLD_BETA = [0.13, 0.81, 0.81, 1.18, 0.82, 1.38, 1.08, 1.05, 1.13, 0.79, 1.52, 1.38,
            0.59, 0.59, 0.59, 0.56, 0.72]   # base column of the earlier report table
# ----------------------------------------------------------------------------
LOAD = ["W2", "Q1", "Q2", "Q3", "E1", "E2", "E3", "E4"]


def p_or(*ps):
    return 1 - np.prod([1 - p for p in ps], axis=0)


def tree(p):
    """Top event and the two main branches for a dict of event probabilities."""
    load = p_or(*(p[e] for e in LOAD))
    not_recognised = p_or(p["S1"], p["S2"], p["S3"]) * p_or(p["I1"], p["I2"])
    not_repaired = p_or(not_recognised, p["I3"], p_or(p["L1"], p["L2"], p["L3"], p["L4"]))
    return p_or(load, p["M"] * not_repaired), load, not_repaired


def betas(check):
    if check:
        return np.array(OLD_BETA), None
    rows = list(csv.DictReader(SENS.open()))
    base = np.array([float(r["beta_base"]) for r in rows])
    i = np.argsort(base)[len(base) // 2]
    cols = ["beta_base", "beta_kgamma", "beta_more", "beta_groundwater", "beta_soil_mixed"]
    return base, (rows[i]["Naam"], [norm.cdf(-float(rows[i][c])) for c in cols])


def monte_carlo(p, m_walls, common, rng):
    """Mean, SD and P(N >= 5) of the number of failing walls among the walls."""
    n = len(m_walls)
    z = (np.sqrt(RHO_WALLS) * rng.standard_normal((N_MC, 1))
         + np.sqrt(1 - RHO_WALLS) * rng.standard_normal((N_MC, n)))
    occurs = {"M": z < norm.ppf(m_walls)}
    for e, (base, _, _) in EVENTS.items():
        pe = p[e]
        share = COMMON.get(e, 0.0) if common else 0.0
        shared = rng.random((N_MC, 1)) < share * pe
        own = rng.random((N_MC, n)) < (pe - share * pe) / (1 - share * pe)
        occurs[e] = shared | own
    o = occurs
    load = np.logical_or.reduce([o[e] for e in LOAD])
    not_recognised = (o["S1"] | o["S2"] | o["S3"]) & (o["I1"] | o["I2"])
    not_repaired = not_recognised | o["I3"] | o["L1"] | o["L2"] | o["L3"] | o["L4"]
    count = (load | (o["M"] & not_repaired)).sum(axis=1)
    return count.mean(), count.std(), (count >= 5).mean()


def main() -> None:
    check = "--check" in sys.argv
    beta_walls, median = betas(check)
    m_walls = norm.cdf(-beta_walls)
    m = norm.cdf(-np.median(beta_walls))
    base = {e: v[0] for e, v in EVENTS.items()} | {"M": m}
    top, load, not_repaired = tree(base)
    print(f"M (median wall) {m:.3f}" + (f", {median[0]}, range {min(median[1]):.3f}-{max(median[1]):.3f}"
                                        if median else ""))
    print(f"load {load:.3f}, not repaired in time {not_repaired:.3f}, top {top:.3f},"
          f" without repair {tree(base | {'L1': 1.0})[0]:.3f}")
    low = {e: v[1] for e, v in EVENTS.items()} | {"M": min(median[1]) if median else 0.20}
    high = {e: v[2] for e, v in EVENTS.items()} | {"M": max(median[1]) if median else 0.28}
    print(f"all low {tree(low)[0]:.3f}, all high {tree(high)[0]:.3f}")
    per_wall = np.array([tree(base | {"M": mi})[0] for mi in m_walls])
    print(f"per wall {per_wall.min():.3f}-{per_wall.max():.3f}, sum over walls {per_wall.sum():.2f},"
          f" per year {per_wall.sum() / 15:.2f}")
    print("Fussell-Vesely: " + ", ".join(
        f"{e} {1 - tree(base | {e: 0.0})[0] / top:.2f}" for e in ["M"] + list(EVENTS) if base[e] > 0))
    swings = {e: tree(base | {e: high[e]})[0] - tree(base | {e: low[e]})[0] for e in ["M"] + list(EVENTS)}
    print("swing low->high: " + ", ".join(f"{e} {s:.3f}" for e, s in
                                          sorted(swings.items(), key=lambda x: -x[1])[:6]))
    rng = np.random.default_rng(SEED)
    for common in (False, True):
        mean, sd, p5 = monte_carlo(base, m_walls, common, rng)
        print(f"17 walls, common cause {common}: mean {mean:.2f}, SD {sd:.2f}, P(N>=5) {p5:.3f}")

    print(f"\n{'alternative':24s} {'Pf':>5s} {'load':>5s} {'notrep':>6s} {'E[C]':>6s} {'CE':>6s} {'pess':>6s} {'N17':>5s}")
    res = {}
    for name, (cost, change) in ALTERNATIVES.items():
        p = base | change
        pf, ld, nr = tree(p)
        pess = high | {e: high.get(e, 0) * (v / base[e]) if base[e] > 0 else v for e, v in change.items()}
        if "M" in change:
            pess["M"] = change["M"]
        pf_pess = tree(pess)[0]
        n17 = sum(tree(base | {"M": mi} | change)[0] for mi in m_walls)
        ce = cost + R * np.log(1 - pf + pf * np.exp(C_F / R))
        res[name] = (cost, pf)
        print(f"{name:24s} {pf:5.3f} {ld:5.3f} {nr:6.3f} {cost + pf * C_F:6.0f} {ce:6.0f}"
              f" {cost + pf_pess * C_F:6.0f} {n17:5.2f}")
    c0, p0 = res["A0 Current programme"]
    for name in ("A3 Organisation", "A5 Package", "A4 Strengthen now"):
        c, p = res[name]
        print(f"break-even C_f for {name} against A0: {(c - c0) / (p0 - p) / 1000:.1f} M EUR")
    best, switches = None, []
    for cf in np.arange(100, 30_001, 50):
        name = min(res, key=lambda k: res[k][0] + res[k][1] * cf)
        if name != best:
            switches.append(f"{name.split()[0]} from {cf / 1000:.2f} M")
            best = name
    print("cheapest alternative as C_f rises: " + ", ".join(switches))
    print("Pf: " + ", ".join(f"{k.split()[0]} {v[1]:.4f}" for k, v in res.items()))
    c3, p3 = res["A3 Organisation"]
    c5, p5_ = res["A5 Package"]
    print(f"break-even C_f A5 against A3: {(c5 - c3) / (p3 - p5_) / 1000:.1f} M EUR")
    c4, p4 = res["A4 Strengthen now"]
    print(f"break-even C_f A4 against A5: {(c4 - c5) / (p5_ - p4) / 1000:.1f} M EUR;"
          f" NEN 8700 target Phi(-1.8) = {norm.cdf(-1.8):.3f}")


if __name__ == "__main__":
    main()

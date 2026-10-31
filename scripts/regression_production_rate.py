"""Production rate of the walmuur programme and the risk carried until renewal.

Report section 4.1. Uses the renewal year of every renewed walmuur
(walmuur_foundation.csv) and its length in the asset register.

1. Trend: least-squares line through the renewed length per year, 2015-2026
   (a year without a renewal counts as 0 m), with a 95% interval for the slope
   and a t-test of H0: no trend.
2. Recent pace: mean renewed length per year since 2019, with a 95% t-interval,
   and a t-test against the 100 m/yr of the programme plan.
3. Backlog: the 17 modelled walls (walmuur_failure_probability.csv) are renewed
   one after the other from 2027. The yearly production is drawn from the years
   2019-2026 (bootstrap), or fixed at 100 m/yr, or drawn from 2015-2018. Each
   draw gives the year in which each wall is renewed.
4. Risk until renewal: a wall carries the hazard h(t) = -ln(1 - Pf(t)) / 15
   until it is renewed, with Pf(t) its best-estimate updated Pf over the 15-year
   reference period, linear between 2026 and 2041 and extended linearly after
   2041 (at most 0.95). The expected number of walls that reach a limit state
   before renewal is the sum over the walls of 1 - exp(-sum of h over the years
   it waits). Two orders: lowest beta first, and a random order.

Writes data/processed/production_rate_risk.csv.
Run: python3 scripts/regression_production_rate.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "data" / "processed" / "walmuur_foundation.csv"
RESULTS = ROOT / "data" / "processed" / "walmuur_failure_probability.csv"
AREAAL = ROOT / "data" / "raw" / "Output areaal GU TU Delft 26-08.json"
OUT = ROOT / "data" / "processed" / "production_rate_risk.csv"

# ---- Inputs ----------------------------------------------------------------
YEARS = range(2015, 2027)       # years of the trend fit; 2015 is the first renewal
RECENT = range(2019, 2027)      # the recent pace, after the fast years 2016-2018
FAST = range(2015, 2019)
PLAN_RATE = 100.0               # [m/yr], pace of the programme plan
START = 2027                    # first year of future production
HORIZON = 2100                  # last year simulated
REFERENCE = 15                  # NEN 8700 reference period [yr]
PF_MAX = 0.95
N_BOOT = 20_000
SEED = 1
# ----------------------------------------------------------------------------


def lengths():
    features = json.loads(AREAAL.read_text())["features"]
    return {f["properties"]["Nummer"]: float(str(f["properties"]["Lengte"]).replace(",", "."))
            for f in features if f.get("properties") and f["properties"].get("Lengte") not in (None, "")}


def renewed_per_year(length):
    per_year = defaultdict(float)
    for r in csv.DictReader(FOUNDATION.open()):
        if r["status"] == "renewed" and r["year"]:
            per_year[int(float(r["year"]))] += length[r["Nummer"]]
    return np.array([per_year.get(y, 0.0) for y in YEARS])


def modelled_walls():
    """Length and best-estimate updated Pf in 2026 and 2041 of the 17 modelled walls."""
    walls = defaultdict(dict)
    for r in csv.DictReader(RESULTS.open()):
        if r["type"] == "unknown":
            walls[r["Nummer"]]["length"] = float(r["length_m"])
            walls[r["Nummer"]][int(r["year"])] = float(r["pf_updated"])
            walls[r["Nummer"]]["name"] = r["Naam"]
    return list(walls.values())


def cumulative_hazard(walls):
    """Sum of h(t) from 2026 up to and including each year to HORIZON, per wall."""
    years = np.arange(2026, HORIZON + 1)
    out = []
    for w in walls:
        pf = w[2026] + (w[2041] - w[2026]) * (years - 2026) / (2041 - 2026)
        out.append(np.cumsum(-np.log(1 - np.clip(pf, 0, PF_MAX)) / REFERENCE))
    return np.array(out)


def simulate(walls, cumhaz, order, production):
    """Year all walls are renewed and expected number of walls failing before renewal."""
    cum_needed = np.cumsum([walls[i]["length"] for i in order])
    cum_made = np.cumsum(production)
    years = np.arange(START, START + len(production))
    done = years[np.minimum(np.searchsorted(cum_made, cum_needed - 1e-9), len(years) - 1)]
    expected = np.sum(1 - np.exp(-cumhaz[np.asarray(order), done - 2026]))
    return done[-1], expected


def main() -> None:
    per_year = renewed_per_year(lengths())
    x = np.array(list(YEARS), dtype=float)
    fit = stats.linregress(x, per_year)
    t95 = stats.t.ppf(0.975, len(x) - 2)
    print(f"Renewed per year {list(YEARS)[0]}-{list(YEARS)[-1]}: {np.round(per_year).astype(int).tolist()}")
    print(f"Trend: slope {fit.slope:.1f} m/yr per yr, 95% CI {fit.slope - t95 * fit.stderr:.1f}"
          f" to {fit.slope + t95 * fit.stderr:.1f}, p = {fit.pvalue:.3f}, R2 = {fit.rvalue**2:.2f}")

    recent = per_year[[list(YEARS).index(y) for y in RECENT]]
    fast = per_year[[list(YEARS).index(y) for y in FAST]]
    m, se = recent.mean(), recent.std(ddof=1) / np.sqrt(len(recent))
    tr = stats.t.ppf(0.975, len(recent) - 1)
    test = stats.ttest_1samp(recent, PLAN_RATE)
    print(f"Recent pace {RECENT[0]}-{RECENT[-1]}: mean {m:.0f} m/yr, 95% CI {m - tr * se:.0f} to {m + tr * se:.0f},"
          f" t-test against {PLAN_RATE:.0f} m/yr: p = {test.pvalue:.2f}; 2015-2018 mean {fast.mean():.0f} m/yr")

    walls = modelled_walls()
    cumhaz = cumulative_hazard(walls)
    n_years = HORIZON - START + 1
    by_beta = sorted(range(len(walls)), key=lambda i: walls[i][2026], reverse=True)
    print(f"Modelled walls: {len(walls)}, {sum(w['length'] for w in walls):.0f} m")
    rng = np.random.default_rng(SEED)
    scenarios = {
        f"recent pace ({RECENT[0]}-{RECENT[-1]})": lambda: rng.choice(recent, n_years),
        f"plan, {PLAN_RATE:.0f} m/yr": lambda: np.full(n_years, PLAN_RATE),
        f"fast pace ({FAST[0]}-{FAST[-1]})": lambda: rng.choice(fast, n_years),
    }
    rows = []
    for name, draw in scenarios.items():
        for order_name in ("lowest beta first", "random order"):
            done, risk = [], []
            for _ in range(N_BOOT if "plan" not in name or order_name == "random order" else 1):
                order = by_beta if order_name == "lowest beta first" else rng.permutation(len(walls))
                d, e = simulate(walls, cumhaz, order, draw())
                done.append(d)
                risk.append(e)
            done, risk = np.array(done), np.array(risk)
            row = {"production": name, "order": order_name,
                   "done_median": int(np.median(done)), "done_p05": int(np.percentile(done, 5)),
                   "done_p95": int(np.percentile(done, 95)),
                   "expected_failures_mean": round(risk.mean(), 2),
                   "expected_failures_p05": round(np.percentile(risk, 5), 2),
                   "expected_failures_p95": round(np.percentile(risk, 95), 2)}
            rows.append(row)
            print(f"{name:28s} {order_name:18s} all renewed {row['done_median']}"
                  f" ({row['done_p05']}-{row['done_p95']}), expected walls reaching a limit state"
                  f" before renewal {row['expected_failures_mean']:.2f}"
                  f" ({row['expected_failures_p05']:.2f}-{row['expected_failures_p95']:.2f})")
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

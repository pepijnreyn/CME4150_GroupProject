"""Production rate of the walmuur programme and the risk carried until renewal.

Report section 4.1. Uses the renewal year of every renewed walmuur
(walmuur_foundation.csv) and its length in the asset register.

1. Trend: least-squares line through the renewed length per year, 2015-2026
   (a year without a renewal counts as 0 m), with a 95% interval for the slope
   and a t-test of H0: no trend.
2. Step model: L_y = a + c [y >= 2019] + e_y, compared with the straight line
   (R2, AIC), with the 95% interval of the step and a prediction interval for
   one year. Recent pace: mean since 2019 with a 95% t-interval, and a t-test
   against the 100 m/yr of the programme plan. The forecast uses the step model:
   its level after 2019 with its residuals, by resampling the years 2019-2026.
3. Backlog: the 17 modelled walls (walmuur_failure_probability.csv) are renewed
   one after the other from 2027. The yearly production is drawn from the years
   2019-2026 (bootstrap), or fixed at 100 m/yr, or drawn from 2015-2018. Each
   draw gives the year in which each wall is renewed; both orders use the same
   draws, so the year all walls are renewed does not depend on the order.
4. Risk until renewal: a wall carries the hazard h(t) = -ln(1 - Pf(t)) / 15
   until it is renewed, with Pf(t) its best-estimate updated Pf over the 15-year
   reference period, linear between 2026 and 2041 and extended linearly after
   2041 (at most 0.95). The expected number of walls that reach a limit state
   before renewal is the sum over the walls of 1 - exp(-sum of h over the years
   it waits). Two orders: lowest beta first, and a random order.
   The constant hazard treats the 15-year Pf as spread evenly over time. If the
   weakness is a present state and the critical load occurs within a few years,
   the chance before renewal is the 15-year Pf itself, whatever the pace or
   order: the upper bound sum(Pf 2026) is printed as well.

5. Per wall, at the recent pace and lowest beta first: the mean number of years it
   waits (2026 up to and including its renewal year) and its chance to reach a
   limit state before renewal. The fault tree of section 3.1 uses these.
6. Order check: the bootstrap assumes the 17 walls are next in line, but 780 m is
   still to do (gu2025up), so 169 m of other walls may come first, and the raks
   with many cellar owners (3-6) may come last on purpose.

Writes data/processed/production_rate_risk.csv and production_rate_walls.csv.
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
OUT_WALLS = ROOT / "data" / "processed" / "production_rate_walls.csv"

# ---- Inputs ----------------------------------------------------------------
YEARS = range(2015, 2027)       # years of the trend fit; 2015 is the first renewal
RECENT = range(2019, 2027)      # the recent pace, after the fast years 2016-2018
FAST = range(2015, 2019)
PLAN_RATE = 100.0               # [m/yr], pace of the programme plan
START = 2027                    # first year of future production
HORIZON = 2100                  # last year simulated
REFERENCE = 15                  # NEN 8700 reference period [yr]
PF_MAX = 0.95
REMAINING = 780.0               # [m] walmuur still to restore (gu2025up)
LAST_RAKS = (3, 4, 5, 6)        # raks with many cellar owners, possibly done last
N_BOOT = 20_000
UNIT_COST = 35_000.0            # [EUR/m] renewal cost (programme plan, report section 3.2)
RATE = 0.028                    # discount rate [1/yr]
C_F_PACE = 1.5e6                # failure cost per wall [EUR] (report section 3.2)
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
            walls[r["Nummer"]]["Nummer"] = r["Nummer"]
            walls[r["Nummer"]]["rak"] = int(float(r["rak"]))
    return list(walls.values())


def cumulative_hazard(walls):
    """Sum of h(t) from 2026 up to and including each year to HORIZON, per wall."""
    years = np.arange(2026, HORIZON + 1)
    out = []
    for w in walls:
        pf = w[2026] + (w[2041] - w[2026]) * (years - 2026) / (2041 - 2026)
        out.append(np.cumsum(-np.log(1 - np.clip(pf, 0, PF_MAX)) / REFERENCE))
    return np.array(out)


def simulate(walls, cumhaz, order, production, offset=0.0, per_wall=False):
    """Year all walls are renewed and expected number of walls failing before renewal.

    offset [m] is renewed before the first of these walls."""
    cum_needed = offset + np.cumsum([walls[i]["length"] for i in order])
    cum_made = np.cumsum(production)
    years = np.arange(START, START + len(production))
    done = years[np.minimum(np.searchsorted(cum_made, cum_needed - 1e-9), len(years) - 1)]
    p_wall = 1 - np.exp(-cumhaz[np.asarray(order), done - 2026])
    if per_wall:
        return done, p_wall
    return done[-1], np.sum(p_wall)


def main() -> None:
    per_year = renewed_per_year(lengths())
    x = np.array(list(YEARS), dtype=float)
    fit = stats.linregress(x, per_year)
    t95 = stats.t.ppf(0.975, len(x) - 2)
    print(f"Renewed per year {list(YEARS)[0]}-{list(YEARS)[-1]}: {np.round(per_year).astype(int).tolist()}")
    print(f"Trend: slope {fit.slope:.1f} m/yr per yr, 95% CI {fit.slope - t95 * fit.stderr:.1f}"
          f" to {fit.slope + t95 * fit.stderr:.1f}, p = {fit.pvalue:.3f}, R2 = {fit.rvalue**2:.2f}")

    step = (x >= RECENT[0]).astype(float)
    X = np.column_stack([np.ones_like(x), step])
    coef = np.linalg.lstsq(X, per_year, rcond=None)[0]
    resid = per_year - X @ coef
    s2 = resid @ resid / (len(x) - 2)
    xtx = np.linalg.inv(X.T @ X)
    se_c = np.sqrt(s2 * xtx[1, 1])
    r2 = 1 - resid @ resid / np.sum((per_year - per_year.mean())**2)
    aic = lambda rss: len(x) * np.log(rss / len(x)) + 4
    lin_rss = np.sum((per_year - fit.intercept - fit.slope * x)**2)
    half = t95 * np.sqrt(s2 * (1 + np.array([1, 1]) @ xtx @ np.array([1, 1])))
    print(f"Step model: before {coef[0]:.0f} m/yr, step {coef[1]:.0f} (95% CI {coef[1] - t95 * se_c:.0f} to"
          f" {coef[1] + t95 * se_c:.0f}, p = {2 * stats.t.sf(abs(coef[1] / se_c), len(x) - 2):.3f}),"
          f" R2 {r2:.2f}, AIC {aic(resid @ resid):.1f} vs straight line {aic(lin_rss):.1f};"
          f" one-year prediction {coef.sum():.0f} m (95% PI {max(coef.sum() - half, 0):.0f} to {coef.sum() + half:.0f});"
          f" Shapiro-Wilk on residuals p = {stats.shapiro(resid).pvalue:.2f}")
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
    print(f"Modelled walls: {len(walls)}, {sum(w['length'] for w in walls):.0f} m;"
          f" without time scaling E[N] = sum of Pf 2026 = {sum(w[2026] for w in walls):.2f}")
    rng = np.random.default_rng(SEED)
    scenarios = {
        f"recent pace ({RECENT[0]}-{RECENT[-1]})": lambda: rng.choice(recent, n_years),
        f"plan, {PLAN_RATE:.0f} m/yr": lambda: np.full(n_years, PLAN_RATE),
        f"fast pace ({FAST[0]}-{FAST[-1]})": lambda: rng.choice(fast, n_years),
    }
    rows = []
    all_draws = {}
    for name, draw in scenarios.items():
        draws = all_draws[name] = [draw() for _ in range(N_BOOT)]
        for order_name in ("lowest beta first", "random order"):
            done, risk = [], []
            for b in range(N_BOOT if "plan" not in name or order_name == "random order" else 1):
                order = by_beta if order_name == "lowest beta first" else rng.permutation(len(walls))
                d, e = simulate(walls, cumhaz, order, draws[b])
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
    # Per wall, recent pace, lowest beta first (used by the fault tree, section 3.1).
    done_w = np.zeros((N_BOOT, len(walls)))
    p_w = np.zeros((N_BOOT, len(walls)))
    for b in range(N_BOOT):
        d, pw = simulate(walls, cumhaz, by_beta, all_draws[f"recent pace ({RECENT[0]}-{RECENT[-1]})"][b],
                         per_wall=True)
        done_w[b, by_beta], p_w[b, by_beta] = d, pw
    wall_rows = [{"Nummer": w["Nummer"], "Naam": w["name"], "length_m": w["length"],
                  "pf_2026": w[2026], "pf_2041": w[2041],
                  "years_until_renewal": round((done_w[:, i] - 2026 + 1).mean(), 2),
                  "renewal_year_median": int(np.median(done_w[:, i])),
                  "p_before_renewal": round(p_w[:, i].mean(), 4)} for i, w in enumerate(walls)]
    with OUT_WALLS.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(wall_rows[0]))
        wr.writeheader()
        wr.writerows(wall_rows)
    print("Per wall (recent pace, lowest beta first): years until renewal "
          + ", ".join(f"{r['Naam'].replace('Oude Gracht - ', '').replace('Kromme Nieuwe Gracht', 'KNG')}"
                      f" {r['years_until_renewal']:.1f}" for r in wall_rows))
    # Order check: other remaining walls first; raks 3-6 last.
    offset = REMAINING - sum(w["length"] for w in walls)
    late = sorted(by_beta, key=lambda i: walls[i]["rak"] in LAST_RAKS)
    for label, order, off in (("other walls first", by_beta, offset),
                              (f"other walls first, raks {LAST_RAKS[0]}-{LAST_RAKS[-1]} last", late, offset)):
        res = [simulate(walls, cumhaz, order, rng.choice(recent, n_years), off) for _ in range(N_BOOT)]
        done, risk = np.array([r[0] for r in res]), np.array([r[1] for r in res])
        print(f"recent pace, {label} ({off:.0f} m first): all renewed {int(np.median(done))}"
              f" ({int(np.percentile(done, 5))}-{int(np.percentile(done, 95))}), E[N] {risk.mean():.2f}"
              f" ({np.percentile(risk, 5):.2f}-{np.percentile(risk, 95):.2f})")
    # L1 of the fault tree (section 3.1): share of the modelled length not renewed by the end
    # of the reference period, at the recent pace and at the lower 95% bound of its mean.
    years_left = 2041 - START + 1
    total = sum(w["length"] for w in walls)
    made = rng.choice(recent, (N_BOOT, years_left)).sum(axis=1)
    share = np.clip(total - made, 0, None) / total
    low_pace = m - tr * se
    print(f"L1, share of {total:.0f} m not renewed by 2041: recent pace mean {share.mean():.4f}"
          f" (P(share > 0) = {(share > 0).mean():.4f}); at {low_pace:.0f} m/yr"
          f" {max(0.0, total - years_left * low_pace) / total:.2f}; at {PLAN_RATE:.0f} m/yr"
          f" {max(0.0, total - years_left * PLAN_RATE) / total:.2f}")
    # Pace as a programme decision: a faster pace advances the renewal cost of the 17
    # walls (present value at RATE) and avoids limit states (E[N] x C_F x DF).
    pv, en = {}, {}
    for name in all_draws:
        cost, risk = [], []
        for prod in all_draws[name][:2000]:
            done, pw = simulate(walls, cumhaz, by_beta, prod, per_wall=True)
            lengths_ = np.array([walls[i]["length"] for i in by_beta])
            cost.append(np.sum(lengths_ * UNIT_COST * (1 + RATE) ** -(done - 2026 + 0.5)))
            risk.append(np.sum(pw))
        pv[name], en[name] = np.mean(cost), np.mean(risk)
    base = f"recent pace ({RECENT[0]}-{RECENT[-1]})"
    for name in pv:
        extra = pv[name] - pv[base]
        avoided = (en[base] - en[name]) * C_F_PACE * (1 + RATE) ** -2.5
        line = (f"pace {name:24s}: PV renewal {pv[name] / 1e6:5.2f} M EUR, E[N] {en[name]:.2f}")
        if name != base:
            line += (f"; vs recent: extra cost {extra / 1e6:+.2f} M, avoided failures {avoided / 1e6:+.2f} M"
                     f" at C_f {C_F_PACE / 1e6:.1f} M; break-even C_f"
                     f" {extra / ((en[base] - en[name]) * (1 + RATE) ** -2.5) / 1e6:.1f} M")
        print(line)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

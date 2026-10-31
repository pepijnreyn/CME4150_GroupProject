"""Fault tree (report section 3.1) and decision tree (section 3.2) for the walmuren.

The tree, for one wall over the years until it is renewed:

  top            = load OR (M AND not_repaired)
  load           = W2 OR Q1 OR Q2 OR Q3 OR E1 OR E2 OR E3 OR E4
  not_repaired   = D OR not_recognised OR I3 OR repair_late
  not_recognised = (S1 OR S2 OR S3) AND (I1 OR I2)
  repair_late    = L1 OR L2 OR L3 OR L4

Exposure. The walls are renewed around 2031 (section 4.1), so a wall is exposed
only until its renewal, not for the 15-year reference period of NEN 8700.
production_rate_walls.csv gives, per wall, the mean number of years until
renewal T and the chance M to reach a limit state of the model in those years
(recent pace, lowest beta first). The load events are given for 15 years in
Table 3.1 and are scaled to T as 1 - (1 - p)^(T / 15). The human and
organisational events are chances per weakness or per programme, so they are
not scaled.

D is the chance that a weakness gives no warning that an inspection could see
before the limit state is reached: pile bending and overturning of a low wall
give little warning. Without D the AND gate would let the repair chain stop
every failure that the model predicts.

The median wall (median beta) is Oude Gracht Rak 09 WZ. For the 17 walls
together, a Monte Carlo links the M events of the walls with a Gaussian copula
(RHO_WALLS, an assumption) and draws S3 and I1 once for all walls and half of
I2 once for all walls.

Decision, per alternative, with costs discounted at RATE (Werkgroep
discontovoet 2025: 2.8 %): E[C] = c + P_f C_f DF, with DF the mean discount
factor over the exposure; CE = c + R ln(1 - P_f + P_f exp(C_f DF / R));
pessimistic: every event at its upper bound, and a measure lowers an event by
the same factor as in the base case. Two alternatives use the failure model
directly (walmuur_model_checks.csv): A6 restricts use until renewal, and A7
first measures the displacement of the wall (preposterior): if it is below
5 mm the wall stays in the programme as it is, otherwise use is restricted.

Run: python3 scripts/fault_tree.py
"""

import csv
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
WALLS = ROOT / "data" / "processed" / "production_rate_walls.csv"
CHECKS = ROOT / "data" / "processed" / "walmuur_model_checks.csv"
SENS = ROOT / "data" / "processed" / "walmuur_sensitivity.csv"
MEDIAN_WALL = "Oude Gracht - Rak 09 WZ"

# ---- Inputs ----------------------------------------------------------------
REF = 15.0                      # years over which Table 3.1 gives the load events
EVENTS = {  # id: (base, low, high); load events over 15 years, the others per weakness
    "W2": (0.001, 0.0002, 0.005), "Q1": (0.005, 0.001, 0.02), "Q2": (0.001, 0.0002, 0.005),
    "Q3": (0.001, 0.0002, 0.005), "E1": (0.001, 0.0002, 0.005), "E2": (0.005, 0.001, 0.02),
    "E3": (0.05, 0.02, 0.15), "E4": (0.001, 0.0002, 0.005),
    "D": (0.50, 0.30, 0.80), "S1": (0.10, 0.05, 0.20), "S2": (0.0, 0.0, 0.0),
    "S3": (0.10, 0.05, 0.20), "I1": (0.30, 0.10, 0.73), "I2": (0.16, 0.12, 0.28),
    "I3": (0.03, 0.008, 0.11), "L1": (0.0, 0.0, 0.45),
    "L2": (0.10, 0.05, 0.20), "L3": (0.10, 0.05, 0.20), "L4": (0.10, 0.05, 0.20),
}
LOAD = ["W2", "Q1", "Q2", "Q3", "E1", "E2", "E3", "E4"]
RATE = 0.028                    # discount rate [1/yr]
C_F = 1500.0                    # failure cost [k EUR]
C_RENEW = 1300.0                # renewal of the median wall (36 m) [k EUR]
R = 500.0                       # risk tolerance [k EUR]
RHO_WALLS = 0.084               # copula correlation between the M events of the walls (assumption)
COMMON = {"S3": 1.0, "I1": 1.0, "I2": 0.5}   # share of the probability drawn once for all walls
N_MC = 400_000
SEED = 1
# Alternatives: one-off cost and yearly cost [k EUR], changed events. "M" as a factor on
# the hazard of the model event, "T" as the years until renewal.
ALTERNATIVES = {
    "A0 Current programme": (0, 0, {}),
    "A1 Scour and load control": (72, 3.2, {"E3": 0.02, "Q1": 0.001, "E2": 0.001}),
    "A2 Inspection": (60, 2.0, {"I1": 0.10, "I2": 0.12, "I3": 0.008, "S3": 0.05, "D": 0.30}),
    "A3 Organisation": (15, 6.7, {"L2": 0.05, "L3": 0.05, "L4": 0.05}),
    "A4 Renew now": (None, 0, {"T": 1.0, "E3": 0.02, "W2": 0.0002}),
    "A6 Restrict use": (10, 3.0, {"M": "restrict", "Q1": 0.001, "Q2": 0.0002}),
}
ALTERNATIVES["A5 Package A1-A3"] = tuple(
    sum(ALTERNATIVES[a][i] for a in ("A1 Scour and load control", "A2 Inspection",
                                     "A3 Organisation")) for i in (0, 1)) + (
    {**ALTERNATIVES["A1 Scour and load control"][2], **ALTERNATIVES["A2 Inspection"][2],
     **ALTERNATIVES["A3 Organisation"][2]},)
C_SURVEY = 15.0                 # A7: survey of the displacement of the wall [k EUR]
# ----------------------------------------------------------------------------
RHO = np.log(1 + RATE)


def p_or(*ps):
    return 1 - np.prod([1 - np.asarray(p) for p in ps], axis=0)


def scale(p, T):
    """A probability over REF years, scaled to T years."""
    return 1 - (1 - np.asarray(p))**(np.asarray(T) / REF)


def discount(T):
    """Mean discount factor over T years, and the present value of 1 per year for T years."""
    df = (1 - np.exp(-RHO * T)) / (RHO * T)
    return df, df * T


def tree(p):
    """Top event and the two main branches for a dict of event probabilities."""
    load = p_or(*(p[e] for e in LOAD))
    not_recognised = p_or(p["S1"], p["S2"], p["S3"]) * p_or(p["I1"], p["I2"])
    not_repaired = p_or(p["D"], not_recognised, p["I3"], p_or(p["L1"], p["L2"], p["L3"], p["L4"]))
    return p_or(load, p["M"] * not_repaired), load, not_repaired


def events(level, T, M, change=None):
    """Event probabilities for a wall exposed T years with model event M."""
    i = {"base": 0, "low": 1, "high": 2}[level]
    p = {e: v[i] for e, v in EVENTS.items()}
    for e, v in (change or {}).items():
        if e in p:  # a measure moves the event by the same factor at every level
            p[e] = v if level == "base" or EVENTS[e][0] == 0 else EVENTS[e][i] * v / EVENTS[e][0]
    T = (change or {}).get("T", T)
    M = 1 - (1 - M)**(T / (change or {}).get("T_base", T)) if "T" in (change or {}) else M
    for e in LOAD:
        p[e] = scale(p[e], T)
    p["M"] = M
    return p


def read_walls():
    rows = list(csv.DictReader(WALLS.open()))
    return {r["Naam"]: (float(r["years_until_renewal"]), float(r["p_before_renewal"]),
                        float(r["pf_2026"])) for r in rows}


def model_factor(checks, col):
    """Ratio of the cumulative hazard of a model variant to that of the base model (median wall)."""
    pf = lambda c: norm.cdf(-float(checks[c]))
    return np.log(1 - pf(col)) / np.log(1 - pf("beta_base"))


def monte_carlo(p_walls, rng):
    """Mean, SD, P(N >= 5) and the draws of the number of failing walls, without and with common cause."""
    n = len(p_walls)
    m = np.array([pw["M"] for pw in p_walls])
    out = []
    for common in (False, True):
        z = (np.sqrt(RHO_WALLS) * rng.standard_normal((N_MC, 1))
             + np.sqrt(1 - RHO_WALLS) * rng.standard_normal((N_MC, n)))
        o = {"M": z < norm.ppf(m)}
        for e in EVENTS:
            pe = np.array([pw[e] for pw in p_walls])
            share = COMMON.get(e, 0.0) if common else 0.0
            shared = rng.random((N_MC, 1)) < share * pe
            own = rng.random((N_MC, n)) < (pe - share * pe) / np.maximum(1 - share * pe, 1e-12)
            o[e] = shared | own
        load = np.logical_or.reduce([o[e] for e in LOAD])
        not_recognised = (o["S1"] | o["S2"] | o["S3"]) & (o["I1"] | o["I2"])
        not_repaired = o["D"] | not_recognised | o["I3"] | o["L1"] | o["L2"] | o["L3"] | o["L4"]
        count = (load | (o["M"] & not_repaired)).sum(axis=1)
        out.append((count.mean(), count.std(), (count >= 5).mean(), count))
    return out


def main() -> dict:
    """Prints the results and returns what plot_appendix_figures.py needs."""
    walls = read_walls()
    checks = {r["Naam"]: r for r in csv.DictReader(CHECKS.open())}[MEDIAN_WALL]
    T, M, pf15 = walls[MEDIAN_WALL]
    sens = {r["Naam"]: r for r in csv.DictReader(SENS.open())}[MEDIAN_WALL]
    cols = ["beta_base", "beta_kgamma", "beta_more", "beta_groundwater", "beta_soil_mixed"]
    m_range = [1 - (1 - M)**(np.log(1 - norm.cdf(-float(sens[c]))) / np.log(1 - pf15)) for c in cols]
    base = events("base", T, M)
    low = events("low", T, min(m_range))
    high = events("high", T, max(m_range))
    top, load, not_repaired = tree(base)
    print(f"{MEDIAN_WALL}: T = {T:.2f} yr until renewal, M = {M:.4f} ({min(m_range):.4f}-{max(m_range):.4f});"
          f" over 15 years M would be {pf15:.3f}")
    print(f"load {load:.4f}, not repaired in time {not_repaired:.3f}, top {top:.4f};"
          f" without repair {tree(base | {'D': 1.0})[0]:.4f}; without D {tree(base | {'D': 0.0})[0]:.4f}")
    print(f"all low {tree(low)[0]:.4f}, all high {tree(high)[0]:.4f}")
    p_walls = [events("base", t, m) for (t, m, _) in walls.values()]
    per_wall = np.array([tree(p)[0] for p in p_walls])
    m_part = np.array([p["M"] * tree(p)[2] for p in p_walls])
    print(f"per wall {per_wall.min():.3f}-{per_wall.max():.3f}; 17 walls: sum {per_wall.sum():.2f}"
          f" (model event before renewal {sum(m for (_, m, _) in walls.values()):.2f}, of which not repaired"
          f" {m_part.sum():.2f}; other loads {per_wall.sum() - m_part.sum():.2f});"
          f" per year {per_wall.sum() / np.mean([t for (t, _, _) in walls.values()]):.2f}")
    print("Fussell-Vesely: " + ", ".join(
        f"{e} {1 - tree(base | {e: 0.0})[0] / top:.2f}" for e in ["M"] + list(EVENTS) if base[e] > 0))
    swings = {e: tree(base | {e: high[e]})[0] - tree(base | {e: low[e]})[0] for e in ["M"] + list(EVENTS)}
    print("swing low->high: " + ", ".join(f"{e} {s:.4f}" for e, s in
                                          sorted(swings.items(), key=lambda x: -x[1])[:7]))
    rng = np.random.default_rng(SEED)
    counts = {}
    for common, (mean, sd, p5, count) in zip((False, True), monte_carlo(p_walls, rng)):
        print(f"17 walls, common cause {common}: mean {mean:.2f}, SD {sd:.2f}, P(N>=5) {p5:.4f}")
        counts[common] = count

    df, annuity = discount(T)
    print(f"\ndiscount: mean factor over {T:.2f} yr {df:.3f}; PV of 1 per year {annuity:.2f}")
    m_restrict = 1 - (1 - M)**model_factor(checks, "beta_restrict_use")
    res = {}
    print(f"{'alternative':28s} {'cost':>6s} {'Pf':>6s} {'load':>6s} {'notrep':>6s} {'E[C]':>6s}"
          f" {'CE':>6s} {'pess':>6s} {'N17':>5s}")
    for name, (once, yearly, change) in ALTERNATIVES.items():
        change = dict(change)
        if name.startswith("A4"):
            t_new = change["T"]
            cost = C_RENEW * (np.exp(-RHO * 0.5) - np.exp(-RHO * T))
            change["T_base"] = T
            fac = None
        else:
            t_new = T
            cost = once + yearly * annuity
        if change.get("M") == "restrict":
            fac = model_factor(checks, "beta_restrict_use")
            del change["M"]
        else:
            fac = None
        def prob(level, t, m, ch):
            ch = dict(ch, T_base=t) if "T" in ch else ch
            mm = 1 - (1 - m)**fac if fac else m
            return tree(events(level, t, mm, ch))[0]
        pf = prob("base", T, M, change)
        _, ld, nr = tree(events("base", T, M, change))
        pf_pess = prob("high", T, max(m_range), change)
        df_alt = discount(t_new)[0] if t_new != T else df
        n17 = sum(prob("base", t, m, change) for (t, m, _) in walls.values())
        ce = cost + R * np.log(1 - pf + pf * np.exp(C_F * df_alt / R))
        res[name] = (cost, pf, df_alt)
        print(f"{name:28s} {cost:6.0f} {pf:6.4f} {ld:6.4f} {nr:6.3f} {cost + pf * C_F * df_alt:6.0f}"
              f" {ce:6.0f} {cost + pf_pess * C_F * df_alt:6.0f} {n17:5.2f}")

    # A7: survey first (preposterior). After the survey the best response is chosen:
    # A0, A6 (restrict use) or A4 (renew now), with M updated by the outcome.
    p_fav = float(checks["monitor_p_fav"])
    m_obs = {"fav": 1 - (1 - M)**model_factor(checks, "beta_monitor_fav"),
             "unf": 1 - (1 - M)**model_factor(checks, "beta_monitor_unf")}
    m_obs_r = {"fav": m_obs["fav"] * 0 + 1 - (1 - m_obs["fav"])**model_factor(checks, "beta_restrict_use"),
               "unf": 1 - (1 - M)**model_factor(checks, "beta_monitor_unf_restrict")}
    once6, yearly6, ch6 = ALTERNATIVES["A6 Restrict use"]
    ch6 = {k: v for k, v in ch6.items() if k != "M"}
    c6 = once6 + yearly6 * annuity
    c4 = C_RENEW * (np.exp(-RHO * 0.5) - np.exp(-RHO * T))
    df1 = discount(1.0)[0]
    responses = {}
    for out in ("fav", "unf"):
        responses[out] = {
            "A0": (0.0, tree(events("base", T, m_obs[out]))[0], df),
            "A6": (c6, tree(events("base", T, m_obs_r[out], ch6))[0], df),
            "A4": (c4, tree(events("base", 1.0, 1 - (1 - m_obs[out])**(1 / T),
                                   {"E3": 0.02, "W2": 0.0002}))[0], df1)}

    def a7(cf):
        """E[C] of A7 at failure cost cf, the best response per outcome, and Pf."""
        best = {out: min(r.items(), key=lambda kv: kv[1][0] + kv[1][1] * cf * kv[1][2])
                for out, r in responses.items()}
        ec = C_SURVEY + sum(pw * (c + p * cf * d) for pw, (_, (c, p, d)) in
                            zip((p_fav, 1 - p_fav), (best["fav"], best["unf"])))
        pf = p_fav * best["fav"][1][1] + (1 - p_fav) * best["unf"][1][1]
        return ec, pf, best["fav"][0], best["unf"][0]

    ec7, pf7, r_fav, r_unf = a7(C_F)
    print(f"A7 Monitor, then decide: P(below 5 mm) {p_fav:.2f}; M fav {m_obs['fav']:.4f}, unf {m_obs['unf']:.4f};"
          f" responses: " + "; ".join(f"{out} " + ", ".join(f"{k} Pf {v[1]:.4f} E[C] {v[0] + v[1] * C_F * v[2]:.0f}"
                                                   for k, v in r.items()) for out, r in responses.items()))
    print(f"A7 at C_f {C_F:.0f}: E[C] {ec7:.0f}, Pf {pf7:.4f}, best response fav {r_fav}, unf {r_unf}")
    ec_best = min(c + p * C_F * d for (c, p, d) in res.values())
    print(f"value of the survey (before its cost) at C_f {C_F:.0f}: {ec_best - (ec7 - C_SURVEY):.0f} k EUR")

    best, switches = None, []
    for cf in np.arange(100, 30_001, 50):
        costs = {k: c + p * cf * d for k, (c, p, d) in res.items()}
        costs["A7 Monitor, then decide"] = a7(cf)[0]
        name = min(costs, key=costs.get)
        if name != best:
            switches.append(f"{name.split()[0]} from {cf / 1000:.2f} M")
            best = name
    print("cheapest alternative as C_f rises: " + ", ".join(switches))
    for cf in (3000.0, 5000.0):
        e, pf_, rf, ru = a7(cf)
        others = {k: c + p * cf * d for k, (c, p, d) in res.items()}
        print(f"C_f {cf / 1000:.0f} M: A7 E[C] {e:.0f} (fav {rf}, unf {ru}); best other "
              f"{min(others, key=others.get)} {min(others.values()):.0f}; survey worth"
              f" {min(others.values()) - (e - C_SURVEY):.0f} k EUR")
    print(f"NEN 8700 target Phi(-1.8) over 15 yr = {norm.cdf(-1.8):.3f}, scaled to {T:.1f} yr:"
          f" {scale(norm.cdf(-1.8), T):.4f}")

    # Scenarios for the model event M. The model is not calibrated, so its absolute
    # level is uncertain: M times 0.3 and 3. "No time scaling": the weakness is a
    # present state and the critical load occurs within the exposure, so the chance
    # of a limit state before renewal is the 15-year P_f itself (an upper bound).
    print("\nScenarios for M (A0-A6, C_f = 1.5 M EUR):")
    scen = {"x0.3": lambda m, pf: 0.3 * m, "x1": lambda m, pf: m,
            "x3": lambda m, pf: min(1.0, 3 * m), "no scaling": lambda m, pf: pf}
    for label, f in scen.items():
        m_med = f(M, pf15)
        costs = {}
        for name, (once, yearly, change) in ALTERNATIVES.items():
            change = dict(change)
            fac = model_factor(checks, "beta_restrict_use") if change.pop("M", None) else None
            if name.startswith("A4"):
                cost, change["T_base"], d = C_RENEW * (np.exp(-RHO * 0.5) - np.exp(-RHO * T)), T, discount(1.0)[0]
            else:
                cost, d = once + yearly * annuity, df
            mm = 1 - (1 - m_med)**fac if fac else m_med
            pf = tree(events("base", T, mm, change))[0]
            ce = cost + R * np.log(1 - pf + pf * np.exp(C_F * d / R))
            costs[name] = (cost + pf * C_F * d, ce, pf)
        n17 = sum(tree(events("base", t, f(m, p)))[0] for (t, m, p) in walls.values())
        ev = min(costs, key=lambda k: costs[k][0])
        ce_best = min(costs, key=lambda k: costs[k][1])
        print(f"  M {label:10s}: M median {m_med:.3f}, A0 Pf {costs['A0 Current programme'][2]:.3f},"
              f" N17 {n17:.2f}; E[C] A0 {costs['A0 Current programme'][0]:.0f},"
              f" A4 {costs['A4 Renew now'][0]:.0f}, A6 {costs['A6 Restrict use'][0]:.0f};"
              f" cheapest {ev.split()[0]}, lowest CE {ce_best.split()[0]}")
    return {"res": res, "a7": a7, "counts": counts, "C_F": C_F}


if __name__ == "__main__":
    main()

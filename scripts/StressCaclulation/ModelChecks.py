"""Checks of the walmuur failure model that answer the review of the report.

FailureProbability.py updates the failure probability with one piece of
evidence: the wall stands today under soil and water, without surcharge. This
script reruns the same model (the same functions, fewer draws) for the 17
walls with one change at a time and reports beta (updated, 2026):

  base           the model as it is
  service_load   proven strength with a survived service load: the wall also
                 stands under the terrace and crowd load that the werven carry,
                 Q_ETA at A_ETA from the edge (EN 1991-1-1 Table 6.2, category
                 C1 areas with tables: 2-3 kPa)
  prior_type     no update of the wall type: the types weighted by their prior
                 chance (computed from the base runs)
  screen_failed  the timber screen below the floor has gone (assumption A1 of
                 the report fails): the soil between the floor and the canal
                 bed, H_SCREEN deep, also pushes on the piles
  no_friction    no wall friction on the back of the body (delta = 0), since
                 K of clay and peat is near K0, where little friction is mobilised
  restrict_use   use restricted until renewal: no terraces, goods or vehicles
                 within A_RESTRICT of the edge (a ~ U(A_RESTRICT, 3) m)

and one monitoring example, a preposterior analysis: the horizontal
displacement of the pile heads under today's soil and water load (Hetenyi,
y = P lambda / (k D0) for a fixed head, twice that for a pinned head) is
measured with an error of SIGMA_OBS. If the measured displacement is below
Y_LIM, the draws with a larger displacement become less likely; the script
gives the chance of that outcome and beta after each outcome.

Writes data/processed/walmuur_model_checks.csv.
Run: python3 scripts/StressCaclulation/ModelChecks.py   (about 6 minutes)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import FailureProbability as FP  # noqa: E402
from PileStrength import head_moment, pile_stress, remaining_diameter  # noqa: E402
from SoilForce import soil_force  # noqa: E402
from TotalStress import total_stress  # noqa: E402
from TraficLoad import A_MAX, effective_surcharge, sample_surcharge, surcharge_force  # noqa: E402
from WallResistance import SECTIONS, friction_tan, section_resistance  # noqa: E402
from WaterLoad import CANAL_NAP, GAMMA_W, GROUNDWATER_NAP, water_force  # noqa: E402

OUT = ROOT / "data" / "processed" / "walmuur_model_checks.csv"

# ---- Inputs ----------------------------------------------------------------
N_MC = 100_000                  # draws per wall, type and variant
YEAR = 2026
Q_ETA, A_ETA = 2.5, 0.5         # survived service load [kPa] and its distance to the edge [m]
H_SCREEN = (0.3, 1.0)           # depth of the canal bed below the floor if the screen has gone [m]
A_RESTRICT = 1.5                # no load closer to the edge than this under restricted use [m]
SIGMA_OBS = 0.002               # error of a displacement measurement [m]
Y_LIM = 0.005                   # threshold of the monitoring example [m]
SEED = 7
# ----------------------------------------------------------------------------
TYPES = ("type 1", "type 2")
VARIANTS = ("base", "service_load", "screen_failed", "no_friction", "restrict_use")


def beta(pf):
    return -norm.ppf(max(pf, 0.5 / N_MC))


def simulate(wall, section, rng, variant):
    """FailureProbability.simulate with the changes of `variant`, plus the displacement today."""
    s = SECTIONS[section]
    n = N_MC
    werf = (rng.normal(wall["werf_nap"], FP.WERF_SD, n) if wall["werf"] == "yes"
            else rng.uniform(*FP.NO_WERF, n))
    dz = rng.uniform(*FP.DZ, n)
    K, gamma_s = FP.sample_soil(wall["soil_type"], n, rng)
    gamma_m, _ = FP.sample_wall(n, rng)
    gammas = {"masonry": gamma_m, "rc": FP.GAMMA_RC, "timber": FP.GAMMA_TIMBER, "soil": gamma_s,
              "concrete": rng.normal(FP.GAMMA_C_MEAN, FP.GAMMA_C_COV * FP.GAMMA_C_MEAN, n)}
    theta_R = FP.lognormal(rng, FP.THETA_R_COV, n)
    p = FP.sample_piles(n, rng)
    H = werf - (s["base"] + dz)
    x_front, x_rear = s["piles"]
    h_screen = rng.uniform(*H_SCREEN, n)

    def event(q, a, gw):
        d_w, d_c = werf - gw, werf - CANAL_NAP
        S = total_stress(K, gamma_s, q, a, H, d_w, d_c)
        F_soil = soil_force(K, gamma_s, H, d_w) + surcharge_force(K, q, a, H)
        F_h = F_soil + water_force(H, d_w, d_c)
        V, M = section_resistance(section, werf, dz, (CANAL_NAP + gw) / 2, gammas)
        F_v = 0 * K if variant == "no_friction" else friction_tan(K) * F_soil
        M_R = theta_R * M + F_v * (s["back"] - x_front)
        rear = (M_R - S) / (x_rear - x_front)
        front = np.maximum(V + F_v - rear, 0)
        H_rest = np.maximum(F_h - s["rake"] * front, 0)
        if variant == "screen_failed":
            # Earth pressure of the soil between the floor and the canal bed, and the
            # difference of groundwater and canal level over that depth, on the piles.
            sigma_v = gamma_s * np.minimum(d_w, H) + (gamma_s - GAMMA_W) * np.maximum(H - d_w, 0)
            q_eff = effective_surcharge(q, a, H)
            H_rest = H_rest + (K * (sigma_v + q_eff + 0.5 * (gamma_s - GAMMA_W) * h_screen)
                               + GAMMA_W * np.maximum(gw - CANAL_NAP, 0)) * h_screen
        return {"overturning": M_R < S, "P": H_rest * p["s"] / 2,
                "N": front * np.sqrt(1 + s["rake"]**2) * p["s"]}

    def pile(e):
        d = remaining_diameter(p["D0"], p["shell"], p["rate"], YEAR)
        core = np.maximum(d, 0.02)
        M = head_moment(e["P"], core, p["D0"], p["E"], p["k"], s["fixed_head"])
        ratio = np.where(d > 0.02, pile_stress(M, e["N"], core, p["theta_M"]) / p["MOR"], np.inf)
        lam = (p["k"] * p["D0"] / (4 * p["E"] * np.pi * core**4 / 64))**0.25
        y = (1 if s["fixed_head"] else 2) * e["P"] * lam / (p["k"] * p["D0"])
        return ratio, y

    zero = np.zeros(n)
    q_eta = np.full(n, Q_ETA) if variant == "service_load" else zero
    a_eta = np.full(n, A_ETA) if variant == "service_load" else zero
    today = event(q_eta, a_eta, rng.uniform(*GROUNDWATER_NAP, n))
    ratio_today, _ = pile(today)
    stands = ~today["overturning"] & (ratio_today <= 1)
    # The displacement that a survey would see: under soil and water only.
    _, y_today = pile(event(zero, zero, rng.uniform(*GROUNDWATER_NAP, n)))

    a_min = A_RESTRICT if variant == "restrict_use" else 0.0
    q, a = sample_surcharge(n, rng, a_min=a_min, a_max=A_MAX)
    e = event(q, a, rng.uniform(*GROUNDWATER_NAP, n))
    ratio, _ = pile(e)
    fail = e["overturning"] | (ratio > 1)
    return {"stands": stands, "fail": fail, "y": y_today}


def mixture(res, p2, weight=None):
    """Updated Pf of the two types, weighted by prior x P(evidence | type)."""
    w = {t: (1 - p2 if t == "type 1" else p2) * (res[t]["stands"] if weight is None else weight[t])
         for t in TYPES}
    total = sum(w.values())
    return sum(w[t] / total * res[t]["pf"] for t in TYPES), w["type 2"] / total


def main() -> None:
    walls = FP.wall_table()
    walls = walls[(walls["status"] != "renewed") & walls["has_werf"].ne("no")]
    rows = []
    for i, (_, wall) in enumerate(walls.iterrows()):
        p2 = wall["p_type2_prior"]
        row = {"Nummer": wall["Nummer"], "Naam": wall["Naam"], "length_m": wall["Lengte"],
               "p_type2_prior": p2}
        for variant in VARIANTS:
            res, draws = {}, {}
            for j, t in enumerate(TYPES):
                x = simulate(wall, t, np.random.default_rng(SEED + 100 * i + j), variant)
                st = x["stands"]
                res[t] = {"stands": st.mean(), "pf": (x["fail"] & st).sum() / max(st.sum(), 1)}
                draws[t] = x
                row[f"beta_{variant}_{t.replace(' ', '')}"] = round(beta(res[t]["pf"]), 3)
            pf, post2 = mixture(res, p2)
            row[f"beta_{variant}"] = round(beta(pf), 3)
            row[f"p_type2_{variant}"] = round(post2, 3)
            if variant == "base":
                prior_pf = (1 - p2) * res["type 1"]["pf"] + p2 * res["type 2"]["pf"]
                row["beta_prior_type"] = round(beta(prior_pf), 3)
            if variant in ("base", "restrict_use"):
                # Monitoring: measured displacement below Y_LIM (with error) or not.
                like, res_fav, res_unf = {}, {}, {}
                for t in TYPES:
                    x = draws[t]
                    st = x["stands"]
                    l_fav = norm.cdf((Y_LIM - x["y"]) / SIGMA_OBS)      # P(measured < Y_LIM | draw)
                    for out, lk in (("fav", l_fav), ("unf", 1 - l_fav)):
                        wgt = lk * st
                        target = res_fav if out == "fav" else res_unf
                        target[t] = {"pf": (wgt * x["fail"]).sum() / max(wgt.sum(), 1e-12)}
                        like[t, out] = wgt.sum() / N_MC          # P(stands and outcome | type)
                    row[f"y_median_mm_{t.replace(' ', '')}"] = round(1000 * np.median(x["y"][st]), 2)
                pf_fav, post_fav = mixture(res_fav, p2, {t: like[t, "fav"] for t in TYPES})
                pf_unf, post_unf = mixture(res_unf, p2, {t: like[t, "unf"] for t in TYPES})
                p_fav = (((1 - p2) * like["type 1", "fav"] + p2 * like["type 2", "fav"])
                         / ((1 - p2) * res["type 1"]["stands"] + p2 * res["type 2"]["stands"]))
                tag = "" if variant == "base" else "_restrict"
                row.update({f"monitor_p_fav{tag}": round(p_fav, 3),
                            f"beta_monitor_fav{tag}": round(beta(pf_fav), 3),
                            f"beta_monitor_unf{tag}": round(beta(pf_unf), 3),
                            f"p_type2_monitor_fav{tag}": round(post_fav, 3),
                            f"p_type2_monitor_unf{tag}": round(post_unf, 3)})
        rows.append(row)
        print(f"{wall['Naam']:30s} base {row['beta_base']:5.2f} service {row['beta_service_load']:5.2f}"
              f" prior-type {row['beta_prior_type']:5.2f} screen {row['beta_screen_failed']:5.2f}"
              f" no-friction {row['beta_no_friction']:5.2f} restrict {row['beta_restrict_use']:5.2f}"
              f" | monitor P(<{Y_LIM * 1000:.0f} mm) {row['monitor_p_fav']:.2f}:"
              f" {row['beta_monitor_fav']:5.2f} / {row['beta_monitor_unf']:5.2f}", flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)
    print()
    for col in ["service_load", "prior_type", "screen_failed", "no_friction", "restrict_use",
                "monitor_fav", "monitor_unf", "monitor_unf_restrict"]:
        for suffix in ("", "_type1", "_type2"):
            c = f"beta_{col}{suffix}"
            if c in d:
                db = d[c] - d[f"beta_base{suffix}"]
                print(f"{c:30s} change: median {db.median():+.2f}, {db.min():+.2f} to {db.max():+.2f};"
                      f" values {d[c].min():.2f} to {d[c].max():.2f}")
    print(f"monitoring: P(measured < {Y_LIM * 1000:.0f} mm) {d['monitor_p_fav'].min():.2f}"
          f" to {d['monitor_p_fav'].max():.2f}")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

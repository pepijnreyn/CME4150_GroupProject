"""Sensitivity of the walmuur failure probability to the dependence and input assumptions.

FailureProbability.py takes most inputs as independent and gives each wall one
soil class. This script reruns its Monte Carlo (FailureProbability.simulate) for
the same 17 walls with one change at a time and reports beta (updated with
proven strength, 2026):

  base                    the model as it is
  kgamma                  K and gamma_s correlated, rho = -0.5 (denser soil is
                          heavier and has a lower K), Gaussian copula
  more                    MOR and E correlated, rho = +0.8 (JCSS Probabilistic
                          Model Code, part 3.5)
  groundwater             groundwater under the werf Uniform(+0.6, +1.0) m NAP
                          instead of Uniform(+0.5, +0.9): from the canal level up
                          to about the werf
  soil_mixed              soil class uncertain: a mixture over the classes of the
                          DINO borings within 150 m (build_soil_type.py), updated
                          with proven strength like the wall type

It also gives, for type 2, how often overturning and pile failure happen
together, to show the dependence between the two limit states.

Writes data/processed/walmuur_sensitivity.csv.
Run: python3 scripts/StressCaclulation/SensitivityDependence.py   (about 25 minutes)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import build_soil_type as BST  # noqa: E402
import FailureProbability as FP  # noqa: E402
import PileStrength as PS  # noqa: E402
import SoilForce as SF  # noqa: E402

OUT = ROOT / "data" / "processed" / "walmuur_sensitivity.csv"

# ---- Inputs ----------------------------------------------------------------
N_MC = 200_000                  # draws per wall, type and variant
YEAR = 2026
RHO_K_GAMMA = -0.5
RHO_MOR_E = 0.8
GROUNDWATER_HIGH = (0.6, 1.0)   # [m NAP], uniform
# ----------------------------------------------------------------------------
FP.N_MC = N_MC
TYPES = ("type 1", "type 2")
BASE_SOIL, BASE_PILES, BASE_GROUNDWATER = FP.sample_soil, FP.sample_piles, FP.GROUNDWATER_NAP


def beta(pf):
    return -norm.ppf(max(pf, 0.5 / N_MC))


def soil_correlated(rho):
    """sample_soil with K (lognormal) and gamma_s (normal) correlated through a Gaussian copula."""
    def sample(soil_type, n, rng):
        s = SF.SOIL_TYPES[soil_type]
        sigma = np.sqrt(np.log(1 + s["K_cov"]**2))
        mu = np.log(s["K_mean"]) - sigma**2 / 2
        z1 = rng.standard_normal(n)
        z2 = rho * z1 + np.sqrt(1 - rho**2) * rng.standard_normal(n)
        return np.exp(mu + sigma * z1), s["gamma_mean"] * (1 + s["gamma_cov"] * z2)
    return sample


def piles_correlated(rho):
    """sample_piles with E drawn correlated to MOR (both normal)."""
    def sample(n, rng):
        p = BASE_PILES(n, rng)
        z1 = (p["MOR"] - PS.MOR_MEAN) / (PS.MOR_COV * PS.MOR_MEAN)
        z2 = rho * z1 + np.sqrt(1 - rho**2) * rng.standard_normal(n)
        p["E"] = np.maximum(PS.E_MEAN * (1 + PS.E_COV * z2), 0.1 * PS.E_MEAN)
        return p
    return sample


VARIANTS = {
    "base": {},
    "kgamma": {"sample_soil": soil_correlated(RHO_K_GAMMA)},
    "more": {"sample_piles": piles_correlated(RHO_MOR_E)},
    "groundwater": {"GROUNDWATER_NAP": GROUNDWATER_HIGH},
}


def use(variant):
    """Set FailureProbability to the base model, then apply the changes of `variant`."""
    FP.sample_soil, FP.sample_piles, FP.GROUNDWATER_NAP = BASE_SOIL, BASE_PILES, BASE_GROUNDWATER
    for name, value in VARIANTS[variant].items():
        setattr(FP, name, value)


def run(wall, section, seed):
    """One wall and type: chance it stands today, updated Pf and the two limit states."""
    x = FP.simulate(wall, section, np.random.default_rng(seed))
    fail = x["overturning"] | x[f"pile_{YEAR}"]
    stands = x["stands"]
    return {"stands": stands.mean(), "pf": fail.mean(),
            "pf_upd": (fail & stands).sum() / max(stands.sum(), 1),
            "overturning": x["overturning"].mean(), "pile": x[f"pile_{YEAR}"].mean(),
            "both": (x["overturning"] & x[f"pile_{YEAR}"]).mean()}


def updated_pf(results, prior):
    """Pf over the cases in `results`, each weighted by prior x P(stands | case)."""
    w = {case: prior[case] * r["stands"] for case, r in results.items()}
    return sum(w[case] / sum(w.values()) * results[case]["pf_upd"] for case in results)


def soil_weights(nummers):
    """Share of each soil class among the borings within 150 m of each walmuur."""
    borings = BST.read_borings()
    walls = BST.walls()
    out = {}
    for _, wall in walls[walls["Nummer"].isin(nummers)].iterrows():
        classes = []
        for b in borings:
            top = b["ground_nap"] - BST.WHARF_LEVEL_NAP
            share = BST.shares(b["layers"], top, top + BST.WALMUUR_H)
            if (share is not None and
                    BST.distance_m(wall["lon"], wall["lat"], b["lon"], b["lat"]) <= BST.NEARBY_M):
                classes.append(BST.soil_type(share))
        counts = pd.Series(classes).value_counts(normalize=True)
        out[wall["Nummer"]] = {c: float(counts.get(c, 0.0)) for c in SF.SOIL_TYPES}
    return out


def main() -> None:
    walls = FP.wall_table()
    walls = walls[(walls["status"] != "renewed") & walls["has_werf"].ne("no")]
    weights = soil_weights(walls["Nummer"])
    rows = []
    for i, (_, wall) in enumerate(walls.iterrows()):
        seeds = {t: 1000 + 10 * i + j for j, t in enumerate(TYPES)}
        p2 = wall["p_type2_prior"]
        prior_type = {"type 1": 1 - p2, "type 2": p2}
        row = {"Nummer": wall["Nummer"], "Naam": wall["Naam"], "soil_type": wall["soil_type"],
               **{f"w_{c}": round(w, 2) for c, w in weights[wall["Nummer"]].items()}}
        for variant in VARIANTS:
            use(variant)
            res = {t: run(wall, t, seeds[t]) for t in TYPES}
            row[f"beta_{variant}"] = beta(updated_pf(res, prior_type))
            for t in TYPES:
                row[f"beta_{variant}_{t.replace(' ', '')}"] = beta(res[t]["pf_upd"])
            if variant == "base":
                r2 = res["type 2"]
                row.update({"t2_pf_overturning": r2["overturning"], "t2_pf_pile": r2["pile"],
                            "t2_pf_both": r2["both"], "t2_pf": r2["pf"]})
        # Soil class uncertain: every class with nearby borings, both types.
        use("base")
        res, prior = {}, {}
        for c, wc in weights[wall["Nummer"]].items():
            if wc > 0:
                w = wall.copy()
                w["soil_type"] = c
                for t in TYPES:
                    res[t, c] = run(w, t, seeds[t])
                    prior[t, c] = prior_type[t] * wc
        row["beta_soil_mixed"] = beta(updated_pf(res, prior))
        rows.append(row)
        print(f"{wall['Naam']:38s} beta base {row['beta_base']:5.2f}  K-gamma {row['beta_kgamma']:5.2f}"
              f"  MOR-E {row['beta_more']:5.2f}  groundwater {row['beta_groundwater']:5.2f}"
              f"  soil mixed {row['beta_soil_mixed']:5.2f}", flush=True)

    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)
    print()
    for v in ["kgamma", "more", "groundwater", "soil_mixed"]:
        for suffix in ["", "_type1", "_type2"]:
            col = f"beta_{v}{suffix}"
            if col in d:
                db = d[col] - d[f"beta_base{suffix}"]
                print(f"{col:28s} change: median {db.median():+.2f}, {db.min():+.2f} to {db.max():+.2f}")
    ratio = d["t2_pf_both"] / (d["t2_pf_overturning"] * d["t2_pf_pile"]).replace(0, np.nan)
    indep = 1 - (1 - d["t2_pf_overturning"]) * (1 - d["t2_pf_pile"])
    print(f"type 2: both limit states together {ratio.median():.1f} times as often as if independent;"
          f" series Pf within {((indep - d['t2_pf']) / d['t2_pf']).abs().max():.0%} of the independent value")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

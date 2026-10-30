"""One-at-a-time (tornado) sensitivity of the walmuur failure probability to each input.

FailureProbability.py draws 18 inputs per wall. This script reruns its Monte
Carlo (FailureProbability.simulate) for the same 17 walls with one input fixed
at a time, at the 5% and at the 95% value of its distribution, and reports
beta (updated with proven strength) per wall type and for the best estimate,
in 2026 and 2041. Fixing an input stands for measuring it: the swing between
the two values shows how much knowing that input could change beta.

The soil class is fixed to each of the three classes in turn, and the wall
type is the difference between the two types, which every run gives anyway.
A last run fixes all inputs in REDUCED at their median at once, to show what
leaving them out of the Monte Carlo would change.

Every run of a wall and type uses the same seed, and a fixed input still uses
up its random numbers, so all other inputs get the same draws in every run.
The differences between runs are therefore not Monte Carlo noise.

Writes data/processed/walmuur_tornado.csv: one row per wall, input and level
(base, low, high, or a soil class).
Run: python3 scripts/StressCaclulation/SensitivityTornado.py   (about 15 minutes)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import FailureProbability as FP  # noqa: E402
import PileStrength as PS  # noqa: E402
import SoilForce as SF  # noqa: E402
import TraficLoad as TL  # noqa: E402
import WallResistance as WR  # noqa: E402

OUT = ROOT / "data" / "processed" / "walmuur_tornado.csv"

# ---- Inputs ----------------------------------------------------------------
N_MC = 100_000                  # draws per wall, type and run
P_LOW, P_HIGH = 0.05, 0.95      # the two fixed values of each input
# Inputs whose swing stayed below 0.2 for both types in a first run, fixed together;
# the werf level only where AHN measured it.
REDUCED = ("werf", "gamma_c", "gamma_s", "E", "k", "rate")
# ----------------------------------------------------------------------------
FP.N_MC = N_MC
TYPES = ("type 1", "type 2")
BASE = {name: getattr(FP, name) for name in
        ("sample_soil", "sample_piles", "sample_surcharge", "sample_wall", "lognormal",
         "GROUNDWATER_NAP", "DZ", "NO_WERF", "WERF_SD", "GAMMA_C_MEAN", "GAMMA_C_COV")}

# Input: (label, distribution in FailureProbability). Pile inputs are keys of
# PileStrength.sample_piles.
INPUTS = {
    "werf": ("Werf level", f"N(AHN, {FP.WERF_SD} m); U{FP.NO_WERF} m NAP if assumed"),
    "dz": ("Foundation level", f"drawing + U{FP.DZ} m"),
    "theta_R": ("Model factor on M_R", f"LN(1, {FP.THETA_R_COV})"),
    "gamma_m": ("Unit weight masonry", f"N({WR.GAMMA_M_MEAN} kN/m3, {WR.GAMMA_M_COV})"),
    "gamma_c": ("Unit weight tamped concrete", f"N({WR.GAMMA_C_MEAN} kN/m3, {WR.GAMMA_C_COV})"),
    "K": ("Earth pressure coefficient K", "LN per soil class"),
    "gamma_s": ("Unit weight soil", "N per soil class"),
    "groundwater": ("Groundwater level", f"U{BASE['GROUNDWATER_NAP']} m NAP"),
    "q": ("Surcharge q", f"N({TL.Q_MEAN} kPa, {TL.Q_COV})"),
    "a": ("Distance a of the surcharge", f"U({TL.A_MIN}, {TL.A_MAX}) m"),
    "D0": ("Pile diameter D0", f"N({PS.D0_MEAN * 1000:.0f} mm, {PS.D0_COV})"),
    "s": ("Pile spacing", f"U{PS.SPACING} m"),
    "shell": ("Soft shell today", f"U(0, {PS.SHELL_NOW[1] * 1000:.0f}) mm"),
    "rate": ("Shell growth", f"U({PS.RATE[0] * 1000:.2f}, {PS.RATE[1] * 1000:.2f}) mm/yr"),
    "MOR": ("Bending strength MOR", f"N({PS.MOR_MEAN / 1000:g} MPa, {PS.MOR_COV})"),
    "E": ("Modulus of elasticity E", f"N({PS.E_MEAN / 1e6:g} GPa, {PS.E_COV})"),
    "k": ("Subgrade modulus k", f"U({PS.K_SUBGRADE[0]:g}, {PS.K_SUBGRADE[1]:g}) kN/m3"),
    "theta_M": ("Model factor on the pile moment", f"LN(1, {PS.THETA_M_COV})"),
}
PILE_DIST = {"D0": ("normal", PS.D0_MEAN, PS.D0_COV), "s": ("uniform", PS.SPACING),
             "shell": ("uniform", PS.SHELL_NOW), "rate": ("uniform", PS.RATE),
             "MOR": ("normal", PS.MOR_MEAN, PS.MOR_COV), "E": ("normal", PS.E_MEAN, PS.E_COV),
             "k": ("uniform", PS.K_SUBGRADE), "theta_M": ("lognormal", 1.0, PS.THETA_M_COV)}


def quantile(dist, p):
    """p-quantile of ("normal", mean, cov), ("lognormal", mean, cov) or ("uniform", (lo, hi))."""
    if dist[0] == "uniform":
        lo, hi = dist[1]
        return lo + p * (hi - lo)
    mean, cov = dist[1], dist[2]
    if dist[0] == "normal":
        return mean * (1 + cov * norm.ppf(p))
    sigma = np.sqrt(np.log(1 + cov**2))
    return mean * np.exp(-sigma**2 / 2 + sigma * norm.ppf(p))


def replace(sampler, index, value):
    """A sampler that draws as `sampler` does, then sets output `index` to `value`.

    It still draws the input it replaces, so the other inputs keep their draws.
    """
    def sample(*args):
        out = sampler(*args)
        if isinstance(out, dict):
            out = {**out, index: np.full(len(out[index]), value)}
        elif isinstance(out, tuple):
            out = tuple(np.full(len(v), value) if i == index else v for i, v in enumerate(out))
        else:
            out = np.full(len(out), value)
        return out
    return sample


def fix(name, p, wall, changes=None):
    """Input `name` at its p-quantile: (value, changes to FailureProbability, wall).

    `changes` from an earlier call are kept, so several inputs can be fixed at once.
    """
    changes = dict(changes or {})
    soil = SF.SOIL_TYPES[wall["soil_type"]]

    def wrap(attr, index, value):
        changes[attr] = replace(changes.get(attr, BASE[attr]), index, value)
        return value, changes, wall

    # Read the distributions from BASE: FailureProbability may still hold the
    # changes of the previous run.
    if name == "werf" and wall["werf"] == "yes":
        wall = wall.copy()
        wall["werf_nap"] = wall["werf_nap"] + BASE["WERF_SD"] * norm.ppf(p)
        return wall["werf_nap"], {**changes, "WERF_SD": 0.0}, wall
    if name == "werf":
        v = quantile(("uniform", BASE["NO_WERF"]), p)
        return v, {**changes, "NO_WERF": (v, v)}, wall
    if name in ("dz", "groundwater"):
        attr = {"dz": "DZ", "groundwater": "GROUNDWATER_NAP"}[name]
        v = quantile(("uniform", BASE[attr]), p)
        return v, {**changes, attr: (v, v)}, wall
    if name == "theta_R":
        return wrap("lognormal", 0, quantile(("lognormal", 1.0, FP.THETA_R_COV), p))
    if name == "gamma_m":
        return wrap("sample_wall", 0, quantile(("normal", WR.GAMMA_M_MEAN, WR.GAMMA_M_COV), p))
    if name == "gamma_c":
        v = quantile(("normal", WR.GAMMA_C_MEAN, WR.GAMMA_C_COV), p)
        return v, {**changes, "GAMMA_C_MEAN": v, "GAMMA_C_COV": 0.0}, wall
    if name == "K":
        return wrap("sample_soil", 0, quantile(("lognormal", soil["K_mean"], soil["K_cov"]), p))
    if name == "gamma_s":
        return wrap("sample_soil", 1, quantile(("normal", soil["gamma_mean"], soil["gamma_cov"]), p))
    if name == "q":
        return wrap("sample_surcharge", 0, quantile(("normal", TL.Q_MEAN, TL.Q_COV), p))
    if name == "a":
        return wrap("sample_surcharge", 1, quantile(("uniform", (TL.A_MIN, TL.A_MAX)), p))
    return wrap("sample_piles", name, quantile(PILE_DIST[name], p))


def beta(pf):
    return -norm.ppf(max(pf, 0.5 / N_MC))


def use(changes):
    """Set FailureProbability to the base model, then apply `changes`."""
    for name, value in {**BASE, **changes}.items():
        setattr(FP, name, value)


def run(wall, seeds, changes):
    """Updated beta per type and for the best estimate, in both years, for one set of changes."""
    use(changes)
    pf, stands = {}, {}
    for t in TYPES:
        x = FP.simulate(wall, t, np.random.default_rng(seeds[t]))
        stands[t] = x["stands"].mean()
        for year in FP.YEARS:
            fail = x["overturning"] | x[f"pile_{year}"]
            pf[t, year] = (fail & x["stands"]).sum() / max(x["stands"].sum(), 1)
    p2 = wall["p_type2_prior"]
    w2 = p2 * stands["type 2"]
    post2 = w2 / (w2 + (1 - p2) * stands["type 1"])
    row = {"p_type2": round(post2, 3)}
    for year in FP.YEARS:
        row[f"beta_type1_{year}"] = beta(pf["type 1", year])
        row[f"beta_type2_{year}"] = beta(pf["type 2", year])
        row[f"beta_{year}"] = beta((1 - post2) * pf["type 1", year] + post2 * pf["type 2", year])
    return row


def main() -> None:
    walls = FP.wall_table()
    walls = walls[(walls["status"] != "renewed") & walls["has_werf"].ne("no")]
    rows = []
    for i, (_, wall) in enumerate(walls.iterrows()):
        seeds = {t: 2000 + 10 * i + j for j, t in enumerate(TYPES)}
        base = {"Nummer": wall["Nummer"], "Naam": wall["Naam"], "soil_type": wall["soil_type"]}
        rows.append({**base, "input": "base", "level": "base", "value": None,
                     **run(wall, seeds, {})})
        for name in INPUTS:
            for level, p in (("low", P_LOW), ("high", P_HIGH)):
                value, changes, w = fix(name, p, wall)
                rows.append({**base, "input": name, "level": level, "value": value,
                             **run(w, seeds, changes)})
        for soil in SF.SOIL_TYPES:
            w = wall.copy()
            w["soil_type"] = soil
            rows.append({**base, "input": "soil_class", "level": soil, "value": None,
                         **run(w, seeds, {})})
        changes, w = {}, wall
        for name in REDUCED:
            if name == "werf" and wall["werf"] != "yes":
                continue        # an assumed werf range is not measurement noise
            _, changes, w = fix(name, 0.5, w, changes)
        rows.append({**base, "input": "reduced", "level": "median", "value": None,
                     **run(w, seeds, changes)})
        print(f"{wall['Naam']:38s} done", flush=True)
    use({})

    d = pd.DataFrame(rows)
    d.to_csv(OUT, index=False)
    print()
    for year in FP.YEARS:
        print(f"{year}: change of beta from the 5% to the 95% value, median over the walls [min, max]")
        swings = []
        for name, (label, dist) in INPUTS.items():
            lo = d[(d["input"] == name) & (d["level"] == "low")].set_index("Nummer")
            hi = d[(d["input"] == name) & (d["level"] == "high")].set_index("Nummer")
            s = {c: hi[f"beta{c}_{year}"] - lo[f"beta{c}_{year}"] for c in ("", "_type1", "_type2")}
            swings.append((s[""].abs().median(), label, dist, s))
        for _, label, dist, s in sorted(swings, key=lambda x: x[0], reverse=True):
            print(f"  {label:32s} {dist:42s}" + "".join(
                f"  {c.strip('_') or 'best':5s} {v.median():+.2f} [{v.min():+.2f}, {v.max():+.2f}]"
                for c, v in s.items()))
        by_class = d[d["input"] == "soil_class"].groupby("Nummer")[f"beta_{year}"]
        sw = by_class.max() - by_class.min()
        b = d[d["input"] == "base"].set_index("Nummer")
        tw = b[f"beta_type2_{year}"] - b[f"beta_type1_{year}"]
        print(f"  {'Soil class (three classes)':32s} highest - lowest: median {sw.median():.2f}"
              f" [{sw.min():.2f}, {sw.max():.2f}]")
        print(f"  {'Wall type':32s} type 2 - type 1: median {tw.median():.2f}"
              f" [{tw.min():.2f}, {tw.max():.2f}]")
        r = d[d["input"] == "reduced"].set_index("Nummer")
        print(f"  {'Fixed together: ' + ', '.join(REDUCED):32s}" + "".join(
            f"  {c.strip('_') or 'best':5s} {v.median():+.2f} [{v.min():+.2f}, {v.max():+.2f}]"
            for c in ("", "_type1", "_type2")
            for v in [r[f"beta{c}_{year}"] - b[f"beta{c}_{year}"]]))
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

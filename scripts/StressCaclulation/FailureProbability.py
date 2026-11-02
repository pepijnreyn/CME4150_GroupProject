"""Failure probability of the walmuren that still stand on their old timber foundation.

For every walmuur that is not renewed (status not renewed, in progress or
unclear in walmuur_foundation.csv), a Monte Carlo of two limit states, for both
wall types of WallResistance.SECTIONS:

  overturning  the wall, its floor and the soil on it tip about the front pile
               row: M_R + M_delta < S_total (WallResistance, TotalStress)
  pile         the rotted pile heads bend under the horizontal force that the
               raked front row does not take (PileStrength)

A wall fails when either happens. Pf = failures / draws, beta = -Phi^-1(Pf).
The pile heads keep rotting, so Pf is given now (2026) and at the end of a
15-year reference period (2041, NEN 8700). The wall type is not known per wall.
"unknown" (the best estimate) weighs the types per rak by what TNO's divers found
in 2008 (data/raw/walmuur_tno2009_type.csv): a watersloof, the timber beam that
only type 1 has, makes type 2 unlikely (20%); a concrete floor makes it likely
(90%); both gives 50%; a rak without a hint gets 80%, since report 156 calls the
usual walmuren of the 1960s largely concrete.

Proven strength (Hemel et al. 2024, eq. 12; docs/failure_formula_notes.md
section 6): every one of these walls stands today under its own soil and water,
without surcharge. Draws in which it would already have failed under that load
cannot be the real wall, so the updated Pf counts only the draws that pass that
check: Pf|stands = P(fail and stands) / P(stands). The same evidence updates
the type: P(type | stands) is proportional to P(type) P(stands | type).

Per wall from the data: werf level (AHN, walmuur_height.csv), soil type (DINO,
masonry_walls_soil.csv) and the chance of each wall type. The condition of the
piles is not known per wall: every wall gets the same broad soft shell
(PileStrength.SHELL_NOW). Everything else is one guess with a distribution for
all walls; INPUTS below lists each one and its source.

Walls marked "no werf? check map" in walmuur_height.csv get an assumed werf level
until they are checked on a map in data/raw/walmuur_werf_check.csv: has_werf
"yes" with a werf_nap uses that level, "yes" without one keeps the assumption,
and "no" (the street runs to the water) leaves the wall out, since the low
walmuur sections do not describe it.

How the forces reach the piles: the rear row carries (M_R - S) / a, the rest of
the weight goes to the front row. The front row of type 2 is raked 10:1, so it
takes a tenth of its vertical force horizontally; the rest of the horizontal
force bends the piles, shared by both rows.

Writes
  data/processed/walmuur_failure_probability.csv   per walmuur, type and year
  data/processed/walmuur_failure_draws.json         a sample of draws per wall and type
  data/processed/walmuur_failure_inputs.csv         every input and its distribution
Run: python3 scripts/StressCaclulation/FailureProbability.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from PileStrength import (D0_COV, D0_MEAN, E_COV, E_MEAN, K_SUBGRADE, MOR_COV, MOR_MEAN,
                          RATE, SHELL_NOW, SPACING, THETA_M_COV, head_moment, pile_stress,
                          remaining_diameter, sample_piles)
from SoilForce import sample_soil, soil_force
from TotalStress import total_stress
from TraficLoad import A_MAX, A_MIN, Q_COV, Q_MEAN, sample_surcharge, surcharge_force
from WallResistance import (GAMMA_C_COV, GAMMA_C_MEAN, GAMMA_M_COV, GAMMA_M_MEAN, GAMMA_RC,
                            GAMMA_TIMBER, SECTIONS, friction_tan, sample_wall,
                            section_resistance)
from WaterLoad import CANAL_NAP, GROUNDWATER_NAP, water_force

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from screening import load, walmuren, with_renewals  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
TNO_TYPE = ROOT / "data" / "raw" / "walmuur_tno2009_type.csv"
WERF_CHECK = ROOT / "data" / "raw" / "walmuur_werf_check.csv"
OUT = PROCESSED / "walmuur_failure_probability.csv"
OUT_DRAWS = PROCESSED / "walmuur_failure_draws.json"
OUT_INPUTS = PROCESSED / "walmuur_failure_inputs.csv"

# ---- Inputs ----------------------------------------------------------------
# The canal level and the groundwater under the werf are set in WaterLoad.py.
WERF_SD = 0.05                  # werf level ~ N(AHN median, 0.05) [m]
NO_WERF = (1.0, 1.6)            # werf assumed for walls marked "no werf? check map" [m NAP]
DZ = (-0.15, 0.15)              # foundation level against the drawing [m], uniform
THETA_R_COV = 0.15              # model factor on the resisting moment, lognormal
YEARS = (2026, 2041)            # now, and the end of the 15-year reference period
P_TYPE2 = 0.8                   # chance of type 2 in a rak without a TNO hint
N_MC = 400_000                  # draws per wall and type
N_PLOT = 600                    # draws per wall and type kept for the scatter plots
SEED = 1
# ----------------------------------------------------------------------------
SOIL_LABELS = {"soft_clay_peat": "soft clay / peat", "mixed": "mixed", "sand": "sand"}

INPUTS = [
    # (input, distribution, per wall?, source)
    ("Werf level", f"Normal(AHN median, {WERF_SD} m)", "yes",
     "AHN dtm_05m, build_walmuur_height.py"),
    ("Werf level, walls marked [h]", f"Uniform({NO_WERF[0]}, {NO_WERF[1]}) m NAP", "yes",
     "guess: the range of the measured werven; replaced once checked on a map"),
    ("Werf level, walls checked on a map", f"Normal(level read, {WERF_SD} m)", "yes",
     "data/raw/walmuur_werf_check.csv, filled in by hand"),
    ("Soil type (K, gamma_s)", "per SOIL_TYPES in SoilForce.py", "yes",
     "DINO borings, build_soil_type.py; K and gamma_s: team judgement (report Table A.6)"),
    ("Wall type", "chance of type 2 per rak: 20% where TNO found a watersloof, 90% where it "
     f"found a concrete floor, 50% for both, {P_TYPE2:.0%} without a hint", "yes",
     "TNO-034-DTM-2009-01978 Bijlage G (walmuur_tno2009_type.csv); IBU note pp. 4-5; "
     "report 156 p. 23"),
    ("Cross-section", "measured polygons, WallResistance.SECTIONS", "no",
     "Erfgoed Utrecht report 156 Afb. 3.1 (type 2); IBU note Afb. 2.1.1a (type 1)"),
    ("Foundation level", f"drawing + Uniform({DZ[0]}, {DZ[1]}) m", "no",
     "guess: schematic drawings; report 158 gives -0.08 m NAP for the wall underside"),
    ("Model factor on M_R", f"Lognormal(1, CoV {THETA_R_COV})", "no", "guess"),
    ("Masonry", f"Normal({GAMMA_M_MEAN} kN/m3, CoV {GAMMA_M_COV})", "no", "typical value"),
    ("Tamped concrete", f"Normal({GAMMA_C_MEAN} kN/m3, CoV {GAMMA_C_COV})", "no",
     "typical value"),
    ("Reinforced concrete", f"{GAMMA_RC} kN/m3", "no", "typical value"),
    ("Timber floor", f"{GAMMA_TIMBER} kN/m3", "no", "waterlogged pine"),
    ("Wall friction", "delta = 2/3 phi, phi from K", "no", "Rankine; common practice"),
    ("Canal level", f"{CANAL_NAP} m NAP", "no", "Erfgoed Utrecht report 158"),
    ("Groundwater under the werf",
     f"Uniform({GROUNDWATER_NAP[0]}, {GROUNDWATER_NAP[1]}) m NAP", "no",
     "guess around the canal level"),
    ("Surcharge q", f"Normal({Q_MEAN} kPa, CoV {Q_COV})", "no", "Hemel et al. (2024)"),
    ("Distance a to the load", f"Uniform({A_MIN}, {A_MAX}) m", "no", "guess"),
    ("Pile diameter D0", f"Normal({D0_MEAN * 1000:.0f} mm, CoV {D0_COV})", "no",
     "IBU note p. 4 (180 mm); CoV Hemel (2023) Table 7.1"),
    ("Pile spacing along the wall", f"Uniform({SPACING[0]}, {SPACING[1]}) m", "no",
     "IBU note p. 4: 'ca. 1 meter'"),
    ("Soft shell of the piles today",
     f"Uniform({SHELL_NOW[0] * 1000:.0f}, {SHELL_NOW[1] * 1000:.0f}) mm", "no",
     "Hemel (2023) chapter 3: 21 mm on average, up to 45 mm"),
    ("Proven strength", "the wall stands today under soil and water, no surcharge", "no",
     "Hemel et al. (2024) eq. 12"),
    ("Soft-shell growth after 2026",
     f"Uniform({RATE[0] * 1000:.2f}, {RATE[1] * 1000:.2f}) mm/yr", "no",
     "Hemel (2023) 7.3.2: 0.17 mm/yr; range is a guess"),
    ("Bending strength MOR", f"Normal({MOR_MEAN / 1000:g} MPa, CoV {MOR_COV})", "no",
     "Hemel (2023) Table 7.1"),
    ("Modulus of elasticity", f"Normal({E_MEAN / 1e6:g} GPa, CoV {E_COV})", "no",
     "Hemel (2023) Table 7.1"),
    ("Subgrade modulus k", f"Uniform({K_SUBGRADE[0]:g}, {K_SUBGRADE[1]:g}) kN/m3", "no",
     "Hemel (2023) Table 7.1, clay and peat"),
    ("Model factor on the pile moment", f"Lognormal(1, CoV {THETA_M_COV})", "no",
     "JCSS, as Hemel et al. (2024)"),
]


def lognormal(rng, cov, n):
    sigma = np.sqrt(np.log(1 + cov**2))
    return rng.lognormal(-sigma**2 / 2, sigma, n)


def beta(pf):
    """Reliability index; with no failures in the draws, the bound for half a failure."""
    return -norm.ppf(max(pf, 0.5 / N_MC))


def wall_table() -> pd.DataFrame:
    """The 51 walmuren with screening, foundation, werf level, soil and chance of type 2."""
    w = with_renewals(walmuren(load()))[["Nummer", "group", "cls", "Lengte"]]
    f = pd.read_csv(PROCESSED / "walmuur_foundation.csv")[["Nummer", "Naam", "rak", "side", "status"]]
    h = pd.read_csv(PROCESSED / "walmuur_height.csv")[["Nummer", "werf_nap", "werf"]]
    s = pd.read_csv(PROCESSED / "masonry_walls_soil.csv")[["Nummer", "soil_type"]]
    walls = f.merge(w, on="Nummer").merge(h, on="Nummer").merge(s, on="Nummer")
    walls["werf_source"] = np.where(walls["werf"] == "yes", "AHN", "assumed")

    t = pd.read_csv(TNO_TYPE).rename(columns={"found": "type_hint", "p_type2": "p_type2_prior"})
    walls["rak"] = walls["rak"].astype("Int64")
    walls = walls.merge(t[["rak", "type_hint", "p_type2_prior"]].astype({"rak": "Int64"}),
                        on="rak", how="left")
    walls["type_hint"] = walls["type_hint"].fillna("no TNO hint")
    walls["p_type2_prior"] = walls["p_type2_prior"].fillna(P_TYPE2)

    walls["has_werf"] = ""
    if WERF_CHECK.exists():
        c = pd.read_csv(WERF_CHECK, dtype=str).fillna("")
        checked = dict(zip(c["Nummer"], zip(c["has_werf"].str.strip().str.lower(), c["werf_nap"])))
        walls["has_werf"] = walls["Nummer"].map(lambda n: checked.get(n, ("", ""))[0])
        level = walls["Nummer"].map(lambda n: checked.get(n, ("", ""))[1])
        seen = walls["has_werf"].eq("yes") & level.ne("")
        walls.loc[seen, "werf_nap"] = level[seen].astype(float)
        walls.loc[seen, "werf"] = "yes"
        walls.loc[seen, "werf_source"] = "map check"
    return walls


def simulate(wall: pd.Series, section: str, rng) -> dict:
    """Draws of one wall for one cross-section type, before and after the evidence."""
    s = SECTIONS[section]
    n = N_MC
    # What stays the same over time: the wall, its soil and its piles.
    werf = (rng.normal(wall["werf_nap"], WERF_SD, n) if wall["werf"] == "yes"
            else rng.uniform(*NO_WERF, n))
    dz = rng.uniform(*DZ, n)
    K, gamma_s = sample_soil(wall["soil_type"], n, rng)
    gamma_m, _ = sample_wall(n, rng)
    gammas = {"masonry": gamma_m, "rc": GAMMA_RC, "timber": GAMMA_TIMBER, "soil": gamma_s,
              "concrete": rng.normal(GAMMA_C_MEAN, GAMMA_C_COV * GAMMA_C_MEAN, n)}
    theta_R = lognormal(rng, THETA_R_COV, n)
    p = sample_piles(n, rng)
    H = werf - (s["base"] + dz)
    x_front, x_rear = s["piles"]

    def event(q, a, gw):
        """Overturning and the forces on one pile, for one load event."""
        d_w, d_c = werf - gw, werf - CANAL_NAP
        S = total_stress(K, gamma_s, q, a, H, d_w, d_c)
        F_soil = soil_force(K, gamma_s, H, d_w) + surcharge_force(K, q, a, H)
        F_h = F_soil + water_force(H, d_w, d_c)
        V, M = section_resistance(section, werf, dz, (CANAL_NAP + gw) / 2, gammas)
        F_v = friction_tan(K) * F_soil        # wall friction on the back of the body
        M_R = theta_R * M + F_v * (s["back"] - x_front)
        rear = (M_R - S) / (x_rear - x_front)
        front = np.maximum(V + F_v - rear, 0)
        H_rest = np.maximum(F_h - s["rake"] * front, 0)
        return {"S": S, "M_R": M_R, "overturning": M_R < S,
                "P": H_rest * p["s"] / 2,
                "N": front * np.sqrt(1 + s["rake"]**2) * p["s"]}

    def pile(e, year):
        """Sound core diameter and stress over MOR of the front pile in `year`."""
        d = remaining_diameter(p["D0"], p["shell"], p["rate"], year)
        core = np.maximum(d, 0.02)
        M = head_moment(e["P"], core, p["D0"], p["E"], p["k"], s["fixed_head"])
        ratio = np.where(d > 0.02, pile_stress(M, e["N"], core, p["theta_M"]) / p["MOR"], np.inf)
        return d, ratio

    # The evidence: the wall stands today under soil and water, without surcharge.
    zero = np.zeros(n)
    today = event(zero, zero, rng.uniform(*GROUNDWATER_NAP, n))
    _, ratio_today = pile(today, YEARS[0])
    stands = ~today["overturning"] & (ratio_today <= 1)

    q, a = sample_surcharge(n, rng)
    e = event(q, a, rng.uniform(*GROUNDWATER_NAP, n))
    out = {"S": e["S"], "M_R": e["M_R"], "overturning": e["overturning"], "K": K, "H": H,
           "stands": stands}
    for year in YEARS:
        d, ratio = pile(e, year)
        out[f"d_{year}"], out[f"ratio_{year}"], out[f"pile_{year}"] = d, ratio, ratio > 1
    return out


def main() -> None:
    rng = np.random.default_rng(SEED)
    walls = wall_table()
    computed = (walls["status"] != "renewed") & walls["has_werf"].ne("no")
    old = walls[computed]
    rows, draws = [], []
    for _, wall in old.iterrows():
        base = {"Nummer": wall["Nummer"], "Naam": wall["Naam"], "canal": wall["group"],
                "rak": wall["rak"], "screening": wall["cls"], "status": wall["status"],
                "length_m": round(wall["Lengte"], 1),
                "werf_nap": round(wall["werf_nap"], 2) if wall["werf"] == "yes" else None,
                "werf_assumed": wall["werf"] != "yes", "werf_source": wall["werf_source"],
                "soil_type": wall["soil_type"], "soil": SOIL_LABELS[wall["soil_type"]],
                "type_hint": wall["type_hint"], "p_type2_prior": wall["p_type2_prior"]}
        pf, stands = {}, {}
        keep = rng.choice(N_MC, N_PLOT, replace=False)
        for section in SECTIONS:
            x = simulate(wall, section, rng)
            stands[section] = x["stands"].mean()
            for year in YEARS:
                fail = x["overturning"] | x[f"pile_{year}"]
                pf_upd = (fail & x["stands"]).sum() / max(x["stands"].sum(), 1)
                pf[section, year] = fail.mean(), pf_upd
                rows.append({**base, "type": section, "year": year,
                             "H_mean_m": round(x["H"].mean(), 2),
                             "p_stands": round(x["stands"].mean(), 4),
                             "pf_overturning": x["overturning"].mean(),
                             "pf_pile": x[f"pile_{year}"].mean(),
                             "pf": fail.mean(), "beta": round(beta(fail.mean()), 2),
                             "pf_updated": pf_upd, "beta_updated": round(beta(pf_upd), 2)})
            for i in keep:
                draws.append({"Nummer": wall["Nummer"], "type": section,
                              "S": round(float(x["S"][i]), 2), "M_R": round(float(x["M_R"][i]), 2),
                              "K": round(float(x["K"][i]), 3), "H": round(float(x["H"][i]), 2),
                              "stands": int(x["stands"][i]),
                              **{f"d_{y}": round(float(x[f"d_{y}"][i]) * 1000, 1) for y in YEARS},
                              **{f"ratio_{y}": round(min(float(x[f"ratio_{y}"][i]), 9.99), 3)
                                 for y in YEARS}})
        # Unknown type: before the evidence the chance of the rak, after it weighted by
        # P(stands | type).
        p2 = wall["p_type2_prior"]
        w2 = p2 * stands["type 2"]
        post2 = w2 / (w2 + (1 - p2) * stands["type 1"])
        for year in YEARS:
            prior = (1 - p2) * pf["type 1", year][0] + p2 * pf["type 2", year][0]
            upd = (1 - post2) * pf["type 1", year][1] + post2 * pf["type 2", year][1]
            rows.append({**base, "type": "unknown", "year": year, "p_type2": round(post2, 3),
                         "pf": prior, "beta": round(beta(prior), 2),
                         "pf_updated": upd, "beta_updated": round(beta(upd), 2)})
        now = {r["type"]: r for r in rows if r["Nummer"] == wall["Nummer"] and r["year"] == YEARS[0]}
        print(f"{wall['Naam']:38s} {YEARS[0]} beta (updated) type 1 "
              f"{now['type 1']['beta']:5.2f} ({now['type 1']['beta_updated']:5.2f}), type 2 "
              f"{now['type 2']['beta']:5.2f} ({now['type 2']['beta_updated']:5.2f}), unknown "
              f"{now['unknown']['beta']:5.2f} ({now['unknown']['beta_updated']:5.2f}), "
              f"P(type 2) {p2:.2f} -> {post2:.2f}")
    for _, wall in walls[~computed].iterrows():
        rows.append({"Nummer": wall["Nummer"], "Naam": wall["Naam"], "canal": wall["group"],
                     "rak": wall["rak"], "screening": wall["cls"], "status": wall["status"],
                     "length_m": round(wall["Lengte"], 1), "type": "not computed",
                     "reason": "renewed" if wall["status"] == "renewed" else "no werf"})

    table = pd.DataFrame(rows).astype({"year": "Int64"})
    # One key per row, for tables that pick a type and a year.
    table.insert(0, "row", table["Nummer"] + " " + table["type"]
                 + table["year"].map(lambda y: "" if pd.isna(y) else f" {int(y)}"))
    pf_cols = ["pf_overturning", "pf_pile", "pf", "pf_updated"]
    table[pf_cols] = table[pf_cols].round(6)
    table.to_csv(OUT, index=False)
    OUT_DRAWS.write_text(json.dumps(draws, separators=(",", ":")))
    pd.DataFrame(INPUTS, columns=["input", "distribution", "per_wall", "source"]).to_csv(
        OUT_INPUTS, index=False)
    print(f"\n{len(old)} walls computed, {len(walls) - len(old)} not ->"
          f" {OUT.relative_to(ROOT)}, {OUT_DRAWS.relative_to(ROOT)}, {OUT_INPUTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""Total load on a retaining wall: soil load plus water load plus surcharge load.

S_total = S_soil + S_water + S_q                                    [kNm/m]

    S_soil  = K (gamma_s H^3 - gamma_w h_w^3) / 6     effective soil weight
    S_water = gamma_w (h_w^3 - h_c^3) / 6             groundwater minus canal water
    S_q     = 1/2 K q_eff H^2                         surcharge

with h_w = H - d_w and h_c = H - d_c the heights of the groundwater and the
canal water above the base (see WaterLoad.py for the derivation).

S_soil and S_q use the same K, because the same soil carries its own weight and
spreads the surcharge. S_soil and S_water use the same groundwater depth d_w.
In the Monte Carlo every draw samples K, gamma_s, q, a and d_w once and uses
them in all terms. The canal level d_c is fixed.

Run: python3 scripts/StressCaclulation/TotalStress.py
"""

import numpy as np

from SoilForce import SOIL_TYPES, sample_soil, soil_stress
from TraficLoad import sample_surcharge, surcharge_moment
from WaterLoad import D_C, D_GHG, D_GLG, sample_groundwater, water_stress

# ---- Inputs ----------------------------------------------------------------
# K and gamma_s per soil type are set in SOIL_TYPES in SoilForce.py.
# The groundwater (D_GHG, D_GLG) and canal (D_C) depths below the werf are set in WaterLoad.py.
# H is the median for the 38 walmuren with a werf in data/processed/walmuur_height.csv
# (0.99 to 1.48 m): werf level (AHN) to the canal bed, taken at the wall underside
# (-0.08 m NAP, Erfgoed Utrecht report 158). The bed may be deeper.
H = 1.21                    # retained soil height, werf to canal bed [m]
Q_MEAN, Q_COV = 7.0, 0.20   # surcharge q, normal [kPa]; Q_COV = 0 fixes q
A_MIN, A_MAX = 0.0, 3.0     # distance wall to load a, uniform [m]; A_MIN = A_MAX fixes a
WATER = True                # False = no groundwater and no canal water (dry soil)
N_MC = 100_000              # Monte Carlo draws per soil type
SEED = 1                    # same seed gives the same draws
# ----------------------------------------------------------------------------


def total_stress(K, gamma_soil, q, a, H, d_w=np.inf, d_c=np.inf):
    """S_total [kNm/m], for single values or arrays of draws. Default depths: dry."""
    return (soil_stress(K, gamma_soil, H, d_w) + water_stress(H, d_w, d_c)
            + surcharge_moment(K, q, a, H))


def sample_inputs(soil_type, n, rng):
    """Draw n values of every random input for a soil type, with the inputs above."""
    K, gamma = sample_soil(soil_type, n, rng)
    q, a = sample_surcharge(n, rng, Q_MEAN, Q_COV, A_MIN, A_MAX)
    d_w = sample_groundwater(n, rng, D_GHG, D_GLG) if WATER else np.full(n, np.inf)
    return {"K": K, "gamma": gamma, "q": q, "a": a, "d_w": d_w}


def sample_total(soil_type, H, n, rng):
    """Draw n values of S_total for a soil type, with the inputs above."""
    x = sample_inputs(soil_type, n, rng)
    d_c = D_C if WATER else np.inf
    return total_stress(x["K"], x["gamma"], x["q"], x["a"], H, x["d_w"], d_c)


if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    a_mean = (A_MIN + A_MAX) / 2
    d_w_mean, d_c = ((D_GHG + D_GLG) / 2, D_C) if WATER else (np.inf, np.inf)
    print(f"H = {H:g} m, q ~ Normal({Q_MEAN:g} kPa, CoV {Q_COV:g}),"
          f" a ~ Uniform({A_MIN:g}, {A_MAX:g}) m, {N_MC:,} draws")
    if WATER:
        print(f"groundwater ~ Uniform({D_GHG:g}, {D_GLG:g}) m, canal at {D_C:g} m below ground")
    else:
        print("no water")
    print(f"\n{'':15s}   mean values [kNm/m]                Monte Carlo S_total [kNm/m]")
    print(f"{'soil':15s} {'S_soil':>7s} {'S_water':>8s} {'S_q':>6s} {'S_total':>8s}"
          f"   {'mean':>7s} {'CoV':>6s} {'5%':>7s} {'95%':>7s}")
    for soil_type, soil in SOIL_TYPES.items():
        K, gamma = soil["K_mean"], soil["gamma_mean"]
        S_soil = soil_stress(K, gamma, H, d_w_mean)
        S_water = water_stress(H, d_w_mean, d_c)
        S_q = surcharge_moment(K, Q_MEAN, a_mean, H)
        S = sample_total(soil_type, H, N_MC, rng)
        print(f"{soil_type:15s} {S_soil:7.2f} {S_water:8.2f} {S_q:6.2f} {S_soil + S_water + S_q:8.2f}"
              f"   {S.mean():7.2f} {S.std() / S.mean():6.3f}"
              f" {np.percentile(S, 5):7.2f} {np.percentile(S, 95):7.2f}")

"""Soil load on a retaining wall from lateral earth pressure."""

import numpy as np

# K is lognormal, gamma_s is normal, both given as (mean, CoV).
# kappa_f0 is deterministic, one value for shallow foundations and one for piles.
SOIL_TYPES = {
    "soft_clay_peat": {
        "K_mean": 0.60, "K_cov": 0.20,
        "gamma_mean": 15.0, "gamma_cov": 0.05,
        "kappa_f0_shallow": 0.80, "kappa_f0_piles": 1.10,
    },
    "sand": {
        "K_mean": 0.35, "K_cov": 0.20,
        "gamma_mean": 18.0, "gamma_cov": 0.05,
        "kappa_f0_shallow": 1.00, "kappa_f0_piles": 1.20,
    },
    "mixed": {
        "K_mean": 0.45, "K_cov": 0.25,
        "gamma_mean": 16.5, "gamma_cov": 0.06,
        "kappa_f0_shallow": 0.90, "kappa_f0_piles": 1.15,
    },
}


def soil_stress(K, gamma_soil, H):
    """
    K          : earth pressure coefficient [-]
    gamma_soil : unit weight of the soil [kN/m3]
    H          : retained soil height [m]
    """
    return K * gamma_soil * H**3 / 6


def soil_stress_mean(soil_type, H):
    """S for a soil type in SOIL_TYPES, using the mean K and gamma_s."""
    soil = SOIL_TYPES[soil_type]
    return soil_stress(soil["K_mean"], soil["gamma_mean"], H)


def sample_soil(soil_type, n, rng):
    """Draw n values of K (lognormal) and gamma_s (normal) for a soil type."""
    soil = SOIL_TYPES[soil_type]
    sigma = np.sqrt(np.log(1 + soil["K_cov"]**2))
    mu = np.log(soil["K_mean"]) - sigma**2 / 2
    K = rng.lognormal(mu, sigma, n)
    gamma = rng.normal(soil["gamma_mean"], soil["gamma_cov"] * soil["gamma_mean"], n)
    return K, gamma


if __name__ == "__main__":
    H = 3.0  # [m]
    rng = np.random.default_rng(1)
    for soil_type in SOIL_TYPES:
        K, gamma = sample_soil(soil_type, 100_000, rng)
        S = soil_stress(K, gamma, H)
        print(f"{soil_type:15s} mean values: S = {soil_stress_mean(soil_type, H):6.2f}"
              f"   sampled: mean {S.mean():6.2f}, CoV {S.std() / S.mean():.3f}")




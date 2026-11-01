"""Surcharge load on a retaining wall from a uniform load behind it.

q is a given surcharge [kPa]. Its traffic dependence (the ADT-based
extreme-value distribution) is left out here.
"""

import numpy as np

# q is normal, as in Hemel et al. (2024), see docs/failure_formula_notes.md.
# a is uniform: only a plausible range is known, no value is preferred.
# a = 0 is a load right at the quay edge (parked or delivering vehicles).
Q_MEAN, Q_COV = 7.0, 0.20   # [kPa]
A_MIN, A_MAX = 0.0, 3.0     # [m]


def effective_surcharge(q, a, H):
    """
    q : surcharge [kPa]
    a : distance between the wall and the load [m]
    H : retained soil height [m]
    """
    # same as q / (1 + (a/H)^2), but finite at H = 0
    return q * H**2 / (H**2 + a**2)


def surcharge_stress(K, q, a, H):
    """Lateral pressure K q_eff [kPa], uniform with depth."""
    return K * effective_surcharge(q, a, H)


def surcharge_force(K, q, a, H):
    """Resultant force K q_eff H [kN/m], acting at H/2."""
    return surcharge_stress(K, q, a, H) * H


def surcharge_moment(K, q, a, H):
    """Moment S_q = 1/2 K q_eff H^2 [kNm/m] about the base."""
    return 0.5 * surcharge_stress(K, q, a, H) * H**2


def sample_surcharge(n, rng, q_mean=Q_MEAN, q_cov=Q_COV, a_min=A_MIN, a_max=A_MAX):
    """Draw n values of q (normal) and a (uniform)."""
    q = rng.normal(q_mean, q_cov * q_mean, n)
    a = rng.uniform(a_min, a_max, n)
    return q, a

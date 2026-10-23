"""Bending of the rotted timber pile heads under the horizontal load.

Lateral failure of the pile foundation, the mechanism of Hemel (2023, 2024):
the soil behind the wall pushes the floor towards the canal and the piles bend.
The pile fails when the timber yields:

    sigma = theta_M M / W(d) + N / A(d) > MOR,   W = pi d^3 / 32,  A = pi d^2 / 4

d is the diameter of the sound core: d = D0 - 2 shell. The outer shell of an
old pile has rotted and carries nothing; it keeps growing at `rate` per year.

The moment in a pile follows from a long beam on elastic springs (Hetenyi):
a horizontal force P at the head gives

    M = P / (2 lambda)          head fixed in a concrete floor (type 2)
    M = 0.3224 P / lambda       head pinned into a timber beam (type 1)

with lambda = (k D0 / (4 E I_core))^(1/4) and k the subgrade modulus of the soil.

Run: python3 scripts/StressCaclulation/PileStrength.py
"""

import numpy as np

# Pine piles of the low walmuren: about 180 mm, 4 m long, 2 rows (IBU Stadsingenieurs,
# Ontwerpnotitie herstel lage walmuren, p. 4). The spacing along the wall is not
# given; "onderlinge afstand ca. 1 meter" is read as about 1 m.
D0_MEAN, D0_COV = 0.180, 0.10           # [m], normal; CoV as Hemel (2023) Table 7.1
SPACING = (0.8, 1.2)                    # [m] along the wall, uniform
# Timber and soil, Hemel (2023) Table 7.1 (Amsterdam pine piles, peat and clay).
MOR_MEAN, MOR_COV = 22.0e3, 0.10        # [kPa], normal
E_MEAN, E_COV = 9.0e6, 0.20             # [kPa], normal
K_SUBGRADE = (4300.0, 10000.0)          # [kN/m3], uniform between clay and peat
THETA_M_COV = 0.10                      # model factor on the moment, lognormal
# Decay. The condition of the piles is not known per wall. Hemel (2023, chapter 3
# conclusions) measured the soft shell of 115-year-old pine piles in Amsterdam:
# 21 mm on average, up to 45 mm. Today's shell is taken uniform over that whole
# range, the same for every wall. After today it grows 0.17 mm/yr in Hemel
# (2023, section 7.3.2); the range around that is a guess.
SHELL_NOW = (0.0, 0.045)                # [m] soft shell in NOW, uniform
NOW = 2026
RATE = (0.10e-3, 0.25e-3)               # [m/yr] growth of the soft shell, uniform


def remaining_diameter(D0, shell, rate, year):
    """Diameter of the sound core [m] in `year`, from the soft shell [m] of NOW."""
    return D0 - 2 * (shell + rate * (year - NOW))


def head_moment(P, d, D0, E, k, fixed):
    """Largest moment in a pile [kNm] from a horizontal force P [kN] at its head."""
    I_core = np.pi * d**4 / 64
    lam = (k * D0 / (4 * E * I_core))**0.25
    return P / (2 * lam) if fixed else 0.3224 * P / lam


def pile_stress(M, N, d, theta_M):
    """Bending plus axial stress in the sound core [kPa]."""
    return theta_M * M / (np.pi * d**3 / 32) + N / (np.pi * d**2 / 4)


def sample_piles(n, rng):
    """Draw n values of every pile input."""
    sigma = np.sqrt(np.log(1 + THETA_M_COV**2))
    return {
        "D0": rng.normal(D0_MEAN, D0_COV * D0_MEAN, n),
        "s": rng.uniform(*SPACING, n),
        "MOR": rng.normal(MOR_MEAN, MOR_COV * MOR_MEAN, n),
        # a normal E goes below zero once in about 3 million draws
        "E": np.maximum(rng.normal(E_MEAN, E_COV * E_MEAN, n), 0.1 * E_MEAN),
        "k": rng.uniform(*K_SUBGRADE, n),
        "theta_M": rng.lognormal(-sigma**2 / 2, sigma, n),
        "shell": rng.uniform(*SHELL_NOW, n),
        "rate": rng.uniform(*RATE, n),
    }


if __name__ == "__main__":
    # One pile at mean values: 3 kN at the head, 30 kN axial, fixed head.
    for shell_mm in (0, 10, 21, 30, 45):
        d = remaining_diameter(D0_MEAN, shell_mm / 1000, np.mean(RATE), NOW)
        M = head_moment(3.0, d, D0_MEAN, E_MEAN, np.mean(K_SUBGRADE), True)
        s = pile_stress(M, 30.0, d, 1.0)
        print(f"soft shell {shell_mm:2d} mm: d = {d * 1000:5.1f} mm,"
              f" M = {M:4.2f} kNm, stress = {s / 1000:5.1f} MPa (MOR {MOR_MEAN / 1000:g})")

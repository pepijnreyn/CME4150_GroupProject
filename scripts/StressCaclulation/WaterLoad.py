"""Water load on a retaining wall: groundwater behind it, canal water in front.

Depths z are measured down from the ground surface behind the wall; the base,
about which all moments are taken, is at z = H. A water level at depth d stands

    h = H - d                                   [m]

above the base (0 if it is below the base). The two water levels are

    h_w = H - d_w     groundwater behind the wall
    h_c = H - d_c     canal water in front of the wall

Water pushes sideways with its full unit weight (no K): below a water level at
depth d the pressure is gamma_w (z - d). Its moment about the base is

    integral from d to H of gamma_w (z - d) (H - z) dz = gamma_w h^3 / 6

Groundwater pushes the wall towards the canal and canal water pushes it back,
so the net water load is

    S_water = gamma_w (h_w^3 - h_c^3) / 6       [kNm/m]

It is negative when the groundwater is below the canal level. Below the
groundwater the soil itself also weighs less (effective stress), which is
taken into account in soil_stress in SoilForce. The surcharge load is not
affected by water.

The canal level is fixed: the water board keeps it at a target level. The
groundwater depth is uniform between the mean highest (GHG) and mean lowest
(GLG) groundwater level.
"""

import numpy as np

GAMMA_W = 9.81   # unit weight of water [kN/m3]

# Medians over the 158 quay walls in data/processed/objects_groundwater.csv.
# For one wall: GLG depth = glg_depth_below_ground_m, GHG depth = that minus swing_m.
D_GHG, D_GLG = 1.73, 2.13   # groundwater depth below ground [m]
# Drop height (Valhoogte) of Van Asch van Wijckskade (KM060031), taken as the canal level.
D_C = 2.0                   # canal water depth below ground [m]


def water_height(H, d):
    """Height of a water level at depth d above the base [m], 0 if below the base."""
    return np.clip(H - d, 0, H)


def water_stress(H, d_w, d_c):
    """
    H   : retained soil height [m]
    d_w : groundwater depth below ground, behind the wall [m]
    d_c : canal water depth below ground, in front of the wall [m]
    """
    return GAMMA_W * (water_height(H, d_w)**3 - water_height(H, d_c)**3) / 6


def water_force(H, d_w, d_c):
    """Net horizontal force of groundwater minus canal water [kN/m]."""
    return GAMMA_W * (water_height(H, d_w)**2 - water_height(H, d_c)**2) / 2


def sample_groundwater(n, rng, d_ghg=D_GHG, d_glg=D_GLG):
    """Draw n groundwater depths below ground, uniform between GHG and GLG [m]."""
    return rng.uniform(d_ghg, d_glg, n)


if __name__ == "__main__":
    H = 1.22  # retained soil height, werf to canal bed [m]
    for label, d_w in [("GLG", D_GLG), ("canal level", D_C), ("GHG", D_GHG)]:
        print(f"groundwater at {label:11s} ({d_w:.2f} m): S_water = {water_stress(H, d_w, D_C):6.2f} kNm/m")

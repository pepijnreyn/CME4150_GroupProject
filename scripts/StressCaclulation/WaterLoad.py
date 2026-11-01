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
groundwater level is uniform between the two values of GROUNDWATER_NAP.
Both are levels on the werf, below the street: the BRO wells stand under the
streets and give groundwater above the werf, so they do not describe it.
"""

import numpy as np

GAMMA_W = 9.81   # unit weight of water [kN/m3]

# Water levels on the werf, also used per wall by FailureProbability.py.
CANAL_NAP = 0.60                # canal level [m NAP], fixed (Erfgoed Utrecht report 158)
GROUNDWATER_NAP = (0.50, 0.90)  # groundwater under the werf [m NAP], uniform; guess


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

"""Resistance of a masonry wall against overturning.

Two models:

1. The masonry block. The wall is a rigid block of masonry, height H and
   thickness t, that tips over its toe (the front edge of the base, on the
   canal side). Its own weight W = gamma_m H t acts at t/2 from the toe, so

       M_R = gamma_m H t^2 / 2                     [kNm/m]

   Only the masonry resists; the floor, the soil on it and the piles are left
   out. For a 0.40-0.45 m walmuur this is far below the load.

2. The real cross-sections of the low walmuren on their old timber foundation
   (SECTIONS below). The body that tips is the wall, its floor and the soil on
   the floor, about the front pile row at the underside of the floor. Its
   weight comes from the areas of the parts in the drawing; below the water
   each part weighs gamma - gamma_w. The soil behind the body also drags it
   down along its back (wall friction, delta = 2/3 phi), which adds

       M_delta = tan(delta) F_h (x_back - x_front)     [kNm/m]

   with F_h the horizontal force of the soil and the surcharge.

The wall overturns when M_R < S_total (TotalStress.py), both about the same
level: the base of the block, or the underside of the floor.

Run: python3 scripts/StressCaclulation/WallResistance.py
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator

from WaterLoad import GAMMA_W

# gamma_m is normal: a typical value for old brick masonry with lime mortar.
# t is uniform: only a plausible range is known. It is the thickness at the top
# of the Oudegracht walmuren, 0.41 m (Rak 02 OZ), 0.45 m (Rak 12-14) and 0.40 m
# (Erfgoed Utrecht report 156), as T_ASSUMED in scripts/table_wervengebied_data.py.
# The wall may be thicker lower down.
GAMMA_M_MEAN, GAMMA_M_COV = 19.0, 0.05   # [kN/m3]
T_MIN, T_MAX = 0.40, 0.45                # [m]

# Unit weights of the other materials of the cross-sections [kN/m3].
GAMMA_C_MEAN, GAMMA_C_COV = 23.0, 0.05   # tamped (unreinforced) concrete, normal
GAMMA_RC = 25.0                          # reinforced concrete floor
GAMMA_TIMBER = 10.0                      # waterlogged pine

# The two types of low walmuur on timber piles, from IBU Stadsingenieurs,
# "Ontwerpnotitie herstel lage walmuren" (about 2010), pp. 4-5:
#   type 1  since the late 19th century: a stepped masonry wall on a timber
#           floor and two timber beams (kesp), on two rows of vertical piles;
#   type 2  after WWII to the 1970s: a masonry facing with a tamped-concrete
#           backing on a reinforced concrete floor; the front row is raked 10:1.
# Measured on the drawings at 221 px/m: type 2 on Erfgoed Utrecht report 156,
# Afb. 3.1 (2 m scale bar; the IBU drawing is the same), type 1 on the IBU
# drawing at the same scale. Its 0.39 m top matches the 0.40 m wall of report 156.
# x [m] from the front face towards the werf, z [m NAP] as drawn. Above the
# floor the parts stretch with the werf level of the wall; dz shifts the
# foundation up or down. The kesp beams of type 1 and the timber screen between
# the rows stay on the piles: the screen holds the soil below the floor.
SECTIONS = {
    "type 1": {
        "werf": 1.167, "floor_top": -0.416,
        "base": -0.552,              # underside of the floor, on the kesp
        "pile_head": -0.765,         # underside of the kesp
        "back": 0.914,               # x of the back of the floor
        "piles": (0.109, 0.801),     # x of the front and rear row
        "rake": 0.0,                 # horizontal over vertical of the front row
        "fixed_head": False,         # pile heads pinned into the kesp
        "parts": [
            ("masonry", [(0, 1.167), (0.394, 1.167), (0.394, 0.919), (0.633, 0.919),
                         (0.633, -0.167), (0.778, -0.167), (0.778, -0.416), (0, -0.416)]),
            ("timber", [(0, -0.416), (0.914, -0.416), (0.914, -0.552), (0, -0.552)]),
            ("soil", [(0.394, 1.167), (0.914, 1.167), (0.914, -0.416), (0.778, -0.416),
                      (0.778, -0.167), (0.633, -0.167), (0.633, 0.919), (0.394, 0.919)]),
        ],
    },
    "type 2": {
        "werf": 1.145, "floor_top": 0.118,
        "base": -0.222,              # underside of the floor
        "pile_head": -0.222,
        "back": 1.371,
        "piles": (0.235, 1.118),
        "rake": 0.1,
        "fixed_head": True,          # pile heads cast into the concrete floor
        "parts": [
            ("masonry", [(0, 1.145), (0.493, 1.145), (0.493, 0.909), (0.244, 0.909),
                         (0.244, 0.118), (0, 0.118)]),
            ("concrete", [(0.244, 0.909), (0.493, 0.909), (1.027, 0.118), (0.244, 0.118)]),
            ("rc", [(0, 0.118), (1.371, 0.118), (1.371, -0.222), (0, -0.222)]),
            ("soil", [(0.493, 1.145), (1.371, 1.145), (1.371, 0.118), (1.027, 0.118),
                      (0.493, 0.909)]),
        ],
    },
}
MATERIALS = ["masonry", "concrete", "rc", "timber", "soil"]


def resistance_moment(gamma_m, H, t):
    """
    gamma_m : unit weight of the masonry [kN/m3]
    H       : wall height [m]
    t       : wall thickness [m]
    """
    return gamma_m * H * t**2 / 2


def resistance_moment_mean(H, gamma_m_mean=GAMMA_M_MEAN, t_min=T_MIN, t_max=T_MAX):
    """M_R using the mean gamma_m and the mean t."""
    return resistance_moment(gamma_m_mean, H, (t_min + t_max) / 2)


def sample_wall(n, rng, gamma_m_mean=GAMMA_M_MEAN, gamma_m_cov=GAMMA_M_COV,
                t_min=T_MIN, t_max=T_MAX):
    """Draw n values of gamma_m (normal) and t (uniform)."""
    gamma_m = rng.normal(gamma_m_mean, gamma_m_cov * gamma_m_mean, n)
    t = rng.uniform(t_min, t_max, n)
    return gamma_m, t


def place(section, werf, dz):
    """The parts of a section for a wall with this werf level and foundation shift.

    Points at or below the floor top move down or up by dz. Points above it
    stretch between the shifted floor top and the werf level of the wall.
    """
    s = SECTIONS[section]
    top = s["floor_top"] + dz
    stretch = (werf - top) / (s["werf"] - s["floor_top"])
    parts = []
    for material, poly in s["parts"]:
        moved = [(x, z + dz if z <= s["floor_top"] else top + (z - s["floor_top"]) * stretch)
                 for x, z in poly]
        parts.append((material, moved))
    return parts


def clip_below(poly, level):
    """The part of a polygon at or below z = level (Sutherland-Hodgman)."""
    out = []
    for (x0, z0), (x1, z1) in zip(poly, poly[1:] + poly[:1]):
        in0, in1 = z0 <= level, z1 <= level
        if in0:
            out.append((x0, z0))
        if in0 != in1:
            f = (level - z0) / (z1 - z0)
            out.append((x0 + f * (x1 - x0), level))
    return out


def area_moment(poly):
    """Area [m2] and first moment about x = 0 [m3] of a polygon (shoelace)."""
    if len(poly) < 3:
        return 0.0, 0.0
    a = m = 0.0
    for (x0, z0), (x1, z1) in zip(poly, poly[1:] + poly[:1]):
        cross = x0 * z1 - x1 * z0
        a += cross
        m += (x0 + x1) * cross
    a /= 2
    return abs(a), abs(m / 6)


def section_areas(section, werf, dz, z_water):
    """Per material: area and first moment, in total and below the water."""
    out = {}
    for material, poly in place(section, werf, dz):
        a, m = area_moment(poly)
        ab, mb = area_moment(clip_below(poly, z_water))
        prev = out.get(material, np.zeros(4))
        out[material] = prev + np.array([a, m, ab, mb])
    return out


def friction_tan(K):
    """tan(delta) of wall friction, delta = 2/3 phi, phi from K = (1 - sin phi)/(1 + sin phi)."""
    phi = np.arcsin((1 - K) / (1 + K))
    return np.tan(2 / 3 * phi)


def section_resistance(section, werf, dz, z_water, gammas, n_grid=(15, 7, 7)):
    """Weight V [kN/m] and resisting moment about the front pile row [kNm/m].

    werf, dz, z_water and the unit weights in `gammas` (a dict per material)
    are arrays of draws. The areas are worked out on a grid of werf, dz and
    z_water and interpolated, which is exact up to the grid's linear steps.
    """
    axes = [np.linspace(v.min() - 1e-6, v.max() + 1e-6, k)
            for v, k in zip((werf, dz, z_water), n_grid)]
    grid = np.zeros([len(a) for a in axes] + [len(MATERIALS), 4])
    for i, w in enumerate(axes[0]):
        for j, d in enumerate(axes[1]):
            for k, zw in enumerate(axes[2]):
                areas = section_areas(section, w, d, zw)
                for m, material in enumerate(MATERIALS):
                    grid[i, j, k, m] = areas.get(material, np.zeros(4))
    pts = np.column_stack([werf, dz, z_water])
    V = M = 0.0
    for m, material in enumerate(MATERIALS):
        a, mom, ab, mb = (RegularGridInterpolator(axes, grid[..., m, c])(pts) for c in range(4))
        V = V + gammas[material] * a - GAMMA_W * ab
        M = M + gammas[material] * mom - GAMMA_W * mb
    x_front = SECTIONS[section]["piles"][0]
    return V, M - V * x_front


if __name__ == "__main__":
    H = 1.22  # wall height, werf to wall underside, median in walmuur_height.csv [m]
    rng = np.random.default_rng(1)
    gamma_m, t = sample_wall(100_000, rng)
    M_R = resistance_moment(gamma_m, H, t)
    print(f"Masonry block, H = {H:g} m, gamma_m ~ Normal({GAMMA_M_MEAN:g} kN/m3, CoV {GAMMA_M_COV:g}),"
          f" t ~ Uniform({T_MIN:g}, {T_MAX:g}) m")
    print(f"mean values: M_R = {resistance_moment_mean(H):6.2f} kNm/m"
          f"   sampled: mean {M_R.mean():6.2f}, CoV {M_R.std() / M_R.mean():.3f},"
          f" 5% {np.percentile(M_R, 5):6.2f}, 95% {np.percentile(M_R, 95):6.2f}")

    gammas = {"masonry": GAMMA_M_MEAN, "concrete": GAMMA_C_MEAN, "rc": GAMMA_RC,
              "timber": GAMMA_TIMBER, "soil": 16.5}
    print("\nCross-sections at werf +1.10 m NAP, water +0.60 m NAP, soil 16.5 kN/m3:")
    for name, s in SECTIONS.items():
        one = np.array([1.10])
        V, M = section_resistance(name, one, np.zeros(1), np.full(1, 0.60), gammas)
        print(f"{name}: underside of the floor {s['base']:+.2f} m NAP, H = {1.10 - s['base']:.2f} m,"
              f" V = {V[0]:5.1f} kN/m, M_R about the front pile = {M[0]:5.2f} kNm/m")

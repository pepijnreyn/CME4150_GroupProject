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
"""

import numpy as np

from SoilForce import soil_stress
from TraficLoad import surcharge_moment
from WaterLoad import water_stress


def total_stress(K, gamma_soil, q, a, H, d_w=np.inf, d_c=np.inf):
    """S_total [kNm/m], for single values or arrays of draws. Default depths: dry."""
    return (soil_stress(K, gamma_soil, H, d_w) + water_stress(H, d_w, d_c)
            + surcharge_moment(K, q, a, H))


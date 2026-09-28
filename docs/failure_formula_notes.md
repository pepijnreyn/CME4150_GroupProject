# Project notes: failure formula for quay walls on timber piles

*CME4150 Team Challenge*

## 1. Failure mechanism

Lateral failure of the timber pile foundation. Earth pressure and traffic load push the wall towards the water and the piles bend. Failure is defined as the onset of yielding in the timber (Hemel et al., 2024).

## 2. Limit state (Hemel et al., 2024, Eq. 3–4)

$$
g(X,t) = MOR - \sigma_b(t), \qquad P_f = P\left[g(X,t) < 0\right]
$$

$$
\sigma_b = \theta_M \frac{32\,M}{\pi D^3} + \theta_N \frac{4\,N}{\pi D^2}
$$

## 3. Simplified bending stress (own calibration)

We do not have the analytical pile model used by Hemel, so $M$ is replaced by a simple expression calibrated to the published case ($\beta \approx 1.5$ at $q = 7$ kN/m² over 15 years):

$$
\sigma_b(t) = \theta_M\,\theta_S\,(s_0 + s_q\,q)\left(\frac{D_{ref}}{D(t)}\right)^4 + \theta_N \frac{4N}{\pi D(t)^2}
$$

$$
D(t) = D_0 - r\,t
$$

- $s_0 = 3.0$ N/mm²
- $s_q = 0.10$ (N/mm²)/(kN/m²)
- $D_{ref} = 240$ mm

The exponent 4 is a fitted value: $D$ acts on the stress through $D^3$ and on pile stiffness through $D^4$. The resulting influence factors (diameter 0.63, soil 0.14, load 0.07) are close to those in the paper (0.67, about 0.21, 0.07).

## 4. Inputs

| Symbol | Meaning | Distribution | Source |
|---|---|---|---|
| $D_0$ | Pile diameter now | Normal(245 mm, CoV 0.10) | Hemel 2024 |
| $r$ | Diameter loss by bacterial decay | 0.34 mm/yr | Hemel 2024 |
| $t$ | Time window | 15 yr | NEN 8700 |
| $MOR$ | Bending strength timber | Normal(22 N/mm², 0.10) | Hemel 2024 |
| $q$ | Traffic load | Normal(7 kN/m², 0.20) | Hemel 2024 |
| $\theta_M$ | Model uncertainty bending | Lognormal(1, 0.10) | JCSS |
| $\theta_N$ | Model uncertainty axial | Lognormal(1, 0.05) | JCSS |
| $\theta_S$ | Lumped soil uncertainty | Lognormal(1, 0.20) | Own calibration |
| $N$ | Axial force per pile | 20 kN | Own estimate |

Notes:

- Replace Amsterdam values with Utrecht data where available (axle-load limits for $q$, diameter or soft-shell measurements for $D_0$ and $r$).
- The thesis (Hemel, 2023) finds a soft shell of 21 mm on average (max. 45 mm) and a CoV of 0.26 for MOR. Useful as a sensitivity case.

## 5. Solving and assessment

Crude Monte Carlo with $n \geq 10^5$:

$$
P_f = \frac{1}{n}\sum_{j=1}^{n} \mathbf{1}\left[g(X_j,t) < 0\right], \qquad \beta = -\Phi^{-1}(P_f)
$$

Minimum reliability for existing structures, 15-year reference period (NEN 8700, Table B.2):

| Consequence class | $\beta_{min}$ | $P_{f,max}$ |
|---|---|---|
| CC1 | 1.8 | $3.6 \cdot 10^{-2}$ |
| CC2 | 2.5 | $6.2 \cdot 10^{-3}$ |
| CC3 | 3.3 | $4.8 \cdot 10^{-4}$ |

$P_f$ is the $P$ in the risk score $R = P \cdot C$ per structure.

## 6. Optional: updating with past performance (Hemel et al., 2024, Eq. 12)

If a load $q_\eta$ is known to have been survived, evaluate the limit state a second time with $q_\eta$ and today's diameter, and keep only the surviving samples:

$$
P_{f|\eta} = \frac{\sum_j \mathbf{1}\left[g(X_j,q_j)<0\right]\cdot \mathbf{1}\left[g(X_{\eta,j},q_{\eta,j})>0\right]}{\sum_j \mathbf{1}\left[g(X_{\eta,j},q_{\eta,j})>0\right]}
$$

In the paper, survival of 10 kN/m² raises $\beta$ from 1.5 to 2.0. Adding a measured displacement below 4 mm raises it to 3.2.

## 7. Limitations

- Valid only for masonry walls on timber piles. Concrete revetments and sheet piling need other mechanisms (e.g. corrosion).
- Calibrated on one Amsterdam case. Suitable for relative comparison between structures, not for absolute failure probabilities.
- Inputs are treated as uncorrelated, which overestimates reliability. MOR and stiffness have a measured correlation of 0.83.

## References

- Hemel, M.-J., Peters, D.J., Schweckendiek, T., & Jonkman, S.N. (2024). Reliability updating for lateral failure of historic quay walls. *Georisk*, 18(4), 882–903.
- Hemel, M.-J. (2023). *Amsterdam quays under pressure: modelling and testing of historic canal walls*. PhD thesis, TU Delft.
- NEN 8700:2011+A1:2020. *Beoordeling van de constructieve veiligheid van een bestaand bouwwerk*.

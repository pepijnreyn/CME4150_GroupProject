# Task: replace assumed fault-tree probabilities with calculated ones (Section 3.1)

The report is handed in on 2026-11-01. Section 3.1 of the report gets marked down because 14 of the
20 basic events in the fault tree are assumptions on an ordinal scale (0.001 / 0.005 / 0.02 / 0.10 /
0.30). Replace the most important ones with values calculated from data or from the failure model we
already have. Read `CLAUDE.md` first and follow it (Overleaf subtree, build before push, ask before
every push, never print the token).

## Before you start

- `git status`: if `report/` still has unresolved merge conflicts (`UU` files from a subtree pull),
  stop and ask me how to resolve them. Don't resolve them yourself by discarding the Overleaf side.
- Build the report once (XeLaTeX, see `CLAUDE.md`) and keep the warning list.
- Read `scripts/fault_tree.py`. In the code, event `M` is LS in the report and `D` is NW. The basic
  events with (p, lower, upper) are in the dictionary around line 67. Common-cause shares are in
  `COMMON`. Intervention effects per alternative are around line 86.
- Read Sections 3.1 and 3.2 (`report/mainmatter/chapter-3.tex`) and Table 3.1 so you know which
  numbers depend on the tree.

## Scope: do these three, in this order

### 1. NW (`D`): no visible warning before failure. Now 0.50 (0.30–0.80), an assumption
Calculate it from the failure model.
- `scripts/StressCaclulation/ModelChecks.py` already computes the horizontal displacement of the
  pile heads under today's soil and water (Hetényi: y = Pλ/(kD₀) for a fixed head, twice that for a
  pinned head) for the survey alternative A7. See Appendix B.1.10 and Table B.6.
- For each wall and wall type, take the draws that stand today (evidence E) but fail with surcharge,
  and compute the fraction whose displacement today is below a visible threshold. Use 5 mm as the
  base, the same threshold as A7, and 3 mm and 10 mm for the range.
- NW for a wall = Σ_T P(T | E) × fraction(T). Report the value for the median wall Oude Gracht
  Rak 09 WZ and the range over the 17 walls.
- Caveat to state in the text: the model leaves out settlement from pile rot, the damage actually
  observed (Duurland, 2020), so visible warning is probably more common than the model says. NW from
  the model is therefore on the safe side.
- Use the existing script and seed. Don't change `FailureProbability.py` itself. Add the calculation
  to `ModelChecks.py` or a small new script, and write the result to `data/processed/`.

### 2. S1: wrong year or foundation in register. Now 0.10 (0.05–0.20), an assumption
Calculate it from the register with a Beta posterior, Beta(1 + k, 1 + n − k), uniform prior.
- Walmuren: 11 of 51 walls keep the year of the old wall after a renewal on steel. 8 have unclear
  foundation status. Check both counts in `data/processed/walmuur_foundation.csv` and Table A.2.
- Use k = 11, n = 51 for the base value (posterior mean ≈ 0.23) and the 5–95 % posterior interval as
  the range. Mention the portfolio check: 23 collective (1917) + 418 rounded (1450/1900) years out of
  1,844 objects (Table A.3, Appendix A.1.3).
- Note in the text that S1 matters only through the AND with NW (screening misses the wall AND no
  visible warning).

### 3. I1: targeted inspection not done in time. Now 0.30 (0.10–0.73), an assumption
Calculate it from the inspection programme.
- The re-assessment of all quay walls runs until 2030 (Gemeente Utrecht, 2026a). Assume uniform
  coverage from 2026 to 2030, so 25 % per year. Then P(not inspected before renewal) =
  max(0, 1 − 0.25 × T_r), with T_r the years until renewal per wall from
  `regression_production_rate.py` (5.2 years for the median wall).
- The result for the median wall will be close to 0. Inspection can still be too late if it comes
  after the weakness becomes critical. Explain this, and set the base value as the chance that the
  inspection falls in the second half of the exposure, or use another rule you can justify in one
  sentence. Give the range from coverage spread over 2026–2030 vs. 2026–2035.
- If you can't defend a calculated value in two sentences, keep 0.30 and only explain the upper
  bound of 0.73, which the report doesn't do now.

## Don't change

- Load events (Q1, Q2, Q3, E1, E2, E4). A zero-failure estimate (Jeffreys or rule of three over
  306 wall-years) gives higher values than now, and the model already predicts 2× the observed
  incidents. Mention this in one sentence in 3.1.4 as a possible next step, nothing more.
- L2–L4 and S3. Leave them as assumptions.
- The failure model, its seeds and the draws file.

## Optional, only if time is left (in this order)

1. Write out the HEART calculation for I2 and I3 in Appendix B: generic task type, nominal value,
   EPCs, assessed proportion of affect, and nominal × Π[(EPC − 1) × APOA + 1]. Values should
   reproduce 0.16 and 0.03 from Aghaei et al. (2021) and Williams (1986).
2. Sample each basic event from a Beta distribution fitted to its (p, lower, upper) in the Monte
   Carlo of `fault_tree.py`, and report a 90 % band for the top event.

## Rerun and update

1. Update the three events in `fault_tree.py`, including the alternatives that change them (A2 sets
   `D` to 0.30. Keep the same relative reduction or justify a new value). Run the script.
2. Update every number that comes from the tree, and check each one against the script output:
   - Section 3.1: the list of bases ("Of the 20 events, one comes from the model…": the counts change
     to 3 more derived/model events and 3 fewer assumptions), Table 3.1 (basis column), 3.1.3
     (0.049, 0.023, 0.48, 0.015/0.47, 0.042–0.067, 0.077, 0.039, 0.82, cut sets, Fussell–Vesely, swings),
     3.1.4 (0.17 per year, 0.28 per km, "more than twice").
   - Section 3.2: Tables 3.2 and 3.3, Figure 3.2, the break-even values of C_f (€2.4M, €4.4M,
     €5.05M), the certainty equivalents, the pessimistic case, LS ×3 and ÷3, half effect, 3.2.5.
   - Appendix B.2 (Figure B.6), Section 4.2, the conclusion (Chapter 5), Table 1.2 (A10) and the
     municipality summary (Appendix E).
   - Regenerate the figures with `plot_appendix_figures.py` and `fault_tree_figure.py`, and copy them
     to `report/figures/`.
3. If the ranking of the alternatives changes (A0 vs. A6 risk-neutral, A4 risk-averse), tell me
   before rewriting the conclusions, because 4.2 and the conclusion depend on it.
4. Keep the page limits: 3.1 is at about 2.8 of 3 pages and 3.2 at 3 of 3. Cut as much as you add.

## Finish

- Build with XeLaTeX. No new undefined references or citations, and `latexmk` exits with 0.
- Commit script changes and `report/` changes in separate commits.
- Show me the old and new values of NW, S1, I1, P_f of the median wall, E[N] over the 17 walls and the
  preferred alternatives, and ask me before pushing to Overleaf.

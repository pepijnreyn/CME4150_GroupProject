# Section-by-section grading of the report (CME4150 rubric, criteria 1.1–4.2)

I graded the PDF that was built at 18:44 today (`$TMPDIR/overleaf-build/report.pdf`). Your working tree is in the middle of a subtree merge, with conflicts in `chapter-1.tex`, `chapter-3.tex`, `appendix-b.tex` and the fault-tree figure. The text you end up pushing may therefore differ from what I read. I didn't edit anything.

Each section was read the way a different teacher would read it: only that section, the parts it points to, the guide and the Municipality Q&A.

---

## 1.1 Problem synthesis & goal definition (5 %) — **8.5**
Length is about 0.5 page, which is right at the limit.

| Element | Verdict |
|---|---|
| Goal is relevant | **Met.** It is a risk-ranking method for the whole portfolio, which matches the Q&A ("transparent, risk-based methodology … portfolio level"). |
| Goal is clearly stated | **Met.** The decision variables are named: where to inspect or intervene first, and which interim measure to take. **Missing:** a time horizon (until renewal? 2050?) and the output metric. |
| Variables | **Met:** werf level, soil class, wall type, pile condition, canal bed, loads, groundwater. |
| Processes | **Met:** bacterial pile decay, and earth pressure tipping the wall and bending the piles. |
| Relations between variables | **Partly met.** One sentence covers it ("soil, groundwater and surcharge set the earth pressure…; the wall type decides which governs"). There is no diagram or table. |
| Availability and uncertainty | **Met.** Reducible vs. carried uncertainty, the 0.05 m werf accuracy, soil class agreeing with 25–67 % of borings. |

**Other points:** Figure 1.1 is too small to read. Terms like werf, rak and walmuur are used before a reader new to them can follow. Organisational uncertainty only gets "(Chapter 3)".

**Best improvements per hour:**
1. Add the decision horizon and the output (a risk class per wall, from now until renewal) in one clause. About 10 minutes.
2. Replace Figure 1.1 with a small influence diagram (variables → processes → failure, coloured by data availability). This fills the "relations" gap without adding text. 1–2 hours.
3. Add one clause on which organisational uncertainties exist and why they are carried rather than reduced. About 15 minutes.

---

## 1.2 Assumptions, data collection & generation (10 %) — **8.5**
Length is about 2 pages.

| Element | Verdict |
|---|---|
| Excellent presentation of the collected data | **Mostly met.** Table 1.1 (source, use, coverage, known errors) is the data-quality table the guide asks for. The generated per-wall data are only summarised as ranges; the actual values are in Table A.4. |
| Sound assumptions where data is missing | **Met.** Table 1.2 gives each assumption a distribution and a basis. |
| Impact of assumptions on the result | **Met.** Section 1.2.3 and the "Effect on β" column. **However**, that column mixes units: A3 says "unknown", A7 says "conservative", A9 and A10 talk about the decision. A5 is about K and γ being *independent*, but its effect cell reports the *soil-class* swing; independence itself changes β by only 0.03. A10 bundles two assumptions. |
| Data properly generated and presented | **Met.** The AHN median rule, the soil-class rule, the Monte Carlo seed, and the scripts in A.1. Validation: werf level against excavations, renewed length against the municipal figure, and the service-history check. |

**Other points:**
- The register errors that matter for the portfolio (the year 2118, the collective year 1917, 418 rounded years, widths with two meanings) appear only in 1.4 and A.1.3. A teacher who reads only 1.2 will see the analysis as Oudegracht-only, which goes against the Q&A's portfolio framing.
- The Q&A says high-level replacement unit costs can be shared. Section 1.2 doesn't say why they weren't used.

**Best improvements per hour:**
1. Make the effect column consistent: give a Δβ range for each assumption, plus "decision changes yes/no". Fix A5 and split A10. About 1 hour.
2. Add two lines summarising register quality for the whole portfolio, pointing to A.1.3. About 20 minutes.
3. Add a small map or strip chart of the generated inputs per wall (werf level, soil class, prior P(type 2)). 1–2 hours, but it costs page space.

---

## 1.3 Problem exploration & dimension reduction (5 %) — **8**
Length is about 1.5 pages, at the limit.

| Element | Verdict |
|---|---|
| Adequate sensitivity analysis | **Mostly met.** One-at-a-time swings from the 5th to 95th percentile, with common random numbers, reported per wall type (Table 1.3). **Weak spot:** you found strong interactions yourselves (wall type × inputs, and the "higher K raises β" artefact), yet one-at-a-time analysis cannot capture interactions. A strict reader will also contest the dismissal of variance-based methods. Conditional variance, or the expected value of information, is exactly what a decision about what to measure needs. |
| Decisions consistent with results and uncertainty | **Met.** Six minor inputs are fixed (verified effect ≤ 0.03). Model factors stay random. The wall type is measured first, then micro-drilling, then a terrace survey. Each is tied to a named set of walls. |
| Whole process justified | **Mostly met.** The four reduction steps are stated. The accuracy cost of the soil classes is quantified. The cost of "two cross-sections represent all walls" is explicitly *not* quantified, although the guide asks for it. |

**Other points:** The swings are in β, while the decision depends on the risk class. Percentile swings also depend on the chosen distribution shape (uniform vs. lognormal). You acknowledge this.

**Best improvements per hour:**
1. Add a column to Table 1.3: the number of walls that change risk class per input. This ties the sensitivity analysis directly to the decision. The tornado CSV already exists, so 1–2 hours.
2. Bound the error of the two-section reduction, for example by using the type-1 vs. type-2 gap or the foundation-level swing as a proxy. About 30 minutes of text.
3. Estimate first-order variance indices for the wall type and the soft shell by binning the existing Monte Carlo draws. No new runs are needed, and it answers the interaction critique. 3–4 hours.

---

## 1.4 Approach selection (5 %) — **8**
Length is about 0.9 page.

| Element | Verdict |
|---|---|
| Excellent explanation, including tools and uncertainty methods | **Met.** Figure 1.2, the coarse-to-fine logic, Monte Carlo vs. FORM, Bayesian proven strength, and why a deterministic check, ARK alone, Markov, Bayesian networks or multi-criteria analysis were not chosen. |
| Most convenient approach for the problem and data | **Partly met.** The portfolio path (indicator scoring for the 60 km) is described but not applied. Almost all the effort goes to 611 m that the Q&A says an existing programme already covers. The section doesn't say how uncertainty is carried on the indicator path. Chapter 3 analyses one median wall rather than one wall per class, which the figure doesn't show. |

**Best improvements per hour:**
1. Mark in Figure 1.2 which boxes this report applied and which are only proposed (dashed for the indicator path). About 30 minutes.
2. Add 2–3 sentences: why the test bed is the walmuren despite the Q&A, and which parts carry over unchanged to other asset types. About 30 minutes.
3. Add one sentence on how uncertainty is carried for walls without a model (data-quality score, class ranges). About 15 minutes.

---

## 2.1 Probabilistic models (15 %) — **7.5**
Length is about 2 pages. A strict examiner could go down to 6.5.

| Element | Verdict |
|---|---|
| Adequate models | **Met.** Two physics-based limit states in series, a basis for every variable (Table 2.1), Bayesian proven-strength updating by rejection, and a mixture over wall type. I checked the equations: d = D₀ − 2(s₀ + r(t − 2026)) and β = −Φ⁻¹(P_f) are correct. |
| Explicit dependence | **Met.** Wall type and soil class act as common causes. One draw of K and of groundwater is shared across terms. The two limit states occur together 4.4 times as often as if independent. Copula tests show the correlations change β by at most 0.03. Dependence *between walls* is deferred to 3.1. |
| Adequately validated | **Partly met. This is the weakest element.** Only the werf level is fitted to data. The groundwater data are unrepresentative and the soil class agrees with only 25–67 % of borings. Your own type-1 model fails in up to two-thirds of draws for walls that stand, and you call it "miscalibrated". The type update "mainly reflects this error". Agreement with the rak-6 incident is anecdotal. |
| Relevant conclusions | **Met.** "A ranking and an order of magnitude, not a NEN 8700 verdict." The 2041 drift is small. |

**Conceptual gap no one has flagged:** there is no length effect. Diameter and soft shell are drawn once per wall ("E/A varies between piles"), and only the most loaded pile is checked. A 101 m wall with about 200 piles and a 3.4 m wall are therefore treated identically. The ranking quietly favours long walls.

Also, "MOR [kPa] … (22 MPa)" is technically consistent but reads oddly.

**Best improvements per hour:**
1. Treat robustness of the ranking as the validation metric. Report the Spearman rank correlation between the base ranking and each variant in Tables B.3 and B.6. You claim the model supports a ranking, so test that claim directly. About 1 hour.
2. Recalibrate the type-1 model. Choose θ_R so that P(E | T=1) is at least about 0.9, then show the rank correlation with the base model. This turns your weakest validation point into a test. 2–3 hours.
3. Address the length effect. At minimum, add a sentence saying P_f is per cross-section and the ranking ignores length (30 minutes). Better, run a series system of N segments with partial correlation (2–3 hours).

---

## 3.1 Fault tree construction (10 %) — **8**
Length is about 2.8 pages.

| Element | Verdict |
|---|---|
| Rich top event and causes | **Met.** "The programme does not prevent a wall failure before renewal", with about 30 basic events coloured by type (technical, human, organisational, external). The repair chain is drawn once and shared. |
| Appropriate Boolean gates | **Mostly met.** The AND of "weakness" and "not repaired in time" is sound. **But the drawn tree is not the quantified tree.** G1, G2, GW, P1, P3, WT, M1 and M2 are collapsed into a single event LS that Figure 3.1 never shows. G1, G2 and GW also appear under "Load too high", so a reader checking the figure alone sees double counting. |
| Numerical analysis | **Met.** Analytical calculation plus Monte Carlo with a copula and shared common-cause draws, minimal cut sets, Fussell–Vesely importance, and lower/upper swings. |
| Critical reflection on the numbers | **Met.** The model gives about 2× the observed incident rate per km. Data quality is discussed per type, along with the conditions under which conclusions hold and which data are needed next. |

**Weak spots:**
- 14 of the 20 events come from an ordinal scale the team assumed, with no elicitation, even though the guide suggests structured expert judgement.
- The HEART derivation for I2 and I3 (error-producing conditions, their weights) isn't shown.
- The upper bound of 0.73 for I1 isn't explained.
- "S2 = 0 from data" is circular, because the screening rule was designed on the same data.
- Load events are scaled to the years until renewal; human and organisational events are not.

**Best improvements per hour:**
1. Redraw Figure 3.1 to match what is computed. Draw an LS box around the eight model events, mark G1, G2 and GW in the load branch as "inside LS", and print the probabilities on the leaves. 1–2 hours. Of all the fixes in this section, this one most changes how a teacher reads the section.
2. Put the HEART steps for I2 and I3 in an appendix (generic task, error-producing conditions, weights). About 1 hour.
3. Run a quick elicitation for NW, I1 and L2–L4, the highest-importance assumed events: 4–5 independent estimates, then aggregate. 2–3 hours.

---

## 3.2 Trade-off analysis (10 %) — **8.5**
Length is about 3 pages.

| Element | Verdict |
|---|---|
| Trade-off of costs and benefits of risk-reduction measures | **Met.** A decision tree with 8 alternatives covering technical, human and organisational measures, expected cost with 2.8 % discounting, and a preposterior analysis for monitoring (A7). |
| Justified numerical evaluation of the uncertainties | **Mostly met.** C_f is varied from €0.1M to €30M with break-even points. The section also includes risk aversion (exponential utility at three risk tolerances), a pessimistic scenario, LS ×3 and ÷3, the "half effect" case, value of information, and the non-monetary objectives (life safety, terrace owners, access). **Not propagated:** uncertainty in the intervention costs, which are team estimates. The Q&A offered municipal unit costs, and the text admits they weren't used. The rule that a measure moves events to their lower bound is arbitrary; it is tested once, at half effect. |

**Other points:** Only the median wall is analysed. Section 1.4 promises each risk class its own measure, but no class-level decision is shown. Table 3.3 and Figure 3.2 repeat the same numbers.

**Best improvements per hour:**
1. Rerun the decision for one red type-1 wall and one green wall. The script exists, so about 2 hours. This shows whether the class-to-measure mapping is backed by the analysis.
2. Give the costs of A1, A3 and A4 a range and add a small tornado chart of E[C] over the cost inputs. 1–2 hours.
3. Shrink Figure 3.2 or merge it with Table 3.3, and use the space for a short qualitative table of the non-monetised objectives. About 1 hour.

---

## 4.1 Regression analysis (10 %) — **8**
Length is about 1.25 pages.

| Element | Verdict |
|---|---|
| Adequate regression for predicting future trends | **Met.** Linear vs. step model for renewal pace, compared by AIC; a bootstrap of the backlog to 2050; E[N] per pace and order (Table 4.2). |
| Hypothesis validation | **Met, with a caveat.** A constant pace is rejected (p = 0.04). The plan's 100 m/yr is not rejected (p = 0.58). Residuals pass Shapiro–Wilk (p = 0.43). **However**, the 2019 break was chosen *after* looking at the residuals, so its p-value of 0.007 is optimistic. With n = 12, three zero years and a normal model on non-negative lengths, the model is fragile. |
| Confidence intervals | **Met:** for the slope, the step and the recent mean, plus 90 % bootstrap bands. |
| Relevant observations | **Met.** Pace matters more than order. Ordering by β ignores wall length. The 780 m backlog could slip past 2050 at the lower bound of the pace. The height and age test shows the indicators are weak. |

**Other points:** The main regression uses only time as a predictor. The regression of β on height (n = 14) regresses model output on a model input, so it is somewhat circular. There is no figure in the section, although there is room for one.

**Best improvements per hour:**
1. Move a compact version of Figure B.7 into the section: yearly bars, the step fit and the 100 m line. About 30 minutes. A teacher reading only 4.1 currently sees no graph.
2. Justify the 2019 break with an outside event (for example the programme reorganisation or the Antea 2019 report) or a sup-F test for an unknown break, and label the step model as exploratory. About 1 hour.
3. Add one sentence on the zero years: why a normal model is acceptable here, or a Poisson/hurdle check. 1–2 hours.

---

## 4.2 Results interpretation & recommendations (10 %) — **7.5**
Length is about 1.4 pages.

| Element | Verdict |
|---|---|
| Discussed against model abstraction, data uncertainty and assumptions | **Met.** "Relative, not a NEN verdict." The section separates what is known from what is assumed, notes the 2× incident bias, and says which walls stay red in every variant. |
| Specific actions or plans from a complex analysis | **Mostly met.** Table 4.3 gives R1–R7 with timing, cost and what each needs, and flags the institutional changes (R6, R7). **But:** the column of expected *benefits* is missing, although the guide asks for benefits, uncertainties and risks. Portfolio-level advice, the core of the Q&A, gets one row (R5). R1 and R4 effectively re-prioritise named Oudegracht walls, which contradicts both the Q&A ("we do not want the analysis to focus on the prioritisation of individual Oudegracht sections") and your own 1.1 ("does not reorder the programme"). |
| Clear to non-experts | **Partly met.** The "In plain terms" paragraph and Figure 4.1 work well. Table 4.3 and the first paragraph use β, rak, werf, "class factor", NEN 8700 bands and "proven strength" without explaining them. |

**Best improvements per hour:**
1. Reframe R1 and R4 as "what the method would advise here, to be checked against the existing programme". Expand R5 into 2–3 portfolio rows: which inspection or measurement for which asset class, and the decision rule per class. 1–2 hours. This is the most visible gap for a reader who knows the Q&A.
2. Add an "Expected benefit" column (ΔE[N], number of walls whose class becomes settled, Δβ). About 1 hour.
3. Do a plain-language pass on Table 4.3 and the first paragraph. About 30 minutes.

---

## Summary

| Criterion | Weight | Score | Main missing element |
|---|---|---|---|
| 1.1 | 5 % | 8.5 | Relations between variables only in one sentence; no horizon |
| 1.2 | 10 % | 8.5 | Effect column inconsistent (A5 mislabelled); portfolio data quality not in the section |
| 1.3 | 5 % | 8 | One-at-a-time analysis despite known interactions; cost of the two-section reduction not quantified |
| 1.4 | 5 % | 8 | Portfolio path proposed but not applied |
| 2.1 | 15 % | 7.5 | Weak validation (miscalibrated type 1); no length effect |
| 3.1 | 10 % | 8 | Figure ≠ quantified tree; mostly assumed probabilities |
| 3.2 | 10 % | 8.5 | Cost uncertainty not propagated; median wall only |
| 4.1 | 10 % | 8 | Post-hoc breakpoint; no figure in the section |
| 4.2 | 10 % | 7.5 | Conflicts with the Q&A; thin portfolio advice; no benefit column |
| **Weighted (1.1–4.2)** | 80 % | **8.0** | |

**The five improvements that gain the most grade points per hour:**
1. **2.1:** report Spearman rank robustness across all variants, and add a recalibrated type-1 check (3–4 h, 15 % weight).
2. **4.2:** align with the Q&A by reframing R1/R4, adding portfolio rows and a benefit column (2–3 h).
3. **3.1:** redraw Figure 3.1 as the tree that is actually quantified (1–2 h).
4. **3.2:** rerun the decision for a red and a green wall, with cost ranges (3 h).
5. **4.1:** move the regression figure into the section and justify the 2019 break (1.5 h).

**Quick fixes, under 15 minutes each:** the A5 effect cell in Table 1.2; the I1 upper bound of 0.73; the S2 "data" caveat; the horizon in 1.1.

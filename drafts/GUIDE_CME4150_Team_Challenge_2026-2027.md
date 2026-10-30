# CME4150. Managing Uncertainty & Data — 2026-2027

## TEAM CHALLENGE

**Team number:** ____

---

## Context

### Strategic programming of maintenance, strengthening and replacement of quay walls in Municipality of Utrecht

Municipalities across the Netherlands are entering a replacement wave for their civil infrastructure. Current programming rests largely on theoretical service-life models and calculation methodologies that were written for the design of new structures. Practical experience and recent research show that the actual technical service life of many assets differs substantially, often favourably, from those predictions: reliability-based assessments of real quay walls indicate that the partial factors used in the original design are not a reliable guide to the remaining capacity, and that evidence of past performance can be used formally to update the assessed reliability (Roubos et al., 2020; Hemel et al., 2024). Structures are therefore declared to be at the end of their life on paper while they continue to perform in practice; occasionally the opposite happens and a structure deteriorates faster than expected. Both errors are expensive. The first wastes public capital and imposes years of avoidable disruption on a city; the second endangers users.

> *Figure 1. Official municipal boating map with Vecht in the north, the inner-city Oudegracht and singels, and the Vaartsche Rijn in the south, with bridges and locks marked. Source: Official Gemeente Utrecht. For interactive harbour and quay atlas: here.*

The Municipality of Utrecht faces this problem at scale. It manages more than 60 kilometres of quay walls and sheet pile walls (*kademuren en damwanden*) and some 800 fixed and movable bridges (Gemeente Utrecht, 2026a), see Figure 1.

The municipality is currently re-assessing whether these structures still comply with current laws and regulations; the inspection programme covering all quay walls and sheet pile walls is scheduled to be completed in 2030. Where a structure no longer complies, measures range from continued monitoring to the closure of a road or a bridge, and the municipality attempts to align those measures with other works so that the city stays accessible (Gemeente Utrecht, 2026a).

The portfolio is strikingly heterogeneous, and that heterogeneity is a large part of the difficulty:

- **The Wervengebied (inner city).** Along the Oudegracht, Nieuwegracht and Kromme Nieuwegracht the canals lie several metres below street level. Masonry retaining structures hold up the city: *walmuren* between the water and the wharf, *kluismuren* where a vaulted wharf cellar fronts the water directly, and *werfmuren* retaining the street behind the wharf. The system originates in a medieval harbour complex in which merchants moved goods directly from the water into cellars beneath the canal houses (Erfgoed Utrecht, n.d.). The ensemble is a national monument (*rijksmonument*) and is structurally interlocked with roughly 1,000 wharf cellars belonging to some 750 private owners. The recovery programme covers 3.82 km of walmuur, 1.3 km of kluismuur, close to 1,000 cellars and 25 bridges, and runs until 2050 at a pace of roughly 100 m of wall and 35 cellars per year (Gemeente Utrecht, 2026b). That pace is set by budget, execution capacity and tolerable disruption, not by the condition of the structures.
- **The twentieth-century network.** Along the Vecht, the Kromme Rijn, the Vaartsche Rijn, the singels, Leidsche Rijn and the industrial harbours, steel and concrete sheet piling and concrete quay walls were installed largely in the second half of the twentieth century, in many cases replacing earlier timber structures. Documentation quality varies widely, and the governing deterioration mechanisms, such as corrosion, timber pile decay, concrete degradation, differ fundamentally from those acting on historic masonry.
- **The Merwedekanaal.** Rijkswaterstaat currently owns and manages this canal. The municipality is preparing to take ownership, with day-to-day management passing to the regional water authority HDSR; the transfer is planned for the first quarter of 2027. The municipality expects to inherit deferred maintenance on bridges, locks and quays, and is at present surveying the condition of those assets and the way the banks were built (Gemeente Utrecht, 2026c). Programming an asset group whose condition is not yet known, and whose date of acquisition is itself uncertain, is a live problem rather than a hypothetical one.

The uncertainties are varied. The structures are largely hidden below ground and water, so condition is inferred rather than observed. Construction details of older assets are frequently unknown. Deterioration is driven by processes that are themselves uncertain and increasingly non-stationary: groundwater fluctuation and drought acting on timber pile foundations, bacterial and fungal decay, corrosion, masonry degradation, scour, and pressure from the roots of trees. Demands on the assets are changing too, through urban densification, heavier vehicles and construction traffic, vessel impact and mooring, and a changing climate, for which the KNMI'23 scenarios project drier summers, wetter winters and more extreme rainfall (KNMI, 2023). On top of this sits a layer of organisational and financial uncertainty: annual budgets, contractor and engineering capacity, cost escalation, permitting, the willingness and ability of private cellar owners to act, and the tolerance of residents and businesses for years of works. Finally, the assessment rules themselves are a source of uncertainty: they embed safety margins calibrated for new design, and evidence of 'proven strength' suggests that the margin between calculated and actual capacity is itself an uncertain quantity worth estimating (Roubos et al., 2020; Hemel et al., 2024).

---

## Your assignment

As data and uncertainty analysts advising the Municipality of Utrecht, your team is asked to develop insight and an actionable approach for the strategic programming of maintenance, strengthening and replacement of quay walls. The assignment is explicitly **not** about designing a single structure. It is about producing a methodology, decision framework or model that lets the municipality make better strategic choices when the evidence is incomplete.

Note that your team can analyse a designated stretch (e.g., a section of the inner-city canals, a stretch along the Vecht, the Vaartsche Rijn or the Leidsche Rijn, or a bank of the Merwedekanaal) or a portfolio-level analysis covering several stretches.

Below are examples of specific tasks that are useful in problems of this kind. They are ideas, not requirements. You are free to take a different route, to address only some of them, or to devise your own, provided you justify the choice in Section 1.4. What matters is that the uncertainty is quantified rather than mentioned, that the data handling is reproducible, and that the analysis ends in a decision.

1. **Scope the problem and name the dominant uncertainties.** Choose the assets you will analyse: a designated stretch (e.g., a section of the inner-city canals, a stretch along the Vecht, the Vaartsche Rijn or the Leidsche Rijn, or a bank of the Merwedekanaal) or a portfolio-level analysis covering several stretches. Describe their structural typologies, approximate age and construction, the loads they carry and the functions they serve: retaining ground and street, carrying traffic and trees, mooring and navigation, water level and water quality, heritage value, and ecology. State the decision the municipality has to make and over which horizon, which regulatory and institutional instruments genuinely constrain it, and where the dominant uncertainties lie.
    - Draw the system boundary explicitly. Does a privately owned wharf cellar belong to your system? Does the road on top, and the cable duct inside it?
    - Classify the uncertainties you face and argue which of them the municipality could actually reduce (and at which temporal and economic cost) and which it must simply carry.
    - State the decision variable precisely. Is it when to intervene, where to intervene first, how much to inspect, or how fast to spend? These are different problems with different answers.
    - Map the stakeholders whose objectives conflict (residents, businesses, cellar owners, heritage authority, water authority, cyclists, freight) and note which of those conflicts your analysis will and will not resolve.
2. **Assemble the evidence and confront theory with observed performance.** Collect what is publicly available, generate what you additionally need, and state your assumptions and their provenance. Relevant information includes inspection and monitoring records, field and proof testing, documented failures elsewhere, and the 'proven strength' implied by decades of survival under load. Reflect on how the gaps in this evidence limit what you can conclude.
    - Build a small structured dataset of the assets in your scope from public sources, and document its provenance, completeness and known errors. A data quality table is often more informative than the data itself.
    - Exploit proxy data: satellite-based deformation from the bodemdalingskaart, groundwater levels from the BRO, tree registers, traffic counts, dredging and water-level records, street-level imagery over time.
    - Take one asset and contrast its code-based assessment outcome with its observed service history; state what the discrepancy implies for the rest of the portfolio.
3. **Establish which variables actually drive the outcome.** Identify the variables at play and determine whose variability changes the answer and whose does not. This is also the municipality's own question: where should a limited inspection and monitoring budget be spent across more than 60 kilometres of structures?
    - Run a sensitivity analysis and be clear about what your chosen method can tell you.
    - Reduce the problem deliberately: fix variables at defensible values, aggregate assets into homogeneous classes, or represent a stretch by a few characteristic cross-sections. Justify each reduction and estimate what accuracy it costs you.
    - Turn the result into an inspection strategy: which measurement would most reduce the variance of your output, and on which assets?
4. **Build probabilistic models of deterioration and demand.** Represent the relevant degradation processes and their drivers, and the future demands placed on the assets, treating dependence between assets and between drivers explicitly rather than assuming it away.
5. **Decompose a 'rich' undesired event.** Establish what it means for the programming of quay walls to fail, technically, but also in human and organisational terms, break it down into causal paths, quantify the basic events and propagate the probabilities.
    - Consider candidate top events beyond structural collapse: an unplanned emergency closure of a quay or street; damage during works; an asset replaced with decades of life still in it; a programme so far behind that risk accumulates faster than it is retired; heritage value destroyed by the very intervention meant to save it.
    - Include human and organisational basic events: an inspection not carried out or misread; drawings that do not match what is in the ground; a permit or an owner's consent that never arrives; budget reallocated mid-programme.
    - Quantify basic events from records, literature or elicitation, and mark clearly the ones for which you had nothing and assumed.
    - Handle common-cause failure deliberately: a shared ground profile, a shared design era, a single inspection contractor, a single assessment convention applied portfolio-wide.
6. **Compare interventions and programme them under real constraints.** Structure the full range of alternatives: doing nothing and continuing to monitor; restricting use (load limits, traffic restrictions, closure); maintenance that preserves existing functionality; life-extension and strengthening (renovation, foundation improvement, relieving structures, load reduction); replacement at the end of life; and improvement or expansion that adds functionality, such as nature-friendly banks, ecological integration, circular or demountable structures, and climate adaptation. Weigh these against annual budget, contractor and engineering capacity, permissible disruption and accessibility, heritage requirements, dependency on private owners, coordination with other works, and financial risks including inflation, cost escalation and the discount rate applied to long-lived public investments.
7. **Extrapolate towards 2050.** Predict outcomes under alternative futures, or under alternative municipal actions: for instance how measurable indicators relate to condition and remaining service life, or how annual budget and production rate translate into backlog and risk exposure over time.
8. **Prepare actionable recommendations.** Integrate the analyses into a substantiated recommendation stating what is known, what is assumed, which programming direction you propose, and what the municipality should measure next in order to reduce the uncertainty that currently dominates the decision. You may also flag which of your recommendations need an institutional or regulatory change rather than money.

---

## Available information and data

The assignment is designed to be completed with publicly available information, supplemented by defensible assumptions, expert judgement and generated data. Dealing with limited and inconsistent information is an integral part of the research assignment, and the quality of your reasoning about what is missing will be assessed. Your team may submit **one** concrete and justified data request through the teaching team, which will be forwarded to the Municipality of Utrecht. Provision is not guaranteed.

Useful public starting points:

- Open data catalogue of the Municipality of Utrecht: data.utrecht.nl and open.utrecht.nl
- Municipal map viewer (including the Wervengebied implementation plan): kaart.utrecht.nl
- Knowledge centre for the wharf district, including technical guidance and the Wervenkadaster: kenniscentrum-werven.utrecht.nl
- Council documents, programme plans, progress and budget reports: utrecht.bestuurlijkeinformatie.nl
- National geo-information (BGT, BAG, topography, aerial imagery): pdok.nl
- Subsurface data: CPTs, borings, groundwater monitoring: Basisregistratie Ondergrond, broloket.nl
- Elevation and deformation: ahn.nl and the national subsidence map, bodemdalingskaart.nl
- Climate projections and effects: KNMI'23 scenarios, knmi.nl/klimaatscenarios, and the Klimaateffectatlas
- Population, households and economic statistics: cbs.nl
- Regional water authority HDSR (water levels, dredging, permits): hdsr.nl
- Comparable programmes elsewhere, with published programme plans and progress reports: Amsterdam's Programma Bruggen en Kademuren, covering 829 bridges and about 205 km of founded quay walls: openresearch.amsterdam

---

## Regulatory and institutional framework

Your recommendations must be usable inside the frameworks that actually govern these decisions. The list below is a starting point, not a checklist. Identify which instruments genuinely constrain your chosen scope and state how they shape the interventions you propose and the safety level you adopt. Note that several of these instruments are part of the problem rather than only its solution: they were largely written for the design of new structures, and applying them unmodified to ageing assets is precisely what produces the conservatism the municipality is questioning.

- **Assessment of existing structures.** The NEN 8700 series — NEN 8700 (basic rules), NEN 8701 (actions) and NEN 8707 (geotechnical structures, which is the relevant part for quay walls and sheet piling) — sets the safety levels for assessing existing structures at renovation and at disapproval, below those required for new build: nen.nl — constructieve veiligheid bestaande bouw
- **Design codes.** Eurocodes NEN-EN 1990 (basis of structural design) and NEN-EN 1997 with the Dutch NEN 9997-1 (geotechnical design), which define the partial factor and reliability framework your assessment inherits.
- **Quay-wall specific guidance.** CROW/CUR Handboek Binnenstedelijke kademuren, covering inspection, management and maintenance and the steps for assessing existing quay walls for adaptation, renewal or retention — including a revised clause on loading by tree roots: crow.nl — Binnenstedelijke kademuren; CUR 166 Damwandconstructies for sheet pile structures; the CROW Handboek Oeverconstructies for risk-driven management of bank constructions; and the Platform Binnenstedelijke Kademuren (BiKa) network.
- **Assessment practice for civil structures.** Rijkswaterstaat's Richtlijnen Beoordeling Kunstwerken (RBK) and Richtlijnen Ontwerp Kunstwerken (ROK), the national reference for assessing and designing existing civil structures: rijkswaterstaat.nl — bouwrichtlijnen kunstwerken
- **Condition assessment.** NEN 2767-4, the standard for uniform condition measurement of infrastructure including quay walls, which is how condition scores feeding multi-year maintenance plans are generated: nen.nl — normen conditiemeting
- **Asset management.** NEN-ISO 55000/55001 for asset management systems, and the Dutch public-sector asset management platform iAMPro: iampro-portaal.nl
- **Environmental and building law.** The Omgevingswet and the Besluit bouwwerken leefomgeving (Bbl), which set the requirements applicable to existing structures and the obligation to periodically assess structural safety: iplo.nl — periodiek beoordelen constructie; and the Utrecht omgevingsplan and omgevingsvisie for local rules.
- **Heritage.** The Erfgoedwet together with the monument provisions of the Omgevingswet. Large parts of the Utrecht canal system are protected as rijksmonument and lie within a protected townscape, which constrains which interventions are admissible at all: wetten.overheid.nl — Erfgoedwet, monumentenregister.cultureelerfgoed.nl
- **Water.** The waterschapsverordening of Hoogheemraadschap De Stichtse Rijnlanden for works in and along water, and the EU Water Framework Directive as the driver behind nature-friendly banks and water-quality objectives: hdsr.nl, EU Water Framework Directive
- **Public finance and appraisal.** The Besluit begroting en verantwoording provincies en gemeenten (BBV), which governs how a municipality may capitalise and depreciate replacement investments and therefore constrains what 'cheaper' means in practice, and the national guidance on the discount rate for social cost-benefit analysis: Rapport Werkgroep discontovoet 2025

---

## References

- Gemeente Utrecht. (2026a). *Onderzoek bruggen en kademuren.* [https://www.utrecht.nl/wonen-en-leven/onderhoud-openbare-ruimte/onderzoek-bruggen-en-kademuren](https://www.utrecht.nl/wonen-en-leven/onderhoud-openbare-ruimte/onderzoek-bruggen-en-kademuren)
- Gemeente Utrecht. (2026b). *Herstel werven.* [https://www.utrecht.nl/wonen-en-leven/bouwprojecten-en-stedelijke-ontwikkeling/bouwprojecten/binnenstad/herstel-werven](https://www.utrecht.nl/wonen-en-leven/bouwprojecten-en-stedelijke-ontwikkeling/bouwprojecten/binnenstad/herstel-werven)
- Gemeente Utrecht. (2026c). *Merwedekanaal van Rijk naar gemeente en waterschap.* [https://www.utrecht.nl/wonen-en-leven/onderhoud-openbare-ruimte/merwedekanaal-van-rijk-naar-gemeente-en-waterschap](https://www.utrecht.nl/wonen-en-leven/onderhoud-openbare-ruimte/merwedekanaal-van-rijk-naar-gemeente-en-waterschap)
- Gemeente Amsterdam. *Programmaplan Bruggen en Kademuren and progress reports.* [https://openresearch.amsterdam/nl/page/56187/programmaplan-bruggen-en-kademuren](https://openresearch.amsterdam/nl/page/56187/programmaplan-bruggen-en-kademuren)
- Gemeente Amsterdam / AMS Institute. *Living Lab Levensduurverlenging (life-extension of quay walls).* [https://openresearch.amsterdam/nl/page/50181/living-lab-levensduurverlenging](https://openresearch.amsterdam/nl/page/50181/living-lab-levensduurverlenging)
- Hemel, M.-J., Peters, D. J., Schweckendiek, T., & Jonkman, S. N. (2024). Reliability updating for lateral failure of historic quay walls. *Georisk: Assessment and Management of Risk for Engineered Systems and Geohazards, 18*(4), 882–903. [https://doi.org/10.1080/17499518.2024.2302141](https://doi.org/10.1080/17499518.2024.2302141)
- Roubos, A. A., Schweckendiek, T., Brinkgreve, R. B. J., Steenbergen, R. D. J. M., & Jonkman, S. N. (2020). Finite element-based reliability assessment of quay walls. *Georisk: Assessment and Management of Risk for Engineered Systems and Geohazards, 15*(3), 165–181. [https://doi.org/10.1080/17499518.2020.1756344](https://doi.org/10.1080/17499518.2020.1756344)
- TU Delft. (2023). *Nieuw model voorspelt de veiligheid van Amsterdamse kademuren.* [https://www.tudelft.nl/2023/tu-delft/nieuw-model-voorspelt-de-veiligheid-van-amsterdamse-kademuren](https://www.tudelft.nl/2023/tu-delft/nieuw-model-voorspelt-de-veiligheid-van-amsterdamse-kademuren)
- CROW. (n.d.). *Binnenstedelijke kademuren* [handbook for inspection, management, maintenance and assessment of urban quay walls; includes the revised clause on loading by tree roots]. [https://www.crow.nl/kennisproducten/binnenstedelijke-kademuren/](https://www.crow.nl/kennisproducten/binnenstedelijke-kademuren/)
- KNMI. (2023). *KNMI'23-klimaatscenario's.* [https://www.knmi.nl/klimaatscenarios](https://www.knmi.nl/klimaatscenarios)
- Erfgoed Utrecht. (n.d.). *De Utrechtse werven.* [https://erfgoed.utrecht.nl/verhalen/de-utrechtse-werven](https://erfgoed.utrecht.nl/verhalen/de-utrechtse-werven)

---

# Report template

*This document is provided as a template for reporting your work. You may use Word, LaTeX, or other text editors to complete your report. Delete the context and all the comments in blue and complete each section. Note that each section relates to an aspect considered in the rubric for your assessment. Each section will be evaluated independently (several teachers will evaluate different sections), so make sure each section is self-explained and contains adequate references to previous sections if needed.*

*Information exceeding the maximum section length will not be considered.*

| Section | Title | Max length |
|---|---|---|
| 1.1 | Problem synthesis & goal definition | 0.5 page |
| 1.2 | Assumptions, data collection & generation | 2 pages |
| 1.3 | Problem exploration and dimension reduction | 1.5 page |
| 1.4 | Approach selection | 1 page |
| 2.1 | Probabilistic models | 2 pages |
| 3.1 | Fault tree construction | 3 pages |
| 3.2 | Trade-off analysis | 3 pages |
| 4.1 | Regression analysis | 1.5 pages |
| 4.2 | Results interpretation and proposed recommendations | 1.5 page |
| — | Use of AI for the assignment and integrity issues | no limit |
| — | Appendices | no limit |

## 1.1 Problem synthesis & goal definition (max 0.5 page)

*Task description:* Define the scope of your problem and the specific goal(s). Considering your specific scope, analyze the main sources of uncertainty that should be considered in the analysis. You may focus on the most relevant ones that may affect the project progress and thus, have a larger impact on the results. Justify your choices.

## 1.2 Assumptions, data collection & generation (max 2 pages)

*Task description:* Describe/represent the needed data and how is relevant to the identified problem (described in 1.1). You may consider references in data records, literature, or stakeholder elicitation.

Generate other data that you can need. Explain the process and input data to guarantee reproductivity of your results.

Indicate sound assumptions to support the problem analysis when data is not available.

Link to the interpretation of the results in 4.2 and reflect on to what extent the lack of data accuracy or uncertainty associated with the data assumptions may impact your analysis and results; Discuss and validate the use of the assumptions in the analysis.

This section provides an overview. Use the Appendices to add supporting information if you need it.

## 1.3 Problem exploration and dimension reduction (max 1.5 page)

*Task description:* Identify the variables playing a role in your problem and analyse how their levels of variability/uncertainty might affect the final result.

Reflect on the results. For example: To what extent a specific variable really makes a change to the results? Do the results correspond to your beliefs? How does the lack of accuracy of the data you use affect the results? On which datasets require more attention?, or which estimations can be made without a significant loss of credibility in the obtained conclusion?

Make decisions on those variables that you should invest more effort in reducing their variability to improve the accuracy of your results and indicate those variables whose variability can be neglected.

Justify the process and the use of specific tools for the analysis.

## 1.4 Approach selection (max 1 page)

*Task description:* Explain/represent the approach you will follow to achieve your goal.

You can use a flowchart or graphical representation to convey the main idea. You can provide both, the general picture and a detailed description of the tools and methods, avoiding definitions of the methods or other trivial information.

Motivate on what and why you choose specific modelling tools and uncertainty quantification methods for the analysis. You may compare relevant tools you learned in the course and choose the adequate ones considering the defined problem and available data.

## 2.1 Probabilistic models (max 2 pages)

*Task description:* To perform the risk analysis (Sections 3.1 and 3.2), you will need to create probabilistic models. Identify the relevant variables and clarify the (in)dependence between those variables.

Construct adequate probabilistic models with explicit consideration of the dependence between the variables. You may consider using uni- or multi-variate probability distributions to describe or quantify the randomness in the data. You may apply different parameter estimation techniques.

Justify the selection of the model(s) and evaluate the model quality or validity, for example: Does the model fit well with the data? To what extent is the model valid to represent the data?

Use the Appendices to add supporting information if you need it.

## 3.1 Fault tree construction (max 3 pages)

*Task description:* Identify a 'rich' undesired event associated with the failure of the municipality's quay wall programming to deliver its intended function, which can be broken down into different causal paths. You may consider distinguishing the paths from a technical perspective, a human factors perspective, and/or an organizational perspective. Your creativity and research initiative will be appreciated here!

Quantify the occurrence probabilities of the basic events in your fault, based on data records, a literature study, or a structured expert judgment study.

Propagate the probabilities through your tree, by analytical methods and/or Monte Carlo simulations in case the basic events might occur due to (partial) common causes.

Present and interpret the results, for example: Do the (numerical) results correspond to your beliefs? What are the most sensitive components in your system? What other data would be needed to elaborate the trees in further detail?

Discuss the main difficulties - if any - encountered with decomposing the system and processing the data. Explain to what extent data availability or quality issues may have impacted your analysis. In particular, reflect on the role of the technical, human and organizational factors in your model. Under what conditions can conclusions be drawn based on the decomposed system and the collected data?

## 3.2 Trade-off analysis (max 3 pages)

*Task description:* The 'rich' undesired event broken down into different causal paths in 3.1 will be used in 3.2 to analyze the possible interventions to reduce the occurrence probability of the undesired event. You may consider interventions from a technical perspective, a human factors perspective, and/or an organizational perspective. Again, your creativity and research initiative will be appreciated here!

Structure and systematically investigate the interventions in a decision tree in order to compare the costs and benefits of your decision alternatives.

Also here present and interpret the results, for example: Do the results correspond to your beliefs? What are the most effective interventions in your system? What other data would be needed to elaborate the decision tree in further detail? Which decision alternative is preferred from a rational risk-neutral optimization procedure? Which decision alternative is preferred from a risk-averse procedure?

Reflect on the procedure and results of your trade-off analysis.

Can all conflicting objectives be quantified? Discuss the main difficulties encountered with trading off the objectives processing the data.

Explain to what extent data availability or quality issues may have impacted your analysis. In particular, reflect on the role of the technical, human and organizational factors in your model. Under what conditions can conclusions be drawn based on the optimal interventions and the collected data?

To what extent are the proposed intervention measures to reduce the occurrence frequency of undesired events in your construction project effective?

## 4.1 Regression analysis (max 1.5 pages)

*Task description:* Make educated guesses to predict other outcomes and future trends, to investigate future scenarios or to inform the Municipality of Utrecht about alternative outcomes if specific actions are taken. Validate the assumed hypothesis. You may also estimate the confidence intervals.

You may include graphs to support statements, and use the Appendix to add other supporting information.

## 4.2 Results interpretation and proposed recommendations (max 1.5 page)

*Task description:* Discuss the obtained solution by linking the results to the level of abstraction of the selected models, data uncertainty, and assumptions made. Discuss and justify the soundness of the results.

You may include graphs to support statements, and use the Appendix to add other supporting information.

Based on the interpretation of the result, what is the recommendation that you will give to the Municipality of Utrecht? Try to communicate the results to non-experts in data and uncertainty management. You may suggest feasible interventions, expected benefits, associated costs, uncertainties, and risks, as well as potential synergies with other transport and spatial planning initiatives.

## Use of AI for the assignment and integrity issues (no page limit)

Acknowledge and reference the AI tools used. Add an explanation of how you utilized these tools for specific parts of the assignment, the prompts you employed to obtain the results, how you verified the generated output, and how you safeguarded academic integrity.

It is acceptable to use AI to check grammar and spelling in a text, generate ideas by compiling information from various sources in an accessible manner, summarize or expand texts and concepts, and search for pieces of code, among other tasks. In essence, AI can serve as a supportive tool to enhance the quality of your work. Remember that despite its name, AI is not intelligent. Chatbots merely identify patterns in language but do not understand it. So, be very critical of their use.

## Appendices (no page limit)

This information won't be assessed, however, it will serve to justify and support statements in the previous sections.
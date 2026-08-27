# Experimental sufficiency, generality, scale, and appendix audit

Judge experiments against the scope and causal strength of the paper's live claims. Do not reward volume by itself or demand an unrelated standard battery.

## Build an experimental completeness ledger

For every important empirical claim, record:

| Claim | Tasks/data | Models/settings | Baselines and fairness | Analysis unit and N | Repeats/uncertainty | Reproducibility details | Boundary tested | Verdict |
|---|---|---|---|---|---|---|---|---|

## Completeness and reproducibility

Check whether the paper supplies enough information to interpret and reproduce the reported result without material guessing:

- dataset provenance, license or collection process where relevant, splits, exclusions, leakage controls, preprocessing, and sampling;
- model/backbone versions, initialization or checkpoints, training and inference procedures, prompts, decoding, stopping, and post-processing;
- objective, optimizer, schedules, hyperparameters, selection criteria, early stopping, and tuning budget;
- metrics, direction, aggregation, analysis unit, denominators, missing-data handling, and evaluation protocol;
- number of independent seeds, runs, examples, participants, annotators, tasks, or environments as appropriate;
- uncertainty intervals, variance, pairedness, statistical tests, multiple-comparison handling, and effect sizes when the claim needs them;
- hardware, compute budget, runtime, memory, and resource comparison when efficiency or practicality is claimed;
- code, data, artifacts, or exact procedures needed to audit generated results.

## Superiority and numerical displays

A claim of superiority must be visible in a main-text table or figure whose numbers are readable and independently interpretable. Require:

- the closest and strongest relevant baselines, not only weak or outdated comparators;
- comparable data, model capacity, information access, tuning budget, and evaluation protocol;
- clearly labeled metrics, units, direction, aggregation, and analysis population;
- sample size or analysis unit plus uncertainty/statistical support where meaningful;
- raw or sufficiently precise values, not only ranks, colors, boldface, or prose summaries;
- disclosure of negative cells, failures, and selection rules that could reverse the ordering.

Bolded best values do not establish significance. A numerically higher mean does not establish reliable superiority without suitable uncertainty when stochastic or sampled variation is material.

## Generality and scale

Match required breadth to the wording of the claim:

- A narrow claim may be supported by a focused experiment.
- A cross-domain, architecture-agnostic, model-agnostic, robust, universal, or generally applicable claim requires variation across the corresponding datasets, tasks, domains, backbones, scales, seeds, perturbations, or environments.
- One dataset, one backbone, one seed, or one favorable operating point cannot support universal language.

Judge effective experimental scale, not raw run count. Consider independent datasets/tasks, model families and sizes, seeds, samples or participants, time horizons, operating conditions, baselines, and effective sample size. Repeated measurements on the same underlying unit do not automatically create independent evidence. State the smallest additional experiment that would materially increase confidence in each unsupported live claim.

## Appendix length and role

Use the compiled PDF and identify the first appendix page and final appendix page. Report the exact count and counting convention. Exclude the main paper and a separately placed bibliography from the appendix count; if references are embedded within the appendix, report both the literal page span and the appendix-content count when separable. Count a formal supplement that functions as the appendix and disclose separate files.

- **20 pages or fewer:** passes the default length target.
- **21--30 pages:** overlong. Treat as a substantive presentation/completeness defect and normally prevent an 8/10 recommendation unless the excess is convincingly justified and highly navigable.
- **More than 30 pages:** hard format failure under this rubric; flag prominently and materially reduce the score.

An explicit venue or user-specified page rule overrides these defaults. Regardless of length, the appendix may deepen evidence but may not carry the only support for a central acceptance-facing claim.

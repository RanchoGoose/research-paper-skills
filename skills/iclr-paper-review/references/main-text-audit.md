# Main-text self-containment and all-visual audit

Use this reference for empirical papers and any paper whose argument depends on figures or tables. Audit every figure and table in both the main paper and appendix; apply the additional self-containment and evidence-visibility gate to the main paper.

## Abstract gate

Read the abstract once before the paper and again after reconstructing the full argument. The second reading determines the verdict.

The abstract must provide one compact, logically connected account of:

- the problem and why it matters;
- the proposed method or conceptual mechanism;
- the main evidence-backed finding;
- the actual scientific contribution;
- the most material scope condition, limitation, or boundary needed to prevent overreading.

It must remain a summary, not a compressed appendix. Flag as excessive detail:

- multiple exact scores, decimals, confidence intervals, $p$-values, ranks, or per-dataset results;
- sample counts, hardware, hyperparameters, schedules, implementation mechanics, and long metric definitions;
- enumerations of secondary ablations or every experimental branch;
- explanatory detours that belong in the introduction, method, or discussion.

A single headline magnitude may be retained only if removing it would make the contribution materially less informative. Prefer qualitative direction and calibrated scope over a list of numbers.

Check coverage against the completed claim-to-evidence ledger, not against the paper's contribution bullets. The abstract fails coverage if it omits a central problem/method/result, presents a secondary result as the paper's center, hides an important limiting condition, or claims a breadth the full paper does not establish. Complete coverage does not require naming every dataset, baseline, metric, or experiment.

Report one verdict: **passes**, **too long/detailed**, **incomplete**, **unclear**, or a combination. Explain whether the defect is cosmetic or changes the scientific interpretation and score.

## Main-text gate

Assume a time-constrained reviewer may not read the appendix. The main paper must contain, in a self-contained form:

- the core problem and why it matters;
- the complete method at the level needed to understand the contribution;
- definitions of central concepts, mechanisms, variables, and metrics;
- decisive baselines and controls;
- primary positive and negative results;
- uncertainty or inferential status needed to interpret those results;
- material failure modes, scope boundaries, and the final conclusion.

The appendix may contain implementation detail, extended grids, additional proofs, qualitative galleries, sensitivity analyses, or reproduction material. It may not be the only location of evidence required to believe a central contribution.

## Prose-only experimental claim search

Scan the main text for:

- isolated numbers, confidence intervals, $p$-values, wins, ranks, percentages, or speedups;
- “we outperform,” “best,” “top,” “improves,” “degrades,” “robust,” “unchanged,” “no difference,” “scales,” or “only”;
- claims that a mechanism, component, or boundary is established;
- important null, negative, safety, cost, or failure findings.

For each, identify a main-text table or figure that visibly carries the evidence. If none exists, classify it as a substantive evidence-visibility defect. Interpretation may remain in prose; decisive empirical evidence may not.

## Cross-reference and placement audit for every visual

For every figure and table in the main paper and appendix, verify:

1. It is cited in prose by the correct number before or near its appearance.
2. Every panel, row, column, or cell invoked by the prose actually exists and has the stated label.
3. The prose points to the exact visual evidence that supports the sentence rather than to a loosely related visual.
4. Numbering, labels, and references are consistent after compilation; there are no orphan visuals, unresolved references, duplicate labels, or misleading forward references.
5. A main-text claim that depends on an appendix visual is identified as an appendix-dependence defect when the evidence is central.

Record uncited, miscited, or ambiguously cited visuals even if their content is otherwise correct.

## Audit every figure

Record whether it is in the main text or appendix, plus figure number, page, first prose citation, role, asserted conclusion, and verdict. Check:

1. **Placement and size:** appears near first use; not stranded, clipped, or undersized.
2. **Legibility:** labels, tick marks, annotations, legends, and panel letters are readable at normal page scale.
3. **Encoding:** colors, line styles, markers, and ordering are distinguishable, color-blind aware, and not dependent on color alone.
4. **Axes and scale:** units, baselines, limits, transformations, truncation, and normalization are explicit and non-misleading.
5. **Caption self-containment:** states what is measured, compared, aggregated, and uncertain; defines nonstandard abbreviations.
6. **Comparators:** includes the methods and controls needed for the claimed conclusion; omitted arms are justified.
7. **Statistics:** analysis unit, repetitions, uncertainty, and tests match the visual claim; error bars are defined.
8. **Selection risk:** examples, seeds, prompts, checkpoints, horizons, or panels are not selectively chosen without disclosure.
9. **Text consistency:** values, labels, directions, and conclusions agree with the prose and other tables.
10. **Scientific function:** the conclusion is visible from the figure and the figure rules out the relevant alternative.

For qualitative figures, additionally check whether examples share inputs/seeds where comparison requires it, whether failures are shown, and whether the figure is evidence or illustration.

## Audit every table

Record whether it is in the main text or appendix, plus table number, page, first prose citation, role, asserted conclusion, and verdict. Check:

1. **Placement and density:** readable at normal scale; no clipping, microscopic font, extreme compression, or page-breaking confusion.
2. **Rows and columns:** comparison objects, metrics, directionality, units, sample counts, and analysis units are explicit.
3. **Caption and notes:** self-contained; defines aggregation, uncertainty, significance, bolding, dashes, and abbreviations.
4. **Comparator completeness:** includes the closest baseline, claimed mechanism controls, and relevant ablations.
5. **Statistical expression:** estimates, variability/intervals, repetitions, and tests match the claim.
6. **Evidence level:** confirmatory, unresolved, and descriptive results are visually distinguishable; a null is not presented as equivalence.
7. **Bolding and ranking:** emphasis follows a stated, defensible rule and does not turn descriptive noise into significance.
8. **Consistency:** numbers and conclusions match the prose, appendix, generated artifacts, and other tables.
9. **Selectivity:** no unexplained metric, dataset, seed, prompt, or horizon omission.
10. **Claim support:** the result needed for each stated conclusion is directly visible.

## Layout defects that affect the score

Treat layout as substantive when it prevents verification, hides uncertainty, merges evidence levels, encourages a misleading comparison, or forces important results out of the main paper. Dense but readable presentation is not automatically fatal; explain its effect on comprehension and evidence hierarchy.

## Audit summary

End with:

- whether the main text is acceptance-self-contained;
- which figures/tables fully support their intended claims;
- which are uncited, miscited, ambiguously cited, or inconsistent with the prose;
- which are readable but scientifically incomplete;
- which are misleading or unverifiable;
- every decisive result still carried only by prose or appendix;
- the smallest revision that restores visibility without indiscriminately adding material.

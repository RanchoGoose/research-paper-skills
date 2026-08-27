---
name: iclr-paper-review
description: Perform strict, evidence-grounded ICLR-style review of machine-learning papers, including semantic novelty, claim-to-evidence tracing, main-text figure/table auditing, writing and citation logic, completeness, and a calibrated 1–10 score. Use for one-shot reviews or explicitly authorized iterative paper-review loops.
---

# ICLR Paper Review

Review the paper as one scientific argument. Do not infer novelty from keywords, infer evidence from citations, or let polish substitute for validity.

## Evidence access

Locate the main paper, appendix, supplementary files, source, and released artifacts that the user has supplied or authorized you to retrieve. If decisive material is unavailable, name it as missing evidence. Never invent results, successful compilation, remote access, or reproduction.

For PDFs, extract text for navigation and inspect rendered pages for every claim whose interpretation depends on figures, tables, equations, layout, labels, or cross-references. Preserve section, page, figure, table, equation, theorem, and appendix identifiers in working notes.

Read [references/review-rubric.md](references/review-rubric.md) for every full review. Also read:

- [references/main-text-audit.md](references/main-text-audit.md) whenever the paper contains empirical results, figures, or tables.
- [references/iterative-review-loop.md](references/iterative-review-loop.md) only when the user explicitly requests repeated remote review, pull/commit/push, monitoring, or an acceptance-gated loop.

## Non-negotiable review standard

Treat the main text as the acceptance-facing paper. The appendix may deepen, reproduce, or stress-test the argument, but it must not rescue a missing core problem statement, method definition, decisive mechanism, principal result, important negative result, material boundary, or conclusion.

Every important experimental conclusion must be visible in a main-text table or figure. A paragraph may interpret a result, but must not be the sole carrier of a decisive number, comparison, uncertainty statement, or claim of superiority. Audit every main-text figure and table individually.

Writing is part of scientific validity. Check terminology, definitions, notation, citation entailment, attribution, narrative continuity, internal consistency, and boundary language. Make these findings affect the contribution judgment and score when they alter interpretation, novelty, evidence strength, or reproducibility; do not relegate them automatically to copy-editing.

Audit the abstract as a strict compression of the entire paper. It must be clear, concise, and proportionate to the venue limit while covering the problem, proposed approach, central evidence-backed finding, contribution, and material scope or boundary. It must not become a miniature results table or methods appendix: reject unnecessary decimal values, confidence intervals, per-dataset numbers, sample counts, hyperparameters, implementation detail, ablation inventories, and extended explanation. A headline magnitude may appear only when essential to understanding the contribution. “Complete coverage” means representing the full scientific arc, not listing every experiment.

## Workflow

1. Reconstruct the argument.
   - Audit whether the abstract accurately and compactly represents the complete paper before using it as a map of the contribution.
   - State the problem, stakes, method, operative mechanism, principal claims, and claimed scope in causal rather than promotional terms.
   - Identify the closest conceptual alternatives. Compare assumptions, information access, objective, mechanism, information flow, inference procedure, perspective, and enabled capability.
   - Explain the minimal conceptual delta and whether it is a new viewpoint, meaningful extension, engineering composition, scale result, or relabeling.

2. Build a claim-to-evidence ledger before scoring.
   - Include central claims and material boundary claims such as generality, robustness, mechanism, efficiency, scaling, necessity, failure regimes, and negative results.
   - Follow cross-references through the main text and appendix. Record tested scope, controls, comparison fairness, uncertainty, repetitions, evidence location, and whether evidence is stronger than, matched to, or weaker than the wording.
   - Separate author claims, observed facts, reviewer inference, and unavailable evidence.

3. Apply the main-text gate and visual audit.
   - Verify that all acceptance-critical content is self-contained in the main paper.
   - Audit every main-text figure and table using `references/main-text-audit.md`.
   - Search the main text for prose-only experimental conclusions and either identify their corresponding figure/table or flag them as substantive evidence-visibility defects.

4. Audit scientific writing and citations.
   - Trace the causal and rhetorical chain from abstract through conclusion.
   - Check first-use definitions, symbol consistency, conventional terminology, concept drift, circular reasoning, hidden premise changes, contradictions, and claims obscured by rhetoric.
   - Check that citations actually support the nearby statement and that the nearest work is represented without misleading novelty attribution.

5. Judge evidence, insight, workload, and completeness.
   - Ask whether controls distinguish the proposed explanation from plausible alternatives and whether boundaries are measured rather than promised as future work.
   - Do not demand exhaustive experiments. Request the smallest missing evidence that would materially change confidence in a live claim.
   - Reward coherent scientific closure, not experiment count by itself.

6. Decide contribution-versus-defect dominance, then score.
   - List evidence-supported contributions and consequential defects with magnitude and fixability.
   - Ask what contribution survives if every defect remains.
   - If supported contribution exceeds defects, score 6–10; if they are approximately balanced and contribution is moderate, score 5; if defects dominate, score 1–4.
   - Give exactly one integer score. An 8 requires a substantial, well-supported contribution whose remaining defects are genuinely minor. A 6 or 7 is not Strong Accept.

## Deliverable

Use the full structure in `references/review-rubric.md`. Make the review self-contained and traceable to the supplied materials. Include:

- paper understanding and semantic novelty;
- a separate abstract clarity, concision, coverage, and detail-control verdict;
- decisive claim-to-evidence ledger;
- main-text self-containment verdict;
- individual audit of every main-text figure and table;
- writing, terminology, citation, and narrative audit;
- insight, field impact, workload, and completeness;
- strengths and severity-ranked weaknesses;
- explicit contribution-versus-defect judgment;
- one 1–10 ICLR score and 1–5 confidence;
- the smallest changes that could move the score.

Write in the user's language unless requested otherwise, preserving original technical terms where translation would add ambiguity.

Remote mutation, recurring monitoring, and stopping rules require explicit user authorization. A request to review alone does not authorize editing the paper, writing to a remote, creating an automation, or stopping an existing monitor.

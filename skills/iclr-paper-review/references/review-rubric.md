# ICLR review rubric and output contract

Use this reference for every full paper review. The review must remain evidence-grounded even when the user requests a short answer.

## Working ledgers

### Claim-to-evidence ledger

Build this before drafting and expose all decisive entries in the final review.

| ID | Claim and strength | Claim location | Evidence and location | Tested scope | Controls / alternatives | Match |
|---|---|---|---|---|---|---|
| C1 | Exact central or boundary claim | Sec./page | Fig./Table/Thm/App. | Data, tasks, models, regimes, units | What is and is not ruled out | Stronger / matched / weaker |

Interpret `Match` as follows:

- **Evidence stronger than claim:** the evidence supports more than the paper states. Note this without silently enlarging the authors' claim.
- **Matched:** wording, scope, certainty, and causal force are proportional to the evidence.
- **Evidence weaker than claim:** the result lacks scope, control, power, robustness, proof conditions, causal identification, or main-text visibility needed for the wording.

Include negative and boundary claims. Examples: “works generally,” “is robust,” “scales,” “requires X,” “outperforms,” “is efficient,” “causes Y,” “fails only when,” or “the difference is null.” Failure to reject is not equivalence unless an equivalence margin and appropriate analysis are supplied.

### Terminology and narrative ledger

For concepts central to the paper, record:

| Term / symbol | First definition | Conventional meaning | Later uses consistent? | Citation / attribution support | Consequence |
|---|---|---|---|---|---|

Use this to detect concept substitution, undefined mechanisms, changing comparison classes, overloaded terms, and novelty claims that shift meaning between introduction and experiments.

### Figure and table inventory

List every main-text figure and table with its page, asserted conclusion, evidence level, and audit verdict. Use `main-text-audit.md` for the checks.

## Semantic novelty test

Compare the method with the closest conceptual alternatives along these axes:

| Axis | Question |
|---|---|
| Problem formulation | Is a different object optimized, predicted, controlled, or explained? |
| Assumptions / information | Does it use different supervision, priors, access, identifiability, or deployment assumptions? |
| Mechanism | Is there a new causal/computational mechanism or only renamed modules? |
| Objective | Is the training or inference criterion materially different? |
| Procedure | Does information flow or decision-making differ consequentially? |
| Perspective | Does it reveal a useful equivalence, decomposition, limitation, or framing? |
| Capability | Does it enable a previously unavailable regime or modestly improve a metric? |

Keyword overlap proves neither sameness nor novelty. State the minimal conceptual delta and why it matters. If novelty is mainly scale, engineering, data, or composition, say so and judge whether that delta remains scientifically valuable.

## Evidence adequacy

Apply only checks relevant to live claims:

- comparator fairness: data, compute, parameter count, pretraining, tuning budget, and evaluation protocol;
- ablations: isolation of the claimed mechanism rather than arbitrary deletion;
- robustness and scope: datasets, tasks, prompts, seeds, analysis units, uncertainty, sensitivity, failures, and distribution shift;
- theory: assumptions, proof completeness, theorem-to-algorithm connection, and predicted empirical phenomenon;
- efficiency: hardware, wall-clock, memory, preprocessing, serving cost, and quality–cost trade-off;
- causality/mechanism: interventions that distinguish the explanation from plausible alternatives;
- reproducibility: enough data, method, hyperparameter, environment, and evaluation detail to avoid guessing material choices.

Do not turn this into an exhaustive-experiment checklist. Ask for the smallest missing evidence that would materially alter confidence.

## Required final review structure

### 1. Abstract audit

Judge the abstract independently on four dimensions:

- **Clarity:** states the problem, approach, and finding in direct language without undefined jargon or promotional fog.
- **Concision:** fits the venue's abstract scale, avoids repetition, and contains no paragraph-level detours.
- **Whole-paper coverage:** represents the core problem, method/mechanism, principal evidence-backed result, contribution, and material boundary or scope. It must not omit a central part of the paper or imply broader evidence than the paper contains.
- **Detail control:** does not include unnecessary decimal values, confidence intervals, sample counts, per-dataset results, hyperparameters, implementation details, long causal explanations, or ablation inventories. At most, retain a headline magnitude when it is indispensable to understanding the contribution.

Complete coverage is conceptual, not exhaustive. The abstract should summarize the scientific arc rather than enumerate experiments. Treat an abstract that materially misrepresents, narrows, or overstates the paper as a substantive writing/evidence defect; treat modest excess length or removable detail as a presentation defect unless it obscures the contribution.

### 2. Paper understanding and conceptual novelty

- Core problem and stakes.
- Proposed method and operative mechanism.
- Closest conceptual alternatives and minimal conceptual delta.
- Verdict: new perspective/capability, meaningful extension, or mostly incremental/relabeling.

### 3. Claim-to-evidence alignment

Expose the decisive ledger. Cite claim and evidence locations. Identify overclaiming, underclaiming, missing controls, alternative explanations, selective presentation, and the most important unresolved boundary.

### 4. Main-text evidence visibility and per-visual audit

- State whether a reviewer can verify every central contribution without reading the appendix.
- Audit every main-text figure and table individually.
- Identify prose-only experimental claims and core evidence located only in the appendix.

### 5. Writing, terminology, citations, and narrative logic

Assess clarity, definitions, notation, terminology, reproducibility, citation entailment, novelty attribution, internal consistency, causal chain, and boundary discipline. Distinguish cosmetic prose from ambiguity that changes science.

### 6. New insight, field impact, workload, and completeness

Judge frontier awareness, depth and likely influence, quantity and coherence of supported contributions, experimental/theoretical workload, and whether the paper forms a complete scientific unit.

### 7. Strengths

List only substantiated strengths, ordered by importance.

### 8. Weaknesses and required clarifications

Separate:

- **Contribution-threatening defects:** can invalidate the main conclusion or novelty.
- **Scope/confidence defects:** narrow the valid conclusion or reduce confidence.
- **Presentation/minor defects:** matter but do not change the scientific verdict.

For each weakness, state why it matters and the smallest evidence or revision that would resolve it.

### 9. Contribution versus defects

State one of: contribution greater than defects, approximately balanced, or defects greater than contribution. State what contribution survives all identified weaknesses.

### 10. ICLR score and confidence

| Score | Anchor |
|---:|---|
| 10 | Landmark, exceptionally well-supported field-level advance with negligible material defects. |
| 9 | Clear top-tier accept; major, broadly important advance with unusually strong evidence and only minor limitations. |
| 8 | Strong accept; substantial and well-supported contribution, with only minor remaining defects. |
| 7 | Accept; clear meaningful contribution and adequate evidence; real weaknesses remain but are narrower than the contribution. |
| 6 | Borderline/weak accept; contribution exceeds defects, but novelty, evidence, scope, or presentation has notable limitations. |
| 5 | Borderline; moderate contribution and defects are approximately balanced. |
| 4 | Weak reject; defects outweigh contribution although a useful result remains. |
| 3 | Reject; serious novelty, validity, evidence, or completeness problems dominate. |
| 2 | Strong reject; central claims are largely unsupported or contribution is very limited. |
| 1 | Fundamentally invalid, empty, or unreviewable as a scientific contribution. |

Report one integer score and confidence from 1–5. Identify the single uncertainty most likely to move the score. Never select the number first and backfill reasons.

## Guardrails

- Do not score an unread or materially incomplete submission; mark it unreviewable and name missing material.
- Do not infer evidence from citations, planned experiments, or future-work promises.
- Do not penalize unrelated missing experiments. Tie every request to a live claim or plausible alternative.
- Do not reward volume by itself.
- Do not treat polish as validity or rough prose as invalidity; explain when writing changes interpretation or reproducibility.
- Do not speculate about author identity, institution, or venue politics.

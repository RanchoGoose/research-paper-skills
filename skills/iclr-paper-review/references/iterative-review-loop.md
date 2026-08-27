# Iterative remote paper-review loop

Use this workflow only when the user explicitly authorizes repeated retrieval and remote review updates. Review authorization alone does not permit pull, edit, commit, push, scheduling, or stopping an automation.

## Establish the contract

Record:

- remote project or repository;
- local working directory;
- review output filename and whether a compiled PDF is required;
- polling interval or event trigger;
- acceptance threshold and stopping condition;
- authorized mutations: pull, write review, commit, push, create/update/pause automation;
- exact paper files and supplementary material in scope.

An acceptance-gated loop should default to continuing until the explicit threshold is met. If the user chooses 8, scores of 6 or 7 do not complete the task.

## Identify paper changes, not reviewer echo

Prevent the loop from treating its own review commit as a new paper revision.

- Persist or report the last reviewed paper commit/fingerprint.
- Compare paper source, figures, data summaries, appendix, and supplementary files while excluding review outputs, generated review PDFs, build artifacts, and local state.
- If only review output changed, record “no paper update” and do not rewrite, recommit, or push.
- Preserve unrelated user changes and untracked files. Never use destructive reset to simplify the loop.

## Each review round

1. Fetch and inspect the remote state. Pull only after confirming the intended branch/project and handling local overlap safely.
2. Determine whether paper content changed. If not, finish the round quietly.
3. Read the complete current source, appendix, supplementary material, and cross-referenced artifacts.
4. Compile the paper using the project’s actual root document and bibliography flow. Do not let the independent review manuscript enter the paper’s main compilation.
5. Inspect the rendered main-paper pages individually; audit every figure and table and verify the main-text page budget.
6. Re-run available deterministic aggregation, statistical, or reproducibility checks. Report exact commands, return codes, mismatches, exemptions, and missing raw material.
7. Rebuild the claim-to-evidence, terminology/narrative, and figure/table ledgers against the new revision. Do not merely check whether authors responded to the last review.
8. Write a complete replacement review, not an opaque delta. Include paper commit, review round, score, confidence, contribution-defect judgment, resolved issues, remaining blockers, and minimal path to the threshold.
9. Compile and visually inspect the review artifact when a PDF is requested.
10. Before committing, fetch again. If the paper changed during review, integrate and reassess rather than pushing a stale verdict.
11. Commit only the authorized review files, push to the specified remote, and verify local and remote commit identity.

## Review-output isolation

Prefer a separate root manuscript such as `review_result.tex` and `review_result.pdf`. Do not `\input` it from the paper, add it to the paper bibliography, or change the submission root. Avoid committing auxiliary files unless requested.

## Scheduling and notifications

Use the product’s supported automation/heartbeat mechanism for recurring review; do not hold a shell loop open. Keep the automation prompt human-readable and include the project, work directory, change-detection rule, review standard, output, push authorization, threshold, and blocker policy.

Do not notify on unchanged rounds unless the user requests a log. Notify when:

- paper content changed and a new review was pushed;
- the score or acceptance status changed;
- access, credentials, compilation, reproduction, or push is blocked;
- the acceptance threshold is met and the automation is paused/stopped as authorized.

## Stopping and blockers

Stop or pause only when the explicit scientific condition is satisfied, not merely because a score is numerically high. For an 8-point threshold, require a substantial, well-supported contribution, main-text self-containment, and only minor remaining defects.

If access, authentication, Git credentials, compilation, source completeness, reproduction, or push fails, report the exact failing operation and available evidence. Do not bypass permissions, fabricate a successful run, or score evidence you could not inspect.

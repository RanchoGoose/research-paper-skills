# Method, notation, parameter, and equation audit

Use this audit for every methods section containing mathematical notation, objectives, transformations, algorithms, theorems, or tunable quantities. Do not restrict the audit to numbered or headline equations.

## Build a notation and equation ledger

Use one row per symbol or equation:

| Symbol/equation | First definition | Domain/type/shape/units | Role and status | Conventional or explained? | Validity | Claim supported |
|---|---|---|---|---|---|---|

“Status” means fixed, observed, learned, sampled, optimized, derived, or tuned. Preserve exact section, page, equation, theorem, and algorithm identifiers.

## Audit every parameter, variable, and operator

At first use, require the information needed to interpret or reproduce the method:

- semantic meaning and role;
- scalar/vector/matrix/tensor/function type and domain;
- tensor shape, axes, index ranges, and broadcasting rules where relevant;
- physical units or dimensional meaning where relevant;
- allowed range, constraints, boundary or initial conditions;
- whether it is fixed, learned, sampled, estimated, scheduled, or tuned;
- default value or selection rule when results depend on it;
- consistent notation and capitalization across prose, equations, algorithms, figures, and code.

Prefer field-standard identifiers when they have stable meanings. Nonstandard notation is acceptable only when it is explicitly motivated, defined, and not easily confused with a conventional use. Flag overloaded symbols, silent changes of meaning, undefined subscripts, ambiguous superscripts, inconsistent bolding, and the same object appearing under multiple names.

## Audit every formula

Check, as applicable:

1. **Syntax and definition:** every operand and operator is defined; equation references resolve correctly.
2. **Type and shape correctness:** inputs and outputs compose; sums, products, concatenations, contractions, and broadcasting are valid.
3. **Dimensional correctness:** quantities combined by addition or equality have compatible units or dimensions.
4. **Indices and sets:** summation ranges, masks, neighborhoods, batches, time steps, and boundary cases are complete and consistent.
5. **Numerical validity:** denominators cannot silently vanish; logarithm and square-root domains are valid; signs, constants, normalization, and clipping are correct.
6. **Probabilistic validity:** distributions, conditioning, expectations, independence assumptions, normalization, and support are specified.
7. **Optimization validity:** optimized variables, constraints, minimization/maximization direction, stop-gradient behavior, and approximation signs are correct.
8. **Logical validity:** assumptions are sufficient, intermediate steps follow, and equality, proportionality, approximation, bound, implication, and heuristic language are not interchanged.
9. **Special cases:** the expression behaves sensibly at limiting, degenerate, or canonical inputs and does not contradict the prose or algorithm.
10. **Claim relevance:** the equation actually proves, entails, operationalizes, or tests the stated proposition. A plausible heuristic is not a proof.

Trace theory into implementation: theorem assumptions must match experimental conditions, and algorithms must implement the stated equations without omitted operations or conflicting update orders. If a derivation cannot be verified from supplied material, say so; never repair it silently or invent a proof.

## Severity

- A cosmetic notation inconsistency is a presentation defect.
- Missing definitions that force implementation guesses are reproducibility defects.
- An invalid auxiliary formula is a technical defect proportional to its downstream role.
- An incorrect central objective, update, theorem, or claimed implication is contribution-threatening and must materially affect the score.

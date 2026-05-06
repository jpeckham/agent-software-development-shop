# Cross-Stage QA Guardrails Design

## Goal

Strengthen the shop's process so it catches user-visible quality defects and suspicious domain decisions earlier and more reliably. The process should stop relying on a single end-of-cycle QA pass and instead apply a QA-minded review lens during requirements, architecture, implementation, and QA.

## Problem

Recent output against a target repository exposed two process failures:

1. User-visible labels regressed during refactoring and were not caught.
2. Domain semantics became suspicious, such as weaker items appearing to have higher rarity signaling than stronger items, and no stage challenged that inconsistency.

The current process has evidence-oriented language, but it does not explicitly require cross-stage critical review of:

- UI terminology and label integrity
- semantic ordering and consistency in player-facing systems
- challenging requirements or implementation details that technically "work" but look wrong

## Desired Behavior

Each role should act with a QA-minded lens appropriate to its stage:

- `business_analyst` must define observable UI text and semantic consistency expectations where relevant.
- `architect` must define verification seams and invariants for those expectations.
- `developer` must implement validation hooks, tests, or checks when touching affected behavior.
- `qa` must validate requirements, architecture, and implementation critically rather than treating earlier artifacts as unquestionable truth.

## Recommended Approach

Add a cross-stage QA guardrail contract to prompt generation rather than inserting a new orchestration stage.

This keeps the workflow shape simple while materially changing behavior:

- all stages inherit a shared QA-minded review rubric
- role-specific guidance makes the rubric concrete for each stage
- prompt tests lock the new instructions in place

## Guardrail Contract

The new contract should require agents to look for:

- user-visible label drift after refactors or component extraction
- mismatches between displayed category/status/rarity signals and actual item quality or behavior
- suspicious design decisions that may technically satisfy existing artifacts but violate user expectations
- acceptance criteria that are too weak to catch the above

The contract should also explicitly authorize later stages to challenge earlier artifacts:

- QA can question requirements if they seem incomplete or self-contradictory
- architecture can require verification mechanisms when requirements omit them
- developer can add tests or validation hooks needed to prove semantics, not just syntax

## Implementation Shape

### Prompt changes

Update `src/asd_shop/prompts.py` so that:

- shared guidance adds a QA-minded critical review section for all stages
- `business_analyst` guidance requires explicit observable UI labels and semantic consistency criteria
- `architect` guidance requires invariants and validation strategy for user-visible semantics
- `developer` guidance requires tests or validation hooks for user-visible naming and ranking consistency when relevant
- `qa` guidance explicitly says to challenge suspicious product logic, not just confirm literal artifact compliance

### Test coverage

Add and update prompt tests to verify:

- QA prompt includes instructions to challenge suspicious semantics and prior assumptions
- BA prompt includes label and semantic consistency expectations
- architect prompt includes invariants/validation guidance for user-visible semantics
- developer prompt includes implementing proofs for semantic consistency when relevant

## Non-Goals

- Adding repository-specific hardcoded rules for item rarity, labels, or balancing
- Adding a new orchestration stage or persistent rubric artifact in this change
- Building a generic static analyzer in this iteration

Those may come later, but the immediate gap is process guidance, not repository-specific mechanics.

## Risks

- Overly generic wording could be ignored by agent backends
- Overly verbose prompts could dilute higher-priority instructions

Mitigation:

- keep the contract concise and imperative
- pin the instructions with tests
- place the new guidance near existing role execution guidance, where behavior is already shaped

## Verification Strategy

Verify by:

- prompt-level tests asserting the new instructions are present
- running the existing test suite to ensure no regressions in prompt construction behavior

## Expected Outcome

After this change, the shop should be more likely to catch defects like:

- broken or stale UI labels after refactors
- semantics that feel internally inconsistent, such as weaker items signaling higher rarity than stronger ones
- acceptance criteria that fail to define how those issues are verified

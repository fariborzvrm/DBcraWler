# Project Instructions

## Before Starting Work

Read:

1. docs/memory/PROJECT_STATE.md
2. docs/memory/CURRENT_TASK.md
3. docs/memory/DECISIONS.md
4. docs/memory/CONTRACTS.md

Only read EVALUATION.md when working on evaluation,
generation accuracy, prompts, or validation.

## Before Making Changes

Verify the memory against the actual code.

Never blindly trust the memory ledger.

The source of truth for implementation is the code.

## Safety

Generated SQL must never be executed before guardrails.

Never weaken database permissions.

Never remove a guardrail merely to make a test pass.

Never bypass validation without explicitly documenting
the reason.

## After Meaningful Work

Update CURRENT_TASK.md.

Update PROJECT_STATE.md if project progress changed.

Update DECISIONS.md if an architectural decision was made.

Update CONTRACTS.md if an API/interface contract changed.

Update EVALUATION.md when evaluation results change.

Keep memory concise.

Do not record conversational history.

Record state, decisions, constraints, failures,
and next actions.

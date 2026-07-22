# Hermes orchestration workflow (sanitized)

This artifact documents one disposable, non-production verification of the
manager-control pattern used in AJ Chandler's private Hermes lab. It is a
first-party engineering record, not independent certification and not a claim
that the full private appliance is continuously healthy.

## Observed workflow

1. A manager received an explicit, versioned revision contract.
2. The deterministic reconciler created one reviewer task and linked it to the
   revision without granting the reviewer additional execution authority.
3. The reviewer returned `REQUEST_CHANGES`.
4. The reconciler created exactly one corrected revision and one new review.
5. Approval created one dependency-bound, non-live verification task whose
   parents were the approved revision and review.
6. The verification reached `done`; a final reconciliation produced no output,
   demonstrating idempotency rather than duplicate work.

Opaque, malformed, protected, and `HOLD` states created no downstream work.
The verification did not touch a live account, credential, external message,
financial action, publication, protected system, or security control.

## What failed during development

The first test run failed because the manager-control module did not exist. A
later link assertion also failed before the review-to-revision dependency was
implemented. The final disposable workflow passed three deterministic tests,
Python compilation, static analysis, and scoped whitespace validation.

## Claim boundary

This walkthrough demonstrates revision-specific review, bounded progression,
fail-closed handling, and idempotent reconciliation in a disposable database.
It does not prove autonomous production operation, a completed disaster-recovery
restore, or flawless health across every maintenance task.

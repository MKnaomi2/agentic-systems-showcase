# Hermes agent lab system card

- Status: active personal systems lab with a recent orchestration regression under repair
- Period: 2026
- Ownership: architecture, implementation, and operation
- Source: private lab; sanitized walkthrough available

## Core decision

Prompts, credentials, memory, and machine authority remain separate. A manager
routes work across 12 isolated role profiles with distinct models, tools, state,
authority, and concurrency. Durable Kanban dependencies and bounded context
packets connect the team to a canonical Obsidian continuity layer without
collapsing those boundaries. Evidence gates and human authorization constrain
consequential action.

## Sanitized evidence

- [`hermes-workflow.md`](../evidence/hermes-workflow.md) documents a disposable
  revision-review workflow: requested changes, one corrected revision, a new
  review, approval, dependency-bound non-live verification, and an idempotent
  terminal reconcile.
- [`hermes-probes-2026-07-21.json`](../evidence/hermes-probes-2026-07-21.json)
  publishes six read-only probe definitions, observed results, and limitations.
- The topology counts in that artifact are supporting observations, not a claim
  that more profiles or notes automatically produce better outcomes.

## Claim boundary

Active systems research, not a production compliance certification, a
continuous-health guarantee, a completed full disaster-recovery restore, or a
claim of flawless autonomous operation. Profile names, local paths,
credentials, private note contents, account details, and raw system records are
intentionally excluded.

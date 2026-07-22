# ADR 0001: Keep authority below the model boundary

- Status: accepted
- Date: 2026-07-21

## Context

A tool-using model can interpret intent well, but its output is untrusted input.
Prompt instructions are not a durable place to enforce tenant isolation,
permissions, write gates, or replay protection.

## Decision

The model emits a structured `ProposedAction`. A deterministic authority engine
then evaluates a registry controlled by application code:

```text
model proposal
      |
      v
registered tool -> tenant match -> scope check -> confirmation -> replay check
      |                                                       |
      +---------------- denial receipt <----------------------+
                                                              |
                                                       authorization receipt
```

Unknown tools fail closed. The authority inputs exclude prompt text, so language
cannot create a scope or change a tenant. Consequential effects also require a
confirmation issued outside the model boundary.

## Alternatives considered

1. Put the rules in the system prompt. Rejected because prompts guide behavior
   but do not enforce authorization.
2. Let each tool validate itself. Rejected as the only control because policy
   would drift across tools and make decisions harder to audit.
3. Give the model a broad credential and inspect logs afterward. Rejected
   because detection does not prevent an unauthorized effect.

## Consequences

- Policy is testable without a model or network call.
- Every decision produces a compact receipt.
- New tools require an explicit registry entry.
- The demonstration uses a lock-protected in-process replay set; a distributed
  production system would use an atomic durable store with retention rules.

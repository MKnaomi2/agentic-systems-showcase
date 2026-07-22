# Agentic Systems Showcase

[![CI](https://github.com/MKnaomi2/agentic-systems-showcase/actions/workflows/ci.yml/badge.svg)](https://github.com/MKnaomi2/agentic-systems-showcase/actions/workflows/ci.yml)

Public engineering evidence for [AJ Chandler](https://ai.wadevo.com), a systems
engineer and independent AI product builder focused on secure agent
applications, deterministic authority boundaries, and recoverable automation.

This repository has one job: make the strongest claims in my portfolio
inspectable.

## Run the technical demonstration

The reference implementation is dependency-free Python. It models a tool-using
agent that may propose actions but cannot grant itself authority.

```bash
python -m reference_agent.demo
python -m unittest discover -s tests -v
```

The 12 adversarial and invariant-focused tests verify that:

- unknown tools fail closed;
- tenant boundaries cannot be crossed;
- scopes are enforced below model output;
- consequential actions require a signed, action-bound confirmation;
- changing arguments invalidates a confirmation;
- request IDs cannot be replayed; and
- prompt-injection text cannot create a permission or mint authority.

Start with [`reference_agent/authority.py`](reference_agent/authority.py) and
[`tests/test_authority.py`](tests/test_authority.py).

## Evidence map

| Artifact | What it demonstrates |
| --- | --- |
| [`reference_agent/`](reference_agent/) | Runnable deterministic authority boundary |
| [`tests/`](tests/) | Adversarial and invariant-focused verification |
| [`docs/architecture/`](docs/architecture/) | Decisions, alternatives, and consequences |
| [`docs/evidence/hermes-workflow.md`](docs/evidence/hermes-workflow.md) | Sanitized orchestration workflow and claim boundary |
| [`docs/evidence/hermes-probes-2026-07-21.json`](docs/evidence/hermes-probes-2026-07-21.json) | Definitions and results for six read-only Hermes probes |
| [`docs/system-cards/`](docs/system-cards/) | Status and claim boundaries for private systems |
| [`site/`](site/) | Portfolio source, machine-readable evidence, and hardening tests |

## Featured work

1. **[Wadevo Design](https://design.wadevo.com)** - public AI-assisted design
   system sampler with generated examples, portable agent artifacts, protected
   model-spending routes, and a private authenticated studio.
2. **[Wadevo Finance](https://app.wadevo.com)** - live invite-only alpha with a
   public landing surface, deterministic forecasting and attention logic, and a
   bounded natural-language interface. Source remains private.
3. **This repository** - runnable public evidence for the authorization pattern
   used throughout the portfolio.

Healthspan and Hermes remain private systems. Their sanitized system cards are
public, and technical walkthroughs are available to hiring teams.

## What this reference is not production-ready for

The implementation is intentionally small enough to inspect. It demonstrates
the boundary, not a complete distributed authorization service:

- replay state is process-local and disappears on restart;
- confirmation signing uses a symmetric in-memory key;
- approver identity is supplied by trusted calling code, not independently
  authenticated by this package;
- there is no durable, externally anchored audit store;
- there is no real model or provider integration; and
- distributed concurrency and cross-process race handling are outside the
  demonstration's scope.

Those are deployment requirements, not hidden assumptions. A production
version would require durable atomic replay storage, independently verified
identity, managed key custody and rotation, and append-only audit evidence.

## Public and private boundary

This repository is a fresh public snapshot. It contains no private repository
history, credentials, customer data, employer-specific systems, internal
project names, or local infrastructure details. The reference code is a
sanitized implementation of the engineering pattern, not extracted production
code and not proof that the exact module protects a private product.

## About

- Portfolio: [ai.wadevo.com](https://ai.wadevo.com)
- LinkedIn: [linkedin.com/in/alvento-chandler-jr](https://www.linkedin.com/in/alvento-chandler-jr)
- Contact: [alvento.lisp@proton.me](mailto:alvento.lisp@proton.me)
- Target roles: AI Systems Engineer, Agent Infrastructure Engineer, AI Product Engineer

Designed and authored by AJ Chandler. AI tools assisted implementation and
review; AJ owns the architecture, claims, decisions, and final work.

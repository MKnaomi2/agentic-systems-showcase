# ADR 0002: Bind confirmations to the exact proposed action

- Status: accepted
- Date: 2026-07-21

## Context

A generic confirmation such as "allow writes for five minutes" creates a
time-of-check/time-of-use gap. The model could change the tool, arguments,
tenant, or request after the user approved a different action.

## Decision

The confirmation authority signs a short-lived payload containing:

- actor and tenant identifiers;
- tool name;
- request identifier;
- canonical argument digest;
- human approver; and
- expiry time.

The authority engine verifies every field with a constant-time signature
comparison before a consequential action is authorized.

## Consequences

- Changing one argument invalidates the confirmation.
- A token cannot be reused for another tenant, actor, tool, or request.
- Short expiry reduces the useful lifetime of a leaked token.
- The signing service becomes a high-value boundary and must be isolated,
  rotated, monitored, and independently authenticated in production.


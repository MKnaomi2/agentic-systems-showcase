"""Deterministic authority boundary for a tool-using agent.

The model may create a ``ProposedAction``. This module alone decides whether
that proposal is authorized. Prompt text is deliberately absent from the
authorization inputs: language cannot create a scope, change a tenant, or mint
a confirmation.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class Effect(str, Enum):
    """Observable effect of a registered tool."""

    READ = "read"
    WRITE = "write"
    EXTERNAL = "external"


@dataclass(frozen=True)
class ToolPolicy:
    """Policy attached to a tool below the model boundary."""

    name: str
    effect: Effect
    required_scopes: frozenset[str]
    requires_confirmation: bool = False
    max_argument_bytes: int = 4096


@dataclass(frozen=True)
class ActorContext:
    """Identity and authority supplied by trusted application code."""

    actor_id: str
    tenant_id: str
    scopes: frozenset[str]


@dataclass(frozen=True)
class ProposedAction:
    """Structured proposal emitted by an agent or ordinary application code."""

    tool_name: str
    tenant_id: str
    arguments: Mapping[str, Any]
    request_id: str

    def canonical_arguments(self) -> bytes:
        return json.dumps(
            self.arguments,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_arguments()).hexdigest()


@dataclass(frozen=True)
class DecisionReceipt:
    """Auditable output from the deterministic policy decision."""

    allowed: bool
    code: str
    tool_name: str
    request_id: str
    tenant_id: str
    action_digest: str
    checks: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "tool_name": self.tool_name,
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "action_digest": self.action_digest,
            "checks": list(self.checks),
        }


class ConfirmationAuthority:
    """Issues and verifies short-lived confirmations bound to one action."""

    def __init__(self, signing_key: bytes) -> None:
        if len(signing_key) < 32:
            raise ValueError("signing_key must contain at least 32 bytes")
        self._signing_key = signing_key

    def issue(
        self,
        actor: ActorContext,
        action: ProposedAction,
        *,
        approved_by: str,
        now: int | None = None,
        ttl_seconds: int = 300,
    ) -> str:
        """Create a confirmation after a separate human approval event."""

        if not approved_by.strip():
            raise ValueError("approved_by is required")
        if ttl_seconds <= 0 or ttl_seconds > 900:
            raise ValueError("ttl_seconds must be between 1 and 900")

        issued_at = int(time.time() if now is None else now)
        payload = {
            "actor_id": actor.actor_id,
            "tenant_id": actor.tenant_id,
            "tool_name": action.tool_name,
            "request_id": action.request_id,
            "action_digest": action.digest(),
            "approved_by": approved_by,
            "expires_at": issued_at + ttl_seconds,
        }
        encoded = _b64encode(_canonical_json(payload))
        signature = hmac.new(self._signing_key, encoded.encode("ascii"), hashlib.sha256).digest()
        return f"{encoded}.{_b64encode(signature)}"

    def verify(
        self,
        token: str,
        actor: ActorContext,
        action: ProposedAction,
        *,
        now: int | None = None,
    ) -> tuple[bool, str]:
        """Verify signature, expiry, identity, tenant, tool, request, and arguments."""

        try:
            encoded, supplied_signature = token.split(".", 1)
            expected_signature = hmac.new(
                self._signing_key, encoded.encode("ascii"), hashlib.sha256
            ).digest()
            if not hmac.compare_digest(_b64decode(supplied_signature), expected_signature):
                return False, "confirmation_signature_invalid"
            payload = json.loads(_b64decode(encoded).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return False, "confirmation_malformed"

        current_time = int(time.time() if now is None else now)
        expected = {
            "actor_id": actor.actor_id,
            "tenant_id": actor.tenant_id,
            "tool_name": action.tool_name,
            "request_id": action.request_id,
            "action_digest": action.digest(),
        }
        for field, expected_value in expected.items():
            if payload.get(field) != expected_value:
                return False, f"confirmation_{field}_mismatch"
        if not isinstance(payload.get("approved_by"), str) or not payload["approved_by"].strip():
            return False, "confirmation_approver_missing"
        if not isinstance(payload.get("expires_at"), int) or payload["expires_at"] < current_time:
            return False, "confirmation_expired"
        return True, "confirmation_valid"


class AuthorityEngine:
    """Default-deny policy engine with action-bound confirmations and replay control."""

    def __init__(
        self,
        policies: tuple[ToolPolicy, ...],
        confirmations: ConfirmationAuthority,
    ) -> None:
        self._policies = {policy.name: policy for policy in policies}
        if len(self._policies) != len(policies):
            raise ValueError("tool policy names must be unique")
        self._confirmations = confirmations
        self._consumed_request_ids: set[tuple[str, str]] = set()
        self._replay_lock = threading.Lock()

    def authorize(
        self,
        actor: ActorContext,
        action: ProposedAction,
        *,
        confirmation_token: str | None = None,
        now: int | None = None,
    ) -> DecisionReceipt:
        """Evaluate and consume an authorized request ID atomically for this process."""

        checks: list[str] = []
        policy = self._policies.get(action.tool_name)
        if policy is None:
            return self._deny(action, "tool_not_registered", checks)
        checks.append("tool_registered")

        if not action.request_id.strip():
            return self._deny(action, "request_id_missing", checks)
        checks.append("request_id_present")

        try:
            argument_size = len(action.canonical_arguments())
        except (TypeError, ValueError):
            return self._deny(action, "arguments_not_canonical_json", checks)
        if argument_size > policy.max_argument_bytes:
            return self._deny(action, "arguments_too_large", checks)
        checks.append("argument_size_allowed")

        if action.tenant_id != actor.tenant_id:
            return self._deny(action, "tenant_mismatch", checks)
        checks.append("tenant_matches")

        missing_scopes = sorted(policy.required_scopes - actor.scopes)
        if missing_scopes:
            return self._deny(action, "scope_missing:" + ",".join(missing_scopes), checks)
        checks.append("scopes_satisfied")

        consequential = policy.effect in {Effect.WRITE, Effect.EXTERNAL}
        if consequential and not policy.requires_confirmation:
            return self._deny(action, "unsafe_policy_configuration", checks)

        if policy.requires_confirmation:
            if not confirmation_token:
                return self._deny(action, "confirmation_required", checks)
            valid, confirmation_code = self._confirmations.verify(
                confirmation_token, actor, action, now=now
            )
            if not valid:
                return self._deny(action, confirmation_code, checks)
            checks.append(confirmation_code)

        replay_key = (actor.actor_id, action.request_id)
        with self._replay_lock:
            if replay_key in self._consumed_request_ids:
                return self._deny(action, "request_replayed", checks)
            self._consumed_request_ids.add(replay_key)
        checks.append("request_not_replayed")
        return DecisionReceipt(
            allowed=True,
            code="authorized",
            tool_name=action.tool_name,
            request_id=action.request_id,
            tenant_id=action.tenant_id,
            action_digest=_safe_digest(action),
            checks=tuple(checks),
        )

    @staticmethod
    def _deny(action: ProposedAction, code: str, checks: list[str]) -> DecisionReceipt:
        return DecisionReceipt(
            allowed=False,
            code=code,
            tool_name=action.tool_name,
            request_id=action.request_id,
            tenant_id=action.tenant_id,
            action_digest=_safe_digest(action),
            checks=tuple(checks),
        )


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def _safe_digest(action: ProposedAction) -> str:
    try:
        return action.digest()
    except (TypeError, ValueError):
        return "unavailable"


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)

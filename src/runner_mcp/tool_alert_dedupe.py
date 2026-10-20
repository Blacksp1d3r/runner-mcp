"""Pure source-only deduplication of sanitized tool mismatch observations.

No clock access, network, notification sender, persistent state or authority.
An authenticated fleet observer must supply bounded, ordered observations with
independently verified scope fingerprints before this is operationally useful.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from runner_mcp.tool_identity_classifier import ToolIdentityReason

_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ID = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
_LIMIT = 1024


@dataclass(frozen=True, slots=True)
class ToolMismatchObservation:
    scope_digest: str
    stable_tool_id: str
    reason: ToolIdentityReason
    observed_at_second: int


def summarize_tool_mismatch_alerts(
    observations: list[ToolMismatchObservation] | tuple[ToolMismatchObservation, ...],
    *,
    cooldown_seconds: int = 60,
) -> list[dict[str, object]]:
    """Return only a sanitized bounded per-scope/ID/reason alert digest.

    No external alerts are sent. Duplicate observations within the cooldown
    are counted under the FIRST occurrence; no host paths or free-text errors
    can enter the output. Bad input fails closed with ValueError.
    """
    if (
        isinstance(cooldown_seconds, bool)
        or not isinstance(cooldown_seconds, int)
        or not 1 <= cooldown_seconds <= 86400
        or not isinstance(observations, (list, tuple))
        or len(observations) > _LIMIT
    ):
        raise ValueError("invalid tool alert observations")
    if len(observations) == 0:
        return []
    last_timestamp = -1
    emitted: list[dict[str, object]] = []
    recent: dict[tuple[str, str, ToolIdentityReason], tuple[int, int]] = {}
    for event in observations:
        if (
            not isinstance(event, ToolMismatchObservation)
            or not isinstance(event.scope_digest, str)
            or _DIGEST.fullmatch(event.scope_digest) is None
            or not isinstance(event.stable_tool_id, str)
            or _ID.fullmatch(event.stable_tool_id) is None
            or not isinstance(event.reason, ToolIdentityReason)
            or isinstance(event.observed_at_second, bool)
            or not isinstance(event.observed_at_second, int)
            or not 0 <= event.observed_at_second <= 2**53 - 1
            or event.observed_at_second < last_timestamp
        ):
            raise ValueError("invalid tool alert observation")
        last_timestamp = event.observed_at_second
        if event.reason is ToolIdentityReason.READY:
            # One source-observed recovery transition ends the previous
            # cooldown episode for exactly this scope and tool. Otherwise
            # a newly recurring fault immediately after recovery is silently
            # suppressed as if it never recovered. This is only a pure
            # summary rule; it does not authenticate any READY observation.
            for active_key in tuple(recent):
                if active_key[:2] == (event.scope_digest, event.stable_tool_id):
                    del recent[active_key]
            continue
        key = (event.scope_digest, event.stable_tool_id, event.reason)
        previous = recent.get(key)
        if previous is not None and event.observed_at_second - previous[0] < cooldown_seconds:
            emitted[previous[1]]["suppressed_count"] += 1
            continue
        if len(emitted) >= _LIMIT:
            raise ValueError("too many tool alert summaries")
        index = len(emitted)
        recent[key] = (event.observed_at_second, index)
        emitted.append({
            "scope_digest": event.scope_digest,
            "stable_tool_id": event.stable_tool_id,
            "reason": event.reason.value,
            "first_seen_second": event.observed_at_second,
            "suppressed_count": 0,
        })
    return emitted

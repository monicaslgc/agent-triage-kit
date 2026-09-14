"""A tiny in-memory knowledge base the InvestigatorAgent matches tickets against.

In a real deployment this would be backed by a wiki, a vector index over past
incidents, or a ticketing system's own history. Here it's a plain list of
keyword -> known-issue entries so the whole project stays dependency-free and
the matching logic stays easy to read.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnownIssue:
    keywords: tuple[str, ...]
    diagnosis: str
    next_step: str
    confidence: float


KNOWN_ISSUES: tuple[KnownIssue, ...] = (
    KnownIssue(
        keywords=("timeout", "connection refused", "database", "db"),
        diagnosis="Likely a database connectivity or pool-exhaustion issue.",
        next_step="Check active connection count and recent deploys touching the DB pool config.",
        confidence=0.75,
    ),
    KnownIssue(
        keywords=("401", "403", "token expired", "unauthorized", "auth"),
        diagnosis="Likely an expired or misconfigured auth credential.",
        next_step="Verify token/key expiry and rotation schedule for the affected integration.",
        confidence=0.8,
    ),
    KnownIssue(
        keywords=("webhook", "500", "integration", "callback"),
        diagnosis="Likely a downstream integration returning a server error.",
        next_step="Check the downstream service's status page and recent response logs.",
        confidence=0.65,
    ),
    KnownIssue(
        keywords=("duplicate", "double", "ran twice"),
        diagnosis="Likely a retry or idempotency-key issue causing duplicate processing.",
        next_step="Confirm whether the workflow has idempotency protection on retries.",
        confidence=0.6,
    ),
)


def match(text: str) -> KnownIssue | None:
    """Return the best-matching known issue for `text`, or None."""
    text_l = text.lower()
    best: KnownIssue | None = None
    best_hits = 0
    for issue in KNOWN_ISSUES:
        hits = sum(1 for kw in issue.keywords if kw in text_l)
        if hits > best_hits:
            best, best_hits = issue, hits
    return best

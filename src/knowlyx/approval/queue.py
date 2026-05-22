"""
Approval queue — structured human-in-the-loop workflow.

AI submits an ApprovalRequest before proceeding on HIGH/CRITICAL risk actions.
Human reviews and calls approve() or reject().
AI polls or is notified of the outcome.

Stored in .knowlyx/approvals.json (same pattern as memory store).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    id: str = ""
    title: str
    description: str
    risk_level: str
    domain: str
    repo_path: str = ""
    requested_action: str
    impact_summary: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewed_by: str = ""
    rejection_reason: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalQueue:
    """
    Concurrent-safe approval queue. Each mutation does atomic R-M-W
    under a file lock so two processes can't lose updates.

    Fail-safe rule: once an approval is REJECTED, it stays REJECTED
    even if someone later tries to approve it (security default).
    """

    def __init__(self, store_path: str | Path = ".knowlyx/approvals.json") -> None:
        self.path = Path(store_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _new_id() -> str:
        import hashlib
        import uuid
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:12]

    # ------------------------------------------------------------------
    # Write — all use atomic R-M-W
    # ------------------------------------------------------------------

    def submit(self, request: ApprovalRequest) -> ApprovalRequest:
        """Submit a new approval request. Returns the saved request with ID."""
        from knowlyx.storage import read_modify_write
        if not request.id:
            request.id = self._new_id()
        payload = request.model_dump(mode="json")

        def mutate(current: dict) -> dict:
            current[request.id] = payload
            return current

        read_modify_write(self.path, mutate, default={})
        return request

    def approve(self, request_id: str, reviewed_by: str = "human") -> ApprovalRequest | None:
        """
        Approve — but a previously REJECTED request stays rejected (fail-safe).
        Returns the final state of the request.
        """
        from knowlyx.storage import read_modify_write
        captured: dict[str, ApprovalRequest | None] = {"req": None}

        def mutate(current: dict) -> dict:
            raw = current.get(request_id)
            if not raw:
                return current
            existing = ApprovalRequest(**raw)
            if existing.status == ApprovalStatus.REJECTED:
                # fail-safe: do not flip a reject into approve
                captured["req"] = existing
                return current
            existing.status = ApprovalStatus.APPROVED
            existing.reviewed_by = reviewed_by
            existing.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            current[request_id] = existing.model_dump(mode="json")
            captured["req"] = existing
            return current

        read_modify_write(self.path, mutate, default={})
        return captured["req"]

    def reject(self, request_id: str, reason: str = "", reviewed_by: str = "human") -> ApprovalRequest | None:
        """Reject — wins over a prior approve (security fail-safe)."""
        from knowlyx.storage import read_modify_write
        captured: dict[str, ApprovalRequest | None] = {"req": None}

        def mutate(current: dict) -> dict:
            raw = current.get(request_id)
            if not raw:
                return current
            existing = ApprovalRequest(**raw)
            existing.status = ApprovalStatus.REJECTED
            existing.reviewed_by = reviewed_by
            existing.rejection_reason = reason or existing.rejection_reason
            existing.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            current[request_id] = existing.model_dump(mode="json")
            captured["req"] = existing
            return current

        read_modify_write(self.path, mutate, default={})
        return captured["req"]

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, request_id: str) -> ApprovalRequest | None:
        raw = self._read().get(request_id)
        return ApprovalRequest(**raw) if raw else None

    def pending(self) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._read().values() if r.get("status") == "pending"]

    def all(self) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._read().values()]

    def for_repo(self, repo_path: str) -> list[ApprovalRequest]:
        return [ApprovalRequest(**r) for r in self._read().values() if r.get("repo_path") == repo_path]

    def status_of(self, request_id: str) -> ApprovalStatus | None:
        req = self.get(request_id)
        return req.status if req else None


def get_queue(repo_path: str = ".") -> ApprovalQueue:
    """
    Resolve approval queue path.

    If repo (or ancestor) has .knowlyx/config.toml, use the central
    workspace queue at ~/.knowlyx/workspaces/<name>/approvals.json
    — shared across all repos in the same workspace.
    Otherwise fall back to legacy per-repo .knowlyx/approvals.json.
    """
    from knowlyx.link.resolver import resolve_workspace_or_legacy

    _, approvals_path, _mode = resolve_workspace_or_legacy(repo_path)
    return ApprovalQueue(approvals_path)

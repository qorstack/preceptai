"""Git sync — share central workspace via GitHub/GitLab without infra."""

from precept.sync.auto import (
    SyncResult,
    full_sync,
    last_sync_status,
    pull,
    push,
    schedule_full_sync,
    sync_enabled,
)
from precept.sync.git_sync import (
    GitSync,
    SyncStatus,
    auto_merge_json,
)

__all__ = [
    "GitSync",
    "SyncResult",
    "SyncStatus",
    "auto_merge_json",
    "full_sync",
    "last_sync_status",
    "pull",
    "push",
    "schedule_full_sync",
    "sync_enabled",
]

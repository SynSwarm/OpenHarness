"""Resolve schema and repo paths when installed outside the full OpenHarness clone."""
from __future__ import annotations

import os
from pathlib import Path

# Directory containing this adapter (e.g. .../openharness-adapter-openclaw/)
_ADAPTER_DIR = Path(__file__).resolve().parent
# OpenHarness repo root when this folder lives at adapters/openharness-adapter-openclaw/
_REPO_ROOT = _ADAPTER_DIR.parents[1]


def resolve_schema_path() -> Path | None:
    """
    Order:
    1. OPENHARNESS_SCHEMA_PATH (file path to openharness-v1.draft.json)
    2. ../../schema/... when cloned inside OpenHarness repo
    3. ./openharness-v1.draft.json next to this adapter (vendored copy for standalone installs)
    """
    env = os.environ.get("OPENHARNESS_SCHEMA_PATH", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_file():
            return p
    in_repo = _REPO_ROOT / "schema" / "openharness-v1.draft.json"
    if in_repo.is_file():
        return in_repo
    beside = _ADAPTER_DIR / "openharness-v1.draft.json"
    if beside.is_file():
        return beside
    return None


def repo_root() -> Path:
    return _REPO_ROOT

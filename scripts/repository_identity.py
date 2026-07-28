#!/usr/bin/env python3
"""Canonical public repository identity shared by generators and validators."""

from __future__ import annotations

import os
import re


DEFAULT_REPOSITORY = "bluelittlerain/quantumultx-app-rules"
DEFAULT_BRANCH = "main"

REPOSITORY = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPOSITORY)
if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", REPOSITORY):
    raise RuntimeError(f"Invalid GITHUB_REPOSITORY value: {REPOSITORY!r}")

OWNER, NAME = REPOSITORY.split("/", 1)
REPOSITORY_URL = f"https://github.com/{REPOSITORY}"
RAW_BASE_URL = (
    f"https://raw.githubusercontent.com/{REPOSITORY}/{DEFAULT_BRANCH}"
)


def user_agent(component: str) -> str:
    """Return a generic User-Agent containing the canonical repository URL."""

    normalized = re.sub(r"[^a-z0-9-]+", "-", component.casefold()).strip("-")
    if not normalized:
        raise ValueError("component must contain an alphanumeric character")
    return f"quantumultx-app-rules-{normalized}/1.0 (+{REPOSITORY_URL})"

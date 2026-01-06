"""Git utilities for extracting repository context."""

import os
import re
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitContext:
    """Git repository context information."""
    commit_id: str
    short_commit_id: str
    owner: str
    repo: str
    branch: str
    is_ci: bool


def get_git_context(
    commit_id: Optional[str] = None,
    owner: Optional[str] = None,
    repo: Optional[str] = None
) -> GitContext:
    """
    Resolve git context from CLI args, environment variables, or git commands.

    Priority order:
    1. Explicit CLI arguments
    2. GitHub Actions environment variables
    3. Local git commands
    """
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"

    resolved_commit = _resolve_commit_id(commit_id)
    short_commit = resolved_commit[:7]
    resolved_owner, resolved_repo = _resolve_owner_repo(owner, repo)
    branch = _resolve_branch()

    return GitContext(
        commit_id=resolved_commit,
        short_commit_id=short_commit,
        owner=resolved_owner,
        repo=resolved_repo,
        branch=branch,
        is_ci=is_ci
    )


def _resolve_commit_id(explicit_commit: Optional[str] = None) -> str:
    if explicit_commit:
        return explicit_commit
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"


def _resolve_owner_repo(
    explicit_owner: Optional[str] = None,
    explicit_repo: Optional[str] = None
) -> tuple[str, str]:
    if explicit_owner and explicit_repo:
        return explicit_owner, explicit_repo

    github_repository = os.environ.get("GITHUB_REPOSITORY")
    if github_repository and "/" in github_repository:
        parts = github_repository.split("/", 1)
        return parts[0], parts[1]

    try:
        remote_url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        return _parse_remote_url(remote_url)
    except subprocess.CalledProcessError:
        return "unknown", "unknown"


def _resolve_branch() -> str:
    if os.environ.get("GITHUB_REF_NAME"):
        return os.environ["GITHUB_REF_NAME"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"


def _parse_remote_url(url: str) -> tuple[str, str]:
    patterns = [
        r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$",
        r"github\.com[:/]([^/]+)/([^/.]+)$"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return "unknown", "unknown"

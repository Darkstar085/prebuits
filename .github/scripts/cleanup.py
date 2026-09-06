#!/usr/bin/env python3
"""Remove old workflow runs and releases, keeping only the latest ones."""

from __future__ import annotations

import json
import os
import subprocess

REPO = os.environ.get("GITHUB_REPOSITORY", "Darkstar085/android-app-updater")


def gh_api(endpoint: str, *args: str):
    command = ["gh", "api", endpoint, *args]
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def delete(endpoint: str) -> None:
    subprocess.run(["gh", "api", "--method", "DELETE", endpoint], check=False)


def paginated(endpoint: str, key: str | None = None) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        batch = gh_api(f"{endpoint}?per_page=100&page={page}") or []
        values = batch.get(key, []) if isinstance(batch, dict) and key else batch
        if not values:
            break
        items.extend(values)
        if len(values) < 100:
            break
        page += 1
    return items


def cleanup_runs() -> None:
    runs = paginated(f"repos/{REPO}/actions/runs", "workflow_runs")
    runs_sorted = sorted(runs, key=lambda run: run.get("created_at", ""), reverse=True)
    for run in runs_sorted[1:]:
        delete(f"repos/{REPO}/actions/runs/{run['id']}")


def cleanup_releases() -> None:
    releases = paginated(f"repos/{REPO}/releases")
    releases_sorted = sorted(
        releases,
        key=lambda release: release.get("published_at") or release.get("created_at", ""),
        reverse=True,
    )
    for release in releases_sorted[1:]:
        release_id = release.get("id")
        tag_name = release.get("tag_name")
        if release_id:
            delete(f"repos/{REPO}/releases/{release_id}")
        if tag_name:
            delete(f"repos/{REPO}/git/refs/tags/{tag_name}")


def main() -> None:
    cleanup_runs()
    cleanup_releases()
    print("Cleanup completed. Kept the latest workflow run and latest release.")


if __name__ == "__main__":
    main()

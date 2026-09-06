#!/usr/bin/env python3
"""Build and publish updated application prebuilts."""

from __future__ import annotations

import fnmatch
import glob
import html
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOWNLOAD_DIR = ROOT / "dl"
APPS_FILE = ROOT / "apps.json"
VERSIONS_FILE = ROOT / "latest-apk-versions.txt"
CAPTIONS_FILE = ROOT / "captions.txt"


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True, capture_output=True)


def gh_api(endpoint: str):
    result = run(["gh", "api", endpoint])
    return json.loads(result.stdout)


def load_apps() -> list[tuple[str, str, str, str, str, str | None]]:
    with APPS_FILE.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return [
        (
            item["name"],
            item["repo"],
            item["pattern"],
            item.get("description", ""),
            item.get("emoji", ""),
            item.get("rename"),
        )
        for item in data
    ]


APPS = load_apps()
APP_INFO = {app: (repo, description, emoji) for app, repo, _pattern, description, emoji, _rename in APPS}


def latest_release(repo: str, pattern: str) -> dict:
    """Find the newest non-draft release containing an asset matching pattern."""
    releases = gh_api(f"repos/{repo}/releases?per_page=30")
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        if any(fnmatch.fnmatch(asset.get("name", ""), pattern) for asset in release.get("assets", [])):
            return release
    raise RuntimeError(f"no release asset matching {pattern!r} found in {repo}")


def download_asset(app: str, repo: str, pattern: str) -> None:
    destination = DOWNLOAD_DIR / app
    shutil.rmtree(destination, ignore_errors=True)
    destination.mkdir(parents=True, exist_ok=True)

    try:
        release = latest_release(repo, pattern)
        tag = release["tag_name"]
        result = run(
            [
                "gh",
                "release",
                "download",
                tag,
                "--repo",
                repo,
                "--pattern",
                pattern,
                "--dir",
                str(destination),
                "--clobber",
            ],
            check=False,
        )
    except Exception as exc:
        print(f"⚠️ {app}: could not fetch matching release: {exc}")
        shutil.rmtree(destination, ignore_errors=True)
        return

    if result.returncode != 0:
        print(f"⚠️ {app}: no matching release asset for selected release")
        shutil.rmtree(destination, ignore_errors=True)
        return

    if app in {"AmarokHider", "DeltaIcons"}:
        for path in destination.glob("*foss*.apk"):
            path.unlink(missing_ok=True)
    if app == "ReFra":
        for path in destination.glob("*nomaps*.apk"):
            path.unlink(missing_ok=True)


def apk_metadata(path: Path) -> tuple[str | None, str | None]:
    result = run(["aapt", "dump", "badging", str(path)], check=False)
    if result.returncode != 0:
        return None, None
    package = re.search(r"package: name='([^']+)'", result.stdout)
    version = re.search(r"versionName='([^']+)'", result.stdout)
    return (package.group(1) if package else None, version.group(1) if version else None)


def matching_files(app: str, pattern: str) -> list[Path]:
    return sorted(Path(p) for p in glob.glob(str(DOWNLOAD_DIR / app / pattern)) if Path(p).is_file())


def asset_priority(path: Path) -> tuple[int, int, int, int, str]:
    name = path.name.lower()
    return (
        0 if "universal" in name else 1 if "arm64-v8a" in name else 2,
        0 if "release" in name else 1 if "stable" in name else 2,
        0 if "foss" not in name else 1,
        0 if "debug" not in name else 1,
        name,
    )


def choose_asset(app: str, pattern: str) -> tuple[Path, str] | None:
    candidates = matching_files(app, pattern)
    apk_candidates = [path for path in candidates if path.suffix.lower() == ".apk"]
    if not apk_candidates:
        print(f"⚠️ {app}: no APK files matched; skipping app")
        return None

    inspected = []
    for candidate in apk_candidates:
        package, version = apk_metadata(candidate)
        if package and version:
            inspected.append((candidate, package, version))

    if not inspected:
        print(f"⚠️ {app}: could not read Android package metadata; skipping app")
        return None

    identities = {(package, version) for _path, package, version in inspected}
    if len(identities) > 1:
        packages = {package for _path, package, _version in inspected}
        non_foss = [item for item in inspected if "foss" not in item[0].name.lower()]
        foss = [item for item in inspected if "foss" in item[0].name.lower()]

        # Some releases publish the same app twice with a normal and a FOSS
        # build. When the package is the same, prefer the normal build rather
        # than treating the FOSS suffix as a version conflict.
        if len(packages) == 1 and non_foss and foss:
            inspected = non_foss
        else:
            universal = [item for item in inspected if "universal" in item[0].name.lower()]
            arm64 = [item for item in inspected if "arm64-v8a" in item[0].name.lower()]
            preferred = universal or arm64 or inspected
            preferred_identities = {(package, version) for _path, package, version in preferred}
            if len(preferred_identities) > 1:
                details = ", ".join(
                    f"{path.name}: {package or 'unknown package'} {version or 'unknown version'}"
                    for path, package, version in preferred
                )
                print(f"⚠️ {app}: multiple APK versions/packages remain; skipping app: {details}")
                return None
            inspected = preferred

    path, package, version = sorted(inspected, key=lambda item: asset_priority(item[0]))[0]
    return path, version


def process_assets(old: dict[str, str]) -> list[tuple[str, str, Path]]:
    updates: list[tuple[str, str, Path]] = []
    for app, _repo, pattern, _desc, _emoji, rename in APPS:
        candidates = matching_files(app, pattern)
        if not candidates:
            continue

        if all(path.suffix.lower() == ".exe" for path in candidates):
            source = sorted(candidates)[0]
            match = re.search(r"[-_]v?([0-9]+(?:\.[0-9]+){1,3}).*\.exe$", source.name, re.I)
            version = match.group(1) if match else "unknown"
        else:
            selected = choose_asset(app, pattern)
            if not selected:
                shutil.rmtree(DOWNLOAD_DIR / app, ignore_errors=True)
                continue
            source, version = selected

        if version == "unknown":
            print(f"⚠️ {app}: could not determine version from {source.name}; skipping app")
            shutil.rmtree(DOWNLOAD_DIR / app, ignore_errors=True)
            continue
        if old.get(app) == version:
            print(f"{app} unchanged (v{version}) — skipping")
            shutil.rmtree(DOWNLOAD_DIR / app, ignore_errors=True)
            continue

        final = ROOT / (f"{app}_v{version}{source.suffix.lower()}")
        if rename:
            temporary = ROOT / rename
            shutil.move(str(source), temporary)
            shutil.move(str(temporary), final)
        else:
            final.unlink(missing_ok=True)
            shutil.move(str(source), final)
        updates.append((app, version, final))
        print(f"Will update {app} → v{version} (was: {old.get(app, 'none')})")
    return updates


def read_versions() -> dict[str, str]:
    if not VERSIONS_FILE.exists():
        return {}
    versions: dict[str, str] = {}
    for line in VERSIONS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            app, version = line.split(":", 1)
        elif "=" in line:
            app, version = line.split("=", 1)
        else:
            continue
        app, version = app.strip(), version.strip()
        if app and version:
            versions[app] = version
    return versions


def generate_metadata(updates: list[tuple[str, str, Path]], old: dict[str, str]) -> None:
    version_lines = {app: old[app] for app, _repo, _pattern, _desc, _emoji, _rename in APPS if app in old}
    captions: list[str] = []

    for app, version, path in updates:
        previous = old.get(app)
        version_lines[app] = version
        repo, description, emoji = APP_INFO[app]
        version_line = f"🚀 Version: {previous} → {version}" if previous else f"🆕 Version: {version}"
        filename = html.escape(path.name)
        description = html.escape(description)
        changelog = f"Changelog: <a href='https://github.com/{repo}/releases/latest'>Open</a>"
        captions.append(
            f"📦 <b>File name</b> – {filename}\n"
            f"    {emoji} {description}\n"
            f"{version_line}\n\n"
            f"{changelog}\n"
            f"    ----"
        )

    with VERSIONS_FILE.open("w", encoding="utf-8") as handle:
        for app, _repo, _pattern, _desc, _emoji, _rename in APPS:
            if app in version_lines:
                handle.write(f"{app}: {version_lines[app]}\n")

    with CAPTIONS_FILE.open("w", encoding="utf-8") as handle:
        if captions:
            handle.write("\n".join(captions))
            handle.write("\n")


def publish(updates: list[tuple[str, str, Path]]) -> None:
    if not updates:
        print("No app updates to publish")
        return

    now = datetime.now(timezone.utc)
    run_id = os.getenv("GITHUB_RUN_ID")
    tag = f"prebuilts-{run_id}" if run_id else f"prebuilts-{now:%Y%m%d%H%M%S}"
    title = f"Prebuilts {now:%Y-%m-%d %H:%M UTC}"
    body = "\n".join(f"- {app} v{version}" for app, version, _ in updates)
    run(
        [
            "gh",
            "release",
            "create",
            tag,
            *[str(path) for _, _, path in updates],
            str(CAPTIONS_FILE),
            "--title",
            title,
            "--notes",
            body,
        ]
    )
    print(f"Published release {tag}")


def main() -> None:
    print(f"Build started: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}")
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for app, repo, pattern, _desc, _emoji, _rename in APPS:
        print(f"::group::Download {app}")
        download_asset(app, repo, pattern)
        print("::endgroup::")

    old = read_versions()
    updates = process_assets(old)
    generate_metadata(updates, old)
    publish(updates)
    print("Build completed")


if __name__ == "__main__":
    main()

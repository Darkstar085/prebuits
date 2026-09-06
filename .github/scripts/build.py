#!/usr/bin/env python3
"""Build and publish updated application prebuilts."""

from __future__ import annotations

import fnmatch
import glob
import json
import re
import shutil
import subprocess
from datetime import datetime
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
        (item["name"], item["repo"], item["pattern"], item.get("description", ""), item.get("emoji", ""), item.get("rename"))
        for item in data
    ]


APPS = load_apps()


def latest_release(repo: str) -> dict:
    return gh_api(f"repos/{repo}/releases/latest")


def download_asset(app: str, repo: str, pattern: str) -> None:
    destination = DOWNLOAD_DIR / app
    shutil.rmtree(destination, ignore_errors=True)
    destination.mkdir(parents=True, exist_ok=True)

    try:
        release = latest_release(repo)
    except Exception as exc:
        print(f"⚠️ {app}: could not fetch latest release: {exc}")
        shutil.rmtree(destination, ignore_errors=True)
        return

    assets = release.get("assets", [])
    matched = [asset for asset in assets if fnmatch.fnmatchcase(asset.get("name", ""), pattern)]
    if not matched:
        print(f"⚠️ {app}: no matching release asset")
        shutil.rmtree(destination, ignore_errors=True)
        return

    for asset in matched:
        target = destination / asset["name"]
        try:
            subprocess.run(
                ["gh", "api", asset["url"], "-H", "Accept: application/octet-stream", "--output", str(target)],
                check=True,
                text=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            print(f"⚠️ {app}: failed to download {asset['name']}: {exc}")
            shutil.rmtree(destination, ignore_errors=True)
            return

    if app in {"AmarokHider", "DeltaIcons"}:
        for path in destination.glob("*foss*.apk"):
            path.unlink(missing_ok=True)
    if app == "DotGallery":
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
    return [Path(p) for p in glob.glob(str(DOWNLOAD_DIR / app / pattern)) if Path(p).is_file()]


def choose_asset(app: str, pattern: str) -> tuple[Path, str] | None:
    candidates = matching_files(app, pattern)
    apk_candidates = [path for path in candidates if path.suffix.lower() == ".apk"]
    if not apk_candidates:
        print(f"⚠️ {app}: no APK files matched; skipping app")
        return None

    inspected = []
    for candidate in sorted(apk_candidates):
        package, version = apk_metadata(candidate)
        inspected.append((candidate, package, version))

    universal = [item for item in inspected if "universal" in item[0].name.lower()]
    arm64 = [item for item in inspected if "arm64-v8a" in item[0].name.lower()]
    selected = universal or arm64 or inspected

    if len(selected) > 1:
        details = ", ".join(f"{path.name}: {package or 'unknown package'}" for path, package, _ in selected)
        print(f"⚠️ {app}: multiple APKs remain after universal/arm64-v8a selection; skipping app: {details}")
        return None

    path, package, version = selected[0]
    if not package or not version:
        print(f"⚠️ {app}: could not read Android package metadata from {path.name}; skipping app")
        return None
    return path, version


def process_assets(old: dict[str, str]) -> list[tuple[str, str, Path]]:
    updates: list[tuple[str, str, Path]] = []
    for app, _repo, pattern, _desc, _emoji, rename in APPS:
        candidates = matching_files(app, pattern)
        if not candidates:
            continue

        if candidates[0].suffix.lower() == ".exe":
            source = sorted(candidates)[0]
            match = re.search(r"[-_]([0-9]+\.[0-9]+\.[0-9]+).*\.exe$", source.name, re.I)
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
        if "=" in line:
            app, version = line.split("=", 1)
            if app and version:
                versions[app.strip()] = version.strip()
    return versions


def generate_metadata(updates: list[tuple[str, str, Path]], old: dict[str, str]) -> None:
    version_lines = dict(old)
    captions = []
    for app, version, _path in updates:
        version_lines[app] = version
        captions.append(f"{app} v{version}")

    with VERSIONS_FILE.open("w", encoding="utf-8") as handle:
        for app, version in version_lines.items():
            handle.write(f"{app}={version}\n")
    with CAPTIONS_FILE.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(captions))
        if captions:
            handle.write("\n")


def publish(updates: list[tuple[str, str, Path]]) -> None:
    if not updates:
        print("No app updates to publish")
        return
    now = datetime.utcnow()
    tag = f"prebuilts-{now:%Y%m%d%H%M%S}"
    title = f"Prebuilts {now:%Y-%m-%d %H:%M UTC}"
    body = "\n".join(f"- {app} v{version}" for app, version, _ in updates)
    run(["gh", "release", "create", tag, *[str(path) for _, _, path in updates], "--title", title, "--notes", body])


def main() -> None:
    print(f"Build started: {datetime.utcnow():%Y-%m-%d %H:%M UTC}")
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

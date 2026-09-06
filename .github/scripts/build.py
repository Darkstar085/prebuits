#!/usr/bin/env python3
"""Build the configured prebuilts and publish one GitHub release."""

from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOWNLOAD_DIR = ROOT / "dl"
VERSIONS_FILE = ROOT / "latest-apk-versions.txt"
OLD_VERSIONS_FILE = ROOT / "old-apk-versions.txt"
CAPTIONS_FILE = ROOT / "captions.txt"

# name, repository, asset pattern, description, emoji, optional final filename
APPS = [
    ("ABDownloadManager", "amir1376/ab-download-manager", "*windows_x64*.exe", "Powerful download manager with multi-threading", "📥", None),
    ("Acode", "Acode-Foundation/Acode", "*fdroid*.apk", "Lightweight yet powerful code editor", "💻", None),
    ("Aegis", "beemdevelopment/Aegis", "*.apk", "Modern two-factor authentication app", "🔐", None),
    ("NopeRemote", "monuk7735/nope-remote", "NopeRemote*.apk", "Open-source universal IR remote control app for Android", "📺", None),
    ("Kudu", "AdventDevInc/kudu", "Kudu-Setup-*.exe", "Open-source system cleaner and security scanner for Windows, macOS and Linux", "🧹", None),
    ("SpotiFLAC", "spotiflacapp/SpotiFLAC-Mobile", "SpotiFLAC-*-arm64.apk", "Open-source music player and lossless audio downloader for Android", "🎵", None),
    ("LibreCuts", "tharunbirla/LibreCuts", "*arm64*.apk", "Free, open-source video editor for Android", "🎬", None),
    ("OrganicMaps", "organicmaps/organicmaps", "OrganicMaps*-web-release.apk", "Privacy-focused offline maps and navigation app", "🗺️", None),
    ("AmarokHider", "deltazefiro/Amarok-Hider", "*.apk", "Hide apps as your choice", "🙈", None),
    ("Arcticons", "Arcticons-Team/Arcticons", "*dayNight*.apk", "Modern icon pack and theming app", "🎭", None),
    ("Bitwarden", "bitwarden/android", "*bitwarden-fdroid*.apk", "Open-source password manager with cloud sync", "🔑", None),
    ("BreezyWeather", "breezy-weather/breezy-weather", "*freenet*.apk", "Clean, customizable open-source weather app", "🌦️", None),
    ("Cherrygram", "arsLan4k1390/Cherrygram", "Cherrygram*universal*.apk", "Enhanced Telegram client with extra features", "🍒", None),
    ("ConverterNOW", "ferraridamiano/ConverterNOW", "*app-arm64-v8a-release*.apk", "Simple unit and currency converter", "🔄", None),
    ("Cromite", "uazo/cromite", "*arm64_ChromePublic*.apk", "Bromite-based privacy browser", "🌐", None),
    ("CpuInfo", "kamgurgul/cpu-info", "*androidApp*.apk", "Detailed CPU info tool", "💻", None),
    ("DeltaIcons", "Delta-Icons/android", "*.apk", "Beautiful, minimal icon pack", "🎨", None),
    ("DotGallery", "IacobIonut01/Gallery", "*arm64-v8a*.apk", "Jetpack Compose-based photo gallery app", "📷", None),
    ("DuckDuckGo", "duckduckgo/Android", "*.apk", "Private, tracker-blocking browser", "🦆", None),
    ("Florisboard", "florisboard/florisboard", "*stable*.apk", "Privacy-friendly Android keyboard", "⌨️", None),
    ("Flip2DND", "robinsrk/flip_2_dnd", "*.apk", "Flip your phone to toggle Do Not Disturb automatically", "🤳", "Flip2DND.apk"),
    ("Fossify_Calculator", "FossifyOrg/Calculator", "*.apk", "Open-source, privacy-friendly calculator by Fossify", "🧮", None),
    ("Fossify_Keyboard", "FossifyOrg/Keyboard", "*.apk", "Easy keyboard for inserting texts, special characters and numbers", "⌨️", None),
    ("Fossify_MusicPlayer", "FossifyOrg/Music-Player", "*.apk", "Modern music player by Fossify", "🎶", None),
    ("Fossify_Notes", "FossifyOrg/Notes", "*.apk", "Secure, privacy-focused notes app by Fossify", "🗒️", None),
    ("Fossify_VoiceRecorder", "FossifyOrg/Voice-Recorder", "*.apk", "Simple, privacy-respecting voice recorder by Fossify", "🎤", None),
    ("Gramophone", "FoedusProgramme/Gramophone", "*.apk", "Minimalist, elegant music player", "🎼", None),
    ("IceravenBrowser", "fork-maintainers/iceraven-browser", "*v8a*.apk", "Privacy-focused web browser", "🦦", None),
    ("ImageToolbox", "T8RIN/ImageToolbox", "*v8a*.apk", "All-in-one image editing and viewing app", "🖼️", None),
    ("LibreTube", "libre-tube/LibreTube", "app-release.apk", "Open-source YouTube app focusing on privacy", "🔒", None),
    ("LocalSend", "localsend/localsend", "*android-arm64v8.apk", "Secure, local file sharing app", "📤", None),
    ("LTECleanerFOSS", "MDP43140/LTECleanerFOSS", "*.apk", "Clean up unnecessary files to free up space", "🧹", "LTECleanerFOSS.apk"),
    ("Magisk", "topjohnwu/Magisk", "*.apk", "Powerful systemless rooting solution", "🪄", None),
    ("MicroG_RE", "WSTxda/MicroG-RE", "*.apk", "MicroG RE - Enhanced Play Services compatibility", "🧩", None),
    ("MoeList", "axiel7/MoeList", "*universal*.apk", "Anime and manga tracking app", "📖", None),
    ("Momogram", "dic1911/Momogram", "*arm64-v8a*.apk", "Telegram client with privacy and customization features", "📱", None),
    ("Nekogram", "Nekogram/Nekogram", "*universal*.apk", "Feature-rich Telegram client with enhanced privacy", "🐱", None),
    ("Omni", "FoedusProgramme/Omni", "*.apk", "All-in-one tool app with Compass, Spirit Level, Ruler and Flashlight", "🛠️", "Omni.apk"),
    ("OuterTune", "OuterTune/OuterTune", "*core*.apk", "A Material 3 YouTube Music client & local music player for Android", "🎧", None),
    ("Pixelplay", "theovilardo/PixelPlay", "*PixelPlay*.apk", "Lightweight music player with Material You design", "🎵", None),
    ("PhonographPlus", "chr56/Phonograph_Plus", "*ModernStableRelease*.apk", "Enhanced music player fork", "🎧", None),
    ("PrismFileExplorer", "Raival-e/Prism-File-Explorer", "*.apk", "Powerful, material design file explorer", "🗂️", "PrismFileExplorer.apk"),
    ("Quantum_Download_Manager", "PBhadoo/QDM", "*.exe", "A modern, open-source download manager for Windows", "📥", None),
    ("Shizuku", "RikkaApps/Shizuku", "*.apk", "Use system APIs directly with adb/root privileges from normal apps", "🤖", None),
    ("RetroMusicPlayer", "RetroMusicPlayer/RetroMusicPlayer", "*normal*.apk", "Modern music player", "🎵", None),
    ("Morphe_YouTube", "j-hc/revanced-magisk-module", "youtube*all*.apk", "YouTube with ad-block, background play, sponsor block and more", "🎬", None),
    ("Morphe_YTMusic", "j-hc/revanced-magisk-module", "music*v8a*.apk", "YouTube Music with premium unlock, ad-block and advanced playback", "🎵", None),
    ("Morphe_GooglePhotos", "j-hc/revanced-magisk-module", "googlephotos*v8a*.apk", "Google Photos with premium/unlocked features", "📷", None),
    ("Morphe_MicroG", "WSTxda/MicroG-RE", "*microg*.apk", "MicroG for Morphe - enables Google sign-in", "🧩", None),
    ("Morphe_Manager", "MorpheApp/morphe-manager", "*.apk", "Manage and install Morphe patches easily", "🛠️", None),
    ("Sdmaid", "d4rken-org/sdmaid-se", "*.apk", "Powerful system cleaning tool", "🧹", None),
    ("SimpMusic", "maxrave-dev/SimpMusic", "*foss*universal*.apk", "Lightweight YT music player with Material You support", "🎵", None),
    ("Symphony", "zyrouge/symphony", "*.apk", "Lightweight music player for Android 9+", "🎼", None),
    ("Termux", "termux/termux-app", "*universal.apk", "Terminal emulator and Linux environment for Android", "🖥️", None),
    ("ThunderbirdAndroid", "thunderbird/thunderbird-android", "*.apk", "Official Thunderbird email client for Android", "📧", None),
    ("VisualCodeSpace", "Visual-Code-Space/Visual-Code-Space", "*.apk", "Lightweight, feature-rich Android code editor and IDE", "💻", "VisualCodeSpace.apk"),
    ("WeatherMaster", "PranshulGG/WeatherMaster", "*WeatherMaster*.apk", "Modern weather app with graphs", "☁️", None),
    ("XedEditor", "Xed-Editor/Xed-Editor", "*xed*.apk", "Simple and fast text/code editor", "✏️", None),
    ("Ytdlnis", "deniscerri/ytdlnis", "YTDLnis*universal*.apk", "YouTube downloader with advanced features", "⬇️", None),
]


def run(*args: str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=capture)


def load_versions(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if ":" not in line:
                continue
            app, version = line.split(":", 1)
            app, version = app.strip(), version.strip()
            if app and version:
                result[app] = version
    return result


def download_assets() -> None:
    shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
    DOWNLOAD_DIR.mkdir()
    for app, repo, pattern, *_ in APPS:
        target_dir = DOWNLOAD_DIR / app
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"::group::Download {app}")
        result = run(
            "gh", "release", "download", "--repo", repo,
            "--pattern", pattern, "--dir", str(target_dir), "--clobber",
            check=False, capture=True,
        )
        if result.returncode:
            print(f"⚠️ {app}: no matching release asset")
        if app in {"AmarokHider", "DeltaIcons"}:
            for path in target_dir.glob("*foss*.apk"):
                path.unlink(missing_ok=True)
        if app == "DotGallery":
            for path in target_dir.glob("*nomaps*.apk"):
                path.unlink(missing_ok=True)
        print("::endgroup::")


def apk_metadata(path: Path) -> tuple[str | None, str | None]:
    result = run("aapt", "dump", "badging", str(path), check=False, capture=True)
    if result.returncode:
        return None, None
    package = re.search(r"package: name='([^']+)'", result.stdout)
    version = re.search(r"versionName='([^']+)'", result.stdout)
    return (package.group(1) if package else None, version.group(1) if version else None)


def matching_files(app: str, pattern: str) -> list[Path]:
    return [Path(p) for p in glob.glob(str(DOWNLOAD_DIR / app / pattern)) if Path(p).is_file()]


def choose_asset(app: str, pattern: str) -> tuple[Path, str] | None:
    candidates = matching_files(app, pattern)
    if not candidates:
        return None

    apk_candidates = [path for path in candidates if path.suffix.lower() == ".apk"]
    if not apk_candidates:
        raise RuntimeError(f"{app}: matched assets are not APK files: {pattern}")

    inspected: list[tuple[Path, str | None, str | None]] = []
    for candidate in sorted(apk_candidates):
        package, version = apk_metadata(candidate)
        inspected.append((candidate, package, version))

    universal = [item for item in inspected if "universal" in item[0].name.lower()]
    arm64 = [item for item in inspected if "arm64-v8a" in item[0].name.lower()]

    if universal:
        selected = universal
    elif arm64:
        selected = arm64
    else:
        selected = inspected

    if len(selected) > 1:
        details = ", ".join(f"{path.name}: {package or 'unknown package'}" for path, package, _ in selected)
        raise RuntimeError(f"{app}: multiple APKs remain after universal/arm64-v8a selection: {details}")

    path, package, version = selected[0]
    if not package or not version:
        raise RuntimeError(f"{app}: could not read Android package metadata from {path.name}")
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
                continue
            source, version = selected
        if version == "unknown":
            print(f"⚠️ {app}: could not determine version from {source.name}")
            continue
        if old.get(app) == version:
            print(f"{app} unchanged (v{version}) — skipping")
            shutil.rmtree(DOWNLOAD_DIR / app, ignore_errors=True)
            continue
        final_name = rename or f"{app}_v{version}{source.suffix.lower()}"
        if rename:
            temporary = ROOT / rename
            shutil.move(str(source), temporary)
            final = ROOT / f"{app}_v{version}{source.suffix.lower()}"
            shutil.move(str(temporary), final)
        else:
            final = ROOT / final_name
            if final.exists():
                final.unlink()
            shutil.move(str(source), final)
        updates.append((app, version, final))
        print(f"Will update {app} → v{version} (was: {old.get(app, 'none')})")
    return updates


def generate_metadata(updates: list[tuple[str, str, Path]], old: dict[str, str]) -> None:
    captions: list[str] = []
    notes: list[str] = []
    for app, version, path in updates:
        entry = next(item for item in APPS if item[0] == app)
        _name, repo, _pattern, desc, emoji, _rename = entry
        previous = old.get(app)
        version_line = f"🆕 Version: {version}" if not previous else f"🚀 Version: {previous} → {version}"
        captions.append(f"📦 <b>File name</b> – {path.name}\n{emoji} {desc}\n{version_line}\n\nChangelog: <a href='https://github.com/{repo}/releases/latest'>Open</a>\n----")
        notes.append(f"{app}: {version}" if not previous else f"{app}: {previous} → {version}")
    CAPTIONS_FILE.write_text("\n".join(captions) + ("\n" if captions else ""), encoding="utf-8")
    merged = dict(load_versions(VERSIONS_FILE))
    for app, version, _path in updates:
        merged[app] = version
    VERSIONS_FILE.write_text("\n".join(f"{app}: {merged[app]}" for app in sorted(merged)) + "\n", encoding="utf-8")
    (ROOT / "release-notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")


def publish(updates: list[tuple[str, str, Path]]) -> None:
    tag = f"prebuilts-{os.environ.get('GITHUB_RUN_ID', int(datetime.now().timestamp()))}"
    now = datetime.now().astimezone()
    title = f"Prebuilts Update - {now:%Y-%m-%d %H:%M %Z}"
    files = [str(path.name) for _app, _version, path in updates] + [CAPTIONS_FILE.name]
    run("gh", "release", "create", tag, "--repo", os.environ.get("GITHUB_REPOSITORY", "Darkstar085/android-app-updater"), "--title", title, "--notes-file", str(ROOT / "release-notes.txt"), *files)


def commit_state(updates: list[tuple[str, str, Path]]) -> None:
    run("git", "config", "--local", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "config", "--local", "user.name", "github-actions[bot]")
    run("git", "add", "latest-apk-versions.txt", "captions.txt")
    names = ", ".join(app for app, _version, _path in updates)
    message = f"Prebuilts Update — {datetime.now().astimezone():%Y-%m-%d} [skip ci]"
    body = (
        "Prebuilts Update\n\nUpdated apps:\n"
        + "\n".join(f"- {app}: {version}" for app, version, _path in updates)
        + "\n\nUpdated files:\n- latest-apk-versions.txt\n- captions.txt\n\n"
        + "Automated by GitHub Actions"
    )
    run("git", "commit", "-m", message, "-m", body, check=False)
    run("git", "push", "origin", "main")
    print(f"Published: {names}")


def main() -> None:
    os.environ["TZ"] = "Asia/Kolkata"
    time = datetime.now().astimezone()
    print(f"Build started: {time:%Y-%m-%d %H:%M %Z}")
    old = load_versions(VERSIONS_FILE)
    OLD_VERSIONS_FILE.write_text(VERSIONS_FILE.read_text(encoding="utf-8") if VERSIONS_FILE.exists() else "", encoding="utf-8")
    download_assets()
    updates = process_assets(old)
    shutil.rmtree(DOWNLOAD_DIR, ignore_errors=True)
    if not updates:
        print("No updates found. Nothing to release.")
        return
    generate_metadata(updates, old)
    publish(updates)
    commit_state(updates)
    (ROOT / "release-notes.txt").unlink(missing_ok=True)
    OLD_VERSIONS_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

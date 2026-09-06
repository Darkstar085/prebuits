# Android App Updater

Automatically tracks configured GitHub releases, downloads matching APK/EXE assets, packages changed apps into a GitHub Release, and publishes the same updates to Telegram. 🚀

## ✨ How It Works

The main GitHub Actions workflow:

1. 🔎 Checks configured upstream repositories for their latest releases.
2. 📥 Downloads matching APK/EXE assets.
3. 🧩 Handles repositories whose release asset names need special matching or renaming.
4. 🏷️ Extracts versions and renames changed files as `App_vVERSION.apk` or `App_vVERSION.exe`.
5. 📝 Generates release notes and Telegram captions.
6. 📦 Creates one GitHub Release containing only changed apps.
7. 📲 Publishes changed files to Telegram.
8. 💾 Updates `latest-apk-versions.txt` so unchanged versions are skipped later.

Workflow phases:

- **Download all apps**
- **Process downloaded apps**
- **Prepare release metadata**
- **Create release**
- **Commit update summary**

## 📱 Apps Covered

The configured updater currently covers:

- 📥 ABDownloadManager
- 💻 Acode
- 🔐 Aegis
- 📺 NopeRemote
- 🧹 Kudu
- 🎵 SpotiFLAC
- 🎬 LibreCuts
- 🗺️ Organic Maps
- 🙈 Amarok Hider
- 🎭 Arcticons
- 🔑 Bitwarden
- 🌦️ BreezyWeather
- 🍒 Cherrygram
- 🔄 ConverterNOW
- 🌐 Cromite
- 💻 CpuInfo
- 🎨 DeltaIcons
- 📷 DotGallery
- 🦆 DuckDuckGo
- 🤳 Flip2DND
- ⌨️ Florisboard
- 🧮 Fossify Calculator
- ⌨️ Fossify Keyboard
- 🎶 Fossify Music Player
- 🗒️ Fossify Notes
- 🎤 Fossify Voice Recorder
- 🎼 Gramophone
- 🦦 Iceraven Browser
- 🖼️ ImageToolbox
- 🔒 LibreTube
- 📤 LocalSend
- 🧹 LTECleanerFOSS
- 🪄 Magisk
- 🧩 MicroG RE
- 📖 MoeList
- 📱 Momogram
- 🐱 Nekogram
- 🛠️ Omni
- 🎧 OuterTune
- 🎵 Pixelplay
- 🎧 Phonograph Plus
- 🗂️ Prism File Explorer
- 📥 Quantum Download Manager
- 🤖 Shizuku
- 🧹 SD Maid SE
- 🎵 SimpMusic
- 🎼 Symphony
- 🖥️ Termux
- 📧 Thunderbird Android
- 💻 Visual Code Space
- ☁️ WeatherMaster
- ✏️ Xed Editor
- ⬇️ YTDLnis
- 🎬 Morphe YouTube
- 🎵 Morphe YT Music
- 📷 Morphe Google Photos
- 🧩 Morphe MicroG
- 🛠️ Morphe Manager

The source-of-truth configuration is `.github/workflows/build-release.yml`; `latest-apk-versions.txt` is runtime version state, not a second app configuration list.

## 📦 Releases

Each update creates a GitHub Release containing only apps whose detected version changed since the previous successful update.

Release assets use:

```text
AppName_vVERSION.apk
AppName_vVERSION.exe
```

Release metadata includes updated app names, versions, descriptions, and upstream changelog links.

## 🕐 Automation Schedule

- **Build & Release:** every Sunday at **10:00 AM Asia/Kolkata**.
- **Cleanup:** the **1st of every month at 10:00 AM Asia/Kolkata**.
- Both workflows support manual runs.
- Documentation, version-text, and workflow-only changes are excluded from the automatic build push trigger; manual runs remain available.

## 🧹 Cleanup Policy

The monthly cleanup job:

- Keeps at least 5 recent workflow runs while removing runs older than 1 day.
- Keeps the latest 3 GitHub Releases.
- Keeps the latest 3 numeric `prebuilts-*` tags by run ID.
- Preserves tags attached to retained releases.
- Removes remaining orphaned/old tags.

## 📲 Telegram

Successful releases are automatically published to the configured Telegram channel.

Telegram uploads use a bounded recent-message scan to avoid duplicate filename/size combinations. Captions do not repeat the filename because Telegram already displays the uploaded document name.

## ⚙️ Reliability

- Handles special asset naming and explicit rename cases.
- Continues when an upstream repository has no matching asset.
- Tracks versions to avoid republishing unchanged apps.
- Retries Telegram uploads and handles FloodWait errors.
- Uses concurrency controls to prevent overlapping build or delivery runs.

## 🔐 Required GitHub Secrets

```text
TOKEN
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_SESSION
TELEGRAM_CHAT_ID
```

Keep these values private and never commit them directly to the repository.

## 🤝 Requests & Support

Want an app added or found an issue? Open an issue in the repository or use the project's configured Telegram support channels.

## 📜 License

This repository's workflow scripts and automation code are licensed under the MIT License.

Third-party APK/EXE files referenced or redistributed by the workflow remain the property of their respective copyright holders.

## 🧭 CI Notes

Changes limited to documentation, version text, or workflow files do not need an automatic build. The build workflow remains available through manual dispatch and its weekly schedule.

# Android App Updater

An automated release aggregation and distribution system for Android applications and other configured software.

Android App Updater monitors selected GitHub repositories, detects new releases, downloads the required APK/EXE assets, and publishes updated applications through a centralized GitHub Release and Telegram channel. 🚀

## ✨ Features

- **Automatic release tracking**
  - Monitors configured upstream GitHub repositories
  - Detects newly available versions
- **Smart asset handling**
  - Matches APK/EXE release assets
  - Supports repositories with non-standard asset names
  - Applies explicit rename rules where required
- **Version tracking**
  - Compares upstream versions with previously published versions
  - Republishes only applications that have changed
- **Centralized releases**
  - Creates a single GitHub Release for each update cycle
  - Includes only changed applications
  - Uses a consistent naming format: `AppName_vVERSION.apk` or `AppName_vVERSION.exe`
- **Telegram distribution**
  - Publishes updated applications automatically
  - Avoids duplicate uploads
  - Handles Telegram FloodWait and upload retries

## 🔄 Update Pipeline

```text
              Upstream GitHub Releases
                        │
                        ▼
                 Release Discovery
                        │
                        ▼
                   Asset Download
                        │
                        ▼
                 Asset Processing
                        │
                        ▼
                Version Comparison
                        │
                 ┌──────┴──────┐
                 │             │
              Unchanged      Changed
                 │             │
                Skip           ▼
                       Prepare Release
                              │
                       ┌──────┴──────┐
                       ▼             ▼
                GitHub Release   Telegram
                       │             │
                       └──────┬──────┘
                              ▼
                     Update Version State
```

## 📱 Supported Applications

The updater currently manages a collection of applications, including:

- ABDownloadManager
- Acode
- Aegis
- BreezyWeather
- Cromite
- DuckDuckGo
- Florisboard
- Fossify applications
- ImageToolbox
- LibreTube
- LocalSend
- Magisk
- Shizuku
- Termux
- Thunderbird Android
- YTDLnis
- Morphe applications
- And more

The complete application configuration is maintained in [`apps.json`](apps.json).

## 📦 Releases

Each update creates a GitHub Release containing only applications whose detected version has changed since the previous successful update.

Release metadata includes updated application names, versions, descriptions, and upstream changelog links.

## ⏰ Automation

- **Build & Release:** Every Sunday at **10:00 AM Asia/Kolkata**
- Both workflows support manual execution.

## 📲 Telegram

Successful releases are automatically published to the configured Telegram channel.

Telegram uploads use a bounded recent-message scan to avoid duplicate filename/size combinations. Captions do not repeat the filename because Telegram already displays the uploaded document name.

## ⚙️ Reliability

- Handles special asset naming and explicit rename cases
- Continues when an upstream repository has no matching asset
- Tracks versions to avoid republishing unchanged applications
- Retries Telegram uploads and handles FloodWait errors
- Uses concurrency controls to prevent overlapping build or delivery runs

## 🔐 Required Secrets

The following GitHub Actions secrets are required:

```text
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_SESSION
TELEGRAM_CHAT_ID
```

GitHub authentication uses the built-in `GITHUB_TOKEN` provided by GitHub Actions.

Keep all credentials and session data private and never commit them directly to the repository.

## 🤝 Requests & Support

Want an application added or found an issue?

- Open an issue in this repository
- Use the project's configured Telegram support channels

## 📜 License

The workflow and automation code in this repository is licensed under the MIT License.

Third-party applications and their distributed APK/EXE files remain subject to their respective licenses and copyright ownership.

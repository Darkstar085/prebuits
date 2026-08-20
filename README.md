# Android App Updater

Automatically tracks GitHub releases, downloads updated Android apps, packages them into a GitHub Release, and publishes new updates to Telegram. 🚀

## ✨ How It Works

The GitHub Actions workflow runs automatically and:

1. 🔎 Checks the configured GitHub repositories for new releases.
2. 📥 Downloads matching APK/EXE release assets.
3. 🧩 Detects and processes the actual downloaded filenames.
4. 🏷️ Renames updated files using a consistent `App_VERSION.apk` format.
5. 📝 Generates release notes and Telegram captions.
6. 📦 Creates one GitHub Release containing all updated apps.
7. 📲 Publishes the updated files to the Telegram channel.
8. 💾 Records the latest versions so the same update is not released twice.

The workflow is organized into clear phases in GitHub Actions, making runs easier to follow:

- **Download all apps**
- **Process downloaded apps**
- **Prepare release metadata**
- **Create release**
- **Commit update summary**

## 📱 Apps Covered

- 🔐 Aegis — Modern two-factor authentication app
- 📂 AmazeFileManager — Fast, customizable file manager
- 🙈 AmarokHider — Keep Amarok music app hidden when needed
- 🎭 Arcticons — Modern icon pack and theming app
- 🔑 Bitwarden — Open-source password manager with cloud sync
- 🌦️ BreezyWeather — Clean, customizable open-source weather app
- 🍒 Cherrygram — Enhanced Telegram client with extra features
- 🔄 ConverterNOW — Simple unit and currency converter
- 🌐 Cromite — Privacy-focused browser
- 💻 CpuInfo — Detailed CPU information tool
- 🎨 DeltaIcons — Minimal icon pack
- 📷 DotGallery — Jetpack Compose-based photo gallery
- 🦆 DuckDuckGo — Private, tracker-blocking browser
- ⌨️ Florisboard — Privacy-friendly Android keyboard
- 🤳 Flip2DND — Flip your phone to toggle Do Not Disturb
- 🧮 Fossify Calculator — Open-source calculator
- ⌨️ Fossify Keyboard — Privacy-friendly keyboard
- 🎶 Fossify Music Player — Modern music player
- 🗒️ Fossify Notes — Privacy-focused notes app
- 🎤 Fossify Voice Recorder — Privacy-respecting voice recorder
- 🎼 Gramophone — Minimalist music player
- 🦦 IceravenBrowser — Privacy-focused browser
- 🔒 LibreTube — Open-source YouTube app
- ✂️ LibreCuts — Video editing app
- 📤 LocalSend — Secure local file sharing
- 🧩 MicroG_RE — Enhanced Play Services compatibility
- 📖 MoeList — Anime and manga tracking
- 🛠️ Omni — All-in-one utility app
- 🎧 PhonographPlus — Enhanced music player fork
- 🖼️ Photok — Simple photo gallery
- 🗂️ PrismFileExplorer — Material-design file explorer
- 🖥️ Kudu — Desktop application
- 🕹️ NopeRemote — Remote-control application
- 🎵 ReVanced_GooglePhotos — ReVanced Google Photos build
- 🧩 ReVanced_MicroG — MicroG for ReVanced
- 🎵 ReVanced_YTMusic — ReVanced YouTube Music build
- 🎬 ReVanced_YouTube — ReVanced YouTube build
- 🧹 Sdmaid — System cleaning tool
- 🤖 Shizuku — Advanced Android background utility
- 🎶 Spotify_Revanced — Spotify ReVanced build
- 🎼 SpotiFLAC — Spotify/FLAC-related music application
- 🎼 Symphony — Lightweight music player
- 🖥️ Termux — Terminal emulator and Linux environment
- 📧 ThunderbirdAndroid — Thunderbird email client
- 💻 VisualCodeSpace — Android code editor and IDE
- ☁️ WeatherMaster — Modern weather application
- ✏️ XedEditor — Text/code editor
- ⬇️ Ytdlnis — YouTube downloader
- 🗺️ Organic Maps — Privacy-focused offline maps

## 📦 Releases

Each update creates a GitHub Release containing only apps that have changed since the previous run.

Files follow a consistent naming style such as:

```text
AppName_VERSION.apk
```

The release metadata contains the updated app names, versions, descriptions, and changelog links.

## 📲 Telegram

New releases are automatically published to the Telegram channel:

- 📢 **Channel:** [Darkstar's Hub](https://t.me/darkstar085_channel)

Telegram captions are kept clean and avoid repeating information already displayed by Telegram, such as the uploaded filename.

## ⚙️ Automation

The workflow is designed to be resilient when a repository changes its release asset naming:

- Detects actual downloaded APK filenames where necessary.
- Avoids assuming every APK is named `app-release.apk`.
- Skips repositories when no matching release asset is available.
- Tracks versions to prevent duplicate releases.
- Uses controlled Telegram uploads with retry/error handling.

## 🔐 Required GitHub Secrets

The Telegram publishing workflow uses these repository secrets:

```text
TOKEN
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_SESSION
TELEGRAM_CHAT_ID
```

Keep these values private and never commit them directly to the repository.

## 🤝 Requests & Support

Want an app added or found an issue?

- 💬 Telegram group: [Darkstar's Group](https://t.me/darkstar085_group)
- 🐛 Open an issue in this repository for workflow/app problems.

## 📜 License

This repository's workflow scripts and automation code are licensed under the [MIT License](./LICENSE).

Third-party APK/EXE files referenced or redistributed by the workflow remain the property of their respective copyright holders.

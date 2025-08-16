# Update Prebuilt APKs

Automate the process of fetching, updating, and sharing prebuilt APKs for popular Android apps—all in one workflow!

---

## 📦 Apps & Sources

| App            | Source                                                                |
|----------------|-----------------------------------------------------------------------|
| **Via Browser** | Direct URL: [via-release.apk](https://res.viayoo.com/v1/via-release.apk) |
| **DotGallery**  | GitHub: [`IacobIonut01/Gallery`](https://github.com/IacobIonut01/Gallery)   |
| **DuckDuckGo**  | GitHub: [`duckduckgo/Android`](https://github.com/duckduckgo/Android)        |
| **Keyboard**    | GitHub: [`FossifyOrg/Keyboard`](https://github.com/FossifyOrg/Keyboard)      |

---

## 🚀 What It Does

- Downloads the latest APKs from the above sources  
- Checks APK versions, updates only if new  
- Commits and pushes updated APKs to the repo  
- Sends updated APKs as documents to your Telegram channel with version info  

---

## 📲 Telegram Integration

Updates are sent directly to your Telegram channel or group via a bot.  
Make sure to set these secrets in your repo:  

- `TELEGRAM_TOKEN`: Your bot’s API token  
- `TELEGRAM_CHAT_ID`: Your channel or group chat ID  

---

## ⏰ Schedule & Trigger

- Runs **daily at 10:00 AM IST** automatically  
- Can also be triggered manually from GitHub Actions UI  

---

Keep your APKs always fresh and your team notified with zero hassle!

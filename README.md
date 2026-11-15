# Pricify Store Multi-Platform Promoter Pro

A unified, multi-platform promotional powerhouse supporting **Telegram**, **Instagram**, and **Facebook** in a single interactive dashboard.

---

## 📁 Project Structure

```
telegram-group-ad-sender/
├── sender.py        # Unified engine for Telegram, Instagram & Facebook
├── config.json      # Shared credentials, delays, targets, and Spintax ad templates
├── groups.json      # Telegram target groups list
├── run.bat          # 1-click launcher for Windows
└── README.md        # Comprehensive documentation
```

---

## 🌟 Supported Platforms & Features

### 1. ✈️ Telegram Operations
* **[1] Launch Broadcast:** Single run or Continuous Auto-Loop.
* **[2] Group Scanner:** Discovers joined groups and lets you pick targets interactively.
* **[3] Deep Group Inspector:** Inspects member counts, slowmode delays, write permissions, and link restrictions.

### 2. 📸 Instagram Operations
* **[4] Reel Auto-Commenter:** Finds latest Reels posted by competitor and niche creator pages (`netflix_in`, `primevideoin`, etc.), likes the Reel, and posts human-spaced Spintax comments referring viewers to your profile bio (`@PricifyStore`).
* **[5] Manage Instagram Targets:** Add/remove creator usernames and update your Instagram credentials.

### 3. 📘 Facebook Operations
* **[6] Facebook Group Auto-Poster:** Posts promotional updates into public buyer/deal groups using lightweight browser cookie sessions (`c_user` & `xs`).
* **[7] Manage Facebook Targets:** Add group IDs and update cookies.

### 4. ⚙️ Global Tools & Shared Ad Engine
* **[8] Shared Ad Payload Maker:** Create, edit, or delete Spintax ads (like your Spotify/Apple Music Stock Update). Any ad created here is **automatically available across Telegram, Instagram, and Facebook**!
* **[9] Timing Engine:** Switch between Ultra-Safe, Normal, Fast, and Danger (1s gap) timing profiles.

---

## 🚀 How to Run

Double-click [`run.bat`](file:///C:/Users/Xivam/.gemini/antigravity/scratch/telegram-group-ad-sender/run.bat) or run from PowerShell:
```bash
cd "C:\Users\Xivam\.gemini\antigravity\scratch\telegram-group-ad-sender"
python sender.py
```

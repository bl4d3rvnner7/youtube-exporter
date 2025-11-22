![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=blue)
![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-black?style=for-the-badge)
![Dependencies](https://img.shields.io/badge/Dependencies-yt--dlp%20%7C%20yt--chat--downloader%20%7C%20transcript--api%20%7C%20colorama%20%7C%20pytubefix%20%7C%20requests-blue?style=for-the-badge)
![Output](https://img.shields.io/badge/Output-Chat%20%7C%20Transcript%20%7C%20Video-orange?style=for-the-badge)
![Tested](https://img.shields.io/badge/Tested-Multiple%20YouTube%20Videos-brightgreen?style=for-the-badge)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-blueviolet?style=for-the-badge)

![GitHub Stars](https://img.shields.io/github/stars/bl4d3rvnner7/youtube-exporter?style=for-the-badge)
![GitHub Forks](https://img.shields.io/github/forks/bl4d3rvnner7/youtube-exporter?style=for-the-badge)
![GitHub Issues](https://img.shields.io/github/issues/bl4d3rvnner7/youtube-exporter?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/bl4d3rvnner7/youtube-exporter?style=for-the-badge)

---

# 🎥 YouTube Exporter

**Export YouTube chats, transcripts, profile images, and optionally the video itself — all in one tool.**  
Supports **live streams**, **replays**, **regular videos**, **shorts**, and all URL formats.  
Perfect for analysis, archiving, or research.

---

## 🚀 Features

- Download **live chat** + **replay chat**
- Save **transcripts** with timestamps (start → end)
- Extract clean text logs from YouTube comments
- Download **profile images** of each user
- Extract full metadata → `Video Info.txt` (*Link*, *Uploader*, *Title*, *Video ID*, *Date*, *Comments*, *Views*, *Thumbnail*, *Likes & Dislikes*, *Description*)
- Optional **1080p video download** using `yt-dlp`
- Robust URL parser for every YouTube format
- Auto-creates folders and cleans output formatting

---

## 📦 Requirements

```
yt-dlp
yt-chat-downloader
youtube-transcript-api
pytubefix
requests
colorama
```

Install them via:

```bash
pip install -r requirements.txt
````

---

## ⚙️ Usage (CLI)

Basic usage:

```bash
python3 Exporter.py --url <YouTube_URL>
```

Export chat + transcript:

```bash
python3 Exporter.py --url <URL> --export
```

Download video:

```bash
python3 Exporter.py --url <URL> --download
```

Do everything:

```bash
python3 Exporter.py --url <URL> --export --download
```

---

## 📁 Output Overview

This tool automatically generates:

| File / Folder      | Description                 |
| ------------------ | --------------------------- |
| `Chatdump.txt`     | Clean readable chat log     |
| `ChatDump.json`    | Raw chat dump               |
| `Transcript.txt`   | Transcript with timestamps  |
| `ProfilePictures/` | Downloaded profile images   |
| `Video Info.txt`   | Full metadata dump          |
| `*.mp4`            | Downloaded video (optional) |

Example of a formatted chat entry:

```
[00:12] @user123 (John Doe): Hello everyone!
```

Example transcript line:

```
[00:00 -> 00:04] Willkommen zum heutigen Video!
```

---

## 🧠 Internals & How It Works

The script:

* Extracts the **video ID** using multiple regex patterns
* Uses `yt-dlp` to fetch metadata without downloading
* Downloads chat using `YouTubeChatDownloader`
* Normalizes timestamps and usernames
* Downloads profile pictures via channel scraper (you may have to update cookies at some time)
* Retrieves transcripts via YouTube Transcript API
* Writes output into clean text files
* Optional video download using optimized yt-dlp options

Everything is handled inside `Exporter.py`.

---

## 🤝 Contributing

Pull requests are always welcome.
You can add formats, new exporting features, GUI support, or performance improvements.

---

## ⭐ Support

If you like this project, consider leaving a **star** ⭐ on GitHub.
It motivates further updates and improvements.



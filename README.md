![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=blue)
![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-black?style=for-the-badge)
![Dependencies](https://img.shields.io/badge/Dependencies-yt--dlp%20%7C%20transcript--api%20%7C%20colorama%20%7C%20requests%20%7C%20secretstorage-blue?style=for-the-badge)
![Output](https://img.shields.io/badge/Output-Chat%20%7C%20Transcript%20%7C%20Video-orange?style=for-the-badge)
![Tested](https://img.shields.io/badge/Tested-Multiple%20YouTube%20Videos-brightgreen?style=for-the-badge)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-blueviolet?style=for-the-badge)

![GitHub Stars](https://img.shields.io/github/stars/bl4d3rvnner7/youtube-exporter?style=for-the-badge)
![GitHub Forks](https://img.shields.io/github/forks/bl4d3rvnner7/youtube-exporter?style=for-the-badge)
![GitHub Issues](https://img.shields.io/github/issues/bl4d3rvnner7/youtube-exporter?style=for-the-badge)
![GitHub Last Commit](https://img.shields.io/github/last-commit/bl4d3rvnner7/youtube-exporter?style=for-the-badge)

---

# 🎥 YouTube Exporter

**Export YouTube chats, transcripts, profile images, metadata, and optionally the video itself — all in one tool.**

Supports regular videos, live streams, replays, Shorts, `youtu.be` links, `/live/` links, `/watch?v=` links, embed URLs, and raw YouTube video IDs.

The project includes two variants:

- `Exporter.py` — standalone / cookieless version
- `ExporterCookies.py` — browser-cookie version for videos where YouTube requires authentication or bot-check bypass

---

## 🚀 Features

- Download **live chat / replay chat** when YouTube exposes a `live_chat` replay track
- Save **transcripts** with timestamps
- Export normalized chat data to `Chat.json`
- Export readable chat logs to `Chat.txt`
- Download **profile images** of chat users
- Extract full metadata to `Video Info.txt`
- Optional **video download** using `yt-dlp`
- Robust YouTube URL normalization
- Supports `/watch`, `/live`, `/shorts`, `/embed`, `youtu.be`, and raw video IDs
- Current `yt-dlp` JavaScript challenge support through EJS / Deno
- Cross-platform yt-dlp execution through the current Python interpreter
- Browser-cookie support in `ExporterCookies.py`
- Graceful handling when chat replay is not exposed by YouTube
- Automatic output folder creation

---

## 📦 Requirements

Recommended `requirements.txt`:

- `yt-dlp[default]`
- `youtube-transcript-api`
- `requests`
- `colorama`
- `secretstorage`

Install dependencies with:

`pip install -r requirements.txt`

### Additional system requirement

Recent YouTube extraction may require a supported JavaScript runtime.

Deno is recommended because yt-dlp can use it for YouTube EJS challenge solving.

Deno is **not** a Python package and therefore is not included in `requirements.txt`.

---

## ⚙️ Usage

### Standalone / cookieless version

Basic usage:

`python3 Exporter.py --url <YouTube_URL>`

Export chat + transcript:

`python3 Exporter.py --url <URL> --export`

Download video:

`python3 Exporter.py --url <URL> --download`

Do everything:

`python3 Exporter.py --url <URL> --export --download`

`Exporter.py` intentionally does not use browser cookies.

If YouTube responds with:

`Sign in to confirm you're not a bot`

use `ExporterCookies.py` instead.

---

## 🍪 Browser Cookie Version

`ExporterCookies.py` uses browser cookies for videos where unauthenticated yt-dlp requests are blocked.

Example:

`python3 ExporterCookies.py --url <URL> --export --download`

The cookie-enabled version is designed to use the same authentication path for metadata, chat extraction, and video downloads.

Depending on the version in the repository, browser selection may be automatic or configurable.

Typical supported browsers include:

- Brave
- Chrome
- Chromium
- Firefox
- Edge

### Browser cookie notes

Chromium-based browsers may lock their cookie database while running.

If cookie extraction fails:

1. Fully close the browser.
2. Run the exporter again.
3. Make sure the selected browser profile is logged into YouTube.

On Linux, `secretstorage` may be required for reading browser-encrypted cookies from the desktop keyring.

---

## 💬 Why `yt-chat-downloader` Was Removed

Earlier versions of YouTube Exporter used `yt-chat-downloader` / `YouTubeChatDownloader` directly.

That dependency has been removed from the current exporter path.

### Reason

YouTube has changed its live-chat and replay-chat behavior multiple times.

Older and currently published `yt-chat-downloader` versions can fail on newer YouTube responses with issues such as:

- missing continuation tokens
- `400 INVALID_ARGUMENT`
- bot-detection responses
- authentication failures
- parser failures caused by changed YouTube response structures
- inconsistent cookie support between different library versions

The package also created a second, independent YouTube extraction path inside the project.

That meant a video could work perfectly through yt-dlp while chat extraction failed because `yt-chat-downloader` used different request logic, authentication handling, continuation parsing, and YouTube internals.

### Current approach

The exporter now uses **yt-dlp as the common YouTube backend** wherever possible.

For chat replay extraction, yt-dlp exposes YouTube chat replay as a special `live_chat` subtitle track.

This gives the project a more consistent architecture:

- one YouTube extraction backend
- one authentication path
- one EJS / JavaScript challenge implementation
- fewer version-specific incompatibilities
- simpler cross-platform behavior
- fewer dependencies

If YouTube does not expose a `live_chat` track for a video, the exporter skips chat export gracefully instead of crashing.

### Important limitation

A completed livestream does not always immediately expose its chat replay.

YouTube may still be processing the replay, the creator may have disabled chat replay, or the chat track may simply not be available through the extraction endpoint.

In that case, the exporter can still download available video, metadata, and transcript data.

---

## 🔗 URL Handling

The exporter normalizes supported YouTube URLs into a canonical form:

`https://www.youtube.com/watch?v=<VIDEO_ID>`

Supported input examples include:

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://www.youtube.com/live/VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- raw 11-character video IDs

This avoids compatibility problems caused by downstream tools receiving `/live/`, Shorts, tracking parameters, or other URL variants.

---

## 📁 Output Overview

| File / Folder | Description |
| --- | --- |
| `Chat.txt` | Readable normalized chat log |
| `Chat.json` | Structured chat export |
| `Transcript.txt` | Transcript with timestamps |
| `ProfilePictures/` | Downloaded profile images |
| `Video Info.txt` | Metadata dump |
| `*.mp4` | Downloaded video, when `--download` is used |

Example chat entry:

`[00:12] @user123 (John Doe): Hello everyone!`

Example transcript entry:

`[00:00 -> 00:04] Willkommen zum heutigen Video!`

---

## 🧠 Internals

The exporter currently follows this general flow:

1. Extract and validate the YouTube video ID.
2. Normalize the URL to a canonical `watch?v=` URL.
3. Fetch metadata through yt-dlp.
4. Check whether YouTube exposes a `live_chat` replay track.
5. Export and normalize chat data when available.
6. Retrieve transcript data through `youtube-transcript-api`.
7. Download profile images where possible.
8. Optionally download the video through yt-dlp.
9. Write metadata and session information to disk.

The cookie-enabled variant adds browser authentication to the yt-dlp path.

---

## 🧩 yt-dlp / EJS Notes

Recent YouTube versions use JavaScript challenges that may prevent older or minimally configured yt-dlp installations from exposing all formats.

The exporter is designed for current yt-dlp releases with EJS support.

Using:

`yt-dlp[default]`

is recommended.

A supported JavaScript runtime such as Deno should also be installed on the host system.

If formats are unexpectedly missing, first verify that:

- yt-dlp is current
- Deno is installed
- EJS challenge solving is working
- browser cookies are used when YouTube requires authentication

---

## 🛠 Troubleshooting

### `Sign in to confirm you're not a bot`

Use `ExporterCookies.py` with a browser profile that is logged into YouTube.

### `There are no subtitles for the requested languages`

For chat export, this can mean YouTube is not exposing a `live_chat` replay track.

The exporter will skip chat export and continue with the remaining data.

### `n challenge solving failed`

Update yt-dlp and make sure a supported JavaScript runtime such as Deno is installed.

### Browser cookies cannot be decrypted

Close the browser completely and make sure the required platform keyring dependencies are installed.

On Linux this can include `secretstorage`.

### Requested video format is unavailable

The exporter uses a flexible format selection targeting video up to 720p with an audio fallback rather than requiring one exact format ID.

---

## 🤝 Contributing

Pull requests are welcome.

Useful contribution areas include:

- additional YouTube URL variants
- improved chat parsing
- new export formats
- GUI support
- profile image handling
- better retry logic
- Windows/macOS/Linux compatibility improvements
- tests for archived livestreams and replay chat

---

## ⭐ Support

If you find the project useful, consider leaving a **star** ⭐ on GitHub.

It helps support continued maintenance as YouTube and yt-dlp behavior changes.

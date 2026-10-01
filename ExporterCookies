import os
import sys
import re
import argparse
import subprocess
import tempfile
import json
import platform
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

import colorama
import requests
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

colorama.init()

# ======================= UTILS =======================

def safe_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', name).strip()

def extract_video_id(value: str) -> str:
    """Extract an 11-character YouTube video ID from common URL variants or a raw ID."""
    if not value or not isinstance(value, str):
        raise ValueError("Invalid YouTube URL / video ID")

    value = value.strip()

    # Raw video ID
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    # Add scheme for URLs such as youtube.com/watch?v=...
    candidate = value
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", candidate):
        if candidate.startswith(("youtube.com/", "www.youtube.com/", "m.youtube.com/",
                                 "music.youtube.com/", "youtu.be/")):
            candidate = "https://" + candidate

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""

    # youtu.be/<id>
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = path.lstrip("/").split("/", 1)[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return video_id

    # youtube.com/watch?v=<id>
    if host == "youtube.com" or host.endswith(".youtube.com"):
        query = parse_qs(parsed.query)
        video_id = (query.get("v") or [None])[0]
        if video_id and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            return video_id

        # /live/<id>, /shorts/<id>, /embed/<id>, /v/<id>
        match = re.search(r"/(?:live|shorts|embed|v)/([A-Za-z0-9_-]{11})(?:[/?#]|$)", path)
        if match:
            return match.group(1)

    # Fallback for unusual but recognizable YouTube strings
    patterns = [
        r"(?:youtu\.be/|youtube\.com/(?:live|shorts|embed|v)/)([A-Za-z0-9_-]{11})",
        r"[?&]v=([A-Za-z0-9_-]{11})(?:[&#]|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)

    raise ValueError(f"Could not extract video ID from: {value}")


def canonical_youtube_url(video_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError(f"Invalid YouTube video ID: {video_id}")
    return f"https://www.youtube.com/watch?v={video_id}"


def seconds_to_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes:02d}:{secs:02d}"


def save_transcript_with_timestamps(transcript, output_file: str = "Transcript.txt"):
    global main_dir
    with open(os.path.join(main_dir, output_file), "w", encoding="utf-8") as f:
        for item in transcript:
            text = item.get("text", "").strip()
            if not text:
                continue
            start = item.get("start", 0)
            end = start + item.get("duration", 0)
            line = f"[{seconds_to_timestamp(start)} -> {seconds_to_timestamp(end)}] {text}\n"
            f.write(line)
    print(f"\x1b[97m[\x1b[92m+\x1b[97m] Transcript saved as : \x1b[92m{output_file} ({len(transcript)})\x1b[0m")


def grab_msg(msg) -> str:
    datetime_str = msg.get('datetime', '')
    if datetime_str:
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            datetime_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    timestamp = msg.get('timestamp', '')
    display_name = msg.get('user_display_name', 'Unknown')
    handle = msg.get('user_handle', '@unknown')
    comment = msg.get('comment', '')
    badges = msg.get('badges', [])
    rank_number = msg.get('rank_number')
    time_display = timestamp if timestamp and timestamp != '0:00' else datetime_str
    rank_str = f" #{rank_number}" if rank_number is not None else ""
    badge_str = f" [{', '.join(badges)}]" if badges else ""
    return f"[{time_display}] {handle} ({display_name}){rank_str}{badge_str}: {comment}\n"


def download_image(username: str):
    global main_dir
    filepath = os.path.join(main_dir, "ProfilePictures", f"{username}.jpg")
    if os.path.exists(filepath):
        return
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language': 'en-US,en;q=0.5','DNT': '1','Sec-GPC': '1','Upgrade-Insecure-Requests': '1','Sec-Fetch-Dest': 'document','Sec-Fetch-Mode': 'navigate','Sec-Fetch-Site': 'cross-site','Connection': 'keep-alive'}
    cookies = {'SOCS': 'CAISEwgDEgk4MzQ1MjYxNTkaAmVuIAEaBgiA1_7IBg','YSC': '8mKFfDLuLac','VISITOR_PRIVACY_METADATA': 'CgJHQhIEGgAgLQ%3D%3D','PREF': 'tz=Europe.Berlin&f6=40000000&f7=100','VISITOR_INFO1_LIVE': 'NBIpGV5Ujd4','GPS': '1'}
    try:
        if "@" in username:
            username = username.replace('@', '')
        response = requests.get(f'https://www.youtube.com/@{username}', headers=headers, cookies=cookies, timeout=3)
        match = re.search(r'<meta property="og:image" content="(.*?)"', response.text)
        if match:
            img_url = match.group(1)
            img_data = requests.get(img_url, timeout=10).content
            with open(filepath, 'wb') as f:
                f.write(img_data)
    except Exception as e:
        print(f"Download failed for following user profile picture: @{username}: {e}")


def get_dislikes(video_id: str) -> int:
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0','Accept': '*/*','Accept-Language': 'en-US,en;q=0.5','Accept-Encoding': 'gzip, deflate, br, zstd','Referer': 'https://www.youtube.com/','Origin': 'https://www.youtube.com','DNT': '1','Sec-GPC': '1','Sec-Fetch-Dest': 'empty','Sec-Fetch-Mode': 'cors','Sec-Fetch-Site': 'cross-site','Connection': 'keep-alive'}
    params = (('videoId', video_id),)
    response = requests.get('https://returnyoutubedislikeapi.com/Votes', headers=headers, params=params)
    try:
        response.raise_for_status()
        if response.status_code == 200:
            json_info = response.json()
            return json_info.get('dislikes')
    except Exception:
        pass
    return 0

# ======================= ARGUMENT PARSING =======================
def parse_args():
    parser = argparse.ArgumentParser(description="YouTube Chat, Transcript & Video Downloader")
    parser.add_argument("--url", type=str, required=True, help="YouTube video URL")
    parser.add_argument("--download", action="store_true", help="Download video")
    parser.add_argument("--export", action="store_true", help="Export chat & transcript")
    parser.add_argument(
        "--browser",
        default="auto",
        choices=["auto", "brave", "chrome", "chromium", "firefox", "edge"],
        help="Browser to read YouTube cookies from (default: auto)",
    )
    parser.add_argument(
        "--cookies",
        dest="cookies_file",
        help="Optional Netscape cookies.txt file; overrides --browser",
    )
    return parser.parse_args()



# ======================= YT-DLP / AUTH HELPERS =======================

def yt_dlp_base_cmd():
    """Run the same yt-dlp installation as this Python interpreter."""
    return [sys.executable, "-m", "yt_dlp"]


def browser_candidates(preferred="auto"):
    if preferred != "auto":
        return [preferred]

    system = platform.system().lower()
    if system == "windows":
        return ["brave", "chrome", "edge", "firefox", "chromium"]
    if system == "darwin":
        return ["brave", "chrome", "firefox", "edge", "chromium"]
    return ["brave", "chrome", "chromium", "firefox", "edge"]


def auth_cli_args(browser="auto", cookies_file=None):
    if cookies_file:
        return ["--cookies", os.path.abspath(os.path.expanduser(cookies_file))]
    # Browser is resolved later where failures can be tested.
    return ["--cookies-from-browser", browser]


def export_browser_cookies(url, browser="auto", cookies_file=None):
    """
    Return (cookie_path, temporary, selected_browser).
    If --cookies was supplied, use it directly.
    Otherwise try supported browsers and export cookies to a temporary
    Netscape-format file for libraries that cannot read browser databases.
    """
    if cookies_file:
        path = os.path.abspath(os.path.expanduser(cookies_file))
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Cookie file not found: {path}")
        return path, False, None

    errors = []
    for candidate in browser_candidates(browser):
        fd, path = tempfile.mkstemp(prefix="yt_chat_", suffix=".cookies.txt")
        os.close(fd)
        os.remove(path)  # yt-dlp must create the Netscape file itself

        cmd = yt_dlp_base_cmd() + [
            "--cookies-from-browser", candidate,
            "--cookies", path,
            "--skip-download",
            "--quiet",
            "--no-warnings",
            url,
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                return path, True, candidate
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    raise RuntimeError(
        "Could not export browser cookies. Tried: "
        + ", ".join(browser_candidates(browser))
        + (f" ({'; '.join(errors)})" if errors else "")
    )


def get_video_info(url, browser="auto", cookies_file=None):
    """
    Fetch metadata through yt-dlp CLI so Windows/macOS/Linux all use the same
    yt-dlp configuration and JS runtime behavior.
    """
    last_error = None
    candidates = [None] if cookies_file else browser_candidates(browser)

    for candidate in candidates:
        cmd = yt_dlp_base_cmd() + [
            "--remote-components", "ejs:github",
            "--dump-single-json",
            "--skip-download",
            "--no-warnings",
        ]

        if cookies_file:
            cmd += ["--cookies", os.path.abspath(os.path.expanduser(cookies_file))]
        else:
            cmd += ["--cookies-from-browser", candidate]

        cmd.append(url)

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(result.stdout), candidate
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"yt-dlp metadata extraction failed: {last_error}")



# ======================= YOUTUBE CHAT VIA YT-DLP =======================

def has_live_chat_track(info):
    """Return True if yt-dlp exposes a YouTube live_chat subtitle/replay track."""
    subtitles = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    return "live_chat" in subtitles or "live_chat" in automatic



def _runs_text(obj):
    runs = obj.get("runs", []) if isinstance(obj, dict) else []
    return "".join(run.get("text", "") for run in runs if isinstance(run, dict))


def _parse_chat_renderer(renderer):
    if not isinstance(renderer, dict):
        return None

    author = renderer.get("authorName", {})
    display_name = author.get("simpleText", "") if isinstance(author, dict) else ""
    author_id = renderer.get("authorExternalChannelId", "")
    message = _runs_text(renderer.get("message", {}))

    if not message:
        # Memberships / paid messages can use alternative fields
        message = (
            _runs_text(renderer.get("headerSubtext", {}))
            or _runs_text(renderer.get("primaryText", {}))
            or _runs_text(renderer.get("purchaseAmountText", {}))
        )

    badges = []
    for badge in renderer.get("authorBadges", []) or []:
        br = badge.get("liveChatAuthorBadgeRenderer", {})
        tooltip = br.get("tooltip")
        if tooltip:
            badges.append(tooltip)

    offset_usec = renderer.get("videoOffsetTimeMsec")
    if offset_usec is not None:
        try:
            seconds = int(offset_usec) / 1000.0
            timestamp = seconds_to_timestamp(seconds)
        except Exception:
            timestamp = ""
    else:
        timestamp = renderer.get("timestampText", {}).get("simpleText", "")

    timestamp_usec = renderer.get("timestampUsec")
    datetime_str = ""
    if timestamp_usec:
        try:
            dt = datetime.fromtimestamp(int(timestamp_usec) / 1_000_000, timezone.utc)
            datetime_str = dt.isoformat()
        except Exception:
            pass

    purchase = renderer.get("purchaseAmountText", {})
    purchase_amount = purchase.get("simpleText", "") if isinstance(purchase, dict) else ""

    return {
        "user_id": author_id,
        "user_display_name": display_name or "Unknown",
        "user_handle": "",
        "datetime": datetime_str,
        "timestamp": timestamp,
        "comment": message,
        "message_type": (
            "super_chat" if purchase_amount
            else "membership" if "Membership" in str(type(renderer))
            else "text"
        ),
        "badges": badges,
        "message_id": renderer.get("id", ""),
        "purchase_amount": purchase_amount,
        "video_offset_ms": renderer.get("videoOffsetTimeMsec", ""),
    }


def _walk_chat_actions(obj, out):
    """Recursively extract common YouTube live-chat renderer objects."""
    if isinstance(obj, dict):
        renderer_keys = (
            "liveChatTextMessageRenderer",
            "liveChatPaidMessageRenderer",
            "liveChatMembershipItemRenderer",
            "liveChatPaidStickerRenderer",
        )
        for key in renderer_keys:
            if key in obj:
                parsed = _parse_chat_renderer(obj[key])
                if parsed and (parsed.get("comment") or parsed.get("user_display_name")):
                    out.append(parsed)

        for value in obj.values():
            _walk_chat_actions(value, out)

    elif isinstance(obj, list):
        for item in obj:
            _walk_chat_actions(item, out)


def download_chat_with_ytdlp(url, main_dir, browser="auto", cookies_file=None):
    """
    Download YouTube live-chat replay using yt-dlp's live_chat subtitle.
    This uses the same cross-platform authentication path as video downloads.
    Returns normalized chat message dictionaries.
    """
    chat_base = os.path.join(main_dir, "yt_chat_raw")

    cmd = yt_dlp_base_cmd() + [
        "--remote-components", "ejs:github",
        "--skip-download",
        "--write-subs",
        "--sub-langs", "live_chat",
        "--sub-format", "json",
        "-o", chat_base + ".%(ext)s",
    ]

    if cookies_file:
        cmd += ["--cookies", os.path.abspath(os.path.expanduser(cookies_file))]
    else:
        cmd += ["--cookies-from-browser", browser]

    cmd.append(url)

    subprocess.run(cmd, check=True)

    candidates = [
        Path(chat_base + ".live_chat.json"),
        Path(chat_base + ".json"),
    ]
    raw_path = next((p for p in candidates if p.exists()), None)

    if raw_path is None:
        # yt-dlp naming can vary; look for the generated live_chat file.
        found = list(Path(main_dir).glob("yt_chat_raw*.json"))
        raw_path = found[0] if found else None

    if raw_path is None:
        raise RuntimeError("yt-dlp did not produce a live_chat JSON file")

    messages = []
    with raw_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            _walk_chat_actions(data, messages)

    # Deduplicate renderer IDs because recursive replay structures can repeat.
    unique = []
    seen = set()
    for msg in messages:
        key = msg.get("message_id") or (
            msg.get("timestamp"),
            msg.get("user_display_name"),
            msg.get("comment"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(msg)

    with open(os.path.join(main_dir, "Chat.json"), "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    try:
        raw_path.unlink()
    except OSError:
        pass

    return unique


# ======================= MAIN FUNCTION =======================
def main():
    global main_dir
    args = parse_args()
    url = args.url
    skip_download = not args.download
    skip_export = not args.export
    browser = args.browser
    cookies_file = args.cookies_file

    try:
        video_id = extract_video_id(url)
        url = canonical_youtube_url(video_id)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"\x1b[97m[\x1b[92m+\x1b[97m] Video ID: \x1b[92m{video_id}\x1b[0m")
    print(f"\x1b[97m[\x1b[92m+\x1b[97m] Canonical URL: \x1b[92m{url}\x1b[0m")

    # ======================= VIDEO INFO =======================
    info, selected_browser = get_video_info(
        url,
        browser=browser,
        cookies_file=cookies_file,
    )
    if selected_browser:
        browser = selected_browser
        print(f"\x1b[97m[\x1b[92m+\x1b[97m] Browser cookies: \x1b[92m{browser}\x1b[0m")
    elif cookies_file:
        print(f"\x1b[97m[\x1b[92m+\x1b[97m] Cookies file: \x1b[92m{cookies_file}\x1b[0m")

    main_dir = safe_filename(info.get('title') or video_id)
    os.makedirs(main_dir, exist_ok=True)
    os.makedirs(os.path.join(main_dir, "ProfilePictures"), exist_ok=True)

    try:
        if info.get('is_live'):
            start_time = "Live"
        elif info.get('release_timestamp', 0):
            start_time = datetime.fromtimestamp(info.get('release_timestamp', 0), timezone.utc).strftime('%d.%m.%Y - %H:%M:%S')
        elif info.get('timestamp', 0):
            start_time = datetime.fromtimestamp(info.get('timestamp', 0), timezone.utc).strftime('%d.%m.%Y - %H:%M:%S')
        else:
            start_time = "N/A"
    except:
        start_time = 'N/A'
    print(f"\x1b[97m[\x1b[92m+\x1b[97m] {info.get('title')} \x1b[97m(\x1b[95m{start_time}\x1b[97m)")

    kcounter = 0

    # ======================= CHAT EXPORT =======================
    if not skip_export:
        chat = []

        if has_live_chat_track(info):
            print("\x1b[97m[\x1b[92m+\x1b[97m] Downloading chat via yt-dlp...\x1b[0m")
            try:
                chat = download_chat_with_ytdlp(
                    url,
                    main_dir,
                    browser=browser,
                    cookies_file=cookies_file,
                )
            except Exception as e:
                print(f"Chat-Error: {e}")
                chat = []
        else:
            live_status = info.get("live_status", "unknown")
            print(
                "\x1b[97m[\x1b[93m!\x1b[97m] "
                "No live_chat replay track exposed by YouTube/yt-dlp "
                f"(live_status={live_status}). Skipping chat export.\x1b[0m"
            )

        with open(os.path.join(main_dir, "Chat.txt"), "w", encoding="utf-8") as f:
            for msg in chat:
                try:
                    kcounter += 1
                    f.write(grab_msg(msg))
                    username = (
                        msg.get("user_handle", "").lstrip("@")
                        or msg.get("user_display_name", "unknown")
                    )
                    download_image(username)
                except Exception as e:
                    print(f"Error at dumping chat: {e}")
                    continue

        print(f"\x1b[97m[\x1b[92m+\x1b[97m] \x1b[95m{kcounter}\x1b[97m Exported chat → Chat.txt\x1b[0m")

    # ======================= TRANSCRIPT =======================
    if not skip_export:
        try:
            yt_transcript = YouTubeTranscriptApi()
            try:
                transcript_class = yt_transcript.fetch(video_id=video_id, languages=["de"])
                transcript = transcript_class.to_raw_data()
                if len(transcript) > 0:
                    save_transcript_with_timestamps(transcript, "Transcript.txt")
            except:
                try:
                    print(yt_transcript.get_transcript(video_id=video_id, languages=['de']))
                except:
                    pass
        except Exception as e:
            print(f"No Transcript available: {e}")

    # ======================= VIDEO DOWNLOAD =======================
    if not skip_download:
        print("\x1b[97m[\x1b[92m+\x1b[97m] Downloading video, this can take a while...\x1b[0m")
        
        outpath = os.path.join(main_dir, "%(title)s.%(ext)s")
        cmd = yt_dlp_base_cmd() + [
            "--remote-components", "ejs:github",
            "-N", "4",
            "--no-part",
            "-o", outpath,
            "--continue",
        ]

        if cookies_file:
            cmd += ["--cookies", os.path.abspath(os.path.expanduser(cookies_file))]
        else:
            cmd += ["--cookies-from-browser", browser]

        cmd += [
            "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "--merge-output-format", "mp4",
            "--retries", "infinite",
            "--fragment-retries", "infinite",
            "--no-overwrites",
            url,
        ]
        subprocess.run(cmd, check=True)
        print(f"\x1b[97m[\x1b[92m+\x1b[97m] Saved Video!\x1b[0m")

    # ======================= VIDEO INFO TXT =======================
    info_text = f"""~ Video Information ~

├─> Link         : {url}
├─> Uploader     : {info.get('uploader') or info.get('channel', 'N/A')}
├─> Title        : {info.get('title', 'N/A')}
├─> Video ID     : {video_id}
├─> Date         : {start_time}
├─> Comments     : {kcounter}
├─> Views        : {info.get('view_count', 'N/A')}
├─> Thumbnail    : {info.get('thumbnail', 'N/A')}
├─> Likes        : {info.get('like_count', 'N/A')}
├─> Dislikes     : {get_dislikes(video_id)}
└─> Description  : {info.get('description', '')}
"""
    with open(os.path.join(main_dir, "Video Info.txt"), "w", encoding="utf-8") as f:
        f.write(info_text)
    print(f"\x1b[97m[\x1b[92m+\x1b[97m] Video Info.txt created\x1b[0m")

    with open('.session', 'w') as f:
        f.write(main_dir)

# ======================= ENTRY POINT =======================
if __name__ == "__main__":
    main()

import os
import sys
import re
import argparse
import subprocess
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import colorama
import requests
import yt_dlp
from yt_chat_downloader import YouTubeChatDownloader
from youtube_transcript_api import YouTubeTranscriptApi
from pytubefix import YouTube
from pytubefix.cli import on_progress

colorama.init()

# ======================= UTILS =======================
def extract_video_id(url: str) -> str:
    if not url or not isinstance(url, str):
        raise ValueError("Invalid URL")
    url = url.strip()
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0].split("&")[0].split("#")[0]
    patterns = [
        r"(?:v=|\/embed\/|\/watch\?v=|\/v\/|\/live\/|live\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})",
        r"youtube\.com.*[?&]v=([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    parsed = urlparse(url)
    if parsed.hostname and "youtube.com" in parsed.hostname:
        query_params = parse_qs(parsed.query)
        if "v" in query_params:
            return query_params["v"][0][:11]
    raise ValueError(f"Could not extract video ID from URL: {url}")


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
    return parser.parse_args()


# ======================= MAIN FUNCTION =======================
def main():
    global main_dir
    args = parse_args()
    url = args.url
    skip_download = not args.download
    skip_export = not args.export

    try:
        video_id = extract_video_id(url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"\x1b[97m[\x1b[92m+\x1b[97m] Video ID: \x1b[92m{video_id}\x1b[0m")

    # ======================= VIDEO INFO =======================
    yt = YouTube(url, on_progress_callback=on_progress)
    ydl = yt_dlp.YoutubeDL({'quiet': True})
    info = ydl.extract_info(url, download=False)

    main_dir = yt.title.replace('"', '').replace("'", "")
    os.makedirs(main_dir, exist_ok=True)
    os.makedirs(os.path.join(main_dir, "ProfilePictures"), exist_ok=True)

    start_time = "Live" if info.get('is_live') else datetime.utcfromtimestamp(info.get('release_timestamp', 0)).strftime('%d.%m.%Y - %H:%M:%S')
    print(f"\x1b[97m[\x1b[92m+\x1b[97m] {info.get('title')} \x1b[97m(\x1b[95m{start_time}\x1b[97m)")

    kcounter = 0

    # ======================= CHAT EXPORT =======================
    if not skip_export:
        print("\x1b[97m[\x1b[92m+\x1b[97m] Downloading chat...\x1b[0m")
        downloader = YouTubeChatDownloader()
        try:
            chat = downloader.download_chat(video_url=url, chat_type="both", output_file=os.path.join(main_dir, "Chat.json"))
        except Exception as e:
            print(f"Chat-Error: {e}")
            chat = []

        with open(os.path.join(main_dir, "Chat.txt"), "w", encoding="utf-8") as f:
            for msg in chat:
                try:
                    kcounter += 1
                    f.write(grab_msg(msg))
                    username = msg.get('user_handle', '').lstrip('@') or msg.get('user_display_name', 'unknown')
                    download_image(username)
                except Exception as e:
                    print(f"Error at dumping chat: {e}")
                    continue

        print(f"\x1b[97m[\x1b[92m+\x1b[97m] \x1b[95m{kcounter}\x1b[97m Exported chat → Chat.txt\x1b[0m")

    # ======================= TRANSCRIPT =======================
    if not skip_export:
        try:
            yt_transcript = YouTubeTranscriptApi()
            transcript_class = yt_transcript.fetch(video_id=video_id, languages=["de"])
            transcript = transcript_class.to_raw_data()
            if len(transcript) > 0:
                save_transcript_with_timestamps(transcript, "Transcript.txt")
        except Exception as e:
            print(f"No Transcript available: {e}")

    # ======================= VIDEO DOWNLOAD =======================
    if not skip_download:
        print("\x1b[97m[\x1b[92m+\x1b[97m] Downloading video, this can take a while...\x1b[0m")
        
        outpath = os.path.join(main_dir, "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-N", "4",
            "--no-part",
            "-o", outpath,
            "--wait-for-video", "5-15",
            "--continue",
            "-f", "bestvideo[height=720]+bestaudio",
            "--merge-output-format", "mp4",
            "--retries", "infinite",
            "--fragment-retries", "infinite",
            "--no-overwrites",
            url
        ]
        subprocess.run(cmd, check=True)
        print(f"\x1b[97m[\x1b[92m+\x1b[97m] Saved Video!\x1b[0m")

    # ======================= VIDEO INFO TXT =======================
    info_text = f"""~ Video Information ~

├─> Link         : {url}
├─> Uploader     : {yt.author}
├─> Title        : {yt.title}
├─> Video ID     : {video_id}
├─> Date         : {start_time}
├─> Comments     : {kcounter}
├─> Views        : {yt.views or info.get('view_count', 'N/A')}
├─> Thumbnail    : {yt.thumbnail_url}
├─> Likes        : {yt.likes or info.get('like_count', 'N/A')}
├─> Dislikes     : {get_dislikes(video_id)}
└─> Description  : {yt.description}
"""
    with open(os.path.join(main_dir, "Video Info.txt"), "w", encoding="utf-8") as f:
        f.write(info_text)
    print(f"\x1b[97m[\x1b[92m+\x1b[97m] Video Info.txt created\x1b[0m")

    with open('.session', 'w') as f:
        f.write(main_dir)

# ======================= ENTRY POINT =======================
if __name__ == "__main__":
    main()

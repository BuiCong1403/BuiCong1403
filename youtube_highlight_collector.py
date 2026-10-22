import json
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "youtube_highlight_cache.json"
TZ = timezone(timedelta(hours=7))
CHANNELS = {
    "FPT Bong Da": "UC4LvrpNXujjbGOS4RDvr41g",
    "TV360 The Thao": "UCbxWTKqVmD_AMeOIcKFhQ3Q",
    "SCTV The Thao": "UCiWyQp2HgKX2-WQUq11V8FA",
    "MyTV Football": "UC8P4an6-C_1PlbGGVgE9KhA",
    "VTVcab C1": "UCbdlxg0t8O7WGPrFsVcz6Gg",
    "VTVcab Bong Da": "UCErTggiNDIaWJbDJuQKvN2Q",
    "WEBTHETHAO": "UCXtlD2njsXWo2HoPfSC-rsQ",
}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def recent(items, days=5):
    cutoff = datetime.now(TZ) - timedelta(days=days)
    kept = []
    for item in items:
        try:
            published = datetime.fromisoformat(item["published"].replace("Z", "+00:00"))
            if cutoff <= published <= datetime.now(TZ) + timedelta(hours=1):
                kept.append(item)
        except (KeyError, ValueError, TypeError):
            continue
    return sorted(kept, key=lambda item: item["published"], reverse=True)


def read_cache(path=CACHE):
    try:
        return recent(json.loads(path.read_text(encoding="utf-8"))["videos"])
    except (OSError, ValueError, KeyError, TypeError):
        return []


def feed_items(text, channel):
    result = []
    for entry in ET.fromstring(text).findall("a:entry", NS):
        video_id = entry.findtext("yt:videoId", namespaces=NS)
        if video_id:
            result.append({"id": video_id, "channel": channel,
                           "title": entry.findtext("a:title", namespaces=NS) or video_id,
                           "published": entry.findtext("a:published", namespaces=NS) or ""})
    return recent(result)


def channel_page_items(text, channel):
    marker = re.search(r'(?:var\s+ytInitialData|window\["ytInitialData"\])\s*=\s*', text)
    if not marker:
        raise ValueError("YouTube channel response has no video data")
    data = json.JSONDecoder().raw_decode(text[marker.end():])[0]
    result = []

    def walk(node):
        if isinstance(node, dict):
            video = node.get("videoRenderer")
            lockup = node.get("lockupViewModel")
            if isinstance(lockup, dict):
                metadata = (lockup.get("metadata") or {}).get("lockupMetadataViewModel") or {}
                rows = ((metadata.get("metadata") or {}).get("contentMetadataViewModel") or {}).get("metadataRows", [])
                labels = []
                for row in rows:
                    for part in row.get("metadataParts", []):
                        labels.append(part.get("accessibilityLabel") or (part.get("text") or {}).get("content", ""))
                video = {"videoId": lockup.get("contentId"), "title": {"simpleText": (metadata.get("title") or {}).get("content", "")},
                         "publishedTimeText": {"simpleText": " ".join(labels)}}
            if isinstance(video, dict):
                label = (video.get("publishedTimeText") or {}).get("simpleText", "")
                label = label.replace("\u00a0", " ")
                age = re.search(r'(\d+)\s*(minute|hour|day|week|min|hr|m|h|d|w)s?\s+ago', label, re.I)
                video_id = video.get("videoId")
                if age and video_id:
                    seconds = int(age.group(1)) * {"minute": 60, "min": 60, "m": 60, "hour": 3600, "hr": 3600, "h": 3600, "day": 86400, "d": 86400, "week": 604800, "w": 604800}[age.group(2).lower()]
                    title = video.get("title") or {}
                    result.append({"id": video_id, "channel": channel,
                                   "title": title.get("simpleText") or "".join(x.get("text", "") for x in title.get("runs", [])),
                                   "published": (datetime.now(TZ) - timedelta(seconds=seconds)).isoformat()})
                return
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    tabs = (data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs") or [])
    for tab in tabs:
        content = tab.get("tabRenderer") or {}
        if content.get("selected"):
            walk(content.get("content", {}))
    return recent(result)


def valid_hls(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    text = response.text.lstrip()
    if not text.startswith("#EXTM3U"):
        return False
    child = next((line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")), None)
    if not child:
        return False
    if "#EXT-X-STREAM-INF" in text:
        response = requests.get(urljoin(url, child), timeout=20)
        response.raise_for_status()
        text = response.text.lstrip()
    return text.startswith("#EXTM3U") and "#EXTINF:" in text


def check_item(item):
    url = "https://caodanh.io.vn/highlight/iptv_hls.php?v=" + item["id"] + "&ext=.m3u8"
    try:
        if valid_hls(url):
            return dict(item, url=url)
    except requests.RequestException:
        pass
    return None


def load_channels():
    channels = []
    for item in read_cache():
        published = datetime.fromisoformat(item["published"].replace("Z", "+00:00")).astimezone(TZ)
        channels.append({"source": "YouTubeHighlight", "group": "Highlight",
                         "name": f"{item['title']} | {item['channel']} | {published:%d/%m}",
                         "logo": f"https://i.ytimg.com/vi/{item['id']}/hqdefault.jpg",
                         "stream_url": item["url"], "referer": "", "user_agent": "",
                         "event_date": published.date(), "event_datetime": published,
                         "skip_event_filter": True})
    return channels


def main():
    previous = read_cache()
    try:
        socket.getaddrinfo("caodanh.io.vn", 443)
    except OSError as exc:
        raise RuntimeError("CaoDanh DNS lookup failed; video availability cannot be checked. Previous snapshot preserved.") from exc
    candidates = []
    feeds_ok = 0
    for channel, channel_id in CHANNELS.items():
        try:
            response = requests.get("https://www.youtube.com/feeds/videos.xml",
                                    params={"channel_id": channel_id}, timeout=25)
            response.raise_for_status()
            items = feed_items(response.text, channel)
            candidates.extend(items)
            feeds_ok += 1
            print(f"[YouTube] {channel}: {len(items)} recent videos", flush=True)
        except (requests.RequestException, ET.ParseError) as exc:
            print(f"[WARN] {channel}: {exc}", flush=True)
        # RSS only exposes 15 uploads, frequently crowded by Shorts. Always
        # inspect the public Videos tab as an independent discovery path.
        try:
            response = requests.get(f"https://www.youtube.com/channel/{channel_id}/videos",
                                    params={"hl": "en", "gl": "US"}, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}, timeout=25)
            response.raise_for_status()
            items = channel_page_items(response.text, channel)
            candidates.extend(items)
            feeds_ok += 1
            print(f"[YouTube page] {channel}: {len(items)} recent videos", flush=True)
        except (requests.RequestException, ValueError) as fallback_error:
            print(f"[WARN] {channel} page fallback: {fallback_error}", flush=True)
    if not feeds_ok:
        raise RuntimeError("All YouTube feeds failed; previous snapshot preserved")
    if not candidates:
        raise RuntimeError("No recent videos discovered; previous snapshot preserved, not marked refreshed")
    unique = {}
    for item in candidates:
        unique.setdefault(item["id"], item)
    candidates = list(unique.values())
    with ThreadPoolExecutor(max_workers=4) as pool:
        checked = list(pool.map(check_item, candidates))
    valid = [item for item in checked if item]
    for channel in CHANNELS:
        found = sum(item["channel"] == channel for item in candidates)
        playable = sum(item["channel"] == channel for item in valid)
        print(f"[CHECK] {channel}: {playable}/{found} playable", flush=True)
    if candidates and not valid:
        raise RuntimeError("No playable CaoDanh videos; previous snapshot preserved")
    merged = {item["id"]: item for item in previous}
    for item in valid:
        merged[item["id"]] = item
    # Transient network failures do not discard previously validated videos;
    # publication time still expires them after five days.
    videos = recent(list(merged.values()))
    temporary = CACHE.with_suffix(".tmp")
    temporary.write_text(json.dumps({"updated": datetime.now(TZ).isoformat(), "videos": videos}, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(CACHE)
    print(f"[DONE] {len(valid)}/{len(candidates)} checked videos playable; snapshot {len(videos)}", flush=True)


if __name__ == "__main__":
    main()

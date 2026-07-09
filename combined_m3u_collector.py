import html
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import requests
except Exception:
    requests = None


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output_combined"
ALL_M3U = BASE_DIR / "full.m3u"
ALL_JSON = BASE_DIR / "all_sources.json"
STATS_TXT = BASE_DIR / "stats.txt"
TZ_VN = timezone(timedelta(hours=7))

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

CHUOICHIEN_TOKEN = os.environ.get("CHUOICHIEN_TOKEN", "").strip()
# Default is raw collection for GitHub Actions: keep every non-empty .m3u8 link.
# Set VERIFY_STREAMS=1 only when you want to test whether streams respond now.
VERIFY_STREAMS = os.environ.get("VERIFY_STREAMS", "0").strip().lower() in {"1", "true", "yes"}
MAX_VERIFY_WORKERS = int(os.environ.get("MAX_VERIFY_WORKERS", "20"))


def log(message):
    print(message, flush=True)


def now_ict():
    return datetime.now(TZ_VN).strftime("%Y-%m-%d %H:%M ICT")


def request_get(url, headers=None, params=None, timeout=20):
    merged_headers = {
        "User-Agent": UA,
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    }
    if headers:
        merged_headers.update(headers)
    if requests is not None:
        return requests.get(url, headers=merged_headers, params=params, timeout=timeout)
    return urllib_request("GET", url, headers=merged_headers, params=params, timeout=timeout)


class UrllibResponse:
    def __init__(self, status_code, data, url):
        self.status_code = status_code
        self.content = data
        self.text = data.decode("utf-8", errors="replace")
        self.url = url

    def json(self):
        return json.loads(self.text)


def urllib_request(method, url, headers=None, params=None, timeout=20):
    if params:
        separator = "&" if "?" in url else "?"
        url = url + separator + urlencode(params)
    request = Request(url, headers=headers or {}, method=method)
    with urlopen(request, timeout=timeout) as response:
        return UrllibResponse(response.getcode(), response.read(), response.geturl())


def fetch_json(url, headers=None, timeout=20):
    try:
        r = request_get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            log(f"[HTTP] {r.status_code} {url}")
            return {}
        return r.json()
    except Exception as exc:
        log(f"[HTTP] JSON error {url}: {exc}")
        return {}


def clean_text(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def parse_iso_to_ict(value, fmt="%H:%M | %d.%m"):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(TZ_VN).strftime(fmt)
    except Exception:
        return str(value)


def channel_key(channel):
    return (
        channel.get("stream_url", "").strip(),
        channel.get("name", "").strip(),
        channel.get("source", "").strip(),
    )


def is_valid_stream_url(url):
    url = clean_text(url)
    return bool(url and ".m3u8" in url and not url.startswith(("udp://", "rtp://")))


def is_working_m3u8(url, referer="", user_agent=UA):
    if not is_valid_stream_url(url):
        return False

    headers = {"User-Agent": user_agent or UA}
    if referer:
        headers["Referer"] = referer

    try:
        if requests is not None:
            response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        else:
            response = urllib_request("HEAD", url, headers=headers, timeout=5)
        if response.status_code in (200, 204, 206):
            return True
        if response.status_code not in (403, 405):
            return False
    except Exception:
        pass

    try:
        headers["Range"] = "bytes=0-2048"
        if requests is not None:
            response = requests.get(url, headers=headers, timeout=8, stream=True, allow_redirects=True)
        else:
            response = urllib_request("GET", url, headers=headers, timeout=8)
        return response.status_code in (200, 204, 206)
    except Exception:
        return False


def verify_live_channels(channels):
    unique = []
    seen = set()
    for channel in channels:
        url = clean_text(channel.get("stream_url"))
        if not url or url in seen:
            continue
        seen.add(url)
        channel["stream_url"] = url
        unique.append(channel)

    if not VERIFY_STREAMS or not unique:
        return unique

    live = []
    with ThreadPoolExecutor(max_workers=MAX_VERIFY_WORKERS) as executor:
        futures = {
            executor.submit(
                is_working_m3u8,
                channel.get("stream_url", ""),
                channel.get("referer", ""),
                channel.get("user_agent", UA),
            ): channel
            for channel in unique
        }
        for future in as_completed(futures):
            channel = futures[future]
            try:
                if future.result():
                    live.append(channel)
            except Exception:
                pass
    live.sort(key=lambda item: (item.get("source", ""), item.get("name", "")))
    return live


def write_m3u(path, channels):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Updated : {now_ict()}\n")
        f.write(f"# Total   : {len(channels)}\n\n")
        for ch in channels:
            attrs = [
                f'tvg-logo="{ch.get("logo", "")}"',
                f'group-title="{ch.get("group", ch.get("source", "Unknown"))}"',
            ]
            f.write(f'#EXTINF:-1 {" ".join(attrs)},{ch.get("name", "Unknown")}\n')
            if ch.get("referer"):
                f.write(f'#EXTVLCOPT:http-referrer={ch["referer"]}\n')
            if ch.get("user_agent"):
                f.write(f'#EXTVLCOPT:http-user-agent={ch["user_agent"]}\n')
            f.write(f'{ch.get("stream_url", "")}\n\n')


def write_outputs(source_name, channels):
    source_dir = OUTPUT_DIR / source_name
    write_m3u(source_dir / f"{source_name}.m3u", channels)
    with (source_dir / f"{source_name}.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "source": source_name,
                "updated": now_ict(),
                "total": len(channels),
                "channels": channels,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def collect_hoiquan3():
    source = "HoiQuan3"
    site_url = "https://sv2.hoiquan3.live/"
    api_url = "https://sv.hoiquantv.xyz/api/v1/external/fixtures/unfinished"
    headers = {
        "Accept": "application/json, */*",
        "Referer": site_url,
        "Origin": site_url.rstrip("/"),
    }
    log(f"[{source}] Fetch API")
    try:
        r = request_get(api_url, headers=headers, timeout=20)
        log(f"[{source}] HTTP {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []

    items = data if isinstance(data, list) else data.get("data") or data.get("fixtures") or []
    channels = []
    for item in items:
        league = clean_text((item.get("league") or {}).get("name")) or source
        home = item.get("homeTeam") or {}
        away = item.get("awayTeam") or {}
        home_name = clean_text(home.get("name")) or "Home"
        away_name = clean_text(away.get("name")) or "Away"
        logo = home.get("logoUrl") or away.get("logoUrl") or ""
        time_label = parse_iso_to_ict(item.get("startTime"))

        for wrapper in item.get("fixtureCommentators") or []:
            commentator = wrapper.get("commentator") or {}
            blv = clean_text(commentator.get("nickname") or commentator.get("name")) or "BLV"
            seen = set()
            for stream in commentator.get("streams") or []:
                stream_url = clean_text(stream.get("sourceUrl"))
                if not stream_url or stream_url in seen:
                    continue
                seen.add(stream_url)
                quality = clean_text(stream.get("name")) or "HD"
                name = f"[{time_label}] {home_name} - {away_name} [{league}] | BLV: {blv} [{quality.upper()}]"
                channels.append(
                    {
                        "source": source,
                        "name": name,
                        "group": league,
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": site_url,
                        "user_agent": UA,
                    }
                )
    log(f"[{source}] {len(channels)} links")
    return channels


def collect_standard_api(source, api_url, site_url="", group_name=None):
    headers = {"Accept": "application/json, */*"}
    if site_url:
        headers["Referer"] = site_url
        headers["Origin"] = site_url.rstrip("/")

    log(f"[{source}] Fetch standard API")
    data = fetch_json(api_url, headers=headers)
    items = data if isinstance(data, list) else data.get("data") or data.get("fixtures") or []
    channels = []

    for item in items:
        league = clean_text((item.get("league") or {}).get("name")) or group_name or source
        title = clean_text(item.get("title"))
        home = item.get("homeTeam") or {}
        away = item.get("awayTeam") or {}
        home_name = clean_text(home.get("name"))
        away_name = clean_text(away.get("name"))
        if not title:
            title = f"{home_name or 'Home'} - {away_name or 'Away'}"
        logo = home.get("logoUrl") or away.get("logoUrl") or ""
        time_label = parse_iso_to_ict(item.get("startTime"))

        for wrapper in item.get("fixtureCommentators") or []:
            commentator = wrapper.get("commentator") or {}
            blv = clean_text(commentator.get("nickname") or commentator.get("name")) or "BLV"
            streams = commentator.get("streams") or []
            for stream in streams:
                stream_url = clean_text(stream.get("sourceUrl"))
                if not is_valid_stream_url(stream_url):
                    continue
                quality = clean_text(stream.get("name")) or "HD"
                channels.append(
                    {
                        "source": source,
                        "name": f"[{time_label}] {title} [{league}] | BLV: {blv} [{quality.upper()}]",
                        "group": group_name or league,
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": site_url,
                        "user_agent": UA,
                    }
                )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def iter_grouped_stream_links(channel):
    for source in channel.get("sources") or []:
        blv_name = clean_text(source.get("name")) or "Main"
        for content in source.get("contents") or []:
            for stream in content.get("streams") or []:
                stream_name = clean_text(stream.get("name")) or blv_name
                for link in stream.get("stream_links") or []:
                    stream_url = clean_text(link.get("url"))
                    if stream_url:
                        yield stream_name, stream_url


def collect_grouped_json(source, api_url, group_name):
    log(f"[{source}] Fetch grouped JSON")
    data = fetch_json(api_url)
    channels = []

    groups = data.get("groups") if isinstance(data, dict) else []
    for group in groups or []:
        actual_group = clean_text(group.get("name")) or group_name
        for channel in group.get("channels") or []:
            logo = ((channel.get("image") or {}).get("url")) or ""
            title = clean_text(channel.get("name")) or group_name
            for blv_name, stream_url in iter_grouped_stream_links(channel):
                if not is_valid_stream_url(stream_url):
                    continue
                channels.append(
                    {
                        "source": source,
                        "name": f"{title} | {blv_name}",
                        "group": actual_group,
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": api_url,
                        "user_agent": UA,
                    }
                )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_vongcam():
    source = "VongCamTV"
    api_url = "https://sv.bugiotv.xyz/internal/api/matches"
    log(f"[{source}] Fetch API")
    data = fetch_json(api_url)
    channels = []

    for item in data.get("data") or []:
        commentator = item.get("commentator") or {}
        streams = [
            ("FHD", commentator.get("streamSourceFhd")),
            ("HD", commentator.get("streamSourceHd")),
            ("SD", commentator.get("streamSourceSd")),
        ]
        for quality, stream_url in streams:
            if not is_valid_stream_url(stream_url):
                continue
            channels.append(
                {
                    "source": source,
                    "name": f"{clean_text(item.get('title')) or source} | {quality}",
                    "group": source,
                    "logo": (item.get("homeClub") or {}).get("logoUrl", ""),
                    "stream_url": stream_url,
                    "referer": "https://bugiotv.xyz/",
                    "user_agent": UA,
                }
            )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_cola():
    source = "CoLaTV"
    api_url = "https://api.cltvlv.com/api/matches"
    log(f"[{source}] Fetch API")
    data = fetch_json(api_url)
    values = (data.get("data") or {}).values() if isinstance(data.get("data"), dict) else []
    channels = []

    for item in values:
        match_time = item.get("matchTime")
        try:
            dt = datetime.fromtimestamp(match_time).strftime("%H:%M")
        except Exception:
            dt = ""
        home = item.get("home_team") or {}
        away = item.get("away_team") or {}
        title = f"{dt} | {clean_text(home.get('name'))} vs {clean_text(away.get('name'))}".strip()
        for anchor in item.get("anchorAppointmentVoList") or []:
            blv = clean_text(anchor.get("anchorName")) or "BLV"
            for key in ("playStreamAddress2", "playStreamAddress1", "playStreamAddress3"):
                stream_url = clean_text(anchor.get(key))
                if not is_valid_stream_url(stream_url):
                    continue
                channels.append(
                    {
                        "source": source,
                        "name": f"{title} | {blv}",
                        "group": source,
                        "logo": home.get("logo", ""),
                        "stream_url": stream_url,
                        "referer": "https://cltvlv.com/",
                        "user_agent": UA,
                    }
                )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_tamquoc():
    source = "TamQuocTV"
    api_url = "https://sv.tamquoctv.xyz/internal/api/matches"
    log(f"[{source}] Fetch API")
    data = fetch_json(api_url)
    items = data.get("data") or []
    if isinstance(items, dict):
        items = list(items.values())
    channels = []

    for item in items:
        title = clean_text(item.get("title"))
        if not title:
            home = clean_text((item.get("homeClub") or {}).get("name"))
            away = clean_text((item.get("awayClub") or {}).get("name"))
            title = f"{home} vs {away}".strip()
        time_label = parse_iso_to_ict(item.get("startTime"))
        commentator = item.get("commentator") or {}
        blv = clean_text(commentator.get("nickname") or commentator.get("name")) or "BLV"
        streams = [
            ("FHD", commentator.get("streamSourceFhd")),
            ("HD", commentator.get("streamSourceHd")),
            ("SD", commentator.get("streamSourceSd")),
        ]
        for quality, stream_url in streams:
            if not is_valid_stream_url(stream_url):
                continue
            channels.append(
                {
                    "source": source,
                    "name": f"[{time_label}] {title} | {blv} [{quality}]",
                    "group": source,
                    "logo": (item.get("homeClub") or {}).get("logoUrl", ""),
                    "stream_url": stream_url,
                    "referer": "https://tamquoctv.xyz/",
                    "user_agent": UA,
                }
            )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def parse_extinf(line):
    title = line.split(",", 1)[1].strip() if "," in line else ""
    logo_match = re.search(r'tvg-logo="([^"]*)"', line)
    group_match = re.search(r'group-title="([^"]*)"', line)
    return {
        "title": clean_text(title),
        "logo": logo_match.group(1) if logo_match else "",
        "group": group_match.group(1) if group_match else "",
    }


def collect_m3u_playlist(source, playlist_url, group_name, referer=""):
    log(f"[{source}] Fetch M3U")
    try:
        r = request_get(playlist_url, timeout=20)
        log(f"[{source}] HTTP {r.status_code}")
        if r.status_code != 200:
            return []
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []

    channels = []
    current = {"title": group_name, "logo": "", "group": group_name}
    for raw_line in r.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            current = parse_extinf(line)
            continue
        if line.startswith("http") and is_valid_stream_url(line):
            channels.append(
                {
                    "source": source,
                    "name": current.get("title") or group_name,
                    "group": group_name or current.get("group") or source,
                    "logo": current.get("logo", ""),
                    "stream_url": line,
                    "referer": referer or playlist_url,
                    "user_agent": UA,
                }
            )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_chuoichien():
    source = "ChuoiChienTV"
    site_url = "https://live25.chuoichientv.com"
    site_ref = "https://live.chuoichientv.com"
    api_url = "https://api.chuoichientv.com/v1/matches?page=1&limit=100&sport=&type=blv"
    headers = {
        "Accept": "application/json, */*",
        "Origin": site_url,
        "Referer": site_ref + "/",
    }
    if CHUOICHIEN_TOKEN:
        headers["Authorization"] = f"Bearer {CHUOICHIEN_TOKEN}"

    log(f"[{source}] Fetch API")
    try:
        r = request_get(api_url, headers=headers, timeout=20)
        log(f"[{source}] HTTP {r.status_code}")
        if r.status_code == 401:
            log(f"[{source}] Need token: set CHUOICHIEN_TOKEN environment variable")
            return []
        if r.status_code != 200:
            return []
        matches = r.json().get("matches") or []
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []

    channels = []
    for match in matches:
        teams = match.get("teams") or {}
        home = teams.get("home") or {}
        away = teams.get("away") or {}
        home_name = clean_text(home.get("name")) or "Home"
        away_name = clean_text(away.get("name")) or "Away"
        logo = home.get("logo") or away.get("logo") or ""
        league = clean_text((match.get("tournament") or {}).get("name")) or source
        time_label = parse_iso_to_ict(match.get("matchTime"), "%Hh%M")

        for blv in match.get("blvs") or []:
            blv_name = clean_text(blv.get("name") or blv.get("nickname")) or "BLV"
            for stream in blv.get("streams") or []:
                stream_url = clean_text(stream.get("url"))
                if not stream_url:
                    continue
                quality = clean_text(stream.get("name") or stream.get("quality")) or "HD"
                channels.append(
                    {
                        "source": source,
                        "name": f"[{time_label}] {home_name} vs {away_name} | BLV: {blv_name} [{quality}]",
                        "group": league,
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": site_ref + "/",
                        "user_agent": UA,
                    }
                )
    log(f"[{source}] {len(channels)} links")
    return channels


class LinkCardParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.current_href = None
        self.current_text = []
        self.images = []
        self.texts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.current_href = attrs["href"]
            self.current_text = []
        if tag == "img":
            alt = clean_text(attrs.get("alt"))
            src = attrs.get("src") or ""
            if alt:
                self.images.append((alt, urljoin(self.base_url, src)))

    def handle_data(self, data):
        text = clean_text(data)
        if text:
            self.texts.append(text)
        if self.current_href is not None and text:
            self.current_text.append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_href is not None:
            href = self.current_href.strip()
            text = clean_text(" ".join(self.current_text))
            self.links.append((href, text))
            self.current_href = None
            self.current_text = []


STREAM_PATTERNS = [
    re.compile(r"(https?://[^\s'\"<>{}\\,\]]+?\.m3u8[^\s'\"<>{}\\,\]]*)"),
    re.compile(r'"(?:url|src|source|hls|stream|file|link)"\s*:\s*"(https?://[^"]+)"'),
    re.compile(r"(?:url|src|hls|file)\s*[=:]\s*['\"]?(https?://[^\s'\"]+?\.m3u8[^\s'\"]*)"),
    re.compile(r"<source[^>]+src=[\"']([^\"']+\.m3u8[^\"']*)[\"']", re.I),
]
TIME_RE = re.compile(r"(\d{1,2}:\d{2})\s*[\|\-]\s*(\d{1,2}/\d{1,2})")
MODE_RE = re.compile(r"[?&]mode=(\w+)")
MODE_LABEL = {
    "sd": "SD",
    "hd": "HD",
    "fullhd": "FullHD",
    "flv": "SD Nhanh",
    "flv2": "HD Nhanh",
    "ndsd": "Nha dai SD",
    "ndhd": "Nha dai HD",
}


def extract_stream_url(text):
    for pattern in STREAM_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        url = match.group(1).strip().strip("'\"")
        if any(bad in url.lower() for bad in ["facebook", "google", ".css", ".js", "jquery"]):
            continue
        return html.unescape(url)
    return ""


def fetch_text(url, headers=None, params=None, timeout=15):
    r = request_get(url, headers=headers, params=params, timeout=timeout)
    if r.status_code == 200:
        return r.text
    return ""


def collect_hoadaotv():
    source = "HoaDaoTV"
    site_url = "https://hoadaotv.info"
    headers = {
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Referer": site_url + "/",
        "Origin": site_url,
    }
    log(f"[{source}] Fetch home")
    try:
        home_html = fetch_text(site_url, headers=headers, timeout=15)
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []
    if not home_html:
        log(f"[{source}] Home not available")
        return []

    parser = LinkCardParser(site_url)
    parser.feed(home_html)

    image_logo = parser.images[0][1] if parser.images else ""
    time_match = TIME_RE.search(" ".join(parser.texts))
    time_label = f"[{time_match.group(2)} {time_match.group(1)}]" if time_match else ""
    matches = []
    seen_pages = set()
    for href, link_text in parser.links:
        if not href or href.startswith("javascript:"):
            continue
        low = href.lower()
        if any(skip in low for skip in ["bang-xep-hang", "ket-qua", "tin-tuc", "xemlai", "facebook", "telegram"]):
            continue
        if "vs" not in low and not re.search(r"-\d{6,}", low):
            continue
        page_url = urljoin(site_url + "/", href).split("?")[0]
        if page_url in seen_pages:
            continue
        seen_pages.add(page_url)
        slug = page_url.rstrip("/").split("/")[-1]
        title = clean_text(link_text)
        if not title or len(title) < 4:
            title = re.sub(r"-\d+$", "", slug).replace("-", " ").title()
        matches.append({"title": title, "url": page_url, "time_label": time_label, "logo": image_logo})

    log(f"[{source}] {len(matches)} match pages")
    channels = []
    for index, match in enumerate(matches, start=1):
        if index > 80:
            break
        try:
            detail = fetch_text(match["url"], headers=headers, timeout=12)
        except Exception:
            continue
        if not detail:
            continue
        modes = []
        for mode in MODE_RE.findall(detail):
            if mode not in modes and mode != "emulator":
                modes.append(mode)
        if not modes:
            modes = [""]
        seen_urls = set()
        for mode in modes:
            try:
                mode_html = detail if not mode else fetch_text(match["url"], headers=headers, params={"mode": mode}, timeout=12)
            except Exception:
                continue
            stream_url = extract_stream_url(mode_html)
            if not stream_url or stream_url in seen_urls:
                continue
            seen_urls.add(stream_url)
            label = MODE_LABEL.get(mode, mode.upper() if mode else "HD")
            prefix = f"{match['time_label']} " if match.get("time_label") else ""
            channels.append(
                {
                    "source": source,
                    "name": f"{prefix}{match['title']} [{label}]",
                    "group": source,
                    "logo": match.get("logo", ""),
                    "stream_url": stream_url,
                    "referer": site_url + "/",
                    "user_agent": UA,
                }
            )
            time.sleep(0.2)
    log(f"[{source}] {len(channels)} links")
    return channels


def collect_missing_source(name):
    log(f"[{name}] Skipped: file in Downloads contains only HTTP 429 text, not scraper code")
    return []


def main():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log("=" * 60)
    mode = "verify live links" if VERIFY_STREAMS else "raw m3u8 collection"
    log(f"Combined M3U collector - {now_ict()} - {mode}")
    log("=" * 60)

    collectors = [
        ("HoiQuan3", collect_hoiquan3),
        (
            "HoiQuan1",
            lambda: collect_standard_api(
                "HoiQuan1",
                "https://sv.hoiquantv.xyz/api/v1/external/fixtures/unfinished",
                "https://sv2.hoiquan3.live/",
                "Hoi Quan 1",
            ),
        ),
        (
            "HoiQuan2",
            lambda: collect_grouped_json(
                "HoiQuan2",
                "https://pub-26bab83910ab4b5781549d12d2f0ef6f.r2.dev/hoiquan1.json",
                "Hoi Quan 2",
            ),
        ),
        (
            "ThienDinh",
            lambda: collect_standard_api(
                "ThienDinh",
                "https://sv.thiendinhtv.xyz/api/v1/external/fixtures/unfinished",
                "",
                "Thien Dinh",
            ),
        ),
        (
            "XayCon",
            lambda: collect_standard_api(
                "XayCon",
                "https://sv.xaycontv.xyz/api/v1/external/fixtures/unfinished",
                "",
                "Xay Con",
            ),
        ),
        ("VongCamTV", collect_vongcam),
        ("CoLaTV", collect_cola),
        ("TamQuocTV", collect_tamquoc),
        (
            "LuongSonTV",
            lambda: collect_grouped_json("LuongSonTV", "https://apithethao1.vercel.app/luongsontv", "Luong Son TV"),
        ),
        (
            "QueChoaTV",
            lambda: collect_grouped_json("QueChoaTV", "https://apithethao1.vercel.app/quechoatv", "Que Choa TV"),
        ),
        (
            "FPTSport",
            lambda: collect_m3u_playlist(
                "FPTSport",
                "https://raw.githubusercontent.com/t23-02/bongda/refs/heads/main/bongda.m3u",
                "FPT Sport",
            ),
        ),
        (
            "GioVang",
            lambda: collect_grouped_json(
                "GioVang",
                "https://raw.githubusercontent.com/jasminliu98/giovang-stream/refs/heads/main/output.json",
                "Gio Vang",
            ),
        ),
        (
            "QueChoaRaw",
            lambda: collect_grouped_json(
                "QueChoaRaw",
                "https://raw.githubusercontent.com/huybuonvp/xem_football/refs/heads/main/All_CHANNEL.json",
                "Que Choa",
            ),
        ),
        (
            "TieuLamTV",
            lambda: collect_m3u_playlist(
                "TieuLamTV",
                "https://raw.githubusercontent.com/Bacbenny/testtieulam/refs/heads/main/output/iptv.m3u",
                "Tieu Lam TV",
            ),
        ),
        ("HoaDaoTV", collect_hoadaotv),
        ("ChuoiChienTV", collect_chuoichien),
        ("QueChoa8", lambda: collect_missing_source("QueChoa8")),
    ]

    all_channels = []
    per_source_counts = {}
    for source_name, collector in collectors:
        log("")
        try:
            channels = collector()
        except Exception as exc:
            log(f"[{source_name}] Fatal error: {exc}")
            channels = []
        unique = []
        seen = set()
        for channel in channels:
            key = channel_key(channel)
            if not key[0] or key in seen:
                continue
            seen.add(key)
            unique.append(channel)

        selected = verify_live_channels(unique)
        per_source_counts[source_name] = len(selected)
        if selected:
            write_outputs(source_name, selected)
            all_channels.extend(selected)

    deduped = []
    seen_urls = set()
    for channel in all_channels:
        url = channel.get("stream_url", "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(channel)

    write_m3u(ALL_M3U, deduped)
    with ALL_JSON.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "updated": now_ict(),
                "total": len(deduped),
                "per_source": per_source_counts,
                "channels": deduped,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    with STATS_TXT.open("w", encoding="utf-8") as f:
        f.write(f"updated={now_ict()}\n")
        f.write(f"total_unique={len(deduped)}\n")
        for source_name, count in per_source_counts.items():
            f.write(f"{source_name}={count}\n")

    log("")
    log(f"[DONE] Total unique links: {len(deduped)}")
    log(f"[DONE] M3U: {ALL_M3U}")
    log(f"[DONE] JSON: {ALL_JSON}")
    log(f"[DONE] Stats: {STATS_TXT}")


if __name__ == "__main__":
    main()

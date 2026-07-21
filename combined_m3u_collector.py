import html
import json
import os
import re
import sys
import time
import unicodedata
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.parse import unquote
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
ALL_M3U = BASE_DIR / "all.m3u"
TZ_VN = timezone(timedelta(hours=7))

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

CHUOICHIEN_TOKEN = os.environ.get("CHUOICHIEN_TOKEN", "").strip()
CHUOICHIEN_SITE_URL = os.environ.get("CHUOICHIEN_SITE_URL", "https://live25.chuoichientv.com")
CHUOICHIEN_SITE_REF = os.environ.get("CHUOICHIEN_SITE_REF", "https://live.chuoichientv.com")
CHUOICHIEN_API_URL = os.environ.get(
    "CHUOICHIEN_API_URL",
    "https://api.chuoichientv.com/v1/matches?page=1&limit=100&sport=&type=blv",
)
KHANDAIA_FRONTEND_URL = os.environ.get("KHANDAIA_FRONTEND", "https://tructiep.khandaia.link")
KHANDAIA_KNOWN_API_BASE = os.environ.get("KHANDAIA_API", "https://sv.khandai-a.xyz/api/v1/external")
COLATV_FRONTEND_URL = os.environ.get("COLATV_FRONTEND", "https://colatv48.live")
COLATV_API_URL = os.environ.get("COLATV_API", "https://api.cltvlv.com/api/matches")
LUONGSON_API_URL = os.environ.get("LUONGSON_API", "https://api-ls.cdnokvip.com/api/get-livestream-group")
LUONGSON_MATCH_URL = os.environ.get("LUONGSON_MATCH", "https://api-ls.cdnokvip.com/api/match-detail?matchId=%s")
NAUXOI_API_BASE = os.environ.get("NAUXOI_API", "https://apixx.connect9nx.com/api")
NAUXOI_SITE_URL = os.environ.get("NAUXOI_SITE", "https://nauxoi.fit/")
TIEULAMWC_API_BASE = os.environ.get("TIEULAMWC_API", "https://api.tlap17062026.com")
TIEULAMWC_REFERERS = [
    item.strip()
    for item in os.environ.get("TIEULAMWC_REFERERS", "https://sv2.tieulam2.xyz/,https://sv2.tieulamwc.com/").split(",")
    if item.strip()
]
GIOVANG_REFERER = os.environ.get("GIOVANG_REFERER", "https://giovang.store/")
HOIQUAN_API_BASE = os.environ.get("HOIQUAN_API_BASE", "https://sv.hoiquantv.xyz/api/v1/external")
HOIQUAN3_REFERER = os.environ.get("HOIQUAN3_REFERER", "https://sv2.hoiquan3.live/")
HOIQUAN1_REFERER = os.environ.get("HOIQUAN1_REFERER", "https://sv2.hoiquan1.live/")
HOIQUAN_REFERER = os.environ.get("HOIQUAN_REFERER", HOIQUAN3_REFERER)
XAYCON_REFERER = os.environ.get("XAYCON_REFERER", "https://sv2.xaycon3.live/")
BUGIO_REFERER = os.environ.get("BUGIO_REFERER", "https://sv1.bugio9.live/")
VONGCAM_API_URL = os.environ.get("VONGCAM_API", "https://sv.bugiotv.xyz/internal/api/matches")
VONGCAM_FRONTEND_URL = os.environ.get("VONGCAM_FRONTEND", BUGIO_REFERER)
QUECHOA_SITE_URL = os.environ.get("QUECHOA_SITE_URL", "https://quechoa11.live")
QUECHOA_HOME_URL = os.environ.get("QUECHOA_HOME_URL", "https://quechoa11.live/")
VSC9_URL = os.environ.get("VSC9_URL", "https://vsc9.top/")
VSC9_REFERER = os.environ.get("VSC9_REFERER", "https://vsc9.top/")
ALL_CHANNEL_M3U_URL = os.environ.get(
    "ALL_CHANNEL_M3U_URL",
    "https://raw.githubusercontent.com/huybuonvp/xem_football/refs/heads/main/All_CHANNEL.m3u",
)
VMTTV_M3U_URL = os.environ.get(
    "VMTTV_M3U_URL",
    "https://raw.githubusercontent.com/vuminhthanh12/vuminhthanh12/refs/heads/main/vmttv",
)
CUONGHEHE_M3U_URL = os.environ.get(
    "CUONGHEHE_M3U_URL",
    "https://raw.githubusercontent.com/cuongnh1989/iptv/refs/heads/main/cuonghehe",
)
COTIVI_SPORTS_M3U_URL = os.environ.get(
    "COTIVI_SPORTS_M3U_URL",
    "https://raw.githubusercontent.com/Bacbenny/freetvco/refs/heads/main/output/cotivi_sports.m3u",
)
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


API_DISCOVERY_CACHE = {}


def discover_frontend_url(frontend_url, timeout=8):
    frontend_url = clean_text(frontend_url).rstrip("/")
    if not frontend_url:
        return ""
    try:
        response = request_get(
            frontend_url,
            headers={"Accept": "text/html,application/xhtml+xml,*/*;q=0.9"},
            timeout=timeout,
        )
        if response.status_code == 200:
            return clean_text(getattr(response, "url", "") or frontend_url).rstrip("/")
    except Exception as exc:
        log(f"[DISCOVER] Frontend error {frontend_url}: {exc}")
    return ""


def iter_script_urls(html_text, base_url, limit=10):
    seen = set()
    for match in re.finditer(r"""<script[^>]+src=["']([^"']+\.js[^"']*)["']""", html_text or "", re.I):
        script_url = urljoin(base_url.rstrip("/") + "/", html.unescape(match.group(1)))
        if script_url in seen:
            continue
        seen.add(script_url)
        yield script_url
        if len(seen) >= limit:
            break


def discover_api_url(source, frontend_url, fallback_url, patterns, transform=None):
    cache_key = (source, frontend_url, fallback_url)
    if cache_key in API_DISCOVERY_CACHE:
        return API_DISCOVERY_CACHE[cache_key]

    final_frontend = discover_frontend_url(frontend_url)
    if not final_frontend:
        API_DISCOVERY_CACHE[cache_key] = fallback_url
        return fallback_url
    headers = {
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Referer": final_frontend.rstrip("/") + "/",
    }
    texts = []
    try:
        response = request_get(final_frontend or frontend_url, headers=headers, timeout=10)
        if response.status_code == 200:
            texts.append(response.text)
            for script_url in iter_script_urls(response.text, final_frontend or frontend_url):
                try:
                    js_response = request_get(script_url, headers=headers, timeout=12)
                    if js_response.status_code == 200:
                        texts.append(js_response.text)
                except Exception:
                    continue
    except Exception as exc:
        log(f"[{source}] API discovery skipped: {exc}")

    for text in texts:
        for pattern in patterns:
            for match in re.findall(pattern, text):
                candidate = match[0] if isinstance(match, tuple) else match
                candidate = html.unescape(clean_text(candidate).rstrip(".,;)'\"`"))
                if transform:
                    candidate = transform(candidate)
                if candidate:
                    log(f"[{source}] Discovered API: {candidate}")
                    API_DISCOVERY_CACHE[cache_key] = candidate
                    return candidate

    API_DISCOVERY_CACHE[cache_key] = fallback_url
    return fallback_url


def external_api_base_from_hit(hit):
    match = re.match(r"(https://sv\.[a-z0-9.-]+/api/v1/external)", hit)
    return match.group(1) if match else ""


def cola_api_from_hit(hit):
    match = re.match(r"(https://[a-z0-9.-]+)/api/", hit)
    return match.group(1).rstrip("/") + "/api/matches" if match else ""


def discover_external_api_base(source, frontend_url, fallback_base):
    return discover_api_url(
        source,
        frontend_url,
        fallback_base.rstrip("/"),
        (r"https://sv\.[a-z0-9.-]+/api/v1/external",),
        external_api_base_from_hit,
    )


def discover_internal_matches_api(source, frontend_url, fallback_url):
    return discover_api_url(
        source,
        frontend_url,
        fallback_url,
        (r"https?://[a-z0-9.-]+/internal/api/matches",),
    )


def discover_cola_api():
    return discover_api_url(
        "CoLaTV",
        COLATV_FRONTEND_URL,
        COLATV_API_URL,
        (r"https://[a-z0-9.-]+/api/match[^\"'`\s<)]*",),
        cola_api_from_hit,
    )


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


def is_valid_highlight_url(url):
    url = clean_text(url)
    if not url or not url.startswith(("http://", "https://")):
        return False
    lower = url.lower().split("?", 1)[0]
    return (".m3u8" in lower or lower.endswith(".mp4")) and ".mpd" not in lower


SPORT_SOURCES = {
    "HoiQuan1",
    "HoiQuan2",
    "HoiQuan3",
    "KhanDaiA",
    "ThienDinh",
    "XayCon",
    "VongCamTV",
    "CoLaTV",
    "TamQuocTV",
    "LuongSonTV",
    "QueChoaTV",
    "GioVang",
    "QueChoaRaw",
    "TieuLamTV",
    "HoaDaoTV",
    "ChuoiChienTV",
    "QueChoa8",
    "S8TV",
    "TieuLamWC",
}

SPORT_KEYWORDS = [
    ("Bong Chuyen", ("bong chuyen", "volleyball", "v-league volleyball")),
    ("Bong Ro", ("bong ro", "basketball", "wnba", "nba", "fiba", "trail blazers", "mystics", "sparks")),
    ("Tennis", ("tennis", "atp", "wta")),
    ("Cau Long", ("cau long", "badminton", "bwf")),
    ("Futsal", ("futsal",)),
]


def text_key(value):
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.replace("đ", "d")
    return "".join(ch for ch in value if ch.isalnum() or ch.isspace()).strip()


def detect_sport(*parts):
    haystack = text_key(" ".join(clean_text(part) for part in parts if part))
    for sport, keywords in SPORT_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return sport
    return "Bong Da"


def extract_match_title(channel):
    title = clean_text(channel.get("match_title") or channel.get("name") or "")
    if not title:
        return ""
    parts = [part.strip() for part in title.split("|") if part.strip()]
    if len(parts) >= 2 and re.fullmatch(r"\d{1,2}:\d{2}", parts[0]):
        title = parts[1]
    else:
        title = parts[0] if parts else title
    title = re.sub(r"^\[[^\]]+\]\s*", "", title).strip()
    title = re.sub(r"\s*\[[^\]]+\]\s*$", "", title).strip()
    title = re.sub(r"\s+", " ", title)
    return title[:120]


def output_group(channel):
    group = clean_text(channel.get("group"))
    return clean_text(group or channel.get("source") or "Unknown")


def is_working_m3u8(url, referer="", user_agent=UA):
    if not is_valid_stream_url(url) and not is_valid_highlight_url(url):
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


def first_working_referer(url, referers):
    for referer in referers:
        if is_working_m3u8(url, referer=referer, user_agent=UA):
            return referer
    return referers[0] if referers else ""


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
            raw_extinf = clean_text(ch.get("raw_extinf")) if ch.get("preserve_extinf") else ""
            if raw_extinf:
                f.write(f"{raw_extinf}\n")
                for option_line in ch.get("raw_options") or []:
                    option_line = clean_text(option_line)
                    if option_line:
                        f.write(f"{option_line}\n")
            else:
                attrs = [
                    f'tvg-logo="{ch.get("logo", "")}"',
                    f'group-title="{output_group(ch)}"',
                ]
                f.write(f'#EXTINF:-1 {" ".join(attrs)},{ch.get("name", "Unknown")}\n')
            referer = clean_text(ch.get("referer"))
            user_agent = clean_text(ch.get("user_agent"))
            if referer:
                f.write(f"#EXTVLCOPT:http-referrer={referer}\n")
            if user_agent:
                f.write(f"#EXTVLCOPT:http-user-agent={user_agent}\n")
            f.write(f'{ch.get("stream_url", "")}\n\n')


def collect_hoiquan3():
    source = "HoiQuan3"
    site_url = HOIQUAN3_REFERER
    api_base = discover_external_api_base(source, site_url, HOIQUAN_API_BASE)
    api_url = f"{api_base.rstrip('/')}/fixtures/unfinished"
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
                        "group": "Hoi Quan",
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": site_url,
                        "user_agent": UA,
                    }
                )
    log(f"[{source}] {len(channels)} links")
    return channels


def collect_hoiquan1():
    api_base = discover_external_api_base("HoiQuan1", HOIQUAN1_REFERER, HOIQUAN_API_BASE)
    return collect_standard_api(
        "HoiQuan1",
        f"{api_base.rstrip('/')}/fixtures/unfinished",
        HOIQUAN1_REFERER,
        "Hoi Quan",
    )


def collect_khandaia():
    api_base = discover_external_api_base("KhanDaiA", KHANDAIA_FRONTEND_URL, KHANDAIA_KNOWN_API_BASE)
    return collect_standard_api(
        "KhanDaiA",
        f"{api_base.rstrip('/')}/fixtures/unfinished",
        KHANDAIA_FRONTEND_URL,
        "Khan Dai A",
    )


def collect_luongson():
    source = "LuongSonTV"
    log(f"[{source}] Fetch API")
    data = fetch_json(LUONGSON_API_URL, headers={"Accept": "application/json, */*"}, timeout=25)
    items = ((data.get("value") or {}).get("datas") or []) if isinstance(data, dict) else []
    channels = []

    for item in items:
        match_id = item.get("matchId")
        if not match_id:
            continue

        detail_url = LUONGSON_MATCH_URL % match_id
        try:
            response = request_get(detail_url, headers={"Accept": "application/json, */*"}, timeout=20)
            if response.status_code == 405 and requests is not None:
                response = requests.post(detail_url, headers={"User-Agent": UA, "Accept": "application/json, */*"}, timeout=20)
            if response.status_code != 200:
                continue
            detail = response.json()
        except Exception:
            continue

        match = ((detail.get("value") or {}).get("datas") or {}) if isinstance(detail, dict) else {}
        stream_urls = [
            ("FHD", match.get("linkLive")),
            ("HD", match.get("linkLiveFlv")),
            ("CDN", match.get("cdnUrl")),
        ]
        title = clean_text(
            f"{match.get('homeName') or item.get('homeName') or ''} vs {match.get('awayName') or item.get('awayName') or ''}"
        ).strip(" vs")
        if not title:
            title = source
        commentator = clean_text(match.get("commentator") or item.get("commentator")) or "BLV"
        logo = match.get("homeLogo") or item.get("homeLogo") or match.get("awayLogo") or item.get("awayLogo") or ""
        league = clean_text(match.get("leagueName") or item.get("leagueName")) or source

        for quality, stream_url in stream_urls:
            if not is_valid_stream_url(stream_url):
                continue
            channels.append(
                {
                    "source": source,
                    "name": f"{title} [{league}] | {commentator} [{quality}]",
                    "group": "Luong Son TV",
                    "logo": logo,
                    "stream_url": stream_url,
                    "referer": "https://luongsontv60.com/",
                    "user_agent": UA,
                }
            )

    log(f"[{source}] {len(channels)} raw links")
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


def collect_grouped_json(source, api_url, group_name, referer=None):
    log(f"[{source}] Fetch grouped JSON")
    headers = {"Accept": "application/json, */*"}
    if referer:
        headers["Referer"] = referer
        headers["Origin"] = referer.rstrip("/")
    data = fetch_json(api_url, headers=headers)
    channels = []

    groups = data.get("groups") if isinstance(data, dict) else []
    for group in groups or []:
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
                        "group": group_name,
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": referer or api_url,
                        "user_agent": UA,
                    }
                )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_vongcam():
    source = "VongCamTV"
    api_url = discover_internal_matches_api(source, VONGCAM_FRONTEND_URL, VONGCAM_API_URL)
    log(f"[{source}] Fetch API")
    data = fetch_json(
        api_url,
        headers={
            "Accept": "application/json, */*",
            "Referer": BUGIO_REFERER,
            "Origin": BUGIO_REFERER.rstrip("/"),
        },
    )
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
                    "referer": BUGIO_REFERER,
                    "user_agent": UA,
                }
            )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_cola():
    source = "CoLaTV"
    api_url = discover_cola_api()
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


def is_supported_playlist_url(url, allow_non_m3u8=False):
    url = clean_text(url)
    if not url or not url.startswith(("http://", "https://")):
        return False
    lower = url.lower().split("?", 1)[0]
    if lower.endswith(".mpd") or ".mpd/" in lower:
        return False
    if url.startswith(("udp://", "rtp://")):
        return False
    return allow_non_m3u8 or ".m3u8" in lower


def group_key(value):
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.replace("Ä‘", "d").replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", "", value)


def group_matches_any(group, allowed_groups):
    if not allowed_groups:
        return True
    key = group_key(group)
    for allowed_group in allowed_groups:
        target = group_key(allowed_group)
        if not target:
            continue
        if target == "vtv":
            if key == "vtv":
                return True
            continue
        if target in key:
            return True
    return False


def collect_m3u_playlist(
    source,
    playlist_url,
    group_name,
    referer="",
    preserve_group=False,
    allow_non_m3u8=False,
    timeout=30,
    retries=2,
    allowed_groups=None,
    default_referer_to_playlist=True,
    user_agent=UA,
    preserve_extinf=False,
):
    log(f"[{source}] Fetch M3U")
    r = None
    for attempt in range(1, retries + 1):
        try:
            r = request_get(playlist_url, timeout=timeout)
            log(f"[{source}] HTTP {r.status_code}")
            if r.status_code == 200:
                break
            return []
        except Exception as exc:
            log(f"[{source}] Attempt {attempt}/{retries} error: {exc}")
            if attempt == retries:
                return []
            time.sleep(2)

    channels = []
    current = {"title": group_name, "logo": "", "group": group_name, "raw_options": []}
    for raw_line in r.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            current = parse_extinf(line)
            current["raw_extinf"] = line
            current["raw_options"] = []
            continue
        if line.startswith(("#EXTVLCOPT", "#KODIPROP", "#EXTHTTP")):
            current.setdefault("raw_options", []).append(line)
            continue
        if line.startswith("http") and is_supported_playlist_url(line, allow_non_m3u8=allow_non_m3u8):
            group = current.get("group") if preserve_group else group_name
            if not group_matches_any(group, allowed_groups):
                continue
            channels.append(
                {
                    "source": source,
                    "name": current.get("title") or group_name,
                    "group": group or group_name or source,
                    "logo": current.get("logo", ""),
                    "stream_url": line,
                    "referer": referer or (playlist_url if default_referer_to_playlist else ""),
                    "user_agent": user_agent,
                    "raw_extinf": current.get("raw_extinf", ""),
                    "raw_options": list(current.get("raw_options") or []),
                    "preserve_extinf": preserve_extinf,
                }
            )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_chuoichien():
    source = "ChuoiChienTV"
    site_url = CHUOICHIEN_SITE_URL
    site_ref = CHUOICHIEN_SITE_REF
    api_url = CHUOICHIEN_API_URL
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


def collect_cuonghehe():
    source = "CuongHeHe"
    channels = collect_m3u_playlist(
        source,
        CUONGHEHE_M3U_URL,
        "CuongHeHe",
        referer="",
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        default_referer_to_playlist=False,
        user_agent="",
        preserve_extinf=True,
    )
    selected = []
    sport_group_key = "thethaoquocte"
    for channel in channels:
        name = clean_text(channel.get("name"))
        group = clean_text(channel.get("group"))
        if "4k" in name.lower() or group_key(group) == sport_group_key:
            selected.append(channel)
    log(f"[{source}] {len(selected)} selected links")
    return selected


def collect_vmttv():
    source = "VMTTV"
    channels = collect_m3u_playlist(
        source,
        VMTTV_M3U_URL,
        "VMTTV",
        referer="https://github.com/vuminhthanh12/vuminhthanh12",
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        allowed_groups=("VTV", "the thao quoc te"),
    )
    sport_group_key = "thethaoquocte"
    for channel in channels:
        if group_key(channel.get("group")) == sport_group_key:
            channel["group"] = "THỂ THAO QUỐC TẾ"
    return channels


def collect_cotivi_sports():
    return collect_m3u_playlist(
        "CoTiViSports",
        COTIVI_SPORTS_M3U_URL,
        "CoTiVi Sports",
        referer="",
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        default_referer_to_playlist=False,
        user_agent="",
        preserve_extinf=True,
    )


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

S8TV_TITLE_URL_RE = re.compile(
    r'\\"title\\":\\"((?:\\\\.|[^\\"])*)\\"(?:(?!\\"title\\":).){0,4000}?'
    r'\\"(?:link_m3u8|videoUrl)\\":\\"((?:\\\\.|[^\\"])*)\\"',
    re.S,
)
S8TV_PLACEHOLDER_RE = re.compile(r'\\"link_video_placeholder\\":\\"((?:\\\\.|[^\\"])*)\\"')
S8TV_M3U8_RE = re.compile(r"https?://[^\s'\"<>\\]+?\.m3u8[^\s'\"<>\\]*")
VSC9_M3U8_RE = re.compile(r"https?://[^\s'\"<>\\]+?\.m3u8[^\s'\"<>\\]*")
VSC9_TIME_RE = re.compile(r"(\d{1,2}:\d{2}\s+\d{1,2}/\d{1,2})")


def decode_json_string(value):
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value.replace("\\/", "/").replace('\\"', '"')


def title_from_stream_url(url, prefix):
    path = unquote(url.split("?", 1)[0]).strip("/")
    parts = [part for part in path.split("/") if part and part.lower() != "master.m3u8"]
    label = parts[-1] if parts else prefix
    label = label.replace("+", " ").replace("_", " ").replace("-", " ")
    label = re.sub(r"\s+", " ", label).strip()
    return f"{prefix} {label}".strip()


def fetch_vsc9_html():
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Referer": VSC9_REFERER,
    }
    for verify in (True, False):
        try:
            if requests is not None:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    response = requests.get(VSC9_URL, headers=headers, timeout=30, verify=verify)
            else:
                response = request_get(VSC9_URL, headers=headers, timeout=30)
            if response.status_code == 200 and response.text:
                return response.text
        except Exception:
            continue
    return ""


def vsc9_title_from_context(html_text, url):
    pos = html_text.find(url)
    raw_context = html_text[max(0, pos - 2500):pos] if pos >= 0 else ""
    after_context = html_text[pos:pos + 700] if pos >= 0 else ""

    def last_json_value(pattern):
        matches = re.findall(pattern, raw_context)
        if not matches:
            return ""
        return clean_text(decode_json_string(matches[-1]))

    date_value = last_json_value(r'\\"date\\":\\"([^"]+)\\"')
    time_value = last_json_value(r'\\"time\\":\\"([^"]+)\\"')
    home_name = last_json_value(r'\\"home\\":\{(?:(?!\\"away\\").)*?\\"name\\":\\"([^"]+)\\"')
    away_name = last_json_value(r'\\"away\\":\{(?:(?!\\"lives\\").)*?\\"name\\":\\"([^"]+)\\"')
    commentator_after = re.search(r'\\"commentator\\":\\"([^"]+)\\"', after_context)
    commentator = clean_text(decode_json_string(commentator_after.group(1))) if commentator_after else ""
    if not commentator:
        commentator = last_json_value(r'\\"commentator\\":\\"([^"]+)\\"')

    day_label = ""
    date_match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_value)
    if date_match:
        day_label = f"{date_match.group(3)}/{date_match.group(2)}"
    time_label = clean_text(f"{time_value} {day_label}").strip()

    if home_name and away_name:
        title = clean_text(f"{time_label} ⚽ {home_name} vs {away_name}").strip()
        if commentator:
            title = f"{title} ({commentator})"
    else:
        context = decode_json_string(raw_context.replace("\\u0026", "&"))
        context = html.unescape(context)
        context = re.sub(r"<[^>]+>", " ", context)
        context = re.sub(r"\\[nrt]", " ", context)
        context = re.sub(r"\s+", " ", context).strip()
        time_match = VSC9_TIME_RE.search(context)
        time_label = time_match.group(1) if time_match else time_label
        title = title_from_stream_url(url, "VSC9")

    title = clean_text(title).strip(" ,")
    return title, time_label


def playlist_is_usable(url, referer):
    headers = {
        "User-Agent": UA,
        "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,*/*",
    }
    if referer:
        headers["Referer"] = referer
        headers["Origin"] = referer.rstrip("/")
    try:
        response = request_get(url, headers=headers, timeout=15)
        return response.status_code == 200 and response.text.lstrip().startswith("#EXTM3U")
    except Exception:
        return False


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


def collect_s8tv():
    source = "S8TV"
    site_url = "https://s8tv002.com/"
    headers = {
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Referer": site_url,
    }
    log(f"[{source}] Fetch home")
    try:
        html_text = fetch_text(site_url, headers=headers, timeout=25)
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []
    if not html_text:
        log(f"[{source}] Home not available")
        return []

    channels = []
    seen_urls = set()
    placeholder_urls = {
        clean_text(decode_json_string(match.group(1)))
        for match in S8TV_PLACEHOLDER_RE.finditer(html_text)
    }

    for match in S8TV_TITLE_URL_RE.finditer(html_text):
        title = clean_text(decode_json_string(match.group(1)))
        stream_url = clean_text(decode_json_string(match.group(2)))
        if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)
        title = re.sub(r"\s+-\s+Xem lại.*$", "", title, flags=re.I).strip() or source
        channels.append(
            {
                "source": source,
                "name": title,
                "group": "Highlight | S8TV",
                "logo": "",
                "stream_url": stream_url,
                "referer": site_url,
                "user_agent": UA,
            }
        )

    for stream_url in S8TV_M3U8_RE.findall(html_text):
        stream_url = clean_text(decode_json_string(stream_url))
        if not is_valid_stream_url(stream_url) or stream_url in seen_urls or stream_url in placeholder_urls:
            continue
        if "live-bong.s3" not in stream_url.lower():
            continue
        seen_urls.add(stream_url)
        channels.append(
            {
                "source": source,
                "name": title_from_stream_url(stream_url, source),
                "group": "Highlight | S8TV",
                "logo": "",
                "stream_url": stream_url,
                "referer": site_url,
                "user_agent": UA,
            }
        )

    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_vsc9():
    source = "VSC9"
    log(f"[{source}] Fetch home")
    html_text = fetch_vsc9_html()
    if not html_text:
        log(f"[{source}] Home not available")
        return []

    channels = []
    seen_urls = set()
    for raw_url in VSC9_M3U8_RE.findall(html_text):
        stream_url = clean_text(decode_json_string(raw_url))
        if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)
        if not playlist_is_usable(stream_url, VSC9_REFERER):
            continue
        title, time_label = vsc9_title_from_context(html_text, raw_url)
        group = "Vua San Co TV"
        if time_label:
            group = f"{group} | {time_label}"
        channels.append(
            {
                "source": source,
                "name": title or title_from_stream_url(stream_url, source),
                "group": group,
                "logo": "https://vsc9.top/favicon.ico",
                "stream_url": stream_url,
                "referer": VSC9_REFERER,
                "user_agent": UA,
            }
        )

    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_nauxoi_highlights():
    source = "NauXoiHighlight"
    api_url = f"{NAUXOI_API_BASE.rstrip('/')}/highlights"
    headers = {
        "Accept": "application/json, */*",
        "Origin": NAUXOI_SITE_URL.rstrip("/"),
        "Referer": NAUXOI_SITE_URL,
    }
    log(f"[{source}] Fetch highlights")
    data = fetch_json(api_url, headers=headers, timeout=25)
    content = ((data.get("data") or {}).get("content") or []) if isinstance(data, dict) else []
    channels = []
    seen_urls = set()

    for item in content:
        stream_url = clean_text(item.get("videoUrl"))
        if not is_valid_highlight_url(stream_url) or stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)
        home = item.get("homeTeam") or {}
        away = item.get("awayTeam") or {}
        title = clean_text(item.get("title"))
        if not title:
            title = clean_text(f"{home.get('name') or ''} vs {away.get('name') or ''}").strip(" vs") or source
        logo = clean_text(item.get("thumbnail"))
        if logo.startswith("/"):
            logo_base = NAUXOI_API_BASE.rstrip("/")
            if logo_base.endswith("/api"):
                logo_base = logo_base[:-4]
            logo = urljoin(logo_base + "/", logo.lstrip("/"))
        channels.append(
            {
                "source": source,
                "name": title,
                "group": "Highlight | Nau Xoi",
                "logo": logo,
                "stream_url": stream_url,
                "referer": NAUXOI_SITE_URL,
                "user_agent": UA,
            }
        )

    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_tieulamwc():
    source = "TieuLamWC"
    api_base = TIEULAMWC_API_BASE.rstrip("/")
    api_referer = TIEULAMWC_REFERERS[0] if TIEULAMWC_REFERERS else "https://sv2.tieulam2.xyz/"
    headers = {
        "Accept": "application/json, */*",
        "Referer": api_referer,
        "Origin": api_referer.rstrip("/"),
    }
    log(f"[{source}] Fetch matches")
    try:
        response = request_get(f"{api_base}/matches/graph", headers=headers, timeout=25)
        if response.status_code == 405 and requests is not None:
            response = requests.post(
                f"{api_base}/matches/graph",
                headers={"User-Agent": UA, **headers},
                json={},
                timeout=25,
            )
        log(f"[{source}] HTTP {response.status_code}")
        if response.status_code != 200:
            return []
        data = response.json()
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []

    items = data.get("data") if isinstance(data, dict) else []
    channels = []
    for item in items or []:
        match_id = item.get("id")
        if not match_id or not (item.get("is_live") or item.get("source_live")):
            continue
        try:
            live = fetch_json(f"{api_base}/match/{match_id}/live", headers=headers, timeout=20)
        except Exception:
            continue
        title = clean_text(item.get("title"))
        if not title:
            title = clean_text(f"{item.get('team_1') or ''} vs {item.get('team_2') or ''}").strip(" vs") or source
        league = clean_text(item.get("league"))
        sport = detect_sport(item.get("desc"), league, title)
        logo = clean_text(item.get("team_1_logo") or item.get("team_2_logo"))
        blv = clean_text(item.get("blv")) or "BLV"
        stream_candidates = [
            ("HD1", live.get("hd_1")),
            ("HD2", live.get("hd_2")),
            ("HD3", live.get("hd_3")),
            ("SRC", live.get("source")),
        ]
        seen_urls = set()
        referer_cache = {}
        for quality, stream_url in stream_candidates:
            stream_url = clean_text(stream_url)
            if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
                continue
            seen_urls.add(stream_url)
            referer = referer_cache.get(stream_url)
            if referer is None:
                referer = first_working_referer(stream_url, TIEULAMWC_REFERERS)
                referer_cache[stream_url] = referer
            channels.append(
                {
                    "source": source,
                    "name": f"{title} [{league}] | {blv} [{quality}]",
                    "group": source,
                    "sport": sport,
                    "logo": logo,
                    "stream_url": stream_url,
                    "referer": referer,
                    "user_agent": UA,
                }
            )

    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_missing_source(name):
    log(f"[{name}] Skipped: file in Downloads contains only HTTP 429 text, not scraper code")
    return []


def main():
    log("=" * 60)
    mode = "verify live links" if VERIFY_STREAMS else "raw m3u8 collection"
    log(f"Combined M3U collector - {now_ict()} - {mode}")
    log("=" * 60)

    collectors = [
        ("HoiQuan3", collect_hoiquan3),
        ("HoiQuan1", collect_hoiquan1),
        (
            "HoiQuan2",
            lambda: collect_grouped_json(
                "HoiQuan2",
                "https://pub-26bab83910ab4b5781549d12d2f0ef6f.r2.dev/hoiquan1.json",
                "Hoi Quan",
                HOIQUAN1_REFERER,
            ),
        ),
        ("KhanDaiA", collect_khandaia),
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
                XAYCON_REFERER,
                "Xay Con",
            ),
        ),
        ("VongCamTV", collect_vongcam),
        ("CoLaTV", collect_cola),
        ("TamQuocTV", collect_tamquoc),
        ("LuongSonTV", collect_luongson),
        ("TieuLamWC", collect_tieulamwc),
        (
            "QueChoaTV",
            lambda: collect_grouped_json(
                "QueChoaTV",
                "https://apithethao1.vercel.app/quechoatv",
                "Que Choa TV",
                QUECHOA_HOME_URL,
            ),
        ),
        (
            "TinhLaGi",
            lambda: collect_m3u_playlist(
                "TinhLaGi",
                "https://tinhlagi.pro/s.m3u",
                "Tinh La Gi",
                allow_non_m3u8=True,
                timeout=60,
                retries=3,
                default_referer_to_playlist=False,
                user_agent="",
                preserve_extinf=True,
            ),
        ),
        (
            "GioVang",
            lambda: collect_grouped_json(
                "GioVang",
                "https://raw.githubusercontent.com/jasminliu98/giovang-stream/refs/heads/main/output.json",
                "Gio Vang",
                GIOVANG_REFERER,
            ),
        ),
        (
            "AllChannelM3U",
            lambda: collect_m3u_playlist(
                "AllChannelM3U",
                ALL_CHANNEL_M3U_URL,
                "All Channel",
                referer="",
                preserve_group=True,
                allow_non_m3u8=True,
                timeout=60,
                retries=3,
                default_referer_to_playlist=False,
                user_agent="",
                preserve_extinf=True,
            ),
        ),
        ("VMTTV", collect_vmttv),
        ("CuongHeHe", collect_cuonghehe),
        ("CoTiViSports", collect_cotivi_sports),
        (
            "TieuLamTV",
            lambda: collect_m3u_playlist(
                "TieuLamTV",
                "https://raw.githubusercontent.com/Bacbenny/testtieulam/refs/heads/main/output/iptv.m3u",
                "Tieu Lam TV",
                referer=TIEULAMWC_REFERERS[0] if TIEULAMWC_REFERERS else "https://sv2.tieulam2.xyz/",
            ),
        ),
        ("HoaDaoTV", collect_hoadaotv),
        ("ChuoiChienTV", collect_chuoichien),
        ("S8TV", collect_s8tv),
        ("VSC9", collect_vsc9),
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
            all_channels.extend(selected)

    deduped = []
    seen_urls = set()
    for channel in all_channels:
        url = channel.get("stream_url", "").strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        deduped.append(channel)

    deduped.sort(key=lambda channel: (output_group(channel), clean_text(channel.get("name")), channel.get("stream_url", "")))
    write_m3u(ALL_M3U, deduped)

    log("")
    log(f"[DONE] Total unique links: {len(deduped)}")
    for source_name, count in per_source_counts.items():
        log(f"[DONE] {source_name}: {count}")
    log(f"[DONE] M3U: {ALL_M3U}")


if __name__ == "__main__":
    main()

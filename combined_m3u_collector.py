import html
import base64
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
from urllib.parse import parse_qs
from urllib.parse import urljoin
from urllib.parse import urlparse
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
OTT_M3U = BASE_DIR / "ott.m3u"
TINHLAGI_M3U = BASE_DIR / "tinhlagi.m3u"
THETHAOCOBAN_M3U = BASE_DIR / "thethaocoban.m3u"
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
BONG_LAU_SITE_URL = os.environ.get("BONG_LAU_SITE_URL", "https://lau03.bonglautv1.org")
BONG_LAU_REFERER = os.environ.get("BONG_LAU_REFERER", "https://lau03.bonglautv1.org/")
BONG_LAU_API_URL = os.environ.get(
    "BONG_LAU_API_URL",
    "https://api-v2.chuoichientv.net/v2/matches?page=1&limit=100&sport=&type=blv",
)
KHANDAIA_FRONTEND_URL = os.environ.get("KHANDAIA_FRONTEND", "https://tructiep.khandaia.link")
KHANDAIA_KNOWN_API_BASE = os.environ.get("KHANDAIA_API", "https://sv.khandai-a.xyz/api/v1/external")
COLATV_FRONTEND_URL = os.environ.get("COLATV_FRONTEND", "https://colatv48.live")
COLATV_API_URL = os.environ.get("COLATV_API", "https://api.cltvlv.com/api/matches")
BIAOM_SITE_URL = os.environ.get("BIAOM_SITE_URL", "https://biaomtv12.com/")
LUONGSON_API_URL = os.environ.get("LUONGSON_API", "https://api-ls.cdnokvip.com/api/get-livestream-group")
LUONGSON_MATCH_URL = os.environ.get("LUONGSON_MATCH", "https://api-ls.cdnokvip.com/api/match-detail?matchId=%s")
SOCOLIVE_API_URL = os.environ.get("SOCOLIVE_API_URL", "https://json.vnres.co/matches.json?v=%d")
SOCOLIVE_LIVE_ROOMS_URL = os.environ.get("SOCOLIVE_LIVE_ROOMS_URL", "https://json.vnres.co/all_live_rooms.json?v=%d")
SOCOLIVE_MATCH_URL = os.environ.get("SOCOLIVE_MATCH_URL", "https://json.vnres.co/room/%s/detail.json?v=%d")
SOCOLIVE_REFERER = os.environ.get("SOCOLIVE_REFERER", "https://socoliveaus.co/")
SOCOLIVE_LIMIT = int(os.environ.get("SOCOLIVE_LIMIT", "30"))
SOCOLIVE_LIVE_ROOM_LIMIT = int(os.environ.get("SOCOLIVE_LIVE_ROOM_LIMIT", "80"))
NAUXOI_API_BASE = os.environ.get("NAUXOI_API", "https://apixx.connect9nx.com/api")
NAUXOI_SITE_URL = os.environ.get("NAUXOI_SITE", "https://nauxoi.fit/")
TIEULAMWC_API_BASE = os.environ.get("TIEULAMWC_API", "https://api.tlap17062026.com")
TIEULAMWC_REFERERS = [
    item.strip()
    for item in os.environ.get("TIEULAMWC_REFERERS", "https://sv2.tieulam2.xyz/,https://sv2.tieulamwc.com/").split(",")
    if item.strip()
]
GIOVANG_REFERER = os.environ.get("GIOVANG_REFERER", "https://giovang.city/")
GIOVANG_API_LIVE = os.environ.get(
    "GIOVANG_API_LIVE",
    "https://live-api.keonhacaitp.one/storage/livestream/live.json",
)
GIOVANG_API_ALL = os.environ.get(
    "GIOVANG_API_ALL",
    "https://live-api.keonhacaitp.one/storage/livestream/all.json",
)
GIOVANG_API_FIXTURES = os.environ.get("GIOVANG_API_FIXTURES", "https://live-api.keonhacaitp.one/api/fixtures/")
GIOVANG_OLD_API_LIVE = "https://live-api.keovip88.net/storage/livestream/live.json"
GIOVANG_OLD_API_ALL = "https://live-api.keovip88.net/storage/livestream/all.json"
GIOVANG_OLD_API_FIXTURES = "https://live-api.keovip88.net/api/fixtures/"
GIOVANG_LIMIT = int(os.environ.get("GIOVANG_LIMIT", "1000"))
GIOVANG_FALLBACK_JSON_URL = os.environ.get(
    "GIOVANG_FALLBACK_JSON_URL",
    "https://raw.githubusercontent.com/jasminliu98/giovang-stream/refs/heads/main/output.json",
)
PHAOHOA_API_BASE = (os.environ.get("PHAOHOA_API") or "https://phaohoa1.live").rstrip("/")
PHAOHOA_FRONTEND_URL = (os.environ.get("PHAOHOA_FRONTEND") or "https://phaohoa.live").rstrip("/")
CHOANG_ENTRY_SITE_URL = os.environ.get("CHOANG_ENTRY_SITE_URL", "https://choangtv.com/")
CHOANG_DEFAULT_DOMAIN = os.environ.get("CHOANG_DEFAULT_DOMAIN", "choangtv21.com")
CHOANG_SITE_URL = os.environ.get("CHOANG_SITE_URL", f"https://{CHOANG_DEFAULT_DOMAIN}")
CHOANG_API_URL = os.environ.get("CHOANG_API_URL", f"https://api.{CHOANG_DEFAULT_DOMAIN}/matchSchedule/getList")
CHOANG_DETAIL_URL = os.environ.get("CHOANG_DETAIL_URL", f"https://api.{CHOANG_DEFAULT_DOMAIN}/matchSchedule/getDetail")
CHOANG_CDN_BASE = os.environ.get("CHOANG_CDN_BASE", "https://cdn.sports-cas889abxfileposo.site/live")
CHOANG_DAYS = int(os.environ.get("CHOANG_DAYS", "2"))
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
S8TV_SITE_URL = os.environ.get("S8TV_SITE_URL", "https://s8tv001.com/")
ALL_CHANNEL_M3U_URL = os.environ.get(
    "ALL_CHANNEL_M3U_URL",
    "https://raw.githubusercontent.com/huybuonvp/xem_football/refs/heads/main/All_CHANNEL.m3u",
)
VMTTV_M3U_URL = os.environ.get(
    "VMTTV_M3U_URL",
    "https://raw.githubusercontent.com/vuminhthanh12/vuminhthanh12/refs/heads/main/vmttv",
)
MYTV_FPT_EVENTS_M3U_URL = os.environ.get(
    "MYTV_FPT_EVENTS_M3U_URL",
    "https://raw.githubusercontent.com/thaichieucm92/MyTV/9c3081488d0dccb26381819d0d1120c3110f0b2d/MyTVnew",
)
LKVN_FPT_EVENTS_M3U_URL = os.environ.get(
    "LKVN_FPT_EVENTS_M3U_URL",
    "https://raw.githubusercontent.com/LKVN85/GIAI-TRI/3410a334f3e86938dd644cfe11dca70e4bf71a7b/LKVN%20GIAI%20TRI.M3U",
)
CUONGHEHE_M3U_URL = os.environ.get(
    "CUONGHEHE_M3U_URL",
    "https://raw.githubusercontent.com/cuongnh1989/iptv/refs/heads/main/cuonghehe",
)
TT1_4K_M3U_PATH = Path(os.environ.get("TT1_4K_M3U_PATH", str(BASE_DIR / "tt1.m3u")))
TT1_4K_ALLOWED_PREFIXES = tuple(
    prefix.strip().lower()
    for prefix in os.environ.get("TT1_4K_ALLOWED_PREFIXES", "4K | UK,4K | VIP").split(",")
    if prefix.strip()
)
COTIVI_SPORTS_M3U_URL = os.environ.get(
    "COTIVI_SPORTS_M3U_URL",
    "https://raw.githubusercontent.com/Bacbenny/freetvco/refs/heads/main/output/cotivi_sports.m3u",
)
CHOANG_JSON_URL = os.environ.get(
    "CHOANG_JSON_URL",
    "https://raw.githubusercontent.com/jasminliu98/choang-stream/refs/heads/main/output.json",
)
CHOANG_REFERER = os.environ.get("CHOANG_REFERER", f"https://{CHOANG_DEFAULT_DOMAIN}/")
CDNLIVE_EVENTS_URL = os.environ.get(
    "CDNLIVE_EVENTS_URL",
    "https://api.cdnlivetv.tv/api/v1/events/sports/?user=cdnlivetv&plan=free",
)
CDNLIVE_REFERER = os.environ.get("CDNLIVE_REFERER", "https://cdnlivetv.tv/")
CDNLIVE_GROUP = os.environ.get("CDNLIVE_GROUP", "CDNLive")
CDNLIVE_LIMIT = int(os.environ.get("CDNLIVE_LIMIT", "80") or "80")
CDNLIVE_WORKERS = int(os.environ.get("CDNLIVE_WORKERS", "12") or "12")
TIVIHUB_M3U_URL = os.environ.get("TIVIHUB_M3U_URL", "https://api.tivihub.app/matches.m3u")
TIVIHUB_API_BASE_URL = os.environ.get("TIVIHUB_API_BASE_URL", "https://api.tivihub.app/api/match/")
TIVIHUB_GROUP_PREFIX = os.environ.get("TIVIHUB_GROUP_PREFIX", "Tivihub")
TIVIHUB_REFERER = os.environ.get("TIVIHUB_REFERER", "https://iframe.rumsport8.live")
TIVIHUB_LIMIT = int(os.environ.get("TIVIHUB_LIMIT", "200") or "200")
TIVIHUB_WORKERS = int(os.environ.get("TIVIHUB_WORKERS", "12") or "12")
MEBONG_SITE_URL = os.environ.get("MEBONG_SITE_URL", "https://mebongtv.live/")
MEBONG_GROUP = os.environ.get("MEBONG_GROUP", "MebongTV")
MEBONG_LIMIT = int(os.environ.get("MEBONG_LIMIT", "80") or "80")
MEBONG_WORKERS = int(os.environ.get("MEBONG_WORKERS", "6") or "6")
MEBONG_PROXY_UA = os.environ.get("MEBONG_PROXY_UA", UA)
XOILACZ_SITE_URL = os.environ.get("XOILACZ_SITE_URL", "https://xoilacz.vip/")
XOILACZ_REFERER = os.environ.get("XOILACZ_REFERER", "https://xlz.livecarriercdn.com/")
XOILACZ_FALLBACK_REFERERS = [
    item.strip()
    for item in os.environ.get(
        "XOILACZ_FALLBACK_REFERERS",
        "https://xlz.livecarriercdn.com/,https://xoilacxtv.tv/,https://xoilacct.tv/",
    ).split(",")
    if item.strip()
]
XOILACZ_PAGES = int(os.environ.get("XOILACZ_PAGES", "1"))
XOILACZ_SPORTS = [
    item.strip()
    for item in os.environ.get("XOILACZ_SPORTS", "football,basketball,tennis,volleyball").split(",")
    if item.strip()
]
AZABU_BASE_URL = os.environ.get("AZABU_BASE_URL", "https://azabuglobal.com/")
AZABU_LIVE_LIMIT = int(os.environ.get("AZABU_LIVE_LIMIT", "30"))
AZABU_HIGHLIGHT_PAGES = int(os.environ.get("AZABU_HIGHLIGHT_PAGES", "1"))
DEKIKI_M3U_URL = os.environ.get(
    "DEKIKI_M3U_URL",
    "https://raw.githubusercontent.com/Bacbenny/dekiki/refs/heads/main/dekki.m3u",
)
TV365_ERROR_M3U_URL = os.environ.get(
    "TV365_ERROR_M3U_URL",
    "https://raw.githubusercontent.com/TV365-VN/TV365-DATA/refs/heads/main/error.m3u",
)
TINHLAGI_SPORT_M3U_URL = os.environ.get("TINHLAGI_SPORT_M3U_URL", "https://tinhlagi.pro/s.m3u")
THETHAOCOBAN_M3U_URL = os.environ.get("THETHAOCOBAN_M3U_URL", "https://thcoban.github.io/ththethao/ttthethao.m3u")
CLOUDOK_M3U_URL = os.environ.get(
    "CLOUDOK_M3U_URL",
    "https://raspy-waterfall-a003.ngoibut-cachmang.workers.dev/",
)
CLOUDOK_AUTH_TOKEN = os.environ.get("CLOUDOK_AUTH_TOKEN", "dc5521f1fe411d6f2e83c2bf047d6294")
SPORT_INTERNATIONAL_GROUP = "TH\u1ec2 THAO QU\u1ed0C T\u1ebe"
FLV_OTT_GROUP = "FLV | OTT Player"
FLV_OTT_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; Mobile) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36"
)
# Default is raw collection for GitHub Actions: keep every non-empty .m3u8 link.
# Set VERIFY_STREAMS=1 only when you want to test whether streams respond now.
VERIFY_STREAMS = os.environ.get("VERIFY_STREAMS", "0").strip().lower() in {"1", "true", "yes"}
MAX_VERIFY_WORKERS = int(os.environ.get("MAX_VERIFY_WORKERS", "20"))
FILTER_PAST_EVENTS = os.environ.get("FILTER_PAST_EVENTS", "1").strip().lower() not in {"0", "false", "no"}
PAST_EVENT_GRACE_MINUTES = int(os.environ.get("PAST_EVENT_GRACE_MINUTES", "180") or "180")


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


def request_get_no_cache(url, headers=None, params=None, timeout=20):
    params = dict(params or {})
    params.setdefault("t", int(time.time() * 1000))
    return request_get(url, headers=headers, params=params, timeout=timeout)


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


def fetch_json_no_cache(url, headers=None, timeout=20):
    separator = "&" if "?" in url else "?"
    return fetch_json(f"{url}{separator}t={int(time.time() * 1000)}", headers=headers, timeout=timeout)


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


def remove_icons(value):
    text = str(value or "")
    cleaned = []
    for char in text:
        code = ord(char)
        category = unicodedata.category(char)
        if code in (0x200D, 0xFE0F):
            continue
        if category == "So" and code >= 0x2600:
            continue
        if 0x1F000 <= code <= 0x1FAFF:
            continue
        cleaned.append(char)
    return re.sub(r"\s+", " ", "".join(cleaned)).strip()


def sanitize_extinf_line(line):
    line = remove_icons(line)
    line = re.sub(
        r'group-title="([^"]*)"',
        lambda match: f'group-title="{clean_text(match.group(1))}"',
        line,
    )
    line = re.sub(r"\s+\|", " |", line)
    line = re.sub(r"\|\s+", "| ", line)
    line = re.sub(r"\s+,", ",", line)
    return line


def set_extinf_group_title(line, group_title):
    line = str(line or "")
    replacement = f'group-title="{group_title}"'
    if re.search(r'group-title="[^"]*"', line):
        return re.sub(r'group-title="[^"]*"', replacement, line, count=1)
    if "," in line:
        left, right = line.split(",", 1)
        return f"{left} {replacement},{right}"
    return f"{line} {replacement}"


def parse_iso_to_ict(value, fmt="%H:%M | %d.%m"):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(TZ_VN).strftime(fmt)
    except Exception:
        return str(value)


def parse_iso_to_ict_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(TZ_VN)
    except Exception:
        return None


def parse_iso_to_ict_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(TZ_VN).date()
    except Exception:
        return None


def parse_epoch_to_ict_date(value):
    try:
        timestamp = int(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp, TZ_VN).date()
    except Exception:
        return None


def parse_epoch_to_ict_datetime(value):
    try:
        timestamp = int(value)
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp, TZ_VN)
    except Exception:
        return None


def parse_utc_text_to_ict_datetime(value):
    text = clean_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).astimezone(TZ_VN)
        except Exception:
            pass
    return parse_iso_to_ict_datetime(text)


def date_from_text(value):
    text = clean_text(value)
    if not text:
        return None
    today = datetime.now(TZ_VN).date()

    def build_date(day, month, year=None):
        has_year = bool(year)
        year = int(year) if has_year else today.year
        try:
            candidate = datetime(year, int(month), int(day), tzinfo=TZ_VN).date()
        except Exception:
            return None
        if not has_year and (today - candidate).days > 180:
            try:
                candidate = datetime(today.year + 1, int(month), int(day), tzinfo=TZ_VN).date()
            except Exception:
                pass
        return candidate

    match = re.search(r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), tzinfo=TZ_VN).date()
        except Exception:
            return None
    for match in re.finditer(
        r"(?:^|[^\d])\d{1,2}:\d{2}\s*[- ]\s*(\d{1,2})[/-](\d{1,2})(?:[/-](20\d{2}))?(?!\d)",
        text,
    ):
        candidate = build_date(match.group(1), match.group(2), match.group(3))
        if candidate:
            return candidate
    for match in re.finditer(r"(?<!\d)(\d{1,2})[/-](\d{1,2})(?:[/-](20\d{2}))?(?!\d)", text):
        candidate = build_date(match.group(1), match.group(2), match.group(3))
        if candidate:
            return candidate
    for match in re.finditer(r"(?<!\d)(\d{1,2})[.](\d{1,2})(?!\d)", text):
        candidate = build_date(match.group(1), match.group(2))
        if candidate:
            return candidate
    return None


def datetime_from_text(value):
    text = clean_text(value)
    if not text:
        return None
    today = datetime.now(TZ_VN).date()
    patterns = [
        r"\b(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})\s+(\d{1,2}):(\d{2})\b",
        r"\b(\d{1,2}):(\d{2})\s*[- ]\s*(\d{1,2})[/-](\d{1,2})(?:[/-](20\d{2}))?\b",
        r"\b(\d{1,2}):(\d{2})\s+(\d{1,2})[/-](\d{1,2})(?:[/-](20\d{2}))?\b",
    ]
    match = re.search(patterns[0], text)
    if match:
        try:
            return datetime(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
                int(match.group(4)),
                int(match.group(5)),
                tzinfo=TZ_VN,
            )
        except Exception:
            return None
    for pattern in patterns[1:]:
        match = re.search(pattern, text)
        if not match:
            continue
        hour, minute, day, month, year = match.groups()
        year = int(year) if year else today.year
        try:
            candidate = datetime(year, int(month), int(day), int(hour), int(minute), tzinfo=TZ_VN)
        except Exception:
            continue
        if not match.group(5) and (today - candidate.date()).days > 180:
            try:
                candidate = candidate.replace(year=today.year + 1)
            except Exception:
                pass
        return candidate
    return None


def combine_date_and_time(event_date, time_text):
    if not event_date:
        return None
    if hasattr(event_date, "date"):
        event_date = event_date.date()
    match = re.search(r"\b(\d{1,2}):(\d{2})\b", clean_text(time_text))
    if not match:
        return None
    try:
        return datetime(
            event_date.year,
            event_date.month,
            event_date.day,
            int(match.group(1)),
            int(match.group(2)),
            tzinfo=TZ_VN,
        )
    except Exception:
        return None


def channel_event_datetime(channel):
    explicit = channel.get("event_datetime")
    if explicit:
        if hasattr(explicit, "astimezone"):
            return explicit.astimezone(TZ_VN)
        parsed = parse_vn_datetime_text(explicit) or datetime_from_text(explicit)
        if parsed:
            return parsed
    text = " ".join(
        clean_text(part)
        for part in (
            channel.get("name"),
            channel.get("group"),
            channel.get("raw_extinf"),
            " ".join(channel.get("raw_options") or []),
        )
        if part
    )
    return parse_vn_datetime_text(text) or datetime_from_text(text)


def channel_event_date(channel):
    explicit = channel.get("event_date")
    if explicit:
        if hasattr(explicit, "date"):
            return explicit.date()
        parsed = parse_iso_to_ict_date(explicit) or date_from_text(explicit)
        if parsed:
            return parsed
    text = " ".join(
        clean_text(part)
        for part in (
            channel.get("name"),
            channel.get("group"),
            channel.get("raw_extinf"),
            " ".join(channel.get("raw_options") or []),
        )
        if part
    )
    return date_from_text(text)


def filter_current_and_future_events(channels):
    if not FILTER_PAST_EVENTS:
        return channels
    now = datetime.now(TZ_VN)
    today = now.date()
    cutoff = now - timedelta(minutes=max(0, PAST_EVENT_GRACE_MINUTES))
    kept = []
    removed_by_date = 0
    removed_by_time = 0
    for channel in channels:
        if channel.get("skip_event_filter"):
            kept.append(channel)
            continue
        event_dt = channel_event_datetime(channel)
        if event_dt and event_dt < cutoff:
            removed_by_time += 1
            continue
        event_date = channel_event_date(channel)
        if event_date and event_date < today:
            removed_by_date += 1
            continue
        kept.append(channel)
    if removed_by_date or removed_by_time:
        log(f"[FILTER] Removed past events: date={removed_by_date}, time={removed_by_time}")
    return kept


def channel_key(channel):
    return (
        channel.get("stream_url", "").strip(),
        channel.get("name", "").strip(),
        channel.get("source", "").strip(),
    )


def is_hls_url(url):
    lower = clean_text(url).lower().split("?", 1)[0]
    return ".m3u8" in lower or lower.endswith("/m3u8")


def is_flv_url(url):
    lower = clean_text(url).lower().split("?", 1)[0]
    return lower.endswith(".flv")


def is_valid_xoilacz_stream_url(url):
    url = clean_text(url)
    if not url or not url.startswith(("http://", "https://")):
        return False
    lower = url.lower().split("?", 1)[0]
    if lower.endswith(".mpd") or ".mpd/" in lower:
        return False
    return is_hls_url(url) or is_flv_url(url)


def xoilacz_stream_referer(stream_url):
    stream_url_key = clean_text(stream_url).lower()
    if (
        "originpullstream.com" in stream_url_key
        or "m3u8delivery.com" in stream_url_key
        or "quickscoreboardz.com" in stream_url_key
    ):
        return XOILACZ_FALLBACK_REFERERS[0] if XOILACZ_FALLBACK_REFERERS else XOILACZ_REFERER
    return XOILACZ_REFERER


def is_valid_stream_url(url):
    url = clean_text(url)
    return bool(url and is_hls_url(url) and not url.startswith(("udp://", "rtp://")))


def is_valid_highlight_url(url):
    url = clean_text(url)
    if not url or not url.startswith(("http://", "https://")):
        return False
    lower = url.lower().split("?", 1)[0]
    return (is_hls_url(url) or lower.endswith(".mp4")) and ".mpd" not in lower


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
    ("Bida", ("bida", "billiard", "billiards", "pool", "cuesports", "phoenix open")),
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


def compact_text_key(value):
    return re.sub(r"[^a-z0-9]+", "", text_key(value))


GROUP_CANONICAL_RULES = [
    ("Sự kiện", ("su kien", "suu kien")),
    ("Gi\u1edd V\u00e0ng TV", ("giovang", "gio vang", "gio vang tv")),
    ("Socolive TV", ("socolive", "soco live", "soco sport", "socosport")),
    (SPORT_INTERNATIONAL_GROUP, ("the thao quoc te", "thethaoquocte", "sport quoc te", "international sport")),
    ("Vua S\u00e2n C\u1ecf TV", ("vua san co", "vuasanco", "vsc9")),
]

PREFERRED_OUTPUT_GROUPS = [
    "VTV",
    "Sự kiện",
    "MyTVFPTEvents",
    "FLV | OTT Player",
    "Gi\u1edd V\u00e0ng TV",
    "Vua S\u00e2n C\u1ecf TV",
    "Socolive TV",
    "CoLaTV",
    "BiaomTV",
    "MebongTV",
]

PREFERRED_SOURCE_PRIORITY = {
    "GioVang": 80,
    "VSC9": 76,
    "SocoliveTV": 72,
    "CoLaTV": 68,
    "BiaomTV": 64,
    "MebongTV": 60,
    "TinhLaGi": 40,
}

OMIT_REFERRER_GROUPS = {
    "VTV",
    "Sự kiện",
    "MyTVFPTEvents",
    "Socolive TV",
    "CoLaTV",
    "CO LA TV",
    "Highlight | S8TV",
    "MebongTV",
}
OMIT_REFERRER_GROUP_KEYS = {compact_text_key(item) for item in OMIT_REFERRER_GROUPS}

OMIT_USER_AGENT_GROUPS = {
    "VTV",
    "Sự kiện",
    "MyTVFPTEvents",
    "Socolive TV",
    "CoLaTV",
    "CO LA TV",
    "Highlight | S8TV",
    "MebongTV",
}
OMIT_USER_AGENT_GROUP_KEYS = {compact_text_key(item) for item in OMIT_USER_AGENT_GROUPS}


def canonical_group_title(group):
    group = clean_text(group)
    if not group:
        return group
    key = compact_text_key(group)
    spaced_key = text_key(group)
    for canonical, aliases in GROUP_CANONICAL_RULES:
        for alias in aliases:
            alias_key = compact_text_key(alias)
            alias_spaced = text_key(alias)
            if alias_key and alias_key in key:
                return canonical
            if alias_spaced and alias_spaced in spaced_key:
                return canonical
    return group


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
    return canonical_group_title(group or channel.get("source") or "Unknown")


def should_write_referrer(channel):
    group = output_group(channel)
    return compact_text_key(group) not in OMIT_REFERRER_GROUP_KEYS


def should_write_user_agent(channel):
    group = output_group(channel)
    return compact_text_key(group) not in OMIT_USER_AGENT_GROUP_KEYS


def normalize_channel_group(channel):
    if is_flv_url(channel.get("stream_url")):
        group = FLV_OTT_GROUP
        channel["user_agent"] = FLV_OTT_USER_AGENT
        if not clean_text(channel.get("referer")):
            stream_url_key = clean_text(channel.get("stream_url")).lower()
            if (
                "streambylivepulse.com" in stream_url_key
                or "procdnlive.com" in stream_url_key
                or "originpullstream.com" in stream_url_key
                or "m3u8delivery.com" in stream_url_key
                or "quickscoreboardz.com" in stream_url_key
            ):
                channel["referer"] = xoilacz_stream_referer(stream_url_key)
        raw_options = []
        for option_line in channel.get("raw_options") or []:
            if "http-user-agent=" in clean_text(option_line).lower():
                continue
            raw_options.append(option_line)
        channel["raw_options"] = raw_options
    elif channel.get("preserve_group_exact"):
        group = clean_text(channel.get("group") or channel.get("source") or "Unknown")
        if channel.get("source") == "TinhLaGi":
            group = canonical_group_title(remove_icons(group))
            if "tinhlagi" in compact_text_key(group):
                group = "Tinhlagi"
            else:
                group = f"Tinhlagi - {group}"
        elif "vuasanco" in compact_text_key(group):
            group = "Vua S\u00e2n C\u1ecf TV"
    else:
        group = output_group(channel)
    channel["group"] = group
    raw_extinf = clean_text(channel.get("raw_extinf"))
    if raw_extinf:
        channel["raw_extinf"] = set_extinf_group_title(raw_extinf, group)
    return channel


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
    return unique


def channel_priority(channel):
    group = group_key(channel.get("group"))
    source = clean_text(channel.get("source"))
    if group == group_key("VTV"):
        return 110
    if group == group_key("Sự kiện"):
        return 100
    if source == "VMTTV":
        return 90
    if is_flv_url(channel.get("stream_url")):
        return 85
    return PREFERRED_SOURCE_PRIORITY.get(source, 0)


def group_sort_rank(channel):
    group = group_key(output_group(channel))
    for index, preferred_group in enumerate(PREFERRED_OUTPUT_GROUPS):
        if group == group_key(preferred_group):
            return index
    if group.startswith("tinhlagi"):
        return len(PREFERRED_OUTPUT_GROUPS) + 10
    return len(PREFERRED_OUTPUT_GROUPS) + 50


def channel_time_sort_value(channel):
    event_dt = channel_event_datetime(channel)
    if event_dt:
        return int(event_dt.timestamp())
    return 9_999_999_999


def dedupe_and_sort_channels(channels):
    deduped = []
    seen_urls = {}
    for channel in channels:
        channel = normalize_channel_group(channel)
        url = channel.get("stream_url", "").strip()
        if not url:
            continue
        if url in seen_urls:
            current_index = seen_urls[url]
            current = deduped[current_index]
            current_header_score = bool(clean_text(current.get("referer"))) + bool(clean_text(current.get("user_agent")))
            new_header_score = bool(clean_text(channel.get("referer"))) + bool(clean_text(channel.get("user_agent")))
            current_priority = channel_priority(current)
            new_priority = channel_priority(channel)
            if new_priority > current_priority or (
                new_priority == current_priority and new_header_score > current_header_score
            ):
                deduped[current_index] = channel
            continue
        seen_urls[url] = len(deduped)
        deduped.append(channel)
    deduped.sort(
        key=lambda channel: (
            group_sort_rank(channel),
            output_group(channel),
            channel_time_sort_value(channel),
            clean_text(channel.get("name")),
            channel.get("stream_url", ""),
        )
    )
    return deduped


def write_m3u(path, channels):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Updated : {now_ict()}\n")
        f.write(f"# Total   : {len(channels)}\n\n")
        for ch in channels:
            if is_flv_url(ch.get("stream_url")):
                name = remove_icons(ch.get("name", "Unknown"))
                f.write(f"#EXTINF:0,{name}\n")
                f.write(f"#EXTGRP:{output_group(ch)}\n")
                referer = clean_text(ch.get("referer"))
                if referer and should_write_referrer(ch):
                    f.write(f"#EXTVLCOPT:http-referrer={referer}\n")
                f.write(f'{ch.get("stream_url", "")}\n\n')
                continue

            raw_extinf = clean_text(ch.get("raw_extinf")) if ch.get("preserve_extinf") else ""
            if raw_extinf:
                f.write(f"{sanitize_extinf_line(raw_extinf)}\n")
                for option_line in ch.get("raw_options") or []:
                    option_line = clean_text(option_line)
                    if option_line:
                        if option_line.lower().startswith("#extvlcopt:http-referrer=") and not should_write_referrer(ch):
                            continue
                        if option_line.lower().startswith("#extvlcopt:http-user-agent=") and not should_write_user_agent(ch):
                            continue
                        f.write(f"{option_line}\n")
            else:
                attrs = [
                    f'tvg-logo="{ch.get("logo", "")}"',
                    f'group-title="{output_group(ch)}"',
                ]
                name = remove_icons(ch.get("name", "Unknown"))
                f.write(f'#EXTINF:-1 {" ".join(attrs)},{name}\n')
            referer = clean_text(ch.get("referer"))
            user_agent = clean_text(ch.get("user_agent"))
            if referer and should_write_referrer(ch):
                f.write(f"#EXTVLCOPT:http-referrer={referer}\n")
            if user_agent and should_write_user_agent(ch):
                f.write(f"#EXTVLCOPT:http-user-agent={user_agent}\n")
            f.write(f'{ch.get("stream_url", "")}\n\n')


def write_ott_m3u(path, channels):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Updated : {now_ict()}\n")
        f.write(f"# Total   : {len(channels)}\n\n")
        for ch in channels:
            name = remove_icons(ch.get("name", "Unknown"))
            if is_flv_url(ch.get("stream_url")):
                f.write(f"#EXTINF:0,{name}\n")
                f.write(f"#EXTGRP:{FLV_OTT_GROUP}\n")
            else:
                attrs = [
                    f'tvg-logo="{ch.get("logo", "")}"',
                    f'group-title="{output_group(ch)}"',
                ]
                f.write(f'#EXTINF:-1 {" ".join(attrs)},{name}\n')
            f.write(f'{ch.get("stream_url", "")}\n\n')


def write_raw_playlist(path, source_name, playlist_url):
    log(f"[{source_name}] Fetch raw M3U")
    try:
        response = request_get(playlist_url, headers={"Accept": "*/*"}, timeout=60)
        log(f"[{source_name}] Raw HTTP {response.status_code}")
        if response.status_code != 200:
            return 0
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(response.text, encoding="utf-8", newline="")
        return response.text.count("#EXTINF")
    except Exception as exc:
        log(f"[{source_name}] Raw error: {exc}")
        return 0


def split_ott_channels(channels):
    normal_channels = []
    ott_channels = []
    for channel in channels:
        if is_flv_url(channel.get("stream_url")):
            ott_channels.append(channel)
        else:
            normal_channels.append(channel)
    return normal_channels, ott_channels


def channel_needs_extvlcopt(channel):
    if clean_text(channel.get("referer")) and should_write_referrer(channel):
        return True
    if clean_text(channel.get("user_agent")) and should_write_user_agent(channel):
        return True
    for option_line in channel.get("raw_options") or []:
        option_line = clean_text(option_line).lower()
        if option_line.startswith("#extvlcopt:http-referrer=") and should_write_referrer(channel):
            return True
        if option_line.startswith("#extvlcopt:http-user-agent=") and should_write_user_agent(channel):
            return True
    return False


def select_ott_compatible_channels(channels):
    selected = []
    for channel in channels:
        if is_flv_url(channel.get("stream_url")) or not channel_needs_extvlcopt(channel):
            selected.append(channel)
    return selected


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
        r = request_get_no_cache(api_url, headers=headers, timeout=20)
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
        event_datetime = parse_iso_to_ict_datetime(item.get("startTime"))
        event_date = event_datetime.date() if event_datetime else parse_iso_to_ict_date(item.get("startTime"))
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
                        "event_date": event_date,
                        "event_datetime": event_datetime,
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
    data = fetch_json_no_cache(LUONGSON_API_URL, headers={"Accept": "application/json, */*"}, timeout=25)
    items = ((data.get("value") or {}).get("datas") or []) if isinstance(data, dict) else []
    channels = []

    for item in items:
        match_id = item.get("matchId")
        if not match_id:
            continue

        detail_url = LUONGSON_MATCH_URL % match_id
        try:
            response = request_get_no_cache(detail_url, headers={"Accept": "application/json, */*"}, timeout=20)
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
    data = fetch_json_no_cache(api_url, headers=headers)
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
        event_datetime = parse_iso_to_ict_datetime(item.get("startTime"))
        event_date = event_datetime.date() if event_datetime else parse_iso_to_ict_date(item.get("startTime"))
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
                        "event_date": event_date,
                        "event_datetime": event_datetime,
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


def headers_from_request_headers(request_headers):
    headers = {}
    for item in request_headers or []:
        key = clean_text(item.get("key"))
        value = clean_text(item.get("value"))
        if key and value:
            headers[key.lower()] = value
    return headers


def collect_grouped_json(source, api_url, group_name, referer=None):
    log(f"[{source}] Fetch grouped JSON")
    headers = {"Accept": "application/json, */*"}
    if referer:
        headers["Referer"] = referer
        headers["Origin"] = referer.rstrip("/")
    data = fetch_json_no_cache(api_url, headers=headers)
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


def parse_vn_datetime_text(value):
    text = clean_text(value)
    if not text:
        return None
    text = re.sub(r"([+-]\d{2})$", r"\1:00", text)
    for fmt in ("%Y-%m-%d %H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S"):
        try:
            dt = datetime.strptime(text, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TZ_VN)
            return dt.astimezone(TZ_VN)
        except Exception:
            continue
    return None


def giovang_item_datetime(item):
    event_date = date_from_text(item.get("date") or item.get("day_month"))
    return combine_date_and_time(event_date, item.get("time")) or datetime_from_text(
        clean_text(f"{item.get('time', '')} {item.get('date') or item.get('day_month') or ''}")
    )


def collect_giovang_api():
    source = "GioVang"
    headers = {
        "Accept": "application/json, */*",
        "Origin": GIOVANG_REFERER.rstrip("/"),
        "Referer": GIOVANG_REFERER,
    }
    log(f"[{source}] Fetch API")
    api_sets = [
        (GIOVANG_API_LIVE, GIOVANG_API_ALL, GIOVANG_API_FIXTURES),
        (GIOVANG_OLD_API_LIVE, GIOVANG_OLD_API_ALL, GIOVANG_OLD_API_FIXTURES),
    ]
    seen_fixtures = {}
    fixture_api_by_id = {}
    for live_url, all_url, fixtures_url in api_sets:
        live_data = fetch_json_no_cache(live_url, headers=headers, timeout=30)
        all_data = fetch_json_no_cache(all_url, headers=headers, timeout=30)
        live_items = live_data.get("response") if isinstance(live_data, dict) else []
        all_items = all_data.get("response") if isinstance(all_data, dict) else []
        for item in live_items or []:
            fixture_id = clean_text(item.get("id") or item.get("fi"))
            if fixture_id and fixture_id not in seen_fixtures:
                seen_fixtures[fixture_id] = item
                fixture_api_by_id[fixture_id] = fixtures_url
        for item in all_items or []:
            fixture_id = clean_text(item.get("id") or item.get("fi"))
            if fixture_id and fixture_id not in seen_fixtures:
                seen_fixtures[fixture_id] = item
                fixture_api_by_id[fixture_id] = fixtures_url
    now = datetime.now(TZ_VN)
    fixtures = list(seen_fixtures.values())
    fixtures.sort(
        key=lambda item: (
            giovang_item_datetime(item) is None,
            giovang_item_datetime(item) and giovang_item_datetime(item) < now - timedelta(minutes=PAST_EVENT_GRACE_MINUTES),
            giovang_item_datetime(item) or datetime.max.replace(tzinfo=TZ_VN),
        )
    )
    if not fixtures:
        log(f"[{source}] Direct API empty, fallback grouped JSON")
        return collect_grouped_json(source, GIOVANG_FALLBACK_JSON_URL, "Gio Vang", GIOVANG_REFERER)

    channels = []
    seen_urls = set()
    for item in fixtures[:GIOVANG_LIMIT]:
        fixture_id = clean_text(item.get("id") or item.get("fi"))
        if not fixture_id:
            continue
        if clean_text(item.get("status_code")).upper() == "FT":
            continue
        primary_fixtures_url = fixture_api_by_id.get(fixture_id) or GIOVANG_API_FIXTURES
        detail = {}
        for fixtures_url in dict.fromkeys([primary_fixtures_url, GIOVANG_API_FIXTURES, GIOVANG_OLD_API_FIXTURES]):
            detail = fetch_json_no_cache(urljoin(fixtures_url.rstrip("/") + "/", fixture_id), headers=headers, timeout=20)
            if isinstance(detail, dict) and detail.get("response"):
                break
        match = detail.get("response") if isinstance(detail, dict) else {}
        if not isinstance(match, dict):
            continue

        teams = match.get("teams") or item.get("teams") or {}
        home = teams.get("home") or {}
        away = teams.get("away") or {}
        home_name = clean_text(home.get("name")) or "Home"
        away_name = clean_text(away.get("name")) or "Away"
        league = clean_text(((match.get("league") or item.get("league") or {}).get("title"))) or "Giờ Vàng TV"
        logo = clean_text(home.get("logo") or away.get("logo"))
        time_label = clean_text(match.get("time") or item.get("time"))
        event_date = date_from_text(match.get("date") or item.get("date") or item.get("day_month"))
        event_datetime = combine_date_and_time(event_date, time_label)

        for blv in match.get("blv") or []:
            blv_name = clean_text(blv.get("blv_name") or blv.get("name")) or "BLV"
            streams = [
                ("HD", blv.get("pc_stream_url")),
                ("Mobile", blv.get("mobile_stream_url")),
                ("HD Alt", blv.get("link_stream_hd")),
                ("SD", blv.get("link_stream_sd")),
            ]
            for quality, stream_url in streams:
                stream_url = clean_text(stream_url)
                if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
                    continue
                seen_urls.add(stream_url)
                channels.append(
                    {
                        "source": source,
                        "name": f"[{time_label}] {home_name} vs {away_name} | {blv_name} [{quality}]",
                        "group": "Giờ Vàng TV",
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": GIOVANG_REFERER,
                        "user_agent": UA,
                        "event_date": event_date,
                        "event_datetime": event_datetime,
                    }
                )

    fallback_channels = collect_grouped_json(source, GIOVANG_FALLBACK_JSON_URL, "Gio Vang", GIOVANG_REFERER)
    if fallback_channels:
        channels.extend(fallback_channels)

    if not channels:
        log(f"[{source}] Direct API has no stream, fallback grouped JSON")
        return fallback_channels
    log(f"[{source}] {len(channels)} raw links")
    return channels


PHAOHOA_STREAM_RE = re.compile(r"https://[^\"'\s<>]+?\.m3u8[^\"'\s<>]*", re.I)


def decode_phaohoa_html(text):
    return html.unescape(text or "").replace("\\u002F", "/").replace("\\/", "/")


def is_slug_like(value):
    value = clean_text(value)
    return bool(re.search(r"[a-z0-9]+-[a-z0-9-]*", value)) and value.lower() == value


def phaohoa_match_info_from_context(context):
    strings = [clean_text(s) for s in re.findall(r'"([^"{}\[\],:]+)"', context)]
    strings = [s for s in strings if s]

    start_matches = re.findall(r'"(\d{4}-\d{2}-\d{2}T[^"]+)"', context)
    event_datetime = parse_iso_to_ict_datetime(start_matches[-1]) if start_matches else None
    time_label = event_datetime.strftime("%H:%M %d/%m") if event_datetime else ""

    tail = strings
    if "requires_token" in strings:
        last_requires_token = len(strings) - 1 - strings[::-1].index("requires_token")
        tail = strings[last_requires_token + 1:]
    id_index = tail.index("id") if "id" in tail else len(tail)
    match_segment = tail[:id_index]

    name_pairs = []
    for index, value in enumerate(match_segment[:-1]):
        next_value = match_segment[index + 1]
        if value.startswith("/") or next_value.startswith("/"):
            continue
        if " vs " in value.lower() or value.startswith(("http://", "https://")):
            continue
        if is_slug_like(next_value):
            name_pairs.append(value)

    home_name = name_pairs[-2] if len(name_pairs) >= 2 else ""
    away_name = name_pairs[-1] if len(name_pairs) >= 1 else ""

    blv_name = ""
    if "is_live" in strings:
        last_is_live = len(strings) - 1 - strings[::-1].index("is_live")
        after_live = strings[last_is_live + 1:]
        for value in after_live:
            if value.startswith("/") or is_slug_like(value):
                continue
            if value in {"id", "name", "slug", "avatar_url", "sort_order", "chat_enabled"}:
                continue
            blv_name = value
            break

    return home_name, away_name, blv_name, time_label, event_datetime


def collect_phaohoa():
    source = "PhaoHoaTV"
    log(f"[{source}] Fetch home")
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Referer": PHAOHOA_FRONTEND_URL + "/",
    }
    try:
        response = requests.get(PHAOHOA_API_BASE + "/", headers=headers, timeout=30)
        html_text = decode_phaohoa_html(response.text)
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []

    channels = []
    seen_urls = set()
    for match in PHAOHOA_STREAM_RE.finditer(html_text):
        stream_url = clean_text(match.group(0)).rstrip(".,);]")
        if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)
        context = html_text[max(0, match.start() - 2600):match.start()]
        home_name, away_name, blv_name, time_label, event_datetime = phaohoa_match_info_from_context(context)
        if home_name and away_name:
            name = f"[{time_label}] {home_name} vs {away_name}".strip()
        else:
            name = title_from_stream_url(stream_url, source)
        if blv_name:
            name = f"{name} | {blv_name}"
        channels.append(
            {
                "source": source,
                "name": name,
                "group": "PhaoHoaTV",
                "logo": PHAOHOA_API_BASE + "/images/logo.png",
                "stream_url": stream_url,
                "referer": PHAOHOA_API_BASE + "/",
                "user_agent": UA,
                "event_datetime": event_datetime,
            }
        )

    log(f"[{source}] {len(channels)} raw links")
    return channels


def resolve_choang_endpoints():
    site_url = CHOANG_SITE_URL.rstrip("/")
    referer = CHOANG_REFERER
    api_url = CHOANG_API_URL
    detail_url = CHOANG_DETAIL_URL

    if os.environ.get("CHOANG_SITE_URL") or os.environ.get("CHOANG_API_URL") or os.environ.get("CHOANG_DETAIL_URL"):
        return site_url, referer, api_url, detail_url

    try:
        response = request_get(
            CHOANG_ENTRY_SITE_URL,
            headers={"Accept": "text/html,application/xhtml+xml,*/*"},
            timeout=10,
        )
        parsed = urlparse(response.url)
        netloc = parsed.netloc[4:] if parsed.netloc.startswith("www.") else parsed.netloc
        if parsed.scheme and netloc:
            site_url = f"{parsed.scheme}://{netloc}"
            referer = site_url + "/"
            api_url = f"{parsed.scheme}://api.{netloc}/matchSchedule/getList"
            detail_url = f"{parsed.scheme}://api.{netloc}/matchSchedule/getDetail"
            if netloc != CHOANG_DEFAULT_DOMAIN:
                log(f"[ChoangTV] Discovered domain: {site_url}")
    except Exception as exc:
        log(f"[ChoangTV] Domain discovery skipped: {exc}")

    return site_url, referer, api_url, detail_url


def collect_choangtv_api():
    source = "ChoangTV"
    site_url, referer, api_url, detail_api_url = resolve_choang_endpoints()
    headers = {
        "Accept": "application/json, */*",
        "Origin": site_url,
        "Referer": referer,
    }
    channels = []
    seen_urls = set()
    today = datetime.now(TZ_VN).date()

    log(f"[{source}] Fetch API")
    for day_offset in range(max(1, CHOANG_DAYS)):
        target_date = today + timedelta(days=day_offset)
        list_data = fetch_json_no_cache(
            api_url,
            headers=headers,
            timeout=20,
        ) if "?" in api_url else fetch_json_no_cache(
            f"{api_url}?date={target_date.isoformat()}",
            headers=headers,
            timeout=20,
        )
        matches = list_data.get("data") if isinstance(list_data, dict) else []
        if not isinstance(matches, list):
            continue
        for item in matches:
            match_id = item.get("id")
            if not match_id:
                continue
            detail_url = f"{detail_api_url}?matchId={match_id}"
            detail = fetch_json_no_cache(detail_url, headers=headers, timeout=20)
            match = detail.get("data") if isinstance(detail, dict) else {}
            if not isinstance(match, dict):
                continue
            stream_url = normalize_choang_stream_url(match.get("liveUrl"))
            if not stream_url:
                stream_url = normalize_choang_stream_url(f"live{match_id}/index.m3u8")
            if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
                continue
            seen_urls.add(stream_url)
            dt = parse_vn_datetime_text(match.get("time") or item.get("time"))
            time_label = dt.strftime("%Hh%M") if dt else ""
            league = clean_text(match.get("league") or item.get("league"))
            category = clean_text(match.get("category") or item.get("category"))
            channels.append(
                {
                    "source": source,
                    "name": (
                        f"[{time_label}] {clean_text(match.get('name1')) or 'Home'} "
                        f"vs {clean_text(match.get('name2')) or 'Away'} | {clean_text(match.get('caster')) or 'BLV'}"
                        f"{f' [{league}]' if league else ''}"
                    ),
                    "group": "ChoangTV",
                    "logo": clean_text(match.get("logo1") or match.get("logo2") or match.get("casterLogo")),
                    "stream_url": stream_url,
                    "referer": referer,
                    "user_agent": UA,
                    "sport": detect_sport(category, league, match.get("name1"), match.get("name2")),
                    "event_date": dt.date() if dt else date_from_text(match.get("time") or item.get("time")),
                    "event_datetime": dt,
                }
            )

    if not channels:
        log(f"[{source}] Direct API has no stream, fallback grouped JSON")
        return collect_grouped_json(source, CHOANG_JSON_URL, "ChoangTV", referer)
    log(f"[{source}] {len(channels)} raw links")
    return channels


def normalize_choang_stream_url(value):
    stream_url = clean_text(value)
    if not stream_url:
        return ""
    if stream_url.startswith("//"):
        return "https:" + stream_url
    if stream_url.startswith(("http://", "https://")):
        return stream_url
    return CHOANG_CDN_BASE.rstrip("/") + "/" + stream_url.lstrip("/")


def collect_vongcam():
    source = "VongCamTV"
    api_url = discover_internal_matches_api(source, VONGCAM_FRONTEND_URL, VONGCAM_API_URL)
    log(f"[{source}] Fetch API")
    data = fetch_json_no_cache(
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
    data = fetch_json_no_cache(api_url)
    values = (data.get("data") or {}).values() if isinstance(data.get("data"), dict) else []
    channels = []

    for item in values:
        match_time = item.get("matchTime")
        event_datetime = parse_epoch_to_ict_datetime(match_time)
        event_date = event_datetime.date() if event_datetime else parse_epoch_to_ict_date(match_time)
        dt = event_datetime.strftime("%H:%M") if event_datetime else ""
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
                        "event_date": event_date,
                        "event_datetime": event_datetime,
                    }
                )
    log(f"[{source}] {len(channels)} raw links")
    return channels


def biaom_field_from_context(context, field):
    matches = re.findall(rf'{re.escape(field)}\\":\\"((?:\\\\.|[^\\"])*)\\"', context)
    return clean_text(decode_json_string(matches[-1]).rstrip("\\")) if matches else ""


def biaom_nested_field_from_context(context, object_name, field):
    pattern = rf'{re.escape(object_name)}\\":\{{[^{{}}]*?{re.escape(field)}\\":\\"((?:\\\\.|[^\\"])*)\\"'
    matches = re.findall(pattern, context)
    return clean_text(decode_json_string(matches[-1]).rstrip("\\")) if matches else ""


def collect_biaom():
    source = "BiaomTV"
    site_url = BIAOM_SITE_URL.rstrip("/") + "/"
    headers = {
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Referer": site_url,
    }
    log(f"[{source}] Fetch home")
    try:
        html_text = fetch_text(site_url, headers=headers, timeout=30)
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []
    if not html_text:
        log(f"[{source}] Home not available")
        return []

    channels = []
    seen_urls = set()
    for match in re.finditer(r"https?://[^\s'\"<>\\]+?\.m3u8[^\s'\"<>\\]*", html_text):
        stream_url = clean_text(decode_json_string(match.group(0)))
        if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)

        context = html_text[max(0, match.start() - 1600) : match.start()]
        league = biaom_field_from_context(context, "league_title") or biaom_nested_field_from_context(context, "league", "name")
        home = biaom_field_from_context(context, "localteam_title") or biaom_nested_field_from_context(context, "home", "name")
        away = biaom_field_from_context(context, "visitorteam_title") or biaom_nested_field_from_context(context, "away", "name")
        start_time = biaom_field_from_context(context, "starting_at")
        logo = (
            biaom_field_from_context(context, "localteam_logo")
            or biaom_field_from_context(context, "visitorteam_logo")
            or biaom_nested_field_from_context(context, "home", "image_url")
            or biaom_nested_field_from_context(context, "away", "image_url")
        )
        time_label = parse_iso_to_ict(start_time, fmt="%H:%M-%d/%m")

        title_parts = []
        if time_label:
            title_parts.append(f"[{time_label}]")
        if home and away:
            title_parts.append(f"{home} vs {away}")
        if league:
            title_parts.append(f"[{league}]")
        title = " ".join(title_parts) or title_from_stream_url(stream_url, source)

        channels.append(
            {
                "source": source,
                "name": title,
                "group": source,
                "logo": logo,
                "stream_url": stream_url,
                "referer": site_url,
                "user_agent": UA,
            }
        )

    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_tamquoc():
    source = "TamQuocTV"
    api_url = "https://sv.tamquoctv.xyz/internal/api/matches"
    log(f"[{source}] Fetch API")
    data = fetch_json_no_cache(api_url)
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
    return allow_non_m3u8 or is_hls_url(url)


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
    preserve_group_exact=False,
    request_headers=None,
):
    log(f"[{source}] Fetch M3U")
    r = None
    for attempt in range(1, retries + 1):
        try:
            r = request_get(playlist_url, headers=request_headers, timeout=timeout)
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
            title = current.get("title") or group_name
            if source == "TinhLaGi":
                logo = clean_text(current.get("logo"))
                if group_key(title) == "capnhat" or line.rstrip("/") == "https://tinhlagi.pro/logo.jpg":
                    continue
                if "tinhlagi.pro/info_card.php?kind=clock" in logo:
                    continue
            if not group_matches_any(group, allowed_groups):
                continue
            channels.append(
                {
                    "source": source,
                    "name": title,
                    "group": group or group_name or source,
                    "logo": current.get("logo", ""),
                    "stream_url": line,
                    "referer": referer or (playlist_url if default_referer_to_playlist else ""),
                    "user_agent": user_agent,
                    "raw_extinf": current.get("raw_extinf", ""),
                    "raw_options": list(current.get("raw_options") or []),
                    "preserve_extinf": preserve_extinf,
                    "preserve_group_exact": preserve_group_exact,
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
        r = request_get_no_cache(api_url, headers=headers, timeout=20)
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
        league_data = match.get("league") or match.get("tournament") or {}
        if isinstance(league_data, dict):
            league = clean_text(league_data.get("name") or league_data.get("title")) or source
        else:
            league = clean_text(league_data) or source
        event_datetime = parse_iso_to_ict_datetime(match.get("matchTime"))
        event_date = event_datetime.date() if event_datetime else parse_iso_to_ict_date(match.get("matchTime"))
        time_label = parse_iso_to_ict(match.get("matchTime"), "%Hh%M")

        for blv in match.get("blvs") or []:
            blv_name = clean_text(blv.get("name") or blv.get("nickname")) or "BLV"
            for stream in blv.get("streams") or []:
                stream_url = clean_text(stream.get("url"))
                if not stream_url:
                    continue
                quality = clean_text(stream.get("label") or stream.get("name") or stream.get("quality")) or "HD"
                channels.append(
                    {
                        "source": source,
                        "name": f"[{time_label}] {home_name} vs {away_name} | BLV: {blv_name} [{quality}]",
                        "group": league,
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": site_ref + "/",
                        "user_agent": UA,
                        "event_date": event_date,
                        "event_datetime": event_datetime,
                    }
                )
    log(f"[{source}] {len(channels)} links")
    return channels


def collect_bonglau():
    source = "BongLauTV"
    headers = {
        "Accept": "application/json, */*",
        "Origin": BONG_LAU_SITE_URL.rstrip("/"),
        "Referer": BONG_LAU_REFERER,
    }

    log(f"[{source}] Fetch API")
    try:
        r = request_get_no_cache(BONG_LAU_API_URL, headers=headers, timeout=20)
        log(f"[{source}] HTTP {r.status_code}")
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
        event_datetime = parse_iso_to_ict_datetime(match.get("matchTime"))
        event_date = event_datetime.date() if event_datetime else parse_iso_to_ict_date(match.get("matchTime"))
        time_label = parse_iso_to_ict(match.get("matchTime"), "%Hh%M")
        blvs = match.get("blvs_bonglau") or match.get("blvs") or []

        for blv in blvs:
            blv_name = clean_text(blv.get("name") or blv.get("nickname")) or "BLV"
            for stream in blv.get("streams") or []:
                stream_url = clean_text(stream.get("url"))
                if not stream_url:
                    continue
                quality = clean_text(stream.get("label") or stream.get("name") or stream.get("quality")) or "HD"
                channels.append(
                    {
                        "source": source,
                        "name": f"[{time_label}] {home_name} vs {away_name} | BLV: {blv_name} [{quality}]",
                        "group": "Bong Lau TV",
                        "logo": logo,
                        "stream_url": stream_url,
                        "referer": BONG_LAU_REFERER,
                        "user_agent": UA,
                        "event_date": event_date,
                        "event_datetime": event_datetime,
                    }
                )
    log(f"[{source}] {len(channels)} links")
    return channels


def parse_jsonp(text, callback_name):
    pattern = rf"\s*{re.escape(callback_name)}\((.*)\)\s*;?\s*$"
    match = re.match(pattern, text or "", re.S)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except Exception:
        return {}


def socolive_time_label(match_time):
    try:
        timestamp = int(match_time)
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        return datetime.fromtimestamp(timestamp, TZ_VN).strftime("%H:%M %d/%m")
    except Exception:
        return ""


def collect_socolive():
    source = "SocoliveTV"
    timestamp = int(time.time())
    api_url = SOCOLIVE_API_URL % timestamp if "%d" in SOCOLIVE_API_URL else SOCOLIVE_API_URL
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "Referer": SOCOLIVE_REFERER,
        "Origin": SOCOLIVE_REFERER.rstrip("/"),
    }
    log(f"[{source}] Fetch matches")
    try:
        text = fetch_text(api_url, headers=headers, timeout=30)
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []
    data = parse_jsonp(text, "matches")
    matches_data = (data.get("data") or {}) if isinstance(data, dict) else {}
    matches = []
    if isinstance(matches_data, dict):
        for items in matches_data.values():
            if isinstance(items, list):
                matches.extend(items)
    elif isinstance(matches_data, list):
        matches = matches_data

    channels = []
    room_candidates = []
    seen_candidate_rooms = set()
    seen_urls = set()
    for match in matches[: max(1, SOCOLIVE_LIMIT)]:
        home_name = clean_text(match.get("hostName"))
        guest_name = clean_text(match.get("guestName"))
        title = clean_text(f"{home_name} vs {guest_name}") if home_name and guest_name else home_name or guest_name
        league = clean_text(match.get("subCateName") or match.get("categoryName")) or "Socolive TV"
        logo = clean_text(match.get("hostIcon") or match.get("guestIcon") or match.get("categoryIcon"))
        event_datetime = parse_epoch_to_ict_datetime(match.get("matchTime"))
        event_date = event_datetime.date() if event_datetime else parse_epoch_to_ict_date(match.get("matchTime"))
        time_label = socolive_time_label(match.get("matchTime"))
        anchors = match.get("anchors") or []
        for anchor_item in anchors:
            anchor_info = anchor_item.get("anchor") or {}
            room_num = clean_text(anchor_info.get("roomNum") or anchor_item.get("uid"))
            if not room_num or room_num in seen_candidate_rooms:
                continue
            seen_candidate_rooms.add(room_num)
            room_candidates.append(
                {
                    "room_num": room_num,
                    "title": title,
                    "league": league,
                    "logo": logo,
                    "time_label": time_label,
                    "event_date": event_date,
                    "event_datetime": event_datetime,
                    "blv_name": clean_text(anchor_item.get("nickName")),
                }
            )

    live_rooms_url = SOCOLIVE_LIVE_ROOMS_URL % int(time.time()) if "%d" in SOCOLIVE_LIVE_ROOMS_URL else SOCOLIVE_LIVE_ROOMS_URL
    try:
        live_rooms_text = fetch_text(live_rooms_url, headers=headers, timeout=30)
        live_rooms_data = parse_jsonp(live_rooms_text, "all_live_rooms")
    except Exception:
        live_rooms_data = {}
    live_rooms_root = (live_rooms_data.get("data") or {}) if isinstance(live_rooms_data, dict) else {}
    live_room_count = 0
    if isinstance(live_rooms_root, dict):
        for rooms in live_rooms_root.values():
            if not isinstance(rooms, list):
                continue
            for room in rooms:
                room_num = clean_text(room.get("roomNum"))
                if not room_num or room_num in seen_candidate_rooms:
                    continue
                seen_candidate_rooms.add(room_num)
                live_room_count += 1
                room_candidates.append(
                    {
                        "room_num": room_num,
                        "title": clean_text(room.get("title") or room.get("detail") or room.get("notice")),
                        "league": clean_text(room.get("title")).split(":", 1)[0] if ":" in clean_text(room.get("title")) else "Socolive TV",
                        "logo": clean_text(room.get("cover") or room.get("customCoverUrl")),
                        "time_label": "",
                        "event_date": None,
                        "event_datetime": None,
                        "blv_name": clean_text((room.get("anchor") or {}).get("nickName") or room.get("detail")),
                    }
                )
                if live_room_count >= max(0, SOCOLIVE_LIVE_ROOM_LIMIT):
                    break
            if live_room_count >= max(0, SOCOLIVE_LIVE_ROOM_LIMIT):
                break

    for candidate in room_candidates:
        room_num = candidate["room_num"]
        detail_url = SOCOLIVE_MATCH_URL % (room_num, int(time.time())) if "%s" in SOCOLIVE_MATCH_URL else SOCOLIVE_MATCH_URL
        try:
            detail_text = fetch_text(detail_url, headers=headers, timeout=20)
        except Exception:
            continue
        detail = parse_jsonp(detail_text, "detail")
        detail_data = (detail.get("data") or {}) if isinstance(detail, dict) else {}
        room = detail_data.get("room") or {}
        stream_data = detail_data.get("stream") or {}
        blv_name = clean_text(candidate.get("blv_name") or (room.get("anchor") or {}).get("nickName") or room.get("detail"))
        title = clean_text(candidate.get("title") or room.get("title") or source)
        league = clean_text(candidate.get("league") or "Socolive TV")
        logo = clean_text(candidate.get("logo") or room.get("cover") or room.get("customCoverUrl"))
        time_label = clean_text(candidate.get("time_label"))
        event_date = candidate.get("event_date")
        event_datetime = candidate.get("event_datetime")
        stream_pairs = [
            ("SD M3U8", stream_data.get("m3u8")),
            ("HD M3U8", stream_data.get("hdM3u8")),
            ("SD FLV", stream_data.get("flv")),
            ("HD FLV", stream_data.get("hdFlv")),
        ]
        for quality, stream_url in stream_pairs:
            stream_url = clean_text(stream_url)
            if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
                continue
            seen_urls.add(stream_url)
            name_bits = []
            if time_label:
                name_bits.append(f"[{time_label}]")
            name_bits.append(title or source)
            if blv_name:
                name_bits.append(f"| BLV: {blv_name}")
            name_bits.append(f"[{quality}]")
            channels.append(
                {
                    "source": source,
                    "name": " ".join(name_bits),
                    "group": f"Socolive TV | {league}",
                    "logo": logo,
                    "stream_url": stream_url,
                    "referer": SOCOLIVE_REFERER,
                    "user_agent": FLV_OTT_USER_AGENT if is_flv_url(stream_url) else UA,
                    "event_date": event_date,
                    "event_datetime": event_datetime,
                }
            )

    log(f"[{source}] {len(channels)} raw links")
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


def collect_tt1_4k():
    source = "CuongHeHe4K"
    path = TT1_4K_M3U_PATH
    if not path.exists():
        log(f"[{source}] Skipped: {path} not found")
        return []

    channels = []
    seen_urls = set()
    current = {"title": "4K", "logo": ""}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            current = parse_extinf(line)
            continue
        if line.startswith("http") and is_supported_playlist_url(line, allow_non_m3u8=True):
            if line in seen_urls:
                continue
            seen_urls.add(line)
            title = remove_icons(current.get("title") or "4K")
            title = re.sub(r"#+", "", title)
            title = re.sub(r"\s+", " ", title).strip(" -|")
            if not title.lower().startswith("4k"):
                title = f"4K | {title}"
            title_key = title.lower()
            if TT1_4K_ALLOWED_PREFIXES and not title_key.startswith(TT1_4K_ALLOWED_PREFIXES):
                continue
            title = re.sub(r"^4K\s*\|\s*(?:UK|VIP)\s*-\s*", "", title, flags=re.I)
            channels.append(
                {
                    "source": source,
                    "name": title,
                    "group": "4K",
                    "logo": current.get("logo", ""),
                    "stream_url": line,
                    "referer": "",
                    "user_agent": "",
                    "preserve_group_exact": True,
                }
            )

    log(f"[{source}] {len(channels)} raw links")
    return channels


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
        allowed_groups=("VTV", "the thao quoc te", "su kien vtvprime"),
    )
    sport_group_key = "thethaoquocte"
    event_group_keys = {"sukienvtvprime"}
    for channel in channels:
        channel_group_key = group_key(channel.get("group"))
        if channel_group_key == sport_group_key:
            channel["group"] = "THỂ THAO QUỐC TẾ"
        elif channel_group_key in event_group_keys:
            channel["group"] = "Sự kiện"
            channel["skip_event_filter"] = True
    return channels


def collect_mytv_fpt_events():
    source = "MyTVFPTEvents"
    primary_channels = collect_m3u_playlist(
        source,
        MYTV_FPT_EVENTS_M3U_URL,
        source,
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        allowed_groups=("su kien fpt play",),
        default_referer_to_playlist=False,
        user_agent="",
        preserve_extinf=True,
    )

    supplement_channels = collect_m3u_playlist(
        source,
        LKVN_FPT_EVENTS_M3U_URL,
        source,
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        allowed_groups=("su kien",),
        default_referer_to_playlist=False,
        user_agent="",
        preserve_extinf=True,
    )

    channels = []
    seen_urls = set()
    for channel in primary_channels + supplement_channels:
        name_key = text_key(channel.get("name"))
        stream_key = clean_text(channel.get("stream_url")).lower()
        is_fpt_event = (
            "fpt" in name_key
            or "/live/media/event-" in stream_key
            or "/live/media/su-kien-" in stream_key
        )
        if not is_fpt_event:
            continue
        if stream_key in seen_urls:
            continue
        seen_urls.add(stream_key)
        channel["source"] = source
        channel["group"] = source
        channel["skip_event_filter"] = True
        channels.append(channel)
    return channels


def collect_thethaocoban():
    return collect_m3u_playlist(
        "TheThaoCoBan",
        THETHAOCOBAN_M3U_URL,
        "TheThaoCoBan",
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        default_referer_to_playlist=False,
        user_agent="",
        preserve_extinf=True,
        preserve_group_exact=True,
    )


def collect_cloudok_premier_league():
    return collect_m3u_playlist(
        "CloudOKPremierLeague",
        CLOUDOK_M3U_URL,
        "PREMIER LEAGUE",
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        allowed_groups=("premier league",),
        default_referer_to_playlist=False,
        user_agent="",
        preserve_extinf=True,
        request_headers={
            "Accept": "text/plain,application/octet-stream,*/*",
            "Cache-Control": "no-cache",
            "X-Auth-Token": CLOUDOK_AUTH_TOKEN,
        },
    )


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


def collect_dekiki_sports():
    source = "DekikiSports"
    channels = collect_m3u_playlist(
        source,
        DEKIKI_M3U_URL,
        SPORT_INTERNATIONAL_GROUP,
        referer="",
        preserve_group=True,
        allow_non_m3u8=True,
        timeout=60,
        retries=3,
        allowed_groups=("bong da anh", "the thao quoc te"),
        default_referer_to_playlist=False,
        user_agent="",
        preserve_extinf=True,
    )
    for channel in channels:
        channel["group"] = SPORT_INTERNATIONAL_GROUP
        channel["raw_extinf"] = set_extinf_group_title(channel.get("raw_extinf", ""), SPORT_INTERNATIONAL_GROUP)
    log(f"[{source}] {len(channels)} selected links")
    return channels


def mebong_headers(base_url, referer=None, accept="application/json, text/plain, */*"):
    base_url = base_url.rstrip("/") + "/"
    return {
        "Accept": accept,
        "Origin": base_url.rstrip("/"),
        "Referer": referer or base_url,
        "User-Agent": UA,
    }


def extract_mebong_embed_src(page_html):
    patterns = [
        r'<iframe[^>]+id=["\']iframe-stream["\'][^>]+src=["\']([^"\']+)',
        r'src=["\']([^"\']*/?api/hls-embed\?[^"\']+)',
        r'["\'](/api/hls-embed\?[^"\']+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html or "", re.I | re.S)
        if match:
            return html.unescape(match.group(1))
    return ""


def mebong_original_stream_url(embed_src):
    parsed = urlparse(html.unescape(embed_src or ""))
    query = parse_qs(parsed.query)
    stream_values = query.get("u") or query.get("url")
    if not stream_values:
        match = re.search(r"[?&](?:u|url)=([^&\"']+)", embed_src or "")
        if not match:
            return ""
        return clean_text(unquote(match.group(1)))
    return clean_text(stream_values[0])


def mebong_all_matches(data):
    if not isinstance(data, dict):
        return []
    result = []
    seen = set()

    def add_items(items):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            key = clean_text(item.get("href") or item.get("slug") or item.get("fid") or item.get("text"))
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(item)

    add_items(data.get("matches"))
    for items in (data.get("matchesBySport") or {}).values():
        add_items(items)
    return result


def fetch_mebong_detail_html(detail_url, base_url):
    headers = mebong_headers(base_url, referer=base_url, accept="text/html,application/xhtml+xml,*/*")
    for attempt in range(1, 4):
        try:
            return fetch_text(detail_url, headers=headers, timeout=25)
        except Exception:
            if attempt == 3:
                return ""
            time.sleep(0.4 * attempt)
    return ""


def collect_mebongtv():
    source = "MebongTV"
    base_url = MEBONG_SITE_URL.rstrip("/") + "/"
    api_url = urljoin(base_url, "api/home-matches")
    log(f"[{source}] Fetch home matches")
    data = fetch_json_no_cache(api_url, headers=mebong_headers(base_url), timeout=30)
    matches = mebong_all_matches(data)
    if not isinstance(matches, list) or not matches:
        log(f"[{source}] 0 matches")
        return []

    channels = []
    seen_urls = set()

    def resolve(item):
        if not isinstance(item, dict):
            return []
        href = clean_text(item.get("href"))
        if not href:
            return []
        detail_url = urljoin(base_url, href)
        page_html = fetch_mebong_detail_html(detail_url, base_url)
        if not page_html:
            return []

        embed_src = extract_mebong_embed_src(page_html)
        original_url = mebong_original_stream_url(embed_src)
        if not is_valid_stream_url(original_url):
            return []
        proxy_url = urljoin(
            base_url,
            "api/hls-proxy?"
            + urlencode(
                {
                    "u": original_url,
                    "ua": MEBONG_PROXY_UA,
                }
            ),
        )

        title = clean_text(item.get("text"))
        home = clean_text(item.get("home"))
        away = clean_text(item.get("away"))
        if not title:
            title = " vs ".join(part for part in (home, away) if part) or "MebongTV"
        league = clean_text(item.get("league"))
        status = clean_text(item.get("status") or item.get("liveLabel") or item.get("matchStatus"))
        commentator = clean_text(item.get("commentator"))
        event_datetime = parse_epoch_to_ict_datetime(item.get("runtime"))
        event_date = event_datetime.date() if event_datetime else date_from_text(item.get("timeLabel"))
        time_label = clean_text(item.get("timeLabel")) or (event_datetime.strftime("%H:%M %d/%m") if event_datetime else "")
        if time_label and title.startswith(time_label):
            title = clean_text(title[len(time_label) :])
        logo = clean_text(item.get("homeLogo") or item.get("awayLogo") or item.get("leagueLogo") or item.get("thumbnailUrl"))
        if logo and not logo.startswith(("http://", "https://")):
            logo = urljoin(base_url, logo)

        suffix_bits = [bit for bit in (league, status, commentator) if bit]
        suffix = f" | {' | '.join(suffix_bits)}" if suffix_bits else ""
        name = f"{f'[{time_label}] ' if time_label else ''}{title}{suffix} [HLS]"
        return [
            {
                "source": source,
                "name": name,
                "group": MEBONG_GROUP,
                "sport": detect_sport(league, title),
                "logo": logo,
                "stream_url": proxy_url,
                "referer": base_url,
                "user_agent": UA,
                "event_date": event_date,
                "event_datetime": event_datetime,
            }
        ]

    limited_matches = matches[: max(1, MEBONG_LIMIT)]
    with ThreadPoolExecutor(max_workers=max(1, MEBONG_WORKERS)) as executor:
        futures = [executor.submit(resolve, item) for item in limited_matches]
        for future in as_completed(futures):
            try:
                for channel in future.result():
                    stream_url = channel.get("stream_url")
                    if stream_url in seen_urls:
                        continue
                    seen_urls.add(stream_url)
                    channels.append(channel)
            except Exception:
                continue

    log(f"[{source}] {len(channels)} raw links")
    return channels


def xoilacz_base_candidates():
    candidates = [
        XOILACZ_SITE_URL,
        "https://xoilacxtv.tv/",
        "https://nmsba.com/",
        "https://xoilacz.io/",
        "https://xoilacz.vip/",
        "https://xoilacxtb.tv/",
        "https://xoilaczzrrz.tv/",
    ]
    seen = set()
    for candidate in candidates:
        base_url = candidate.rstrip("/") + "/"
        if base_url in seen:
            continue
        seen.add(base_url)
        yield base_url


def xoilacz_headers(base_url):
    origin_match = re.match(r"^https?://[^/]+", base_url)
    origin = origin_match.group(0) if origin_match else base_url.rstrip("/")
    return {
        "Accept": "application/json, text/plain, */*",
        "Origin": origin,
        "Referer": base_url,
        "User-Agent": UA,
    }


def extract_xoilacz_url_stream(stream_page_url, headers, detail_url=""):
    candidates = [stream_page_url]
    if "/off-tvc" not in stream_page_url:
        separator = "&" if "?" in stream_page_url else "?"
        candidates.append(f"{stream_page_url.rstrip('/')}/off-tvc{separator}is_off_add=true")
    if "xlz" in stream_page_url:
        candidates.extend([url.replace("xlz", "xl365") for url in list(candidates)])
        candidates.extend([url.replace("xlz", "xl") for url in list(candidates)])

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            request_headers = dict(headers or {})
            if detail_url and "/ajax/chanel/" in candidate:
                detail_origin = re.match(r"^https?://[^/]+", detail_url)
                if detail_origin:
                    request_headers["Origin"] = detail_origin.group(0)
                request_headers["Referer"] = detail_url
            html_text = fetch_text(candidate, headers=request_headers, timeout=25)
        except Exception:
            continue
        match = re.search(r'(?:var|let|const)\s+urlStream\s*=\s*["\']([^"\']+)["\']', html_text)
        if match:
            return clean_text(match.group(1).replace("\\/", "/"))
        ad_urls = set()
        ads_match = re.search(r"var\s+adsTvc\s*=\s*(\[[\s\S]*?\]);", html_text)
        if ads_match:
            try:
                ads = json.loads(ads_match.group(1))
                for ad in ads:
                    if isinstance(ad, dict) and ad.get("file"):
                        ad_urls.add(clean_text(str(ad.get("file")).replace("\\/", "/")))
            except Exception:
                pass
        direct_urls = [
            clean_text(match.group(0).replace("\\/", "/"))
            for match in re.finditer(r'https?://[^"\']+\.(?:m3u8|flv)(?:\?[^"\']*)?', html_text)
        ]
        real_urls = [url for url in direct_urls if url not in ad_urls]
        if real_urls:
            return real_urls[0]
        if direct_urls:
            return direct_urls[-1]
        src_match = re.search(r'(?:source|file)\s*[:=]\s*["\'](https?://[^"\']+)["\']', html_text, re.I)
        if src_match:
            return clean_text(src_match.group(1).replace("\\/", "/"))
    return ""


def extract_xoilacz_stream_links(detail_url, headers):
    try:
        html_text = fetch_text(detail_url, headers=headers, timeout=25)
    except Exception:
        return []
    match = re.search(r"var\s+list_stream\s*=\s*(\[.*?\]);", html_text, re.S)
    if not match:
        return []
    try:
        list_stream = json.loads(match.group(1))
    except Exception:
        return []

    stream_urls = []
    for item in list_stream:
        if not isinstance(item, list) or not item:
            continue
        stream_page_url = clean_text(str(item[0]).replace("\\/", "/"))
        if not stream_page_url.startswith(("http://", "https://")):
            continue
        stream_url = extract_xoilacz_url_stream(stream_page_url, headers, detail_url) or stream_page_url
        if is_valid_xoilacz_stream_url(stream_url) and stream_url not in stream_urls:
            stream_urls.append(stream_url)
    return stream_urls


def extract_xoilacz_match_blocks(html_text):
    blocks = re.findall(
        r'(<div\s+class="grid-matches__item[^>]*grid-matches__item-match.*?)(?=<div\s+class="grid-matches__item|\Z)',
        html_text,
        re.S,
    )
    if blocks:
        return blocks
    fallback_blocks = []
    for match in re.finditer(r'<a[^>]+href="([^"]+)"[^>]+title="([^"]*)"', html_text, re.S):
        anchor = match.group(0)
        href = match.group(1)
        if "truc-tiep" not in href and "live" not in href:
            continue
        fallback_blocks.append(anchor)
    return fallback_blocks


def collect_xoilacz():
    source = "XoiLacZ"
    channels = []
    seen_urls = set()

    def collect_match(block):
        blv_match = re.search(r"number-blv-(\d+)", block)
        if blv_match and int(blv_match.group(1)) <= 0:
            return []
        link_match = re.search(
            r'<a[^>]+class="[^"]*redirectPopup[^"]*"[^>]+href="([^"]+)"[^>]+title="([^"]*)"',
            block,
            re.S,
        )
        if not link_match:
            link_match = re.search(
                r'<a[^>]+href="([^"]+)"[^>]+title="([^"]*)"[^>]+class="[^"]*redirectPopup[^"]*"',
                block,
                re.S,
            )
        if not link_match:
            link_match = re.search(r'<a[^>]+href="([^"]+)"[^>]+title="([^"]*)"', block, re.S)
        if not link_match:
            return []

        href = clean_text(link_match.group(1))
        title = clean_text(html.unescape(link_match.group(2)))
        detail_url = urljoin(base_url, href)
        match_channels = []
        for idx, stream_url in enumerate(extract_xoilacz_stream_links(detail_url, headers), 1):
            quality = "FLV" if is_flv_url(stream_url) else "HLS"
            match_channels.append(
                {
                    "source": source,
                        "name": f"{title} | Link {idx} [{quality}]",
                        "group": "Xôi Lạc Z TV",
                        "logo": "",
                        "stream_url": stream_url,
                        "referer": xoilacz_stream_referer(stream_url),
                        "user_agent": FLV_OTT_USER_AGENT,
                    }
                )
        return match_channels

    for base_url in xoilacz_base_candidates():
        headers = xoilacz_headers(base_url)
        before_base = len(channels)
        for sport in XOILACZ_SPORTS:
            for page in range(max(1, XOILACZ_PAGES)):
                url = f"{base_url.rstrip('/')}/sport/{sport}/load-more/home/page/{page}/per/20?t={int(time.time())}"
                log(f"[{source}] Fetch {base_url} {sport} page {page}")
                data = fetch_json(url, headers=headers, timeout=18)
                html_text = ((data.get("data") or {}).get("html") or "") if isinstance(data, dict) else ""
                if not html_text:
                    break

                blocks = extract_xoilacz_match_blocks(html_text)
                with ThreadPoolExecutor(max_workers=6) as executor:
                    futures = [executor.submit(collect_match, block) for block in blocks]
                    for future in as_completed(futures):
                        try:
                            match_channels = future.result()
                        except Exception:
                            continue
                        for channel in match_channels:
                            stream_url = channel.get("stream_url")
                            if stream_url in seen_urls:
                                continue
                            seen_urls.add(stream_url)
                            channels.append(channel)
                time.sleep(0.5)
        if len(channels) == before_base:
            for path in ("", "truc-tiep/"):
                page_url = urljoin(base_url, path)
                log(f"[{source}] Fetch fallback {page_url}")
                try:
                    html_text = fetch_text(page_url, headers=headers, timeout=18)
                except Exception as exc:
                    log(f"[{source}] Fallback error {page_url}: {exc}")
                    continue
                blocks = extract_xoilacz_match_blocks(html_text)
                if not blocks:
                    continue
                with ThreadPoolExecutor(max_workers=6) as executor:
                    futures = [executor.submit(collect_match, block) for block in blocks]
                    for future in as_completed(futures):
                        try:
                            match_channels = future.result()
                        except Exception:
                            continue
                        for channel in match_channels:
                            stream_url = channel.get("stream_url")
                            if stream_url in seen_urls:
                                continue
                            seen_urls.add(stream_url)
                            channels.append(channel)
                if len(channels) > before_base:
                    break
        if len(channels) > before_base:
            break

    log(f"[{source}] {len(channels)} raw links")
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

S8TV_TITLE_URL_RE = re.compile(
    r'\\"title\\":\\"((?:\\\\.|[^\\"])*)\\"(?:(?!\\"title\\":).){0,4000}?'
    r'\\"(?:link_m3u8|videoUrl)\\":\\"((?:\\\\.|[^\\"])*)\\"',
    re.S,
)
S8TV_PLACEHOLDER_RE = re.compile(r'\\"link_video_placeholder\\":\\"((?:\\\\.|[^\\"])*)\\"')
S8TV_M3U8_RE = re.compile(r"https?://[^\s'\"<>\\]+?\.m3u8[^\s'\"<>\\]*")
VSC9_M3U8_RE = re.compile(
    r"https?://(?:(?!https?://)[^\s'\"<>{}\\,\]])+?\.m3u8"
    r"(?:\?(?:(?!https?://)[^\s'\"<>{}\\,\]])*)?",
    re.I,
)
VSC9_TIME_RE = re.compile(r"(\d{1,2}:\d{2}\s+\d{1,2}/\d{1,2})")


def decode_json_string(value):
    try:
        return json.loads(f'"{value}"')
    except Exception:
        return value.replace("\\/", "/").replace('\\"', '"')


def extract_vsc9_m3u8_urls(text):
    text = html.unescape(decode_json_string(clean_text(text)))
    urls = []
    seen = set()
    for match in VSC9_M3U8_RE.finditer(text):
        url = clean_text(match.group(0)).rstrip(".,);]")
        if is_valid_stream_url(url) and url not in seen:
            seen.add(url)
            urls.append(url)

    url_set = set(urls)
    preferred = []
    for url in urls:
        master_url = re.sub(r"/ffmpeg_index_\d+\.m3u8(?:\?.*)?$", "/master.m3u8", url, flags=re.I)
        if master_url != url and master_url in url_set:
            continue
        preferred.append(url)
    return preferred


def title_from_stream_url(url, prefix):
    path = unquote(url.split("?", 1)[0]).strip("/")
    parts = [part for part in path.split("/") if part and part.lower() != "master.m3u8"]
    label = parts[-1] if parts else prefix
    label = label.replace("+", " ").replace("_", " ").replace("-", " ")
    label = re.sub(r"\s+", " ", label).strip()
    return f"{prefix} {label}".strip()


def escaped_json_field(context, field):
    matches = re.findall(rf'{re.escape(field)}\\":\\"((?:\\\\.|[^\\"])*)\\"', context)
    return clean_text(decode_json_string(matches[-1])) if matches else ""


def title_from_html_page(html_text, fallback):
    patterns = [
        r"<h1[^>]*>(.*?)</h1>",
        r'property="og:title"\s+content="([^"]+)"',
        r"<title>(.*?)</title>",
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, re.I | re.S)
        if not match:
            continue
        title = re.sub(r"<.*?>", " ", match.group(1))
        title = clean_text(html.unescape(title))
        title = re.sub(r"\s+-\s+Xoilacz\.TV\s*$", "", title, flags=re.I)
        if title:
            return title
    return fallback


def azabu_headers(referer=None):
    base_url = AZABU_BASE_URL.rstrip("/") + "/"
    return {
        "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        "Origin": base_url.rstrip("/"),
        "Referer": referer or base_url,
        "User-Agent": UA,
    }


def collect_azabu_live():
    source = "AzabuLive"
    base_url = AZABU_BASE_URL.rstrip("/") + "/"
    log(f"[{source}] Fetch home")
    try:
        html_text = fetch_text(base_url, headers=azabu_headers(), timeout=30)
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []

    detail_urls = []
    for match in re.finditer(r'href="(/truc-tiep/[^"]+?/link/\d+)"', html_text, re.I):
        detail_url = urljoin(base_url, re.sub(r"/link/\d+/?$", "/", match.group(1)))
        if detail_url not in detail_urls:
            detail_urls.append(detail_url)
    detail_urls = detail_urls[: max(1, AZABU_LIVE_LIMIT)]

    def collect_detail(detail_url):
        try:
            detail_html = fetch_text(detail_url, headers=azabu_headers(detail_url), timeout=25)
        except Exception:
            return []
        title = title_from_html_page(detail_html, "Azabu Live")
        stream_urls = extract_xoilacz_stream_links(detail_url, azabu_headers(detail_url))
        result = []
        for idx, stream_url in enumerate(stream_urls, 1):
            quality = "FLV" if is_flv_url(stream_url) else "HLS"
            result.append(
                {
                    "source": source,
                    "name": f"{title} | Link {idx} [{quality}]",
                    "group": "Azabu Live",
                    "logo": "",
                    "stream_url": stream_url,
                    "referer": AZABU_BASE_URL.rstrip("/") + "/",
                    "user_agent": FLV_OTT_USER_AGENT if is_flv_url(stream_url) else UA,
                }
            )
        return result

    channels = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(collect_detail, detail_url) for detail_url in detail_urls]
        for future in as_completed(futures):
            try:
                channels.extend(future.result())
            except Exception:
                continue

    log(f"[{source}] {len(channels)} raw links")
    return channels


def collect_azabu_highlights():
    source = "AzabuHighlight"
    base_url = AZABU_BASE_URL.rstrip("/") + "/"
    highlight_url = urljoin(base_url, "highlight/")
    post_urls = []

    for page in range(1, max(1, AZABU_HIGHLIGHT_PAGES) + 1):
        page_url = highlight_url if page == 1 else urljoin(highlight_url, f"page/{page}/")
        log(f"[{source}] Fetch page {page}")
        try:
            html_text = fetch_text(page_url, headers=azabu_headers(page_url), timeout=30)
        except Exception:
            continue
        for match in re.finditer(r"https://azabuglobal\.com/highlight/[^\s'\"<>]+/", html_text, re.I):
            post_url = match.group(0)
            if "/page/" not in post_url and post_url not in post_urls:
                post_urls.append(post_url)

    def collect_post(post_url):
        try:
            html_text = fetch_text(post_url, headers=azabu_headers(post_url), timeout=25)
        except Exception:
            return []
        title = title_from_html_page(html_text, "Azabu Highlight")
        logo_match = re.search(r'property="og:image"\s+content="([^"]+)"', html_text, re.I)
        logo = logo_match.group(1) if logo_match else ""
        stream_urls = []
        for match in re.finditer(r"https?://[^\s'\"<>\\]+?\.m3u8[^\s'\"<>\\]*", html_text, re.I):
            stream_url = clean_text(match.group(0).replace("\\/", "/").replace("\\u0026", "&"))
            if is_valid_stream_url(stream_url) and stream_url not in stream_urls:
                stream_urls.append(stream_url)
        return [
            {
                "source": source,
                "name": title,
                "group": "Highlight | Azabu Global",
                "logo": logo,
                "stream_url": stream_url,
                "referer": post_url,
                "user_agent": UA,
            }
            for stream_url in stream_urls
        ]

    channels = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(collect_post, post_url) for post_url in post_urls]
        for future in as_completed(futures):
            try:
                channels.extend(future.result())
            except Exception:
                continue

    log(f"[{source}] {len(channels)} raw links")
    return channels


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
        content = getattr(r, "content", None)
        if content is not None:
            return content.decode("utf-8", errors="replace")
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
    site_url = S8TV_SITE_URL.rstrip("/") + "/"
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
    for stream_url in extract_vsc9_m3u8_urls(html_text):
        if not is_valid_stream_url(stream_url) or stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)
        title, time_label = vsc9_title_from_context(html_text, stream_url)
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
    data = fetch_json_no_cache(api_url, headers=headers, timeout=25)
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
        response = request_get_no_cache(f"{api_base}/matches/graph", headers=headers, timeout=25)
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
            live = fetch_json_no_cache(f"{api_base}/match/{match_id}/live", headers=headers, timeout=20)
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


def decode_cdnlive_base64(value):
    value = clean_text(value).replace("-", "+").replace("_", "/")
    if not value:
        return ""
    value += "=" * ((4 - len(value) % 4) % 4)
    try:
        return base64.b64decode(value).decode("utf-8", errors="replace")
    except Exception:
        return ""


def resolve_cdnlive_playlist(player_url):
    player_url = clean_text(player_url)
    if not player_url:
        return ""
    headers = {
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
        "Referer": CDNLIVE_REFERER,
        "Origin": CDNLIVE_REFERER.rstrip("/"),
    }
    try:
        response = request_get(player_url, headers=headers, timeout=20)
    except Exception as exc:
        log(f"[CDNLive] Player error {player_url}: {exc}")
        return ""
    if response.status_code != 200:
        log(f"[CDNLive] Player HTTP {response.status_code} {player_url}")
        return ""
    page = response.text
    source_match = re.search(r"source\s*:\s*\{\s*src\s*:\s*([A-Za-z0-9_$]+)\s*,\s*format", page)
    if not source_match:
        return ""
    source_var = source_match.group(1)
    assign_match = re.search(r"var\s+" + re.escape(source_var) + r"\s*=\s*(.*?);", page, re.S)
    if not assign_match:
        return ""
    assign_expr = assign_match.group(1)
    fn_match = re.search(r"([A-Za-z0-9_$]+)\s*\(", assign_expr)
    if not fn_match:
        return ""
    decode_fn = fn_match.group(1)
    refs = re.findall(re.escape(decode_fn) + r"\s*\(\s*([A-Za-z0-9_$]+)\s*\)", assign_expr)
    if not refs:
        return ""
    values = {
        name: value
        for name, _, value in re.findall(r"""var\s+([A-Za-z0-9_$]+)\s*=\s*(["'])(.*?)\2""", page, re.S)
    }
    playlist_url = "".join(decode_cdnlive_base64(values.get(ref, "")) for ref in refs)
    return playlist_url if is_valid_stream_url(playlist_url) else ""


def collect_cdnlive():
    source = "CDNLive"
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "Origin": CDNLIVE_REFERER.rstrip("/"),
        "Referer": CDNLIVE_REFERER,
    }
    log(f"[{source}] Fetch events")
    data = fetch_json_no_cache(CDNLIVE_EVENTS_URL, headers=headers, timeout=45)
    root = data.get("cdn-live-tv") if isinstance(data, dict) else {}
    if not isinstance(root, dict):
        return []

    candidates = []
    seen_player_urls = set()
    for sport_name, events in root.items():
        if not isinstance(events, list):
            continue
        for event in events:
            if not isinstance(event, dict):
                continue
            event_title = clean_text(event.get("event"))
            start_text = clean_text(event.get("start") or event.get("time"))
            tournament = clean_text(event.get("tournament") or event.get("country"))
            event_datetime = parse_utc_text_to_ict_datetime(event.get("start")) or datetime_from_text(start_text)
            event_date = event_datetime.date() if event_datetime else date_from_text(start_text)
            time_label = event_datetime.strftime("%H:%M %d/%m") if event_datetime else start_text
            logo = clean_text(event.get("homeTeamIMG") or event.get("awayTeamIMG") or event.get("countryIMG"))
            for channel in event.get("channels") or []:
                if not isinstance(channel, dict):
                    continue
                player_url = clean_text(channel.get("url"))
                if not player_url or player_url in seen_player_urls:
                    continue
                seen_player_urls.add(player_url)
                channel_name = clean_text(channel.get("channel_name") or channel.get("name") or "CDNLive")
                candidates.append(
                    {
                        "event_title": event_title,
                        "start_text": start_text,
                        "time_label": time_label,
                        "tournament": tournament,
                        "sport_name": clean_text(sport_name),
                        "event_date": event_date,
                        "event_datetime": event_datetime,
                        "logo": clean_text(channel.get("image")) or logo,
                        "channel_name": channel_name,
                        "player_url": player_url,
                    }
                )
                if len(candidates) >= CDNLIVE_LIMIT:
                    break
            if len(candidates) >= CDNLIVE_LIMIT:
                break
        if len(candidates) >= CDNLIVE_LIMIT:
            break

    channels = []
    seen_streams = set()

    def resolve(candidate):
        stream_url = resolve_cdnlive_playlist(candidate["player_url"])
        if not stream_url:
            return None
        start_prefix = f"[{candidate['time_label']}] " if candidate["time_label"] else ""
        tournament_suffix = f" | {candidate['tournament']}" if candidate["tournament"] else ""
        return {
            "source": source,
            "name": f"{start_prefix}{candidate['event_title']} - {candidate['channel_name']}{tournament_suffix}",
            "group": CDNLIVE_GROUP,
            "sport": detect_sport(candidate["sport_name"], candidate["tournament"], candidate["event_title"]),
            "logo": candidate["logo"],
            "stream_url": stream_url,
            "referer": CDNLIVE_REFERER,
            "user_agent": UA,
            "event_date": candidate["event_date"],
            "event_datetime": candidate["event_datetime"],
        }

    with ThreadPoolExecutor(max_workers=max(1, CDNLIVE_WORKERS)) as executor:
        futures = [executor.submit(resolve, candidate) for candidate in candidates]
        for future in as_completed(futures):
            channel = future.result()
            if not channel:
                continue
            stream_url = channel["stream_url"]
            if stream_url in seen_streams:
                continue
            seen_streams.add(stream_url)
            channels.append(channel)

    log(f"[{source}] {len(channels)} raw links")
    return channels


def parse_tivihub_matches_m3u(text):
    matches = []
    current = {}
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', line))
            title = line.split(",", 1)[1].strip() if "," in line else attrs.get("match-name", "")
            current = {
                "id": clean_text(attrs.get("match-id") or attrs.get("tvg-id")),
                "title": clean_text(title or attrs.get("match-name")),
                "group": clean_text(attrs.get("group-title") or attrs.get("group")),
                "status": clean_text(attrs.get("match-status")),
                "league": clean_text(attrs.get("league-name")),
                "timestamp": clean_text(attrs.get("match-timestamp")),
                "logo": clean_text(attrs.get("localteam-logo") or attrs.get("visitorteam-logo")),
            }
            continue
        if line.startswith("http") and current.get("id"):
            matches.append(dict(current))
            current = {}
            if len(matches) >= TIVIHUB_LIMIT:
                break
    return matches


def collect_tivihub():
    source = "Tivihub"
    headers = {
        "Accept": "application/json,text/plain,*/*",
        "Referer": TIVIHUB_REFERER,
        "Origin": TIVIHUB_REFERER.rstrip("/"),
    }
    log(f"[{source}] Fetch M3U")
    try:
        response = request_get_no_cache(TIVIHUB_M3U_URL, headers={"Accept": "*/*"}, timeout=45)
        log(f"[{source}] HTTP {response.status_code}")
        if response.status_code != 200:
            return []
    except Exception as exc:
        log(f"[{source}] Error: {exc}")
        return []

    matches = parse_tivihub_matches_m3u(response.text)
    if not matches:
        log(f"[{source}] 0 matches")
        return []

    channels = []
    seen_streams = set()

    def resolve(match):
        match_id = match.get("id")
        if not match_id:
            return []
        detail_url = TIVIHUB_API_BASE_URL.rstrip("/") + "/" + match_id
        data = fetch_json_no_cache(detail_url, headers=headers, timeout=20)
        detail = data.get("data") if isinstance(data, dict) else {}
        if not isinstance(detail, dict):
            return []
        title = clean_text(detail.get("name") or match.get("title") or source)
        league = clean_text(detail.get("league_name") or match.get("league"))
        status = clean_text(detail.get("status") or match.get("status"))
        group_name = clean_text(match.get("group") or "LIVE")
        logo = clean_text(detail.get("localteam_logo") or detail.get("visitorteam_logo") or match.get("logo"))
        referer = clean_text(detail.get("referer")) or TIVIHUB_REFERER
        event_datetime = parse_epoch_to_ict_datetime(detail.get("timestamp") or detail.get("start_at") or match.get("timestamp"))
        event_date = event_datetime.date() if event_datetime else None
        time_label = event_datetime.strftime("%H:%M %d/%m") if event_datetime else ""
        results = []
        for stream in detail.get("link_live") or []:
            if not isinstance(stream, dict):
                continue
            stream_url = clean_text(stream.get("stream_link"))
            if not is_valid_stream_url(stream_url):
                continue
            quality = clean_text(stream.get("display_name") or stream.get("stream_name") or "HD")
            line = clean_text(stream.get("line"))
            suffix_bits = [bit for bit in (league, status, line) if bit]
            suffix = f" | {' | '.join(suffix_bits)}" if suffix_bits else ""
            results.append(
                {
                    "source": source,
                    "name": f"{f'[{time_label}] ' if time_label else ''}{title} [{quality}]{suffix}",
                    "group": f"{TIVIHUB_GROUP_PREFIX} - {group_name}",
                    "sport": detect_sport(group_name, league, title),
                    "logo": logo,
                    "stream_url": stream_url,
                    "referer": referer,
                    "user_agent": UA,
                    "event_date": event_date,
                    "event_datetime": event_datetime,
                }
            )
        return results

    with ThreadPoolExecutor(max_workers=max(1, TIVIHUB_WORKERS)) as executor:
        futures = [executor.submit(resolve, match) for match in matches]
        for future in as_completed(futures):
            for channel in future.result():
                stream_url = channel["stream_url"]
                if stream_url in seen_streams:
                    continue
                seen_streams.add(stream_url)
                channels.append(channel)

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
        ("BiaomTV", collect_biaom),
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
                TINHLAGI_SPORT_M3U_URL,
                "Tinh La Gi",
                preserve_group=True,
                allow_non_m3u8=True,
                timeout=60,
                retries=3,
                default_referer_to_playlist=False,
                user_agent="",
                preserve_extinf=True,
                preserve_group_exact=True,
            ),
        ),
        ("GioVang", collect_giovang_api),
        ("PhaoHoaTV", collect_phaohoa),
        ("ChoangTV", collect_choangtv_api),
        ("SocoliveTV", collect_socolive),
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
        ("MyTVFPTEvents", collect_mytv_fpt_events),
        ("CloudOKPremierLeague", collect_cloudok_premier_league),
        ("CuongHeHe", collect_cuonghehe),
        ("CuongHeHe4K", collect_tt1_4k),
        ("CoTiViSports", collect_cotivi_sports),
        ("DekikiSports", collect_dekiki_sports),
        ("MebongTV", collect_mebongtv),
        ("XoiLacZ", collect_xoilacz),
        ("AzabuLive", collect_azabu_live),
        ("AzabuHighlight", collect_azabu_highlights),
        (
            "TV365KidsInternational",
            lambda: collect_m3u_playlist(
                "TV365KidsInternational",
                TV365_ERROR_M3U_URL,
                "TV365",
                preserve_group=True,
                allow_non_m3u8=True,
                timeout=60,
                retries=3,
                allowed_groups=("thieu nhi", "quoc te"),
                default_referer_to_playlist=False,
                user_agent="",
                preserve_extinf=True,
            ),
        ),
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
        ("BongLauTV", collect_bonglau),
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

    all_channels = filter_current_and_future_events(all_channels)
    deduped_with_ott = dedupe_and_sort_channels(all_channels)
    deduped, _flv_channels = split_ott_channels(deduped_with_ott)
    ott_deduped = select_ott_compatible_channels(deduped_with_ott)
    write_m3u(ALL_M3U, deduped)

    write_ott_m3u(OTT_M3U, ott_deduped)
    tinhlagi_raw_count = write_raw_playlist(TINHLAGI_M3U, "TinhLaGiRaw", TINHLAGI_SPORT_M3U_URL)
    thethaocoban_raw_count = write_raw_playlist(THETHAOCOBAN_M3U, "TheThaoCoBanRaw", THETHAOCOBAN_M3U_URL)

    log("")
    log(f"[DONE] Total unique links: {len(deduped)}")
    log(f"[DONE] OTT unique links: {len(ott_deduped)}")
    log(f"[DONE] TinhLaGi raw links: {tinhlagi_raw_count}")
    log(f"[DONE] TheThaoCoBan raw links: {thethaocoban_raw_count}")
    for source_name, count in per_source_counts.items():
        log(f"[DONE] {source_name}: {count}")
    log(f"[DONE] M3U: {ALL_M3U}")
    log(f"[DONE] OTT M3U: {OTT_M3U}")
    log(f"[DONE] TINHLAGI M3U: {TINHLAGI_M3U}")
    log(f"[DONE] THETHAOCOBAN M3U: {THETHAOCOBAN_M3U}")


if __name__ == "__main__":
    main()

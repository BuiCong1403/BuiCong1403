import html
import json
import os
import re
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
ALL_M3U = BASE_DIR / "all.m3u"
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

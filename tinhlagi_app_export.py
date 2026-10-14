import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_M3U = BASE_DIR / os.environ.get("TINHLAGI_APP_OUTPUT", "tinhlagi_app.m3u")
ACCESS_API = os.environ.get("TINHLAGI_APP_ACCESS_API", "https://tinhlagi.pro/getlink/access-api.php")
SOURCES_API = os.environ.get("TINHLAGI_APP_SOURCES_API", "https://tinhlagi.pro/getlink/sources.php")
ACTIVATION_CODE = os.environ.get("TINHLAGI_APP_ACTIVATION_CODE", "tinhlagipro")
PACKAGE_NAME = os.environ.get("TINHLAGI_APP_PACKAGE", "app.tinhlagi.pro")
ANDROID_ID = os.environ.get("TINHLAGI_APP_ANDROID_ID", "github-actions")
VERSION_CODE = int(os.environ.get("TINHLAGI_APP_VERSION_CODE", "523") or "523")
USER_AGENT = os.environ.get("TINHLAGI_APP_UA", "Dalvik/2.1.0")
EXCLUDE_IDS = {
    item.strip().lower()
    for item in os.environ.get("TINHLAGI_APP_EXCLUDE_IDS", "tv").split(",")
    if item.strip()
}
TIMEOUT = int(os.environ.get("TINHLAGI_APP_TIMEOUT", "35") or "35")


def now_ict():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M ICT")


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def device_id():
    return hashlib.sha256(f"{PACKAGE_NAME}:{ANDROID_ID}".encode("utf-8")).hexdigest()


def post_json(url, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT},
        method="POST",
    )
    with urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8-sig", errors="replace"))


def fetch_text(url, headers=None):
    request = Request(url, headers=headers or {"User-Agent": USER_AGENT})
    with urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def normalize_sources(payload):
    if isinstance(payload, dict) and isinstance(payload.get("sources"), list):
        data = payload.get("sources")
    else:
        data = payload.get("data") if isinstance(payload, dict) else payload
    if isinstance(data, dict) and isinstance(data.get("sources"), list):
        data = data.get("sources")
    if isinstance(data, dict):
        rows = list(data.values())
    elif isinstance(data, list):
        rows = data
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict) and row.get("url")]


def get_sources():
    dev = device_id()
    auth = post_json(
        ACCESS_API,
        {
            "device": dev,
            "versionCode": VERSION_CODE,
            "action": "activate",
            "code": ACTIVATION_CODE,
        },
    )
    token = (
        auth.get("token")
        or auth.get("accessToken")
        or (auth.get("data") or {}).get("token")
        or (auth.get("data") or {}).get("accessToken")
    )
    if not token:
        raise RuntimeError(f"Activation failed: {auth}")
    request = Request(
        SOURCES_API,
        headers={
            "User-Agent": USER_AGENT,
            "X-Device": dev,
            "X-Access-Token": token,
        },
    )
    with urlopen(request, timeout=TIMEOUT) as response:
        return normalize_sources(json.loads(response.read().decode("utf-8-sig", errors="replace")))


def strip_extm3u(text):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return "\n".join(line for line in lines if line.strip() and line.strip().upper() != "#EXTM3U").strip()


def main():
    blocks = []
    counts = {}
    for source in get_sources():
        source_id = clean_text(source.get("id")).lower()
        source_name = clean_text(source.get("name")) or source_id or "Tinhlagi"
        if source_id in EXCLUDE_IDS or source_name.lower() in EXCLUDE_IDS:
            continue
        text = strip_extm3u(fetch_text(source["url"]))
        if not text:
            continue
        count = text.count("#EXTINF")
        counts[source_name] = count
        blocks.append(f"# Source: {source_name} ({source_id})\n{text}")

    total = sum(counts.values())
    output = [
        "#EXTM3U",
        f"# Updated : {now_ict()}",
        f"# Total   : {total}",
        "# Exclude : tv",
        "",
    ]
    output.extend(blocks)
    OUTPUT_M3U.write_text("\n\n".join(output).rstrip() + "\n", encoding="utf-8")
    print(f"[DONE] {OUTPUT_M3U.name}: {total} links")
    for name, count in counts.items():
        print(f"[DONE] {name}: {count}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise

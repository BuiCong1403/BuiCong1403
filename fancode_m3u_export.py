import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_M3U = BASE_DIR / os.environ.get("FANCODE_OUTPUT", "fancode.m3u")
DATA_URL = os.environ.get(
    "FANCODE_DATA_URL",
    "https://raw.githubusercontent.com/kajju027/Fancode-Events-Json/refs/heads/main/fancode.json",
)
QUALITY_ORDER = ["1080p", "720p", "540p", "480p", "360p", "240p"]
PREFERRED_QUALITY = os.environ.get("FANCODE_QUALITY", "1080p").strip().lower()
TAKE_ALL_QUALITIES = os.environ.get("FANCODE_ALL_QUALITIES", "0").strip().lower() in {"1", "true", "yes"}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def now_ict():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M ICT")


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def fetch_json(url):
    request = Request(url, headers={"User-Agent": UA, "Accept": "application/json, */*"})
    with urlopen(request, timeout=35) as response:
        return json.loads(response.read().decode("utf-8-sig", errors="replace"))


def valid_url(url):
    return isinstance(url, str) and url.startswith(("http://", "https://")) and ".m3u8" in url.lower()


def pick_streams(match):
    rows = []
    auto = match.get("auto_streams") or {}
    for language, payload in auto.items():
        streams = (payload or {}).get("streams") or {}
        if TAKE_ALL_QUALITIES:
            qualities = [q for q in QUALITY_ORDER if valid_url(streams.get(q))]
        else:
            qualities = [PREFERRED_QUALITY] if valid_url(streams.get(PREFERRED_QUALITY)) else []
            if not qualities:
                qualities = [q for q in QUALITY_ORDER if valid_url(streams.get(q))][:1]
        for quality in qualities:
            rows.append((clean_text(language), quality, streams[quality]))

    primary = ((match.get("streams") or {}).get("primary") or "").strip()
    if valid_url(primary) and not rows:
        rows.append((clean_text(match.get("language")) or "Fancode", "primary", primary))
    return rows


def main():
    data = fetch_json(DATA_URL)
    matches = data.get("matches") if isinstance(data, dict) else []
    blocks = []
    seen = set()
    for match in matches or []:
        title = clean_text(match.get("title")) or "Fancode"
        tournament = clean_text(match.get("tournament"))
        status = clean_text(match.get("status"))
        start = clean_text(match.get("startTime"))
        logo = clean_text(match.get("image"))
        category = clean_text(match.get("category")) or "Fancode"
        group = f"Fancode - {category}"
        for language, quality, url in pick_streams(match):
            if url in seen:
                continue
            seen.add(url)
            name_bits = [title]
            if tournament:
                name_bits.append(tournament)
            if start:
                name_bits.append(start)
            if status:
                name_bits.append(status)
            name_bits.append(f"{language} {quality}".strip())
            name = " | ".join(bit for bit in name_bits if bit)
            blocks.append(
                f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
                f"#EXTVLCOPT:http-user-agent={UA}\n"
                f"{url}"
            )

    output = [
        "#EXTM3U",
        f"# Updated : {now_ict()}",
        f"# Total   : {len(blocks)}",
        "",
        *blocks,
    ]
    OUTPUT_M3U.write_text("\n\n".join(output).rstrip() + "\n", encoding="utf-8")
    print(f"[DONE] {OUTPUT_M3U.name}: {len(blocks)} links")


if __name__ == "__main__":
    main()

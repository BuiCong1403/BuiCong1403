import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "footonsat.m3u"
TZ_VN = timezone(timedelta(hours=7))
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
REFERENCE_M3U_URLS = [
    value.strip()
    for value in os.environ.get(
        "FOOTONSAT_REFERENCE_M3U_URLS",
        "https://raw.githubusercontent.com/Love4vn/Stalker2M3U/refs/heads/1/Mac_playlist.m3u,"
        "https://raw.githubusercontent.com/Love4vn/Stalker2M3U/refs/heads/1/Test.m3u",
    ).split(",")
    if value.strip()
]
REFERENCE_LOCAL_M3US = [
    value.strip()
    for value in os.environ.get(
        "FOOTONSAT_REFERENCE_LOCAL_M3US",
        "",
    ).split(",")
    if value.strip()
]
MAX_MATCHES_PER_CHANNEL = int(os.environ.get("FOOTONSAT_MAX_MATCHES_PER_CHANNEL", "3") or "3")
SOURCES = (
    ("Premier League", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/premierleague.json"),
    ("Serie A", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/seriea.json"),
    ("La Liga", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/laliga.json"),
    ("Bundesliga", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/bundesliga.json"),
    ("Ligue 1", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/ligue1.json"),
    ("Champions League", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/championsleague.json"),
    ("Europa League", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/europaleague.json"),
    ("Conference League", "https://raw.githubusercontent.com/fairbird/footonsat-api/refs/heads/main/ConferenceLeague.json"),
)


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def fetch_json(url, timeout=35):
    request = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json,text/plain,*/*",
            "Cache-Control": "no-cache",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8-sig", errors="replace"))


def fetch_text(url, timeout=60):
    request = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/x-mpegURL,text/plain,*/*",
            "Cache-Control": "no-cache",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def parse_utc_datetime(item):
    raw_date = clean_text(item.get("date"))
    raw_time = clean_text(item.get("time"))
    if not raw_date or not raw_time:
        return None
    try:
        utc_value = datetime.strptime(f"{raw_date} {raw_time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return utc_value.astimezone(TZ_VN)


def collect_source(default_league, url, first_date, last_date):
    payload = fetch_json(url)
    rows = payload.get("footonsat", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return []

    matches = []
    match_by_name = {}
    for row in rows:
        if not isinstance(row, dict):
            continue

        match_name = clean_text(row.get("match"))
        if match_name:
            start_vn = parse_utc_datetime(row)
            if not start_vn or not (first_date <= start_vn.date() <= last_date):
                continue
            match = {
                "league": clean_text(row.get("compet")) or default_league,
                "short_league": default_league,
                "match": match_name,
                "start": start_vn,
                "channels": [],
                "source_url": url,
            }
            matches.append(match)
            match_by_name.setdefault(match_name.casefold(), []).append(match)
            continue

        related_to = clean_text(row.get("related_to"))
        channel_name = clean_text(row.get("channel"))
        if not related_to or not channel_name:
            continue
        candidates = match_by_name.get(related_to.casefold(), [])
        if candidates and channel_name not in candidates[-1]["channels"]:
            candidates[-1]["channels"].append(channel_name)

    return matches


def safe_attribute(value):
    return clean_text(value).replace('"', "'")


def strip_accents(value):
    normalized = unicodedata.normalize("NFKD", clean_text(value).casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_channel_name(value):
    text = strip_accents(value)
    text = re.sub(r"^\s*(?:\|?\s*[a-z]{2,3}\s*\||[a-z]{2,3}\s*[:|-]|┃\s*[a-z]{2,3}\s*┃)\s*", " ", text)
    replacements = {
        "srbija": "serbia",
        "hrvatska": "croatia",
        "slovenija": "slovenia",
        "bih": "bosnia",
        "deutsch": "germany",
        "italia": "italy",
        "espana": "spain",
    }
    for source, target in replacements.items():
        text = re.sub(rf"\b{re.escape(source)}\b", target, text)
    text = re.sub(r"\b(?:hd|uhd|fhd|sd|4k|8k|hevc|raw|vip|tv|channel|live|stream|online|50fps|60fps|ᴴᴰ|ᵁᴴᴰ)\b", " ", text)
    text = text.replace("+", " plus ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_m3u_channels(text, source_name):
    channels = []
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line.startswith("#EXTINF"):
            index += 1
            continue
        attributes = dict(re.findall(r'([\w-]+)="([^"]*)"', line))
        title = line.split(",", 1)[1].strip() if "," in line else clean_text(attributes.get("tvg-name"))
        if not title or "###" in title or re.search(r"[#=☰]", title):
            index += 1
            continue
        normalized_title = normalize_channel_name(title)
        if len(normalized_title.split()) < 2:
            index += 1
            continue
        options = []
        index += 1
        while index < len(lines):
            next_line = lines[index].strip()
            if next_line.startswith(("http://", "https://", "udp://", "rtp://")):
                break
            if next_line.startswith("#EXT") or next_line.startswith("#KODIPROP"):
                options.append(next_line)
            if next_line.startswith("#EXTINF"):
                index -= 1
                break
            index += 1
        if 0 <= index < len(lines):
            stream_url = lines[index].strip()
            if stream_url.startswith(("http://", "https://", "udp://", "rtp://")) and title:
                channels.append(
                    {
                        "name": title,
                        "normalized": normalized_title,
                        "url": stream_url,
                        "options": options,
                        "logo": clean_text(attributes.get("tvg-logo")),
                        "tvg_id": clean_text(attributes.get("tvg-id")),
                        "source": source_name,
                    }
                )
        index += 1
    return channels


def load_reference_channels():
    channels = []
    seen_urls = set()

    def add_channels(text, source_name):
        for channel in parse_m3u_channels(text, source_name):
            if not channel["normalized"] or channel["url"] in seen_urls:
                continue
            seen_urls.add(channel["url"])
            channels.append(channel)

    for local_name in REFERENCE_LOCAL_M3US:
        path = (BASE_DIR / local_name).resolve()
        if not path.exists() or not path.is_file():
            continue
        try:
            add_channels(path.read_text(encoding="utf-8", errors="ignore"), local_name)
            print(f"[FootOnSat] Reference local {local_name}: {len(channels)} kênh cộng dồn")
        except Exception as exc:
            print(f"[FootOnSat] Reference local {local_name}: lỗi {exc}")

    for url in REFERENCE_M3U_URLS:
        try:
            add_channels(fetch_text(url), url)
            print(f"[FootOnSat] Reference URL {url}: {len(channels)} kênh cộng dồn")
        except Exception as exc:
            print(f"[FootOnSat] Reference URL {url}: lỗi {exc}")
    return channels


def build_reference_index(reference_channels):
    index = {}
    for channel in reference_channels:
        for token in set(channel.get("normalized", "").split()):
            index.setdefault(token, []).append(channel)
    return index


def channel_match_score(target, target_tokens, reference):
    candidate = reference.get("normalized", "")
    if not target or not candidate:
        return 0
    if target == candidate:
        return 100
    candidate_tokens = set(candidate.split())
    if not target_tokens:
        return 0
    if target_tokens == candidate_tokens:
        return 96
    if target in candidate or candidate in target:
        return 90
    overlap = target_tokens & candidate_tokens
    if len(overlap) >= 2:
        # Allow minor country/suffix differences, but avoid broad false
        # positives such as "DAZN Formula 1" for "DAZN 1 Italia".
        missing = target_tokens - candidate_tokens
        extra = candidate_tokens - target_tokens
        weak_missing = {"italy", "spain", "serbia", "croatia", "slovenia", "bosnia", "germany", "france", "uk", "us"}
        noisy_extra = {"formula", "f1", "racing", "backup", "test", "news", "movie", "cinema"}
        if missing <= weak_missing and not (extra & noisy_extra):
            return 84
    return 0


def find_reference_matches(target_name, reference_index):
    target = normalize_channel_name(target_name)
    target_tokens = set(target.split())
    if not target_tokens:
        return []
    candidates = []
    seen_candidates = set()
    for token in target_tokens:
        for channel in reference_index.get(token, []):
            marker = id(channel)
            if marker in seen_candidates:
                continue
            seen_candidates.add(marker)
            candidates.append(channel)

    scored = []
    seen = set()
    for channel in candidates:
        score = channel_match_score(target, target_tokens, channel)
        if score < 84 or channel["url"] in seen:
            continue
        seen.add(channel["url"])
        scored.append((score, channel))
    scored.sort(key=lambda item: (-item[0], item[1]["name"].casefold()))
    return [channel for _score, channel in scored[: max(1, MAX_MATCHES_PER_CHANNEL)]]


def build_live_entries(matches, reference_channels):
    entries = []
    seen_per_match = set()
    reference_index = build_reference_index(reference_channels)
    for match_index, match in enumerate(matches, start=1):
        for channel_name in match.get("channels") or []:
            for reference in find_reference_matches(channel_name, reference_index):
                key = (match_index, reference["url"])
                if key in seen_per_match:
                    continue
                seen_per_match.add(key)
                entries.append(
                    {
                        "key": (match_index, match["match"]),
                        "channel": reference["name"],
                        "target_channel": channel_name,
                        "url": reference["url"],
                        "options": reference.get("options") or [],
                        "logo": reference.get("logo") or "",
                        "tvg_id": reference.get("tvg_id") or "",
                        "match": match,
                    }
                )
    return entries


def write_playlist(entries, scheduled_count):
    generated = datetime.now(TZ_VN).strftime("%Y-%m-%d %H:%M ICT")
    matched_games = len({entry["key"] for entry in entries})
    lines = [
        "#EXTM3U",
        f"# Updated : {generated}",
        f"# Total links   : {len(entries)}",
        f"# Total matches : {scheduled_count}",
        "# Lịch FootOnSat: giờ Việt Nam (UTC+7), hôm nay và 2 ngày kế tiếp.",
        "# Dữ liệu lịch/kênh lấy từ JSON FootOnSat; link xem được map từ các M3U tham chiếu.",
        "# Không sinh link no-signal; kênh không match được link thật sẽ bị bỏ qua.",
        "",
    ]
    link_numbers = {}
    for entry in entries:
        match = entry["match"]
        start = match["start"].strftime("%H:%M %d/%m")
        group = f"{start} | {match['match']}"
        link_numbers[entry["key"]] = link_numbers.get(entry["key"], 0) + 1
        title = entry["channel"] or entry.get("target_channel") or f"Link {link_numbers[entry['key']]}"
        attributes = []
        if entry["tvg_id"]:
            attributes.append(f'tvg-id="{safe_attribute(entry["tvg_id"])}"')
        if entry["logo"]:
            attributes.append(f'tvg-logo="{safe_attribute(entry["logo"])}"')
        attributes.append(f'group-title="{safe_attribute(group)}"')
        lines.append(f"#EXTINF:-1 {' '.join(attributes)},{title}")
        lines.extend(entry["options"])
        lines.extend(
            [
                entry["url"],
                "",
            ]
        )
    OUTPUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    today = datetime.now(TZ_VN).date()
    last_date = today + timedelta(days=2)
    matches = []
    failures = []

    for league, url in SOURCES:
        try:
            selected = collect_source(league, url, today, last_date)
            print(f"[FootOnSat] {league}: {len(selected)} trận")
            matches.extend(selected)
        except Exception as exc:
            failures.append(league)
            print(f"[FootOnSat] {league}: lỗi {exc}")

    matches.sort(key=lambda item: (item["start"], item["short_league"], item["match"].casefold()))
    reference_channels = load_reference_channels()
    entries = build_live_entries(matches, reference_channels)
    entries.sort(
        key=lambda item: (
            item["match"]["start"],
            item["match"]["short_league"],
            item["match"]["match"].casefold(),
            item["channel"].casefold(),
        )
    )
    write_playlist(entries, len(matches))
    print(
        f"[DONE] FootOnSat: {len(entries)} link xem được, {len(matches)} trận "
        f"từ {today:%d/%m} đến {last_date:%d/%m}"
    )
    print(f"[DONE] M3U: {OUTPUT_PATH}")
    if failures:
        print(f"[WARN] Nguồn lỗi tạm thời: {', '.join(failures)}")


if __name__ == "__main__":
    main()

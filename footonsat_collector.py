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
LIVE_PLAYLIST_URL = os.environ.get(
    "FOOTONSAT_LIVE_PLAYLIST_URL",
    "https://raw.githubusercontent.com/Love4vn/Match_Stream/refs/heads/1/live_schedule_Optimize.m3u",
).strip()

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


def fetch_text(url, timeout=45):
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


def normalize_team(value):
    value = unicodedata.normalize("NFKD", clean_text(value).casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"\b(fc|afc|cf|calcio|football club)\b", " ", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def match_key(match_name, event_date):
    teams = re.split(r"\s+(?:vs\.?|v)\s+", clean_text(match_name), maxsplit=1, flags=re.I)
    if len(teams) != 2:
        return None
    normalized = tuple(sorted((normalize_team(teams[0]), normalize_team(teams[1]))))
    if not all(normalized):
        return None
    return event_date.strftime("%d/%m"), normalized


def parse_live_playlist(text):
    entries = []
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    index = 0
    while index < len(lines):
        extinf = lines[index].strip()
        if not extinf.startswith("#EXTINF"):
            index += 1
            continue

        block_options = []
        index += 1
        while index < len(lines):
            line = lines[index].strip()
            if line.startswith("http://") or line.startswith("https://") or line.startswith("udp://"):
                break
            if line.startswith("#EXTVLCOPT") or line.startswith("#KODIPROP"):
                block_options.append(line)
            if line.startswith("#EXTINF"):
                break
            index += 1
        if index >= len(lines):
            break
        stream_url = lines[index].strip()
        if not stream_url.startswith(("http://", "https://", "udp://")):
            continue

        title = extinf.split(",", 1)[1].strip() if "," in extinf else ""
        title_match = re.match(
            r"^(\d{2}/\d{2})\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\s*\|\s*(.+?)(?:\s+\((.+)\))?$",
            title,
            re.I,
        )
        if title_match:
            event_date, match_name, channel_label = title_match.groups()
            day, month = (int(part) for part in event_date.split("/", 1))
            key = match_key(match_name, datetime(2000, month, day))
            if key:
                attributes = dict(re.findall(r'([\w-]+)="([^"]*)"', extinf))
                entries.append(
                    {
                        "key": key,
                        "channel": clean_text(channel_label),
                        "url": stream_url,
                        "options": block_options,
                        "logo": clean_text(attributes.get("tvg-logo")),
                        "tvg_id": clean_text(attributes.get("tvg-id")),
                    }
                )
        index += 1
    return entries


def attach_live_streams(matches):
    live_entries = parse_live_playlist(fetch_text(LIVE_PLAYLIST_URL))
    targets = {}
    for match in matches:
        key = match_key(match["match"], match["start"])
        if key:
            targets.setdefault(key, []).append(match)

    matched = []
    seen = set()
    for entry in live_entries:
        candidates = targets.get(entry["key"], [])
        if not candidates:
            continue
        match = candidates[0]
        unique_key = (entry["key"], entry["url"])
        if unique_key in seen:
            continue
        seen.add(unique_key)
        matched.append({**entry, "match": match})
    return matched, len(live_entries)


def write_playlist(entries, scheduled_count, source_entry_count):
    generated = datetime.now(TZ_VN).strftime("%Y-%m-%d %H:%M ICT")
    matched_games = len({entry["key"] for entry in entries})
    lines = [
        "#EXTM3U",
        f"# Updated : {generated}",
        f"# Total links   : {len(entries)}",
        f"# Matched games : {matched_games}/{scheduled_count}",
        f"# Source links  : {source_entry_count}",
        "# Lịch FootOnSat: giờ Việt Nam (UTC+7), hôm nay và 2 ngày kế tiếp.",
        "# Chỉ xuất link thật khớp lịch; trận chưa có stream sẽ không tạo mục giữ chỗ.",
        "",
    ]
    link_numbers = {}
    for entry in entries:
        match = entry["match"]
        start = match["start"].strftime("%H:%M %d/%m")
        group = f"{start} | {match['match']}"
        link_numbers[entry["key"]] = link_numbers.get(entry["key"], 0) + 1
        title = entry["channel"] or f"Link {link_numbers[entry['key']]}"
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
    entries, source_entry_count = attach_live_streams(matches)
    entries.sort(
        key=lambda item: (
            item["match"]["start"],
            item["match"]["short_league"],
            item["match"]["match"].casefold(),
            item["channel"].casefold(),
        )
    )
    write_playlist(entries, len(matches), source_entry_count)
    matched_games = len({entry["key"] for entry in entries})
    print(
        f"[DONE] FootOnSat: {len(entries)} link, {matched_games}/{len(matches)} trận "
        f"từ {today:%d/%m} đến {last_date:%d/%m}"
    )
    print(f"[DONE] M3U: {OUTPUT_PATH}")
    if failures:
        print(f"[WARN] Nguồn lỗi tạm thời: {', '.join(failures)}")


if __name__ == "__main__":
    main()

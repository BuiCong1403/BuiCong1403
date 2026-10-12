import json
import os
import re
import sys
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


def build_schedule_entries(matches):
    entries = []
    event_number = 0
    for match in matches:
        channels = match.get("channels") or ["Chưa rõ kênh phát"]
        event_number += 1
        for index, channel_name in enumerate(channels, start=1):
            entries.append(
                {
                    "key": (event_number, match["match"]),
                    "channel": channel_name,
                    "url": f"https://freem3u.xyz/static/no-signal/low.m3u8?event={event_number}&channel={index}",
                    "options": [],
                    "logo": "",
                    "tvg_id": "",
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
        f"# Total channels: {len(entries)}",
        f"# Total matches : {scheduled_count}",
        "# Lịch FootOnSat: giờ Việt Nam (UTC+7), hôm nay và 2 ngày kế tiếp.",
        "# Mỗi trận là một group theo giờ Việt Nam; các dòng bên trong là kênh phát từ JSON FootOnSat.",
        "# FootOnSat chỉ cung cấp lịch/kênh phát, không cung cấp luồng video trực tiếp.",
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
    entries = build_schedule_entries(matches)
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
        f"[DONE] FootOnSat: {len(entries)} kênh, {len(matches)} trận "
        f"từ {today:%d/%m} đến {last_date:%d/%m}"
    )
    print(f"[DONE] M3U: {OUTPUT_PATH}")
    if failures:
        print(f"[WARN] Nguồn lỗi tạm thời: {', '.join(failures)}")


if __name__ == "__main__":
    main()

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests


HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_json(url):
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"Error fetching JSON {url}: {exc}")
        return {}


def is_valid_tv(url):
    return bool(url and ".m3u8" in url and not any(x in url for x in ("udp://", "rtp://")))


def is_working_m3u8(url):
    if not is_valid_tv(url):
        return False

    try:
        response = session.head(url, timeout=5, allow_redirects=True)
        if response.status_code in (200, 204):
            return True
        if response.status_code not in (403, 405):
            return False
    except Exception:
        pass

    try:
        response = session.get(url, timeout=7, headers={"Range": "bytes=0-1024"}, stream=True)
        return response.status_code in (200, 206)
    except Exception:
        return False


def check_stream(url):
    return url if is_working_m3u8(url) else None


def first_dict(value):
    if isinstance(value, list) and value:
        return value[0] if isinstance(value[0], dict) else {}
    return {}


def safe_stream_links_from_channel(channel):
    for source in channel.get("sources") or []:
        blv_name = source.get("name") or "Chính"
        for content in source.get("contents") or []:
            for stream in content.get("streams") or []:
                for link in stream.get("stream_links") or []:
                    url = link.get("url")
                    if url:
                        yield blv_name, url


def pick_stream(streams):
    m3u8_hd = None
    m3u8 = None
    for stream in streams or []:
        name = (stream.get("name") or "").upper()
        url = stream.get("sourceUrl")
        if not is_valid_tv(url):
            continue
        if "FHD" in name or "HD" in name:
            m3u8_hd = url
        else:
            m3u8 = url
    return m3u8_hd or m3u8


def parse_start_time(item, add_hours=0):
    start_time = item.get("startTime")
    if not start_time:
        return datetime.now()

    try:
        return datetime.strptime(start_time[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=add_hours)
    except Exception:
        return datetime.now()


def make_item(group, title, url, logo="", blv="Chính", time_value=None):
    return {
        "time": time_value or datetime.now(),
        "group": group,
        "title": title or group,
        "logo": logo or "",
        "url": url,
        "blv": blv or "Chính",
    }


def process_standard(url, group):
    output = []
    data = fetch_json(url)

    for item in data.get("data") or []:
        dt = parse_start_time(item, add_hours=7)
        for commentator_item in item.get("fixtureCommentators") or []:
            commentator = commentator_item.get("commentator") or {}
            blv_name = commentator.get("name") or "Chính"
            stream = pick_stream(commentator.get("streams") or [])
            if not stream:
                continue

            output.append(
                make_item(
                    group=group,
                    title=f'{dt.strftime("%H:%M")} | {item.get("title") or ""}',
                    logo=(item.get("homeTeam") or {}).get("logoUrl", ""),
                    url=stream,
                    blv=blv_name,
                    time_value=dt,
                )
            )
            break

    return output


def process_grouped_channels(url, group_name):
    output = []
    data = fetch_json(url)

    for group in data.get("groups") or []:
        for channel in group.get("channels") or []:
            logo = ((channel.get("image") or {}).get("url")) or ""
            title = channel.get("name") or group_name
            found_url = False

            for blv_name, stream_url in safe_stream_links_from_channel(channel):
                output.append(make_item(group_name, title, stream_url, logo=logo, blv=blv_name))
                found_url = True

            if not found_url:
                output.append(make_item(group_name, title, None, logo=logo, blv="Mặc định"))

    return output


def process_hoiquan2(url, group_name="HỘI QUÁN 2"):
    return process_grouped_channels(url, group_name)


def process_luongson_tv(url, group_name="LƯƠNG SƠN TV"):
    return process_grouped_channels(url, group_name)


def process_quechoa_tv(url, group_name="QUÊ CHOA TV"):
    return process_grouped_channels(url, group_name)


def process_vongcam():
    output = []
    data = fetch_json("https://sv.bugiotv.xyz/internal/api/matches")

    for item in data.get("data") or []:
        commentator = item.get("commentator") or {}
        url = commentator.get("streamSourceFhd")
        if not is_valid_tv(url):
            continue
        output.append(
            make_item(
                group="VÒNG CẤM TV",
                title=item.get("title") or "VÒNG CẤM TV",
                logo=(item.get("homeClub") or {}).get("logoUrl", ""),
                url=url,
                blv=commentator.get("name") or "Chính",
            )
        )

    return output


def process_cala_tv():
    output = []
    data = fetch_json("https://api.cltvlv.com/api/matches")

    for item in (data.get("data") or {}).values():
        dt = datetime.fromtimestamp(item.get("matchTime") or datetime.now().timestamp())
        home = item.get("home_team") or {}
        away = item.get("away_team") or {}
        stream_url = None
        blv_name = "Chính"

        for stream in item.get("anchorAppointmentVoList") or []:
            blv_name = stream.get("anchorName") or blv_name
            for key in ("playStreamAddress2", "playStreamAddress1", "playStreamAddress3"):
                candidate = stream.get(key)
                if is_valid_tv(candidate):
                    stream_url = candidate
                    break
            if stream_url:
                break

        if not stream_url:
            continue

        output.append(
            make_item(
                group="CO LA TV",
                title=f'{dt.strftime("%H:%M")} | {home.get("name") or ""} vs {away.get("name") or ""}',
                logo=home.get("logo", ""),
                url=stream_url,
                blv=blv_name,
                time_value=dt,
            )
        )

    return output


def process_tamquoc_tv():
    output = []
    data = fetch_json("https://sv.tamquoctv.xyz/internal/api/matches")
    items = data.get("data") or []
    if isinstance(items, dict):
        items = items.values()

    for item in items:
        dt = parse_start_time(item)
        home = item.get("homeClub") or {}
        away = item.get("awayClub") or {}
        commentator = item.get("commentator") or {}
        stream_url = (
            commentator.get("streamSourceFhd")
            or commentator.get("streamSourceHd")
            or commentator.get("streamSourceSd")
        )
        if not is_valid_tv(stream_url):
            continue

        output.append(
            make_item(
                group="TAM QUỐC TV",
                title=f'{dt.strftime("%H:%M")} | {home.get("name") or ""} vs {away.get("name") or ""}',
                logo=home.get("logoUrl", ""),
                url=stream_url,
                blv=commentator.get("name") or "Chính",
                time_value=dt,
            )
        )

    return output


def parse_extinf(line):
    title = line.split(",", 1)[1].strip() if "," in line else ""
    logo_match = re.search(r'tvg-logo="([^"]*)"', line)
    group_match = re.search(r'group-title="([^"]*)"', line)
    return {
        "title": title,
        "logo": logo_match.group(1) if logo_match else "",
        "group": group_match.group(1) if group_match else "",
    }


def load_m3u_playlist(url, group_name, blv_name=None):
    output = []
    current = {"title": group_name, "logo": "", "group": group_name}

    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        print(f"Error loading M3U {url}: {exc}")
        return output

    for raw_line in response.text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            current = parse_extinf(line)
            current["group"] = group_name
            continue
        if line.startswith("http"):
            output.append(
                make_item(
                    group=group_name,
                    title=current.get("title") or group_name,
                    logo=current.get("logo", ""),
                    url=line,
                    blv=blv_name or group_name,
                )
            )

    return output


def load_fpt_sport(url):
    return load_m3u_playlist(url, "FPT SPORT", "FPT")


def process_tieulam_tv(url, group_name="TIẾU LÂM TV"):
    return load_m3u_playlist(url, group_name, group_name)


def write_files(data):
    seen = set()
    tv = "#EXTM3U\n"
    full = "#EXTM3U\n"
    live_items = []
    items = []
    unchecked_groups = {"HỘI QUÁN 2", "LƯƠNG SƠN TV", "QUÊ CHOA TV", "GIỜ VÀNG", "QUÊ CHOA"}

    for item in data:
        url = item.get("url")
        if not url or url in seen:
            continue

        seen.add(url)
        extinf = (
            f'#EXTINF:-1 group-title="{item.get("group", "")}" '
            f'tvg-logo="{item.get("logo", "")}",{item.get("title", "")}\n'
        )
        items.append((extinf, url, item))

    for extinf, url, _item in items:
        full += extinf + f"{url}\n\n"

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        for extinf, url, item in items:
            if item.get("group") in unchecked_groups:
                tv += extinf + f"{url}\n\n"
                live_items.append(item)
            else:
                futures[executor.submit(check_stream, url)] = (extinf, url, item)

        for future in as_completed(futures):
            result = future.result()
            if result:
                extinf, url, item = futures[future]
                tv += extinf + f"{url}\n\n"
                live_items.append(item)

    with open("tv.m3u", "w", encoding="utf-8") as file:
        file.write(tv)
    with open("full.m3u", "w", encoding="utf-8") as file:
        file.write(full)

    print("DONE PRO MAX++ OK")
    print(f"TV Channels: {tv.count('#EXTINF')}")
    print(f"FULL Channels: {full.count('#EXTINF')}")

    return live_items


def write_json(data):
    output = {
        "id": "tonghop",
        "url": "https://vanlinh.io.vn",
        "name": "VLINH-TV",
        "color": "#1cb57a",
        "grid_number": 3,
        "image": {
            "type": "cover",
            "url": "https://kaytee1012.github.io/hoiquan_logo.png",
        },
        "notice": {
            "closeable": True,
            "icon": "https://kaytee1012.github.io/pngegg.png",
            "id": "notice",
            "link": "https://t.me/",
            "text": "Nhóm Tele",
        },
        "groups": [],
    }

    groups_map = {}
    for item in data:
        group_id = item.get("group") or "Khác"
        if group_id not in groups_map:
            groups_map[group_id] = {
                "id": re.sub(r"[^a-z0-9-]+", "-", group_id.lower()).strip("-"),
                "name": f"Live {group_id}",
                "display": "vertical",
                "grid_number": 2,
                "enable_detail": False,
                "channels": [],
            }

        has_url = bool(item.get("url"))
        label_text = "Live" if has_url else "Chưa live"
        label_color = "#ff0000" if has_url else "#d54f1a"
        channel_id = f'{group_id}-{item.get("time", datetime.now()).strftime("%H%M%S")}-{len(groups_map[group_id]["channels"]) + 1}'

        channel = {
            "id": channel_id,
            "name": f'{item.get("title", "")}',
            "type": "single",
            "display": "thumbnail-only",
            "enable_detail": False,
            "image": {
                "padding": 1,
                "background_color": "#ececec",
                "display": "contain",
                "url": item.get("logo", ""),
                "width": 1600,
                "height": 1200,
            },
            "labels": [
                {
                    "text": label_text,
                    "position": "top-left",
                    "color": "#00ffffff",
                    "text_color": label_color,
                }
            ],
            "sources": [
                {
                    "id": channel_id,
                    "name": group_id,
                    "contents": [
                        {
                            "id": channel_id,
                            "name": item.get("title", ""),
                            "streams": [
                                {
                                    "id": channel_id,
                                    "name": item.get("blv") or "Chính",
                                    "stream_links": [
                                        {
                                            "id": "lnk-1",
                                            "name": "Link 1",
                                            "type": "hls",
                                            "default": True,
                                            "url": item.get("url"),
                                        }
                                    ]
                                    if has_url
                                    else [],
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        groups_map[group_id]["channels"].append(channel)

    output["groups"] = list(groups_map.values())

    with open("channels.json", "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print("JSON file channels.json da duoc tao OK")


def main():
    data = []
    data += process_standard("https://sv.hoiquantv.xyz/api/v1/external/fixtures/unfinished", "HỘI QUÁN 1")
    data += process_hoiquan2("https://pub-26bab83910ab4b5781549d12d2f0ef6f.r2.dev/hoiquan1.json")
    data += process_standard("https://sv.thiendinhtv.xyz/api/v1/external/fixtures/unfinished", "THIÊN ĐÌNH")
    data += process_standard("https://sv.xaycontv.xyz/api/v1/external/fixtures/unfinished", "XAY CON")
    data += process_vongcam()
    data += process_cala_tv()
    data += process_tamquoc_tv()
    data += process_luongson_tv("https://apithethao1.vercel.app/luongsontv")
    data += process_quechoa_tv("https://apithethao1.vercel.app/quechoatv")
    data += load_fpt_sport("https://raw.githubusercontent.com/t23-02/bongda/refs/heads/main/bongda.m3u")
    data += process_hoiquan2(
        "https://raw.githubusercontent.com/jasminliu98/giovang-stream/refs/heads/main/output.json",
        "GIỜ VÀNG",
    )
    data += process_quechoa_tv(
        "https://raw.githubusercontent.com/huybuonvp/xem_football/refs/heads/main/All_CHANNEL.json",
        "QUÊ CHOA",
    )
    data += process_tieulam_tv(
        "https://raw.githubusercontent.com/Bacbenny/testtieulam/refs/heads/main/output/iptv.m3u",
        "TIẾU LÂM TV",
    )

    write_files(data)
    write_json(data)


if __name__ == "__main__":
    main()

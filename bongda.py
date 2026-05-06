import requests
import re
from datetime import datetime, timedelta

BASE_URL = "https://hoadaotv.info"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ================== HTTP ==================
session = requests.Session()
session.headers.update(HEADERS)


def fetch_json(url):
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return {}


# ================== STREAM FILTER ==================
def is_working_m3u8(url):
    if ".m3u8" not in url:
        return False
    try:
        r = session.get(url, timeout=8, stream=True)
        return r.status_code == 200
    except:
        return False


def is_valid_tv(url):
    if ".m3u8" not in url:
        return False
    if any(x in url for x in ["udp://", "rtp://"]):
        return False
    return True


# ================== PICK STREAM ==================
def pick_stream(streams):
    m3u8_hd = None
    m3u8 = None

    for s in streams:
        name = s.get("name", "").upper()
        url = s.get("sourceUrl")

        if not url:
            continue

        if ".m3u8" in url:
            if "FHD" in name or "HD" in name:
                m3u8_hd = url
            else:
                m3u8 = url

    return m3u8_hd or m3u8


# ================== API ==================
def process_standard(url, group):
    out = []
    data = fetch_json(url)

    for item in data.get("data", []):
        dt = datetime.now()

        if item.get("startTime"):
            try:
                dt = datetime.strptime(item['startTime'][:19], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)
            except:
                pass

        for c in item.get("fixtureCommentators", []):
            comm = c.get("commentator", {})

            stream = pick_stream(comm.get("streams", []))
            if not stream:
                continue

            out.append({
                "time": dt,
                "group": group,
                "title": f"{dt.strftime('%H:%M')} | {item.get('title')}",
                "logo": item.get('homeTeam', {}).get('logoUrl', ''),
                "url": stream
            })
            break

    return out


def process_vongcam():
    out = []
    data = fetch_json("https://sv.bugiotv.xyz/internal/api/matches")

    for item in data.get("data", []):
        url = item.get("commentator", {}).get("streamSourceFhd")

        if not url or ".m3u8" not in url:
            continue

        out.append({
            "time": datetime.now(),
            "group": "🔴 ⚽ VÒNG CẤM TV",
            "title": item.get("title"),
            "logo": item.get("homeClub", {}).get("logoUrl", ""),
            "url": url
        })

    return out


# ================== LOAD EXTERNAL (GIỮ NGUYÊN GROUP) ==================
def load_external_keep_group(url):
    out = []
    try:
        r = session.get(url, timeout=15)
        lines = r.text.splitlines()

        title = ""
        logo = ""
        group = ""

        for line in lines:
            if line.startswith("#EXTINF"):
                title = line.split(",")[-1]

                m_logo = re.search(r'tvg-logo="([^"]+)"', line)
                logo = m_logo.group(1) if m_logo else ""

                m_group = re.search(r'group-title="([^"]+)"', line)
                group = m_group.group(1) if m_group else "📺 OTHER"

            elif line.startswith("http"):
                out.append({
                    "time": datetime.now(),
                    "group": group,
                    "title": title,
                    "logo": logo,
                    "url": line.strip()
                })
    except:
        pass

    return out


# ================== WRITE ==================
def write_files(data):
    seen = set()

    tv = "#EXTM3U\n"
    full = "#EXTM3U\n"

    for item in data:
        url = item["url"]

        if url in seen:
            continue
        seen.add(url)

        full += f'#EXTINF:-1 group-title="{item["group"]}",{item["title"]}\n{url}\n\n'

        if is_valid_tv(url) and is_working_m3u8(url):
            tv += f'#EXTINF:-1 group-title="{item["group"]}",{item["title"]}\n{url}\n\n'

    open("tv.m3u", "w", encoding="utf-8").write(tv)
    open("full.m3u", "w", encoding="utf-8").write(full)

    print("DONE PRO MAX ✔")


# ================== MAIN ==================
if __name__ == "__main__":
    data = []

    data += process_standard(
        "https://sv.hoiquantv.xyz/api/v1/external/fixtures/unfinished",
        "⚽ HỘI QUÁN"
    )

    data += process_standard(
        "https://sv.thiendinhtv.xyz/api/v1/external/fixtures/unfinished",
        "⚽ THIÊN ĐÌNH"
    )

    data += process_vongcam()

    # ✅ M3U mới (giữ group gốc)
    data += load_external_keep_group(
        "https://raw.githubusercontent.com/hieu-TQS/TV/refs/heads/main/TV.m3u"
    )

    write_files(data)

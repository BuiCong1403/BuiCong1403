import requests
import re
from bs4 import BeautifulSoup
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
    """Test link có chạy được không (quan trọng nhất)"""
    if ".m3u8" not in url:
        return False

    try:
        r = session.get(url, timeout=8, stream=True)
        if r.status_code == 200:
            return True
    except:
        return False

    return False


def is_valid_tv(url):
    """lọc link không phù hợp OTT"""
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


# ================== HOADAO (bỏ vì flv không dùng cho TV) ==================
# vẫn giữ trong full.m3u
def process_hoadao_flv():
    out = []
    try:
        r = session.get(BASE_URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "truc-tiep" not in href:
                continue

            url = href if href.startswith("http") else BASE_URL + href

            try:
                html = session.get(url, timeout=10).text
                flv = re.findall(r'https?://[^"\']+\.flv', html)

                if flv:
                    out.append({
                        "time": datetime.now(),
                        "group": "⚽ HOA ĐÀO (FLV)",
                        "title": "HoaDao",
                        "logo": BASE_URL + "/favicon.ico",
                        "url": flv[0]
                    })
            except:
                continue
    except:
        pass

    return out


# ================== EXTERNAL M3U ==================
def load_external(url):
    out = []
    try:
        r = session.get(url, timeout=15)
        lines = r.text.splitlines()

        title = ""
        logo = ""

        for line in lines:
            if line.startswith("#EXTINF"):
                title = line.split(",")[-1]
                m = re.search(r'tvg-logo="([^"]+)"', line)
                logo = m.group(1) if m else ""

            elif line.startswith("http"):
                out.append({
                    "time": datetime.now(),
                    "group": "📺 VIETANH",
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

        # FULL (giữ hết)
        full += f'#EXTINF:-1 group-title="{item["group"]}",{item["title"]}\n{url}\n\n'

        # TV (lọc mạnh)
        if is_valid_tv(url) and is_working_m3u8(url):
            tv += f'#EXTINF:-1 group-title="{item["group"]}",{item["title"]}\n{url}\n\n'

    open("tv.m3u", "w", encoding="utf-8").write(tv)
    open("full.m3u", "w", encoding="utf-8").write(full)

    print("DONE PRO ✔")


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
    data += process_hoadao_flv()
    data += load_external("https://vietanhtv.id.vn/tv")

    write_files(data)

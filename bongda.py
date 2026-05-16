import requests
import re
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ================= HTTP =================
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


# ================= STREAM CHECK =================
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


# ================= PICK STREAM =================
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


# ================= API STANDARD =================
def process_standard(url, group):
    out = []

    data = fetch_json(url)

    for item in data.get("data", []):

        dt = datetime.now()

        if item.get("startTime"):
            try:
                dt = datetime.strptime(
                    item["startTime"][:19],
                    "%Y-%m-%dT%H:%M:%S"
                ) + timedelta(hours=7)
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
                "title": f'{dt.strftime("%H:%M")} | {item.get("title")}',
                "logo": item.get("homeTeam", {}).get("logoUrl", ""),
                "url": stream
            })

            break

    return out


# ================= VONG CAM =================
def process_vongcam():
    out = []

    data = fetch_json(
        "https://sv.bugiotv.xyz/internal/api/matches"
    )

    for item in data.get("data", []):

        url = item.get("commentator", {}).get(
            "streamSourceFhd"
        )

        if not url:
            continue

        if ".m3u8" not in url:
            continue

        out.append({
            "time": datetime.now(),
            "group": "VÒNG CẤM TV",
            "title": item.get("title"),
            "logo": item.get("homeClub", {}).get("logoUrl", ""),
            "url": url
        })

    return out


# ================= LOAD EXTERNAL KEEP GROUP =================
def load_external_keep_group(url):
    out = []

    try:
        r = session.get(url, timeout=15)
        lines = r.text.splitlines()

        title = ""
        logo = ""
        group = "OTHER"

        for line in lines:

            if line.startswith("#EXTINF"):

                title = line.split(",")[-1].strip()

                m_logo = re.search(
                    r'tvg-logo="([^"]+)"',
                    line
                )

                if m_logo:
                    logo = m_logo.group(1)
                else:
                    logo = ""

                m_group = re.search(
                    r'group-title="([^"]+)"',
                    line
                )

                if m_group:
                    group = m_group.group(1)

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


# ================= LOAD FPT SPORT =================
def load_fpt_sport(url):
    out = []

    try:
        r = session.get(url, timeout=15)

        lines = r.text.splitlines()

        title = ""

        for line in lines:

            if line.startswith("#EXTINF"):
                title = line.split(",")[-1].strip()

            elif line.startswith("http"):

                out.append({
                    "time": datetime.now(),
                    "group": "FPT SPORT",
                    "title": title if title else "FPT SPORT",
                    "logo": "",
                    "url": line.strip()
                })

    except:
        pass

    return out


# ================= WRITE FILE =================
def write_files(data):

    seen = set()

    tv = "#EXTM3U\n"
    full = "#EXTM3U\n"

    for item in data:

        url = item["url"]

        if url in seen:
            continue

        seen.add(url)

        extinf = (
            f'#EXTINF:-1 '
            f'group-title="{item["group"]}" '
            f'tvg-logo="{item["logo"]}",'
            f'{item["title"]}\n'
        )

        # FULL
        full += extinf
        full += f"{url}\n\n"

        # TV FILTER
        if is_valid_tv(url) and is_working_m3u8(url):

            tv += extinf
            tv += f"{url}\n\n"

    with open("tv.m3u", "w", encoding="utf-8") as f:
        f.write(tv)

    with open("full.m3u", "w", encoding="utf-8") as f:
        f.write(full)

    print("DONE PRO MAX++ ✔")
    print(f"TV Channels: {tv.count('#EXTINF')}")
    print(f"FULL Channels: {full.count('#EXTINF')}")


# ================= MAIN =================
if __name__ == "__main__":

    data = []

    # HỘI QUÁN
    data += process_standard(
        "https://sv.hoiquantv.xyz/api/v1/external/fixtures/unfinished",
        "HỘI QUÁN"
    )

    # THIÊN ĐÌNH
    data += process_standard(
        "https://sv.thiendinhtv.xyz/api/v1/external/fixtures/unfinished",
        "THIÊN ĐÌNH"
    )

    # VÒNG CẤM
    data += process_vongcam()

    # TV.m3u giữ nguyên group
    data += load_external_keep_group(
        "https://raw.githubusercontent.com/hieu-TQS/TV/refs/heads/main/TV.m3u"
    )

    # FPT SPORT
    data += load_fpt_sport(
        "https://raw.githubusercontent.com/t23-02/bongda/refs/heads/main/bongda.m3u"
    )

    # WRITE
    write_files(data)

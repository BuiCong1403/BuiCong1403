import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

FILENAME = "bongda.m3u"
BASE_URL = "https://hoadaotv.info"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ================== COMMON ==================
def fetch_json(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"Lỗi fetch {url}: {e}")
    return {}


def pick_stream(streams):
    m3u8_hd = None
    m3u8 = None
    flv = None

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
        elif ".flv" in url:
            flv = url

    return m3u8_hd or m3u8 or flv


# ================== API SOURCES ==================
def process_standard(url, group):
    fixtures = []
    data = fetch_json(url)

    for item in data.get('data', []):
        dt = datetime.now()

        if item.get('startTime'):
            try:
                dt = datetime.strptime(item['startTime'][:19], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)
            except:
                pass

        for comm_entry in item.get('fixtureCommentators', []):
            comm = comm_entry.get('commentator', {})
            nickname = comm.get('nickname', '')

            stream_url = pick_stream(comm.get('streams', []))
            if not stream_url:
                continue

            fixtures.append({
                "time": dt,
                "group": group,
                "title": f"{dt.strftime('%H:%M')} | {item.get('title')} ({nickname})",
                "logo": item.get('homeTeam', {}).get('logoUrl', ''),
                "url": stream_url
            })
            break

    return fixtures


def process_vongcam():
    fixtures = []
    data = fetch_json("https://sv.bugiotv.xyz/internal/api/matches")

    for item in data.get('data', []):
        dt = datetime.now()

        if item.get('startTime'):
            try:
                dt = datetime.strptime(item['startTime'][:19], '%Y-%m-%dT%H:%M:%S')
            except:
                pass

        url = item.get('commentator', {}).get('streamSourceFhd')
        if not url:
            continue

        fixtures.append({
            "time": dt,
            "group": "🔴 ⚽ VÒNG CẤM TV",
            "title": f"{dt.strftime('%H:%M')} | {item.get('title')}",
            "logo": item.get('homeClub', {}).get('logoUrl', ''),
            "url": url
        })

    return fixtures


# ================== HOADAOTV ==================
def extract_hoadao_stream(html):
    # ưu tiên m3u8 trước (TV)
    m3u8 = re.findall(r'"(hd|hls|m3u8)"\s*:\s*"([^"]+)"', html)
    if m3u8:
        for key, url in m3u8:
            if key == "hd":
                return url.replace('\\/', '/')
        return m3u8[0][1].replace('\\/', '/')

    # fallback flv
    flv = re.search(r'"flv"\s*:\s*"([^"]+)"', html)
    if flv:
        return flv.group(1).replace('\\/', '/')

    return None


def process_hoadaotv():
    matches = []

    try:
        res = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')

        links = set()

        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/truc-tiep/' in href:
                url = href if href.startswith('http') else BASE_URL + href
                links.add(url)

        for url in links:
            try:
                r = requests.get(url, headers=HEADERS, timeout=10)
                html = r.text

                stream = extract_hoadao_stream(html)
                if not stream:
                    continue

                s = BeautifulSoup(html, 'html.parser')

                title = "HoaDao TV"
                if s.find('h1'):
                    title = s.find('h1').get_text(strip=True)

                logo = BASE_URL + "/favicon.ico"

                matches.append({
                    "time": datetime.now(),
                    "group": "🔴 ⚽ HOA ĐÀO TV",
                    "title": title,
                    "logo": logo,
                    "url": stream
                })

            except:
                continue

    except Exception as e:
        print(f"Lỗi hoadaotv: {e}")

    return matches


# ================== WRITE ==================
def write_m3u(data):
    content = "#EXTM3U\n"

    for item in data:
        content += f'#EXTINF:-1 group-title="{item["group"]}" tvg-logo="{item["logo"]}",{item["title"]}\n'
        content += f'{item["url"]}\n\n'

    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write(content)

    print("Done!")


# ================== MAIN ==================
if __name__ == "__main__":
    hq = process_standard(
        "https://sv.hoiquantv.xyz/api/v1/external/fixtures/unfinished",
        "🔴 ⚽ HỘI QUÁN TV"
    )

    td = process_standard(
        "https://sv.thiendinhtv.xyz/api/v1/external/fixtures/unfinished",
        "🔴 ⚽ THIÊN ĐÌNH TV"
    )

    vc = process_vongcam()
    hd = process_hoadaotv()

    all_data = hq + td + vc + hd
    all_data.sort(key=lambda x: x["time"])

    write_m3u(all_data)
    all_data = hq + td + vc
    all_data.sort(key=lambda x: x["time"])

    write_m3u(all_data)

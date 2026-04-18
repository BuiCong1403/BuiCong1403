import requests
import re
from bs4 import BeautifulSoup

BASE_URL = "https://hoadaotv.info"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": BASE_URL
}

def extract_stream(html):
    # 1. Ưu tiên FLV trước
    flv_matches = re.findall(r'"flv"\s*:\s*"([^"]+)"', html)
    if flv_matches:
        # lấy link đầu tiên
        return flv_matches[0].replace('\\/', '/')

    # 2. Nếu không có FLV → tìm m3u8
    m3u8_matches = re.findall(r'"(hd|hls|m3u8)"\s*:\s*"([^"]+)"', html)

    if m3u8_matches:
        # ưu tiên HD
        for key, url in m3u8_matches:
            if key == "hd":
                return url.replace('\\/', '/')

        # fallback
        return m3u8_matches[0][1].replace('\\/', '/')

    return None


def get_match_data():
    matches = []

    try:
        res_home = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        if res_home.status_code != 200:
            print("Không tải được trang chủ")
            return []

        res_home.encoding = 'utf-8'
        soup_home = BeautifulSoup(res_home.text, 'html.parser')

        links = set()

        # Lấy link trận
        for a in soup_home.find_all('a', href=True):
            href = a['href']
            if '/truc-tiep/' in href or 'xem-bong-da' in href:
                url = href if href.startswith('http') else BASE_URL + href
                links.add(url)

        print(f"Tìm thấy {len(links)} trận")

        for url in links:
            try:
                res = requests.get(url, headers=HEADERS, timeout=10)
                if res.status_code != 200:
                    continue

                html = res.text
                stream_url = extract_stream(html)

                if not stream_url:
                    continue

                soup = BeautifulSoup(html, 'html.parser')

                # Title
                title = "Live Match"
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
                elif soup.title:
                    title = soup.title.get_text(strip=True).split('|')[0]

                # Logo
                logo = BASE_URL + "/favicon.ico"
                img = soup.find('img', src=re.compile(r'logo|team'))
                if img:
                    logo = img['src']
                    if not logo.startswith('http'):
                        logo = BASE_URL + logo

                matches.append({
                    "name": title,
                    "logo": logo,
                    "url": stream_url
                })

                print(f"OK: {title}")

            except Exception as e:
                print(f"Lỗi trận: {url} | {e}")
                continue

        return matches

    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        return []


def write_m3u(matches):
    if not matches:
        print("Không có trận nào!")
        return

    content = "#EXTM3U\n"

    for m in matches:
        content += f'#EXTINF:-1 tvg-logo="{m["logo"]}" group-title="Hoa Dao TV", {m["name"]}\n'
        content += f'#EXTVLCOPT:http-referrer={BASE_URL}/\n'
        content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n'
        content += f'{m["url"]}\n\n'

    with open("hoadao.m3u", "w", encoding="utf-8") as f:
        f.write(content)

    print("Đã tạo file hoadao.m3u")


if __name__ == "__main__":
    data = get_match_data()
    write_m3u(data)

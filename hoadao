import requests
import re
from bs4 import BeautifulSoup

BASE_URL = "https://hoadaotv.info"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": BASE_URL
}

def get_match_data():
    matches = []
    try:
        # 1. Tải trang chủ
        res_home = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        res_home.encoding = 'utf-8'
        soup_home = BeautifulSoup(res_home.text, 'html.parser')
        
        # Chiến thuật: Tìm tất cả thẻ <a> có chứa từ khóa 'truc-tiep' hoặc nằm trong các khối trận đấu
        potential_links = []
        for a in soup_home.find_all('a', href=True):
            href = a['href']
            # Quét các link có cấu trúc trực tiếp bóng đá
            if '/truc-tiep/' in href or 'xem-bong-da' in href:
                url = href if href.startswith('http') else BASE_URL + href
                if url not in potential_links:
                    potential_links.append(url)
        
        # Nếu vẫn không thấy, quét rộng hơn ở các thẻ div chứa trận đấu
        if not potential_links:
             for div in soup_home.find_all('div', class_=re.compile(r'match|item|card')):
                 a = div.find('a', href=True)
                 if a:
                     url = a['href'] if a['href'].startswith('http') else BASE_URL + a['href']
                     if url not in potential_links:
                         potential_links.append(url)

        print(f"Tìm thấy {len(potential_links)} link tiềm năng.")

        for url in potential_links:
            try:
                res_detail = requests.get(url, headers=HEADERS, timeout=10)
                html = res_detail.text
                
                # Móc link FLV/HLS bằng Regex (Xuyên qua lớp bảo vệ Javascript)
                flv_match = re.search(r'"flv":"([^"]+)"', html)
                hls_match = re.search(r'"hd":"([^"]+)"', html)
                
                if not flv_match and not hls_match:
                    continue
                
                # Ưu tiên FLV, nếu không có lấy HLS
                stream_url = ""
                if flv_match:
                    stream_url = flv_match.group(1).replace('\\/', '/')
                elif hls_match:
                    stream_url = hls_match.group(1).replace('\\/', '/')

                # Lấy tiêu đề trận đấu và Logo
                soup_detail = BeautifulSoup(html, 'html.parser')
                
                # Thử lấy tiêu đề từ h1 hoặc title trang
                title = "Trận bóng đang diễn ra"
                h1_tag = soup_detail.find('h1')
                if h1_tag:
                    title = h1_tag.get_text(strip=True)
                else:
                    title_tag = soup_detail.find('title')
                    if title_tag:
                        title = title_tag.get_text(strip=True).split('|')[0]

                # Lấy ảnh logo (đội nhà/đội khách)
                logo = "https://hoadaotv.info/favicon.ico"
                img_tags = soup_detail.find_all('img', src=re.compile(r'logo|team'))
                if img_tags:
                    logo = img_tags[0]['src']
                    if not logo.startswith('http'):
                        logo = BASE_URL + logo

                matches.append({
                    "name": title,
                    "logo": logo,
                    "url": stream_url
                })
                print(f"Thành công: {title}")
            except:
                continue
                
        return matches
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        return []

def write_m3u(matches):
    if not matches:
        print("Không tìm thấy trận nào đang live để cập nhật!")
        return

    content = "#EXTM3U\n"
    for m in matches:
        content += f'#EXTINF:-1 tvg-logo="{m["logo"]}" group-title="Hoa Dao TV LIVE", {m["name"]}\n'
        content += f'#EXTVLCOPT:http-referrer={BASE_URL}/\n'
        content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n'
        content += f'{m["url"]}\n\n'
    
    with open('hoadao.m3u', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Đã ghi đè file hoadao.m3u thành công.")

if __name__ == "__main__":
    data = get_match_data()
    write_m3u(data)

import requests
from datetime import datetime, timedelta

# Cấu hình
FILENAME = "bongda.m3u"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA}

def process_standard(url, provider_name, emoji_group):
    fixtures = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15).json()
        for item in res.get('data', []):
            dt_vn = datetime.max
            if item.get('startTime'):
                dt_vn = datetime.strptime(item['startTime'][:19], '%Y-%m-%dT%H:%M:%S') + timedelta(hours=7)
            
            # Lọc lấy link từ commentator
            for comm_entry in item.get('fixtureCommentators', []):
                comm_data = comm_entry.get('commentator', {})
                nickname = comm_data.get('nickname', '')
                for s in comm_data.get('streams', []):
                    s_name = s.get('name', '').upper()
                    if "FHD" in s_name or "FULLHD" in s_name:
                        fixtures.append({
                            'time': dt_vn,
                            'group': emoji_group,
                            'title': f"{dt_vn.strftime('%H:%M')} | {item.get('title')} ({nickname})",
                            'logo': item.get('homeTeam', {}).get('logoUrl', ''),
                            'url': s.get('sourceUrl')
                        })
                        break
    except:
        pass
    return fixtures

def process_vongcam():
    url = "https://sv.bugiotv.xyz/internal/api/matches"
    fixtures = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15).json()
        for item in res.get('data', []):
            dt_vn = datetime.max
            if item.get('startTime'):
                dt_vn = datetime.strptime(item['startTime'][:19], '%Y-%m-%dT%H:%M:%S')
            
            stream_url = item.get('commentator', {}).get('streamSourceFhd')
            if stream_url:
                fixtures.append({
                    'time': dt_vn,
                    'group': "🔴 ⚽ VÒNG CẤM TV",
                    'title': f"{dt_vn.strftime('%H:%M')} | {item.get('title')}",
                    'logo': item.get('homeClub', {}).get('logoUrl', ''),
                    'url': stream_url
                })
    except:
        pass
    return fixtures

if __name__ == "__main__":
    # Thu thập dữ liệu
    hq = process_standard("https://sv.hoiquantv.xyz/api/v1/external/fixtures/unfinished", "HoiQuanTV", "🔴 ⚽ HỘI QUÁN TV")
    td = process_standard("https://sv.thiendinhtv.xyz/api/v1/external/fixtures/unfinished", "ThienDinhTV", "🔴 ⚽ THIÊN ĐÌNH TV")
    vc = process_vongcam()

    all_data = hq + td + vc
    # Sắp xếp theo thời gian
    all_data.sort(key=lambda x: x['time'])

    # Ghi file M3U
    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for item in all_data:
            # Ghi theo định dạng bạn yêu cầu
            f.write(f'#EXTINF:-1 group-title="{item["group"]}" tvg-logo="{item["logo"]}", {item["title"]}\n')
            f.write(f'#EXTVLCOPT:http-user-agent={UA}\n')
            f.write(f'{item["url"]}\n')
            
    print(f"Done! Created {FILENAME}")

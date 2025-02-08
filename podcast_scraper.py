import socket
_orig_getaddrinfo = socket.getaddrinfo
def _force_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = _force_ipv4_getaddrinfo

import os
import requests
import xml.etree.ElementTree as ET
import psycopg2
from datetime import datetime

# 從環境變數取得 Supabase 資料庫連線字串
SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')
if not SUPABASE_DB_URL:
    raise Exception("請設定環境變數 SUPABASE_DB_URL，並將 Supabase 的連線字串貼上。")

# 連線到 Supabase PostgreSQL，啟用 SSL
conn = psycopg2.connect(SUPABASE_DB_URL, sslmode='require')
cursor = conn.cursor()

# 建立資料表（若尚未存在）
cursor.execute('''
CREATE TABLE IF NOT EXISTS podcasts (
    id SERIAL PRIMARY KEY,
    date TEXT,
    category TEXT,
    rank TEXT,
    title TEXT,
    host TEXT
)
''')
conn.commit()

# 定義各類別對應的 genre 參數
genre_mapping = {
    "熱門": None,
}

# Apple RSS feed 的 URL（台灣地區，限制 200 筆資料）
base_url = "https://itunes.apple.com/tw/rss/toppodcasts/limit=200/{}xml"

# 定義 XML 解析時使用的命名空間
ns = {
    'atom': 'http://www.w3.org/2005/Atom',
    'im': 'http://itunes.apple.com/rss'
}

for category, genre in genre_mapping.items():
    if genre:
        rss_url = base_url.format(f"genre={genre}/")
    else:
        rss_url = base_url.format("")
    
    print(f"開始處理類別：{category}，RSS URL：{rss_url}")
    try:
        response = requests.get(rss_url)
        response.raise_for_status()
    except Exception as e:
        print(f"取得 URL {rss_url} 時發生錯誤：{e}")
        continue

    try:
        root = ET.fromstring(response.content)
    except Exception as e:
        print(f"解析 RSS XML 時發生錯誤（{rss_url}）：{e}")
        continue

    # 取得所有 <entry> 節點，每個 entry 代表一筆排行榜資料
    entries = root.findall('atom:entry', ns)
    print(f"類別 {category} 共找到 {len(entries)} 筆資料")

    # 取得目前日期與時間
    current_datetime = datetime.now().strftime("%Y/%m/%d %H:%M")

    # 遍歷所有資料，依序編號作為排行榜名次
    for index, entry in enumerate(entries, start=1):
        title_elem = entry.find('im:name', ns)
        title = title_elem.text.strip() if title_elem is not None else "未知標題"
        artist_elem = entry.find('im:artist', ns)
        host = artist_elem.text.strip() if artist_elem is not None else "未知主持人"
        rank = str(index)

        cursor.execute('''
            INSERT INTO podcasts (date, category, rank, title, host)
            VALUES (%s, %s, %s, %s, %s)
        ''', (current_datetime, category, rank, title, host))
    
    conn.commit()
    print(f"類別 {category} 的資料已儲存至 Supabase 資料庫。")

cursor.close()
conn.close()
print("所有資料已處理完成，資料庫連線已關閉。")

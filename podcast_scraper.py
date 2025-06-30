import socket
# ... (您的 socket IPv4 強制設定，無需變動)
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

# --- 1. 建立新的正規化資料表結構 ---
print("正在建立/確認資料表結構...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS podcasts_info (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    host TEXT,
    UNIQUE(title, host) -- 確保 Podcast 的唯一性
);
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE -- 確保類別名稱的唯一性
);
CREATE TABLE IF NOT EXISTS rankings (
    id SERIAL PRIMARY KEY,
    ranking_date TIMESTAMPTZ NOT NULL,
    rank SMALLINT NOT NULL,
    podcast_id INTEGER REFERENCES podcasts_info(id),
    category_id INTEGER REFERENCES categories(id)
);
''')
conn.commit()
print("資料表結構完成。")


# --- 2. 輔助函式：取得或建立 ID ---
def get_or_create_podcast_id(title, host):
    cursor.execute("SELECT id FROM podcasts_info WHERE title = %s AND host = %s", (title, host))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO podcasts_info (title, host) VALUES (%s, %s) RETURNING id", (title, host))
        conn.commit()
        return cursor.fetchone()[0]

def get_or_create_category_id(name):
    cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO categories (name) VALUES (%s) RETURNING id", (name,))
        conn.commit()
        return cursor.fetchone()[0]

# 定義各類別對應的 genre 參數 (與您原有的相同)
genre_mapping = {
    "熱門": None, "社會與文化": "1324", "教育": "1304", "商業": "1321",
    "新聞": "1489", "兒童與家庭": "1305", "兒童教育": "1519", "兒童故事": "1520",
    "喜劇": "1303", "健康與瘦身": "1512", "語言學習": "1498", "自我成長": "1500",
    "運動": "1545", "休閒": "1502", "藝術": "1301", "人際關係": "1544",
    "個人日誌": "1302", "心理健康": "1517", "宗教與精神生活": "1314",
    "犯罪紀實": "1488", "電視與電影": "1309", "科技": "1318", "歷史": "1487",
    "音樂": "1310", "小說": "1483", "科學": "1533", "書籍": "1482",
    "子女教養": "1521", "紀實": "1543", "創業": "1493", "政府": "1511"
}

base_url = "https://itunes.apple.com/tw/rss/toppodcasts/limit=200/{}xml"
ns = {'atom': 'http://www.w3.org/2005/Atom', 'im': 'http://itunes.apple.com/rss'}

# 取得目前日期與時間 (只需取得一次)
current_datetime = datetime.now()

for category_name, genre in genre_mapping.items():
    if genre:
        rss_url = base_url.format(f"genre={genre}/")
    else:
        rss_url = base_url.format("")
    
    print(f"開始處理類別：{category_name}，RSS URL：{rss_url}")
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

    entries = root.findall('atom:entry', ns)
    print(f"類別 {category_name} 共找到 {len(entries)} 筆資料")
    
    # --- 3. 取得類別 ID ---
    category_id = get_or_create_category_id(category_name)

    # 遍歷所有資料，依序編號作為排行榜名次
    for index, entry in enumerate(entries, start=1):
        title_elem = entry.find('im:name', ns)
        title = title_elem.text.strip() if title_elem is not None else "未知標題"
        artist_elem = entry.find('im:artist', ns)
        host = artist_elem.text.strip() if artist_elem is not None else "未知主持人"
        rank = index

        # --- 4. 取得 Podcast ID，並插入排名資料 ---
        podcast_id = get_or_create_podcast_id(title, host)
        
        cursor.execute('''
            INSERT INTO rankings (ranking_date, rank, podcast_id, category_id)
            VALUES (%s, %s, %s, %s)
        ''', (current_datetime, rank, podcast_id, category_id))
    
    conn.commit()
    print(f"類別 {category_name} 的資料已儲存完畢。")

cursor.close()
conn.close()
print("所有資料已處理完成，資料庫連線已關閉。")

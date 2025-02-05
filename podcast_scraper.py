import sys
sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sqlite3
from datetime import datetime

# 設定 WebDriver 路徑
driver_path = r'./msedgedriver.exe'
service = Service(driver_path)
driver = webdriver.Edge(service=service)

# 目標網址列表
urls = [
    'https://podcasts.apple.com/tw/charts',
    'https://podcasts.apple.com/tw/charts?genre=1324',
    'https://podcasts.apple.com/tw/charts?genre=1303',
    'https://podcasts.apple.com/tw/charts?genre=1489',
    'https://podcasts.apple.com/tw/charts?genre=1304',
    'https://podcasts.apple.com/tw/charts?genre=1321',
    'https://podcasts.apple.com/tw/charts?genre=1512',
    'https://podcasts.apple.com/tw/charts?genre=1301',
    'https://podcasts.apple.com/tw/charts?genre=1310',
    'https://podcasts.apple.com/tw/charts?genre=1314',
    'https://podcasts.apple.com/tw/charts?genre=1545',
    'https://podcasts.apple.com/tw/charts?genre=1533',
    'https://podcasts.apple.com/tw/charts?genre=1487',
    'https://podcasts.apple.com/tw/charts?genre=1488',
    'https://podcasts.apple.com/tw/charts?genre=1318',
    'https://podcasts.apple.com/tw/charts?genre=1305',
    'https://podcasts.apple.com/tw/charts?genre=1309',
    'https://podcasts.apple.com/tw/charts?genre=1502',
    'https://podcasts.apple.com/tw/charts?genre=1483',
    'https://podcasts.apple.com/tw/charts?genre=1511'
]

# 建立 SQLite 數據庫連接和表格
conn = sqlite3.connect('podcasts.db')
cursor = conn.cursor()

# 創建表格，並加入 date 字段
cursor.execute('''
CREATE TABLE IF NOT EXISTS podcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    rank TEXT,
    title TEXT,
    host TEXT
)
''')

# 定義滾動特定區域的方法
def scroll_down_element(element, scroll_pause_time, max_scrolls):
    last_height = driver.execute_script("return arguments[0].scrollHeight", element)
    for _ in range(max_scrolls):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", element)
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return arguments[0].scrollHeight", element)
        if new_height == last_height:
            break
        last_height = new_height

# 循環遍歷每個網址
for url in urls:
    try:
        # 進入每個目標網址
        driver.get(url)
        time.sleep(5)  # 等待頁面初始加載

        # 點擊 "熱門節目" 按鈕
        try:
            hot_program_button = driver.find_element(By.XPATH, "//button[contains(@class, 'title__button')]")
            actions = ActionChains(driver)
            actions.move_to_element(hot_program_button).click().perform()
            print(f"成功點擊 '熱門節目' 按鈕 - {url}")
            time.sleep(3)  # 等待頁面加載
        except Exception as e:
            print(f"點擊 '熱門節目' 按鈕時出錯 - {url}: {str(e)}")

        # 找到滾動的區域
        try:
            scroll_container = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'scrollable-page'))
            )
        except Exception as e:
            print(f"無法找到滾動區域 - {url}: {str(e)}")
            continue

        # 滾動該區域
        scroll_down_element(scroll_container, scroll_pause_time=6, max_scrolls=30)

        # 抓取滾動後的所有元素
        try:
            category_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".select-text"))
            )
            category = category_element.text.strip() if category_element else "未知類別"

            elements = driver.find_elements(By.CLASS_NAME, 'product-lockup__content')

            print(f"{url} 共找到 {len(elements)} 個元素")
            
            # 獲取當下的日期與時間
            current_datetime = datetime.now().strftime("%Y/%m/%d %H:%M")

            # 抓取並儲存資料到 SQLite 數據庫
            for index, element in enumerate(elements, start=1):
                rank = element.find_element(By.CSS_SELECTOR, ".product-lockup__ordinal.svelte-18go8ze").text.strip()
                title = element.find_element(By.CSS_SELECTOR, ".product-lockup__title.link.svelte-18go8ze").text.strip()
                host = element.find_element(By.CSS_SELECTOR, ".product-lockup__subtitle.svelte-18go8ze").text.strip()

                cursor.execute('INSERT INTO podcasts (date, category, rank, title, host) VALUES (?, ?, ?, ?, ?)', 
                               (current_datetime, category, rank, title, host))

            conn.commit()
            print(f"{url} 資料已成功儲存到 'podcasts.db'。")

        except Exception as e:
            print(f"抓取資料時出錯 - {url}: {str(e)}")

    except Exception as e:
        print(f"無法加載頁面 - {url}: {str(e)}")

# 結束 WebDriver
driver.quit()

# 關閉數據庫連接
conn.close()
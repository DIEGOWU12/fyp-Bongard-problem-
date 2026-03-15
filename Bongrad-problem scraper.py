import requests
from bs4 import BeautifulSoup
import time
import random
import os
import csv
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Lock

# ==========================================================
# 1. 参数设置
# ==========================================================
BASE_URL = "https://oebp.org/BP"
START_ID = 1
END_ID = 5000
TARGET_COUNT = 1000 

OUTPUT_DIR = "Bongard_Dataset_v2"
SOLUTION_FILE = os.path.join(OUTPUT_DIR, "solutions_and_images.csv")
REPORT_FILE = os.path.join(OUTPUT_DIR, "patterns_report.txt") # 新增报告文件

MAX_WORKERS = 7
success_count = 0
count_lock = Lock()
report_lock = Lock()

# ==========================================================
# 2. Session设置
# ==========================================================
session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."}
retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)
session.headers.update(HEADERS)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ==========================================================
# 4. 下载逻辑 (保持你的原版，支持任意数量)
# ==========================================================
def download_image(img_url, filename, bp_id):
    bp_dir = os.path.join(OUTPUT_DIR, f"BP{bp_id}")
    os.makedirs(bp_dir, exist_ok=True)
    image_path = os.path.join(bp_dir, filename)
    if os.path.exists(image_path):
        return os.path.join(f"BP{bp_id}", filename)
    try:
        r = session.get(img_url, timeout=10)
        if r.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(r.content)
            return os.path.join(f"BP{bp_id}", filename)
    except: pass
    return "download_failed"

# ==========================================================
# 6. 核心修改：放宽数量限制并记录报告
# ==========================================================
def fetch_problem(bp_id):
    global success_count
    url = f"{BASE_URL}{bp_id}"

    try:
        r = session.get(url, timeout=10)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, "html.parser")

        # 只要是 examples 目录下的图都抓
        img_tags = soup.find_all("img", src=lambda src: src and "/examples/" in src)
        img_count = len(img_tags)

        # 满足最少 12 张的要求
        if img_count < 12: return None

        # --- 记录大于 12 张的题目 ---
        if img_count > 12:
            with report_lock:
                with open(REPORT_FILE, "a", encoding="utf-8") as rf:
                    rf.write(f"ID: BP{bp_id} | Total Images: {img_count}\n")

        # 提取 solution 逻辑保持不变
        solution_text = "No solution found"
        link = soup.find("a", href=f"/BP{bp_id}", string=f"BP{bp_id}")
        if link and link.find_parent("tr"):
            tds = link.find_parent("tr").find_all("td")
            if len(tds) >= 3: solution_text = tds[2].get_text(strip=True)

        # 下载所有抓到的图片
        image_paths = []
        for img in img_tags:
            src = img["src"]
            img_url = urljoin("https://oebp.org", src)
            filename = os.path.basename(src)
            path = download_image(img_url, filename, bp_id)
            image_paths.append(path)

        print(f"✅ BP{bp_id} success (Found {img_count} images)")

        return {
            "BP_ID": f"BP{bp_id}",
            "solution": solution_text,
            "image_paths": image_paths
        }

    except Exception as e:
        print(f"❌ BP{bp_id} error {e}")
        return None

# ==========================================================
# 7. 主程序
# ==========================================================
if __name__ == "__main__":
    # 初始化报告文件
    with open(REPORT_FILE, "w", encoding="utf-8") as rf:
        rf.write("--- Bongard Problems with > 12 Images ---\n")

    print(f"🚀 Start crawling...")

    with open(SOLUTION_FILE, "w", newline="", encoding="utf-8") as f:
        # 注意：CSV 还是只预留 12 个列，多出的图会存在文件夹里，但不会写进这个 CSV
        # 如果你也想让 CSV 动态变长，可以告诉我
        fieldnames = ["BP_ID", "solution"] + [f"Image_{i+1}_path" for i in range(12)]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(fetch_problem, i): i for i in range(START_ID, END_ID+1)}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    with count_lock:
                        if success_count >= TARGET_COUNT: break
                        success_count += 1
                        current = success_count

                    row = {"BP_ID": result["BP_ID"], "solution": result["solution"]}
                    # 只写入前 12 张到 CSV，其他的都在文件夹里
                    for j in range(12):
                        row[f"Image_{j+1}_path"] = result["image_paths"][j]
                    
                    writer.writerow(row)
                    f.flush()
                    print(f"📊 Collected {current}/{TARGET_COUNT}")

    print(f"\n🎉 Finished! Report saved in {REPORT_FILE}")
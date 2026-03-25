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
# ✅ 你的目标 BP（替换 START_ID / END_ID）
# ==========================================================
TARGET_IDS = [284,344,351,352,356,379,523,524,529,533,559,
              802,809,860,869,917,935,966,997,998,1003,
              1008,1012,1033,1065,1093,1115,1116,1118,
              1122,1184,1187,1200,1202,1252,1258,1261,
              1262,1268,1274,1275,1283]

TARGET_COUNT = len(TARGET_IDS)

OUTPUT_DIR = "Bongard_Dataset_v2"
SOLUTION_FILE = os.path.join(OUTPUT_DIR, "solutions_and_images.csv")
REPORT_FILE = os.path.join(OUTPUT_DIR, "patterns_report.txt")

MAX_WORKERS = 5
success_count = 0
count_lock = Lock()
report_lock = Lock()

# ==========================================================
# Session
# ==========================================================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://oebp.org/"
})

retry = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================================
# ✅ NEW：一次性抓所有 solution（关键）
# ==========================================================
def load_all_solutions():
    print("📥 正在加载所有 solution...")
    url = "https://oebp.org/"
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    solutions = {}

    for row in soup.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) >= 3:
            bp_text = tds[0].get_text(strip=True)
            sol = tds[2].get_text(strip=True)

            if bp_text.startswith("BP"):
                bp_id = int(bp_text[2:])
                solutions[bp_id] = sol

    print(f"✅ 已加载 {len(solutions)} 个 solution")
    return solutions

# ==========================================================
# 下载图片（不变）
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
    except:
        pass

    return "download_failed"

# ==========================================================
# 核心函数
# ==========================================================
def fetch_problem(bp_id, solutions_dict):
    global success_count
    url = f"https://oebp.org/BP{bp_id}"

    try:
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            print(f"❌ BP{bp_id} 请求失败 {r.status_code}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        img_tags = soup.find_all("img", src=lambda src: src and "/examples/" in src)
        img_count = len(img_tags)

        if img_count < 12:
            return None

        # ✅ 正确拿 solution
        solution_text = solutions_dict.get(bp_id, "No solution found")

        # 下载图片
        image_paths = []
        for img in img_tags:
            src = img["src"]
            img_url = urljoin("https://oebp.org", src)
            filename = os.path.basename(src)

            path = download_image(img_url, filename, bp_id)
            image_paths.append(path)

        print(f"✅ BP{bp_id} success ({img_count} imgs)")

        return {
            "BP_ID": f"BP{bp_id}",
            "solution": solution_text,
            "image_paths": image_paths
        }

    except Exception as e:
        print(f"❌ BP{bp_id} error {e}")
        return None

# ==========================================================
# 主程序
# ==========================================================
if __name__ == "__main__":

    # ✅ 先加载 solution
    solutions_dict = load_all_solutions()

    with open(REPORT_FILE, "w", encoding="utf-8") as rf:
        rf.write("--- Bongard Problems with > 12 Images ---\n")

    print("🚀 Start crawling...")

    with open(SOLUTION_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["BP_ID", "solution"] + [f"Image_{i+1}_path" for i in range(12)]
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(fetch_problem, bp_id, solutions_dict): bp_id
                for bp_id in TARGET_IDS
            }

            for future in as_completed(futures):
                result = future.result()
                if result:
                    with count_lock:
                        success_count += 1
                        current = success_count

                    row = {"BP_ID": result["BP_ID"], "solution": result["solution"]}

                    for j in range(12):
                        row[f"Image_{j+1}_path"] = (
                            result["image_paths"][j] if j < len(result["image_paths"]) else ""
                        )

                    writer.writerow(row)
                    f.flush()

                    print(f"📊 Collected {current}/{TARGET_COUNT}")

    print("\n🎉 Finished!")
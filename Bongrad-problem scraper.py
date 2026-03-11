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
END_ID = 5000          # 搜索范围
TARGET_COUNT = 1000    # 想收集的题目数量

OUTPUT_DIR = "Bongard_Dataset_v2"
SOLUTION_FILE = os.path.join(OUTPUT_DIR, "solutions_and_images.csv")

MAX_WORKERS = 7

success_count = 0
count_lock = Lock()

# ==========================================================
# 2. Session设置
# ==========================================================

session = requests.Session()

HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429,500,502,503,504]
)

adapter = HTTPAdapter(max_retries=retry_strategy)

session.mount("https://",adapter)
session.mount("http://",adapter)
session.headers.update(HEADERS)

# ==========================================================
# 3. 创建目录
# ==========================================================

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ==========================================================
# 4. 下载图片
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
# 5. 保存 solution
# ==========================================================

def save_solution(bp_id, text):

    bp_dir = os.path.join(OUTPUT_DIR, f"BP{bp_id}")
    os.makedirs(bp_dir, exist_ok=True)

    path = os.path.join(bp_dir, "solution.txt")

    with open(path,"w",encoding="utf-8") as f:
        f.write(text)

    return os.path.join(f"BP{bp_id}", "solution.txt")

# ==========================================================
# 6. 爬单个题
# ==========================================================

def fetch_problem(bp_id):

    global success_count

    with count_lock:
        if success_count >= TARGET_COUNT:
            return None

    url = f"{BASE_URL}{bp_id}"

    try:

        r = session.get(url,timeout=10)

        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text,"html.parser")

        img_tags = soup.find_all(
            "img",
            src=lambda src: src and "/examples/" in src
        )

        if len(img_tags) != 12:
            return None

        # 提取 solution
        solution_text = "No solution text found"

        link = soup.find("a",href=f"/BP{bp_id}",string=f"BP{bp_id}")

        if link:

            tr = link.find_parent("tr")

            if tr:

                tds = tr.find_all("td")

                if len(tds)>=3:
                    solution_text = tds[2].get_text(strip=True)

        # 下载图片
        image_paths=[]

        for img in img_tags:

            src = img["src"]

            img_url = urljoin("https://oebp.org",src)

            filename = os.path.basename(src)

            path = download_image(img_url,filename,bp_id)

            image_paths.append(path)

        txt_path = save_solution(bp_id,solution_text)

        time.sleep(random.uniform(0.8,1.5))

        print(f"✅ BP{bp_id} success")

        return {
            "BP_ID":f"BP{bp_id}",
            "solution":solution_text,
            "solution_txt_path":txt_path,
            "image_paths":image_paths
        }

    except Exception as e:

        print(f"❌ BP{bp_id} error {e}")

        return None


# ==========================================================
# 7. 主程序
# ==========================================================

if __name__=="__main__":

    print(f"🚀 start crawling target={TARGET_COUNT}")

    with open(SOLUTION_FILE,"w",newline="",encoding="utf-8") as f:

        fieldnames = ["BP_ID","solution","solution_txt_path"] + \
                     [f"Image_{i+1}_path" for i in range(12)]

        writer = csv.DictWriter(f,fieldnames=fieldnames)

        writer.writeheader()

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

            futures = {
                executor.submit(fetch_problem,i):i
                for i in range(START_ID,END_ID+1)
            }

            for future in as_completed(futures):

                result = future.result()

                if result:

                    with count_lock:

                        if success_count >= TARGET_COUNT:
                            break

                        success_count += 1
                        current = success_count

                    row={
                        "BP_ID":result["BP_ID"],
                        "solution":result["solution"],
                        "solution_txt_path":result["solution_txt_path"]
                    }

                    for j in range(12):
                        row[f"Image_{j+1}_path"] = result["image_paths"][j]

                    writer.writerow(row)
                    f.flush()

                    print(f"📊 collected {current}/{TARGET_COUNT}")

                if success_count >= TARGET_COUNT:
                    break

    print("\n🎉 finished crawling!")
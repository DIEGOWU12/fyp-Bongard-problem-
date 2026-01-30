import requests
from bs4 import BeautifulSoup
import time
import random
import os
import csv
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ====================================================================
# 1. 设置目标和参数
# ====================================================================
BASE_URL = "https://oebp.org/BP"
START_ID = 1  
END_ID = 3000  
OUTPUT_DIR = "Bongard_Dataset_v2"
SOLUTION_FILE = os.path.join(OUTPUT_DIR, "solutions_and_images.csv")
MAX_WORKERS = 7  # 并发线程数，建议 5-10，不要太高以免被封

# 初始化 Session 提高连接效率
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
retry_strategy = Retry(
    total=3,                          # 最大重试次数
    backoff_factor=1,                 # 间隔时间系数 (1s, 2s, 4s...)
    status_forcelist=[429, 500, 502, 503, 504], # 遇到这些状态码才重试
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)
session.headers.update(HEADERS)

# 创建输出目录
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ====================================================================
# 2. 辅助函数
# ====================================================================

def download_and_save_image(img_url, filename, bp_id):
    """下载图片"""
    bp_dir = os.path.join(OUTPUT_DIR, f"BP{bp_id}")
    if not os.path.exists(bp_dir):
        os.makedirs(bp_dir)
        
    image_path = os.path.join(bp_dir, filename)
    if os.path.exists(image_path):
        return os.path.join(f"BP{bp_id}", filename)

    try:
        img_response = session.get(img_url, timeout=10)
        if img_response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(img_response.content)
            return os.path.join(f"BP{bp_id}", filename)
    except Exception:
        pass
    return "下载失败"

def save_solution_to_txt(bp_id, solution_text):
    """保存文本"""
    bp_dir = os.path.join(OUTPUT_DIR, f"BP{bp_id}")
    if not os.path.exists(bp_dir):
        os.makedirs(bp_dir)
        
    txt_path = os.path.join(bp_dir, "solution.txt")
    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(solution_text)
        return os.path.join(f"BP{bp_id}", "solution.txt")
    except Exception:
        return "写入失败"

# ====================================================================
# 3. 核心抓取逻辑
# ====================================================================

def fetch_bongard_problem(bp_id):
    """爬取单个问题的核心逻辑"""
    url = f"{BASE_URL}{bp_id}"
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- 步骤 1: 先找图片并校验数量 (核心修复点) ---
        img_tags = soup.find_all('img', src=lambda src: src and '/examples/' in src)
        if len(img_tags) != 12:
            # 图片不足 12 张，直接退出，不创建文件夹
            return None

        # --- 步骤 2: 校验通过，提取文本 ---
        solution_text = "未找到解决方案文本"
        bp_link_tag = soup.find('a', href=f'/BP{bp_id}', string=f'BP{bp_id}')
        if bp_link_tag:
            tr = bp_link_tag.find_parent('tr')
            if tr:
                tds = tr.find_all('td')
                if len(tds) >= 3:
                    solution_text = tds[2].get_text(strip=True)

        # --- 步骤 3: 开始写入磁盘 ---
        txt_path = save_solution_to_txt(bp_id, solution_text)
        
        image_paths = []
        for img_tag in img_tags:
            img_src = img_tag['src']
            img_url = urljoin("https://oebp.org", img_src)
            filename = os.path.basename(img_src)
            path = download_and_save_image(img_url, filename, bp_id)
            image_paths.append(path)

        # 模拟一点点延迟，防止给服务器太大压力
        time.sleep(random.uniform(1, 2))

        print(f"✅ BP{bp_id} 处理成功")
        return {
            'BP_ID': f"BP{bp_id}",
            'solution': solution_text,
            'solution_txt_path': txt_path,
            'image_paths': image_paths
        }

    except Exception as e:
        print(f"❌ BP{bp_id} 错误: {e}")
        return None

# ====================================================================
# 4. 执行多线程任务
# ====================================================================

if __name__ == "__main__":
    print(f"🚀 开始爬取任务，线程数: {MAX_WORKERS}...")
    
    with open(SOLUTION_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['BP_ID', 'solution', 'solution_txt_path'] + [f'Image_{i+1}_path' for i in range(12)]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # 使用线程池加速
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            future_to_bp = {executor.submit(fetch_bongard_problem, i): i for i in range(START_ID, END_ID + 1)}
            
            for future in future_to_bp:
                result = future.result()
                if result:
                    # 准备 CSV 行数据
                    row = {
                        'BP_ID': result['BP_ID'],
                        'solution': result['solution'],
                        'solution_txt_path': result['solution_txt_path']
                    }
                    for j in range(12):
                        row[f'Image_{j+1}_path'] = result['image_paths'][j] if j < len(result['image_paths']) else ''
                    
                    writer.writerow(row)
                    f.flush()  # 实时刷入硬盘，防止丢失

    print(f"\n✨ 任务完成！结果保存在: {SOLUTION_FILE}")
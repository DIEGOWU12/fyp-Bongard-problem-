import requests
from bs4 import BeautifulSoup
import time
import random
import os
import csv
from urllib.parse import urljoin # 用于拼接相对URL
# ====================================================================

# ====================================================================
# 1. 设置目标和参数
# ====================================================================
BASE_URL = "https://oebp.org/BP"
START_ID = 301  # 目标爬取 BP301 到 BP600
END_ID = 1000  # 目标爬取 BP301 到 BP1000
OUTPUT_DIR = "Bongard_Dataset_v2"
SOLUTION_FILE = os.path.join(OUTPUT_DIR, "solutions_and_images.csv")

# 2. 创建输出目录
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"创建目录: {OUTPUT_DIR}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ====================================================================
# 新增：TXT 文件保存函数
# ====================================================================
def save_solution_to_txt(bp_id, solution_text):
    """将解决方案文本保存到 BPID 对应的子文件夹中"""
    bp_dir = os.path.join(OUTPUT_DIR, f"BP{bp_id}")
    if not os.path.exists(bp_dir):
        os.makedirs(bp_dir)
        
    txt_path = os.path.join(bp_dir, "solution.txt")
    
    try:
        # 以 utf-8 编码写入文本文件
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(solution_text)
        # 返回相对路径，用于CSV中的记录（可选）
        return os.path.join(f"BP{bp_id}", "solution.txt")
    except Exception as e:
        print(f"写入 BP{bp_id} 的 TXT 文件时发生错误: {e}")
        return "TXT 写入失败"


# ====================================================================
# 下载函数 (保持不变)
# ====================================================================
def download_and_save_image(img_url, filename, bp_id):
    """下载单个图片并保存到子目录"""
    # 确保保存到 BPID 对应的子文件夹
    bp_dir = os.path.join(OUTPUT_DIR, f"BP{bp_id}")
    if not os.path.exists(bp_dir):
        os.makedirs(bp_dir)
        
    image_path = os.path.join(bp_dir, filename)
    
    # 检查文件是否已存在，避免重复下载（可选优化）
    if os.path.exists(image_path):
         return os.path.join(f"BP{bp_id}", filename)

    try:
        img_response = requests.get(img_url, headers=HEADERS, timeout=10)
        if img_response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(img_response.content)
            return os.path.join(f"BP{bp_id}", filename) # 返回相对路径 for CSV
        else:
            return f"下载失败 (状态码: {img_response.status_code})"
    except Exception as e:
        return f"下载图片时发生错误: {e}"

# ====================================================================
# 核心数据抓取函数 (解决方案定位已优化)
# ====================================================================
def fetch_bongard_problem(bp_id):
    """根据 ID 爬取单个 Bongard Problem 的数据"""
    url = f"{BASE_URL}{bp_id}"
    print(f"正在处理: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 404:
             print(f"警告: BP{bp_id} 页面不存在 (404 Not Found)。跳过。")
             return None
        elif response.status_code != 200:
            print(f"错误: 访问 {url} 失败，状态码: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        # 新增一个字段用于 TXT 文件的保存路径
        data = {'BP_ID': f"BP{bp_id}", 'solution': '未找到解决方案文本', 'image_paths': [], 'txt_path': ''}
        
        # 3. 提取文字描述 (解决方案)
        solution_text = "未找到解决方案文本"
        
        bp_link_tag = soup.find('a', href=f'/{data["BP_ID"]}', string=data["BP_ID"])

        if bp_link_tag:
            solution_tr_inner = bp_link_tag.find_parent('tr')
            
            if solution_tr_inner:
                td_list = solution_tr_inner.find_all('td')
                
                if len(td_list) >= 3:
                    solution_td = td_list[2]
                    solution_text = solution_td.get_text(strip=True)

        data['solution'] = solution_text
        
        # ***** 关键修改：将 solution 文本保存到 TXT 文件 *****
        data['txt_path'] = save_solution_to_txt(bp_id, solution_text)
        
        # 4. 提取和下载图片链接
        img_tags = soup.find_all('img', src=lambda src: src and '/examples/' in src)
        
        image_paths = []
        if img_tags:
            for index, img_tag in enumerate(img_tags):
                img_src = img_tag['src']
                img_url = urljoin("https://oebp.org", img_src)
                filename = os.path.basename(img_src)
                path = download_and_save_image(img_url, filename, bp_id)
                image_paths.append(path)
                
        data['image_paths'] = image_paths

        return data

    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 时发生错误: {e}")
        return None

# ====================================================================
# 5. 主爬取循环和数据保存
# ====================================================================
# 创建 CSV 文件并写入标题
# CSV 字段中新增 'solution_txt_path' 字段
with open(SOLUTION_FILE, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['BP_ID', 'solution', 'solution_txt_path'] + [f'Image_{i+1}_path' for i in range(12)]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for i in range(START_ID, END_ID + 1):
        try:
            result = fetch_bongard_problem(i)
        except Exception as e:
            print(f"处理 BP{i} 时发生未知错误: {e}. 跳过.")
            result = None

        if result:
            # 准备要写入 CSV 的字典行
            row = {
                'BP_ID': result['BP_ID'], 
                'solution': result['solution'], 
                'solution_txt_path': result['txt_path']
            }
            
            # 填充图片路径
            for j in range(12):
                row[f'Image_{j+1}_path'] = result['image_paths'][j] if j < len(result['image_paths']) else ''

            writer.writerow(row)
            
            print("--- 爬取成功 ---")
            print(f"BP{i} 描述: {result['solution']}")
            print(f"BP{i} TXT 文件已保存到: {result['txt_path']}")
            print(f"BP{i} 已下载 {len(result['image_paths'])} 张图片到 {os.path.join(OUTPUT_DIR, f'BP{i}')}/")
            print("----------------\n")
            
        # 6. 设置爬取延迟
        sleep_time = random.uniform(3, 7) # 随机等待 3 到 7 秒
        time.sleep(sleep_time)

print(f"所有任务完成。数据保存在 {SOLUTION_FILE}，图片和 TXT 文件按 BPID 分文件夹保存在 {OUTPUT_DIR}/")
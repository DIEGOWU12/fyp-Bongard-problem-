import os
import json
import re

def natural_sort_key(s):
    """
    逻辑排序：确保 '10.png' 排在 '9.png' 后面
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def build_bongard_v2_dataset(dataset_path, output_json):
    all_questions = []
    
    # 1. 获取所有子文件夹 (BP2, BP3...)
    folders = [f for f in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, f))]
    
    for folder in folders:
        folder_path = os.path.join(dataset_path, folder)
        
        # 2. 扫描并按照数字逻辑排序图片
        valid_exts = ('.png', '.gif', '.jpg', '.jpeg')
        images = [img for img in os.listdir(folder_path) if img.lower().endswith(valid_exts)]
        images.sort(key=natural_sort_key) 
        
        # 3. 严格校验：必须正好 12 张图
        if len(images) != 12:
            print(f"⚠️ 跳过 {folder}: 图片数量为 {len(images)} (要求12张)")
            continue
            
        # 4. 切分 Solution.txt 里的 Left vs. Right
        sol_path = os.path.join(folder_path, "solution.txt")
        left_rule, right_rule = "Unknown", "Unknown"
        
        if os.path.exists(sol_path):
            try:
                with open(sol_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # 使用正则兼容 "vs.", "vs", "VS" 等写法
                    parts = re.split(r'\s+vs\.?\s+', content, flags=re.IGNORECASE)
                    if len(parts) == 2:
                        left_rule, right_rule = parts[0].strip(), parts[1].strip()
                    else:
                        left_rule = content
            except Exception as e:
                print(f"❌ 读取 {folder} 的 solution 失败: {e}")

        # 5. 生成 MCQ 结构数据
        # 假设：前6张是 Context (左侧规则)，后6张是选项池
        question_entry = {
            "question_id": f"{folder}_MCQ",
            "bp_folder": folder,
            "rules": {
                "left": left_rule,
                "right": right_rule
            },
            "context": images[:6],  # 8, 9, 10, 11, 12, 13
            "options_pool": images[6:], # 14, 15, 16, 17, 18, 19
            "metadata": {
                "total_images": 12,
                "path": folder_path
            }
        }
        
        all_questions.append(question_entry)
        print(f"✅ 已加入 {folder} | 规则: {left_rule} ⬅️ VS ➡️ {right_rule}")

    # 6. 最终保存
    final_db = {
        "dataset_info": "Bongard MCQ V2 - Cleaned",
        "total_valid_problems": len(all_questions),
        "questions": all_questions
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_db, f, indent=4, ensure_ascii=False)
    
    print(f"\n✨ 大功告成！生成的数据库包含 {len(all_questions)} 个合规问题。")
    print(f"📂 结果保存至: {output_json}")

# --- 配置你的路径 ---
target_dir = r"C:\Users\fypuser\Documents\fyp-Bongard-problem-\Bongard_Dataset_v2" 
output_file = "bongard_v2_final.json"

build_bongard_v2_dataset(target_dir, output_file)
import os
import json
import re
import random

# 设置随机种子，确保每次运行生成的题目顺序和选项一致（方便实验复现）
random.seed(42)

def natural_sort_key(s):
    """
    逻辑排序：确保 '10.png' 排在 '9.png' 后面，而不是 '1.png' 后面
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def build_dual_mcq_dataset(dataset_path, output_json):
    all_questions = []
    
    # 统计项
    stats = {
        "total_folders_scanned": 0,
        "valid_bp_count": 0,
        "skipped_folders_count": 0,
        "total_questions_generated": 0
    }
    
    # 1. 获取所有子文件夹
    if not os.path.exists(dataset_path):
        print(f"❌ 错误：找不到文件夹路径 {dataset_path}")
        return

    folders = [f for f in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, f))]
    stats["total_folders_scanned"] = len(folders)
    
    print(f"开始扫描目录: {dataset_path} ...\n")

    for folder in folders:
        folder_path = os.path.join(dataset_path, folder)
        
        # 2. 扫描图片并排序
        valid_exts = ('.png', '.gif', '.jpg', '.jpeg')
        images = [img for img in os.listdir(folder_path) if img.lower().endswith(valid_exts)]
        images.sort(key=natural_sort_key) 
        
        # 3. 严格校验：必须正好 12 张图 (左6右6)
        if len(images) != 12:
            stats["skipped_folders_count"] += 1
            # print(f"⚠️ 跳过 {folder}: 图片数量为 {len(images)}")
            continue
            
        stats["valid_bp_count"] += 1
        left_images = images[:6]   # 正向组 (Positive)
        right_images = images[6:]  # 反向组 (Negative)

        # 4. 切分 Solution.txt 里的 Left vs. Right 规则
        sol_path = os.path.join(folder_path, "solution.txt")
        l_rule, r_rule = "Unknown Left Rule", "Unknown Right Rule"
        
        if os.path.exists(sol_path):
            try:
                with open(sol_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    parts = re.split(r'\s+vs\.?\s+', content, flags=re.IGNORECASE)
                    if len(parts) == 2:
                        l_rule, r_rule = parts[0].strip(), parts[1].strip()
                    else:
                        l_rule = content
            except:
                pass

        # --- 任务 A: 考察左侧规则 (Positive Task) ---
        # 选一张左图作为答案，其余5张左图作为Context，3张右图作为干扰项
        ans_idx_l = random.randint(0, 5)
        correct_img_l = left_images[ans_idx_l]
        context_l = [img for i, img in enumerate(left_images) if i != ans_idx_l]
        distractors_l = random.sample(right_images, 3)
        
        options_l = [correct_img_l] + distractors_l
        random.shuffle(options_l)
        
        q_pos = {
            "question_id": f"{folder}_Pos",
            "bp": folder,
            "target_side": "left",
            "rule_description": l_rule,
            "context": context_l,
            "options": options_l,
            "correct": chr(65 + options_l.index(correct_img_l)),
            "correct_image": correct_img_l
        }

        # --- 任务 B: 考察右侧规则 (Negative Task) ---
        # 选一张右图作为答案，其余5张右图作为Context，3张左图作为干扰项
        ans_idx_r = random.randint(0, 5)
        correct_img_r = right_images[ans_idx_r]
        context_r = [img for i, img in enumerate(right_images) if i != ans_idx_r]
        distractors_r = random.sample(left_images, 3)
        
        options_r = [correct_img_r] + distractors_r
        random.shuffle(options_r)
        
        q_neg = {
            "question_id": f"{folder}_Neg",
            "bp": folder,
            "target_side": "right",
            "rule_description": r_rule,
            "context": context_r,
            "options": options_r,
            "correct": chr(65 + options_r.index(correct_img_r)),
            "correct_image": correct_img_r
        }

        all_questions.append(q_pos)
        all_questions.append(q_neg)
        stats["total_questions_generated"] += 2

    # 5. 保存结果
    final_output = {
        "dataset_info": "Bongard Dual-Task MCQ Dataset",
        "statistics": stats,
        "questions": all_questions
    }
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4, ensure_ascii=False)
    
    # 6. 打印汇总报告
    print("\n" + "="*40)
    print("📊 BONGARD 数据集生成报告")
    print("-" * 40)
    print(f"📂 扫描文件夹总数:  {stats['total_folders_scanned']}")
    print(f"✅ 合规 BP 数量:    {stats['valid_bp_count']}")
    print(f"⚠️ 跳过无效文件夹:  {stats['skipped_folders_count']}")
    print(f"📝 生成题目总数:    {stats['total_questions_generated']} (1 BP -> 2 Tasks)")
    print("-" * 40)
    print(f"💾 结果已保存至: {output_json}")
    print("="*40 + "\n")

# --- 修改为你电脑上的实际路径 ---
# 建议使用 r"..." 原始字符串防止转义字符错误
MY_DATASET_PATH = r"C:\Users\fypuser\Documents\fyp-Bongard-problem-\Bongard_Dataset_v2"
OUTPUT_FILENAME = "bongard_v2_dual_tasks.json"

if __name__ == "__main__":
    build_dual_mcq_dataset(MY_DATASET_PATH, OUTPUT_FILENAME)
import os
import shutil
import itertools
import textwrap
from PIL import Image, ImageDraw, ImageFont

# ====================================================================
# --- 配置参数 ---
# ====================================================================
SOURCE_DIR = "Bongard_Dataset_v2"
TARGET_DIR = "bongard_augmented_dataset_v3"

os.makedirs(TARGET_DIR, exist_ok=True)

# 你的分类名单
RIGHT_7 = [284, 344, 351, 529, 533, 809, 917, 1003, 1008, 1065, 1115, 1122, 1184, 1202, 1283, 559]
LEFT_7 = [352, 356, 523, 524, 860, 869, 935, 1093, 1116, 1261, 1262, 1275]
LEFT_8 = [379, 802, 998, 1012, 1258, 1268]
BOTH_7 = [966, 1033, 1274]
RIGHT_8 = [997, 1118, 1187, 1200, 1252]

# 布局常量
SINGLE_IMG_SIZE = 100 # 稍微调大一点，12宫格更清晰
IMG_PADDING = 10
SUB_GRID_ROWS, SUB_GRID_COLS = 3, 2
GROUP_SPACING = 30
SINGLE_GROUP_WIDTH = SUB_GRID_COLS * SINGLE_IMG_SIZE + (SUB_GRID_COLS + 1) * IMG_PADDING
SINGLE_GROUP_HEIGHT = SUB_GRID_ROWS * SINGLE_IMG_SIZE + (SUB_GRID_ROWS + 1) * IMG_PADDING
IMG_AREA_WIDTH = (SINGLE_GROUP_WIDTH * 2) + GROUP_SPACING
IMG_AREA_HEIGHT = SINGLE_GROUP_HEIGHT

def save_variant_folder(bp_id, left_imgs, right_imgs, solution_text, variant_idx):
    """
    核心修改：为每个变体创建 BPxx_cx 文件夹，并存入 combined.png 和 solution.txt
    """
    # 1. 创建子文件夹路径，例如: bongard_augmented_dataset/BP284_c1/
    variant_folder_name = f"BP{bp_id}_c{variant_idx}"
    variant_path = os.path.join(TARGET_DIR, variant_folder_name)
    os.makedirs(variant_path, exist_ok=True)

    # 2. 绘制拼图 (不带右侧文字区，因为文字已单独存为 txt)
    combined_img = Image.new("RGB", (IMG_AREA_WIDTH, IMG_AREA_HEIGHT), "white")
    draw = ImageDraw.Draw(combined_img)
    all_imgs = list(left_imgs) + list(right_imgs)

    for i, img_path in enumerate(all_imgs):
        try:
            with Image.open(img_path) as img:
                img_resized = img.convert("RGB").resize((SINGLE_IMG_SIZE, SINGLE_IMG_SIZE))
            
            # 布局计算
            offset_x = 0 if i < 6 else (SINGLE_GROUP_WIDTH + GROUP_SPACING)
            idx = i if i < 6 else i - 6
            x = offset_x + IMG_PADDING + (idx % SUB_GRID_COLS) * (SINGLE_IMG_SIZE + IMG_PADDING)
            y = IMG_PADDING + (idx // SUB_GRID_COLS) * (SINGLE_IMG_SIZE + IMG_PADDING)
            
            draw.rectangle([x-1, y-1, x+SINGLE_IMG_SIZE, y+SINGLE_IMG_SIZE], outline=(200, 200, 200))
            combined_img.paste(img_resized, (x, y))
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

    # 画中间分隔线
    center_x = SINGLE_GROUP_WIDTH + GROUP_SPACING // 2
    draw.line([(center_x, 20), (center_x, IMG_AREA_HEIGHT - 20)], fill="lightgray", width=1)

    # 3. 保存 combined.png
    combined_img.save(os.path.join(variant_path, "combined.png"), "PNG")

    # 4. 保存 solution.txt
    with open(os.path.join(variant_path, "solution.txt"), "w", encoding="utf-8") as f:
        f.write(solution_text)

def process_special_bp(bp_id):
    folder_path = os.path.join(SOURCE_DIR, f"BP{bp_id}")
    if not os.path.exists(folder_path): return
    
    # 筛选小图，排除可能存在的 combined 图
    imgs = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                   if f.lower().endswith(('.png','.jpg')) and "combined" not in f])
    
    sol_path = os.path.join(folder_path, "solution.txt")
    solution = open(sol_path, "r", encoding="utf-8").read().strip() if os.path.exists(sol_path) else ""

    # 根据你的分类逻辑分配图片池
    if bp_id in RIGHT_7:
        left_pool, right_pool = imgs[:6], imgs[6:13]
    elif bp_id in LEFT_7:
        left_pool, right_pool = imgs[:7], imgs[7:13]
    elif bp_id in LEFT_8:
        left_pool, right_pool = imgs[:8], imgs[8:14]
    elif bp_id in BOTH_7:
        left_pool, right_pool = imgs[:7], imgs[7:14]
    elif bp_id in RIGHT_8:
        left_pool, right_pool = imgs[:6], imgs[6:14]
    else: return

    # 组合生成
    left_combos = list(itertools.combinations(left_pool, 6))
    right_combos = list(itertools.combinations(right_pool, 6))
    
    variant_count = 0
    for l_set in left_combos:
        for r_set in right_combos:
            variant_count += 1
            save_variant_folder(bp_id, l_set, r_set, solution, variant_count)
    
    print(f"📦 BP{bp_id}: 已生成 {variant_count} 个变体文件夹")

if __name__ == "__main__":
    special_list = RIGHT_7 + LEFT_7 + LEFT_8 + BOTH_7 + RIGHT_8
    print("🚀 开始数据增强（文件夹结构版）...")
    
    for bid in sorted(special_list):
        process_special_bp(bid)
    
    print(f"\n✅ 任务完成！请查看 '{TARGET_DIR}' 文件夹。")
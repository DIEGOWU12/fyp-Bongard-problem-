import os
import textwrap
import itertools
from PIL import Image, ImageDraw, ImageFont

# ====================================================================
# --- 配置参数 ---
# ====================================================================
SOURCE_DIR = "Bongard_Dataset_v2"
TARGET_DIR = "bongard_augmented_dataset"

os.makedirs(TARGET_DIR, exist_ok=True)

# 你的分类名单 (保持不变)
RIGHT_7 = [284, 344, 351, 529, 533, 809, 917, 1003, 1008, 1065, 1115, 1122, 1184, 1202, 1283, 559]
LEFT_7 = [352, 356, 523, 524, 860, 869, 935, 1093, 1116, 1261, 1262, 1275]
LEFT_8 = [379, 802, 998, 1012, 1258, 1268]
BOTH_7 = [966, 1033, 1274]
RIGHT_8 = [997, 1118, 1187, 1200, 1252]

# 全局计数器
total_combined_images = 0
total_folders_processed = 0

# 布局常量 (保持和你之前的一致)
SINGLE_IMG_SIZE = 60
IMG_PADDING = 10
SUB_GRID_ROWS, SUB_GRID_COLS = 3, 2
GROUP_SPACING = 20
TEXT_AREA_WIDTH = 350
TEXT_PADDING = 20
SINGLE_GROUP_WIDTH = SUB_GRID_COLS * SINGLE_IMG_SIZE + (SUB_GRID_COLS + 1) * IMG_PADDING
SINGLE_GROUP_HEIGHT = SUB_GRID_ROWS * SINGLE_IMG_SIZE + (SUB_GRID_ROWS + 1) * IMG_PADDING
IMG_AREA_WIDTH = (SINGLE_GROUP_WIDTH * 2) + GROUP_SPACING
IMG_AREA_HEIGHT = SINGLE_GROUP_HEIGHT

try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except:
    FONT = ImageFont.load_default()

def save_combined_image(bp_id, left_imgs, right_imgs, solution_text, suffix):
    global total_combined_images
    
    # 【核心修改 1】确保画布宽度包含了文字区，高度如果文字多可以稍微加高
    full_width = IMG_AREA_WIDTH + TEXT_AREA_WIDTH
    full_height = max(IMG_AREA_HEIGHT, 300) # 确保至少有 300 像素高，防止文字被截断
    
    combined_img = Image.new("RGB", (full_width, full_height), "white")
    draw = ImageDraw.Draw(combined_img)
    all_imgs = list(left_imgs) + list(right_imgs)

    # 贴图逻辑
    for i, img_path in enumerate(all_imgs):
        try:
            with Image.open(img_path) as img:
                img_resized = img.convert("RGB").resize((SINGLE_IMG_SIZE, SINGLE_IMG_SIZE))
            offset_x = 0 if i < 6 else (SINGLE_GROUP_WIDTH + GROUP_SPACING)
            idx = i if i < 6 else i - 6
            x = offset_x + IMG_PADDING + (idx % 2) * (70)
            y = IMG_PADDING + (idx // 2) * (70)
            draw.rectangle([x-1, y-1, x+60, y+60], outline=(180, 180, 180), width=1)
            combined_img.paste(img_resized, (x, y))
        except Exception as e:
            print(f"图片加载失败: {e}")
            continue

    # 【核心修改 2】加粗分隔线，并确保文字坐标正确
    center_x = SINGLE_GROUP_WIDTH + GROUP_SPACING // 2
    # 中间分隔线
    draw.line([(center_x, 10), (center_x, IMG_AREA_HEIGHT - 10)], fill="lightgray", width=1)
    # 图片区与文字区的分界线
    draw.line([(IMG_AREA_WIDTH, 0), (IMG_AREA_WIDTH, full_height)], fill="black", width=2)

    # 【核心修改 3】文字绘制逻辑
    # 如果 solution 为空，给个提示防止完全空白
    if not solution_text:
        solution_text = "No solution text found."

    # 增加 wrap 宽度到 45，让每行多装点字
    lines = textwrap.wrap(solution_text, width=45) 
    curr_y = TEXT_PADDING
    
    for line in lines:
        # 确保文字画在 IMG_AREA_WIDTH 之后的区域
        draw.text((IMG_AREA_WIDTH + TEXT_PADDING, curr_y), line, font=FONT, fill="black")
        curr_y += 22 # 稍微收紧行高，防止文字太长掉出屏幕

    combined_img.save(os.path.join(TARGET_DIR, f"BP{bp_id}_{suffix}.png"))
    total_combined_images += 1

def process_special_bp(bp_id):
    global total_folders_processed
    folder_path = os.path.join(SOURCE_DIR, f"BP{bp_id}")
    if not os.path.exists(folder_path): return
    
    total_folders_processed += 1
    imgs = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.png','.jpg'))])
    sol_path = os.path.join(folder_path, "solution.txt")
    solution = open(sol_path, "r", encoding="utf-8").read().strip() if os.path.exists(sol_path) else ""

    # 分配逻辑
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
    
    current_bp_count = 0
    for l_idx, l_set in enumerate(left_combos):
        for r_idx, r_set in enumerate(right_combos):
            current_bp_count += 1
            save_combined_image(bp_id, l_set, r_set, solution, f"c{current_bp_count}")
    
    print(f"📦 BP{bp_id}: 已生成 {current_bp_count} 个变体")
    print(f"Checking: {sol_path}, exists={os.path.exists(sol_path)}")

if __name__ == "__main__":
    special_list = RIGHT_7 + LEFT_7 + LEFT_8 + BOTH_7 + RIGHT_8
    print("🚀 开始数据增强任务...")
    
    for bid in sorted(special_list):
        process_special_bp(bid)
    
    print("-" * 30)
    print(f"📊 数据集汇总报告:")
    print(f"  - 总处理文件夹数: {total_folders_processed}")
    print(f"  - 总生成的组合图片数: {total_combined_images}")
    print(f"✅ 所有图片已保存在 '{TARGET_DIR}' 文件夹中。")
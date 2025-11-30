from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# ====================================================================
# --- 配置参数 ---
# ====================================================================
OUTPUT_DIR = "Bongard_Dataset_v2"

# --- 布局常量 ---
SUB_GRID_ROWS = 3
SUB_GRID_COLS = 2
NUM_IMAGES_PER_GROUP = SUB_GRID_ROWS * SUB_GRID_COLS  # 6

SINGLE_IMG_SIZE = 60
IMG_PADDING = 5

SINGLE_GROUP_WIDTH = SUB_GRID_COLS * SINGLE_IMG_SIZE + (SUB_GRID_COLS + 1) * IMG_PADDING
SINGLE_GROUP_HEIGHT = SUB_GRID_ROWS * SINGLE_IMG_SIZE + (SUB_GRID_ROWS + 1) * IMG_PADDING

GROUP_SPACING = IMG_PADDING * 2

IMG_AREA_WIDTH = (SINGLE_GROUP_WIDTH * 2) + GROUP_SPACING
IMG_AREA_HEIGHT = SINGLE_GROUP_HEIGHT

TEXT_AREA_WIDTH = 350
TEXT_PADDING = 20

try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    print("警告: 找不到 'arial.ttf'，使用默认字体。")
    FONT = ImageFont.load_default()


# ====================================================================
# 核心：合并单个 BP 文件夹
# ====================================================================
def combine_folder_images(bp_id):
    bp_folder = f"BP{bp_id}"
    folder_path = os.path.join(OUTPUT_DIR, bp_folder)

    if not os.path.exists(folder_path):
        print(f"⚠ 文件夹 {bp_folder} 不存在，跳过。")
        return False

    # 读取 PNG 文件
    img_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(".png")])
    img_files = [f for f in img_files if not f.endswith("_combined.png")]  # 避免重复合并

    if len(img_files) != 12:
        print(f"⚠ BP{bp_id}: 仅找到 {len(img_files)} 张，跳过（需要 12 张）")
        return False

    # 读取 solution.txt
    txt_path = os.path.join(folder_path, "solution.txt")
    if os.path.exists(txt_path):
        try:
            solution_text = open(txt_path, "r", encoding="utf-8").read().strip()
        except:
            solution_text = f"BP{bp_id} - solution.txt 读取失败"
    else:
        solution_text = f"BP{bp_id} - 未找到解决方案文本"

    # 创建新画布
    TOTAL_WIDTH = IMG_AREA_WIDTH + TEXT_AREA_WIDTH
    TOTAL_HEIGHT = IMG_AREA_HEIGHT
    combined_img = Image.new("RGB", (TOTAL_WIDTH, TOTAL_HEIGHT), "white")
    draw = ImageDraw.Draw(combined_img)

    # 布局图片
    for i in range(len(img_files)):
        img_path = os.path.join(folder_path, img_files[i])

        try:
            img = Image.open(img_path).convert("RGB")
            img_resized = img.resize((SINGLE_IMG_SIZE, SINGLE_IMG_SIZE))
        except Exception as e:
            print(f"❌ 图片打开失败 {img_files[i]}: {e}")
            continue

        # 判断左右组
        if i < NUM_IMAGES_PER_GROUP:
            group_offset_x = 0
            idx_in_group = i
        else:
            group_offset_x = SINGLE_GROUP_WIDTH + GROUP_SPACING
            idx_in_group = i - NUM_IMAGES_PER_GROUP

        row = idx_in_group // SUB_GRID_COLS
        col = idx_in_group % SUB_GRID_COLS

        x = group_offset_x + IMG_PADDING + col * (SINGLE_IMG_SIZE + IMG_PADDING)
        y = IMG_PADDING + row * (SINGLE_IMG_SIZE + IMG_PADDING)

        combined_img.paste(img_resized, (x, y))

    # 分隔线
    center_line_x = SINGLE_GROUP_WIDTH + GROUP_SPACING // 2
    draw.line([(center_line_x, 0), (center_line_x, TOTAL_HEIGHT)], fill="lightgray", width=1)

    main_separator_x = IMG_AREA_WIDTH
    draw.line([(main_separator_x, 0), (main_separator_x, TOTAL_HEIGHT)], fill="black", width=2)

    # 绘制文本
    text_x = main_separator_x + TEXT_PADDING
    text_y = TEXT_PADDING

    try:
        avg_char_width = FONT.getbbox("A")[2] - FONT.getbbox("A")[0]
        line_height = FONT.getbbox("Tg")[3] - FONT.getbbox("Tg")[1] + 5
    except:
        avg_char_width = 10
        line_height = 20

    max_chars_per_line = int((TEXT_AREA_WIDTH - 2 * TEXT_PADDING) / avg_char_width * 1.2)
    wrapped_lines = textwrap.wrap(solution_text, width=max_chars_per_line)

    for line in wrapped_lines:
        draw.text((text_x, text_y), line, font=FONT, fill="black")
        text_y += line_height

    # 保存
    out_path = os.path.join(folder_path, f"BP{bp_id}_combined.png")
    combined_img.save(out_path)
    print(f"✅ BP{bp_id} 合并完成 → {out_path}")
    return True


# ====================================================================
# 主程序：自动扫描 Bongard_Dataset_v2
# ====================================================================
if __name__ == "__main__":
    print("🔍 正在扫描 Bongard_Dataset_v2 ...")

    all_bp_folders = sorted(
        [d for d in os.listdir(OUTPUT_DIR) if d.startswith("BP") and d[2:].isdigit()],
        key=lambda x: int(x[2:])
    )

    print(f"📁 找到 {len(all_bp_folders)} 个 BP 文件夹，开始合并...\n")

    for folder in all_bp_folders:
        bp_id = int(folder[2:])
        combine_folder_images(bp_id)

    print("\n🎉 所有完成！")

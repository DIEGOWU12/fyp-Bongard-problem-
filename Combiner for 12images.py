import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

# --- 布局常量 ---
SUB_GRID_ROWS = 3
SUB_GRID_COLS = 2
NUM_IMAGES_PER_GROUP = 6

SINGLE_IMG_SIZE = 60
IMG_PADDING = 10

SINGLE_GROUP_WIDTH = SUB_GRID_COLS * SINGLE_IMG_SIZE + (SUB_GRID_COLS + 1) * IMG_PADDING
SINGLE_GROUP_HEIGHT = SUB_GRID_ROWS * SINGLE_IMG_SIZE + (SUB_GRID_ROWS + 1) * IMG_PADDING

GROUP_SPACING = IMG_PADDING * 2

IMG_AREA_WIDTH = (SINGLE_GROUP_WIDTH * 2) + GROUP_SPACING
IMG_AREA_HEIGHT = SINGLE_GROUP_HEIGHT

TEXT_AREA_WIDTH = 350
TEXT_PADDING = 20

SOURCE_DIR = r"C:\Users\fypuser\Documents\fyp-Bongard-problem-\Bongard_Dataset_v2"
TARGET_DIR = r"C:\Users\fypuser\Documents\fyp-Bongard-problem-\Bongard_Dataset_v2_processed"

# --- 字体 ---
try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    FONT = ImageFont.load_default()


# ====================================================================
# 核心函数
# ====================================================================
def process_and_move(bp_id):
    bp_folder = f"BP{bp_id}"
    folder_path = os.path.join(SOURCE_DIR, bp_folder)

    if not os.path.exists(folder_path):
        return False

    # 1. 筛选图片
    valid_extensions = (".png", ".gif", ".jpg", ".jpeg")
    img_files = sorted([
        f for f in os.listdir(folder_path)
        if f.lower().endswith(valid_extensions) and not f.endswith("_combined.png")
    ])

    if len(img_files) != 12:
        print(f"⚠ BP{bp_id}: 图片数量为 {len(img_files)} (需要 12)，跳过。")
        return False

    # 2. 读取文字
    txt_path = os.path.join(folder_path, "solution.txt")
    solution_text = ""

    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            solution_text = f.read().strip()

    # 3. 创建画布
    combined_img = Image.new(
        "RGB",
        (IMG_AREA_WIDTH + TEXT_AREA_WIDTH, IMG_AREA_HEIGHT),
        "white"
    )
    draw = ImageDraw.Draw(combined_img)

    # 4. 贴图 + 边框
    for i in range(len(img_files)):
        img_path = os.path.join(folder_path, img_files[i])

        try:
            with Image.open(img_path) as img:
                img_resized = img.convert("RGB").resize(
                    (SINGLE_IMG_SIZE, SINGLE_IMG_SIZE)
                )

            # 分组
            group_offset_x = 0 if i < NUM_IMAGES_PER_GROUP else (SINGLE_GROUP_WIDTH + GROUP_SPACING)
            idx = i if i < NUM_IMAGES_PER_GROUP else i - NUM_IMAGES_PER_GROUP

            # 坐标
            x = group_offset_x + IMG_PADDING + (idx % SUB_GRID_COLS) * (SINGLE_IMG_SIZE + IMG_PADDING)
            y = IMG_PADDING + (idx // SUB_GRID_COLS) * (SINGLE_IMG_SIZE + IMG_PADDING)

            # 边框
            border_rect = [x - 1, y - 1, x + SINGLE_IMG_SIZE, y + SINGLE_IMG_SIZE]
            draw.rectangle(border_rect, outline=(180, 180, 180), width=1)

            # 粘贴
            combined_img.paste(img_resized, (x, y))

        except Exception as e:
            print(f"❌ 无法处理图片 {img_path}: {e}")

    # 5. 分隔线 + 文本
    center_x = SINGLE_GROUP_WIDTH + GROUP_SPACING // 2

    draw.line([(center_x, 10), (center_x, IMG_AREA_HEIGHT - 10)], fill="lightgray", width=1)
    draw.line([(IMG_AREA_WIDTH, 0), (IMG_AREA_WIDTH, IMG_AREA_HEIGHT)], fill="black", width=2)

    # 文本换行
    avg_char_w = 10
    try:
        avg_char_w = FONT.getbbox("A")[2] - FONT.getbbox("A")[0]
    except:
        pass

    max_chars = int((TEXT_AREA_WIDTH - 2 * TEXT_PADDING) / avg_char_w * 1.2)
    lines = textwrap.wrap(solution_text, width=max_chars)

    curr_y = TEXT_PADDING
    for line in lines:
        draw.text(
            (IMG_AREA_WIDTH + TEXT_PADDING, curr_y),
            line,
            font=FONT,
            fill="black"
        )
        curr_y += 24

    # 6. 保存
    save_path = os.path.join(TARGET_DIR, f"BP{bp_id}.png")
    combined_img.save(save_path, "PNG")

    print(f"✅ 已生成带边框图: BP{bp_id}.png")
    return True


# ====================================================================
# 主程序
# ====================================================================
if __name__ == "__main__":
    os.makedirs(TARGET_DIR, exist_ok=True)
    all_folders = sorted(
        [d for d in os.listdir(SOURCE_DIR) if d.startswith("BP") and d[2:].isdigit()],
        key=lambda x: int(x[2:])
    )

    for folder in all_folders:
        process_and_move(int(folder[2:]))

    print(f"\n🎉 全部任务完成！请查看 '{TARGET_DIR}' 文件夹。")
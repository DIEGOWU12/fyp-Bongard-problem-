from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# ====================================================================
# --- 配置参数 (请根据您的爬虫设置修改) ---
# ====================================================================
OUTPUT_DIR = "Bongard_Dataset_v2"
START_ID = 1
END_ID = 300 # 目标合并的 BP 编号范围

# --- 布局常量 ---
# Bongard Problem 的经典布局是 左右两组，每组 3 行 x 2 列
SUB_GRID_ROWS = 3 # 每组图片的行数
SUB_GRID_COLS = 2 # 每组图片的列数
NUM_IMAGES_PER_GROUP = SUB_GRID_ROWS * SUB_GRID_COLS # 每组图片数量 (6)

SINGLE_IMG_SIZE = 60 # 每张小图片尺寸
IMG_PADDING = 5 # 图片之间的内边距

# 计算单组 (3x2) 图片区域的尺寸
SINGLE_GROUP_WIDTH = SUB_GRID_COLS * SINGLE_IMG_SIZE + (SUB_GRID_COLS + 1) * IMG_PADDING
SINGLE_GROUP_HEIGHT = SUB_GRID_ROWS * SINGLE_IMG_SIZE + (SUB_GRID_ROWS + 1) * IMG_PADDING

# 两组图片之间的额外间距/分隔线宽度
GROUP_SPACING = IMG_PADDING * 2 # 增加一点间距

# 整个图片区域的总宽度和高度 (两组 3x2 图片并排)
IMG_AREA_WIDTH = (SINGLE_GROUP_WIDTH * 2) + GROUP_SPACING
IMG_AREA_HEIGHT = SINGLE_GROUP_HEIGHT # 两组的高度相同

# 文本区域的宽度
TEXT_AREA_WIDTH = 350 # 文本区域宽度
TEXT_PADDING = 20 # 文本内边距

# 字体设置 (用于文本渲染)
try:
    FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    print("警告: 找不到 'arial.ttf'，使用默认字体。文本渲染效果可能较差。")
    FONT = ImageFont.load_default()

# ====================================================================
# 核心图片合并函数 (针对单个文件夹)
# ====================================================================
def combine_folder_images(bp_id):
    """
    读取指定 BPID 文件夹内的所有 PNG 图片，按照 "左侧 3x2 + 右侧 3x2 + 文本" 布局合并。
    """
    bp_folder = f"BP{bp_id}"
    folder_path = os.path.join(OUTPUT_DIR, bp_folder)
    
    if not os.path.exists(folder_path):
        print(f"警告: 文件夹 {folder_path} 不存在。跳过 BP{bp_id}。")
        return False

    # 1. 获取图片文件列表 (只找 PNG 文件)
    # 依赖于文件名的自然排序 (如 EX1.png, EX2.png, ... EX12.png)
    img_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.png')])
    
    # 过滤掉已合并的图片文件，避免再次合并自己
    img_files = [f for f in img_files if not f.endswith('_combined.png')]
    
    if len(img_files) != 12:
        print(f"警告: BP{bp_id} 找到 {len(img_files)} 张图片，预期 12 张。跳过合并。")
        return False
    
    # 2. 获取解决方案文本
    txt_path = os.path.join(folder_path, "solution.txt")
    solution_text = f"BP{bp_id} - 解决方案文本未找到。"
    if os.path.exists(txt_path):
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                solution_text = f.read().strip()
        except Exception as e:
            print(f"读取 BP{bp_id} solution.txt 失败: {e}")
    else:
        print(f"警告: BP{bp_id} 文件夹中未找到 solution.txt。")
    
    # 3. 创建空白画布
    TOTAL_WIDTH = IMG_AREA_WIDTH + TEXT_AREA_WIDTH
    TOTAL_HEIGHT = IMG_AREA_HEIGHT
    
    combined_img = Image.new('RGB', (TOTAL_WIDTH, TOTAL_HEIGHT), color='white')
    draw = ImageDraw.Draw(combined_img)
    
    # 4. 绘制图片区域 (左侧 3x2 + 右侧 3x2 布局)
    for i in range(len(img_files)):
        img_path = os.path.join(folder_path, img_files[i])
        
        try:
            img = Image.open(img_path).convert('RGB')
            img_resized = img.resize((SINGLE_IMG_SIZE, SINGLE_IMG_SIZE))
            
            # 判断是左组图片 (0-5) 还是右组图片 (6-11)
            if i < NUM_IMAGES_PER_GROUP: # 左组 (索引 0-5)
                group_offset_x = 0
                idx_in_group = i
            else: # 右组 (索引 6-11)
                group_offset_x = SINGLE_GROUP_WIDTH + GROUP_SPACING # 右组的X轴起始点
                idx_in_group = i - NUM_IMAGES_PER_GROUP # 转换为组内索引 (0-5)
            
            # 计算组内的行和列
            row_in_group = idx_in_group // SUB_GRID_COLS
            col_in_group = idx_in_group % SUB_GRID_COLS
            
            # 计算最终的 x, y 坐标
            x = group_offset_x + IMG_PADDING + col_in_group * (SINGLE_IMG_SIZE + IMG_PADDING)
            y = IMG_PADDING + row_in_group * (SINGLE_IMG_SIZE + IMG_PADDING)
            
            combined_img.paste(img_resized, (x, y))
            
        except Exception as e:
            print(f"处理图片 {img_files[i]} 失败: {e}")
            continue
            
    # 5. 绘制分隔线
    # 绘制图片组之间的垂直分隔线
    center_line_x = SINGLE_GROUP_WIDTH + (GROUP_SPACING // 2) 
    draw.line([(center_line_x, 0), (center_line_x, TOTAL_HEIGHT)], fill='lightgray', width=1) # 细一点的灰色分隔

    # 绘制图片区域和文本区域之间的垂直分隔线
    main_separator_x = IMG_AREA_WIDTH
    draw.line([(main_separator_x, 0), (main_separator_x, TOTAL_HEIGHT)], fill='black', width=2)
    
    # 6. 绘制文本区域
    text_x = main_separator_x + TEXT_PADDING
    text_y = TEXT_PADDING
    
    try:
        avg_char_width = FONT.getbbox('A')[2] - FONT.getbbox('A')[0]
        line_height = FONT.getbbox('Tg')[3] - FONT.getbbox('Tg')[1] + 5
    except:
        avg_char_width = 10
        line_height = 20
        
    max_chars_per_line = int((TEXT_AREA_WIDTH - 2 * TEXT_PADDING) / avg_char_width * 1.2)
    wrapped_lines = textwrap.wrap(solution_text, width=max_chars_per_line)

    for line in wrapped_lines:
        draw.text((text_x, text_y), line, fill='black', font=FONT)
        text_y += line_height
        
    # 7. 保存最终图片
    output_filename = f"{bp_folder}_combined.png"
    output_path = os.path.join(folder_path, output_filename)
    combined_img.save(output_path)
    print(f"-> BP{bp_id}: 成功合并并保存到 {output_path}")
    return True

# ====================================================================
# 主运行程序 (使用 for 循环遍历 BP 编号)
# ====================================================================
if __name__ == "__main__":
    print(f"开始合并 {START_ID} 到 {END_ID} 的 Bongard Problems 数据...")
    
    for bp_id in range(START_ID, END_ID + 1):
        combine_folder_images(bp_id)
        
    print("\n所有 BP 合并任务完成。")
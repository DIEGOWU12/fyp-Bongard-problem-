from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# --- 配置参数 (必须与爬虫代码中的设置一致) ---
OUTPUT_DIR = "Bongard_Dataset_v2"
START_ID = 1
END_ID = 300 # 假设您爬取了 BP1 到 BP300

# --- 图像和布局常量 ---
# Bongard Problem 的标准布局是 2 行 x 6 列 (用于显示)
GRID_ROWS = 2 
GRID_COLS = 6
# 假设每张 Bongard 图片的标准尺寸
SINGLE_IMG_SIZE = 60 
IMG_PADDING = 5

# 图片区域总尺寸： 2 行，每行 6 列。
# 宽度 = 6 * 60 + 7 * 5 = 395
# 高度 = 2 * 60 + 3 * 5 = 135
IMG_AREA_WIDTH = GRID_COLS * SINGLE_IMG_SIZE + (GRID_COLS + 1) * IMG_PADDING
IMG_AREA_HEIGHT = GRID_ROWS * SINGLE_IMG_SIZE + (GRID_ROWS + 1) * IMG_PADDING

# 文本区域的宽度
TEXT_AREA_WIDTH = 350 # 稍微增加宽度以容纳更多文字
TEXT_PADDING = 20

# 字体设置
try:
    # 尝试加载常用字体
    FONT = ImageFont.truetype("arial.ttf", 16)
except IOError:
    # 如果找不到 Arial，使用默认点阵字体
    print("警告: 找不到 'arial.ttf'，使用默认字体。文本渲染效果可能较差。")
    FONT = ImageFont.load_default()

# ====================================================================
# 图片合并函数 (已调整布局逻辑)
# ====================================================================

def combine_data_to_single_image(bp_id):
    """
    将 12 张图片 (左侧 6 张 + 右侧 6 张) 排列成 2x6 网格在左边，
    解决方案文本在右边，合并成一张 PNG 图片。
    """
    bp_folder = f"BP{bp_id}"
    bp_dir = os.path.join(OUTPUT_DIR, bp_folder)
    
    # 1. 检查文件夹和文件是否存在
    if not os.path.exists(bp_dir):
        print(f"警告: 文件夹 {bp_dir} 不存在。跳过 BP{bp_id}。")
        return False
    
    # 获取 TXT 文件内容
    txt_path = os.path.join(bp_dir, "solution.txt")
    if not os.path.exists(txt_path):
        print(f"警告: 找不到解决方案文件 {txt_path}。跳过 BP{bp_id}。")
        return False

    with open(txt_path, 'r', encoding='utf-8') as f:
        solution_text = f.read().strip()
    
    # 2. 创建空白画布
    
    # 计算最终图像尺寸
    TOTAL_WIDTH = IMG_AREA_WIDTH + TEXT_AREA_WIDTH
    TOTAL_HEIGHT = IMG_AREA_HEIGHT
    
    # 创建白色背景画布
    combined_img = Image.new('RGB', (TOTAL_WIDTH, TOTAL_HEIGHT), color='white')
    draw = ImageDraw.Draw(combined_img)
    
    # 3. 绘制图片区域 (保持 2x6 布局)
    
    # 找到所有图片文件，并按名称排序（例如 EX1.png, EX2.png, ..., EX12.png）
    # 确保排序是正确的，这依赖于爬虫中文件命名的一致性。
    img_files = sorted([f for f in os.listdir(bp_dir) if f.lower().endswith('.png') and f.startswith('ex')])
    
    if len(img_files) != 12:
        print(f"警告: BP{bp_id} 找到 {len(img_files)} 张图片，预期 12 张。跳过合并。")
        return False

    for i in range(len(img_files)):
        img_path = os.path.join(bp_dir, img_files[i])
        
        try:
            img = Image.open(img_path).convert('RGB')
            # 调整图片大小以适应网格
            img_resized = img.resize((SINGLE_IMG_SIZE, SINGLE_IMG_SIZE))
            
            # **核心逻辑：计算 2x6 网格位置**
            row = i // GRID_COLS # i=0-5 -> row=0; i=6-11 -> row=1
            col = i % GRID_COLS # i=0, 6 -> col=0; i=1, 7 -> col=1; ...
            
            x = IMG_PADDING + col * (SINGLE_IMG_SIZE + IMG_PADDING)
            y = IMG_PADDING + row * (SINGLE_IMG_SIZE + IMG_PADDING)
            
            combined_img.paste(img_resized, (x, y))
            
            # 添加图片编号 (可选)
            # draw.text((x + 5, y + 5), str(i + 1), fill='red', font=FONT)
            
        except Exception as e:
            print(f"处理图片 {img_files[i]} 失败: {e}")
            continue
            
    # 4. 绘制分隔线
    # 在图片区域和文本区域之间画一条黑线
    line_x = IMG_AREA_WIDTH
    draw.line([(line_x, 0), (line_x, TOTAL_HEIGHT)], fill='black', width=2)
    
    # 5. 绘制文本区域
    
    # 文本起始位置 (在分隔线右侧)
    text_x = line_x + TEXT_PADDING
    text_y = TEXT_PADDING
    
    # 文本换行处理，以适应文本区域的宽度
    
    # 确定字体大小和行高
    try:
        avg_char_width = FONT.getbbox('A')[2] - FONT.getbbox('A')[0] # 更好地获取字符宽度
    except:
        avg_char_width = 10 # 失败时使用默认值
        
    # 计算每行字符数
    max_chars_per_line = int((TEXT_AREA_WIDTH - 2 * TEXT_PADDING) / avg_char_width * 1.2)
    
    # 使用 textwrap 进行换行
    wrapped_lines = textwrap.wrap(solution_text, width=max_chars_per_line)
    
    try:
        line_height = FONT.getbbox('Tg')[3] - FONT.getbbox('Tg')[1] + 5 # 更好的行高计算
    except:
        line_height = 20 # 失败时使用默认值

    
    # 渲染每一行文本
    for line in wrapped_lines:
        draw.text((text_x, text_y), line, fill='black', font=FONT)
        text_y += line_height
        
    # 6. 保存最终图片
    output_filename = f"{bp_folder}_combined.png"
    output_path = os.path.join(bp_dir, output_filename)
    combined_img.save(output_path)
    print(f"-> 成功合并并保存到 {output_path}")
    return True

# ====================================================================
# 主运行程序
# ====================================================================

if __name__ == "__main__":
    print(f"开始合并 {START_ID} 到 {END_ID} 的 Bongard Problems 数据...")
    
    # 确保 Arial 字体可用，否则会使用默认字体
    
    for bp_id in range(START_ID, END_ID + 1):
        print(f"正在合并 BP{bp_id}...")
        combine_data_to_single_image(bp_id)

    print("所有合并任务完成。")
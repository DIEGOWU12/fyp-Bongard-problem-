from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# ====================================================================
# --- 配置参数 (你需要修改这里) ---
# = ====================================================================

# 示例文件夹路径：请将这里改为你想要处理的 BP 文件夹的路径
# 例如：'Bongard_Dataset_v2/BP14'
TARGET_FOLDER_PATH = "Bongard_Dataset_v2/BP14" 

# 解决方案文本：如果找不到 solution.txt，将使用这个默认文本
DEFAULT_SOLUTION_TEXT = "未找到 solution.txt 文件，请检查路径。这是默认的解决方案描述。"
OUTPUT_FILENAME = "combined_result.png"

# --- 布局常量 ---
GRID_ROWS = 2 
GRID_COLS = 6
SINGLE_IMG_SIZE = 60 
IMG_PADDING = 5

# 计算图片区域总尺寸
IMG_AREA_WIDTH = GRID_COLS * SINGLE_IMG_SIZE + (GRID_COLS + 1) * IMG_PADDING
IMG_AREA_HEIGHT = GRID_ROWS * SINGLE_IMG_SIZE + (GRID_ROWS + 1) * IMG_PADDING

TEXT_AREA_WIDTH = 350 
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
# 核心图片合并函数
# ====================================================================

def combine_folder_images(folder_path):
    """
    读取指定文件夹内的所有 PNG 图片，按照 2x6 布局与文本合并。
    """
    print(f"正在处理文件夹: {folder_path}")

    # 1. 获取图片文件列表 (不限制文件名开头，只找 PNG 文件)
    img_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.png')])
    
    if len(img_files) != 12:
        print(f"警告: 文件夹中找到 {len(img_files)} 张图片，预期 12 张。跳过合并。")
        return False
    
    # 2. 获取解决方案文本
    txt_path = os.path.join(folder_path, "solution.txt")
    solution_text = DEFAULT_SOLUTION_TEXT
    if os.path.exists(txt_path):
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                solution_text = f.read().strip()
        except Exception as e:
            print(f"读取 solution.txt 失败: {e}")
    else:
        print("警告: 文件夹中未找到 solution.txt，使用默认文本。")
    
    # 3. 创建空白画布
    TOTAL_WIDTH = IMG_AREA_WIDTH + TEXT_AREA_WIDTH
    TOTAL_HEIGHT = IMG_AREA_HEIGHT
    
    combined_img = Image.new('RGB', (TOTAL_WIDTH, TOTAL_HEIGHT), color='white')
    draw = ImageDraw.Draw(combined_img)
    
    # 4. 绘制图片区域 (2x6 布局)
    for i in range(len(img_files)):
        img_path = os.path.join(folder_path, img_files[i])
        
        try:
            img = Image.open(img_path).convert('RGB')
            img_resized = img.resize((SINGLE_IMG_SIZE, SINGLE_IMG_SIZE))
            
            # 计算 2x6 网格位置
            row = i // GRID_COLS 
            col = i % GRID_COLS 
            
            x = IMG_PADDING + col * (SINGLE_IMG_SIZE + IMG_PADDING)
            y = IMG_PADDING + row * (SINGLE_IMG_SIZE + IMG_PADDING)
            
            combined_img.paste(img_resized, (x, y))
            
        except Exception as e:
            print(f"处理图片 {img_files[i]} 失败: {e}")
            continue
            
    # 5. 绘制分隔线
    line_x = IMG_AREA_WIDTH
    draw.line([(line_x, 0), (line_x, TOTAL_HEIGHT)], fill='black', width=2)
    
    # 6. 绘制文本区域
    text_x = line_x + TEXT_PADDING
    text_y = TEXT_PADDING
    
    try:
        avg_char_width = FONT.getbbox('A')[2] - FONT.getbbox('A')[0]
    except:
        avg_char_width = 10
        
    max_chars_per_line = int((TEXT_AREA_WIDTH - 2 * TEXT_PADDING) / avg_char_width * 1.2)
    wrapped_lines = textwrap.wrap(solution_text, width=max_chars_per_line)
    
    try:
        line_height = FONT.getbbox('Tg')[3] - FONT.getbbox('Tg')[1] + 5
    except:
        line_height = 20

    # 渲染每一行文本
    for line in wrapped_lines:
        draw.text((text_x, text_y), line, fill='black', font=FONT)
        text_y += line_height
        
    # 7. 保存最终图片
    output_path = os.path.join(folder_path, OUTPUT_FILENAME)
    combined_img.save(output_path)
    print(f"-> 成功合并并保存到 {output_path}")
    return True

# ====================================================================
# 主运行程序
# ====================================================================
if __name__ == "__main__":
    # 确保你修改了 TARGET_FOLDER_PATH 为你实际要测试的文件夹！
    combine_folder_images(TARGET_FOLDER_PATH) 
    print("操作完成。")
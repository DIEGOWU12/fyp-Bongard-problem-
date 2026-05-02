import os
import re
from PIL import Image

# 路径设置
input_folder = r'C:\Users\Lenovo\OneDrive\文档\GitHub\fyp-Bongard-problem-\kohya_train_data\5_BongardStyle'
output_folder = os.path.join(input_folder, 'split_results')

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def split_images_and_texts():
    count = 0
    # 扫描文件夹
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            base_name = os.path.splitext(filename)[0]
            txt_path = os.path.join(input_folder, f"{base_name}.txt")
            img_path = os.path.join(input_folder, filename)

            # 1. 处理图像裁剪
            with Image.open(img_path) as img:
                width, height = img.size
                mid = width // 2
                left_img = img.crop((0, 0, mid, height))
                right_img = img.crop((mid, 0, width, height))
                left_img.save(os.path.join(output_folder, f"{base_name}_left.png"))
                right_img.save(os.path.join(output_folder, f"{base_name}_right.png"))

            # 2. 处理文本拆分
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                # 使用正则提取 Left Side 和 Right Side 后的描述内容
                left_match = re.search(r"Left Side \(6 panels\): (.*?) Right Side", content)
                right_match = re.search(r"Right Side \(6 panels\): (.*?) Clear visual logic", content)

                if left_match and right_match:
                    left_desc = left_match.group(1).strip().rstrip('.')
                    right_desc = right_match.group(1).strip().rstrip('.')

                    # 构造新的单图标签
                    new_left_txt = f"BongardStyle, a 3x2 geometric grid, white background, {left_desc}, minimalist geometric diagram."
                    new_right_txt = f"BongardStyle, a 3x2 geometric grid, white background, {right_desc}, minimalist geometric diagram."

                    # 保存 .txt 文件
                    with open(os.path.join(output_folder, f"{base_name}_left.txt"), 'w', encoding='utf-8') as f:
                        f.write(new_left_txt)
                    with open(os.path.join(output_folder, f"{base_name}_right.txt"), 'w', encoding='utf-8') as f:
                        f.write(new_right_txt)

            print(f"✅ 已完成拆分: {base_name}")
            count += 1

    print(f"\n🚀 任务完成！生成的 {count * 2} 个文件已存入 split_results 文件夹。")


if __name__ == "__main__":
    split_images_and_texts()
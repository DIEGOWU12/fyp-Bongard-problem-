import os
import shutil

# 你之前整理好的那个文件夹
SOURCE_ROOT = "Bongard_Dataset_v2_new_struct" 
# 准备给 Kohya 训练用的新文件夹
TRAIN_DATA_DIR = "kohya_train_data/10_BongardStyle"

os.makedirs(TRAIN_DATA_DIR, exist_ok=True)

# 遍历所有的 BP 文件夹
folders = [d for d in os.listdir(SOURCE_ROOT) if os.path.isdir(os.path.join(SOURCE_ROOT, d))]

for folder in folders:
    src_path = os.path.join(SOURCE_ROOT, folder)
    
    img_src = os.path.join(src_path, "combined.png")
    txt_src = os.path.join(src_path, "solution.txt")
    
    if os.path.exists(img_src) and os.path.exists(txt_src):
        # 目标文件名使用文件夹名，确保唯一性
        # 比如 BP1_c1_combined.png
        new_base_name = f"{folder}_combined"
        
        # 复制并改名图片
        shutil.copy(img_src, os.path.join(TRAIN_DATA_DIR, f"{new_base_name}.png"))
        
        # 复制并改名为 .caption (或 .txt)
        shutil.copy(txt_src, os.path.join(TRAIN_DATA_DIR, f"{new_base_name}.caption"))
        
        print(f"✅ 已处理: {folder}")

print(f"\n🎉 处理完毕！请将 '{TRAIN_DATA_DIR}' 作为 Kohya 的训练图片路径。")
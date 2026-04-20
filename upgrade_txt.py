import os
import re

# 你的 GitHub 仓库本地路径
dataset_path = r'C:\Users\Lenovo\OneDrive\文档\GitHub\fyp-Bongard-problem-\kohya_train_data\1_BongardStyle'

def refactor_bongard_logic():
    count = 0
    if not os.path.exists(dataset_path):
        print(f"❌ 路径错误，请检查: {dataset_path}")
        return

    print(f"📂 正在扫描目录: {dataset_path} ...")

    for filename in os.listdir(dataset_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(dataset_path, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # 寻找 vs. 标志 (不区分大小写)
            parts = re.split(r'\s+[vV][sS]\.?\s+', content)
            
            if len(parts) == 2:
                # 提取左逻辑和右逻辑，并去掉末尾句号
                left_logic = parts[0].strip().rstrip('.')
                right_logic = parts[1].strip().rstrip('.')
                
                # 构造你最满意的专业格式
                new_content = (
                    f"BongardStyle, a complex black and white geometric 3x4 matrix illustration, "
                    f"12 distinct panels in two separate 3x2 grids, separated by a distinct central vertical line, white background. "
                    f"Left Side (6 panels): each panel features a '{left_logic}' logic, showing geometric shapes with {left_logic} arrangement. "
                    f"Right Side (6 panels): each panel features a '{right_logic}' logic, showing geometric shapes with {right_logic} arrangement. "
                    f"Clear visual logic, stark contrast, minimalist geometric diagram."
                )

                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✅ 已重构: {filename}")
                count += 1

    print(f"\n🚀 重构完成！共处理 {count} 个文件。")
    print("💡 建议：现在可以去 Kohya_ss 开启 TensorBoard 重新训练了。")

if __name__ == "__main__":
    refactor_bongard_logic()